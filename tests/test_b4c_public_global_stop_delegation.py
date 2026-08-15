from __future__ import annotations

import ast
import builtins
from enum import Enum
import inspect
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
from typing import Any

import pytest

import ge_nwp_coordinator
import ge_nwp_coordinator.sqlite_global_stop_preflight_contracts as preflight_module
import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module
import ge_nwp_coordinator.sqlite_writer_session as writer_module
from b3_coherent_transition_fixture import (
    global_stop_event_count_for_test,
    make_coherent_transition_fixture_for_test,
    read_back_fixture_for_test,
    transition_event_count_for_test,
)
from ge_nwp_coordinator.global_stop import (
    GlobalStopAction,
    GlobalStopEvent,
    GlobalStopEventOutcome,
    GlobalStopReasonClass,
    GlobalStopState,
    GlobalStopStatus,
)
from ge_nwp_coordinator.persistence_contracts import SQLITE_SIGNED_INT_MAX
from ge_nwp_coordinator.sqlite_connection import open_existing_sqlite_connection
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import initialize_database
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.state_store import (
    CommittedGlobalStopUpdate,
    GlobalStopApplyPreflightError,
    GlobalStopApplyPreflightFailureReason,
    GlobalStopConflict,
    StateStore,
    WriterSession,
    WriterSessionError,
    WriterSessionFailureReason,
)
from test_b3c1b_rollback_only_writer_fencing import _replace_writer_row
from test_b4b_private_atomic_global_stop_persistence import (
    B4B_TIMESTAMP,
    _command,
    _decision,
    _global_stop_event_envelopes,
    _receipt_rows,
    _seed_receipt,
)
from test_sqlite_b2c_writer_session import _run_writer_attempt, _wait_for_child_result


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
WRITER_SESSION_PATH = PACKAGE_DIR / "sqlite_writer_session.py"
STATE_STORE_PATH = PACKAGE_DIR / "state_store.py"
PACKAGE_EXPORT_PATH = PACKAGE_DIR / "__init__.py"
MIGRATION_DIR = PACKAGE_DIR / "sqlite_migrations"
MIGRATION_0001_SHA256 = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"
PRIVATE_SENTINEL = "b4c-private-sentinel-do-not-leak"


class _OtherPrivateReason(str, Enum):
    INVALID_COMMAND = "global_stop_apply_preflight_invalid_command"


class _FuturePrivateReason(str, Enum):
    INVALID_COMMAND = "global_stop_apply_preflight_invalid_command"
    INVALID_OPERATOR_DECISION = "global_stop_apply_preflight_invalid_operator_decision"
    FUTURE_REASON = "global_stop_apply_preflight_future_reason"


class _PrivateReasonSubclass(str):
    pass


class _HostilePrivateReason:
    def __init__(self, hook_calls: list[str]) -> None:
        object.__setattr__(self, "_hook_calls", hook_calls)

    def _record(self, hook_name: str) -> None:
        object.__getattribute__(self, "_hook_calls").append(hook_name)

    def __getattribute__(self, name: str) -> object:
        if name in {"_hook_calls", "_record"}:
            return object.__getattribute__(self, name)
        self._record("__getattribute__")
        raise RuntimeError(PRIVATE_SENTINEL)

    def __str__(self) -> str:
        self._record("__str__")
        raise RuntimeError(PRIVATE_SENTINEL)

    def __repr__(self) -> str:
        self._record("__repr__")
        raise RuntimeError(PRIVATE_SENTINEL)

    def __eq__(self, other: object) -> bool:
        self._record("__eq__")
        raise RuntimeError(PRIVATE_SENTINEL)

    def __hash__(self) -> int:
        self._record("__hash__")
        raise RuntimeError(PRIVATE_SENTINEL)


def _location(tmp_path: Path) -> CoordinatorStateLocation:
    return CoordinatorStateLocation.from_trusted_root(tmp_path / "state")


def _operation_count(resource: object) -> int:
    return len(resource._active_operations)


def _join_thread(thread: threading.Thread, *, timeout: float = 5.0) -> None:
    thread.join(timeout)
    assert not thread.is_alive()


def _wait_for_event(event: threading.Event, *, timeout: float = 5.0) -> None:
    assert event.wait(timeout)


def _wait_for_state(resource: object, state: str, *, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if resource._state == state:
            return
        time.sleep(0.01)
    pytest.fail(f"resource did not reach {state}")


def _sqlite_sidecars(location: CoordinatorStateLocation) -> tuple[str, ...]:
    database_name = location.database_path.name
    return tuple(sorted(path.name for path in location.state_root.glob(f"{database_name}-*")))


def _assert_no_sqlite_sidecars(location: CoordinatorStateLocation) -> None:
    assert _sqlite_sidecars(location) == ()


def _raise(error: BaseException) -> object:
    raise error


def _assert_mutation_error(error: SQLiteMutationStoreError, error_class: str) -> None:
    assert type(error) is SQLiteMutationStoreError
    assert error.error_class == error_class
    assert str(error) == error_class
    assert error.args == (error_class,)
    assert error.internal_detail is None
    assert error.__cause__ is None
    assert error.__context__ is None
    assert not getattr(error, "__notes__", ())
    rendered = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    for forbidden in (
        PRIVATE_SENTINEL,
        "_GlobalStopApplyPreflightError",
        "_GlobalStopApplyPreflightFailureReason",
        "global_stop_apply_preflight",
    ):
        assert forbidden not in rendered


def _assert_preflight_error(
    error: GlobalStopApplyPreflightError,
    reason: GlobalStopApplyPreflightFailureReason,
) -> None:
    assert type(error) is GlobalStopApplyPreflightError
    assert error.reason is reason
    assert str(error) == reason.value
    assert error.args == (reason.value,)
    assert repr(error) == "<GlobalStopApplyPreflightError>"
    assert error.__cause__ is None
    assert error.__context__ is None
    assert not getattr(error, "__notes__", ())
    rendered = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    for forbidden in (
        PRIVATE_SENTINEL,
        "_GlobalStopApplyPreflightError",
        "_GlobalStopApplyPreflightFailureReason",
        "global_stop_apply_preflight",
    ):
        assert forbidden not in rendered


def _assert_committed(result: object, *, replayed: bool) -> CommittedGlobalStopUpdate:
    assert type(result) is CommittedGlobalStopUpdate
    assert result.replayed is replayed
    return result


def _assert_conflict(result: object, conflict_class: str) -> GlobalStopConflict:
    assert type(result) is GlobalStopConflict
    assert result.conflict_class == conflict_class
    return result


def _committed_result(command: object) -> CommittedGlobalStopUpdate:
    state = GlobalStopState(
        version=1,
        active=True,
        stop_id=command.stop_id,
        reason_class=command.reason_class,
        issuer_ref=command.issuer_ref,
        issued_at=command.issued_at,
        operator_decision_ref=command.operator_decision_ref,
    )
    event = GlobalStopEvent(
        event_ref="global-stop-event-b4c-delegate",
        command_digest=command.canonical_command_digest,
        idempotency_key=command.idempotency_key,
        action=command.action,
        source_version=0,
        resulting_version=1,
        outcome=GlobalStopEventOutcome.ACCEPTED,
        reason="global_stop_update_accepted",
        operator_decision_ref=command.operator_decision_ref,
        resulting_global_stop_ref=command.stop_id,
        resulting_status=GlobalStopStatus.ACTIVE,
    )
    return CommittedGlobalStopUpdate(state=state, event=event, replayed=False)


def _patch_clock(monkeypatch: pytest.MonkeyPatch, timestamp: str = B4B_TIMESTAMP) -> None:
    monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: timestamp)


def _delete_receipts_for_test(location: CoordinatorStateLocation) -> None:
    connection = open_existing_sqlite_connection(location, read_only=False)
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("DELETE FROM global_stop_operator_decision_receipts")
        connection.execute("COMMIT")
    except Exception:
        try:
            connection.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        connection.close()


def test_public_signature_is_unchanged() -> None:
    assert list(inspect.signature(WriterSession.apply_global_stop_update).parameters) == [
        "self",
        "global_stop_command",
        "typed_operator_decision",
    ]
    assert not hasattr(StateStore, "apply_global_stop_update")


def test_public_delegate_call_uses_one_operation_guard_exact_lease_command_and_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        resource = fixture.writer_session._resource
        original_guard = resource.operation_guard
        command = _command()
        decision = _decision()
        sentinel = GlobalStopConflict("validation_failed")
        calls: list[tuple[object, object, object]] = []
        leases: list[object] = []
        entered = 0
        exited = 0

        class TrackingGuard:
            def __init__(self, owner_session: object) -> None:
                self._lease = original_guard(owner_session)
                leases.append(self._lease)

            def __enter__(self) -> object:
                nonlocal entered
                entered += 1
                return self._lease.__enter__()

            def __exit__(
                self,
                exc_type: type[BaseException] | None,
                exc: BaseException | None,
                traceback_value: object,
            ) -> object:
                nonlocal exited
                exited += 1
                return self._lease.__exit__(exc_type, exc, traceback_value)

        def delegate(
            *,
            operation_lease: object,
            global_stop_command: object,
            typed_operator_decision: object,
        ) -> GlobalStopConflict:
            calls.append((operation_lease, global_stop_command, typed_operator_decision))
            assert operation_lease is leases[0]
            assert global_stop_command is command
            assert typed_operator_decision is decision
            assert _operation_count(resource) == 1
            return sentinel

        monkeypatch.setattr(resource, "operation_guard", TrackingGuard)
        monkeypatch.setattr(transaction_module, "_run_atomic_global_stop_apply", delegate)

        result = fixture.writer_session.apply_global_stop_update(command, decision)

        assert result is sentinel
        assert calls == [(leases[0], command, decision)]
        assert entered == 1
        assert exited == 1
        assert _operation_count(resource) == 0
        assert resource._mutation_slot is None


@pytest.mark.parametrize(
    ("command_factory", "decision_factory", "expected_reason"),
    (
        (
            lambda: None,
            lambda: _decision(),
            GlobalStopApplyPreflightFailureReason.INVALID_COMMAND,
        ),
        (
            lambda: _command(),
            lambda: None,
            GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION,
        ),
    ),
)
def test_actual_private_preflight_maps_publicly_before_slot_sqlite_receipts_or_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command_factory: object,
    decision_factory: object,
    expected_reason: GlobalStopApplyPreflightFailureReason,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        calls = {"delegate": 0, "mutation": 0, "open": 0, "clock": 0, "receipt": 0}
        original_delegate = transaction_module._run_atomic_global_stop_apply
        original_mutation_factory = writer_module._MUTATION_LEASE_FACTORY

        def counted_delegate(*, operation_lease: object, global_stop_command: object, typed_operator_decision: object) -> object:
            calls["delegate"] += 1
            return original_delegate(
                operation_lease=operation_lease,
                global_stop_command=global_stop_command,
                typed_operator_decision=typed_operator_decision,
            )

        def mutation_factory(**kwargs: object) -> object:
            calls["mutation"] += 1
            return original_mutation_factory(**kwargs)

        def fail_open(*args: object, **kwargs: object) -> object:
            calls["open"] += 1
            raise AssertionError("public preflight opened SQLite")

        def fail_clock() -> str:
            calls["clock"] += 1
            raise AssertionError("public preflight captured the transaction clock")

        def fail_receipt(*args: object, **kwargs: object) -> object:
            calls["receipt"] += 1
            raise AssertionError("public preflight read receipt authority")

        monkeypatch.setattr(transaction_module, "_run_atomic_global_stop_apply", counted_delegate)
        monkeypatch.setattr(writer_module, "_MUTATION_LEASE_FACTORY", mutation_factory)
        monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_open)
        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", fail_clock)
        monkeypatch.setattr(transaction_module, "_read_global_stop_operator_decision_receipt", fail_receipt)

        with pytest.raises(GlobalStopApplyPreflightError) as exc_info:
            fixture.writer_session.apply_global_stop_update(command_factory(), decision_factory())  # type: ignore[operator]

        _assert_preflight_error(exc_info.value, expected_reason)
        assert calls == {"delegate": 1, "mutation": 0, "open": 0, "clock": 0, "receipt": 0}
        assert fixture.writer_session._resource._mutation_slot is None
        assert global_stop_event_count_for_test(fixture) == 0
        _assert_no_sqlite_sidecars(fixture.location)


def test_malformed_private_preflight_reasons_are_database_integrity_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class SubclassedPrivatePreflight(preflight_module._GlobalStopApplyPreflightError):
        pass

    def exact_private_error_with_reason(reason: object) -> BaseException:
        error = preflight_module._GlobalStopApplyPreflightError.__new__(
            preflight_module._GlobalStopApplyPreflightError
        )
        RuntimeError.__init__(error, PRIVATE_SENTINEL)
        error.reason = reason
        return error

    hook_calls: list[str] = []
    missing_reason = preflight_module._GlobalStopApplyPreflightError.__new__(
        preflight_module._GlobalStopApplyPreflightError
    )
    RuntimeError.__init__(missing_reason, PRIVATE_SENTINEL)
    malformed_errors = (
        exact_private_error_with_reason("global_stop_apply_preflight_invalid_command"),
        exact_private_error_with_reason(_OtherPrivateReason.INVALID_COMMAND),
        exact_private_error_with_reason(_PrivateReasonSubclass("global_stop_apply_preflight_invalid_command")),
        exact_private_error_with_reason(_HostilePrivateReason(hook_calls)),
        missing_reason,
        SubclassedPrivatePreflight(preflight_module._GlobalStopApplyPreflightFailureReason.INVALID_COMMAND),
    )

    for index, private_error in enumerate(malformed_errors):
        with monkeypatch.context() as patch:
            with make_coherent_transition_fixture_for_test(tmp_path / str(index)) as fixture:
                calls = {"mutation": 0, "open": 0}
                original_mutation_factory = writer_module._MUTATION_LEASE_FACTORY

                def mutation_factory(**kwargs: object) -> object:
                    calls["mutation"] += 1
                    return original_mutation_factory(**kwargs)

                def fail_open(*args: object, **kwargs: object) -> object:
                    calls["open"] += 1
                    raise AssertionError("malformed private preflight opened SQLite")

                patch.setattr(writer_module, "_MUTATION_LEASE_FACTORY", mutation_factory)
                patch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_open)
                patch.setattr(
                    transaction_module,
                    "_run_atomic_global_stop_apply",
                    lambda *args, private_error=private_error, **kwargs: _raise(private_error),
                )

                with pytest.raises(SQLiteMutationStoreError) as exc_info:
                    fixture.writer_session.apply_global_stop_update(_command(), _decision())

                _assert_mutation_error(
                    exc_info.value,
                    SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value,
                )
                captured = capsys.readouterr()
                assert PRIVATE_SENTINEL not in captured.out
                assert PRIVATE_SENTINEL not in captured.err
                assert "global_stop_apply_preflight" not in captured.out
                assert "global_stop_apply_preflight" not in captured.err
                assert calls == {"mutation": 0, "open": 0}
                assert _operation_count(fixture.writer_session._resource) == 0
                assert fixture.writer_session._resource._mutation_slot is None
                assert global_stop_event_count_for_test(fixture) == 0
                assert fixture.writer_session.active is True

    assert hook_calls == []


def test_unrecognized_private_preflight_reason_is_database_integrity_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(preflight_module, "_GlobalStopApplyPreflightFailureReason", _FuturePrivateReason)
        private_error = preflight_module._GlobalStopApplyPreflightError(_FuturePrivateReason.FUTURE_REASON)
        with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
            patch.setattr(
                transaction_module,
                "_run_atomic_global_stop_apply",
                lambda *args, **kwargs: _raise(private_error),
            )

            with pytest.raises(SQLiteMutationStoreError) as exc_info:
                fixture.writer_session.apply_global_stop_update(_command(), _decision())

            _assert_mutation_error(
                exc_info.value,
                SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value,
            )
            assert fixture.writer_session.active is True
            assert fixture.writer_session._resource._mutation_slot is None


def test_private_preflight_reason_access_failure_is_database_integrity_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class RaisingReasonDescriptor:
        def __get__(self, instance: object, owner: object = None) -> object:
            raise RuntimeError(PRIVATE_SENTINEL)

    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        private_error = preflight_module._GlobalStopApplyPreflightError.__new__(
            preflight_module._GlobalStopApplyPreflightError
        )
        RuntimeError.__init__(private_error, PRIVATE_SENTINEL)
        with monkeypatch.context() as patch:
            patch.setattr(preflight_module._GlobalStopApplyPreflightError, "reason", RaisingReasonDescriptor())
            patch.setattr(
                transaction_module,
                "_run_atomic_global_stop_apply",
                lambda *args, **kwargs: _raise(private_error),
            )

            with pytest.raises(SQLiteMutationStoreError) as exc_info:
                fixture.writer_session.apply_global_stop_update(_command(), _decision())

        _assert_mutation_error(
            exc_info.value,
            SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value,
        )
        captured = capsys.readouterr()
        assert PRIVATE_SENTINEL not in captured.out
        assert PRIVATE_SENTINEL not in captured.err
        assert fixture.writer_session._resource._mutation_slot is None
        with pytest.raises(GlobalStopApplyPreflightError) as recovered:
            fixture.writer_session.apply_global_stop_update(None, _decision())  # type: ignore[arg-type]
        _assert_preflight_error(recovered.value, GlobalStopApplyPreflightFailureReason.INVALID_COMMAND)


@pytest.mark.parametrize(
    "failure_mode",
    ("preflight_module_import", "transaction_module_import", "missing_delegate_symbol"),
)
def test_import_load_failure_is_pre_delegate_mutation_failed_and_session_recovers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_mode: str,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    original_guard = resource.operation_guard
    entered = 0
    exited = 0
    mutation_calls = 0
    sqlite_calls = 0
    original_import = builtins.__import__

    class TrackingGuard:
        def __init__(self, owner_session: object) -> None:
            self._lease = original_guard(owner_session)

        def __enter__(self) -> object:
            nonlocal entered
            entered += 1
            return self._lease.__enter__()

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            traceback_value: object,
        ) -> object:
            nonlocal exited
            exited += 1
            return self._lease.__exit__(exc_type, exc, traceback_value)

    def mutation_factory(**kwargs: object) -> object:
        nonlocal mutation_calls
        mutation_calls += 1
        raise AssertionError("import failure acquired mutation slot")

    def fail_sqlite_open(*args: object, **kwargs: object) -> object:
        nonlocal sqlite_calls
        sqlite_calls += 1
        raise AssertionError("import failure opened SQLite")

    def controlled_import(
        name: str,
        globals: object = None,
        locals: object = None,
        fromlist: object = (),
        level: int = 0,
    ) -> object:
        if failure_mode == "preflight_module_import" and name == (
            "ge_nwp_coordinator.sqlite_global_stop_preflight_contracts"
        ):
            raise RuntimeError(PRIVATE_SENTINEL)
        if failure_mode == "transaction_module_import" and name == "ge_nwp_coordinator.sqlite_transition_transaction":
            raise RuntimeError(PRIVATE_SENTINEL)
        return original_import(name, globals, locals, fromlist, level)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(resource, "operation_guard", TrackingGuard)
            patch.setattr(writer_module, "_MUTATION_LEASE_FACTORY", mutation_factory)
            patch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_sqlite_open)
            if failure_mode == "missing_delegate_symbol":
                patch.delattr(transaction_module, "_run_atomic_global_stop_apply")
            else:
                patch.setattr(builtins, "__import__", controlled_import)

            with pytest.raises(SQLiteMutationStoreError) as exc_info:
                session.apply_global_stop_update(_command(), _decision())

        _assert_mutation_error(exc_info.value, SQLiteMutationStoreErrorCode.MUTATION_FAILED.value)
        assert entered == 1
        assert exited == 1
        assert mutation_calls == 0
        assert sqlite_calls == 0
        assert _operation_count(resource) == 0
        assert resource._mutation_slot is None
        assert session.active is True

        with pytest.raises(GlobalStopApplyPreflightError) as recovered:
            session.apply_global_stop_update(None, _decision())  # type: ignore[arg-type]
        _assert_preflight_error(recovered.value, GlobalStopApplyPreflightFailureReason.INVALID_COMMAND)
    finally:
        session.close()


def test_session_local_precedence_blocks_import_and_delegate_for_closed_inactive_and_process_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_imports: list[str] = []
    original_import = builtins.__import__

    def fail_private_import(
        name: str,
        globals: object = None,
        locals: object = None,
        fromlist: object = (),
        level: int = 0,
    ) -> object:
        if name in {
            "ge_nwp_coordinator.sqlite_global_stop_preflight_contracts",
            "ge_nwp_coordinator.sqlite_transition_transaction",
        }:
            private_imports.append(name)
            raise AssertionError("session guard failure reached private import")
        return original_import(name, globals, locals, fromlist, level)

    def fail_delegate(*args: object, **kwargs: object) -> object:
        raise AssertionError("session guard failure reached delegate")

    monkeypatch.setattr(transaction_module, "_run_atomic_global_stop_apply", fail_delegate)
    monkeypatch.setattr(builtins, "__import__", fail_private_import)

    closed_location = _location(tmp_path / "closed")
    initialize_database(closed_location)
    closed = acquire_sqlite_writer_session(closed_location)
    closed.close()
    with pytest.raises(WriterSessionError) as closed_error:
        closed.apply_global_stop_update(None, None)  # type: ignore[arg-type]
    assert closed_error.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED

    inactive_location = _location(tmp_path / "inactive")
    initialize_database(inactive_location)
    inactive = acquire_sqlite_writer_session(inactive_location)
    retained_lock = inactive._resource._authority_lock
    assert retained_lock is not None
    retained_lock.close()
    with pytest.raises(WriterSessionError) as inactive_error:
        inactive.apply_global_stop_update(None, None)  # type: ignore[arg-type]
    assert inactive_error.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED
    inactive.close()

    mismatch_location = _location(tmp_path / "mismatch")
    initialize_database(mismatch_location)
    mismatch = acquire_sqlite_writer_session(mismatch_location)
    owner_pid = os.getpid()
    with monkeypatch.context() as pid_patch:
        pid_patch.setattr(writer_module.os, "getpid", lambda: owner_pid + 1)
        with pytest.raises(WriterSessionError) as mismatch_error:
            mismatch.apply_global_stop_update(None, None)  # type: ignore[arg-type]
    assert mismatch_error.value.reason is WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH
    mismatch.close()

    assert private_imports == []


def test_delegate_results_store_errors_and_unexpected_exceptions_propagate_by_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command()
    committed = _committed_result(command)
    propagated = (
        committed,
        GlobalStopConflict("validation_failed"),
        WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_CLOSED),
        SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE),
        SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.EVENT_SEQUENCE_EXHAUSTED),
        SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED),
        SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN),
        RuntimeError(PRIVATE_SENTINEL),
    )
    for index, expected in enumerate(propagated):
        with monkeypatch.context() as patch:
            with make_coherent_transition_fixture_for_test(tmp_path / str(index)) as fixture:
                if isinstance(expected, (CommittedGlobalStopUpdate, GlobalStopConflict)):
                    patch.setattr(
                        transaction_module,
                        "_run_atomic_global_stop_apply",
                        lambda *args, expected=expected, **kwargs: expected,
                    )
                    assert fixture.writer_session.apply_global_stop_update(command, _decision()) is expected
                else:
                    patch.setattr(
                        transaction_module,
                        "_run_atomic_global_stop_apply",
                        lambda *args, expected=expected, **kwargs: _raise(expected),
                    )
                    with pytest.raises(type(expected)) as exc_info:
                        fixture.writer_session.apply_global_stop_update(command, _decision())
                    assert exc_info.value is expected


def test_public_apply_real_atomic_accepted_activate_replace_clear_and_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        _patch_clock(monkeypatch)
        activate_decision = _decision(ref="operator-decision-b4c-activate")
        replace_decision = _decision(ref="operator-decision-b4c-replace")
        clear_decision = _decision(ref="operator-decision-b4c-clear")
        for decision in (activate_decision, replace_decision, clear_decision):
            _seed_receipt(fixture, decision)

        activate_command = _command(decision_ref=activate_decision.decision_ref, stop_id="global-stop-b4c-a")
        activated = _assert_committed(
            fixture.writer_session.apply_global_stop_update(activate_command, activate_decision),
            replayed=False,
        )
        replay = _assert_committed(
            fixture.writer_session.apply_global_stop_update(activate_command, activate_decision),
            replayed=True,
        )
        assert replay.event == activated.event
        assert replay.state == activated.state

        replace_command = _command(
            action=GlobalStopAction.REPLACE,
            key="global-stop-b4c-key-2",
            expected_version=activated.state.version,
            decision_ref=replace_decision.decision_ref,
            source_stop_id=activated.state.stop_id,
            stop_id="global-stop-b4c-b",
            issuer_ref="operator-policy-replace",
            issued_at="2026-07-22T12:00:01Z",
        )
        replaced = _assert_committed(
            fixture.writer_session.apply_global_stop_update(replace_command, replace_decision),
            replayed=False,
        )
        clear_command = _command(
            action=GlobalStopAction.CLEAR,
            key="global-stop-b4c-key-3",
            expected_version=replaced.state.version,
            decision_ref=clear_decision.decision_ref,
            source_stop_id=replaced.state.stop_id,
            stop_id=replaced.state.stop_id or "global-stop-b4c-b",
            reason_class=replaced.state.reason_class or GlobalStopReasonClass.OPERATOR_STOP,
            issuer_ref=replaced.state.issuer_ref or "operator-policy-replace",
            issued_at=replaced.state.issued_at or "2026-07-22T12:00:01Z",
        )
        cleared = _assert_committed(
            fixture.writer_session.apply_global_stop_update(clear_command, clear_decision),
            replayed=False,
        )

        assert activated.event.outcome is GlobalStopEventOutcome.ACCEPTED
        assert activated.state.active is True
        assert replaced.state.active is True
        assert replaced.state.stop_id == "global-stop-b4c-b"
        assert cleared.state == GlobalStopState(version=3, active=False)
        assert tuple(envelope.event_sequence for envelope in _global_stop_event_envelopes(fixture)) == (0, 1, 2)
        assert read_back_fixture_for_test(fixture).global_stop.state == cleared.state
        assert transition_event_count_for_test(fixture) == 0


def test_public_apply_unauthorized_receipt_persists_domain_rejected_event_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        decision = _decision(authorized=False)
        command = _command(decision_ref=decision.decision_ref)
        _seed_receipt(fixture, decision)
        _patch_clock(monkeypatch)
        before = read_back_fixture_for_test(fixture).global_stop

        result = _assert_committed(
            fixture.writer_session.apply_global_stop_update(command, decision),
            replayed=False,
        )

        assert result.event.outcome is GlobalStopEventOutcome.DOMAIN_REJECTED
        assert result.event.reason == "operator_authorization_required"
        assert result.state == before.state
        assert read_back_fixture_for_test(fixture).global_stop.state == before.state
        assert global_stop_event_count_for_test(fixture) == 1


def test_public_apply_real_atomic_conflict_and_receipt_validation_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "stale") as fixture:
        decision = _decision()
        command = _command(decision_ref=decision.decision_ref)
        _seed_receipt(fixture, decision)
        _replace_writer_row(fixture.location, issuance_nonce_digest="0" * 64)

        result = _assert_conflict(
            fixture.writer_session.apply_global_stop_update(command, decision),
            "stale_writer_token",
        )

        assert result.conflict_class == "stale_writer_token"
        assert global_stop_event_count_for_test(fixture) == 0

    with make_coherent_transition_fixture_for_test(tmp_path / "idempotency") as fixture:
        decision = _decision()
        command = _command(decision_ref=decision.decision_ref)
        _seed_receipt(fixture, decision)
        _patch_clock(monkeypatch)
        _assert_committed(fixture.writer_session.apply_global_stop_update(command, decision), replayed=False)
        changed = _command(
            key=command.idempotency_key,
            expected_version=command.expected_version,
            decision_ref=decision.decision_ref,
            stop_id="global-stop-b4c-changed",
        )

        _assert_conflict(
            fixture.writer_session.apply_global_stop_update(changed, decision),
            "idempotency_key_reuse_conflict",
        )
        assert global_stop_event_count_for_test(fixture) == 1

    with make_coherent_transition_fixture_for_test(tmp_path / "expected") as fixture:
        decision = _decision()
        command = _command(expected_version=7, decision_ref=decision.decision_ref)
        _seed_receipt(fixture, decision)

        _assert_conflict(
            fixture.writer_session.apply_global_stop_update(command, decision),
            "expected_version_conflict",
        )
        assert global_stop_event_count_for_test(fixture) == 0

    with make_coherent_transition_fixture_for_test(tmp_path / "missing") as fixture:
        decision = _decision()
        command = _command(decision_ref=decision.decision_ref)

        _assert_conflict(
            fixture.writer_session.apply_global_stop_update(command, decision),
            "validation_failed",
        )
        assert _receipt_rows(fixture) == ()
        assert global_stop_event_count_for_test(fixture) == 0

    with make_coherent_transition_fixture_for_test(tmp_path / "mismatch") as fixture:
        persisted = _decision()
        caller = _decision(ref=persisted.decision_ref, authorized=False)
        command = _command(decision_ref=persisted.decision_ref)
        _seed_receipt(fixture, persisted)

        _assert_conflict(
            fixture.writer_session.apply_global_stop_update(command, caller),
            "validation_failed",
        )
        assert _receipt_rows(fixture) == ((persisted.decision_ref, 1, "accepted"),)
        assert global_stop_event_count_for_test(fixture) == 0

    with make_coherent_transition_fixture_for_test(tmp_path / "malformed") as fixture:
        persisted = _decision()
        caller = _decision(ref=persisted.decision_ref, authorized=False)
        command = _command(decision_ref=persisted.decision_ref)
        _seed_receipt(fixture, persisted, canonical_digest="0" * 64)

        with pytest.raises(SQLiteMutationStoreError) as exc_info:
            fixture.writer_session.apply_global_stop_update(command, caller)
        _assert_mutation_error(exc_info.value, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value)
        assert global_stop_event_count_for_test(fixture) == 0


def test_sequence_store_failures_commit_uncertainty_and_retry_match_private_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as sequence_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "sequence") as fixture:
            decision = _decision()
            command = _command(decision_ref=decision.decision_ref)
            _seed_receipt(fixture, decision)
            _patch_clock(sequence_patch)
            sequence_patch.setattr(
                transaction_module,
                "_read_global_stop_event_max_sequence",
                lambda capability: SQLITE_SIGNED_INT_MAX,
            )

            with pytest.raises(SQLiteMutationStoreError) as exc_info:
                fixture.writer_session.apply_global_stop_update(command, decision)

            _assert_mutation_error(exc_info.value, SQLiteMutationStoreErrorCode.EVENT_SEQUENCE_EXHAUSTED.value)
            assert global_stop_event_count_for_test(fixture) == 0

    with monkeypatch.context() as store_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "store") as fixture:
            decision = _decision()
            command = _command(decision_ref=decision.decision_ref)
            _seed_receipt(fixture, decision)
            _patch_clock(store_patch)
            store_patch.setattr(
                transaction_module,
                "_read_global_stop_event_max_sequence",
                lambda capability: (_ for _ in ()).throw(transaction_module._mutation_failed()),
            )

            with pytest.raises(SQLiteMutationStoreError) as exc_info:
                fixture.writer_session.apply_global_stop_update(command, decision)

            _assert_mutation_error(exc_info.value, SQLiteMutationStoreErrorCode.MUTATION_FAILED.value)
            assert global_stop_event_count_for_test(fixture) == 0

    with monkeypatch.context() as before_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "before") as fixture:
            decision = _decision()
            command = _command(decision_ref=decision.decision_ref)
            _seed_receipt(fixture, decision)
            _patch_clock(before_patch)
            original_commit = transaction_module._commit_transaction
            before_patch.setattr(
                transaction_module,
                "_commit_transaction",
                lambda connection: (_ for _ in ()).throw(RuntimeError(PRIVATE_SENTINEL)),
            )

            with pytest.raises(SQLiteMutationStoreError) as exc_info:
                fixture.writer_session.apply_global_stop_update(command, decision)

            _assert_mutation_error(exc_info.value, SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN.value)
            assert global_stop_event_count_for_test(fixture) == 0
            before_patch.setattr(transaction_module, "_commit_transaction", original_commit)
            _patch_clock(before_patch)
            result = _assert_committed(
                fixture.writer_session.apply_global_stop_update(command, decision),
                replayed=False,
            )
            assert result.event.outcome is GlobalStopEventOutcome.ACCEPTED
            assert global_stop_event_count_for_test(fixture) == 1

    with monkeypatch.context() as after_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "after") as fixture:
            decision = _decision()
            command = _command(decision_ref=decision.decision_ref)
            _seed_receipt(fixture, decision)
            _patch_clock(after_patch)

            def commit_then_raise(connection: sqlite3.Connection) -> None:
                connection.execute("COMMIT")
                raise RuntimeError(PRIVATE_SENTINEL)

            after_patch.setattr(transaction_module, "_commit_transaction", commit_then_raise)
            with pytest.raises(SQLiteMutationStoreError) as exc_info:
                fixture.writer_session.apply_global_stop_update(command, decision)
            _assert_mutation_error(exc_info.value, SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN.value)
            assert global_stop_event_count_for_test(fixture) == 1
            committed = _global_stop_event_envelopes(fixture)[0]

            after_patch.setattr(transaction_module, "_commit_transaction", lambda connection: None)
            replay = _assert_committed(
                fixture.writer_session.apply_global_stop_update(command, decision),
                replayed=True,
            )
            assert replay.event == committed.event
            assert replay.state == committed.replay_state
            changed = _command(
                key=command.idempotency_key,
                expected_version=command.expected_version,
                decision_ref=decision.decision_ref,
                stop_id="global-stop-b4c-changed",
            )
            _assert_conflict(
                fixture.writer_session.apply_global_stop_update(changed, decision),
                "idempotency_key_reuse_conflict",
            )


def test_public_global_stop_and_transition_share_one_mutation_slot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases = (
        ("global-stop-first", "global-stop-second"),
        ("global-stop-first", "transition-second"),
        ("transition-first", "global-stop-second"),
    )
    for first, second in cases:
        with monkeypatch.context() as case_patch:
            with make_coherent_transition_fixture_for_test(tmp_path / f"{first}-{second}") as fixture:
                decision = _decision()
                command = _command(decision_ref=decision.decision_ref)
                _seed_receipt(fixture, decision)
                _patch_clock(case_patch)
                original_open = transaction_module._open_bound_existing_sqlite_connection
                entered = threading.Event()
                release = threading.Event()
                first_result: list[object] = []
                first_error: list[BaseException] = []
                open_calls = 0

                def blocking_open(*args: object, **kwargs: object) -> sqlite3.Connection:
                    nonlocal open_calls
                    open_calls += 1
                    entered.set()
                    if not release.wait(timeout=5):
                        raise RuntimeError(PRIVATE_SENTINEL)
                    return original_open(*args, **kwargs)

                case_patch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", blocking_open)

                def run_first() -> None:
                    try:
                        if first == "transition-first":
                            first_result.append(fixture.writer_session.apply_transition(fixture.command))
                        else:
                            first_result.append(fixture.writer_session.apply_global_stop_update(command, decision))
                    except BaseException as exc:  # noqa: BLE001 - test collects thread failures
                        first_error.append(exc)

                thread = threading.Thread(target=run_first)
                thread.start()
                _wait_for_event(entered)
                assert fixture.writer_session._resource._mutation_slot is not None
                assert open_calls == 1
                try:
                    with pytest.raises(WriterSessionError) as exc_info:
                        if second == "transition-second":
                            fixture.writer_session.apply_transition(fixture.command)
                        else:
                            fixture.writer_session.apply_global_stop_update(command, decision)
                    assert exc_info.value.reason is WriterSessionFailureReason.WRITER_SESSION_MUTATION_IN_PROGRESS
                    assert fixture.writer_session._resource._mutation_slot is not None
                    assert open_calls == 1
                finally:
                    release.set()
                    _join_thread(thread)
                assert first_error == []
                assert len(first_result) == 1
                assert fixture.writer_session._resource._mutation_slot is None


def test_same_thread_close_during_public_global_stop_keeps_existing_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        resource = fixture.writer_session._resource

        def delegate(*, operation_lease: object, global_stop_command: object, typed_operator_decision: object) -> object:
            assert _operation_count(resource) == 1
            fixture.writer_session.close()
            raise AssertionError("close during operation unexpectedly returned")

        monkeypatch.setattr(transaction_module, "_run_atomic_global_stop_apply", delegate)

        with pytest.raises(WriterSessionError) as exc_info:
            fixture.writer_session.apply_global_stop_update(_command(), _decision())

        assert exc_info.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSE_DURING_OPERATION
        assert resource._state == writer_module._ACTIVE
        assert _operation_count(resource) == 0
        assert resource._mutation_slot is None
        assert fixture.writer_session.active is True


def test_cross_thread_close_waits_for_public_global_stop_delegate_and_operation_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        resource = fixture.writer_session._resource
        started = threading.Event()
        release_delegate = threading.Event()
        close_done = threading.Event()
        sentinel = GlobalStopConflict("validation_failed")
        result: dict[str, object] = {}
        close_errors: list[BaseException] = []

        def delegate(*, operation_lease: object, global_stop_command: object, typed_operator_decision: object) -> GlobalStopConflict:
            assert _operation_count(resource) == 1
            started.set()
            _wait_for_event(release_delegate)
            assert _operation_count(resource) == 1
            return sentinel

        def call_apply() -> None:
            try:
                result["value"] = fixture.writer_session.apply_global_stop_update(_command(), _decision())
            except BaseException as exc:  # noqa: BLE001 - test collects thread failures
                result["error"] = exc

        def call_close() -> None:
            try:
                fixture.writer_session.close()
            except BaseException as exc:  # noqa: BLE001 - test collects thread failures
                close_errors.append(exc)
            finally:
                close_done.set()

        monkeypatch.setattr(transaction_module, "_run_atomic_global_stop_apply", delegate)

        apply_thread = threading.Thread(target=call_apply)
        apply_thread.start()
        _wait_for_event(started)
        assert _operation_count(resource) == 1

        close_thread = threading.Thread(target=call_close)
        close_thread.start()
        _wait_for_state(resource, writer_module._CLOSING)
        assert close_done.wait(0.1) is False
        assert _operation_count(resource) == 1

        release_delegate.set()
        _join_thread(apply_thread)
        _join_thread(close_thread)

        assert result == {"value": sentinel}
        assert close_errors == []
        assert close_done.is_set()
        assert _operation_count(resource) == 0
        assert resource._mutation_slot is None
        assert resource._state == writer_module._CLOSED


def test_fork_child_public_global_stop_fails_before_delegate_sqlite_or_parent_slot_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")

    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        resource = fixture.writer_session._resource

        def fail_delegate(*args: object, **kwargs: object) -> object:
            raise AssertionError("fork child reached global-stop delegate")

        monkeypatch.setattr(transaction_module, "_run_atomic_global_stop_apply", fail_delegate)
        before_sidecars = _sqlite_sidecars(fixture.location)
        read_fd, write_fd = os.pipe()
        child_pid = os.fork()
        if child_pid == 0:
            os.close(read_fd)
            try:
                try:
                    fixture.writer_session.apply_global_stop_update(None, None)  # type: ignore[arg-type]
                except WriterSessionError as exc:
                    reason = exc.reason.value
                except BaseException as exc:  # noqa: BLE001 - child reports unexpected failures to parent
                    reason = f"unexpected:{exc.__class__.__name__}"
                else:
                    reason = "unexpected-success"
                sidecars = ",".join(_sqlite_sidecars(fixture.location)) or "no-sidecars"
                slot_state = "slot-clear" if fixture.writer_session._resource._mutation_slot is None else "slot-kept"
                os.write(write_fd, f"{reason}:{slot_state}:{sidecars}".encode("ascii"))
            finally:
                os.close(write_fd)
                os._exit(0)

        os.close(write_fd)
        try:
            child_result = _wait_for_child_result(child_pid, read_fd)
        finally:
            os.close(read_fd)

        assert child_result == "writer_session_process_mismatch:slot-clear:no-sidecars"
        assert _sqlite_sidecars(fixture.location) == before_sidecars == ()
        assert resource._mutation_slot is None
        assert fixture.writer_session.active is True
        assert _run_writer_attempt(fixture.location) == "state_authority_lock_busy"


def test_public_wrapper_static_boundary_has_no_sql_authority_or_delegate_catch_all() -> None:
    source = WRITER_SESSION_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    sqlite_session = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "_SQLiteWriterSession"
    )
    apply_global_stop = next(
        node for node in sqlite_session.body
        if isinstance(node, ast.FunctionDef) and node.name == "apply_global_stop_update"
    )
    method_source = ast.get_source_segment(source, apply_global_stop)
    assert method_source is not None

    forbidden_tokens = (
        "sqlite3",
        "connect(",
        ".execute(",
        ".cursor",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
        "_read_global_stop_event_max_sequence",
        "next_global_stop_event_sequence",
        "INSERT INTO",
        "UPDATE global_stop_current",
        "receipt",
        "evaluate_global_stop_update",
        "_utc_transaction_timestamp",
        "_create_sqlite_mutation_read_capability",
        "_CoordinatorMutationTransactionController",
        "_acquire_mutation_lease",
        "_MUTATION_LEASE_FACTORY",
        "CoordinatorStateLocation",
        "state_root",
        "database_path",
        "getattr(",
        "hasattr(",
        "registry",
        "callback",
        "injection",
        "ge_nwp_coordinator._run_atomic_global_stop_apply",
    )
    for token in forbidden_tokens:
        assert token not in method_source

    top_level_private_imports = [
        node for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module in {
            "ge_nwp_coordinator.sqlite_global_stop_preflight_contracts",
            "ge_nwp_coordinator.sqlite_transition_transaction",
        }
    ]
    assert top_level_private_imports == []

    private_imports = [
        node for node in ast.walk(apply_global_stop)
        if isinstance(node, ast.ImportFrom)
        and node.module in {
            "ge_nwp_coordinator.sqlite_global_stop_preflight_contracts",
            "ge_nwp_coordinator.sqlite_transition_transaction",
        }
    ]
    assert {node.module for node in private_imports} == {
        "ge_nwp_coordinator.sqlite_global_stop_preflight_contracts",
        "ge_nwp_coordinator.sqlite_transition_transaction",
    }
    assert sum(len(node.names) for node in private_imports) == 3

    operation_guard_calls = [
        node for node in ast.walk(apply_global_stop)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "operation_guard"
    ]
    assert len(operation_guard_calls) == 1

    delegate_calls = [
        node for node in ast.walk(apply_global_stop)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_run_atomic_global_stop_apply"
    ]
    assert len(delegate_calls) == 1
    assert delegate_calls[0].args == []
    assert [keyword.arg for keyword in delegate_calls[0].keywords] == [
        "operation_lease",
        "global_stop_command",
        "typed_operator_decision",
    ]
    assert [keyword.value.id for keyword in delegate_calls[0].keywords if isinstance(keyword.value, ast.Name)] == [
        "operation_lease",
        "global_stop_command",
        "typed_operator_decision",
    ]

    private_error_gate = "type(caught_private_preflight) is not _GlobalStopApplyPreflightError"
    reason_access = 'object.__getattribute__(caught_private_preflight, "reason")'
    private_reason_gate = "type(private_preflight_reason) is not _GlobalStopApplyPreflightFailureReason"
    invalid_mapping = "private_preflight_reason is _GlobalStopApplyPreflightFailureReason.INVALID_COMMAND"
    invalid_decision_mapping = (
        "private_preflight_reason is _GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION"
    )
    assert private_error_gate in method_source
    assert reason_access in method_source
    assert private_reason_gate in method_source
    assert invalid_mapping in method_source
    assert invalid_decision_mapping in method_source
    assert method_source.index(private_error_gate) < method_source.index(reason_access)
    assert method_source.index(reason_access) < method_source.index(private_reason_gate)
    assert method_source.index(private_reason_gate) < method_source.index(invalid_mapping)
    assert method_source.index(private_reason_gate) < method_source.index(invalid_decision_mapping)
    assert "SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE" in method_source
    assert "SQLiteMutationStoreErrorCode.MUTATION_FAILED" in method_source
    assert "caught_private_preflight = None" in method_source
    assert "private_preflight_reason = None" in method_source

    try_nodes = [node for node in ast.walk(apply_global_stop) if isinstance(node, ast.Try)]
    delegate_try = next(
        node for node in try_nodes
        if any(nested is delegate_calls[0] for statement in node.body for nested in ast.walk(statement))
    )
    assert [ast.unparse(handler.type) for handler in delegate_try.handlers] == ["_GlobalStopApplyPreflightError"]
    assert all(
        not (
            isinstance(handler.type, ast.Name)
            and handler.type.id in {"Exception", "BaseException"}
            and any(nested is delegate_calls[0] for statement in node.body for nested in ast.walk(statement))
        )
        for node in try_nodes
        for handler in node.handlers
    )
    assert all(handler.type is not None for handler in ast.walk(apply_global_stop) if isinstance(handler, ast.ExceptHandler))
    assert all(
        not (isinstance(handler.type, ast.Name) and handler.type.id == "BaseException")
        for handler in ast.walk(apply_global_stop)
        if isinstance(handler, ast.ExceptHandler)
    )

    handler_ranges = [
        (handler.lineno, handler.end_lineno)
        for handler in ast.walk(apply_global_stop)
        if isinstance(handler, ast.ExceptHandler)
    ]
    final_raise_lines = [
        node.lineno for node in ast.walk(apply_global_stop)
        if isinstance(node, ast.Raise)
        and node.exc is not None
        and (
            "GlobalStopApplyPreflightError" in (ast.get_source_segment(source, node.exc) or "")
            or "DATABASE_INTEGRITY_FAILURE" in (ast.get_source_segment(source, node.exc) or "")
        )
    ]
    assert final_raise_lines
    for line in final_raise_lines:
        assert all(not (start <= line <= end) for start, end in handler_ranges)


def test_import_order_smoke_package_writer_transaction_and_preflight_modules() -> None:
    orders = (
        (
            "import ge_nwp_coordinator",
            "import ge_nwp_coordinator.sqlite_writer_session",
            "import ge_nwp_coordinator.sqlite_transition_transaction",
            "import ge_nwp_coordinator.sqlite_global_stop_preflight_contracts",
        ),
        (
            "import ge_nwp_coordinator.sqlite_transition_transaction",
            "import ge_nwp_coordinator.sqlite_global_stop_preflight_contracts",
            "import ge_nwp_coordinator.sqlite_writer_session",
            "import ge_nwp_coordinator",
        ),
    )
    for lines in orders:
        code = "\n".join(
            (
                *lines,
                "from ge_nwp_coordinator.state_store import GlobalStopApplyPreflightFailureReason",
                "assert GlobalStopApplyPreflightFailureReason.INVALID_COMMAND.value == 'global_stop_apply_invalid_command'",
            )
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env={
                **os.environ,
                "PYTHONPATH": str(ROOT / "src"),
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr


def test_package_exports_state_store_migration_and_public_transition_regression(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_exports = set(ge_nwp_coordinator.__all__)
    assert "_run_atomic_global_stop_apply" not in PACKAGE_EXPORT_PATH.read_text(encoding="utf-8")
    assert not hasattr(ge_nwp_coordinator, "_run_atomic_global_stop_apply")
    assert "sqlite_transition_transaction" not in package_exports
    assert not hasattr(StateStore, "apply_global_stop_update")
    assert sorted(path.name for path in MIGRATION_DIR.glob("0002*")) == [
        "0002_development_program_and_effect_state.sql"
    ]
    assert _sha256(MIGRATION_DIR / "0001_initial.sql") == MIGRATION_0001_SHA256

    with make_coherent_transition_fixture_for_test(
        tmp_path,
        ready_dependency=True,
        dependencies_satisfied=True,
    ) as fixture:
        _patch_clock(monkeypatch)
        result = fixture.writer_session.apply_transition(fixture.command)
        assert type(result).__name__ == "CommittedTransition"
        assert result.replayed is False
        assert transition_event_count_for_test(fixture) == 1
        assert global_stop_event_count_for_test(fixture) == 0


def test_public_global_stop_does_not_provision_or_mutate_receipts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "missing") as fixture:
        decision = _decision()
        command = _command(decision_ref=decision.decision_ref)

        _assert_conflict(
            fixture.writer_session.apply_global_stop_update(command, decision),
            "validation_failed",
        )
        assert _receipt_rows(fixture) == ()

    with make_coherent_transition_fixture_for_test(tmp_path / "accepted") as fixture:
        decision = _decision()
        command = _command(decision_ref=decision.decision_ref)
        _seed_receipt(fixture, decision)
        _patch_clock(monkeypatch)
        traced_sql: list[str] = []
        original_open = transaction_module._open_bound_existing_sqlite_connection

        def tracing_open(*args: object, **kwargs: object) -> sqlite3.Connection:
            connection = original_open(*args, **kwargs)
            connection.set_trace_callback(traced_sql.append)
            return connection

        monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", tracing_open)
        _assert_committed(fixture.writer_session.apply_global_stop_update(command, decision), replayed=False)

        normalized = "\n".join(statement.upper() for statement in traced_sql)
        assert "FROM GLOBAL_STOP_OPERATOR_DECISION_RECEIPTS" in normalized
        assert "INSERT INTO GLOBAL_STOP_OPERATOR_DECISION_RECEIPTS" not in normalized
        assert "UPDATE GLOBAL_STOP_OPERATOR_DECISION_RECEIPTS" not in normalized
        assert "DELETE FROM GLOBAL_STOP_OPERATOR_DECISION_RECEIPTS" not in normalized
        assert "INSERT INTO GLOBAL_STOP_EVENTS" in normalized
        assert "UPDATE GLOBAL_STOP_CURRENT" in normalized


def test_docs_current_boundary_assertions() -> None:
    b4c = (ROOT / ".docs/b4c-public-global-stop-delegation.md").read_text(encoding="utf-8")
    normalized_b4c = " ".join(b4c.split())
    assert "B4c implements guarded public global-stop delegation" in normalized_b4c
    assert "operation guard succeeds before any private import" in normalized_b4c
    assert "caller decision remains comparison material only" in normalized_b4c
    assert "Receipt provisioning remains a separately governed reopened seam" in normalized_b4c
    assert "no generic delegate catch-all" in normalized_b4c
    assert "historical schema-0001 B3/B4 graph hosted in a temporary current-generation-2, terminal-0002 fixture" in normalized_b4c
    assert "Migration `0002` is the current physical C2B2 Slice-1 extension" in normalized_b4c
    assert "B4c itself neither adds nor consumes C2B runtime behavior" in normalized_b4c
    assert "Tests may seed receipt rows only in temporary schema-0001 fixtures" not in b4c
    assert "There is still no migration `0002`." not in b4c
    writer_authority = (ROOT / ".docs/writer-session-authority.md").read_text(encoding="utf-8")
    assert "B4c adds operation-guarded public global-stop delegation" in writer_authority
    authority = (ROOT / ".docs/authority-boundaries.md").read_text(encoding="utf-8")
    assert "B4c guarded public global-stop delegation exists" in authority


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()
