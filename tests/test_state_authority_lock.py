from __future__ import annotations

import ast
import gc
import inspect
import multiprocessing as mp
import os
from pathlib import Path
import stat
import weakref

import pytest

import ge_nwp_coordinator.state_authority_lock as lock_module
from ge_nwp_coordinator.sqlite_location import (
    COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME,
    CoordinatorStateLocation,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteStateError, SQLiteStateErrorCode
from ge_nwp_coordinator.state_authority_lock import (
    StateAuthorityLockError,
    StateAuthorityLockErrorReason,
    acquire_state_authority_lock,
)


def _location(root: Path) -> CoordinatorStateLocation:
    return CoordinatorStateLocation.from_trusted_root(root)


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.lstat().st_mode)


def _attempt_lock(root: str, sender) -> None:
    location = CoordinatorStateLocation.from_trusted_root(Path(root))
    try:
        with acquire_state_authority_lock(location):
            sender.send("acquired")
    except StateAuthorityLockError as exc:
        sender.send(exc.reason.value)
    finally:
        sender.close()


def _hold_lock(root: str, ready_sender, release_receiver) -> None:
    location = CoordinatorStateLocation.from_trusted_root(Path(root))
    try:
        with acquire_state_authority_lock(location):
            ready_sender.send("acquired")
            release_receiver.recv()
    finally:
        ready_sender.close()
        release_receiver.close()


def _crash_after_lock(root: str, ready_sender) -> None:
    location = CoordinatorStateLocation.from_trusted_root(Path(root))
    acquire_state_authority_lock(location)
    ready_sender.send("acquired")
    os._exit(0)


def _simulate_child_cleanup_with_locked_gate(root: str, sender) -> None:
    location = CoordinatorStateLocation.from_trusted_root(Path(root))
    lock = acquire_state_authority_lock(location)
    descriptor = lock._descriptor
    lock_module._at_fork_before()
    try:
        lock_module._at_fork_child()
        try:
            os.fstat(descriptor)
            descriptor_state = "open"
        except OSError:
            descriptor_state = "closed"
        try:
            lock.__enter__()
        except StateAuthorityLockError as exc:
            use_result = exc.reason.value
        else:
            use_result = "unexpected-active"
        sender.send(
            (
                descriptor_state,
                use_result,
                lock._resource.descriptor_for_test,
                len(lock_module._ACTIVE_LOCK_RESOURCES),
            )
        )
    finally:
        sender.close()
        os._exit(0)


def _run_attempt(root: Path) -> str:
    context = mp.get_context("fork")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_attempt_lock, args=(str(root), sender))
    process.start()
    sender.close()
    result = receiver.recv()
    receiver.close()
    process.join(5)
    assert process.exitcode == 0
    return result


def _assert_descriptor_closed(descriptor: int) -> None:
    assert descriptor >= 0
    with pytest.raises(OSError):
        os.fstat(descriptor)


def test_lock_file_is_fixed_private_and_persistent(tmp_path: Path) -> None:
    location = _location(tmp_path / "state")

    with acquire_state_authority_lock(location) as lock:
        assert lock.active is True
        assert location.state_authority_lock_path.name == COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME
        assert location.state_authority_lock_path.exists()
        assert _mode(location.state_root) == 0o700
        assert _mode(location.state_authority_lock_path) == 0o600

    assert lock.active is False
    assert location.state_authority_lock_path.exists()
    assert _mode(location.state_authority_lock_path) == 0o600


def test_lock_rejects_symlink_nonregular_hardlink_and_unsafe_permissions(tmp_path: Path) -> None:
    symlink_location = _location(tmp_path / "symlink" / "state")
    symlink_location.state_root.mkdir(mode=0o700, parents=True)
    target = tmp_path / "outside.lock"
    target.write_text("", encoding="utf-8")
    symlink_location.state_authority_lock_path.symlink_to(target)
    with pytest.raises(StateAuthorityLockError) as symlink_error:
        acquire_state_authority_lock(symlink_location)
    assert symlink_error.value.reason is StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK
    assert str(tmp_path) not in str(symlink_error.value)

    directory_location = _location(tmp_path / "directory" / "state")
    directory_location.state_root.mkdir(mode=0o700, parents=True)
    directory_location.state_authority_lock_path.mkdir(mode=0o700)
    with pytest.raises(StateAuthorityLockError, match="unsafe_authority_lock"):
        acquire_state_authority_lock(directory_location)

    permission_location = _location(tmp_path / "permission" / "state")
    permission_location.state_root.mkdir(mode=0o700, parents=True)
    permission_location.state_authority_lock_path.write_text("", encoding="utf-8")
    permission_location.state_authority_lock_path.chmod(0o640)
    with pytest.raises(StateAuthorityLockError, match="unsafe_authority_lock"):
        acquire_state_authority_lock(permission_location)

    hardlink_location = _location(tmp_path / "hardlink" / "state")
    hardlink_location.state_root.mkdir(mode=0o700, parents=True)
    original = tmp_path / "hardlink-original"
    original.write_text("", encoding="utf-8")
    original.chmod(0o600)
    os.link(original, hardlink_location.state_authority_lock_path)
    with pytest.raises(StateAuthorityLockError, match="unsafe_authority_lock"):
        acquire_state_authority_lock(hardlink_location)


def test_lock_rejects_fifo_when_supported(tmp_path: Path) -> None:
    if not hasattr(os, "mkfifo"):
        pytest.skip("fifo creation is not available")
    location = _location(tmp_path / "state")
    location.state_root.mkdir(mode=0o700, parents=True)
    os.mkfifo(location.state_authority_lock_path, 0o600)

    with pytest.raises(StateAuthorityLockError, match="unsafe_authority_lock"):
        acquire_state_authority_lock(location)


def test_alternate_lock_path_and_traversal_are_rejected(tmp_path: Path) -> None:
    root = tmp_path / "state"
    alternate = CoordinatorStateLocation(
        state_root=root,
        database_path=root / "coordinator-state.sqlite",
        state_authority_lock_path=root / "alternate.lock",
        backup_directory_path=root / "backups",
    )
    traversal = CoordinatorStateLocation(
        state_root=root,
        database_path=root / "coordinator-state.sqlite",
        state_authority_lock_path=root.parent / COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME,
        backup_directory_path=root / "backups",
    )

    for location in (alternate, traversal):
        with pytest.raises(StateAuthorityLockError, match="unsafe_authority_lock"):
            acquire_state_authority_lock(location)
    assert not root.exists()


def test_unsupported_platform_fails_closed_without_creating_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path / "state")
    monkeypatch.setattr(lock_module.sys, "platform", "win32")

    with pytest.raises(StateAuthorityLockError) as exc_info:
        acquire_state_authority_lock(location)

    assert exc_info.value.reason is StateAuthorityLockErrorReason.UNSUPPORTED_PLATFORM
    assert not location.state_root.exists()


def test_root_descriptor_closes_on_validation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path / "state")
    opened_root_descriptors: list[int] = []
    original_open_owned = lock_module._open_owned_descriptor
    original_reject_owner = lock_module._reject_unsafe_owner

    def tracking_open_owned(path, *args, **kwargs):
        descriptor = original_open_owned(path, *args, **kwargs)
        if Path(path) == location.state_root:
            opened_root_descriptors.append(descriptor.descriptor)
        return descriptor

    def reject_root_owner(metadata, error_code):
        if error_code == SQLiteStateErrorCode.UNSAFE_STATE_ROOT:
            raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
        return original_reject_owner(metadata, error_code)

    monkeypatch.setattr(lock_module, "_open_owned_descriptor", tracking_open_owned)
    monkeypatch.setattr(lock_module, "_reject_unsafe_owner", reject_root_owner)

    with pytest.raises(StateAuthorityLockError, match="unsafe_authority_lock"):
        acquire_state_authority_lock(location)

    assert opened_root_descriptors
    _assert_descriptor_closed(opened_root_descriptors[-1])
    assert not location.state_authority_lock_path.exists()


def test_lock_descriptor_closes_on_fstat_failure_after_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path / "state")
    opened_lock_descriptors: list[int] = []
    original_open_owned = lock_module._open_owned_descriptor
    original_fstat = lock_module.os.fstat

    def tracking_open_owned(path, *args, **kwargs):
        descriptor = original_open_owned(path, *args, **kwargs)
        if path == COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME:
            opened_lock_descriptors.append(descriptor.descriptor)
        return descriptor

    def failing_lock_fstat(descriptor: int):
        if opened_lock_descriptors and descriptor == opened_lock_descriptors[-1]:
            raise OSError()
        return original_fstat(descriptor)

    monkeypatch.setattr(lock_module, "_open_owned_descriptor", tracking_open_owned)
    monkeypatch.setattr(lock_module.os, "fstat", failing_lock_fstat)

    with pytest.raises(StateAuthorityLockError):
        acquire_state_authority_lock(location)

    assert opened_lock_descriptors
    _assert_descriptor_closed(opened_lock_descriptors[-1])
    monkeypatch.setattr(lock_module, "_open_owned_descriptor", original_open_owned)
    monkeypatch.setattr(lock_module.os, "fstat", original_fstat)
    with acquire_state_authority_lock(location):
        pass


def test_lock_descriptor_closes_on_metadata_validation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path / "state")
    opened_lock_descriptors: list[int] = []
    original_open_owned = lock_module._open_owned_descriptor
    original_validate = lock_module._validate_lock_metadata

    def tracking_open_owned(path, *args, **kwargs):
        descriptor = original_open_owned(path, *args, **kwargs)
        if path == COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME:
            opened_lock_descriptors.append(descriptor.descriptor)
        return descriptor

    def reject_lock_metadata(metadata):
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK)

    monkeypatch.setattr(lock_module, "_open_owned_descriptor", tracking_open_owned)
    monkeypatch.setattr(lock_module, "_validate_lock_metadata", reject_lock_metadata)

    with pytest.raises(StateAuthorityLockError, match="unsafe_authority_lock"):
        acquire_state_authority_lock(location)

    assert opened_lock_descriptors
    _assert_descriptor_closed(opened_lock_descriptors[-1])
    monkeypatch.setattr(lock_module, "_open_owned_descriptor", original_open_owned)
    monkeypatch.setattr(lock_module, "_validate_lock_metadata", original_validate)
    with acquire_state_authority_lock(location):
        pass


def test_failure_after_flock_releases_descriptor_and_allows_later_acquisition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path / "state")
    original_resource_type = lock_module._StateAuthorityLockResource

    def fail_resource_construction(*args, **kwargs):
        raise RuntimeError("test-only resource publication failure")

    monkeypatch.setattr(lock_module, "_StateAuthorityLockResource", fail_resource_construction)
    with pytest.raises(StateAuthorityLockError) as exc_info:
        acquire_state_authority_lock(location)

    assert exc_info.value.reason is StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_FAILED
    assert "test-only resource publication failure" not in str(exc_info.value)
    assert lock_module._ACTIVE_LOCK_RESOURCES == {}
    monkeypatch.setattr(lock_module, "_StateAuthorityLockResource", original_resource_type)
    with acquire_state_authority_lock(location):
        pass


def test_context_lifecycle_close_and_duplicate_same_process_acquisition(tmp_path: Path) -> None:
    location = _location(tmp_path / "state")
    lock = acquire_state_authority_lock(location)
    assert lock.active is True

    with pytest.raises(StateAuthorityLockError) as exc_info:
        acquire_state_authority_lock(location)
    assert exc_info.value.reason is StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_BUSY

    lock.close()
    lock.close()
    assert lock.active is False
    with pytest.raises(StateAuthorityLockError) as closed_error:
        lock.__enter__()
    assert closed_error.value.reason is StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_CLOSED


def test_abandoned_lock_object_finalizer_releases_descriptor_and_registry(tmp_path: Path) -> None:
    location = _location(tmp_path / "state")
    lock = acquire_state_authority_lock(location)
    identity = lock._resource.identity
    reference = weakref.ref(lock)

    del lock
    gc.collect()

    assert reference() is None
    assert identity not in lock_module._ACTIVE_LOCK_RESOURCES
    assert _run_attempt(location.state_root) == "acquired"


def test_explicit_close_and_finalizer_are_one_shot_and_descriptor_reuse_safe(tmp_path: Path) -> None:
    location = _location(tmp_path / "state")
    lock = acquire_state_authority_lock(location)
    descriptor = lock._descriptor
    identity = lock._resource.identity
    lock.close()
    lock.close()
    assert identity not in lock_module._ACTIVE_LOCK_RESOURCES

    borrowed = os.open(__file__, os.O_RDONLY)
    try:
        reused_descriptor_number = borrowed == descriptor
        del lock
        gc.collect()
        os.fstat(borrowed)
        assert reused_descriptor_number or borrowed >= 0
    finally:
        os.close(borrowed)

    assert _run_attempt(location.state_root) == "acquired"


def test_construction_failure_after_flock_releases_descriptor_and_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path / "state")

    def fail_finalizer(*args, **kwargs):
        raise RuntimeError("test-only finalizer failure")

    monkeypatch.setattr(lock_module, "_FINALIZER_FACTORY", fail_finalizer)
    with pytest.raises(StateAuthorityLockError) as exc_info:
        acquire_state_authority_lock(location)

    assert exc_info.value.reason is StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_FAILED
    assert "test-only finalizer failure" not in str(exc_info.value)
    assert lock_module._ACTIVE_LOCK_RESOURCES == {}
    monkeypatch.setattr(lock_module, "_FINALIZER_FACTORY", weakref.finalize)
    assert _run_attempt(location.state_root) == "acquired"


def test_lock_descriptor_is_not_inheritable(tmp_path: Path) -> None:
    location = _location(tmp_path / "state")
    lock = acquire_state_authority_lock(location)
    try:
        assert os.get_inheritable(lock._descriptor) is False
    finally:
        lock.close()


def test_process_mismatch_rejects_use_without_exposing_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path / "state")
    lock = acquire_state_authority_lock(location)
    real_pid = os.getpid()
    monkeypatch.setattr(lock_module.os, "getpid", lambda: real_pid + 1)

    with pytest.raises(StateAuthorityLockError) as exc_info:
        lock.__enter__()

    assert exc_info.value.reason is StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_PROCESS_MISMATCH
    assert str(real_pid) not in str(exc_info.value)


def test_at_fork_child_invalidates_descriptor_and_parent_retains_lock(tmp_path: Path) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location = _location(tmp_path / "state")
    lock = acquire_state_authority_lock(location)
    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        try:
            try:
                lock.__enter__()
            except StateAuthorityLockError as exc:
                os.write(write_fd, exc.reason.value.encode("ascii"))
            else:
                os.write(write_fd, b"unexpected-active")
        finally:
            os.close(write_fd)
            os._exit(0)

    os.close(write_fd)
    child_result = os.read(read_fd, 128).decode("ascii")
    os.close(read_fd)
    waited_pid, status = os.waitpid(child_pid, 0)
    assert waited_pid == child_pid
    assert status == 0
    assert child_result == "state_authority_lock_process_mismatch"
    assert lock.active is True
    assert _run_attempt(location.state_root) == "state_authority_lock_busy"

    lock.close()
    assert _run_attempt(location.state_root) == "acquired"


def test_fork_child_cleanup_does_not_prolong_parent_lock_after_parent_close(tmp_path: Path) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location = _location(tmp_path / "state")
    lock = acquire_state_authority_lock(location)
    child_ready_read, child_ready_write = os.pipe()
    release_read, release_write = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(child_ready_read)
        os.close(release_write)
        try:
            os.write(child_ready_write, b"ready")
            os.read(release_read, 1)
        finally:
            os.close(child_ready_write)
            os.close(release_read)
            os._exit(0)

    os.close(child_ready_write)
    os.close(release_read)
    assert os.read(child_ready_read, 5) == b"ready"
    os.close(child_ready_read)
    lock.close()
    assert _run_attempt(location.state_root) == "acquired"
    os.write(release_write, b"x")
    os.close(release_write)
    waited_pid, status = os.waitpid(child_pid, 0)
    assert waited_pid == child_pid
    assert status == 0


def test_child_finalizer_after_fork_does_not_double_close_or_affect_parent(tmp_path: Path) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location = _location(tmp_path / "state")
    lock = acquire_state_authority_lock(location)
    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        try:
            del lock
            gc.collect()
            os.write(write_fd, b"ok")
        finally:
            os.close(write_fd)
            os._exit(0)

    os.close(write_fd)
    assert os.read(read_fd, 2) == b"ok"
    os.close(read_fd)
    waited_pid, status = os.waitpid(child_pid, 0)
    assert waited_pid == child_pid
    assert status == 0
    assert lock.active is True
    assert _run_attempt(location.state_root) == "state_authority_lock_busy"
    lock.close()


def test_fork_child_cleanup_does_not_acquire_inherited_locked_gate(tmp_path: Path) -> None:
    context = mp.get_context("fork")
    location = _location(tmp_path / "state")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_simulate_child_cleanup_with_locked_gate, args=(str(location.state_root), sender))
    process.start()
    sender.close()
    assert receiver.poll(5), "child cleanup did not complete"
    descriptor_state, use_result, resource_descriptor, registry_size = receiver.recv()
    receiver.close()
    process.join(5)
    if process.is_alive():
        process.terminate()
        process.join(5)
    assert process.exitcode == 0
    assert descriptor_state == "closed"
    assert use_result == "state_authority_lock_process_mismatch"
    assert resource_descriptor == -1
    assert registry_size == 0


def test_cross_process_exclusion_release_and_crash_release(tmp_path: Path) -> None:
    context = mp.get_context("fork")
    location = _location(tmp_path / "state")

    ready_receiver, ready_sender = context.Pipe(duplex=False)
    release_receiver, release_sender = context.Pipe(duplex=False)
    holder = context.Process(target=_hold_lock, args=(str(location.state_root), ready_sender, release_receiver))
    holder.start()
    ready_sender.close()
    release_receiver.close()
    assert ready_receiver.recv() == "acquired"
    ready_receiver.close()

    assert _run_attempt(location.state_root) == "state_authority_lock_busy"
    release_sender.send("release")
    release_sender.close()
    holder.join(5)
    assert holder.exitcode == 0
    assert _run_attempt(location.state_root) == "acquired"
    assert location.state_authority_lock_path.exists()

    crash_receiver, crash_sender = context.Pipe(duplex=False)
    crasher = context.Process(target=_crash_after_lock, args=(str(location.state_root), crash_sender))
    crasher.start()
    crash_sender.close()
    assert crash_receiver.recv() == "acquired"
    crash_receiver.close()
    crasher.join(5)
    assert crasher.exitcode == 0
    assert _run_attempt(location.state_root) == "acquired"
    assert location.state_authority_lock_path.exists()


def test_at_fork_registration_and_child_callback_boundaries(monkeypatch: pytest.MonkeyPatch) -> None:
    registrations: list[dict[str, object]] = []

    def fake_register_at_fork(**kwargs):
        registrations.append(kwargs)

    monkeypatch.setattr(lock_module, "_AT_FORK_REGISTERED", False)
    monkeypatch.setattr(lock_module.os, "register_at_fork", fake_register_at_fork)
    lock_module._LIFECYCLE_GATE.acquire()
    try:
        lock_module._register_at_fork_once_locked()
        lock_module._register_at_fork_once_locked()
    finally:
        lock_module._LIFECYCLE_GATE.release()

    assert len(registrations) == 1
    assert registrations[0] == {
        "before": lock_module._at_fork_before,
        "after_in_parent": lock_module._at_fork_parent,
        "after_in_child": lock_module._at_fork_child,
    }

    source = "".join(
        inspect.getsource(function)
        for function in (
            lock_module._at_fork_child,
            lock_module._mark_resource_closed_after_fork,
            lock_module._close_inherited_descriptor_after_fork,
        )
    )
    assert ".acquire(" not in source
    assert "LOCK_UN" not in source


def test_lock_path_os_open_calls_are_immediately_owned() -> None:
    source = Path(lock_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    open_call_functions: list[str] = []

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self._function_stack: list[str] = []

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._function_stack.append(node.name)
            self.generic_visit(node)
            self._function_stack.pop()

        def visit_Call(self, node: ast.Call) -> None:
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "open"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "os"
            ):
                open_call_functions.append(self._function_stack[-1])
            self.generic_visit(node)

    Visitor().visit(tree)

    assert open_call_functions == ["_open_owned_descriptor", "_open_owned_descriptor"]


def test_lock_source_has_no_polling_ttl_or_writer_authority() -> None:
    source = Path(lock_module.__file__).read_text(encoding="utf-8")
    for fragment in (
        "sleep(",
        "heartbeat",
        "expiry",
        "takeover",
        "writer_ref",
        "issued_ref",
        "writer_ownership",
        "apply_transition",
        "apply_global_stop_update",
    ):
        assert fragment not in source
