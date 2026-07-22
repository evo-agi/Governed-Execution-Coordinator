from __future__ import annotations

import ast
import builtins
from enum import Enum
import os
from pathlib import Path
import sqlite3
import threading
import time
import traceback
from typing import Any

import pytest

from b3_coherent_transition_fixture import (
    FIXTURE_TIMESTAMP,
    global_stop_event_count_for_test,
    make_coherent_transition_fixture_for_test,
    read_back_fixture_for_test,
    transition_event_count_for_test,
)
from ge_nwp_coordinator.persistence_contracts import SQLITE_SIGNED_INT_MAX
from ge_nwp_coordinator.sqlite_connection import open_existing_sqlite_connection
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import initialize_database
import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module
import ge_nwp_coordinator.sqlite_writer_session as writer_module
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.state_machine import TransitionCommand, TransitionEventOutcome, WorkItemState
from ge_nwp_coordinator.state_store import (
    CommittedTransition,
    TransitionApplyPreflightError,
    TransitionApplyPreflightFailureReason,
    TransitionConflict,
    WriterSessionError,
    WriterSessionFailureReason,
)
from test_b3c1b_rollback_only_writer_fencing import _replace_writer_row
from test_sqlite_b2c_writer_session import _run_writer_attempt, _wait_for_child_result


ROOT = Path(__file__).resolve().parents[1]
WRITER_SESSION_PATH = ROOT / "src/ge_nwp_coordinator/sqlite_writer_session.py"
PRIVATE_SENTINEL = "b3c4c-private-sentinel-do-not-leak"


class _OtherPrivateReason(str, Enum):
    INVALID_COMMAND = "transition_dry_run_invalid_command"


class _FuturePrivateReason(str, Enum):
    FUTURE_REASON = "transition_dry_run_future_reason"


class _HostilePrivateReason:
    def __init__(self, hook_calls: list[str]) -> None:
        object.__setattr__(self, "_hook_calls", hook_calls)
        object.__setattr__(self, "_sentinel", PRIVATE_SENTINEL)

    def _record(self, hook_name: str) -> None:
        object.__getattribute__(self, "_hook_calls").append(hook_name)

    def __getattribute__(self, name: str) -> object:
        if name in {"_hook_calls", "_sentinel", "_record"}:
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
        "hostile",
        "_TransitionDryRunPreflightError",
        "transition_dry_run",
    ):
        assert forbidden not in rendered


def _assert_preflight_error(
    error: TransitionApplyPreflightError,
    reason: TransitionApplyPreflightFailureReason,
) -> None:
    assert type(error) is TransitionApplyPreflightError
    assert error.reason is reason
    assert str(error) == reason.value
    assert error.args == (reason.value,)
    assert repr(error) == "<TransitionApplyPreflightError>"
    assert error.__cause__ is None
    assert error.__context__ is None
    assert not getattr(error, "__notes__", ())
    rendered = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    for forbidden in (
        PRIVATE_SENTINEL,
        "_TransitionDryRunPreflightError",
        "_TransitionDryRunPreflightFailureReason",
        "transition_dry_run",
    ):
        assert forbidden not in rendered


def _assert_committed(result: object, *, replayed: bool) -> CommittedTransition:
    assert type(result) is CommittedTransition
    assert result.replayed is replayed
    return result


def _assert_conflict(result: object, conflict_class: str) -> TransitionConflict:
    assert type(result) is TransitionConflict
    assert result.conflict_class == conflict_class
    return result


def _reissue_command(command: TransitionCommand, **overrides: object) -> TransitionCommand:
    values: dict[str, object] = {
        "work_item_id": command.work_item_id,
        "idempotency_key": command.idempotency_key,
        "expected_version": command.expected_version,
        "target_state": command.target_state,
        "lease_identity_decision_ref": command.lease_identity_decision_ref,
        "authorization_decision_ref": command.authorization_decision_ref,
        "global_stop_ref": command.global_stop_ref,
        "global_stop_version": command.global_stop_version,
        "dependency_decision_ref": command.dependency_decision_ref,
        "evidence_refs": command.evidence_refs,
        "safe_failure_class": command.safe_failure_class,
        "budget_cost": command.budget_cost,
    }
    values.update(overrides)
    return TransitionCommand.create(**values)  # type: ignore[arg-type]


def _delete_all_rows_for_test(location: CoordinatorStateLocation, table_name: str) -> None:
    connection = sqlite3.connect(location.database_path)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(f"DELETE FROM {table_name}")
        connection.commit()
    finally:
        connection.close()


def _patch_clock(monkeypatch: pytest.MonkeyPatch, timestamp: str = FIXTURE_TIMESTAMP) -> None:
    monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: timestamp)


def _raise(error: BaseException) -> object:
    raise error


def test_public_delegate_call_uses_one_operation_guard_exact_lease_and_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        resource = fixture.writer_session._resource
        original_guard = resource.operation_guard
        sentinel = TransitionConflict("validation_failed")
        calls: list[tuple[object, object]] = []
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

        def delegate(*, operation_lease: object, transition_command: object) -> TransitionConflict:
            calls.append((operation_lease, transition_command))
            assert operation_lease is leases[0]
            assert transition_command is fixture.command
            assert _operation_count(resource) == 1
            return sentinel

        monkeypatch.setattr(resource, "operation_guard", TrackingGuard)
        monkeypatch.setattr(transaction_module, "_run_atomic_transition_apply", delegate)

        result = fixture.writer_session.apply_transition(fixture.command)

        assert result is sentinel
        assert calls == [(leases[0], fixture.command)]
        assert entered == 1
        assert exited == 1
        assert _operation_count(resource) == 0
        assert resource._mutation_slot is None


@pytest.mark.parametrize(
    ("command_factory", "expected_reason"),
    (
        (
            lambda fixture: None,
            TransitionApplyPreflightFailureReason.INVALID_COMMAND,
        ),
        (
            lambda fixture: _reissue_command(fixture.command, budget_cost=1),
            TransitionApplyPreflightFailureReason.UNSUPPORTED_COMMAND,
        ),
    ),
)
def test_actual_private_preflight_maps_publicly_before_slot_sqlite_or_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command_factory: object,
    expected_reason: TransitionApplyPreflightFailureReason,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        calls = {"delegate": 0, "mutation": 0, "open": 0, "clock": 0}
        original_delegate = transaction_module._run_atomic_transition_apply
        original_mutation_factory = writer_module._MUTATION_LEASE_FACTORY

        def counted_delegate(*, operation_lease: object, transition_command: object) -> object:
            calls["delegate"] += 1
            return original_delegate(operation_lease=operation_lease, transition_command=transition_command)

        def mutation_factory(**kwargs: object) -> object:
            calls["mutation"] += 1
            return original_mutation_factory(**kwargs)

        def fail_open(*args: object, **kwargs: object) -> object:
            calls["open"] += 1
            raise AssertionError("public preflight opened SQLite")

        def fail_clock() -> str:
            calls["clock"] += 1
            raise AssertionError("public preflight captured the transaction clock")

        monkeypatch.setattr(transaction_module, "_run_atomic_transition_apply", counted_delegate)
        monkeypatch.setattr(writer_module, "_MUTATION_LEASE_FACTORY", mutation_factory)
        monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_open)
        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", fail_clock)

        with pytest.raises(TransitionApplyPreflightError) as exc_info:
            fixture.writer_session.apply_transition(command_factory(fixture))  # type: ignore[operator]

        _assert_preflight_error(exc_info.value, expected_reason)
        assert calls == {"delegate": 1, "mutation": 0, "open": 0, "clock": 0}
        assert fixture.writer_session._resource._mutation_slot is None
        assert transition_event_count_for_test(fixture) == 0
        _assert_no_sqlite_sidecars(fixture.location)


def test_malformed_private_preflight_reasons_are_database_integrity_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from ge_nwp_coordinator.sqlite_transition_dry_run_contracts import (
        _TransitionDryRunPreflightError,
        _TransitionDryRunPreflightFailureReason,
    )

    class SubclassedPrivatePreflight(_TransitionDryRunPreflightError):
        pass

    def exact_private_error_with_reason(reason: object) -> _TransitionDryRunPreflightError:
        error = _TransitionDryRunPreflightError.__new__(_TransitionDryRunPreflightError)
        RuntimeError.__init__(error, PRIVATE_SENTINEL)
        error.reason = reason
        return error

    hook_calls: list[str] = []
    original_mutation_factory = writer_module._MUTATION_LEASE_FACTORY
    missing_reason = _TransitionDryRunPreflightError.__new__(_TransitionDryRunPreflightError)
    RuntimeError.__init__(missing_reason, PRIVATE_SENTINEL)
    malformed_errors = (
        exact_private_error_with_reason("transition_dry_run_invalid_command"),
        exact_private_error_with_reason(_OtherPrivateReason.INVALID_COMMAND),
        exact_private_error_with_reason(_HostilePrivateReason(hook_calls)),
        exact_private_error_with_reason(_FuturePrivateReason.FUTURE_REASON),
        missing_reason,
        SubclassedPrivatePreflight(_TransitionDryRunPreflightFailureReason.INVALID_COMMAND),
    )

    for index, private_error in enumerate(malformed_errors):
        with monkeypatch.context() as patch:
            with make_coherent_transition_fixture_for_test(tmp_path / str(index)) as fixture:
                calls = {"mutation": 0, "open": 0}

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
                    "_run_atomic_transition_apply",
                    lambda *args, private_error=private_error, **kwargs: _raise(private_error),
                )

                with pytest.raises(SQLiteMutationStoreError) as exc_info:
                    fixture.writer_session.apply_transition(fixture.command)

                _assert_mutation_error(
                    exc_info.value,
                    SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value,
                )
                assert not isinstance(exc_info.value, TransitionApplyPreflightError)
                captured = capsys.readouterr()
                assert PRIVATE_SENTINEL not in captured.out
                assert PRIVATE_SENTINEL not in captured.err
                assert "transition_dry_run" not in captured.out
                assert "transition_dry_run" not in captured.err
                assert calls == {"mutation": 0, "open": 0}
                assert _operation_count(fixture.writer_session._resource) == 0
                assert fixture.writer_session._resource._mutation_slot is None
                assert transition_event_count_for_test(fixture) == 0
                assert fixture.writer_session.active is True

        assert hook_calls == []


def test_private_preflight_reason_access_failure_is_database_integrity_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from ge_nwp_coordinator.sqlite_transition_dry_run_contracts import _TransitionDryRunPreflightError

    class RaisingReasonDescriptor:
        def __get__(self, instance: object, owner: object = None) -> object:
            raise RuntimeError(PRIVATE_SENTINEL)

    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        calls = {"mutation": 0, "open": 0}
        original_mutation_factory = writer_module._MUTATION_LEASE_FACTORY
        private_error = _TransitionDryRunPreflightError.__new__(_TransitionDryRunPreflightError)
        RuntimeError.__init__(private_error, PRIVATE_SENTINEL)

        def mutation_factory(**kwargs: object) -> object:
            calls["mutation"] += 1
            return original_mutation_factory(**kwargs)

        def fail_open(*args: object, **kwargs: object) -> object:
            calls["open"] += 1
            raise AssertionError("reason access failure opened SQLite")

        with monkeypatch.context() as patch:
            patch.setattr(writer_module, "_MUTATION_LEASE_FACTORY", mutation_factory)
            patch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_open)
            patch.setattr(_TransitionDryRunPreflightError, "reason", RaisingReasonDescriptor())
            patch.setattr(
                transaction_module,
                "_run_atomic_transition_apply",
                lambda *args, **kwargs: _raise(private_error),
            )

            with pytest.raises(SQLiteMutationStoreError) as exc_info:
                fixture.writer_session.apply_transition(fixture.command)

        _assert_mutation_error(
            exc_info.value,
            SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value,
        )
        assert not isinstance(exc_info.value, TransitionApplyPreflightError)
        captured = capsys.readouterr()
        assert PRIVATE_SENTINEL not in captured.out
        assert PRIVATE_SENTINEL not in captured.err
        assert "transition_dry_run" not in captured.out
        assert "transition_dry_run" not in captured.err
        assert calls == {"mutation": 0, "open": 0}
        assert _operation_count(fixture.writer_session._resource) == 0
        assert fixture.writer_session._resource._mutation_slot is None
        assert transition_event_count_for_test(fixture) == 0
        assert fixture.writer_session.active is True

        with pytest.raises(TransitionApplyPreflightError) as recovered:
            fixture.writer_session.apply_transition(None)  # type: ignore[arg-type]
        _assert_preflight_error(recovered.value, TransitionApplyPreflightFailureReason.INVALID_COMMAND)


def test_import_load_failure_is_pre_delegate_mutation_failed_and_session_recovers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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

    try:
        with monkeypatch.context() as patch:
            patch.setattr(resource, "operation_guard", TrackingGuard)
            patch.setattr(writer_module, "_MUTATION_LEASE_FACTORY", mutation_factory)
            patch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_sqlite_open)
            patch.delattr(transaction_module, "_run_atomic_transition_apply")

            with pytest.raises(SQLiteMutationStoreError) as exc_info:
                session.apply_transition(None)  # type: ignore[arg-type]

        _assert_mutation_error(exc_info.value, SQLiteMutationStoreErrorCode.MUTATION_FAILED.value)
        assert entered == 1
        assert exited == 1
        assert mutation_calls == 0
        assert sqlite_calls == 0
        assert _operation_count(resource) == 0
        assert resource._mutation_slot is None
        assert session.active is True

        with pytest.raises(TransitionApplyPreflightError) as recovered:
            session.apply_transition(None)  # type: ignore[arg-type]
        _assert_preflight_error(recovered.value, TransitionApplyPreflightFailureReason.INVALID_COMMAND)
    finally:
        session.close()


def test_session_local_precedence_blocks_import_and_delegate_for_closed_and_inactive_sessions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_imports: list[str] = []
    original_import = builtins.__import__

    def fail_private_import(name: str, globals: object = None, locals: object = None, fromlist: object = (), level: int = 0) -> object:
        if name in {
            "ge_nwp_coordinator.sqlite_transition_dry_run_contracts",
            "ge_nwp_coordinator.sqlite_transition_transaction",
        }:
            private_imports.append(name)
            raise AssertionError("session guard failure reached private import")
        return original_import(name, globals, locals, fromlist, level)

    def fail_delegate(*args: object, **kwargs: object) -> object:
        raise AssertionError("session guard failure reached delegate")

    monkeypatch.setattr(transaction_module, "_run_atomic_transition_apply", fail_delegate)
    monkeypatch.setattr(builtins, "__import__", fail_private_import)

    closed_location = _location(tmp_path / "closed")
    initialize_database(closed_location)
    closed = acquire_sqlite_writer_session(closed_location)
    closed.close()
    with pytest.raises(WriterSessionError) as closed_error:
        closed.apply_transition(None)  # type: ignore[arg-type]
    assert closed_error.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED

    inactive_location = _location(tmp_path / "inactive")
    initialize_database(inactive_location)
    inactive = acquire_sqlite_writer_session(inactive_location)
    retained_lock = inactive._resource._authority_lock
    assert retained_lock is not None
    retained_lock.close()
    with pytest.raises(WriterSessionError) as inactive_error:
        inactive.apply_transition(None)  # type: ignore[arg-type]
    assert inactive_error.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED
    inactive.close()

    assert private_imports == []


def test_public_transition_slot_contention_remains_private_nonblocking_and_releases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(
        tmp_path,
        ready_dependency=True,
        dependencies_satisfied=True,
    ) as fixture:
        _patch_clock(monkeypatch)
        resource = fixture.writer_session._resource
        original_mutation_factory = writer_module._MUTATION_LEASE_FACTORY
        original_open = transaction_module._open_bound_existing_sqlite_connection
        slot_acquired = threading.Event()
        release_first = threading.Event()
        open_calls = 0
        first: dict[str, object] = {}
        second: dict[str, object] = {}

        def holding_mutation_factory(**kwargs: object) -> object:
            mutation_lease = original_mutation_factory(**kwargs)
            slot_acquired.set()
            _wait_for_event(release_first)
            return mutation_lease

        def tracing_open(*args: object, **kwargs: object) -> sqlite3.Connection:
            nonlocal open_calls
            open_calls += 1
            return original_open(*args, **kwargs)

        def call_first() -> None:
            try:
                first["result"] = fixture.writer_session.apply_transition(fixture.command)
            except BaseException as exc:  # noqa: BLE001 - test collects thread failures
                first["error"] = exc

        def call_second() -> None:
            try:
                second["result"] = fixture.writer_session.apply_transition(fixture.command)
            except BaseException as exc:  # noqa: BLE001 - test collects thread failures
                second["error"] = exc

        monkeypatch.setattr(writer_module, "_MUTATION_LEASE_FACTORY", holding_mutation_factory)
        monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", tracing_open)

        first_thread = threading.Thread(target=call_first)
        first_thread.start()
        _wait_for_event(slot_acquired)
        assert resource._mutation_slot is not None
        assert open_calls == 0

        second_thread = threading.Thread(target=call_second)
        second_thread.start()
        _join_thread(second_thread)

        second_error = second.get("error")
        assert isinstance(second_error, WriterSessionError)
        assert second_error.reason is WriterSessionFailureReason.WRITER_SESSION_MUTATION_IN_PROGRESS
        assert "result" not in second
        assert open_calls == 0
        assert resource._mutation_slot is not None

        release_first.set()
        _join_thread(first_thread)

        committed = _assert_committed(first.get("result"), replayed=False)
        assert committed.event.outcome is TransitionEventOutcome.ACCEPTED
        assert "error" not in first
        assert open_calls == 1
        assert resource._mutation_slot is None
        assert _operation_count(resource) == 0
        assert transition_event_count_for_test(fixture) == 1


def test_same_thread_close_during_public_transition_keeps_existing_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        resource = fixture.writer_session._resource

        def delegate(*, operation_lease: object, transition_command: object) -> object:
            assert _operation_count(resource) == 1
            fixture.writer_session.close()
            raise AssertionError("close during operation unexpectedly returned")

        monkeypatch.setattr(transaction_module, "_run_atomic_transition_apply", delegate)

        with pytest.raises(WriterSessionError) as exc_info:
            fixture.writer_session.apply_transition(fixture.command)

        assert exc_info.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSE_DURING_OPERATION
        assert resource._state == writer_module._ACTIVE
        assert _operation_count(resource) == 0
        assert resource._mutation_slot is None
        assert fixture.writer_session.active is True


def test_cross_thread_close_waits_for_public_delegate_and_operation_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        resource = fixture.writer_session._resource
        started = threading.Event()
        release_delegate = threading.Event()
        delegate_done = threading.Event()
        close_done = threading.Event()
        sentinel = TransitionConflict("validation_failed")
        result: dict[str, object] = {}
        close_errors: list[BaseException] = []

        def delegate(*, operation_lease: object, transition_command: object) -> TransitionConflict:
            assert _operation_count(resource) == 1
            started.set()
            _wait_for_event(release_delegate)
            assert _operation_count(resource) == 1
            delegate_done.set()
            return sentinel

        def call_apply() -> None:
            try:
                result["value"] = fixture.writer_session.apply_transition(fixture.command)
            except BaseException as exc:  # noqa: BLE001 - test collects thread failures
                result["error"] = exc

        def call_close() -> None:
            try:
                fixture.writer_session.close()
            except BaseException as exc:  # noqa: BLE001 - test collects thread failures
                close_errors.append(exc)
            finally:
                close_done.set()

        monkeypatch.setattr(transaction_module, "_run_atomic_transition_apply", delegate)

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
        assert delegate_done.is_set()
        assert close_done.is_set()
        assert _operation_count(resource) == 0
        assert resource._mutation_slot is None
        assert resource._state == writer_module._CLOSED


def test_fork_child_public_transition_fails_before_delegate_sqlite_or_parent_slot_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")

    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        resource = fixture.writer_session._resource

        def fail_delegate(*args: object, **kwargs: object) -> object:
            raise AssertionError("fork child reached transition delegate")

        monkeypatch.setattr(transaction_module, "_run_atomic_transition_apply", fail_delegate)
        before_sidecars = _sqlite_sidecars(fixture.location)
        read_fd, write_fd = os.pipe()
        child_pid = os.fork()
        if child_pid == 0:
            os.close(read_fd)
            try:
                try:
                    fixture.writer_session.apply_transition(None)  # type: ignore[arg-type]
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


def test_public_apply_real_atomic_committed_paths_and_exact_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(
        tmp_path / "accepted",
        ready_dependency=True,
        dependencies_satisfied=True,
    ) as fixture:
        _patch_clock(monkeypatch)

        fresh = _assert_committed(fixture.writer_session.apply_transition(fixture.command), replayed=False)
        replay = _assert_committed(fixture.writer_session.apply_transition(fixture.command), replayed=True)

        assert fresh.event.outcome is TransitionEventOutcome.ACCEPTED
        assert fresh.event.reason == "transition_accepted"
        assert replay.event == fresh.event
        assert replay.record == fresh.record
        assert transition_event_count_for_test(fixture) == 1
        assert global_stop_event_count_for_test(fixture) == 0

    with make_coherent_transition_fixture_for_test(tmp_path / "domain") as fixture:
        _patch_clock(monkeypatch)
        before = read_back_fixture_for_test(fixture).work_item.record

        result = _assert_committed(fixture.writer_session.apply_transition(fixture.command), replayed=False)

        assert result.event.outcome is TransitionEventOutcome.DOMAIN_REJECTED
        assert result.event.reason == "lease_not_authorized"
        assert result.record == before == fixture.work_item
        assert read_back_fixture_for_test(fixture).work_item.record == before
        assert transition_event_count_for_test(fixture) == 1
        assert global_stop_event_count_for_test(fixture) == 0


def test_public_apply_real_atomic_conflict_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "stale", existing_event=True) as fixture:
        _replace_writer_row(fixture.location, issuance_nonce_digest="0" * 64)
        before = transition_event_count_for_test(fixture)

        result = _assert_conflict(fixture.writer_session.apply_transition(fixture.command), "stale_writer_token")

        assert result.conflict_class == "stale_writer_token"
        assert transition_event_count_for_test(fixture) == before

    with make_coherent_transition_fixture_for_test(tmp_path / "idempotency", existing_event=True) as fixture:
        conflict_command = _reissue_command(
            fixture.command,
            target_state=WorkItemState.BLOCKED,
            safe_failure_class="operator_action_required",
        )

        result = _assert_conflict(
            fixture.writer_session.apply_transition(conflict_command),
            "idempotency_key_reuse_conflict",
        )

        assert result.conflict_class == "idempotency_key_reuse_conflict"
        assert transition_event_count_for_test(fixture) == 1

    for name, command_factory, expected in (
        ("missing", lambda fixture: fixture.command, "work_item_not_found"),
        ("expected", lambda fixture: _reissue_command(fixture.command, expected_version=2), "expected_version_conflict"),
        (
            "validation",
            lambda fixture: _reissue_command(
                fixture.command,
                lease_identity_decision_ref="lease-identity-missing",
            ),
            "validation_failed",
        ),
    ):
        with monkeypatch.context() as patch:
            with make_coherent_transition_fixture_for_test(tmp_path / name, ready_dependency=True) as fixture:
                _patch_clock(patch)
                if name == "missing":
                    _delete_all_rows_for_test(fixture.location, "work_items")

                result = _assert_conflict(fixture.writer_session.apply_transition(command_factory(fixture)), expected)

                assert result.conflict_class == expected
                assert transition_event_count_for_test(fixture) == 0


def test_public_apply_real_atomic_sequence_store_failure_and_commit_uncertainty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as sequence_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "sequence") as fixture:
            _patch_clock(sequence_patch)
            sequence_patch.setattr(
                transaction_module,
                "_read_transition_event_max_sequence",
                lambda capability: SQLITE_SIGNED_INT_MAX,
            )

            with pytest.raises(SQLiteMutationStoreError) as exc_info:
                fixture.writer_session.apply_transition(fixture.command)

            _assert_mutation_error(exc_info.value, SQLiteMutationStoreErrorCode.EVENT_SEQUENCE_EXHAUSTED.value)
            assert transition_event_count_for_test(fixture) == 0

    with monkeypatch.context() as store_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "store", ready_dependency=True) as fixture:
            _patch_clock(store_patch)
            store_patch.setattr(
                transaction_module,
                "_read_transition_event_max_sequence",
                lambda capability: (_ for _ in ()).throw(transaction_module._mutation_failed()),
            )

            with pytest.raises(SQLiteMutationStoreError) as exc_info:
                fixture.writer_session.apply_transition(fixture.command)

            _assert_mutation_error(exc_info.value, SQLiteMutationStoreErrorCode.MUTATION_FAILED.value)
            assert transition_event_count_for_test(fixture) == 0

    with monkeypatch.context() as commit_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "commit", ready_dependency=True) as fixture:
            _patch_clock(commit_patch)
            commit_error = transaction_module._commit_outcome_unknown()
            commit_patch.setattr(transaction_module, "_commit_transaction", lambda connection: commit_error)

            with pytest.raises(SQLiteMutationStoreError) as exc_info:
                fixture.writer_session.apply_transition(fixture.command)

            assert exc_info.value is commit_error
            _assert_mutation_error(exc_info.value, SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN.value)
            assert transition_event_count_for_test(fixture) == 0


def test_closed_delegate_errors_and_unexpected_exceptions_are_not_translated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed_errors = (
        WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_CLOSED),
        SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN),
    )
    for index, expected_error in enumerate(closed_errors):
        with monkeypatch.context() as patch:
            with make_coherent_transition_fixture_for_test(tmp_path / f"closed-{index}") as fixture:
                patch.setattr(
                    transaction_module,
                    "_run_atomic_transition_apply",
                    lambda *args, expected_error=expected_error, **kwargs: _raise(expected_error),
                )

                with pytest.raises(type(expected_error)) as exc_info:
                    fixture.writer_session.apply_transition(fixture.command)

                assert exc_info.value is expected_error

    with make_coherent_transition_fixture_for_test(tmp_path / "unexpected") as fixture:
        unexpected = RuntimeError(PRIVATE_SENTINEL)
        monkeypatch.setattr(
            transaction_module,
            "_run_atomic_transition_apply",
            lambda *args, **kwargs: _raise(unexpected),
        )

        with pytest.raises(RuntimeError) as exc_info:
            fixture.writer_session.apply_transition(fixture.command)

        assert exc_info.value is unexpected


def test_global_stop_public_apply_remains_unavailable_without_transaction_import(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    private_imports: list[str] = []
    original_import = builtins.__import__

    def fail_private_import(name: str, globals: object = None, locals: object = None, fromlist: object = (), level: int = 0) -> object:
        if name == "ge_nwp_coordinator.sqlite_transition_transaction":
            private_imports.append(name)
            raise AssertionError("global-stop public method imported transition transaction")
        return original_import(name, globals, locals, fromlist, level)

    try:
        monkeypatch.setattr(builtins, "__import__", fail_private_import)
        with pytest.raises(WriterSessionError) as exc_info:
            session.apply_global_stop_update(None, None)  # type: ignore[arg-type]
        assert exc_info.value.reason is WriterSessionFailureReason.WRITER_SESSION_MUTATION_UNAVAILABLE
        assert private_imports == []
        assert _operation_count(session._resource) == 0
        assert session._resource._mutation_slot is None
    finally:
        session.close()


def test_static_public_transition_method_is_guarded_delegation_without_sql_or_transaction_ownership() -> None:
    source = WRITER_SESSION_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    sqlite_session = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "_SQLiteWriterSession"
    )
    apply_transition = next(
        node for node in sqlite_session.body
        if isinstance(node, ast.FunctionDef) and node.name == "apply_transition"
    )
    apply_global_stop = next(
        node for node in sqlite_session.body
        if isinstance(node, ast.FunctionDef) and node.name == "apply_global_stop_update"
    )
    method_source = ast.get_source_segment(source, apply_transition)
    global_stop_source = ast.get_source_segment(source, apply_global_stop)
    assert method_source is not None
    assert global_stop_source is not None

    forbidden_tokens = (
        "sqlite3",
        "connect(",
        ".execute(",
        ".cursor",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
        "_read_transition_event_max_sequence",
        "next_transition_event_sequence",
        "INSERT INTO",
        "UPDATE work_items",
        "TransitionContext",
        "evaluate_transition",
        "_create_sqlite_transition_read_capability",
        "_TransitionTransactionController",
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
    )
    for token in forbidden_tokens:
        assert token not in method_source

    top_level_private_imports = [
        node for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module in {
            "ge_nwp_coordinator.sqlite_transition_dry_run_contracts",
            "ge_nwp_coordinator.sqlite_transition_transaction",
        }
    ]
    assert top_level_private_imports == []

    private_imports = [
        node for node in ast.walk(apply_transition)
        if isinstance(node, ast.ImportFrom)
        and node.module in {
            "ge_nwp_coordinator.sqlite_transition_dry_run_contracts",
            "ge_nwp_coordinator.sqlite_transition_transaction",
        }
    ]
    assert {node.module for node in private_imports} == {
        "ge_nwp_coordinator.sqlite_transition_dry_run_contracts",
        "ge_nwp_coordinator.sqlite_transition_transaction",
    }
    assert sum(len(node.names) for node in private_imports) == 3

    operation_guard_calls = [
        node for node in ast.walk(apply_transition)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "operation_guard"
    ]
    assert len(operation_guard_calls) == 1

    delegate_calls = [
        node for node in ast.walk(apply_transition)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_run_atomic_transition_apply"
    ]
    assert len(delegate_calls) == 1
    assert delegate_calls[0].args == []
    assert [keyword.arg for keyword in delegate_calls[0].keywords] == [
        "operation_lease",
        "transition_command",
    ]
    assert isinstance(delegate_calls[0].keywords[0].value, ast.Name)
    assert delegate_calls[0].keywords[0].value.id == "operation_lease"
    assert isinstance(delegate_calls[0].keywords[1].value, ast.Name)
    assert delegate_calls[0].keywords[1].value.id == "transition_command"

    private_error_gate = "type(caught_private_preflight) is not _TransitionDryRunPreflightError"
    reason_access = 'object.__getattribute__(caught_private_preflight, "reason")'
    private_reason_gate = "type(private_preflight_reason) is not _TransitionDryRunPreflightFailureReason"
    invalid_mapping = "private_preflight_reason is _TransitionDryRunPreflightFailureReason.INVALID_COMMAND"
    unsupported_mapping = "private_preflight_reason is _TransitionDryRunPreflightFailureReason.UNSUPPORTED_COMMAND"
    assert private_error_gate in method_source
    assert reason_access in method_source
    assert private_reason_gate in method_source
    assert invalid_mapping in method_source
    assert unsupported_mapping in method_source
    assert method_source.index(private_error_gate) < method_source.index(reason_access)
    assert method_source.index(reason_access) < method_source.index(private_reason_gate)
    assert method_source.index(private_reason_gate) < method_source.index(invalid_mapping)
    assert method_source.index(private_reason_gate) < method_source.index(unsupported_mapping)
    assert "SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE" in method_source
    assert "SQLiteMutationStoreErrorCode.MUTATION_FAILED" in method_source
    assert "caught_private_preflight = None" in method_source
    assert "private_preflight_reason = None" in method_source

    try_nodes = [node for node in ast.walk(apply_transition) if isinstance(node, ast.Try)]
    delegate_try = next(
        node for node in try_nodes
        if any(
            nested is delegate_calls[0]
            for statement in node.body
            for nested in ast.walk(statement)
        )
    )
    assert [ast.unparse(handler.type) for handler in delegate_try.handlers] == ["_TransitionDryRunPreflightError"]

    broad_handlers = [
        handler for handler in ast.walk(apply_transition)
        if isinstance(handler, ast.ExceptHandler)
        and isinstance(handler.type, ast.Name)
        and handler.type.id == "Exception"
    ]
    assert len(broad_handlers) == 2
    for try_node in try_nodes:
        if any(handler in broad_handlers for handler in try_node.handlers):
            assert not any(
                nested is delegate_calls[0]
                for statement in try_node.body
                for nested in ast.walk(statement)
            )
    private_handlers = [
        handler for handler in ast.walk(apply_transition)
        if isinstance(handler, ast.ExceptHandler)
        and isinstance(handler.type, ast.Name)
        and handler.type.id == "_TransitionDryRunPreflightError"
    ]
    assert len(private_handlers) == 1
    assert private_handlers[0].lineno > delegate_calls[0].lineno
    handler_ranges = [
        (handler.lineno, handler.end_lineno)
        for handler in ast.walk(apply_transition)
        if isinstance(handler, ast.ExceptHandler)
    ]
    final_raise_lines = [
        node.lineno for node in ast.walk(apply_transition)
        if isinstance(node, ast.Raise)
        and node.exc is not None
        and (
            "TransitionApplyPreflightError" in (ast.get_source_segment(source, node.exc) or "")
            or "DATABASE_INTEGRITY_FAILURE" in (ast.get_source_segment(source, node.exc) or "")
        )
    ]
    assert final_raise_lines
    for line in final_raise_lines:
        assert all(not (start <= line <= end) for start, end in handler_ranges)

    assert "_run_atomic_transition_apply" not in global_stop_source
    assert "sqlite_transition_transaction" not in global_stop_source
    assert "WRITER_SESSION_MUTATION_UNAVAILABLE" in global_stop_source
