from __future__ import annotations

import ast
from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
import traceback
from typing import Any

import pytest

import ge_nwp_coordinator
from ge_nwp_coordinator import StateStore
from ge_nwp_coordinator.backlog import BACKLOG_SCHEMA_ID, FiniteBacklog, WorkItem
from ge_nwp_coordinator.canonicalization import canonical_json_bytes, canonical_sha256
from ge_nwp_coordinator.global_stop import GLOBAL_STOP_SCHEMA_ID
from ge_nwp_coordinator.lease import (
    AUTHORIZATION_DECISION_SCHEMA_ID,
    CANONICALIZATION_ID,
    LEASE_SCHEMA_ID,
    LeaseRevocationState,
    Permission,
    StandingLease,
    UnsupportedAuthorizationProvider,
)
from ge_nwp_coordinator.persistence_contracts import (
    AdmittedBacklogRecordEnvelope,
    AuthorizationReceiptEnvelope,
    DependencyReceiptEnvelope,
    GlobalStopCurrentRecordEnvelope,
    LeaseIdentityRecordEnvelope,
    WorkItemRecordEnvelope,
    encode_sqlite_boolean,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_transition_read_scope import (
    _ADMITTED_BACKLOG_SELECT,
    _AUTHORIZATION_RECEIPT_SELECT,
    _CURRENT_WORK_ITEM_SELECT,
    _DEPENDENCY_RECEIPT_SELECT,
    _GLOBAL_STOP_CURRENT_SELECT,
    _LEASE_IDENTITY_SELECT,
    _SelectQuerySpec,
    _read_admitted_backlog,
    _read_authorization_receipt,
    _read_current_work_item,
    _read_dependency_receipt,
    _read_global_stop_current,
    _read_lease_identity_record,
)
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _TransitionReadCapabilityError,
    _TransitionReadCapabilityFailureReason,
)
from ge_nwp_coordinator import sqlite_transition_read_scope as read_scope
from ge_nwp_coordinator.state_machine import (
    DEPENDENCY_DECISION_SCHEMA_ID,
    WORK_ITEM_STATE_SCHEMA_ID,
    DependencyDecision,
    WorkItemRecord,
    WorkItemState,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
READ_SCOPE_PATH = PACKAGE_DIR / "sqlite_transition_read_scope.py"
SELECT_SUPPORT_PATH = PACKAGE_DIR / "sqlite_transition_select_support.py"
CANONICAL_TIMESTAMP = "2026-07-14T00:00:03Z"
PRIVATE_SQLITE_SENTINEL = "PRIVATE-SQLITE-SENTINEL-DO-NOT-LEAK-314159"
PRIVATE_CAPABILITY_SENTINEL = "PRIVATE-CAPABILITY-SENTINEL-DO-NOT-LEAK-271828"


class _RecordingConnection(sqlite3.Connection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.execute_calls: list[tuple[str, tuple[Any, ...]]] = []
        self.close_count = 0
        self.scripted_cursor: _ScriptedCursor | None = None
        self.scripted_execute_error: sqlite3.Error | None = None

    def execute(self, sql: str, parameters: Any = (), /) -> Any:
        parameter_tuple = tuple(parameters) if parameters is not None else ()
        self.execute_calls.append((sql, parameter_tuple))
        if self.scripted_execute_error is not None:
            raise self.scripted_execute_error
        if self.scripted_cursor is not None:
            return self.scripted_cursor
        return super().execute(sql, parameters)

    def close(self) -> None:
        self.close_count += 1
        super().close()


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


class _CustomSequence:
    def __init__(self, values: tuple[Any, ...]) -> None:
        self._values = values

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self) -> Any:
        return iter(self._values)

    def __getitem__(self, index: int) -> Any:
        return self._values[index]


class _SyntheticSQLiteError(sqlite3.DatabaseError):
    def __init__(self, sqlite_errorcode: int | None) -> None:
        super().__init__(PRIVATE_SQLITE_SENTINEL)
        if sqlite_errorcode is not None:
            self.sqlite_errorcode = sqlite_errorcode


class _TestsOnlyTransitionReadCapabilityEpoch:
    """Tests-only structural capability epoch, not production authority."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._generation = 0
        self._active = False

    def start_for_test(self) -> "_TestsOnlyTransitionReadCapability":
        self._generation += 1
        self._active = True
        return _TestsOnlyTransitionReadCapability(self, self._generation)

    def end_for_test(self) -> None:
        self._active = False

    def _connection_for_generation(self, generation: int) -> sqlite3.Connection:
        if not self._active or generation != self._generation:
            raise _TransitionReadCapabilityError(_TransitionReadCapabilityFailureReason.CAPABILITY_EXPIRED)
        return self._connection


class _TestsOnlyTransitionReadCapability:
    """Clearly test-only structural stand-in for the future B3c capability."""

    def __init__(self, epoch: _TestsOnlyTransitionReadCapabilityEpoch, generation: int) -> None:
        self._epoch = epoch
        self._generation = generation
        self.borrow_count = 0

    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        self.borrow_count += 1
        return self._epoch._connection_for_generation(self._generation)


class _WrongConnectionCapability:
    def _borrow_connection_for_select(self) -> object:
        return object()


class _UnknownExceptionCapability:
    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        try:
            raise ValueError(PRIVATE_CAPABILITY_SENTINEL)
        except ValueError as cause:
            error = RuntimeError(PRIVATE_CAPABILITY_SENTINEL)
            error.add_note(PRIVATE_CAPABILITY_SENTINEL)
            raise error from cause


@dataclass(frozen=True)
class _ReaderCase:
    reader_name: str
    spec: _SelectQuerySpec
    lookup_value: str | None
    row_factory: Callable[[], dict[str, object]]
    envelope_type: type[object]
    adapter_name: str


def _item(
    work_item_id: str = "wi-1",
    *,
    dependencies: tuple[str, ...] = (),
    api_calls: int = 1,
    compute_seconds: int = 10,
) -> WorkItem:
    return WorkItem(
        work_item_id=work_item_id,
        objective_label=f"{work_item_id} objective",
        opaque_private_assignment_ref=f"assignment-{work_item_id}",
        repo="coordinator-local",
        branches=("trunk_dev",),
        allowed_paths=("src", "tests"),
        task_class="code",
        risk_lane="low",
        required_validation_profile="unit-tests",
        budget_allocation={"api_calls": api_calls, "compute_seconds": compute_seconds},
        dependencies=dependencies,
        stop_conditions=("global-stop",),
    )


def _backlog(**overrides: object) -> FiniteBacklog:
    fields = {
        "schema_id": BACKLOG_SCHEMA_ID,
        "schema_version": 1,
        "backlog_id": "backlog-a2-p1",
        "lease_reference": "lease-a2-p1",
        "work_items": (_item(), _item("wi-2", dependencies=("wi-1",), api_calls=2, compute_seconds=20)),
        "content_digest": "0" * 64,
    }
    fields.update(overrides)
    return FiniteBacklog(**fields).with_digest()


def _lease(backlog: FiniteBacklog | None = None, **overrides: object) -> StandingLease:
    backlog = backlog or _backlog()
    fields = {
        "schema_id": LEASE_SCHEMA_ID,
        "schema_version": 1,
        "lease_id": "lease-a2-p1",
        "issuer_label": "operator-policy",
        "issued_at": "2026-07-14T00:00:00Z",
        "valid_from": "2026-07-14T00:00:01Z",
        "expires_at": "2026-07-15T00:00:00Z",
        "revocation_state": LeaseRevocationState.NOT_REVOKED,
        "revocation_reference": None,
        "subject": "nwp-coordinator-p1",
        "repo_identity": {"component": "nwp-coordinator", "repo_label": "coordinator-local"},
        "branch_policy": {"base": "trunk_dev", "mode": "operator-approved"},
        "allowed_paths": ("src", "tests"),
        "forbidden_path_policy_identity": "governed-execution.nwp-forbidden-paths.v1",
        "task_classes": ("docs", "code"),
        "risk_lanes": ("low",),
        "finite_backlog_reference": backlog.backlog_id,
        "finite_backlog_digest": backlog.content_digest,
        "max_work_items": 3,
        "max_concurrency": 1,
        "max_attempts": 2,
        "max_repairs": 1,
        "compute_api_budget": {"api_calls": 3, "compute_seconds": 30},
        "wall_clock_budget_seconds": 3600,
        "validation_requirements": ("unit-tests",),
        "audit_requirements": ("boundary-audit",),
        "local_commit_permission": Permission.FORBIDDEN,
        "publication_permission": Permission.FORBIDDEN,
        "cross_repo_permission": Permission.FORBIDDEN,
        "maintenance_permission": Permission.FORBIDDEN,
        "cleanup_requirements": ("no-worker-artifacts",),
        "reporting_cadence": "on-transition",
        "retention_policy": "safe-projections-only",
        "global_stop_reference": "operator-global-stop",
        "canonical_digest_metadata": {"algorithm": "sha256", "canonicalization": CANONICALIZATION_ID},
        "authorization_mechanism": {"kind": "unsupported", "descriptor": "p1-fail-closed"},
    }
    fields.update(overrides)
    return StandingLease(**fields).with_digest()


def _record(**overrides: object) -> WorkItemRecord:
    fields = {
        "schema_id": WORK_ITEM_STATE_SCHEMA_ID,
        "work_item_id": "wi-1",
        "lease_id": "lease-a2-p1",
        "backlog_id": "backlog-a2-p1",
        "state": WorkItemState.LEASE_ADMITTED,
        "version": 3,
        "attempt_count": 1,
        "repair_count": 0,
        "budget_consumed": 0,
        "budget_limit": 0,
        "max_attempts": 2,
        "max_repairs": 1,
        "cleanup_required": False,
    }
    fields.update(overrides)
    return WorkItemRecord(**fields)


def _lease_identity_row() -> dict[str, object]:
    lease = _lease()
    validation = lease.validate_identity()
    return {
        "decision_ref": validation.decision_ref,
        "lease_ref": validation.lease_ref,
        "identity_valid": encode_sqlite_boolean(validation.identity_valid, "lease_identity_record.identity_valid"),
        "lease_digest": validation.digest,
        "schema_id": LEASE_SCHEMA_ID,
        "canonical_json": canonical_json_bytes(lease.to_dict()).decode("utf-8"),
        "canonical_digest": canonical_sha256(lease.to_dict()),
        "created_at": CANONICAL_TIMESTAMP,
    }


def _authorization_row() -> dict[str, object]:
    decision = UnsupportedAuthorizationProvider().authorize(_lease())
    return {
        "decision_ref": decision.decision_ref,
        "lease_ref": decision.lease_ref,
        "lease_identity_decision_ref": decision.lease_identity_decision_ref,
        "lease_identity_valid": encode_sqlite_boolean(
            decision.lease_identity_valid,
            "authorization_receipt.lease_identity_valid",
        ),
        "authorization_model": decision.authorization_model.value,
        "authorized": encode_sqlite_boolean(decision.authorized, "authorization_receipt.authorized"),
        "executable": encode_sqlite_boolean(decision.executable, "authorization_receipt.executable"),
        "reason": decision.reason,
        "schema_id": AUTHORIZATION_DECISION_SCHEMA_ID,
        "canonical_json": decision.canonical_json(),
        "canonical_digest": decision.canonical_digest(),
        "created_at": CANONICAL_TIMESTAMP,
    }


def _dependency_row() -> dict[str, object]:
    decision = DependencyDecision(decision_ref="deps-ready", work_item_id="wi-1")
    return {
        "decision_ref": decision.decision_ref,
        "work_item_id": decision.work_item_id,
        "dependencies_satisfied": encode_sqlite_boolean(
            decision.dependencies_satisfied,
            "dependency_receipt.dependencies_satisfied",
        ),
        "reason": decision.reason,
        "schema_id": DEPENDENCY_DECISION_SCHEMA_ID,
        "canonical_json": decision.canonical_json(),
        "canonical_digest": decision.canonical_digest(),
        "created_at": CANONICAL_TIMESTAMP,
    }


def _work_item_row() -> dict[str, object]:
    record = _record()
    row = {**record.to_dict(), "updated_at": CANONICAL_TIMESTAMP}
    row["state"] = record.state.value
    row["cleanup_required"] = encode_sqlite_boolean(record.cleanup_required, "work_item_row.cleanup_required")
    return row


def _admitted_backlog_row() -> dict[str, object]:
    backlog = _backlog()
    return {
        "backlog_id": backlog.backlog_id,
        "lease_ref": backlog.lease_reference,
        "schema_id": backlog.schema_id,
        "schema_version": backlog.schema_version,
        "content_digest": backlog.content_digest,
        "canonical_json": canonical_json_bytes(backlog.to_dict()).decode("utf-8"),
        "admitted_at": CANONICAL_TIMESTAMP,
    }


def _global_stop_clear_row() -> dict[str, object]:
    return {
        "singleton_id": 1,
        "schema_id": GLOBAL_STOP_SCHEMA_ID,
        "version": 0,
        "active": 0,
        "stop_id": None,
        "reason_class": None,
        "issuer_ref": None,
        "issued_at": None,
        "operator_decision_ref": None,
        "updated_at": "1970-01-01T00:00:00Z",
    }


READER_CASES = (
    _ReaderCase(
        "_read_current_work_item",
        _CURRENT_WORK_ITEM_SELECT,
        "wi-1",
        _work_item_row,
        WorkItemRecordEnvelope,
        "work_item_record_envelope_from_row",
    ),
    _ReaderCase(
        "_read_lease_identity_record",
        _LEASE_IDENTITY_SELECT,
        "lease-identity-lease-a2-p1",
        _lease_identity_row,
        LeaseIdentityRecordEnvelope,
        "lease_identity_record_envelope_from_row",
    ),
    _ReaderCase(
        "_read_authorization_receipt",
        _AUTHORIZATION_RECEIPT_SELECT,
        "authz-lease-a2-p1",
        _authorization_row,
        AuthorizationReceiptEnvelope,
        "authorization_receipt_envelope_from_row",
    ),
    _ReaderCase(
        "_read_dependency_receipt",
        _DEPENDENCY_RECEIPT_SELECT,
        "deps-ready",
        _dependency_row,
        DependencyReceiptEnvelope,
        "dependency_receipt_envelope_from_row",
    ),
    _ReaderCase(
        "_read_admitted_backlog",
        _ADMITTED_BACKLOG_SELECT,
        "backlog-a2-p1",
        _admitted_backlog_row,
        AdmittedBacklogRecordEnvelope,
        "admitted_backlog_record_envelope_from_row",
    ),
    _ReaderCase(
        "_read_global_stop_current",
        _GLOBAL_STOP_CURRENT_SELECT,
        None,
        _global_stop_clear_row,
        GlobalStopCurrentRecordEnvelope,
        "global_stop_current_envelope_from_row",
    ),
)
OPTIONAL_READER_CASES = tuple(case for case in READER_CASES if case.lookup_value is not None)
READER_NAMES = frozenset(case.reader_name for case in READER_CASES)


def _connect() -> _RecordingConnection:
    return sqlite3.connect(":memory:", factory=_RecordingConnection)


def _scripted_connection(
    *,
    rows: tuple[Any, ...] = (),
    execute_error: sqlite3.Error | None = None,
    fetch_error: sqlite3.Error | None = None,
    close_error: sqlite3.Error | None = None,
) -> tuple[_RecordingConnection, _ScriptedCursor | None]:
    connection = _connect()
    if execute_error is not None:
        connection.scripted_execute_error = execute_error
        return connection, None
    cursor = _ScriptedCursor(rows, fetch_error=fetch_error, close_error=close_error)
    connection.scripted_cursor = cursor
    return connection, cursor


def _capability_for(connection: sqlite3.Connection) -> tuple[_TestsOnlyTransitionReadCapabilityEpoch, _TestsOnlyTransitionReadCapability]:
    epoch = _TestsOnlyTransitionReadCapabilityEpoch(connection)
    return epoch, epoch.start_for_test()


def _create_table(connection: sqlite3.Connection, spec: _SelectQuerySpec) -> None:
    columns_sql = ", ".join(spec.columns)
    connection.execute(f"CREATE TABLE {spec.table_name} ({columns_sql})")


def _insert_row(connection: sqlite3.Connection, spec: _SelectQuerySpec, row: dict[str, object]) -> None:
    placeholders = ", ".join("?" for _ in spec.columns)
    columns_sql = ", ".join(spec.columns)
    values = tuple(row[column] for column in spec.columns)
    connection.execute(f"INSERT INTO {spec.table_name} ({columns_sql}) VALUES ({placeholders})", values)


def _prepare_table_with_rows(case: _ReaderCase, count: int) -> _RecordingConnection:
    connection = _connect()
    _create_table(connection, case.spec)
    row = case.row_factory()
    for _ in range(count):
        _insert_row(connection, case.spec, row)
    connection.execute_calls.clear()
    return connection


def _invoke(case: _ReaderCase, capability: object, lookup_override: str | None = None) -> object:
    reader = getattr(read_scope, case.reader_name)
    if case.lookup_value is None:
        return reader(capability)
    lookup_value = case.lookup_value if lookup_override is None else lookup_override
    return reader(capability, lookup_value)


def _tuple_for(case: _ReaderCase, row: dict[str, object] | None = None) -> tuple[object, ...]:
    row = row or case.row_factory()
    return tuple(row[column] for column in case.spec.columns)


def _assert_safe_mutation_error(exc: SQLiteMutationStoreError, error_class: str) -> None:
    assert exc.error_class == error_class
    assert str(exc) == error_class
    assert exc.args == (error_class,)
    assert exc.internal_detail is None
    assert exc.__cause__ is None
    assert exc.__context__ is None
    assert exc.error_class != "commit_outcome_unknown"
    rendered = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    assert PRIVATE_SQLITE_SENTINEL not in rendered
    for forbidden in (PRIVATE_SQLITE_SENTINEL, ":memory:", "Connection", "SELECT "):
        assert forbidden not in rendered
        assert forbidden not in repr(exc)
        assert forbidden not in repr(exc.args)


def _assert_raises_sqlite_mutation_error(call: Callable[[], object], error_class: str) -> SQLiteMutationStoreError:
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        call()
    _assert_safe_mutation_error(exc_info.value, error_class)
    return exc_info.value


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


def _sqlite_error_code(name: str, fallback: int) -> int:
    code = getattr(sqlite3, name, fallback)
    assert type(code) is int
    return code


def _sqlite_row_object() -> sqlite3.Row:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("CREATE TABLE row_shape_probe (value)")
        connection.execute("INSERT INTO row_shape_probe (value) VALUES (1)")
        row = connection.execute("SELECT value FROM row_shape_probe").fetchone()
        assert isinstance(row, sqlite3.Row)
        return row
    finally:
        connection.close()


@pytest.mark.parametrize("case", OPTIONAL_READER_CASES, ids=[case.reader_name for case in OPTIONAL_READER_CASES])
def test_lookup_ref_validation_runs_before_capability_borrow_or_sql(case: _ReaderCase) -> None:
    connection = _connect()
    _, capability = _capability_for(connection)
    try:
        with pytest.raises(ValueError) as exc_info:
            _invoke(case, capability, lookup_override="malformed ref")

        assert capability.borrow_count == 0
        assert connection.execute_calls == []
        assert not isinstance(exc_info.value, SQLiteMutationStoreError)
        rendered = f"{exc_info.value!r} {exc_info.value.args!r} {exc_info.value}"
        assert "malformed ref" not in rendered
    finally:
        connection.close()


@pytest.mark.parametrize("case", OPTIONAL_READER_CASES, ids=[case.reader_name for case in OPTIONAL_READER_CASES])
def test_valid_lookup_uses_one_bound_parameter_and_no_interpolation(case: _ReaderCase) -> None:
    connection = _prepare_table_with_rows(case, 0)
    _, capability = _capability_for(connection)
    try:
        assert _invoke(case, capability) is None

        assert capability.borrow_count == 1
        assert connection.execute_calls == [(case.spec.sql, (case.lookup_value,))]
        assert case.lookup_value not in case.spec.sql
        assert case.spec.sql.count("?") == 1
    finally:
        connection.close()


@pytest.mark.parametrize("case", READER_CASES, ids=[case.reader_name for case in READER_CASES])
def test_reader_cardinality_zero_one_two_and_more_than_two(case: _ReaderCase) -> None:
    zero_connection = _prepare_table_with_rows(case, 0)
    _, zero_capability = _capability_for(zero_connection)
    try:
        if case.lookup_value is None:
            _assert_raises_sqlite_mutation_error(lambda: _invoke(case, zero_capability), "database_integrity_failure")
        else:
            assert _invoke(case, zero_capability) is None
    finally:
        zero_connection.close()

    one_connection = _prepare_table_with_rows(case, 1)
    _, one_capability = _capability_for(one_connection)
    try:
        envelope = _invoke(case, one_capability)
        assert isinstance(envelope, case.envelope_type)
        assert one_connection.execute_calls == [
            (case.spec.sql, (1,) if case.lookup_value is None else (case.lookup_value,))
        ]
    finally:
        one_connection.close()

    for count in (2, 3):
        duplicate_connection = _prepare_table_with_rows(case, count)
        _, duplicate_capability = _capability_for(duplicate_connection)
        try:
            _assert_raises_sqlite_mutation_error(
                lambda: _invoke(case, duplicate_capability),
                "database_integrity_failure",
            )
        finally:
            duplicate_connection.close()


@pytest.mark.parametrize("case", READER_CASES, ids=[case.reader_name for case in READER_CASES])
def test_fetchmany_is_bounded_to_two_for_each_reader(case: _ReaderCase) -> None:
    row = _tuple_for(case)
    connection, cursor = _scripted_connection(rows=(row, row, row))
    assert cursor is not None
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(lambda: _invoke(case, capability), "database_integrity_failure")
        assert cursor.fetchmany_sizes == [2]
        assert cursor.close_count == 1
    finally:
        connection.close()


@pytest.mark.parametrize("case", READER_CASES, ids=[case.reader_name for case in READER_CASES])
def test_column_order_mapping_uses_exact_bound_adapter_and_no_raw_tuple(case: _ReaderCase, monkeypatch: pytest.MonkeyPatch) -> None:
    raw_tuple = tuple(f"value-{index}" for index, _ in enumerate(case.spec.columns))
    connection, _ = _scripted_connection(rows=(raw_tuple,))
    _, capability = _capability_for(connection)
    marker = object()
    captured: dict[str, object] = {}

    def adapter(payload: object) -> object:
        captured["payload"] = payload
        return marker

    monkeypatch.setattr(read_scope, case.adapter_name, adapter)
    try:
        assert _invoke(case, capability) is marker
        payload = captured["payload"]
        assert type(payload) is dict
        assert payload is not raw_tuple
        assert tuple(payload.keys()) == case.spec.columns  # type: ignore[union-attr]
        assert tuple(payload.values()) == raw_tuple  # type: ignore[union-attr]
    finally:
        connection.close()


@pytest.mark.parametrize("case", READER_CASES, ids=[case.reader_name for case in READER_CASES])
def test_non_exact_tuple_rows_are_rejected_before_adapter(case: _ReaderCase, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_adapter(payload: object) -> object:
        raise AssertionError(f"adapter should not receive {payload!r}")

    monkeypatch.setattr(read_scope, case.adapter_name, forbidden_adapter)
    row = _tuple_for(case)
    malformed_rows = (
        row[:-1],
        list(row),
        {column: value for column, value in zip(case.spec.columns, row, strict=True)},
        _CustomSequence(row),
        _sqlite_row_object(),
    )
    for malformed_row in malformed_rows:
        connection, _ = _scripted_connection(rows=(malformed_row,))
        _, capability = _capability_for(connection)
        try:
            _assert_raises_sqlite_mutation_error(lambda: _invoke(case, capability), "database_integrity_failure")
        finally:
            connection.close()


def test_global_stop_reader_binds_singleton_one_internally_and_exposes_no_argument() -> None:
    signature = __import__("inspect").signature(_read_global_stop_current)
    assert list(signature.parameters) == ["capability"]

    connection = _prepare_table_with_rows(READER_CASES[-1], 1)
    _, capability = _capability_for(connection)
    try:
        envelope = _read_global_stop_current(capability)
        assert isinstance(envelope, GlobalStopCurrentRecordEnvelope)
        assert connection.execute_calls == [(_GLOBAL_STOP_CURRENT_SELECT.sql, (1,))]
    finally:
        connection.close()


def test_capability_errors_are_preserved_and_wrong_return_type_is_safe() -> None:
    connection = _prepare_table_with_rows(READER_CASES[0], 0)
    epoch, capability = _capability_for(connection)
    epoch.end_for_test()
    try:
        with pytest.raises(_TransitionReadCapabilityError) as expired:
            _read_current_work_item(capability, "wi-1")
        assert expired.value.reason is _TransitionReadCapabilityFailureReason.CAPABILITY_EXPIRED
        assert expired.value.__cause__ is None
        assert expired.value.__context__ is None

        with pytest.raises(_TransitionReadCapabilityError) as wrong_type:
            _read_current_work_item(_WrongConnectionCapability(), "wi-1")
        assert wrong_type.value.reason is _TransitionReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE
        assert str(wrong_type.value) == "transition_read_capability_unavailable"
    finally:
        connection.close()


def test_unknown_capability_exception_is_sanitized_outside_raw_exception_context() -> None:
    capability = _UnknownExceptionCapability()

    with pytest.raises(_TransitionReadCapabilityError) as exc_info:
        _read_current_work_item(capability, "wi-1")

    exc = exc_info.value
    assert exc.reason is _TransitionReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE
    assert str(exc) == "transition_read_capability_unavailable"
    assert exc.args == ("transition_read_capability_unavailable",)
    assert exc.__cause__ is None
    assert exc.__context__ is None
    assert getattr(exc, "__notes__", None) is None

    rendered = _render_exception_graph(exc)
    for forbidden in (
        PRIVATE_CAPABILITY_SENTINEL,
        "_UnknownExceptionCapability",
        "RuntimeError",
        "ValueError",
        "Connection",
        ":memory:",
    ):
        assert forbidden not in rendered


def test_test_only_old_transaction_fake_rejects_after_new_generation_starts() -> None:
    connection = _prepare_table_with_rows(READER_CASES[0], 0)
    epoch = _TestsOnlyTransitionReadCapabilityEpoch(connection)
    capability_a = epoch.start_for_test()
    try:
        assert _read_current_work_item(capability_a, "wi-1") is None

        epoch.end_for_test()
        capability_b = epoch.start_for_test()

        with pytest.raises(_TransitionReadCapabilityError) as old_capability:
            _read_current_work_item(capability_a, "wi-1")
        assert old_capability.value.reason is _TransitionReadCapabilityFailureReason.CAPABILITY_EXPIRED
        assert _read_current_work_item(capability_b, "wi-1") is None
    finally:
        connection.close()


@pytest.mark.parametrize("case", READER_CASES, ids=[case.reader_name for case in READER_CASES])
def test_missing_table_schema_query_errors_are_integrity_failures(case: _ReaderCase) -> None:
    connection = _connect()
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(lambda: _invoke(case, capability), "database_integrity_failure")
    finally:
        connection.close()


@pytest.mark.parametrize(
    "sqlite_errorcode",
    (
        _sqlite_error_code("SQLITE_ERROR", 1),
        _sqlite_error_code("SQLITE_SCHEMA", 17),
        _sqlite_error_code("SQLITE_CORRUPT", 11),
        _sqlite_error_code("SQLITE_NOTADB", 26),
        _sqlite_error_code("SQLITE_MISMATCH", 20),
        _sqlite_error_code("SQLITE_CONSTRAINT", 19),
        _sqlite_error_code("SQLITE_CONSTRAINT_CHECK", 275),
    ),
)
def test_schema_query_database_contradiction_sqlite_codes_are_integrity(sqlite_errorcode: int) -> None:
    error = _SyntheticSQLiteError(sqlite_errorcode)
    connection, _ = _scripted_connection(execute_error=error)
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(
            lambda: _read_current_work_item(capability, "wi-1"),
            "database_integrity_failure",
        )
    finally:
        connection.close()


@pytest.mark.parametrize(
    "sqlite_errorcode",
    (
        _sqlite_error_code("SQLITE_BUSY", 5),
        _sqlite_error_code("SQLITE_LOCKED", 6),
        _sqlite_error_code("SQLITE_IOERR", 10),
        _sqlite_error_code("SQLITE_FULL", 13),
        _sqlite_error_code("SQLITE_INTERRUPT", 9),
        123456,
        None,
    ),
)
def test_operational_sqlite_codes_are_mutation_failed(sqlite_errorcode: int | None) -> None:
    error = _SyntheticSQLiteError(sqlite_errorcode)
    connection, _ = _scripted_connection(execute_error=error)
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(lambda: _read_current_work_item(capability, "wi-1"), "mutation_failed")
    finally:
        connection.close()


def test_closed_connection_is_mutation_failed_and_redacted() -> None:
    connection = _prepare_table_with_rows(READER_CASES[0], 0)
    _, capability = _capability_for(connection)
    connection.close()

    _assert_raises_sqlite_mutation_error(lambda: _read_current_work_item(capability, "wi-1"), "mutation_failed")


def test_cursor_cleanup_after_success_fetch_failure_and_close_failure() -> None:
    connection, cursor = _scripted_connection(rows=())
    assert cursor is not None
    _, capability = _capability_for(connection)
    try:
        assert _read_current_work_item(capability, "wi-1") is None
        assert cursor.close_count == 1
        assert connection.close_count == 0
    finally:
        connection.close()

    fetch_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5))
    connection, cursor = _scripted_connection(fetch_error=fetch_error)
    assert cursor is not None
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(lambda: _read_current_work_item(capability, "wi-1"), "mutation_failed")
        assert cursor.close_count == 1
        assert connection.close_count == 0
    finally:
        connection.close()

    close_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_LOCKED", 6))
    connection, cursor = _scripted_connection(rows=(), close_error=close_error)
    assert cursor is not None
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(lambda: _read_current_work_item(capability, "wi-1"), "mutation_failed")
        assert cursor.close_count == 1
        assert connection.close_count == 0
    finally:
        connection.close()

    close_error = sqlite3.IntegrityError(PRIVATE_SQLITE_SENTINEL)
    connection, cursor = _scripted_connection(rows=(), close_error=close_error)
    assert cursor is not None
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(lambda: _read_current_work_item(capability, "wi-1"), "mutation_failed")
        assert cursor.close_count == 1
        assert connection.close_count == 0
    finally:
        connection.close()

    fetch_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_SCHEMA", 17))
    close_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5))
    connection, cursor = _scripted_connection(fetch_error=fetch_error, close_error=close_error)
    assert cursor is not None
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(
            lambda: _read_current_work_item(capability, "wi-1"),
            "database_integrity_failure",
        )
        assert cursor.close_count == 1
        assert connection.close_count == 0
    finally:
        connection.close()


def test_reader_does_not_close_connection() -> None:
    connection = _prepare_table_with_rows(READER_CASES[0], 0)
    _, capability = _capability_for(connection)
    try:
        assert _read_current_work_item(capability, "wi-1") is None
        assert connection.close_count == 0
        assert connection.execute("SELECT 1").fetchone() == (1,)
    finally:
        connection.close()


def test_private_readers_have_no_production_call_sites_or_public_exports() -> None:
    for name in READER_NAMES:
        assert name not in ge_nwp_coordinator.__all__
        assert not hasattr(ge_nwp_coordinator, name)

    for path in PACKAGE_DIR.rglob("*.py"):
        if path == READ_SCOPE_PATH:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "ge_nwp_coordinator.sqlite_transition_read_scope":
                assert all(alias.name not in READER_NAMES for alias in node.names), path
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in READER_NAMES, path
                elif isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in READER_NAMES, path

    assert list(__import__("inspect").signature(StateStore.read_current).parameters) == ["self", "work_item_id"]
    assert list(__import__("inspect").signature(StateStore.read_global_stop).parameters) == ["self"]
    writer_session_source = (PACKAGE_DIR / "sqlite_writer_session.py").read_text(encoding="utf-8")
    report_source = (PACKAGE_DIR / "reports.py").read_text(encoding="utf-8")
    for name in READER_NAMES:
        assert name not in writer_session_source
        assert name not in report_source


def test_reader_source_has_no_production_capability_factory_transaction_or_mutation_sql() -> None:
    source = READ_SCOPE_PATH.read_text(encoding="utf-8")
    support_source = SELECT_SUPPORT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    support_tree = ast.parse(support_source)
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    support_class_names = {node.name for node in ast.walk(support_tree) if isinstance(node, ast.ClassDef)}
    assert "_TransitionReadCapability" not in class_names
    assert "_TransitionReadCapability" in support_class_names
    assert not any(name.endswith("Capability") for name in class_names)
    assert not any(name.endswith("Capability") and name != "_TransitionReadCapability" for name in support_class_names)

    for forbidden in (
        "sqlite3.connect",
        "connection.close",
        "StateStore",
        "WriterSession",
        "TransitionContext",
        "TransitionConflict",
        "validate_b3_work_item_authority_binding",
        "transition_events",
        "global_stop_events",
        "writer_ownership",
        "schema_migrations",
        "operator_decision_history",
    ):
        assert forbidden not in source

    forbidden_calls = {"executemany", "executescript", "commit", "rollback"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_calls


def test_tests_only_schema_setup_is_not_a_fixture_or_production_capability_program() -> None:
    assert not (PACKAGE_DIR / "sqlite_transition_fixtures.py").exists()
    assert not (PACKAGE_DIR / "sqlite_transition_readers.py").exists()
    assert sorted(path.name for path in (PACKAGE_DIR / "sqlite_migrations").glob("*.sql")) == ["0001_initial.sql"]
    assert json.loads(json.dumps({"capability": "tests-only"})) == {"capability": "tests-only"}


def test_b3b2b_docs_pin_private_unintegrated_reader_scope() -> None:
    docs = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            ".docs/b3b2b-select-readers.md",
            ".docs/b3-transition-persistence-contract.md",
            ".docs/durable-state-model.md",
            ".docs/writer-session-authority.md",
            "README.md",
            "AGENTS.md",
        )
    )
    normalized = " ".join(docs.split())
    for phrase in (
        "private SELECT readers implemented and test-executed; no production integration",
        "No production module calls them",
        "lookup-ref validation before capability borrowing",
        "fetchmany(2)",
        "exact built-in tuple",
        "delegating to the B3b1 single-row adapter",
        "`global_stop_current` absence raises `database_integrity_failure` directly",
        "`commit_outcome_unknown` is never produced by B3b2b",
        "The tests-only capability does not prove production transaction authority",
        "B3c1b now implements the nominal concrete capability only inside its private rollback-only writer-fencing controller",
        "Production integration for B3b2 current/context readers waits for a later B3c slice",
        "No `StateStore` mutation backend, integrated production typed SQLite reader",
    ):
        assert phrase in normalized
