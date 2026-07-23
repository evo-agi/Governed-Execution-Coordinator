from __future__ import annotations

from itertools import count
import json
import os
from pathlib import Path
import signal
import sqlite3
import threading
import time
import traceback
from typing import Any, Callable

import pytest

import ge_nwp_coordinator
from b3_coherent_transition_fixture import (
    make_coherent_transition_fixture_for_test,
    _transition_event_row_for_test,
)
from ge_nwp_coordinator.canonicalization import canonical_json_bytes, canonical_sha256
from ge_nwp_coordinator.persistence_contracts import (
    SQLITE_SIGNED_INT_MAX,
    TRANSITION_EVENT_ROW_COLUMNS,
    TransitionEventRecordEnvelope,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_transition_event_contracts import (
    _TRANSITION_EVENT_IDEMPOTENCY_LOOKUP_SELECT,
    _TRANSITION_EVENT_MAX_SEQUENCE_SELECT,
)
import ge_nwp_coordinator.sqlite_transition_event_readers as event_readers
from ge_nwp_coordinator.sqlite_transition_event_readers import (
    _read_transition_event_for_idempotency,
    _read_transition_event_max_sequence,
)
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _MutationReadCapabilityError,
    _MutationReadCapabilityFailureReason,
)
import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module
from ge_nwp_coordinator.sqlite_writer_session import _WriterIssuanceMatch
from ge_nwp_coordinator.state_machine import TransitionEvent


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
MIGRATION_PATH = PACKAGE_DIR / "sqlite_migrations/0001_initial.sql"
EVENT_READERS_PATH = PACKAGE_DIR / "sqlite_transition_event_readers.py"
SELECT_SUPPORT_PATH = PACKAGE_DIR / "sqlite_transition_select_support.py"
PRIVATE_SQLITE_SENTINEL = "PRIVATE-B3C2-SQLITE-SENTINEL-DO-NOT-LEAK"
PRIVATE_CAPABILITY_SENTINEL = "PRIVATE-B3C2-CAPABILITY-SENTINEL-DO-NOT-LEAK"
PRIVATE_ROW_SENTINEL = "PRIVATE-B3C2-ROW-SENTINEL-DO-NOT-LEAK"
PRIVATE_REF_SENTINEL = "PRIVATE-B3C2-REF-SENTINEL-DO-NOT-LEAK"
_ROW_FIXTURE_COUNTER = count()


class _SyntheticSQLiteError(sqlite3.DatabaseError):
    def __init__(self, sqlite_errorcode: int | None) -> None:
        super().__init__(PRIVATE_SQLITE_SENTINEL)
        if sqlite_errorcode is not None:
            self.sqlite_errorcode = sqlite_errorcode


class _ScriptedCursor:
    def __init__(
        self,
        rows: tuple[object, ...] = (),
        *,
        fetch_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self._rows = rows
        self._fetch_error = fetch_error
        self._close_error = close_error
        self.fetchmany_sizes: list[int] = []
        self.close_count = 0

    def fetchmany(self, size: int) -> list[object]:
        self.fetchmany_sizes.append(size)
        if self._fetch_error is not None:
            raise self._fetch_error
        return list(self._rows[:size])

    def close(self) -> None:
        self.close_count += 1
        if self._close_error is not None:
            raise self._close_error


class _RecordingConnection(sqlite3.Connection):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.execute_calls: list[tuple[str, tuple[object, ...]]] = []
        self.scripted_cursor: _ScriptedCursor | None = None
        self.scripted_execute_error: BaseException | None = None
        self.close_count = 0

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


class _TestsOnlyTransitionReadCapabilityEpoch:
    """Tests-only structural epoch; not production transaction authority."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._active = False
        self._generation = 0

    def start_for_test(self) -> "_TestsOnlyTransitionReadCapability":
        self._generation += 1
        self._active = True
        return _TestsOnlyTransitionReadCapability(self, self._generation)

    def end_for_test(self) -> None:
        self._active = False

    def _connection_for_generation(self, generation: int) -> sqlite3.Connection:
        if not self._active or generation != self._generation:
            raise _MutationReadCapabilityError(_MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED)
        return self._connection


class _TestsOnlyTransitionReadCapability:
    def __init__(self, epoch: _TestsOnlyTransitionReadCapabilityEpoch, generation: int) -> None:
        self._epoch = epoch
        self._generation = generation
        self.borrow_count = 0

    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        self.borrow_count += 1
        return self._epoch._connection_for_generation(self._generation)


class _UnknownExceptionCapability:
    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        try:
            raise ValueError(PRIVATE_CAPABILITY_SENTINEL)
        except ValueError as cause:
            error = RuntimeError(PRIVATE_CAPABILITY_SENTINEL)
            error.add_note(PRIVATE_CAPABILITY_SENTINEL)
            raise error from cause


class _HostileEvent:
    def __getattribute__(self, name: str) -> object:
        if name in {"work_item_id", "idempotency_key"}:
            raise AssertionError(PRIVATE_ROW_SENTINEL)
        return object.__getattribute__(self, name)


class _BenignStrSubclass(str):
    pass


class _HostileStrSubclass(str):
    def __new__(cls, value: str, invocations: list[str]) -> "_HostileStrSubclass":
        instance = super().__new__(cls, value)
        instance._invocations = invocations
        return instance

    def _fail(self, operation: str) -> object:
        self._invocations.append(operation)
        raise AssertionError(PRIVATE_REF_SENTINEL)

    def __len__(self) -> int:
        return self._fail("__len__")  # type: ignore[return-value]

    def __bool__(self) -> bool:
        return self._fail("__bool__")  # type: ignore[return-value]

    def lower(self) -> str:
        return self._fail("lower")  # type: ignore[return-value]

    def __str__(self) -> str:
        return self._fail("__str__")  # type: ignore[return-value]

    def __repr__(self) -> str:
        return self._fail("__repr__")  # type: ignore[return-value]

    def __eq__(self, other: object) -> bool:
        return self._fail("__eq__")  # type: ignore[return-value]

    def __hash__(self) -> int:
        return self._fail("__hash__")  # type: ignore[return-value]

    def __iter__(self) -> object:
        return self._fail("__iter__")

    def __getitem__(self, index: object) -> object:
        return self._fail("__getitem__")


class _HostileAdapterResult:
    @property
    def event(self) -> object:
        raise AssertionError(PRIVATE_ROW_SENTINEL)


def _connect() -> _RecordingConnection:
    connection = sqlite3.connect(":memory:", factory=_RecordingConnection)
    connection.executescript(MIGRATION_PATH.read_text(encoding="utf-8"))
    return connection


def _capability_for(connection: sqlite3.Connection) -> tuple[_TestsOnlyTransitionReadCapabilityEpoch, _TestsOnlyTransitionReadCapability]:
    epoch = _TestsOnlyTransitionReadCapabilityEpoch(connection)
    return epoch, epoch.start_for_test()


def _valid_event_row(tmp_path: Path, *, event_sequence: int = 0) -> dict[str, object]:
    fixture_root = tmp_path / f"event-row-{next(_ROW_FIXTURE_COUNTER)}"
    fixture_root.mkdir()
    with make_coherent_transition_fixture_for_test(fixture_root, existing_event=True) as fixture:
        envelope = fixture.transition_event_envelope
        assert envelope is not None
        row = _transition_event_row_for_test(
            envelope.event,
            envelope.replay_record,
            event_sequence=event_sequence,
        )
        return dict(row)


def _row_tuple(row: dict[str, object]) -> tuple[object, ...]:
    return tuple(row[column] for column in TRANSITION_EVENT_ROW_COLUMNS)


def _scripted_capability(
    *,
    rows: tuple[object, ...] = (),
    execute_error: BaseException | None = None,
    fetch_error: BaseException | None = None,
    close_error: BaseException | None = None,
) -> tuple[_RecordingConnection, _ScriptedCursor, _TestsOnlyTransitionReadCapability]:
    connection = _connect()
    cursor = _ScriptedCursor(rows, fetch_error=fetch_error, close_error=close_error)
    connection.scripted_cursor = cursor
    connection.scripted_execute_error = execute_error
    _epoch, capability = _capability_for(connection)
    return connection, cursor, capability


def _insert_transition_event(connection: sqlite3.Connection, row: dict[str, object]) -> None:
    columns = ", ".join(TRANSITION_EVENT_ROW_COLUMNS)
    placeholders = ", ".join("?" for _ in TRANSITION_EVENT_ROW_COLUMNS)
    connection.execute(
        f"INSERT INTO transition_events ({columns}) VALUES ({placeholders})",
        tuple(row[column] for column in TRANSITION_EVENT_ROW_COLUMNS),
    )


def _lookup_event(row: dict[str, object], capability: object) -> TransitionEventRecordEnvelope | None:
    return _read_transition_event_for_idempotency(
        capability,  # type: ignore[arg-type]
        str(row["work_item_id"]),
        str(row["idempotency_key"]),
    )


def _assert_sqlite_mutation_error(
    call: Callable[[], object],
    error_class: str,
    *,
    capsys: pytest.CaptureFixture[str] | None = None,
    private_values: tuple[object, ...] = (),
) -> SQLiteMutationStoreError:
    if capsys is not None:
        capsys.readouterr()
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        call()
    if capsys is not None:
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""
    exc = exc_info.value
    assert exc.error_class == error_class
    assert str(exc) == error_class
    assert exc.args == (error_class,)
    assert exc.internal_detail is None
    assert exc.__cause__ is None
    assert exc.__context__ is None
    rendered = _render_exception_graph(exc)
    for forbidden in (
        PRIVATE_SQLITE_SENTINEL,
        PRIVATE_CAPABILITY_SENTINEL,
        PRIVATE_ROW_SENTINEL,
        "canonical_json",
        "event_json",
        "replay_work_item_json",
        "event_digest",
        "replay_work_item_digest",
        "SELECT ",
        "coordinator-state.sqlite",
        "_SQLiteMutationReadCapability",
        "credential",
        "proof",
        "epoch",
        "binding",
    ):
        assert forbidden not in rendered
    for private_value in private_values:
        assert str(private_value) not in rendered
    return exc


def _assert_safe_validation_error(
    call: Callable[[], object],
    *,
    capsys: pytest.CaptureFixture[str] | None = None,
    private_values: tuple[object, ...] = (),
) -> ValueError:
    if capsys is not None:
        capsys.readouterr()
    with pytest.raises(ValueError) as exc_info:
        call()
    if capsys is not None:
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""
    exc = exc_info.value
    rendered = _render_exception_graph(exc)
    for forbidden in (
        PRIVATE_SQLITE_SENTINEL,
        PRIVATE_CAPABILITY_SENTINEL,
        PRIVATE_ROW_SENTINEL,
        PRIVATE_REF_SENTINEL,
        "SELECT ",
        "coordinator-state.sqlite",
        "_SQLiteMutationReadCapability",
        "credential",
        "proof",
        "epoch",
        "binding",
    ):
        assert forbidden not in rendered
    for private_value in private_values:
        assert str(private_value) not in rendered
    return exc


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
                repr(getattr(current, "internal_detail", None)),
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


def _mutated_replay_json(row: dict[str, object], **overrides: object) -> tuple[str, str]:
    payload = json.loads(str(row["replay_work_item_json"]))
    payload.update(overrides)
    canonical = canonical_json_bytes(payload).decode("utf-8")
    return canonical, canonical_sha256(payload)


def _forged_envelope(event: object) -> TransitionEventRecordEnvelope:
    envelope = object.__new__(TransitionEventRecordEnvelope)
    object.__setattr__(envelope, "event_sequence", 0)
    object.__setattr__(envelope, "event", event)
    object.__setattr__(envelope, "replay_record", object())
    object.__setattr__(envelope, "created_at", "2026-07-14T00:00:03Z")
    return envelope


def _run_real_controller_with_probe(session: object, monkeypatch: pytest.MonkeyPatch, probe: Callable[[object], None]) -> object:
    original_create = transaction_module._create_sqlite_mutation_read_capability
    captured: list[object] = []

    def capture_create(**kwargs: object) -> object:
        capability = original_create(**kwargs)
        captured.append(capability)
        probe(capability)
        return capability

    monkeypatch.setattr(transaction_module, "_create_sqlite_mutation_read_capability", capture_create)
    with session._resource.operation_guard(session) as operation:
        result = transaction_module._run_rollback_only_writer_fencing(operation_lease=operation)
    assert result is _WriterIssuanceMatch.MATCH
    assert len(captured) == 1
    return captured[0]


def _assert_capability_error(exc: _MutationReadCapabilityError, reason: _MutationReadCapabilityFailureReason) -> None:
    assert exc.reason is reason
    assert str(exc) == reason.value
    assert exc.args == (reason.value,)
    assert exc.__cause__ is None
    assert exc.__context__ is None


def _wait_for_child_result(child_pid: int, read_fd: int) -> str:
    return _wait_for_child_result_bounded(child_pid, read_fd, timeout_seconds=5.0)


_CHILD_ALREADY_REAPED = object()


def _wait_for_child_result_bounded(child_pid: int, read_fd: int, *, timeout_seconds: float) -> str:
    chunks: list[bytes] = []
    reaped = False
    status: int | None = None
    try:
        os.set_blocking(read_fd, False)
        deadline = time.monotonic() + timeout_seconds
        while True:
            _drain_child_result_pipe(read_fd, chunks)
            poll_result = _poll_child_once(child_pid)
            if poll_result is _CHILD_ALREADY_REAPED:
                reaped = True
                raise AssertionError("child_result_abnormal") from None
            if type(poll_result) is int:
                reaped = True
                status = poll_result
                _drain_child_result_pipe(read_fd, chunks)
                break
            if time.monotonic() >= deadline:
                reaped = _terminate_and_reap_child(child_pid)
                raise AssertionError("child_result_timeout") from None
            time.sleep(0.005)
        if status is None or not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
            raise AssertionError("child_result_abnormal") from None
        return b"".join(chunks).decode("ascii")
    finally:
        try:
            os.close(read_fd)
        except OSError:
            pass
        if not reaped:
            _terminate_and_reap_child(child_pid)


def _poll_child_once(child_pid: int) -> int | object | None:
    try:
        waited_pid, status = os.waitpid(child_pid, os.WNOHANG)
    except ChildProcessError:
        return _CHILD_ALREADY_REAPED
    if waited_pid == child_pid:
        return status
    return None


def _poll_child_until(child_pid: int, deadline: float) -> int | object | None:
    while True:
        poll_result = _poll_child_once(child_pid)
        if poll_result is not None:
            return poll_result
        now = time.monotonic()
        if now >= deadline:
            return None
        time.sleep(min(0.005, max(0.0, deadline - now)))


def _drain_child_result_pipe(read_fd: int, chunks: list[bytes]) -> None:
    while True:
        try:
            chunk = os.read(read_fd, 1024)
        except BlockingIOError:
            return
        if not chunk:
            return
        chunks.append(chunk)


def _terminate_and_reap_child(child_pid: int, *, timeout_seconds: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    if _poll_child_until(child_pid, time.monotonic()) is not None:
        return True
    _signal_child(child_pid, signal.SIGTERM)
    term_grace = min(0.2, max(0.0, timeout_seconds / 2))
    if _poll_child_until(child_pid, min(deadline, time.monotonic() + term_grace)) is not None:
        return True
    _signal_child(child_pid, signal.SIGKILL)
    return _poll_child_until(child_pid, deadline) is not None


def _signal_child(child_pid: int, signal_number: int) -> None:
    try:
        os.kill(child_pid, signal_number)
    except ProcessLookupError:
        pass
    except OSError:
        pass


def _assert_child_reaped(child_pid: int) -> None:
    with pytest.raises(ChildProcessError):
        os.waitpid(child_pid, os.WNOHANG)


def _assert_fd_closed(fd: int) -> None:
    with pytest.raises(OSError):
        os.fstat(fd)


def test_bounded_child_result_helper_returns_reaps_and_closes_pipe() -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        try:
            os.write(write_fd, b"ok")
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)

    assert _wait_for_child_result_bounded(child_pid, read_fd, timeout_seconds=1.0) == "ok"
    _assert_child_reaped(child_pid)
    _assert_fd_closed(read_fd)


def test_bounded_child_helpers_have_no_unbounded_wait_or_read() -> None:
    import ast
    import inspect
    import textwrap

    helper_functions = (
        _wait_for_child_result,
        _wait_for_child_result_bounded,
        _poll_child_once,
        _poll_child_until,
        _drain_child_result_pipe,
        _terminate_and_reap_child,
        _signal_child,
    )

    for helper in helper_functions:
        helper_name = helper.__name__
        tree = ast.parse(textwrap.dedent(inspect.getsource(helper)))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr == "waitpid":
                assert len(node.args) == 2
                assert not (isinstance(node.args[1], ast.Constant) and node.args[1].value == 0)
            assert node.func.attr not in {"wait", "recv"}
            if node.func.attr == "join":
                assert isinstance(node.func.value, ast.Constant)
                assert isinstance(node.func.value.value, (bytes, str))
            if node.func.attr == "read":
                assert helper_name == "_drain_child_result_pipe"
                assert isinstance(node.func.value, ast.Name)
                assert node.func.value.id == "os"


def test_bounded_child_result_helper_concatenates_result_and_reaps() -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        try:
            os.write(write_fd, b"pro")
            os.write(write_fd, b"cess_mismatch")
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)

    assert _wait_for_child_result_bounded(child_pid, read_fd, timeout_seconds=1.0) == "process_mismatch"
    _assert_child_reaped(child_pid)
    _assert_fd_closed(read_fd)


def test_bounded_child_result_helper_times_out_kills_reaps_and_redacts() -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    read_fd, write_fd = os.pipe()
    block_read_fd, block_write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        os.close(block_write_fd)
        try:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            os.read(block_read_fd, 1)
        finally:
            os.close(block_read_fd)
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    os.close(block_read_fd)

    try:
        with pytest.raises(AssertionError) as exc_info:
            _wait_for_child_result_bounded(child_pid, read_fd, timeout_seconds=0.05)
        assert str(exc_info.value) == "child_result_timeout"
        rendered = _render_exception_graph(exc_info.value)
        for forbidden in (
            PRIVATE_CAPABILITY_SENTINEL,
            PRIVATE_SQLITE_SENTINEL,
            "coordinator-state.sqlite",
            "_SQLiteMutationReadCapability",
            "epoch",
            "binding",
        ):
            assert forbidden not in rendered
        _assert_child_reaped(child_pid)
        _assert_fd_closed(read_fd)
    finally:
        os.close(block_write_fd)


def test_bounded_child_result_helper_detects_abnormal_exit_and_reaps() -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        try:
            os.write(write_fd, b"bad")
        finally:
            os.close(write_fd)
            os._exit(7)
    os.close(write_fd)

    with pytest.raises(AssertionError) as exc_info:
        _wait_for_child_result_bounded(child_pid, read_fd, timeout_seconds=1.0)
    assert str(exc_info.value) == "child_result_abnormal"
    _assert_child_reaped(child_pid)
    _assert_fd_closed(read_fd)


def test_bounded_child_result_helper_handles_already_reaped_child() -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    child_pid = os.fork()
    if child_pid == 0:
        os._exit(0)

    status = _poll_child_until(child_pid, time.monotonic() + 1.0)
    assert type(status) is int
    assert os.WIFEXITED(status)
    _assert_child_reaped(child_pid)
    assert _terminate_and_reap_child(child_pid, timeout_seconds=0.01) is True


def test_bounded_child_result_helper_cleanup_reaps_after_parent_read_failure() -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    read_fd, write_fd = os.pipe()
    block_read_fd, block_write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        os.close(block_write_fd)
        try:
            os.read(block_read_fd, 1)
        finally:
            os.close(block_read_fd)
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    os.close(block_read_fd)
    os.close(read_fd)

    try:
        with pytest.raises(OSError):
            _wait_for_child_result_bounded(child_pid, read_fd, timeout_seconds=0.05)
        _assert_child_reaped(child_pid)
        _assert_fd_closed(read_fd)
    finally:
        os.close(block_write_fd)


def test_invalid_lookup_refs_are_rejected_before_capability_borrow(tmp_path: Path) -> None:
    row = _valid_event_row(tmp_path)
    connection, _cursor, capability = _scripted_capability(rows=(_row_tuple(row),))
    try:
        with pytest.raises(ValueError):
            _read_transition_event_for_idempotency(capability, "bad ref", str(row["idempotency_key"]))
        assert capability.borrow_count == 0
        with pytest.raises(ValueError):
            _read_transition_event_for_idempotency(capability, str(row["work_item_id"]), "bad ref")
        assert capability.borrow_count == 0
    finally:
        connection.close()


def test_lookup_ref_exact_type_preflight_completes_before_shared_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    row = _valid_event_row(tmp_path)
    original_require_contract_ref = event_readers.require_contract_ref
    validation_calls: list[str] = []

    def tracking_require_contract_ref(value: object, field_name: str, **kwargs: object) -> str:
        validation_calls.append(field_name)
        return original_require_contract_ref(value, field_name, **kwargs)

    monkeypatch.setattr(event_readers, "require_contract_ref", tracking_require_contract_ref)

    def assert_rejected_before_shared_validation(work_item_id: object, idempotency_key: object) -> None:
        validation_calls.clear()
        connection, _cursor, capability = _scripted_capability(rows=(_row_tuple(row),))
        try:
            _assert_safe_validation_error(
                lambda: _read_transition_event_for_idempotency(
                    capability,  # type: ignore[arg-type]
                    work_item_id,  # type: ignore[arg-type]
                    idempotency_key,  # type: ignore[arg-type]
                ),
                capsys=capsys,
            )
            assert validation_calls == []
            assert capability.borrow_count == 0
            assert connection.execute_calls == []
        finally:
            connection.close()

    idempotency_invocations: list[str] = []
    assert_rejected_before_shared_validation(
        str(row["work_item_id"]),
        _HostileStrSubclass(str(row["idempotency_key"]), idempotency_invocations),
    )
    assert idempotency_invocations == []

    work_item_invocations: list[str] = []
    assert_rejected_before_shared_validation(
        _HostileStrSubclass(str(row["work_item_id"]), work_item_invocations),
        str(row["idempotency_key"]),
    )
    assert work_item_invocations == []

    assert_rejected_before_shared_validation(
        _BenignStrSubclass(str(row["work_item_id"])),
        str(row["idempotency_key"]),
    )
    assert_rejected_before_shared_validation(
        str(row["work_item_id"]),
        _BenignStrSubclass(str(row["idempotency_key"])),
    )

    validation_calls.clear()
    connection, _cursor, capability = _scripted_capability(rows=())
    try:
        assert (
            _read_transition_event_for_idempotency(
                capability,
                str(row["work_item_id"]),
                str(row["idempotency_key"]),
            )
            is None
        )
        assert validation_calls == [
            "transition_event_idempotency.work_item_id",
            "transition_event_idempotency.idempotency_key",
        ]
        assert capability.borrow_count == 1
        assert len(connection.execute_calls) == 1
    finally:
        connection.close()


def test_exact_builtin_lookup_string_validation_still_runs_after_two_field_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    row = _valid_event_row(tmp_path)
    original_require_contract_ref = event_readers.require_contract_ref
    validation_calls: list[str] = []

    def tracking_require_contract_ref(value: object, field_name: str, **kwargs: object) -> str:
        validation_calls.append(field_name)
        return original_require_contract_ref(value, field_name, **kwargs)

    monkeypatch.setattr(event_readers, "require_contract_ref", tracking_require_contract_ref)

    for work_item_id, idempotency_key, expected_error, expected_calls in (
        (
            "bad ref",
            str(row["idempotency_key"]),
            "invalid_field_type:transition_event_idempotency.work_item_id",
            ["transition_event_idempotency.work_item_id"],
        ),
        (
            str(row["work_item_id"]),
            "bad ref",
            "invalid_field_type:transition_event_idempotency.idempotency_key",
            [
                "transition_event_idempotency.work_item_id",
                "transition_event_idempotency.idempotency_key",
            ],
        ),
    ):
        validation_calls.clear()
        connection, _cursor, capability = _scripted_capability(rows=(_row_tuple(row),))
        try:
            exc = _assert_safe_validation_error(
                lambda work_item_id=work_item_id, idempotency_key=idempotency_key: _read_transition_event_for_idempotency(
                    capability,
                    work_item_id,
                    idempotency_key,
                ),
                capsys=capsys,
            )
            assert str(exc) == expected_error
            assert validation_calls == expected_calls
            assert capability.borrow_count == 0
            assert connection.execute_calls == []
        finally:
            connection.close()


def test_lookup_refs_must_be_exact_builtin_strings_before_borrow_or_sql(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    row = _valid_event_row(tmp_path)

    def assert_rejected(work_item_id: object, idempotency_key: object) -> None:
        connection, _cursor, capability = _scripted_capability(rows=(_row_tuple(row),))
        try:
            _assert_safe_validation_error(
                lambda: _read_transition_event_for_idempotency(
                    capability,  # type: ignore[arg-type]
                    work_item_id,  # type: ignore[arg-type]
                    idempotency_key,  # type: ignore[arg-type]
                ),
                capsys=capsys,
            )
            assert capability.borrow_count == 0
            assert connection.execute_calls == []
        finally:
            connection.close()

    assert_rejected(_BenignStrSubclass(str(row["work_item_id"])), str(row["idempotency_key"]))
    assert_rejected(str(row["work_item_id"]), _BenignStrSubclass(str(row["idempotency_key"])))

    work_item_invocations: list[str] = []
    assert_rejected(_HostileStrSubclass(str(row["work_item_id"]), work_item_invocations), str(row["idempotency_key"]))
    assert work_item_invocations == []

    idempotency_invocations: list[str] = []
    assert_rejected(str(row["work_item_id"]), _HostileStrSubclass(str(row["idempotency_key"]), idempotency_invocations))
    assert idempotency_invocations == []


def test_exact_builtin_lookup_string_validation_remains_safe_and_precedes_borrow(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    row = _valid_event_row(tmp_path)
    connection, _cursor, capability = _scripted_capability(rows=(_row_tuple(row),))
    try:
        for work_item_id, idempotency_key in (
            ("bad ref", str(row["idempotency_key"])),
            ("w" * 200, str(row["idempotency_key"])),
            (str(row["work_item_id"]), "bad ref"),
            (str(row["work_item_id"]), "k" * 200),
        ):
            _assert_safe_validation_error(
                lambda work_item_id=work_item_id, idempotency_key=idempotency_key: _read_transition_event_for_idempotency(
                    capability,
                    work_item_id,
                    idempotency_key,
                ),
                capsys=capsys,
            )
            assert capability.borrow_count == 0
            assert connection.execute_calls == []
    finally:
        connection.close()


def test_idempotency_reader_empty_table_returns_none_and_uses_exact_query(tmp_path: Path) -> None:
    row = _valid_event_row(tmp_path)
    connection = _connect()
    _epoch, capability = _capability_for(connection)
    try:
        assert _lookup_event(row, capability) is None
        assert connection.execute_calls[-1] == (
            _TRANSITION_EVENT_IDEMPOTENCY_LOOKUP_SELECT.sql,
            (row["work_item_id"], row["idempotency_key"]),
        )
    finally:
        connection.close()


def test_idempotency_reader_returns_exact_domain_rejected_envelope(tmp_path: Path) -> None:
    row = _valid_event_row(tmp_path)
    connection = _connect()
    _insert_transition_event(connection, row)
    _epoch, capability = _capability_for(connection)
    try:
        envelope = _lookup_event(row, capability)
        assert type(envelope) is TransitionEventRecordEnvelope
        assert type(envelope.event) is TransitionEvent
        assert envelope.event.work_item_id == row["work_item_id"]
        assert envelope.event.idempotency_key == row["idempotency_key"]
        assert envelope.event.outcome.value == "domain_rejected"
        assert connection.execute_calls[-1] == (
            _TRANSITION_EVENT_IDEMPOTENCY_LOOKUP_SELECT.sql,
            (row["work_item_id"], row["idempotency_key"]),
        )
    finally:
        connection.close()


def test_idempotency_reader_cardinality_and_tuple_shape_faults_are_integrity_failures(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    row = _valid_event_row(tmp_path)
    cases = (
        (_row_tuple(row), _row_tuple(row)),
        (object(),),
        (_row_tuple(row)[:-1],),
    )
    for rows in cases:
        connection, _cursor, capability = _scripted_capability(rows=rows)
        try:
            _assert_sqlite_mutation_error(
                lambda: _lookup_event(row, capability),
                "database_integrity_failure",
                capsys=capsys,
            )
        finally:
            connection.close()


def test_idempotency_reader_rechecks_lookup_address(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    row = _valid_event_row(tmp_path)
    connection, _cursor, capability = _scripted_capability(rows=(_row_tuple(row),))
    try:
        _assert_sqlite_mutation_error(
            lambda: _read_transition_event_for_idempotency(
                capability,
                "wi-b3-fixture-other",
                str(row["idempotency_key"]),
            ),
            "database_integrity_failure",
            capsys=capsys,
        )
    finally:
        connection.close()


@pytest.mark.parametrize(
    "case_name,mutate",
    (
        ("corrupted-event-json", lambda row: row.update(event_json="{")),
        ("event-digest-mismatch", lambda row: row.update(event_digest="0" * 64)),
        ("indexed-event-mismatch", lambda row: row.update(lease_id="lease-b3-fixture-other")),
        ("evidence-refs-json-mismatch", lambda row: row.update(evidence_refs_json='["different"]')),
        ("replay-json-mismatch", lambda row: row.update(replay_work_item_json="{}")),
        ("replay-digest-mismatch", lambda row: row.update(replay_work_item_digest="0" * 64)),
        (
            "replay-event-state-mismatch",
            lambda row: row.update(
                zip(
                    ("replay_work_item_json", "replay_work_item_digest"),
                    _mutated_replay_json(row, state="ready"),
                    strict=True,
                )
            ),
        ),
        (
            "replay-event-version-mismatch",
            lambda row: row.update(
                zip(
                    ("replay_work_item_json", "replay_work_item_digest"),
                    _mutated_replay_json(row, version=int(row["resulting_version"]) + 1),
                    strict=True,
                )
            ),
        ),
        ("created-at-runtime-mismatch", lambda row: row.update(created_at="2026-07-14T00:00:04Z")),
        ("oversized-event-json", lambda row: row.update(event_json="x" * 1048577)),
        ("oversized-replay-json", lambda row: row.update(replay_work_item_json="x" * 1048577)),
    ),
)
def test_idempotency_reader_delegates_corrupt_event_replay_rows_to_adapter(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    case_name: str,
    mutate: Callable[[dict[str, object]], None],
) -> None:
    row = _valid_event_row(tmp_path)
    mutate(row)
    connection, _cursor, capability = _scripted_capability(rows=(_row_tuple(row),))
    try:
        _assert_sqlite_mutation_error(
            lambda: _lookup_event(row, capability),
            "database_integrity_failure",
            capsys=capsys,
            private_values=(case_name,),
        )
    finally:
        connection.close()


def test_idempotency_reader_rejects_hostile_adapter_result_before_semantic_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    row = _valid_event_row(tmp_path)
    connection, _cursor, capability = _scripted_capability(rows=(_row_tuple(row),))
    monkeypatch.setattr(event_readers, "transition_event_record_envelope_from_row", lambda _mapping: _HostileAdapterResult())
    try:
        _assert_sqlite_mutation_error(
            lambda: _lookup_event(row, capability),
            "database_integrity_failure",
            capsys=capsys,
        )
    finally:
        connection.close()

    connection, _cursor, capability = _scripted_capability(rows=(_row_tuple(row),))
    monkeypatch.setattr(
        event_readers,
        "transition_event_record_envelope_from_row",
        lambda _mapping: _forged_envelope(_HostileEvent()),
    )
    try:
        _assert_sqlite_mutation_error(
            lambda: _lookup_event(row, capability),
            "database_integrity_failure",
            capsys=capsys,
        )
    finally:
        connection.close()


@pytest.mark.parametrize(
    "sqlite_errorcode,error_class",
    (
        (_sqlite_error_code("SQLITE_ERROR", 1), "database_integrity_failure"),
        (_sqlite_error_code("SQLITE_SCHEMA", 17), "database_integrity_failure"),
        (_sqlite_error_code("SQLITE_CONSTRAINT", 19), "database_integrity_failure"),
        (_sqlite_error_code("SQLITE_BUSY", 5), "mutation_failed"),
        (_sqlite_error_code("SQLITE_LOCKED", 6), "mutation_failed"),
        (_sqlite_error_code("SQLITE_IOERR", 10), "mutation_failed"),
        (_sqlite_error_code("SQLITE_FULL", 13), "mutation_failed"),
        (_sqlite_error_code("SQLITE_INTERRUPT", 9), "mutation_failed"),
        (_sqlite_error_code("SQLITE_READONLY", 8), "mutation_failed"),
        (None, "mutation_failed"),
    ),
)
def test_idempotency_reader_execute_errors_are_safely_classified(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    sqlite_errorcode: int | None,
    error_class: str,
) -> None:
    row = _valid_event_row(tmp_path)
    connection, cursor, capability = _scripted_capability(
        rows=(_row_tuple(row),),
        execute_error=_SyntheticSQLiteError(sqlite_errorcode),
    )
    try:
        _assert_sqlite_mutation_error(lambda: _lookup_event(row, capability), error_class, capsys=capsys)
        assert cursor.close_count == 0
    finally:
        connection.close()


def test_idempotency_reader_fetch_and_close_precedence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    row = _valid_event_row(tmp_path)
    fetch_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_SCHEMA", 17))
    close_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5))
    connection, cursor, capability = _scripted_capability(
        rows=(_row_tuple(row),),
        fetch_error=fetch_error,
        close_error=close_error,
    )
    try:
        _assert_sqlite_mutation_error(
            lambda: _lookup_event(row, capability),
            "database_integrity_failure",
            capsys=capsys,
        )
        assert cursor.fetchmany_sizes == [2]
        assert cursor.close_count == 1
    finally:
        connection.close()

    fetch_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5))
    close_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_SCHEMA", 17))
    connection, cursor, capability = _scripted_capability(
        rows=(_row_tuple(row),),
        fetch_error=fetch_error,
        close_error=close_error,
    )
    try:
        _assert_sqlite_mutation_error(lambda: _lookup_event(row, capability), "mutation_failed", capsys=capsys)
        assert cursor.fetchmany_sizes == [2]
        assert cursor.close_count == 1
    finally:
        connection.close()

    monkeypatch.setattr(
        event_readers,
        "transition_event_record_envelope_from_row",
        lambda _mapping: (_ for _ in ()).throw(AssertionError(PRIVATE_ROW_SENTINEL)),
    )
    for close_error in (
        sqlite3.IntegrityError(PRIVATE_SQLITE_SENTINEL),
        _SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5)),
        RuntimeError(PRIVATE_SQLITE_SENTINEL),
    ):
        connection, cursor, capability = _scripted_capability(
            rows=(_row_tuple(row),),
            close_error=close_error,
        )
        try:
            _assert_sqlite_mutation_error(
                lambda: _lookup_event(row, capability),
                "mutation_failed",
                capsys=capsys,
            )
            assert cursor.fetchmany_sizes == [2]
            assert cursor.close_count == 1
        finally:
            connection.close()


def test_unknown_capability_exception_is_sanitized(tmp_path: Path) -> None:
    row = _valid_event_row(tmp_path)
    with pytest.raises(_MutationReadCapabilityError) as exc_info:
        _lookup_event(row, _UnknownExceptionCapability())
    _assert_capability_error(exc_info.value, _MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE)
    rendered = _render_exception_graph(exc_info.value)
    assert PRIVATE_CAPABILITY_SENTINEL not in rendered


def test_max_sequence_reader_empty_zero_positive_and_signed_max(tmp_path: Path) -> None:
    connection = _connect()
    _epoch, capability = _capability_for(connection)
    try:
        assert _read_transition_event_max_sequence(capability) is None
        assert connection.execute_calls[-1] == (_TRANSITION_EVENT_MAX_SEQUENCE_SELECT.sql, ())
    finally:
        connection.close()

    for value in (0, 41, SQLITE_SIGNED_INT_MAX):
        row = _valid_event_row(tmp_path, event_sequence=value)
        connection = _connect()
        _insert_transition_event(connection, row)
        _epoch, capability = _capability_for(connection)
        try:
            assert _read_transition_event_max_sequence(capability) == value
            assert connection.execute_calls[-1] == (_TRANSITION_EVENT_MAX_SEQUENCE_SELECT.sql, ())
        finally:
            connection.close()


@pytest.mark.parametrize(
    "rows",
    (
        (),
        ((1,), (2,)),
        (object(),),
        ((),),
        ((1, 2),),
    ),
)
def test_max_sequence_reader_aggregate_shape_faults_are_integrity_failures(
    rows: tuple[object, ...],
    capsys: pytest.CaptureFixture[str],
) -> None:
    connection, cursor, capability = _scripted_capability(rows=rows)
    try:
        _assert_sqlite_mutation_error(
            lambda: _read_transition_event_max_sequence(capability),
            "database_integrity_failure",
            capsys=capsys,
        )
        assert cursor.fetchmany_sizes == [2]
        assert cursor.close_count == 1
    finally:
        connection.close()


@pytest.mark.parametrize(
    "value",
    (False, True, -1, 1.25, "1", b"1", object(), SQLITE_SIGNED_INT_MAX + 1),
)
def test_max_sequence_reader_rejects_malformed_values(value: object, capsys: pytest.CaptureFixture[str]) -> None:
    connection, _cursor, capability = _scripted_capability(rows=((value,),))
    try:
        _assert_sqlite_mutation_error(
            lambda: _read_transition_event_max_sequence(capability),
            "database_integrity_failure",
            capsys=capsys,
        )
    finally:
        connection.close()


def test_max_sequence_reader_fetch_and_close_precedence(capsys: pytest.CaptureFixture[str]) -> None:
    fetch_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_SCHEMA", 17))
    close_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5))
    connection, cursor, capability = _scripted_capability(fetch_error=fetch_error, close_error=close_error)
    try:
        _assert_sqlite_mutation_error(
            lambda: _read_transition_event_max_sequence(capability),
            "database_integrity_failure",
            capsys=capsys,
        )
        assert cursor.fetchmany_sizes == [2]
        assert cursor.close_count == 1
    finally:
        connection.close()

    connection, cursor, capability = _scripted_capability(rows=((0,),), close_error=close_error)
    try:
        _assert_sqlite_mutation_error(
            lambda: _read_transition_event_max_sequence(capability),
            "mutation_failed",
            capsys=capsys,
        )
        assert cursor.fetchmany_sizes == [2]
        assert cursor.close_count == 1
    finally:
        connection.close()


def test_real_nominal_capability_reads_empty_transition_events_and_expires(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        summary: dict[str, object] = {}

        def probe(capability: object) -> None:
            summary["idempotency"] = _read_transition_event_for_idempotency(
                capability,  # type: ignore[arg-type]
                fixture.command.work_item_id,
                fixture.command.idempotency_key,
            )
            summary["max"] = _read_transition_event_max_sequence(capability)  # type: ignore[arg-type]

        capability = _run_real_controller_with_probe(fixture.writer_session, monkeypatch, probe)
        assert summary == {"idempotency": None, "max": None}
        with pytest.raises(_MutationReadCapabilityError) as expired:
            _read_transition_event_max_sequence(capability)  # type: ignore[arg-type]
        _assert_capability_error(expired.value, _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED)


def test_real_nominal_capability_reads_domain_rejected_event_and_max(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, existing_event=True) as fixture:
        expected = fixture.transition_event_envelope
        assert expected is not None
        summary: dict[str, object] = {}

        def probe(capability: object) -> None:
            summary["envelope"] = _read_transition_event_for_idempotency(
                capability,  # type: ignore[arg-type]
                fixture.command.work_item_id,
                fixture.command.idempotency_key,
            )
            summary["max"] = _read_transition_event_max_sequence(capability)  # type: ignore[arg-type]

        capability = _run_real_controller_with_probe(fixture.writer_session, monkeypatch, probe)
        assert summary["envelope"] == expected
        assert summary["max"] == expected.event_sequence
        with pytest.raises(_MutationReadCapabilityError) as expired:
            _read_transition_event_for_idempotency(
                capability,  # type: ignore[arg-type]
                fixture.command.work_item_id,
                fixture.command.idempotency_key,
            )
        _assert_capability_error(expired.value, _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED)


def test_real_nominal_capability_rejects_wrong_thread_and_child_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    with make_coherent_transition_fixture_for_test(tmp_path, existing_event=True) as fixture:
        wrong_thread_errors: list[_MutationReadCapabilityError] = []
        child_results: list[str] = []
        parent_results_after_child: list[int | None] = []

        def probe(capability: object) -> None:
            def borrow_in_thread() -> None:
                try:
                    _read_transition_event_max_sequence(capability)  # type: ignore[arg-type]
                except _MutationReadCapabilityError as exc:
                    wrong_thread_errors.append(exc)

            thread = threading.Thread(target=borrow_in_thread)
            thread.start()
            thread.join(timeout=5)
            assert not thread.is_alive()

            read_fd, write_fd = os.pipe()
            child_pid = os.fork()
            if child_pid == 0:
                os.close(read_fd)
                try:
                    try:
                        _read_transition_event_max_sequence(capability)  # type: ignore[arg-type]
                    except _MutationReadCapabilityError as exc:
                        result = exc.reason.value
                    else:
                        result = "unexpected-success"
                    os.write(write_fd, result.encode("ascii"))
                finally:
                    os.close(write_fd)
                    os._exit(0)
            os.close(write_fd)
            child_results.append(_wait_for_child_result(child_pid, read_fd))
            parent_results_after_child.append(_read_transition_event_max_sequence(capability))  # type: ignore[arg-type]

        capability = _run_real_controller_with_probe(fixture.writer_session, monkeypatch, probe)
        assert len(wrong_thread_errors) == 1
        _assert_capability_error(wrong_thread_errors[0], _MutationReadCapabilityFailureReason.THREAD_MISMATCH)
        assert child_results == [_MutationReadCapabilityFailureReason.PROCESS_MISMATCH.value]
        assert parent_results_after_child == [0]
        with pytest.raises(_MutationReadCapabilityError) as expired:
            _read_transition_event_max_sequence(capability)  # type: ignore[arg-type]
        _assert_capability_error(expired.value, _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED)


def test_real_nominal_capability_from_transaction_a_cannot_read_during_transaction_b(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, existing_event=True) as fixture:
        captured_a: list[object] = []
        observed_b: list[int | None] = []

        captured_a.append(_run_real_controller_with_probe(fixture.writer_session, monkeypatch, lambda capability: None))

        def probe_b(capability: object) -> None:
            with pytest.raises(_MutationReadCapabilityError) as expired:
                _read_transition_event_max_sequence(captured_a[0])  # type: ignore[arg-type]
            _assert_capability_error(expired.value, _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED)
            observed_b.append(_read_transition_event_max_sequence(capability))  # type: ignore[arg-type]

        _run_real_controller_with_probe(fixture.writer_session, monkeypatch, probe_b)
        assert observed_b == [0]


def test_b3c2_source_boundaries_are_private_unintegrated_and_read_only() -> None:
    event_source = EVENT_READERS_PATH.read_text(encoding="utf-8")
    support_source = SELECT_SUPPORT_PATH.read_text(encoding="utf-8")
    package_source = (PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8")
    writer_source = (PACKAGE_DIR / "sqlite_writer_session.py").read_text(encoding="utf-8")
    transaction_source = (PACKAGE_DIR / "sqlite_transition_transaction.py").read_text(encoding="utf-8")
    all_production_sources = {
        path.name: path.read_text(encoding="utf-8")
        for path in PACKAGE_DIR.glob("*.py")
        if path.name != "sqlite_transition_event_readers.py"
    }

    for name in (
        "_read_transition_event_for_idempotency",
        "_read_transition_event_max_sequence",
        "_MutationReadCapability",
        "_MutationReadCapabilityError",
        "_MutationReadCapabilityFailureReason",
    ):
        assert name not in ge_nwp_coordinator.__all__
        assert name not in package_source

    for forbidden in (
        "match_transition_event_idempotency",
        "next_transition_event_sequence",
        "TransitionCommand",
        "CommittedTransition",
        "TransitionConflict",
        "_read_current_work_item",
        "_read_lease_identity_record",
        "_read_authorization_receipt",
        "_read_dependency_receipt",
        "_read_admitted_backlog",
        "_read_global_stop_current",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
        "INSERT",
        "UPDATE",
        "DELETE",
        "evaluate_transition",
        "TransitionContext",
        "datetime",
        "utc_now",
        "sqlite3",
    ):
        assert forbidden not in event_source

    for forbidden in ("transition_events", "work_items", "global_stop_current", "writer_ownership"):
        assert forbidden not in support_source

    assert "_read_transition_event_for_idempotency" not in writer_source
    assert "_read_transition_event_max_sequence" not in writer_source
    assert "_read_transition_event_for_idempotency" in transaction_source
    assert "_read_transition_event_max_sequence" in transaction_source
    for path_name, source in all_production_sources.items():
        if path_name in {
            "sqlite_transition_event_contracts.py",
            "sqlite_transition_event_readers.py",
            "sqlite_transition_transaction.py",
        }:
            continue
        assert "_TRANSITION_EVENT_IDEMPOTENCY_LOOKUP_SELECT" not in source
        assert "_TRANSITION_EVENT_MAX_SEQUENCE_SELECT" not in source


def test_b3c2_reader_signatures_and_no_public_state_store_widening() -> None:
    import inspect

    signature = inspect.signature(_read_transition_event_for_idempotency)
    assert list(signature.parameters) == ["capability", "work_item_id", "idempotency_key"]
    assert str(signature.return_annotation) == "TransitionEventRecordEnvelope | None"
    max_signature = inspect.signature(_read_transition_event_max_sequence)
    assert list(max_signature.parameters) == ["capability"]
    assert str(max_signature.return_annotation) == "int | None"

    from ge_nwp_coordinator import StateStore, WriterSession

    assert list(inspect.signature(StateStore.read_current).parameters) == ["self", "work_item_id"]
    assert list(inspect.signature(StateStore.read_global_stop).parameters) == ["self"]
    assert not hasattr(StateStore, "read_transition_event")
    assert not hasattr(StateStore, "lookup_idempotency")
    assert list(inspect.signature(WriterSession.apply_transition).parameters) == ["self", "transition_command"]
