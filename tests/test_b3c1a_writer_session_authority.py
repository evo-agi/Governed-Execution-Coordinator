from __future__ import annotations

from dataclasses import replace
import gc
import inspect
import os
from pathlib import Path
import time
import traceback
import threading
import weakref

import pytest

import ge_nwp_coordinator
import ge_nwp_coordinator.sqlite_writer_session as writer_module
from ge_nwp_coordinator.sqlite_migration import initialize_database
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.sqlite_writer_state import _DurableWriterIssuance, _parse_writer_ownership_rows
from ge_nwp_coordinator.state_store import WriterSessionError, WriterSessionFailureReason
from test_sqlite_b2c_writer_session import (
    _join_thread,
    _location,
    _operation_count,
    _run_writer_attempt,
    _wait_for_child_result,
    _wait_for_event,
    _writer_rows,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"


def _managed_session(tmp_path: Path):
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    return location, session


def _durable_issuance(location) -> _DurableWriterIssuance:
    issuance = _parse_writer_ownership_rows(_writer_rows(location))
    assert issuance is not None
    return issuance


def _assert_writer_error(exc: pytest.ExceptionInfo[WriterSessionError], reason: WriterSessionFailureReason) -> None:
    assert exc.value.reason is reason
    assert str(exc.value) == reason.value
    assert exc.value.args == (reason.value,)


def _assert_no_private_error_detail(rendered: str, *private_values: object) -> None:
    lowered = rendered.lower()
    for forbidden in ("proof", "digest", "mismatch", "token", "operation_id", "lifecycle_epoch"):
        assert forbidden not in lowered
    for value in private_values:
        if value is not None:
            assert str(value) not in rendered


def test_slot_acquisition_contention_and_release_without_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, session = _managed_session(tmp_path)
    resource = session._resource
    sqlite_open_calls = 0

    def fail_if_sqlite_opens(*args, **kwargs):
        nonlocal sqlite_open_calls
        sqlite_open_calls += 1
        raise AssertionError("B3c1a slot path opened SQLite")

    monkeypatch.setattr(writer_module, "open_existing_sqlite_connection", fail_if_sqlite_opens)
    first_operation = resource.operation_guard(session)
    second_operation = resource.operation_guard(session)
    try:
        first_mutation = first_operation._acquire_mutation_lease()
        assert resource._mutation_slot is not None
        first_operation._require_active_mutation_authority()

        started = time.monotonic()
        with pytest.raises(WriterSessionError) as same_operation_error:
            first_operation._acquire_mutation_lease()
        assert time.monotonic() - started < 0.5
        _assert_writer_error(
            same_operation_error,
            WriterSessionFailureReason.WRITER_SESSION_MUTATION_IN_PROGRESS,
        )

        started = time.monotonic()
        with pytest.raises(WriterSessionError) as other_operation_error:
            second_operation._acquire_mutation_lease()
        assert time.monotonic() - started < 0.5
        _assert_writer_error(
            other_operation_error,
            WriterSessionFailureReason.WRITER_SESSION_MUTATION_IN_PROGRESS,
        )

        first_mutation._close()
        assert resource._mutation_slot is None
        second_mutation = second_operation._acquire_mutation_lease()
        second_operation._require_active_mutation_authority()
        second_mutation._close()
        assert resource._mutation_slot is None
        assert sqlite_open_calls == 0
    finally:
        second_operation._close()
        first_operation._close()
        session.close()


def test_release_identity_duplicate_stale_wrong_operation_thread_and_fork(
    tmp_path: Path,
) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location, session = _managed_session(tmp_path)
    resource = session._resource
    first_operation = resource.operation_guard(session)
    first_mutation = first_operation._acquire_mutation_lease()
    first_mutation._close()
    first_mutation._close()
    assert resource._mutation_slot is None

    first_mutation = first_operation._acquire_mutation_lease()
    assert resource._release_mutation_slot(
        operation_id=first_operation._operation_id + 1000,
        owner_pid=first_operation._owner_pid,
        owner_thread=first_operation._owner_thread,
        lifecycle_epoch=first_operation._lifecycle_epoch,
        token=first_mutation._token,
    ) is False
    first_operation._require_active_mutation_authority()

    thread_errors: list[BaseException] = []

    def wrong_thread_close() -> None:
        try:
            first_mutation._close()
        except BaseException as exc:  # noqa: BLE001 - private release must be a safe no-op
            thread_errors.append(exc)

    thread = threading.Thread(target=wrong_thread_close)
    thread.start()
    _join_thread(thread)
    assert thread_errors == []
    first_operation._require_active_mutation_authority()

    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        try:
            first_mutation._close()
            os.write(write_fd, b"child-close-ok")
        finally:
            os.close(write_fd)
            os._exit(0)

    os.close(write_fd)
    try:
        assert _wait_for_child_result(child_pid, read_fd) == "child-close-ok"
    finally:
        os.close(read_fd)
    first_operation._require_active_mutation_authority()

    first_operation._close()
    assert resource._mutation_slot is None
    second_operation = resource.operation_guard(session)
    second_mutation = second_operation._acquire_mutation_lease()
    first_mutation._close()
    second_operation._require_active_mutation_authority()
    second_mutation._close()
    second_operation._close()
    session.close()
    assert _run_writer_attempt(location) == "acquired:2"


def test_operation_finish_and_finalizer_defensively_clear_mutation_slot(tmp_path: Path) -> None:
    location, session = _managed_session(tmp_path)
    resource = session._resource

    operation = resource.operation_guard(session)
    mutation = operation._acquire_mutation_lease()
    operation._close()
    assert resource._mutation_slot is None
    mutation._close()

    next_operation = resource.operation_guard(session)
    next_mutation = next_operation._acquire_mutation_lease()
    next_mutation._close()
    next_operation._close()

    finalizer_operation = resource.operation_guard(session)
    finalizer_mutation = finalizer_operation._acquire_mutation_lease()
    operation_ref = weakref.ref(finalizer_operation)
    assert resource._mutation_slot is not None
    finalizer_operation = None
    finalizer_mutation = None
    gc.collect()
    assert operation_ref() is None
    assert _operation_count(resource) == 0
    assert resource._mutation_slot is None

    after_finalizer_operation = resource.operation_guard(session)
    after_finalizer_mutation = after_finalizer_operation._acquire_mutation_lease()
    after_finalizer_mutation._close()
    after_finalizer_operation._close()
    session.close()
    assert _run_writer_attempt(location) == "acquired:2"


def test_session_close_interaction_keeps_b2_cleanup_convergence(tmp_path: Path) -> None:
    location, session = _managed_session(tmp_path)
    resource = session._resource
    operation = resource.operation_guard(session)
    mutation = operation._acquire_mutation_lease()

    with pytest.raises(WriterSessionError) as same_thread_close:
        session.close()
    _assert_writer_error(
        same_thread_close,
        WriterSessionFailureReason.WRITER_SESSION_CLOSE_DURING_OPERATION,
    )
    assert resource._state == writer_module._ACTIVE
    assert resource._mutation_slot is not None

    authority_lock = resource._authority_lock
    original_close = authority_lock.close
    cleanup_started = threading.Event()
    release_cleanup = threading.Event()
    close_done = threading.Event()
    close_errors: list[BaseException] = []

    def slow_authority_close() -> None:
        assert resource._mutation_slot is None
        cleanup_started.set()
        _wait_for_event(release_cleanup, timeout=5.0)
        original_close()

    authority_lock.close = slow_authority_close

    def close_session() -> None:
        try:
            session.close()
        except BaseException as exc:  # noqa: BLE001 - thread failure must be visible
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

    release_errors: list[BaseException] = []

    def finish_operation() -> None:
        try:
            operation._close()
        except BaseException as exc:  # noqa: BLE001 - thread failure must be visible
            release_errors.append(exc)

    releaser = threading.Thread(target=finish_operation)
    releaser.start()
    _wait_for_event(cleanup_started)
    assert resource._mutation_slot is None
    mutation._close()
    assert close_done.is_set() is False
    release_cleanup.set()
    _join_thread(releaser)
    _join_thread(closer)
    assert release_errors == []
    assert close_errors == []
    assert close_done.is_set()
    assert resource._state == writer_module._CLOSED
    assert resource._credential is None
    assert resource._authority_lock is None
    assert _run_writer_attempt(location) == "acquired:2"


def test_active_authority_checks_fail_closed_without_new_public_reason(tmp_path: Path) -> None:
    location, session = _managed_session(tmp_path)
    resource = session._resource
    operation = resource.operation_guard(session)

    with pytest.raises(WriterSessionError) as no_slot_error:
        operation._require_active_mutation_authority()
    _assert_writer_error(no_slot_error, WriterSessionFailureReason.WRITER_SESSION_CLOSED)

    mutation = operation._acquire_mutation_lease()
    operation._require_active_mutation_authority()

    thread_results: list[str] = []

    def wrong_thread_require() -> None:
        try:
            operation._require_active_mutation_authority()
        except WriterSessionError as exc:
            thread_results.append(exc.reason.value)
        else:
            thread_results.append("unexpected-pass")

    thread = threading.Thread(target=wrong_thread_require)
    thread.start()
    _join_thread(thread)
    assert thread_results == [WriterSessionFailureReason.WRITER_SESSION_CLOSED.value]
    operation._require_active_mutation_authority()

    mutation._close()
    with pytest.raises(WriterSessionError) as closed_mutation_error:
        operation._require_active_mutation_authority()
    _assert_writer_error(closed_mutation_error, WriterSessionFailureReason.WRITER_SESSION_CLOSED)

    operation._close()
    with pytest.raises(WriterSessionError) as closed_operation_error:
        operation._require_active_mutation_authority()
    _assert_writer_error(closed_operation_error, WriterSessionFailureReason.WRITER_SESSION_CLOSED)
    session.close()
    assert _run_writer_attempt(location) == "acquired:2"


def test_inactive_retained_authority_lock_clears_slot_and_closes_session(tmp_path: Path) -> None:
    location, session = _managed_session(tmp_path)
    resource = session._resource
    operation = resource.operation_guard(session)
    operation._acquire_mutation_lease()
    retained_lock = resource._authority_lock

    retained_lock.close()
    with pytest.raises(WriterSessionError) as inactive_lock_error:
        operation._require_active_mutation_authority()
    _assert_writer_error(inactive_lock_error, WriterSessionFailureReason.WRITER_SESSION_CLOSED)
    assert resource._mutation_slot is None
    operation._close()
    assert resource._state == writer_module._CLOSED
    assert resource._credential is None
    assert resource._authority_lock is None
    session.close()
    assert _run_writer_attempt(location) == "acquired:2"


def test_process_mismatch_private_authority_check_fails_in_fork_child(tmp_path: Path) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location, session = _managed_session(tmp_path)
    resource = session._resource
    operation = resource.operation_guard(session)
    mutation = operation._acquire_mutation_lease()

    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        try:
            try:
                operation._require_active_mutation_authority()
            except WriterSessionError as exc:
                result = exc.reason.value
            else:
                result = "unexpected-pass"
            os.write(write_fd, result.encode("ascii"))
        finally:
            os.close(write_fd)
            os._exit(0)

    os.close(write_fd)
    try:
        child_result = _wait_for_child_result(child_pid, read_fd)
    finally:
        os.close(read_fd)
    assert child_result == WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH.value
    operation._require_active_mutation_authority()
    mutation._close()
    operation._close()
    session.close()
    assert _run_writer_attempt(location) == "acquired:2"


def test_durable_issuance_verification_match_stale_and_private_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    location, session = _managed_session(tmp_path)
    issuance = _durable_issuance(location)
    resource = session._resource
    operation = resource.operation_guard(session)

    with pytest.raises(WriterSessionError) as no_slot_verify_error:
        operation._verify_durable_writer_issuance(issuance)
    _assert_writer_error(no_slot_verify_error, WriterSessionFailureReason.WRITER_SESSION_CLOSED)

    mutation = operation._acquire_mutation_lease()
    assert operation._verify_durable_writer_issuance(issuance) is writer_module._WriterIssuanceMatch.MATCH
    assert operation._verify_durable_writer_issuance(
        replace(issuance, acquired_at="2026-07-19T00:00:00Z")
    ) is writer_module._WriterIssuanceMatch.MATCH
    assert operation._verify_durable_writer_issuance(
        replace(issuance, writer_ref="writer-other")
    ) is writer_module._WriterIssuanceMatch.STALE_WRITER
    assert operation._verify_durable_writer_issuance(
        replace(issuance, generation=issuance.generation + 1)
    ) is writer_module._WriterIssuanceMatch.STALE_WRITER
    assert operation._verify_durable_writer_issuance(
        replace(issuance, issued_ref="issuance-other")
    ) is writer_module._WriterIssuanceMatch.STALE_WRITER
    assert operation._verify_durable_writer_issuance(
        replace(issuance, issuance_nonce_digest="b" * 64)
    ) is writer_module._WriterIssuanceMatch.STALE_WRITER

    class _DurableWriterIssuanceSubclass(_DurableWriterIssuance):
        pass

    class _DurableWriterIssuanceProxy:
        writer_ref = issuance.writer_ref
        generation = issuance.generation
        issued_ref = issuance.issued_ref
        issuance_nonce_digest = issuance.issuance_nonce_digest
        acquired_at = issuance.acquired_at

    def fail_if_parser_is_called(*args, **kwargs):
        raise AssertionError("subclass/proxy reached writer-row parser")

    with monkeypatch.context() as parser_guard:
        parser_guard.setattr(writer_module, "_parse_writer_ownership_rows_or_raise", fail_if_parser_is_called)
        with pytest.raises(ValueError) as subclass_error:
            operation._verify_durable_writer_issuance(
                _DurableWriterIssuanceSubclass(
                    writer_ref=issuance.writer_ref,
                    generation=issuance.generation,
                    issued_ref=issuance.issued_ref,
                    issuance_nonce_digest=issuance.issuance_nonce_digest,
                    acquired_at=issuance.acquired_at,
                )
            )
        with pytest.raises(ValueError) as proxy_error:
            operation._verify_durable_writer_issuance(_DurableWriterIssuanceProxy())  # type: ignore[arg-type]
    for exc_info in (subclass_error, proxy_error):
        assert exc_info.value.args == ("invalid writer input",)
        assert exc_info.value.__cause__ is None

    malformed = object.__new__(_DurableWriterIssuance)
    object.__setattr__(malformed, "writer_ref", issuance.writer_ref)
    object.__setattr__(malformed, "generation", issuance.generation)
    object.__setattr__(malformed, "issued_ref", issuance.issued_ref)
    object.__setattr__(malformed, "issuance_nonce_digest", "B" * 64)
    object.__setattr__(malformed, "acquired_at", issuance.acquired_at)
    with pytest.raises(ValueError) as malformed_error:
        operation._verify_durable_writer_issuance(malformed)
    assert malformed_error.value.args == ("invalid writer input",)
    assert malformed_error.value.__cause__ is None

    rendered_errors = "\n".join(
        "".join(traceback.format_exception_only(type(exc_info.value), exc_info.value))
        + repr(exc_info.value)
        for exc_info in (subclass_error, proxy_error, malformed_error, no_slot_verify_error)
    )
    _assert_no_private_error_detail(rendered_errors, issuance.issuance_nonce_digest)
    assert repr(issuance) == "<_DurableWriterIssuance>"
    assert repr(mutation) == "<_WriterSessionMutationLease>"
    assert repr(resource._mutation_slot) == "<_WriterSessionMutationSlot>"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    mutation._close()
    with pytest.raises(WriterSessionError) as released_verify_error:
        operation._verify_durable_writer_issuance(issuance)
    _assert_writer_error(released_verify_error, WriterSessionFailureReason.WRITER_SESSION_CLOSED)
    operation._close()
    session.close()


def test_public_boundary_exports_and_mutation_methods_remain_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _location_value, session = _managed_session(tmp_path)
    sqlite_open_calls = 0

    def fail_if_sqlite_opens(*args, **kwargs):
        nonlocal sqlite_open_calls
        sqlite_open_calls += 1
        raise AssertionError("public mutation method opened SQLite")

    monkeypatch.setattr(writer_module, "open_existing_sqlite_connection", fail_if_sqlite_opens)
    with pytest.raises(WriterSessionError) as transition_error:
        session.apply_transition(None)  # type: ignore[arg-type]
    _assert_writer_error(
        transition_error,
        WriterSessionFailureReason.WRITER_SESSION_MUTATION_UNAVAILABLE,
    )
    with pytest.raises(WriterSessionError) as global_stop_error:
        session.apply_global_stop_update(None, None)  # type: ignore[arg-type]
    _assert_writer_error(
        global_stop_error,
        WriterSessionFailureReason.WRITER_SESSION_MUTATION_UNAVAILABLE,
    )
    assert sqlite_open_calls == 0
    session.close()

    package_exports = set(ge_nwp_coordinator.__all__)
    for private_name in (
        "_WriterIssuanceMatch",
        "_WriterSessionMutationLease",
        "_WriterSessionMutationSlot",
        "_WriterSessionMutationToken",
    ):
        assert private_name not in writer_module.__all__
        assert private_name not in package_exports
        assert not hasattr(ge_nwp_coordinator, private_name)

    assert not (PACKAGE_DIR / "sqlite_transition_transaction.py").exists()
    writer_source = inspect.getsource(writer_module)
    for forbidden in (
        "class _SQLiteTransitionTransactionController",
        "class _SQLiteTransitionReadCapability",
        "_borrow_connection_for_select",
        "_read_current_work_item",
        "_read_global_stop_current",
        "INSERT INTO transition_events",
        "INSERT INTO global_stop_events",
        "UPDATE work_items",
        "UPDATE global_stop_current",
    ):
        assert forbidden not in writer_source

    transition_source = inspect.getsource(writer_module._SQLiteWriterSession.apply_transition)
    global_stop_source = inspect.getsource(writer_module._SQLiteWriterSession.apply_global_stop_update)
    for source in (transition_source, global_stop_source):
        assert "operation_guard" in source
        assert "_acquire_mutation_lease" not in source
        assert "WRITER_SESSION_MUTATION_UNAVAILABLE" in source
        assert "open_existing_sqlite_connection" not in source
