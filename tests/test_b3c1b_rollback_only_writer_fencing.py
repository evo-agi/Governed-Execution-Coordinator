from __future__ import annotations

import ast
from collections.abc import Callable
from contextlib import ExitStack
import gc
import inspect
import os
from pathlib import Path
import pickle
import shutil
import sqlite3
import threading
import time
import traceback
from typing import Any

import pytest

import ge_nwp_coordinator
from ge_nwp_coordinator import StateStore
from ge_nwp_coordinator.sqlite_connection import apply_observational_connection_posture
import ge_nwp_coordinator.sqlite_connection as connection_module
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError, SQLiteStateError, SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import DatabaseClassification, initialize_database, validate_database
from ge_nwp_coordinator.sqlite_security import (
    _StateDatabaseAuthorityBindingMismatch,
    _StateDatabaseAuthorityBindingUnavailable,
)
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _MutationReadCapabilityError,
    _MutationReadCapabilityFailureReason,
)
from ge_nwp_coordinator.sqlite_writer_session import (
    SQLiteWriterAcquisitionError,
    SQLiteWriterAcquisitionFailureReason,
    _WriterIssuanceMatch,
    acquire_sqlite_writer_session,
)
from ge_nwp_coordinator.state_store import (
    GlobalStopApplyPreflightError,
    GlobalStopApplyPreflightFailureReason,
    TransitionApplyPreflightError,
    TransitionApplyPreflightFailureReason,
    WriterSessionError,
    WriterSessionFailureReason,
)
import ge_nwp_coordinator.sqlite_migration as migration_module
import ge_nwp_coordinator.sqlite_transition_read_scope as read_scope
import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module
import ge_nwp_coordinator.sqlite_writer_session as writer_module

from b3_coherent_transition_fixture import (
    global_stop_event_count_for_test,
    make_coherent_transition_fixture_for_test,
    transition_event_count_for_test,
)
from test_sqlite_b2c_writer_session import (
    _join_thread,
    _location,
    _run_writer_attempt,
    _wait_for_child_result,
    _wait_for_event,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
TRANSACTION_MODULE_PATH = PACKAGE_DIR / "sqlite_transition_transaction.py"
EXPECTED_WRITER_ROW_QUERY = """SELECT
    singleton_id,
    writer_ref,
    generation,
    issued_ref,
    issuance_nonce_digest,
    acquired_at
FROM writer_ownership
ORDER BY singleton_id
LIMIT 2"""
PRIVATE_SENTINEL = "PRIVATE-B3C1B-SENTINEL-DO-NOT-LEAK"


@pytest.fixture(scope="module", autouse=True)
def _force_final_sqlite_connection_collection() -> object:
    yield
    assert type(gc.collect()) is int


class _SyntheticSQLiteError(sqlite3.DatabaseError):
    def __init__(self, sqlite_errorcode: int | None) -> None:
        super().__init__(PRIVATE_SENTINEL)
        if sqlite_errorcode is not None:
            self.sqlite_errorcode = sqlite_errorcode


class _ScriptedCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        fetch_error: sqlite3.Error | None = None,
        close_error: sqlite3.Error | None = None,
    ) -> None:
        self._rows = rows
        self._fetch_error = fetch_error
        self._close_error = close_error
        self.fetchmany_sizes: list[int] = []
        self.close_count = 0

    def fetchmany(self, size: int) -> list[Any]:
        self.fetchmany_sizes.append(size)
        if self._fetch_error is not None:
            raise self._fetch_error
        return list(self._rows[:size])

    def close(self) -> None:
        self.close_count += 1
        if self._close_error is not None:
            raise self._close_error


class _FaultingConnection(sqlite3.Connection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.select_execute_error: sqlite3.Error | None = None
        self.select_cursor: _ScriptedCursor | None = None
        self.validation_execute_error: sqlite3.Error | None = None
        self.validation_execute_sql_fragment: str | None = None
        self.execute_calls: list[str] = []
        self.close_count = 0
        self.close_error: sqlite3.Error | None = None

    def execute(self, sql: str, parameters: Any = (), /) -> Any:
        self.execute_calls.append(sql)
        if (
            self.validation_execute_error is not None
            and self.validation_execute_sql_fragment is not None
            and self.validation_execute_sql_fragment in sql
        ):
            raise self.validation_execute_error
        if sql == transaction_module._WRITER_OWNERSHIP_SELECT.sql:
            if self.select_execute_error is not None:
                raise self.select_execute_error
            if self.select_cursor is not None:
                return self.select_cursor
        return super().execute(sql, parameters)

    def close(self) -> None:
        self.close_count += 1
        if self.close_error is not None:
            raise self.close_error
        super().close()


class _FaultingConnectionLedger:
    """Test-only exact-identity owner for transferred faulting connections."""

    def __init__(self) -> None:
        self._connections: dict[int, _FaultingConnection] = {}
        self.cleanup_failure_count = 0

    @property
    def connections(self) -> tuple[_FaultingConnection, ...]:
        return tuple(self._connections.values())

    def adopt(self, connection: _FaultingConnection) -> None:
        if type(connection) is not _FaultingConnection or id(connection) in self._connections:
            raise ValueError("invalid faulting connection transfer")
        self._connections[id(connection)] = connection

    def cleanup(self) -> None:
        owned = tuple(self._connections.values())
        self._connections.clear()
        for connection in owned:
            try:
                connection.close_error = None
                connection.close()
            except BaseException:
                self.cleanup_failure_count += 1
                try:
                    connection.close_error = None
                    sqlite3.Connection.close(connection)
                except BaseException:
                    self.cleanup_failure_count += 1


def _close_locally_owned_faulting_connection_preserving_primary(
    connection: _FaultingConnection,
) -> None:
    try:
        connection.close()
    except BaseException:
        try:
            connection.close_error = None
            sqlite3.Connection.close(connection)
        except BaseException:
            pass


def _sqlite_error_code(name: str, fallback: int) -> int:
    code = getattr(sqlite3, name, fallback)
    assert type(code) is int
    return code


def _render_exception_graph(exc: BaseException) -> str:
    rendered: list[str] = []
    pending = [exc]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        rendered.extend(
            (
                type(current).__name__,
                str(current),
                repr(current),
                repr(current.args),
                repr(getattr(current, "__notes__", None)),
                "".join(traceback.format_exception(type(current), current, current.__traceback__)),
            )
        )
        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)
    return "\n".join(rendered)


def _assert_safe_mutation_error(
    exc: SQLiteMutationStoreError,
    error_class: str,
    *,
    private_values: tuple[object, ...] = (),
) -> None:
    assert exc.error_class == error_class
    assert str(exc) == error_class
    assert exc.args == (error_class,)
    assert exc.internal_detail is None
    assert exc.__cause__ is None
    assert exc.__context__ is None
    assert exc.error_class != "commit_outcome_unknown"
    rendered = _render_exception_graph(exc)
    for forbidden in (
        PRIVATE_SENTINEL,
        "proof",
        "credential",
        "epoch",
        "operation_id",
        "lifecycle_epoch",
        "SELECT ",
        "BEGIN IMMEDIATE",
        "ROLLBACK",
        "sqlite_errorcode",
    ):
        assert forbidden not in rendered
    for private_value in private_values:
        assert str(private_value) not in rendered


def _assert_capability_error(
    exc: _MutationReadCapabilityError,
    reason: _MutationReadCapabilityFailureReason,
) -> None:
    assert exc.reason is reason
    assert str(exc) == reason.value
    assert exc.args == (reason.value,)
    assert exc.__cause__ is None
    assert exc.__context__ is None


def _run_controller(session: object) -> _WriterIssuanceMatch:
    with session._resource.operation_guard(session) as operation:
        return transaction_module._run_rollback_only_writer_fencing(
            operation_lease=operation,
        )


def _assert_controller_raises(
    session: object,
    error_class: str,
    *,
    private_values: tuple[object, ...] = (),
) -> SQLiteMutationStoreError:
    with session._resource.operation_guard(session) as operation:
        with pytest.raises(SQLiteMutationStoreError) as exc_info:
            transaction_module._run_rollback_only_writer_fencing(
                operation_lease=operation,
            )
        mutation = operation._acquire_mutation_lease()
        operation._require_active_mutation_authority()
        mutation._close()
    _assert_safe_mutation_error(exc_info.value, error_class, private_values=private_values)
    assert session._resource._mutation_slot is None
    return exc_info.value


def _assert_controller_close_unproved_raises(
    session: object,
    error_class: str,
    *,
    private_values: tuple[object, ...] = (),
) -> SQLiteMutationStoreError:
    resource = session._resource
    with resource.operation_guard(session) as operation:
        with pytest.raises(SQLiteMutationStoreError) as exc_info:
            transaction_module._run_rollback_only_writer_fencing(
                operation_lease=operation,
            )
        assert resource._state == "abort_close_unproved"
        assert resource._mutation_slot is not None
        with pytest.raises(WriterSessionError) as unavailable:
            operation._acquire_mutation_lease()
        assert unavailable.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED
    _assert_safe_mutation_error(exc_info.value, error_class, private_values=private_values)
    assert resource._state == "abort_close_unproved"
    assert resource._mutation_slot is not None
    return exc_info.value


def _assert_controller_filesystem_failure(
    session: object,
    error_class: str,
    *,
    private_values: tuple[object, ...] = (),
) -> SQLiteMutationStoreError:
    with session._resource.operation_guard(session) as operation:
        with pytest.raises(SQLiteMutationStoreError) as exc_info:
            transaction_module._run_rollback_only_writer_fencing(
                operation_lease=operation,
            )
    _assert_safe_mutation_error(exc_info.value, error_class, private_values=private_values)
    assert session._resource._mutation_slot is None
    return exc_info.value


def _assert_writer_acquisition_fails_safely(
    location: CoordinatorStateLocation,
    *,
    private_values: tuple[object, ...] = (),
) -> None:
    with pytest.raises((SQLiteWriterAcquisitionError, SQLiteStateError)) as exc_info:
        acquire_sqlite_writer_session(location)
    error = exc_info.value
    if isinstance(error, SQLiteWriterAcquisitionError):
        assert error.reason is SQLiteWriterAcquisitionFailureReason.DATABASE_NOT_MANAGED
    else:
        assert error.error_class == "unsafe_database_file"
    rendered = _render_exception_graph(error)
    for private_value in private_values:
        assert str(private_value) not in rendered


def _managed_session(tmp_path: Path) -> tuple[CoordinatorStateLocation, object]:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    return location, session


def _open_faulting_connection(
    location: CoordinatorStateLocation,
    *,
    select_execute_error: sqlite3.Error | None = None,
    select_cursor: _ScriptedCursor | None = None,
    validation_execute_error: sqlite3.Error | None = None,
    validation_execute_sql_fragment: str | None = None,
    close_error: sqlite3.Error | None = None,
    ownership_ledger: _FaultingConnectionLedger | None = None,
) -> _FaultingConnection:
    connection = sqlite3.connect(
        location.database_path,
        isolation_level=None,
        factory=_FaultingConnection,
    )
    locally_owned = True
    try:
        apply_observational_connection_posture(connection)
        connection.select_execute_error = select_execute_error
        connection.select_cursor = select_cursor
        connection.validation_execute_error = validation_execute_error
        connection.validation_execute_sql_fragment = validation_execute_sql_fragment
        connection.close_error = close_error
        if ownership_ledger is not None:
            ownership_ledger.adopt(connection)
        locally_owned = False
        return connection
    except BaseException:
        if locally_owned:
            _close_locally_owned_faulting_connection_preserving_primary(connection)
        raise


def _patch_bound_open_connect(
    monkeypatch: pytest.MonkeyPatch,
    location: CoordinatorStateLocation,
    *,
    close_error: sqlite3.Error | None = None,
) -> _FaultingConnectionLedger:
    ledger = _FaultingConnectionLedger()

    def connect_uri(uri: str, *, busy_timeout_ms: int) -> _FaultingConnection:
        return _open_faulting_connection(
            location,
            close_error=close_error,
            ownership_ledger=ledger,
        )

    monkeypatch.setattr(connection_module, "_connect_uri", connect_uri)
    return ledger


def _patch_post_open_structural_binding_mismatch(monkeypatch: pytest.MonkeyPatch) -> Callable[[], int]:
    original_validate = connection_module._validate_state_database_authority_binding
    validation_calls = 0

    def validate(binding: object) -> None:
        nonlocal validation_calls
        validation_calls += 1
        if validation_calls > 1:
            raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
        original_validate(binding)

    monkeypatch.setattr(connection_module, "_validate_state_database_authority_binding", validate)
    return lambda: validation_calls


def _patch_post_open_operational_posture_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_posture(connection: sqlite3.Connection, **kwargs: object) -> object:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE, internal_detail=PRIVATE_SENTINEL)

    monkeypatch.setattr(connection_module, "apply_observational_connection_posture", fail_posture)


def _cleanup_faulting_connections(connections: list[_FaultingConnection]) -> None:
    for connection in connections:
        if connection.close_error is not None:
            connection.close_error = None
        connection.close()
        _assert_sqlite_connection_closed(connection)


def _assert_sqlite_connection_closed(connection: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


def _patch_retained_close_failure_once(monkeypatch: pytest.MonkeyPatch) -> None:
    original_close = connection_module._RetainedSQLiteConnection._close_with_proof
    close_attempts = 0

    def fail_once(retained: object) -> object:
        nonlocal close_attempts
        close_attempts += 1
        if close_attempts == 1:
            raise RuntimeError(PRIVATE_SENTINEL)
        return original_close(retained)

    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        fail_once,
    )


def _table_count(location: CoordinatorStateLocation, table_name: str) -> int:
    connection = sqlite3.connect(location.database_path)
    try:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
    finally:
        connection.close()


def _writer_rows(location: CoordinatorStateLocation) -> list[tuple[object, ...]]:
    connection = sqlite3.connect(location.database_path)
    try:
        return connection.execute(
            """
            SELECT singleton_id, writer_ref, generation, issued_ref,
                   issuance_nonce_digest, acquired_at
            FROM writer_ownership
            ORDER BY singleton_id
            """
        ).fetchall()
    finally:
        connection.close()


def _global_stop_rows(location: CoordinatorStateLocation) -> list[tuple[object, ...]]:
    connection = sqlite3.connect(location.database_path)
    try:
        return connection.execute(
            """
            SELECT singleton_id, schema_id, version, active, stop_id, reason_class,
                   issuer_ref, issued_at, operator_decision_ref, updated_at
            FROM global_stop_current
            ORDER BY singleton_id
            """
        ).fetchall()
    finally:
        connection.close()


def _state_counts(location: CoordinatorStateLocation) -> dict[str, int]:
    return {
        table_name: _table_count(location, table_name)
        for table_name in (
            "lease_identity_records",
            "authorization_decision_receipts",
            "admitted_backlogs",
            "dependency_decision_receipts",
            "global_stop_operator_decision_receipts",
            "work_items",
            "transition_events",
            "global_stop_events",
        )
    }


def _replace_writer_row(location: CoordinatorStateLocation, **updates: object) -> None:
    assert updates
    assignments = ", ".join(f"{column} = ?" for column in updates)
    values = tuple(updates.values())
    connection = sqlite3.connect(location.database_path)
    try:
        connection.execute(f"UPDATE writer_ownership SET {assignments} WHERE singleton_id = 1", values)
        connection.commit()
    finally:
        connection.close()


def _copy_database_to_temp(location: CoordinatorStateLocation, target: Path) -> Path:
    shutil.copyfile(location.database_path, target)
    target.chmod(0o600)
    return target


def _swap_database_file(location: CoordinatorStateLocation, replacement: Path, backup: Path) -> None:
    os.replace(location.database_path, backup)
    os.replace(replacement, location.database_path)
    location.database_path.chmod(0o600)


def _delete_writer_row(location: CoordinatorStateLocation) -> None:
    connection = sqlite3.connect(location.database_path)
    try:
        connection.execute("DELETE FROM writer_ownership")
        connection.commit()
    finally:
        connection.close()


def _set_malformed_digest(location: CoordinatorStateLocation) -> None:
    connection = sqlite3.connect(location.database_path)
    try:
        connection.execute("PRAGMA ignore_check_constraints = ON")
        connection.execute("UPDATE writer_ownership SET issuance_nonce_digest = ?", ("B" * 64,))
        connection.commit()
    finally:
        connection.close()


def _break_managed_schema(location: CoordinatorStateLocation) -> None:
    connection = sqlite3.connect(location.database_path)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("DROP TABLE lease_identity_records")
        connection.commit()
    finally:
        connection.close()


def _assert_database_writable(location: CoordinatorStateLocation) -> None:
    connection = sqlite3.connect(location.database_path, isolation_level=None)
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("ROLLBACK")
    finally:
        connection.close()


def test_direct_test_helpers_close_every_owned_sqlite_connection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases: tuple[
        tuple[str, Callable[[CoordinatorStateLocation], object]],
        ...,
    ] = (
        ("table-count", lambda location: _table_count(location, "writer_ownership")),
        ("writer-rows", _writer_rows),
        ("global-stop-rows", _global_stop_rows),
        ("replace-writer", lambda location: _replace_writer_row(location, generation=1)),
        ("delete-writer", _delete_writer_row),
        ("malformed-digest", _set_malformed_digest),
        ("break-schema", _break_managed_schema),
    )

    for case_name, invoke in cases:
        location, session = _managed_session(tmp_path / case_name)
        session.close()
        opened: list[sqlite3.Connection] = []
        with monkeypatch.context() as helper_patch:
            original_connect = sqlite3.connect

            def tracking_connect(*args: object, **kwargs: object) -> sqlite3.Connection:
                connection = original_connect(*args, **kwargs)
                opened.append(connection)
                return connection

            helper_patch.setattr(sqlite3, "connect", tracking_connect)
            invoke(location)

        assert len(opened) == 1
        _assert_sqlite_connection_closed(opened[0])
        opened.clear()
        assert type(gc.collect()) is int


def test_controller_entry_point_is_operation_lease_only() -> None:
    signature = inspect.signature(transaction_module._run_rollback_only_writer_fencing)
    assert tuple(signature.parameters) == ("operation_lease",)
    operation_parameter = signature.parameters["operation_lease"]
    assert operation_parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert operation_parameter.default is inspect.Parameter.empty
    assert operation_parameter.annotation in (
        "_WriterSessionOperationLease",
        writer_module._WriterSessionOperationLease,
    )
    source = TRANSACTION_MODULE_PATH.read_text(encoding="utf-8")
    assert "location:" not in inspect.getsource(transaction_module._run_rollback_only_writer_fencing)
    assert "database_path" not in inspect.getsource(transaction_module._run_rollback_only_writer_fencing)
    assert "def for_test" not in source
    assert "controller_for_test" not in source


def test_controller_opens_resource_owned_location_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location_a, session = _managed_session(tmp_path / "a")
    location_b = _location(tmp_path / "b")
    initialize_database(location_b)
    b_before = location_b.database_path.read_bytes()
    opened_bindings: list[object] = []
    expected_binding = session._resource._database_binding
    original_open = transaction_module._open_bound_existing_sqlite_connection

    def tracking_open(binding: object, **kwargs: Any) -> sqlite3.Connection:
        opened_bindings.append(binding)
        return original_open(binding, **kwargs)

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", tracking_open)
    try:
        assert _run_controller(session) is _WriterIssuanceMatch.MATCH
    finally:
        session.close()

    assert opened_bindings == [expected_binding]
    assert location_b.database_path.read_bytes() == b_before
    assert _writer_rows(location_b) == []


def test_cloned_writer_row_cross_location_cannot_be_supplied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location_a, session = _managed_session(tmp_path / "a")
    location_b = _location(tmp_path / "b")
    initialize_database(location_b)
    shutil.copyfile(location_a.database_path, location_b.database_path)
    b_before = location_b.database_path.read_bytes()
    opened_bindings: list[object] = []
    expected_binding = session._resource._database_binding
    capability_connections: list[int] = []
    original_open = transaction_module._open_bound_existing_sqlite_connection
    original_create = transaction_module._create_sqlite_mutation_read_capability

    def tracking_open(binding: object, **kwargs: Any) -> sqlite3.Connection:
        opened_bindings.append(binding)
        return original_open(binding, **kwargs)

    def tracking_create(**kwargs: Any) -> object:
        capability_connections.append(id(kwargs["connection"]))
        return original_create(**kwargs)

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", tracking_open)
    monkeypatch.setattr(transaction_module, "_create_sqlite_mutation_read_capability", tracking_create)
    try:
        assert _run_controller(session) is _WriterIssuanceMatch.MATCH
    finally:
        session.close()

    assert opened_bindings == [expected_binding]
    assert len(capability_connections) == 1
    assert location_b.database_path.read_bytes() == b_before
    assert _writer_rows(location_b) == _writer_rows(location_a)


@pytest.mark.parametrize("case_name", ("copied-writer-row", "independent-managed-database"))
def test_database_replacement_after_writer_session_acquisition_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case_name: str,
) -> None:
    location, session = _managed_session(tmp_path / case_name / "a")
    replacement = tmp_path / case_name / "replacement.sqlite"
    backup = tmp_path / case_name / "original.sqlite"
    if case_name == "copied-writer-row":
        _copy_database_to_temp(location, replacement)
    else:
        replacement_location = _location(tmp_path / case_name / "b")
        initialize_database(replacement_location)
        replacement_session = acquire_sqlite_writer_session(replacement_location)
        replacement_session.close()
        _copy_database_to_temp(replacement_location, replacement)
    capability_calls = 0
    original_create = transaction_module._create_sqlite_mutation_read_capability

    def tracking_create(**kwargs: Any) -> object:
        nonlocal capability_calls
        capability_calls += 1
        return original_create(**kwargs)

    monkeypatch.setattr(transaction_module, "_create_sqlite_mutation_read_capability", tracking_create)
    _swap_database_file(location, replacement, backup)
    try:
        _assert_controller_filesystem_failure(
            session,
            "database_integrity_failure",
            private_values=(location.state_root, location.database_path),
        )
        assert capability_calls == 0
    finally:
        if location.database_path.exists():
            location.database_path.unlink()
        if backup.exists():
            os.replace(backup, location.database_path)
        session.close()


def test_database_replacement_between_bound_descriptor_check_and_sqlite_open_is_detected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ge_nwp_coordinator.sqlite_connection as connection_module

    location, session = _managed_session(tmp_path)
    replacement = _copy_database_to_temp(location, tmp_path / "replacement.sqlite")
    backup = tmp_path / "original.sqlite"
    drifted = False
    original_descriptor_open = connection_module._open_bound_database_descriptor

    def drifting_descriptor_open(binding: object, *, root_descriptor: int) -> int:
        nonlocal drifted
        descriptor = original_descriptor_open(binding, root_descriptor=root_descriptor)
        if not drifted:
            drifted = True
            _swap_database_file(location, replacement, backup)
        return descriptor

    monkeypatch.setattr(connection_module, "_open_bound_database_descriptor", drifting_descriptor_open)
    try:
        _assert_controller_filesystem_failure(
            session,
            "database_integrity_failure",
            private_values=(location.state_root, location.database_path),
        )
        assert drifted is True
    finally:
        if location.database_path.exists():
            location.database_path.unlink()
        if backup.exists():
            os.replace(backup, location.database_path)

    assert _run_controller(session) is _WriterIssuanceMatch.MATCH
    session.close()


def test_bound_open_post_open_structural_mismatch_close_succeeds_preserves_primary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)
    try:
        with monkeypatch.context() as direct_patch:
            ledger = _patch_bound_open_connect(direct_patch, location)
            with ExitStack() as resources:
                resources.callback(ledger.cleanup)
                validation_calls = _patch_post_open_structural_binding_mismatch(direct_patch)
                with pytest.raises(_StateDatabaseAuthorityBindingMismatch) as direct_error:
                    connection_module._open_bound_existing_sqlite_connection(
                        session._resource._database_binding,
                        read_only=False,
                    )
                opened = ledger.connections
                assert validation_calls() == 2
                assert len(opened) == 1
                assert opened[0].close_count == 1
                assert direct_error.value.__cause__ is None
                assert direct_error.value.__context__ is None

        with monkeypatch.context() as controller_patch:
            ledger = _patch_bound_open_connect(controller_patch, location)
            with ExitStack() as resources:
                resources.callback(ledger.cleanup)
                validation_calls = _patch_post_open_structural_binding_mismatch(controller_patch)
                _assert_controller_filesystem_failure(
                    session,
                    "database_integrity_failure",
                    private_values=(location.state_root, location.database_path),
                )
                opened = ledger.connections
                assert validation_calls() == 2
                assert len(opened) == 1
                assert opened[0].close_count == 1
    finally:
        session.close()


def test_bound_open_post_open_structural_mismatch_close_failure_preserves_primary_and_privacy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    location, session = _managed_session(tmp_path)
    close_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5))
    try:
        with monkeypatch.context() as direct_patch:
            ledger = _patch_bound_open_connect(direct_patch, location, close_error=close_error)
            with ExitStack() as resources:
                resources.callback(ledger.cleanup)
                validation_calls = _patch_post_open_structural_binding_mismatch(direct_patch)
                with pytest.raises(_StateDatabaseAuthorityBindingMismatch) as direct_error:
                    connection_module._open_bound_existing_sqlite_connection(
                        session._resource._database_binding,
                        read_only=False,
                    )
                opened = ledger.connections
                assert validation_calls() == 2
                assert len(opened) == 1
                assert opened[0].close_count == 1
                assert direct_error.value.__cause__ is None
                assert direct_error.value.__context__ is None
                assert PRIVATE_SENTINEL not in _render_exception_graph(direct_error.value)

        with monkeypatch.context() as controller_patch:
            ledger = _patch_bound_open_connect(controller_patch, location, close_error=close_error)
            with ExitStack() as resources:
                resources.callback(ledger.cleanup)
                validation_calls = _patch_post_open_structural_binding_mismatch(controller_patch)
                error = _assert_controller_filesystem_failure(
                    session,
                    "database_integrity_failure",
                    private_values=(location.state_root, location.database_path),
                )
                opened = ledger.connections
                assert validation_calls() == 2
                assert len(opened) == 1
                assert opened[0].close_count == 1
                assert PRIVATE_SENTINEL not in _render_exception_graph(error)
    finally:
        session.close()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_bound_open_post_open_operational_failure_close_failure_preserves_primary_and_privacy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    location, session = _managed_session(tmp_path)
    close_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5))
    try:
        with monkeypatch.context() as direct_patch:
            ledger = _patch_bound_open_connect(direct_patch, location, close_error=close_error)
            with ExitStack() as resources:
                resources.callback(ledger.cleanup)
                _patch_post_open_operational_posture_failure(direct_patch)
                with pytest.raises(_StateDatabaseAuthorityBindingUnavailable) as direct_error:
                    connection_module._open_bound_existing_sqlite_connection(
                        session._resource._database_binding,
                        read_only=False,
                    )
                opened = ledger.connections
                assert len(opened) == 1
                assert opened[0].close_count == 1
                assert direct_error.value.__cause__ is None
                assert direct_error.value.__context__ is None
                assert PRIVATE_SENTINEL not in _render_exception_graph(direct_error.value)

        with monkeypatch.context() as controller_patch:
            ledger = _patch_bound_open_connect(controller_patch, location, close_error=close_error)
            with ExitStack() as resources:
                resources.callback(ledger.cleanup)
                _patch_post_open_operational_posture_failure(controller_patch)
                error = _assert_controller_filesystem_failure(
                    session,
                    "mutation_failed",
                    private_values=(location.state_root, location.database_path),
                )
                opened = ledger.connections
                assert len(opened) == 1
                assert opened[0].close_count == 1
                assert PRIVATE_SENTINEL not in _render_exception_graph(error)
    finally:
        session.close()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_root_directory_replacement_fails_before_writer_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path / "active")
    replacement_location = _location(tmp_path / "replacement")
    initialize_database(replacement_location)
    old_root = tmp_path / "old-active-root"
    sqlite_open_calls = 0

    def fail_if_open(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        nonlocal sqlite_open_calls
        sqlite_open_calls += 1
        raise AssertionError("root drift opened SQLite")

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_if_open)
    os.rename(location.state_root, old_root)
    os.rename(replacement_location.state_root, location.state_root)
    try:
        _assert_controller_filesystem_failure(
            session,
            "database_integrity_failure",
            private_values=(location.state_root, location.database_path),
        )
        assert sqlite_open_calls == 0
    finally:
        session.close()
        if location.state_root.exists():
            shutil.rmtree(location.state_root)
        if old_root.exists():
            os.rename(old_root, location.state_root)


def test_lock_file_replacement_fails_before_sqlite_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)
    sqlite_open_calls = 0
    replacement_lock = tmp_path / "replacement.lock"
    replacement_lock.write_text("", encoding="utf-8")
    replacement_lock.chmod(0o600)

    def fail_if_open(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        nonlocal sqlite_open_calls
        sqlite_open_calls += 1
        raise AssertionError("lock drift opened SQLite")

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_if_open)
    os.replace(replacement_lock, location.state_authority_lock_path)
    try:
        _assert_controller_filesystem_failure(
            session,
            "database_integrity_failure",
            private_values=(location.state_root, location.database_path),
        )
        assert sqlite_open_calls == 0
    finally:
        session.close()


def test_hard_linked_database_before_writer_acquisition_rejects_both_aliases(
    tmp_path: Path,
) -> None:
    location_a = _location(tmp_path / "a")
    location_b = _location(tmp_path / "b")
    initialize_database(location_a)
    initialize_database(location_b)
    location_b.database_path.unlink()
    os.link(location_a.database_path, location_b.database_path)

    _assert_writer_acquisition_fails_safely(
        location_a,
        private_values=(location_a.database_path, location_b.database_path),
    )
    _assert_writer_acquisition_fails_safely(
        location_b,
        private_values=(location_a.database_path, location_b.database_path),
    )
    location_b.database_path.unlink()
    session = acquire_sqlite_writer_session(location_a)
    try:
        assert session.metadata.generation == 1
    finally:
        session.close()


def test_hard_linked_database_after_writer_acquisition_blocks_alias_and_resumes_after_unlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location_a, session = _managed_session(tmp_path / "a")
    location_b = _location(tmp_path / "b")
    initialize_database(location_b)
    location_b.database_path.unlink()
    os.link(location_a.database_path, location_b.database_path)
    capability_calls = 0
    original_create = transaction_module._create_sqlite_mutation_read_capability

    def tracking_create(**kwargs: Any) -> object:
        nonlocal capability_calls
        capability_calls += 1
        return original_create(**kwargs)

    monkeypatch.setattr(transaction_module, "_create_sqlite_mutation_read_capability", tracking_create)
    try:
        _assert_controller_filesystem_failure(
            session,
            "database_integrity_failure",
            private_values=(location_a.database_path, location_b.database_path),
        )
        assert capability_calls == 0
        _assert_writer_acquisition_fails_safely(
            location_b,
            private_values=(location_a.database_path, location_b.database_path),
        )
        location_b.database_path.unlink()
        assert _run_controller(session) is _WriterIssuanceMatch.MATCH
        assert capability_calls == 1
    finally:
        if location_b.database_path.exists():
            location_b.database_path.unlink()
        session.close()


@pytest.mark.parametrize("case_name", ("database", "root", "lock", "hardlink"))
def test_writer_acquisition_rechecks_filesystem_binding_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case_name: str,
) -> None:
    location = _location(tmp_path / case_name)
    initialize_database(location)
    backup_database = tmp_path / f"{case_name}-original.sqlite"
    replacement_database = tmp_path / f"{case_name}-replacement.sqlite"
    old_root = tmp_path / f"{case_name}-old-root"
    replacement_root_location = _location(tmp_path / f"{case_name}-replacement-root")
    replacement_lock = tmp_path / f"{case_name}-replacement.lock"
    hardlink_alias = tmp_path / f"{case_name}-alias.sqlite"
    original_capture = writer_module.StateAuthorityLock._capture_state_database_authority_binding
    capture_calls = 0

    if case_name == "database":
        _copy_database_to_temp(location, replacement_database)
    elif case_name == "root":
        initialize_database(replacement_root_location)
    elif case_name == "lock":
        replacement_lock.write_text("", encoding="utf-8")
        replacement_lock.chmod(0o600)

    def drift_filesystem() -> None:
        if case_name == "database":
            _swap_database_file(location, replacement_database, backup_database)
        elif case_name == "root":
            os.rename(location.state_root, old_root)
            os.rename(replacement_root_location.state_root, location.state_root)
        elif case_name == "lock":
            os.replace(replacement_lock, location.state_authority_lock_path)
        else:
            os.link(location.database_path, hardlink_alias)

    def capture_with_publication_drift(self: object, captured_location: CoordinatorStateLocation) -> object:
        nonlocal capture_calls
        capture_calls += 1
        if capture_calls == 2:
            drift_filesystem()
        return original_capture(self, captured_location)

    monkeypatch.setattr(
        writer_module.StateAuthorityLock,
        "_capture_state_database_authority_binding",
        capture_with_publication_drift,
    )
    with pytest.raises(SQLiteWriterAcquisitionError) as exc_info:
        acquire_sqlite_writer_session(location)
    assert exc_info.value.reason is SQLiteWriterAcquisitionFailureReason.DATABASE_NOT_MANAGED
    assert capture_calls == 2
    rendered = _render_exception_graph(exc_info.value)
    for private_value in (location.state_root, location.database_path):
        assert str(private_value) not in rendered
    assert writer_module._ACTIVE_SESSION_RESOURCES == {}

    monkeypatch.undo()
    if case_name == "database":
        if location.database_path.exists():
            location.database_path.unlink()
        os.replace(backup_database, location.database_path)
    elif case_name == "root":
        if location.state_root.exists():
            shutil.rmtree(location.state_root)
        os.rename(old_root, location.state_root)
    elif case_name == "hardlink" and hardlink_alias.exists():
        hardlink_alias.unlink()

    next_session = acquire_sqlite_writer_session(location)
    try:
        assert next_session.metadata.generation == 2
    finally:
        next_session.close()


def test_resource_bound_location_accessor_requires_active_mutation_authority(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    location, session = _managed_session(tmp_path)
    try:
        with session._resource.operation_guard(session) as operation:
            with pytest.raises(WriterSessionError) as no_slot:
                operation._bound_state_database_for_mutation()
            assert no_slot.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED

            mutation = operation._acquire_mutation_lease()
            binding = operation._bound_state_database_for_mutation()
            assert binding is session._resource._database_binding
            assert repr(binding) == "<_StateDatabaseAuthorityBinding>"

            mutation._close()
            with pytest.raises(WriterSessionError) as released:
                operation._bound_state_database_for_mutation()
            assert released.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED
    finally:
        session.close()

    rendered = _render_exception_graph(no_slot.value) + _render_exception_graph(released.value)
    assert str(location.state_root) not in rendered
    assert str(location.database_path) not in rendered
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_resource_bound_location_accessor_wrong_thread_and_process_fail_closed(
    tmp_path: Path,
) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location, session = _managed_session(tmp_path)
    operation = session._resource.operation_guard(session)
    mutation = operation._acquire_mutation_lease()
    thread_results: list[str] = []

    def wrong_thread_access() -> None:
        try:
            operation._bound_state_database_for_mutation()
        except WriterSessionError as exc:
            thread_results.append(exc.reason.value)
        else:
            thread_results.append("unexpected-binding")

    thread = threading.Thread(target=wrong_thread_access)
    thread.start()
    _join_thread(thread)
    assert thread_results == [WriterSessionFailureReason.WRITER_SESSION_CLOSED.value]

    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        try:
            try:
                operation._bound_state_database_for_mutation()
            except WriterSessionError as exc:
                result = exc.reason.value
            else:
                result = "unexpected-binding"
            os.write(write_fd, result.encode("ascii"))
        finally:
            os.close(write_fd)
            os._exit(0)

    os.close(write_fd)
    try:
        child_result = _wait_for_child_result(child_pid, read_fd)
    finally:
        os.close(read_fd)
        mutation._close()
        operation._close()
        session.close()
    assert child_result == WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH.value
    assert _run_writer_attempt(location) == "acquired:2"


def test_mutation_lease_construction_baseexception_clears_slot_immediately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)

    class _PrivateLeaseConstructionBaseError(BaseException):
        pass

    def fail_lease_construction(**kwargs: Any) -> object:
        raise _PrivateLeaseConstructionBaseError(PRIVATE_SENTINEL)

    try:
        with session._resource.operation_guard(session) as operation:
            with monkeypatch.context() as construction_fault:
                construction_fault.setattr(
                    writer_module,
                    "_MUTATION_LEASE_FACTORY",
                    fail_lease_construction,
                )
                with pytest.raises(_PrivateLeaseConstructionBaseError):
                    operation._acquire_mutation_lease()
                assert session._resource._mutation_slot is None

            mutation = operation._acquire_mutation_lease()
            operation._require_active_mutation_authority()
            mutation._close()
            assert session._resource._mutation_slot is None
    finally:
        session.close()
    assert _run_writer_attempt(location) == "acquired:2"


def test_controller_sanitizes_mutation_lease_construction_failure_before_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    location, session = _managed_session(tmp_path)
    open_calls = 0

    class _PrivateLeaseConstructionError(Exception):
        pass

    def fail_lease_construction(**kwargs: Any) -> object:
        raise _PrivateLeaseConstructionError(PRIVATE_SENTINEL)

    def fail_if_open(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        nonlocal open_calls
        open_calls += 1
        raise AssertionError("constructor fault opened SQLite")

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_if_open)
    try:
        with session._resource.operation_guard(session) as operation:
            with monkeypatch.context() as construction_fault:
                construction_fault.setattr(
                    writer_module,
                    "_MUTATION_LEASE_FACTORY",
                    fail_lease_construction,
                )
                with pytest.raises(SQLiteMutationStoreError) as exc_info:
                    transaction_module._run_rollback_only_writer_fencing(
                        operation_lease=operation,
                    )
            _assert_safe_mutation_error(exc_info.value, "mutation_failed")
            assert PRIVATE_SENTINEL not in _render_exception_graph(exc_info.value)
            assert session._resource._mutation_slot is None
            assert open_calls == 0

            mutation = operation._acquire_mutation_lease()
            operation._require_active_mutation_authority()
            mutation._close()
            assert session._resource._mutation_slot is None
    finally:
        session.close()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert str(location.state_root) not in _render_exception_graph(exc_info.value)
    assert str(location.database_path) not in _render_exception_graph(exc_info.value)


def test_successful_fencing_rolls_back_closes_and_leaves_state_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_coherent_transition_fixture_for_test(
        tmp_path,
        ready_dependency=True,
        existing_event=True,
        dependencies_satisfied=False,
    )
    location = fixture.location
    session = fixture.writer_session
    writer_row_before = _writer_rows(location)
    counts_before = _state_counts(location)
    global_stop_before = _global_stop_rows(location)
    traced_sql: list[str] = []
    original_open = transaction_module._open_bound_existing_sqlite_connection

    def tracing_open(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        connection = original_open(*args, **kwargs)
        connection.set_trace_callback(traced_sql.append)
        return connection

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", tracing_open)
    try:
        with session._resource.operation_guard(session) as operation:
            result = transaction_module._run_rollback_only_writer_fencing(
                operation_lease=operation,
            )
            assert result is _WriterIssuanceMatch.MATCH
            mutation = operation._acquire_mutation_lease()
            operation._require_active_mutation_authority()
            mutation._close()
    finally:
        fixture.close()

    assert _writer_rows(location) == writer_row_before
    assert _state_counts(location) == counts_before
    assert _global_stop_rows(location) == global_stop_before
    assert transition_event_count_for_test(fixture) == counts_before["transition_events"]
    assert global_stop_event_count_for_test(fixture) == 0
    assert any(statement == "BEGIN IMMEDIATE" for statement in traced_sql)
    assert any(statement == "ROLLBACK" for statement in traced_sql)
    assert all("COMMIT" not in statement.upper() for statement in traced_sql)
    assert _run_writer_attempt(location) == "acquired:3"


@pytest.mark.parametrize(
    ("case_name", "update_factory", "expected_result", "expected_capability_calls"),
    (
        (
            "writer-ref",
            lambda row: {"writer_ref": "writer-other"},
            _WriterIssuanceMatch.STALE_WRITER,
            0,
        ),
        (
            "generation",
            lambda row: {"generation": int(row[2]) + 1},
            _WriterIssuanceMatch.STALE_WRITER,
            0,
        ),
        (
            "issued-ref",
            lambda row: {"issued_ref": "issuance-other"},
            _WriterIssuanceMatch.STALE_WRITER,
            0,
        ),
        (
            "digest",
            lambda row: {"issuance_nonce_digest": "0" * 64},
            _WriterIssuanceMatch.STALE_WRITER,
            0,
        ),
        (
            "acquired-at",
            lambda row: {"acquired_at": "2026-07-19T00:00:00Z"},
            _WriterIssuanceMatch.MATCH,
            1,
        ),
    ),
)
def test_stale_writer_variants_and_acquired_at_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case_name: str,
    update_factory: Callable[[tuple[object, ...]], dict[str, object]],
    expected_result: _WriterIssuanceMatch,
    expected_capability_calls: int,
) -> None:
    location, session = _managed_session(tmp_path / case_name)
    capability_calls = 0
    original_create = transaction_module._create_sqlite_mutation_read_capability

    def tracking_create(**kwargs: Any) -> object:
        nonlocal capability_calls
        capability_calls += 1
        return original_create(**kwargs)

    monkeypatch.setattr(transaction_module, "_create_sqlite_mutation_read_capability", tracking_create)
    try:
        original_row = _writer_rows(location)[0]
        _replace_writer_row(location, **update_factory(original_row))
        assert _run_controller(session) is expected_result
        assert capability_calls == expected_capability_calls
        assert session._resource._mutation_slot is None
        _assert_database_writable(location)
    finally:
        session.close()


@pytest.mark.parametrize(
    ("case_name", "mutate", "expected_error"),
    (
        ("missing-row", _delete_writer_row, "database_integrity_failure"),
        ("generation-zero", lambda location: _replace_writer_row(location, generation=0), "database_integrity_failure"),
        ("uppercase-digest", _set_malformed_digest, "database_integrity_failure"),
        ("schema-drift", _break_managed_schema, "database_integrity_failure"),
    ),
)
def test_missing_malformed_and_managed_schema_contradictions_are_integrity_failures(
    tmp_path: Path,
    case_name: str,
    mutate: Callable[[CoordinatorStateLocation], None],
    expected_error: str,
) -> None:
    location, session = _managed_session(tmp_path / case_name)
    try:
        mutate(location)
        _assert_controller_raises(session, expected_error, private_values=(location.database_path,))
    finally:
        session.close()


@pytest.mark.parametrize(
    "sqlite_errorcode",
    (
        _sqlite_error_code("SQLITE_BUSY", 5),
        _sqlite_error_code("SQLITE_LOCKED", 6),
        _sqlite_error_code("SQLITE_IOERR_READ", _sqlite_error_code("SQLITE_IOERR", 10)),
        _sqlite_error_code("SQLITE_INTERRUPT", 9),
        _sqlite_error_code("SQLITE_READONLY", 8),
        123456,
        None,
    ),
)
def test_managed_validation_operational_failure_is_mutation_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sqlite_errorcode: int | None,
) -> None:
    location, session = _managed_session(tmp_path / str(sqlite_errorcode))
    operational_error = _SyntheticSQLiteError(sqlite_errorcode)

    def open_faulting(*args: Any, **kwargs: Any) -> _FaultingConnection:
        return _open_faulting_connection(
            location,
            validation_execute_error=operational_error,
            validation_execute_sql_fragment="FROM sqlite_schema",
        )

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", open_faulting)
    try:
        _assert_controller_raises(session, "mutation_failed", private_values=(location.database_path,))
    finally:
        session.close()


@pytest.mark.parametrize(
    "sqlite_errorcode",
    (
        _sqlite_error_code("SQLITE_ERROR", 1),
        _sqlite_error_code("SQLITE_SCHEMA", 17),
        _sqlite_error_code("SQLITE_CORRUPT", 11),
        _sqlite_error_code("SQLITE_NOTADB", 26),
        _sqlite_error_code("SQLITE_MISMATCH", 20),
        _sqlite_error_code("SQLITE_CONSTRAINT", 19),
    ),
)
def test_managed_validation_schema_query_failure_is_integrity_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sqlite_errorcode: int,
) -> None:
    location, session = _managed_session(tmp_path / str(sqlite_errorcode))
    schema_error = _SyntheticSQLiteError(sqlite_errorcode)

    def open_faulting(*args: Any, **kwargs: Any) -> _FaultingConnection:
        return _open_faulting_connection(
            location,
            validation_execute_error=schema_error,
            validation_execute_sql_fragment="FROM sqlite_schema",
        )

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", open_faulting)
    try:
        _assert_controller_raises(session, "database_integrity_failure", private_values=(location.database_path,))
    finally:
        session.close()


def test_managed_validation_structural_error_remains_integrity_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)

    def fail_validation(connection: sqlite3.Connection) -> object:
        raise SQLiteStateError(
            SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED,
            internal_detail=PRIVATE_SENTINEL,
        )

    monkeypatch.setattr(transaction_module, "_validate_current_managed_connection", fail_validation)
    try:
        _assert_controller_raises(session, "database_integrity_failure", private_values=(location.database_path,))
    finally:
        session.close()


@pytest.mark.parametrize("fault_rows", ("multiple", "bad-singleton", "non-list", "non-tuple"))
def test_cardinality_and_tuple_fault_injection_are_integrity_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault_rows: str,
) -> None:
    location, session = _managed_session(tmp_path / fault_rows)
    valid_row = _writer_rows(location)[0]
    if fault_rows == "multiple":
        rows: object = [valid_row, valid_row]
    elif fault_rows == "bad-singleton":
        rows = [(2, *valid_row[1:])]
    elif fault_rows == "non-list":
        rows = tuple([valid_row])
    else:
        rows = [list(valid_row)]

    monkeypatch.setattr(transaction_module, "_fetch_writer_ownership_rows", lambda connection: rows)
    try:
        _assert_controller_raises(session, "database_integrity_failure")
    finally:
        session.close()


def test_open_failure_is_mutation_failed_before_transaction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)

    def fail_open(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE, internal_detail=PRIVATE_SENTINEL)

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_open)
    try:
        _assert_controller_raises(session, "mutation_failed", private_values=(location.database_path,))
    finally:
        session.close()


def test_begin_failure_closes_opened_connection_and_is_mutation_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)
    close_calls = 0
    original_close = connection_module._RetainedSQLiteConnection._close_with_proof

    def fail_begin(connection: sqlite3.Connection) -> None:
        raise RuntimeError(PRIVATE_SENTINEL)

    def tracking_close(retained: object) -> object:
        nonlocal close_calls
        close_calls += 1
        return original_close(retained)

    monkeypatch.setattr(transaction_module, "_begin_immediate", fail_begin)
    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        tracking_close,
    )
    try:
        _assert_controller_raises(session, "mutation_failed", private_values=(location.database_path,))
        assert close_calls == 1
    finally:
        session.close()


@pytest.mark.parametrize(
    "sqlite_errorcode",
    (
        _sqlite_error_code("SQLITE_BUSY", 5),
        _sqlite_error_code("SQLITE_LOCKED", 6),
        _sqlite_error_code("SQLITE_IOERR", 10),
        _sqlite_error_code("SQLITE_FULL", 13),
        _sqlite_error_code("SQLITE_INTERRUPT", 9),
        _sqlite_error_code("SQLITE_READONLY", 8),
        None,
    ),
)
def test_select_operational_failures_are_mutation_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sqlite_errorcode: int | None,
) -> None:
    location, session = _managed_session(tmp_path / str(sqlite_errorcode))
    error = _SyntheticSQLiteError(sqlite_errorcode)

    def open_faulting(*args: Any, **kwargs: Any) -> _FaultingConnection:
        return _open_faulting_connection(location, select_execute_error=error)

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", open_faulting)
    try:
        _assert_controller_raises(session, "mutation_failed")
    finally:
        session.close()


@pytest.mark.parametrize(
    "sqlite_errorcode",
    (
        _sqlite_error_code("SQLITE_ERROR", 1),
        _sqlite_error_code("SQLITE_SCHEMA", 17),
        _sqlite_error_code("SQLITE_CORRUPT", 11),
        _sqlite_error_code("SQLITE_NOTADB", 26),
        _sqlite_error_code("SQLITE_MISMATCH", 20),
        _sqlite_error_code("SQLITE_CONSTRAINT", 19),
    ),
)
def test_select_schema_query_failures_are_integrity_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sqlite_errorcode: int,
) -> None:
    location, session = _managed_session(tmp_path / str(sqlite_errorcode))
    error = _SyntheticSQLiteError(sqlite_errorcode)

    def open_faulting(*args: Any, **kwargs: Any) -> _FaultingConnection:
        return _open_faulting_connection(location, select_execute_error=error)

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", open_faulting)
    try:
        _assert_controller_raises(session, "database_integrity_failure")
    finally:
        session.close()


@pytest.mark.parametrize(
    ("case_name", "cursor", "expected_error"),
    (
        (
            "fetch-busy",
            _ScriptedCursor(fetch_error=_SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5))),
            "mutation_failed",
        ),
        (
            "fetch-schema-close-busy",
            _ScriptedCursor(
                fetch_error=_SyntheticSQLiteError(_sqlite_error_code("SQLITE_SCHEMA", 17)),
                close_error=_SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5)),
            ),
            "database_integrity_failure",
        ),
        (
            "fetch-busy-close-schema",
            _ScriptedCursor(
                fetch_error=_SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5)),
                close_error=_SyntheticSQLiteError(_sqlite_error_code("SQLITE_SCHEMA", 17)),
            ),
            "mutation_failed",
        ),
        (
            "cursor-close-busy",
            _ScriptedCursor(close_error=_SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5))),
            "mutation_failed",
        ),
        (
            "cursor-close-schema",
            _ScriptedCursor(close_error=_SyntheticSQLiteError(_sqlite_error_code("SQLITE_SCHEMA", 17))),
            "mutation_failed",
        ),
    ),
)
def test_fetch_and_cursor_close_failures_are_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case_name: str,
    cursor: _ScriptedCursor,
    expected_error: str,
) -> None:
    location, session = _managed_session(tmp_path / case_name)

    def open_faulting(*args: Any, **kwargs: Any) -> _FaultingConnection:
        return _open_faulting_connection(location, select_cursor=cursor)

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", open_faulting)
    try:
        _assert_controller_raises(session, expected_error)
        assert cursor.fetchmany_sizes == [2]
        assert cursor.close_count == 1
    finally:
        session.close()


@pytest.mark.parametrize(
    ("case_name", "patcher", "expected_error"),
    (
        (
            "capability-construction",
            lambda monkeypatch: monkeypatch.setattr(
                transaction_module,
                "_create_sqlite_mutation_read_capability",
                lambda **kwargs: (_ for _ in ()).throw(RuntimeError(PRIVATE_SENTINEL)),
            ),
            "mutation_failed",
        ),
        (
            "capability-invalidation",
            lambda monkeypatch: monkeypatch.setattr(
                transaction_module,
                "_invalidate_sqlite_mutation_read_capability",
                lambda *args, **kwargs: transaction_module._mutation_failed(),
            ),
            "mutation_failed",
        ),
        (
            "rollback",
            lambda monkeypatch: monkeypatch.setattr(
                transaction_module,
                "_rollback_transaction",
                lambda connection: transaction_module._mutation_failed(),
            ),
            "mutation_failed",
        ),
        pytest.param(
            "connection-close",
            _patch_retained_close_failure_once,
            "mutation_failed",
            id="connection-close-<lambda>-mutation_failed",
        ),
    ),
)
def test_capability_and_resolution_failures_return_mutation_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case_name: str,
    patcher: Callable[[pytest.MonkeyPatch], None],
    expected_error: str,
) -> None:
    location, session = _managed_session(tmp_path / case_name)
    patcher(monkeypatch)
    try:
        if case_name == "connection-close":
            _assert_controller_close_unproved_raises(
                session,
                expected_error,
                private_values=(location.database_path,),
            )
        else:
            _assert_controller_raises(session, expected_error, private_values=(location.database_path,))
    finally:
        session.close()


def test_rollback_and_close_failures_supersede_planned_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rollback_location, rollback_session = _managed_session(tmp_path / "rollback-precedence")
    _delete_writer_row(rollback_location)
    with monkeypatch.context() as rollback_patch:
        rollback_patch.setattr(
            transaction_module,
            "_rollback_transaction",
            lambda connection: transaction_module._mutation_failed(),
        )
        try:
            _assert_controller_raises(rollback_session, "mutation_failed")
        finally:
            rollback_session.close()

    close_location, close_session = _managed_session(tmp_path / "close-precedence")
    _replace_writer_row(close_location, writer_ref="writer-other")
    with monkeypatch.context() as close_patch:
        _patch_retained_close_failure_once(close_patch)
        try:
            _assert_controller_close_unproved_raises(close_session, "mutation_failed")
        finally:
            close_session.close()


def test_admitted_controller_close_failure_remains_mutation_failed_after_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)
    resource = session._resource
    original_open = transaction_module._open_bound_existing_sqlite_connection
    original_close = connection_module._RetainedSQLiteConnection._close_with_proof
    opened_connections: list[sqlite3.Connection] = []
    close_calls = 0
    result: _WriterIssuanceMatch | None = None

    def tracking_open(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        connection = original_open(*args, **kwargs)
        opened_connections.append(connection)
        return connection

    def fail_once_before_close_proof(retained: object) -> object:
        nonlocal close_calls
        close_calls += 1
        if close_calls == 1:
            raise RuntimeError(PRIVATE_SENTINEL)
        return original_close(retained)

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", tracking_open)
    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        fail_once_before_close_proof,
    )
    try:
        with resource.operation_guard(session) as operation:
            with pytest.raises(SQLiteMutationStoreError) as exc_info:
                result = transaction_module._run_rollback_only_writer_fencing(
                    operation_lease=operation,
                )
            _assert_safe_mutation_error(exc_info.value, "mutation_failed")
            assert result is None
            assert close_calls == 1
            assert len(opened_connections) == 1
            assert resource._state == "abort_close_unproved"
            assert resource._mutation_slot is not None
            with pytest.raises(WriterSessionError) as unavailable:
                operation._acquire_mutation_lease()
            assert unavailable.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED
    finally:
        session.close()
    assert close_calls == 2
    _assert_sqlite_connection_closed(opened_connections[0])


def test_capability_borrow_lifecycle_process_thread_and_privacy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location, session = _managed_session(tmp_path)
    original_create = transaction_module._create_sqlite_mutation_read_capability
    original_rollback = transaction_module._rollback_transaction
    captured: dict[str, object] = {}
    wrong_thread_results: list[_MutationReadCapabilityError] = []
    invalidated_before_rollback = False

    def capture_create(**kwargs: Any) -> object:
        capability = original_create(**kwargs)
        captured["capability"] = capability
        borrowed = capability._borrow_connection_for_select()
        captured["borrowed"] = borrowed
        assert borrowed is kwargs["connection"]
        assert borrowed.in_transaction is True

        def wrong_thread_borrow() -> None:
            try:
                capability._borrow_connection_for_select()
            except _MutationReadCapabilityError as exc:
                wrong_thread_results.append(exc)

        thread = threading.Thread(target=wrong_thread_borrow)
        thread.start()
        _join_thread(thread)

        read_fd, write_fd = os.pipe()
        child_pid = os.fork()
        if child_pid == 0:
            os.close(read_fd)
            try:
                try:
                    capability._borrow_connection_for_select()
                except _MutationReadCapabilityError as exc:
                    result = exc.reason.value
                else:
                    result = "unexpected-borrow"
                os.write(write_fd, result.encode("ascii"))
            finally:
                os.close(write_fd)
                os._exit(0)

        os.close(write_fd)
        try:
            captured["child_result"] = _wait_for_child_result(child_pid, read_fd)
        finally:
            os.close(read_fd)
        return capability

    def checking_rollback(connection: sqlite3.Connection) -> SQLiteMutationStoreError | None:
        nonlocal invalidated_before_rollback
        capability = captured["capability"]
        with pytest.raises(_MutationReadCapabilityError) as exc_info:
            capability._borrow_connection_for_select()
        _assert_capability_error(exc_info.value, _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED)
        invalidated_before_rollback = True
        return original_rollback(connection)

    monkeypatch.setattr(transaction_module, "_create_sqlite_mutation_read_capability", capture_create)
    monkeypatch.setattr(transaction_module, "_rollback_transaction", checking_rollback)
    try:
        assert _run_controller(session) is _WriterIssuanceMatch.MATCH
        assert invalidated_before_rollback is True
        assert len(wrong_thread_results) == 1
        _assert_capability_error(
            wrong_thread_results[0],
            _MutationReadCapabilityFailureReason.THREAD_MISMATCH,
        )
        assert captured["child_result"] == _MutationReadCapabilityFailureReason.PROCESS_MISMATCH.value
        capability = captured["capability"]
        assert repr(capability) == "<_SQLiteMutationReadCapability>"
        assert "Connection" not in repr(capability)
        assert "epoch" not in repr(capability).lower()
        assert not hasattr(capability, "connection")
        assert not hasattr(capability, "epoch")
        assert not hasattr(capability, "close")
        assert not hasattr(capability, "_finalizer")
        with pytest.raises(TypeError):
            pickle.dumps(capability)
        with pytest.raises(_MutationReadCapabilityError) as expired:
            capability._borrow_connection_for_select()
        _assert_capability_error(expired.value, _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED)
    finally:
        session.close()


def test_capability_remains_expired_during_later_controller_transaction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)
    original_create = transaction_module._create_sqlite_mutation_read_capability
    captured: list[object] = []

    def capture_create(**kwargs: Any) -> object:
        capability = original_create(**kwargs)
        if captured:
            with pytest.raises(_MutationReadCapabilityError) as old_error:
                captured[0]._borrow_connection_for_select()
            _assert_capability_error(old_error.value, _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED)
        captured.append(capability)
        return capability

    monkeypatch.setattr(transaction_module, "_create_sqlite_mutation_read_capability", capture_create)
    try:
        assert _run_controller(session) is _WriterIssuanceMatch.MATCH
        assert _run_controller(session) is _WriterIssuanceMatch.MATCH
        assert len(captured) == 2
    finally:
        session.close()


def test_malformed_capability_state_is_unavailable_while_controller_state_still_cleans_up(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)
    original_create = transaction_module._create_sqlite_mutation_read_capability
    captured: dict[str, object] = {}

    def capture_and_malformed_state(**kwargs: Any) -> object:
        capability = original_create(**kwargs)
        capability._state = object()
        with pytest.raises(_MutationReadCapabilityError) as exc_info:
            capability._borrow_connection_for_select()
        _assert_capability_error(
            exc_info.value,
            _MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE,
        )
        captured["capability"] = capability
        return capability

    monkeypatch.setattr(transaction_module, "_create_sqlite_mutation_read_capability", capture_and_malformed_state)
    try:
        assert _run_controller(session) is _WriterIssuanceMatch.MATCH
    finally:
        session.close()


def test_mutation_slot_contention_is_prompt_and_before_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)
    resource = session._resource
    original_open = transaction_module._open_bound_existing_sqlite_connection
    first_open_started = threading.Event()
    release_first_open = threading.Event()
    first_result: list[object] = []
    first_errors: list[BaseException] = []
    open_calls = 0
    open_lock = threading.Lock()

    def blocking_open(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        nonlocal open_calls
        with open_lock:
            open_calls += 1
            call_number = open_calls
        if call_number == 1:
            first_open_started.set()
            _wait_for_event(release_first_open, timeout=5.0)
        return original_open(*args, **kwargs)

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", blocking_open)

    def run_first() -> None:
        try:
            with resource.operation_guard(session) as operation:
                first_result.append(
                    transaction_module._run_rollback_only_writer_fencing(
                        operation_lease=operation,
                    )
                )
        except BaseException as exc:
            first_errors.append(exc)

    thread = threading.Thread(target=run_first)
    thread.start()
    _wait_for_event(first_open_started)
    assert resource._mutation_slot is not None
    with resource.operation_guard(session) as second_operation:
        started = time.monotonic()
        with pytest.raises(WriterSessionError) as contention:
            transaction_module._run_rollback_only_writer_fencing(
                operation_lease=second_operation,
            )
        assert time.monotonic() - started < 0.5
        assert contention.value.reason is WriterSessionFailureReason.WRITER_SESSION_MUTATION_IN_PROGRESS
    assert open_calls == 1
    release_first_open.set()
    _join_thread(thread, timeout=5.0)
    assert first_errors == []
    assert first_result == [_WriterIssuanceMatch.MATCH]
    assert resource._mutation_slot is None
    session.close()


def test_same_thread_nested_controller_fails_before_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)
    open_calls = 0

    def fail_if_open(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        nonlocal open_calls
        open_calls += 1
        raise AssertionError("nested controller opened SQLite")

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_if_open)
    try:
        with session._resource.operation_guard(session) as operation:
            mutation = operation._acquire_mutation_lease()
            with pytest.raises(WriterSessionError) as nested:
                transaction_module._run_rollback_only_writer_fencing(
                    operation_lease=operation,
                )
            assert nested.value.reason is WriterSessionFailureReason.WRITER_SESSION_MUTATION_IN_PROGRESS
            assert open_calls == 0
            operation._require_active_mutation_authority()
            mutation._close()
    finally:
        session.close()


def test_mutation_slot_is_held_through_connection_close_and_outer_operation_remains_active(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)
    resource = session._resource
    original_close = connection_module._RetainedSQLiteConnection._close_with_proof
    slot_seen_during_close = False

    def checking_close(retained: object) -> object:
        nonlocal slot_seen_during_close
        assert resource._mutation_slot is not None
        slot_seen_during_close = True
        return original_close(retained)

    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        checking_close,
    )
    try:
        with resource.operation_guard(session) as operation:
            assert transaction_module._run_rollback_only_writer_fencing(
                operation_lease=operation,
            ) is _WriterIssuanceMatch.MATCH
            assert slot_seen_during_close is True
            assert resource._mutation_slot is None
            mutation = operation._acquire_mutation_lease()
            operation._require_active_mutation_authority()
            mutation._close()
    finally:
        session.close()


def test_session_close_waits_for_controller_operation_to_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)
    resource = session._resource
    original_close_connection = connection_module._RetainedSQLiteConnection._close_with_proof
    close_done = threading.Event()
    close_errors: list[BaseException] = []
    closer_started = False

    def tracking_connection_close(retained: object) -> object:
        nonlocal closer_started
        if not closer_started:
            closer_started = True

            def close_session() -> None:
                try:
                    session.close()
                except BaseException as exc:
                    close_errors.append(exc)
                finally:
                    close_done.set()

            closer = threading.Thread(target=close_session)
            closer.start()
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                with resource._condition:
                    if resource._state == writer_module._CLOSING:
                        break
                time.sleep(0.01)
            assert resource._state == writer_module._CLOSING
            assert close_done.is_set() is False
            tracking_connection_close.closer = closer
        return original_close_connection(retained)

    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        tracking_connection_close,
    )
    with resource.operation_guard(session) as operation:
        assert transaction_module._run_rollback_only_writer_fencing(
            operation_lease=operation,
        ) is _WriterIssuanceMatch.MATCH
        assert close_done.is_set() is False

    closer = tracking_connection_close.closer
    _join_thread(closer, timeout=5.0)
    assert close_errors == []
    assert close_done.is_set()
    assert resource._state == writer_module._CLOSED
    assert session.active is False
    assert _run_writer_attempt(location) == "acquired:2"


def test_no_b3b2_reader_calls_and_no_durable_mutation_sql(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reader_calls: list[str] = []

    def fail_reader(*args: Any, **kwargs: Any) -> None:
        reader_calls.append("called")
        raise AssertionError("B3b2 reader was called")

    for name in (
        "_read_current_work_item",
        "_read_lease_identity_record",
        "_read_authorization_receipt",
        "_read_dependency_receipt",
        "_read_admitted_backlog",
        "_read_global_stop_current",
    ):
        monkeypatch.setattr(read_scope, name, fail_reader)

    location, session = _managed_session(tmp_path)
    try:
        assert _run_controller(session) is _WriterIssuanceMatch.MATCH
        assert reader_calls == []
    finally:
        session.close()

    module_source = TRANSACTION_MODULE_PATH.read_text(encoding="utf-8")
    source = inspect.getsource(transaction_module._run_rollback_only_writer_fencing) + inspect.getsource(
        transaction_module._CoordinatorMutationTransactionController._run_until_writer_fencing_resolution
    )
    for forbidden in (
        "INSERT",
        "UPDATE",
        "DELETE",
        "COMMIT",
        "transition_events",
        "global_stop_events",
        "work_items",
        "global_stop_current",
        "_read_current_work_item",
        "_read_lease_identity_record",
        "_read_authorization_receipt",
        "_read_dependency_receipt",
        "_read_admitted_backlog",
        "_read_global_stop_current",
    ):
        assert forbidden not in source
    assert module_source.count("BEGIN IMMEDIATE") == 1
    assert module_source.count('connection.execute("ROLLBACK")') == 1
    assert EXPECTED_WRITER_ROW_QUERY in module_source


def test_public_transition_preflight_delegates_without_rollback_only_fencing_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)
    controller_calls = 0
    sqlite_calls = 0

    def fail_controller(*args: Any, **kwargs: Any) -> object:
        nonlocal controller_calls
        controller_calls += 1
        raise AssertionError("public method reached B3c1b controller")

    def fail_sqlite_open(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        nonlocal sqlite_calls
        sqlite_calls += 1
        raise AssertionError("public method opened SQLite")

    monkeypatch.setattr(transaction_module, "_run_rollback_only_writer_fencing", fail_controller)
    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_sqlite_open)
    monkeypatch.setattr(writer_module, "open_existing_sqlite_connection", fail_sqlite_open)
    try:
        with pytest.raises(TransitionApplyPreflightError) as transition_error:
            session.apply_transition(None)  # type: ignore[arg-type]
        assert transition_error.value.reason is TransitionApplyPreflightFailureReason.INVALID_COMMAND

        with pytest.raises(GlobalStopApplyPreflightError) as global_stop_error:
            session.apply_global_stop_update(None, None)  # type: ignore[arg-type]
        assert global_stop_error.value.reason is GlobalStopApplyPreflightFailureReason.INVALID_COMMAND
        assert controller_calls == 0
        assert sqlite_calls == 0
    finally:
        session.close()

    assert "_run_rollback_only_writer_fencing" not in ge_nwp_coordinator.__all__
    assert "_CoordinatorMutationTransactionController" not in ge_nwp_coordinator.__all__
    assert "_SQLiteMutationReadCapability" not in ge_nwp_coordinator.__all__
    assert not hasattr(ge_nwp_coordinator, "_run_rollback_only_writer_fencing")
    assert not hasattr(ge_nwp_coordinator, "_SQLiteMutationReadCapability")
    assert not hasattr(StateStore, "apply_transition")
    assert not hasattr(StateStore, "apply_global_stop_update")
    production_source = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE_DIR.glob("*.py"))
    assert "make_coherent_transition_fixture_for_test" not in production_source


def test_invalid_private_inputs_and_constructor_keys_fail_safely(tmp_path: Path) -> None:
    _location, session = _managed_session(tmp_path)
    try:
        with session._resource.operation_guard(session) as operation:
            with pytest.raises(SQLiteMutationStoreError) as bad_operation:
                transaction_module._run_rollback_only_writer_fencing(
                    operation_lease=object(),  # type: ignore[arg-type]
                )
            _assert_safe_mutation_error(bad_operation.value, "mutation_failed")

            with pytest.raises(SQLiteMutationStoreError) as bad_controller_key:
                transaction_module._CoordinatorMutationTransactionController(
                    key=object(),
                    operation_lease=operation,
                )
            _assert_safe_mutation_error(bad_controller_key.value, "mutation_failed")
    finally:
        session.close()


def test_controller_process_mismatch_in_fork_child_fails_before_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location, session = _managed_session(tmp_path)
    sqlite_open_calls = 0

    def fail_if_open(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        nonlocal sqlite_open_calls
        sqlite_open_calls += 1
        raise AssertionError("fork child opened SQLite")

    monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_if_open)
    operation = session._resource.operation_guard(session)
    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        try:
            try:
                transaction_module._run_rollback_only_writer_fencing(
                    operation_lease=operation,
                )
            except WriterSessionError as exc:
                result = exc.reason.value
            except SQLiteMutationStoreError as exc:
                result = exc.error_class
            else:
                result = "unexpected-result"
            os.write(write_fd, result.encode("ascii"))
        finally:
            os.close(write_fd)
            os._exit(0)

    os.close(write_fd)
    try:
        child_result = _wait_for_child_result(child_pid, read_fd)
    finally:
        os.close(read_fd)
        operation._close()
        session.close()
    assert child_result == WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH.value
    assert sqlite_open_calls == 0
    assert _run_writer_attempt(location) == "acquired:2"


def test_temp_state_root_is_removable_after_controller_error(tmp_path: Path) -> None:
    location, session = _managed_session(tmp_path / "removable")
    state_root = location.state_root
    try:
        _delete_writer_row(location)
        _assert_controller_raises(session, "database_integrity_failure")
    finally:
        session.close()
    shutil.rmtree(state_root)
    assert not state_root.exists()


def test_new_module_is_private_unexported_and_static_shape_is_closed() -> None:
    assert TRANSACTION_MODULE_PATH.exists()
    source = TRANSACTION_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert "_CoordinatorMutationTransactionController" in class_names
    assert "_RollbackOnlyTransitionTransactionController" not in class_names
    assert "_SQLiteMutationReadCapability" in class_names
    assert "_MutationCapabilityState" in class_names
    assert "_run_rollback_only_writer_fencing" in function_names
    assert "_run_atomic_transition_apply" in function_names
    assert "def for_test" not in source
    assert "controller_for_test" not in source
    assert "capability_for_test" not in source
    assert "__all__" not in source
    assert "sqlite_transition_transaction" not in ge_nwp_coordinator.__all__
    assert "sqlite_transition_transaction" not in (PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8")
    assert sorted(path.name for path in (PACKAGE_DIR / "sqlite_migrations").glob("*.sql")) == [
        "0001_initial.sql",
        "0002_development_program_and_effect_state.sql",
        "0003_cognitive_proposal_and_selection_state.sql",
    ]
def test_open_faulting_connection_setup_baseexception_closes_exact_local_connection_and_preserves_primary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)
    session.close()
    opened: list[_FaultingConnection] = []
    original_connect = sqlite3.connect
    primary = KeyboardInterrupt()
    synthetic_close = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5))
    ledger = _FaultingConnectionLedger()

    def tracking_connect(*args: object, **kwargs: object) -> _FaultingConnection:
        connection = original_connect(*args, **kwargs)
        assert type(connection) is _FaultingConnection
        opened.append(connection)
        return connection

    def fail_setup(connection: sqlite3.Connection, **kwargs: object) -> None:
        del kwargs
        assert type(connection) is _FaultingConnection
        connection.close_error = synthetic_close
        raise primary

    monkeypatch.setattr(sqlite3, "connect", tracking_connect)
    # Patch the exact module-global used by the helper.
    monkeypatch.setitem(
        _open_faulting_connection.__globals__,
        "apply_observational_connection_posture",
        fail_setup,
    )

    with pytest.raises(KeyboardInterrupt) as captured:
        _open_faulting_connection(location, ownership_ledger=ledger)
    assert captured.value is primary
    assert primary.__cause__ is None
    assert primary.__context__ is None
    assert len(opened) == 1
    assert opened[0].close_count == 1
    _assert_sqlite_connection_closed(opened[0])
    assert ledger.connections == ()


def test_fault_ledger_assertion_exit_runs_idempotent_exact_cleanup(
    tmp_path: Path,
) -> None:
    location, session = _managed_session(tmp_path)
    session.close()
    adopted = _open_faulting_connection(location)
    unrelated = _open_faulting_connection(location)
    ledger = _FaultingConnectionLedger()
    ledger.adopt(adopted)
    with pytest.raises(AssertionError, match="intentional assertion exit"):
        with ExitStack() as resources:
            resources.callback(ledger.cleanup)
            raise AssertionError("intentional assertion exit")
    _assert_sqlite_connection_closed(adopted)
    assert unrelated.execute("SELECT 1").fetchone() == (1,)
    close_count = adopted.close_count
    ledger.cleanup()
    assert adopted.close_count == close_count
    unrelated.close()


def test_fault_ledger_expected_error_mismatch_runs_idempotent_exact_cleanup(
    tmp_path: Path,
) -> None:
    location, session = _managed_session(tmp_path)
    session.close()
    adopted = _open_faulting_connection(location)
    ledger = _FaultingConnectionLedger()
    ledger.adopt(adopted)
    mismatch: BaseException | None = None
    try:
        with ExitStack() as resources:
            resources.callback(ledger.cleanup)
            with pytest.raises(ValueError):
                pass
    except BaseException as exc:
        mismatch = exc
    assert mismatch is not None
    _assert_sqlite_connection_closed(adopted)
    count = adopted.close_count
    ledger.cleanup()
    assert adopted.close_count == count


def test_fault_ledger_close_unproved_until_cleanup_is_exact_idempotent_and_warning_clean(
    tmp_path: Path,
) -> None:
    location, session = _managed_session(tmp_path)
    session.close()
    synthetic_close = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5))
    connection = _open_faulting_connection(location, close_error=synthetic_close)
    ledger = _FaultingConnectionLedger()
    ledger.adopt(connection)
    with ExitStack() as resources:
        resources.callback(ledger.cleanup)
        with pytest.raises(_SyntheticSQLiteError) as close_failure:
            connection.close()
        assert close_failure.value is synthetic_close
        assert connection.execute("SELECT 1").fetchone() == (1,)
        assert connection.close_count == 1
    _assert_sqlite_connection_closed(connection)
    assert connection.close_count == 2
    ledger.cleanup()
    assert connection.close_count == 2
    assert type(gc.collect()) is int
