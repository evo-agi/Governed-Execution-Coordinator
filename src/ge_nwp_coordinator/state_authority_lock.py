"""Shared state-authority advisory lock for SQLite administration.

This module owns only local exclusion for state administration and future
writer acquisition. Holding this lock is not writer authority.
"""

from __future__ import annotations

from _thread import allocate_lock
from dataclasses import dataclass, replace
from enum import Enum
import os
from pathlib import Path
import stat
import sys
from types import TracebackType
from typing import Self
import weakref

try:
    import fcntl
except ImportError:  # pragma: no cover - exercised by platform checks.
    fcntl = None  # type: ignore[assignment]

from ge_nwp_coordinator.sqlite_errors import SQLiteStateError, SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_location import (
    COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME,
    CoordinatorStateLocation,
)
from ge_nwp_coordinator.sqlite_security import (
    _FilesystemObjectIdentity,
    _StateDatabaseAuthorityBinding,
    _StateDatabaseAuthorityBindingMismatch,
    _capture_state_database_authority_binding,
    _filesystem_identity_for_stat,
    _validate_state_database_authority_binding,
    _reject_network_like_root,
    _reject_repository_checkout,
    _reject_unsafe_owner,
    _restrictive_umask,
    _validate_state_root,
)

_PRIVATE_DIR_MODE = 0o700
_PRIVATE_FILE_MODE = 0o600
_ACTIVE = "active"
_CLOSING = "closing"
_RELEASE_UNPROVED = "release_unproved"
_RELEASE_PROVED = "release_proved"
_CLOSED = "closed"
_DESCRIPTOR_NOT_ATTEMPTED = "not_attempted"
_DESCRIPTOR_RECLAIMED = "reclaimed"
_DESCRIPTOR_RECLAMATION_UNKNOWN = "reclamation_unknown"


@dataclass(frozen=True, slots=True)
class _StateAuthorityLockCleanupSnapshot:
    """One complete publication of authority-lock release and reclamation truth."""

    descriptor: int
    attempted_descriptor: int | None
    owner_pid: int
    state: str
    descriptor_outcome: str
    registry_removed: bool
    finalizer_attempted: bool
    retry_reachable: bool

    def __post_init__(self) -> None:
        if type(self.descriptor) is not int or type(self.owner_pid) is not int:
            raise ValueError("invalid authority-lock state")
        if self.attempted_descriptor is not None and (
            type(self.attempted_descriptor) is not int or self.attempted_descriptor < 0
        ):
            raise ValueError("invalid authority-lock state")
        if type(self.registry_removed) is not bool:
            raise ValueError("invalid authority-lock state")
        if type(self.finalizer_attempted) is not bool or type(self.retry_reachable) is not bool:
            raise ValueError("invalid authority-lock state")
        if self.state in {_ACTIVE, _CLOSING, _RELEASE_UNPROVED}:
            valid = (
                self.descriptor >= 0
                and self.attempted_descriptor is None
                and self.descriptor_outcome == _DESCRIPTOR_NOT_ATTEMPTED
                and not self.registry_removed
                and self.owner_pid >= 0
            )
        elif self.state == _RELEASE_PROVED:
            if self.descriptor_outcome == _DESCRIPTOR_NOT_ATTEMPTED:
                valid = self.descriptor >= 0 and self.attempted_descriptor is None
            else:
                valid = (
                    self.descriptor == -1
                    and self.attempted_descriptor is not None
                    and self.descriptor_outcome
                    in {_DESCRIPTOR_RECLAIMED, _DESCRIPTOR_RECLAMATION_UNKNOWN}
                )
            valid = valid and not self.registry_removed and self.owner_pid >= 0
        elif self.state == _CLOSED:
            valid = (
                self.descriptor == -1
                and self.descriptor_outcome
                in {_DESCRIPTOR_RECLAIMED, _DESCRIPTOR_RECLAMATION_UNKNOWN}
            )
        else:
            valid = False
        if not valid:
            raise ValueError("invalid authority-lock state")

_LIFECYCLE_GATE = allocate_lock()
_ACTIVE_LOCK_RESOURCES: dict[tuple[int, int], "_StateAuthorityLockResource"] = {}
_AT_FORK_SNAPSHOT: tuple[tuple["_StateAuthorityLockResource", int], ...] = ()
_AT_FORK_REGISTERED = False
_FINALIZER_FACTORY = weakref.finalize


class StateAuthorityLockErrorReason(str, Enum):
    UNSUPPORTED_PLATFORM = "unsupported_platform"
    UNSAFE_AUTHORITY_LOCK = "unsafe_authority_lock"
    STATE_AUTHORITY_LOCK_BUSY = "state_authority_lock_busy"
    STATE_AUTHORITY_LOCK_FAILED = "state_authority_lock_failed"
    STATE_AUTHORITY_LOCK_CLOSED = "state_authority_lock_closed"
    STATE_AUTHORITY_LOCK_PROCESS_MISMATCH = "state_authority_lock_process_mismatch"


class StateAuthorityLockError(RuntimeError):
    """Closed public lock error whose string form is only the safe reason."""

    def __init__(self, reason: StateAuthorityLockErrorReason | str) -> None:
        normalized = StateAuthorityLockErrorReason(reason)
        self.reason = normalized
        super().__init__(normalized.value)


class StateAuthorityLock:
    """Acquired state-authority lock descriptor.

    The object deliberately contains no writer generation, writer refs, proof,
    SQLite connection, or state mutation method.
    """

    def __init__(self, resource: "_StateAuthorityLockResource") -> None:
        self._resource = resource
        self._finalizer = _FINALIZER_FACTORY(self, _finalize_resource, resource)
        self._finalizer.atexit = False

    @property
    def active(self) -> bool:
        return self._resource.active_for_owner()

    def close(self) -> None:
        self._resource.cleanup_from_owner()
        if self._resource.cleanup_terminal and self._finalizer.alive:
            self._finalizer.detach()

    def __enter__(self) -> Self:
        self._resource.require_active_for_owner()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    @property
    def _descriptor(self) -> int:
        return self._resource.descriptor_for_test

    def _capture_state_database_authority_binding(
        self,
        location: CoordinatorStateLocation,
    ) -> _StateDatabaseAuthorityBinding:
        return self._resource.capture_state_database_authority_binding(location)

    def _validate_state_database_authority_binding(
        self,
        binding: _StateDatabaseAuthorityBinding,
    ) -> None:
        self._resource.validate_state_database_authority_binding(binding)


class _StateAuthorityLockResource:
    """Private descriptor owner for one acquired state-authority lock."""

    def __init__(
        self,
        descriptor: int,
        identity: tuple[int, int],
        *,
        state_root_identity: _FilesystemObjectIdentity,
        authority_lock_file_identity: _FilesystemObjectIdentity,
    ) -> None:
        self._identity = identity
        self._state_root_identity = state_root_identity
        self._authority_lock_file_identity = authority_lock_file_identity
        self._cleanup_snapshot = _StateAuthorityLockCleanupSnapshot(
            descriptor=descriptor,
            attempted_descriptor=None,
            owner_pid=os.getpid(),
            state=_ACTIVE,
            descriptor_outcome=_DESCRIPTOR_NOT_ATTEMPTED,
            registry_removed=False,
            finalizer_attempted=False,
            retry_reachable=True,
        )

    @property
    def _descriptor(self) -> int:
        return self._cleanup_snapshot.descriptor

    @property
    def _owner_pid(self) -> int:
        return self._cleanup_snapshot.owner_pid

    @property
    def _state(self) -> str:
        return self._cleanup_snapshot.state

    @property
    def _descriptor_outcome(self) -> str:
        return self._cleanup_snapshot.descriptor_outcome

    @property
    def _registry_removed(self) -> bool:
        return self._cleanup_snapshot.registry_removed

    @property
    def _finalizer_attempted(self) -> bool:
        return self._cleanup_snapshot.finalizer_attempted

    @property
    def _retry_reachable(self) -> bool:
        return self._cleanup_snapshot.retry_reachable

    @property
    def identity(self) -> tuple[int, int]:
        return self._identity

    @property
    def descriptor_for_test(self) -> int:
        _LIFECYCLE_GATE.acquire()
        try:
            return self._descriptor
        finally:
            _LIFECYCLE_GATE.release()

    @property
    def cleanup_terminal(self) -> bool:
        _LIFECYCLE_GATE.acquire()
        try:
            return self._state == _CLOSED and self._registry_removed
        finally:
            _LIFECYCLE_GATE.release()

    def cleanup_status_for_writer(self) -> tuple[str, str, bool]:
        _LIFECYCLE_GATE.acquire()
        try:
            return (self._state, self._descriptor_outcome, self._registry_removed)
        finally:
            _LIFECYCLE_GATE.release()

    def active_for_owner(self) -> bool:
        if self._owner_pid != os.getpid():
            self.cleanup_from_foreign_process()
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_PROCESS_MISMATCH)
        _LIFECYCLE_GATE.acquire()
        try:
            return self._state == _ACTIVE and self._descriptor >= 0
        finally:
            _LIFECYCLE_GATE.release()

    def require_active_for_owner(self) -> None:
        if self._owner_pid != os.getpid():
            self.cleanup_from_foreign_process()
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_PROCESS_MISMATCH)
        _LIFECYCLE_GATE.acquire()
        try:
            active = self._state == _ACTIVE and self._descriptor >= 0
        finally:
            _LIFECYCLE_GATE.release()
        if not active:
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_CLOSED)

    def capture_state_database_authority_binding(
        self,
        location: CoordinatorStateLocation,
    ) -> _StateDatabaseAuthorityBinding:
        self.require_active_for_owner()
        return _capture_state_database_authority_binding(
            location,
            state_root_identity=self._state_root_identity,
            authority_lock_file_identity=self._authority_lock_file_identity,
        )

    def validate_state_database_authority_binding(
        self,
        binding: _StateDatabaseAuthorityBinding,
    ) -> None:
        self.require_active_for_owner()
        if type(binding) is not _StateDatabaseAuthorityBinding:
            raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
        _capture_state_database_authority_binding(
            binding._location_for_private_open(),
            state_root_identity=self._state_root_identity,
            authority_lock_file_identity=self._authority_lock_file_identity,
        )
        _validate_state_database_authority_binding(binding)

    def active_in_registry(self) -> bool:
        return self._owner_pid == os.getpid() and not self._registry_removed

    def cleanup_from_owner(self) -> None:
        self._require_owner_for_cleanup()
        _LIFECYCLE_GATE.acquire()
        try:
            self._continue_cleanup_locked(finalizer=False)
        finally:
            _LIFECYCLE_GATE.release()

    def cleanup_from_finalizer(self) -> None:
        if self._owner_pid != os.getpid():
            self.cleanup_from_foreign_process()
            return
        _LIFECYCLE_GATE.acquire()
        try:
            self._cleanup_snapshot = replace(
                self._cleanup_snapshot,
                finalizer_attempted=True,
                retry_reachable=False,
            )
            self._continue_cleanup_locked(finalizer=True)
        finally:
            _LIFECYCLE_GATE.release()

    def cleanup_from_foreign_process(self) -> None:
        self._close_without_lock(release_lock=False)

    def _require_owner_for_cleanup(self) -> None:
        if self._owner_pid != os.getpid():
            self.cleanup_from_foreign_process()
            raise StateAuthorityLockError(
                StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_PROCESS_MISMATCH
            )

    def _continue_cleanup_locked(self, *, finalizer: bool) -> None:
        snapshot = self._cleanup_snapshot
        if snapshot.state == _CLOSED and snapshot.registry_removed:
            return
        if snapshot.state == _CLOSED:
            _remove_active_resource(self._identity, self)
            self._cleanup_snapshot = replace(
                snapshot,
                registry_removed=_ACTIVE_LOCK_RESOURCES.get(self._identity) is not self,
            )
            return
        if snapshot.state in {_ACTIVE, _CLOSING, _RELEASE_UNPROVED}:
            self._cleanup_snapshot = replace(snapshot, state=_RELEASE_UNPROVED)
            descriptor = self._cleanup_snapshot.descriptor
            if descriptor < 0:
                return
            try:
                _unlock_authority_descriptor_with_proof(descriptor)
            except Exception:
                return
            except BaseException:
                if finalizer:
                    return
                raise
            else:
                self._cleanup_snapshot = replace(self._cleanup_snapshot, state=_RELEASE_PROVED)

        snapshot = self._cleanup_snapshot
        if snapshot.state == _RELEASE_PROVED and snapshot.descriptor_outcome == _DESCRIPTOR_NOT_ATTEMPTED:
            descriptor = snapshot.descriptor
            self._cleanup_snapshot = replace(
                snapshot,
                descriptor=-1,
                attempted_descriptor=descriptor,
                descriptor_outcome=_DESCRIPTOR_RECLAMATION_UNKNOWN,
            )
            try:
                _reclaim_detached_descriptor_once(descriptor)
            except Exception:
                pass
            except BaseException:
                if finalizer:
                    return
                raise
            else:
                self._cleanup_snapshot = replace(
                    self._cleanup_snapshot,
                    descriptor_outcome=_DESCRIPTOR_RECLAIMED,
                )

        snapshot = self._cleanup_snapshot
        if (
            snapshot.state == _RELEASE_PROVED
            and snapshot.descriptor_outcome
            in {_DESCRIPTOR_RECLAIMED, _DESCRIPTOR_RECLAMATION_UNKNOWN}
        ):
            self._cleanup_snapshot = replace(snapshot, state=_CLOSED)
            _remove_active_resource(self._identity, self)
            self._cleanup_snapshot = replace(
                self._cleanup_snapshot,
                registry_removed=_ACTIVE_LOCK_RESOURCES.get(self._identity) is not self,
            )

    def _cleanup_locked(self, *, release_lock: bool) -> None:
        if release_lock:
            self._continue_cleanup_locked(finalizer=False)
            return
        self._close_without_lock(release_lock=False)

    def _close_without_lock(self, *, release_lock: bool) -> None:
        snapshot = self._cleanup_snapshot
        descriptor = snapshot.descriptor
        identity = self._identity
        self._cleanup_snapshot = _StateAuthorityLockCleanupSnapshot(
            descriptor=-1,
            attempted_descriptor=descriptor if descriptor >= 0 else snapshot.attempted_descriptor,
            owner_pid=-1,
            state=_CLOSED,
            descriptor_outcome=_DESCRIPTOR_RECLAMATION_UNKNOWN,
            registry_removed=True,
            finalizer_attempted=snapshot.finalizer_attempted,
            retry_reachable=False,
        )
        try:
            if _ACTIVE_LOCK_RESOURCES.get(identity) is self:
                _ACTIVE_LOCK_RESOURCES.pop(identity, None)
        finally:
            _close_resource_descriptor(descriptor, release_lock=release_lock)

    def _mark_closed_after_fork(self, descriptor: int) -> None:
        snapshot = self._cleanup_snapshot
        self._cleanup_snapshot = _StateAuthorityLockCleanupSnapshot(
            descriptor=-1,
            attempted_descriptor=descriptor if descriptor >= 0 else snapshot.attempted_descriptor,
            owner_pid=-1,
            state=_CLOSED,
            descriptor_outcome=_DESCRIPTOR_RECLAMATION_UNKNOWN,
            registry_removed=True,
            finalizer_attempted=snapshot.finalizer_attempted,
            retry_reachable=False,
        )


class _OwnedDescriptor:
    """Short-lived descriptor owner used until ownership is explicitly moved."""

    def __init__(self, descriptor: int) -> None:
        self._descriptor = descriptor

    @property
    def descriptor(self) -> int:
        return self._descriptor

    def transfer(self) -> int:
        descriptor = self._descriptor
        self._descriptor = -1
        return descriptor

    def _close(self) -> None:
        _close_raw_descriptor(self.transfer())


def acquire_state_authority_lock(location: CoordinatorStateLocation) -> StateAuthorityLock:
    """Acquire the fixed state-authority lock without blocking indefinitely."""

    _ensure_supported_platform()
    descriptor = -1
    resource: _StateAuthorityLockResource | None = None
    state_root_identity: _FilesystemObjectIdentity | None = None
    lock_file_identity: _FilesystemObjectIdentity | None = None
    _LIFECYCLE_GATE.acquire()
    try:
        _register_at_fork_once_locked()
        descriptor, state_root_identity = _open_prepared_lock_file(location)
        identity, lock_file_identity = _lock_identity(descriptor)
        if _active_resource_for_locked(identity) is not None:
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_BUSY)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)  # type: ignore[union-attr]
        except BlockingIOError:
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_BUSY) from None
        except OSError:
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_FAILED) from None
        if _active_resource_for_locked(identity) is not None:
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_BUSY)
        resource = _StateAuthorityLockResource(
            descriptor,
            identity,
            state_root_identity=state_root_identity,
            authority_lock_file_identity=lock_file_identity,
        )
        _ACTIVE_LOCK_RESOURCES[identity] = resource
        lock = StateAuthorityLock(resource)
        descriptor = -1
        return lock
    except Exception as exc:
        if resource is not None:
            resource._cleanup_locked(release_lock=True)
        elif descriptor >= 0:
            _close_resource_descriptor(descriptor, release_lock=True)
        if isinstance(exc, StateAuthorityLockError):
            raise
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_FAILED) from None
    finally:
        _LIFECYCLE_GATE.release()


def _ensure_supported_platform() -> None:
    if not (sys.platform == "darwin" or sys.platform.startswith("linux")):
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSUPPORTED_PLATFORM)
    required = (
        fcntl is not None,
        hasattr(fcntl, "flock") if fcntl is not None else False,
        hasattr(os, "O_DIRECTORY"),
        hasattr(os, "O_NOFOLLOW"),
        hasattr(os, "O_CLOEXEC"),
        hasattr(os, "register_at_fork"),
        os.open in os.supports_dir_fd,
        os.stat in os.supports_dir_fd,
        os.stat in os.supports_follow_symlinks,
    )
    if not all(required):
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSUPPORTED_PLATFORM)


def _open_prepared_lock_file(location: CoordinatorStateLocation) -> tuple[int, _FilesystemObjectIdentity]:
    if not isinstance(location, CoordinatorStateLocation):
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK)
    _assert_fixed_lock_path(location)
    try:
        _reject_network_like_root(location.state_root)
        _reject_repository_checkout(location.state_root)
    except SQLiteStateError:
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK) from None
    if location.state_root.is_symlink():
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK)
    with _restrictive_umask():
        try:
            location.state_root.mkdir(mode=_PRIVATE_DIR_MODE, parents=True, exist_ok=True)
        except OSError:
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK) from None
    root = _validate_root_for_lock(location.state_root)
    root_descriptor = _open_root_descriptor(root)
    try:
        root_identity = _filesystem_identity_for_stat(os.fstat(root_descriptor.descriptor))
        return (_open_lock_file_at(root_descriptor.descriptor), root_identity)
    finally:
        root_descriptor._close()


def _assert_fixed_lock_path(location: CoordinatorStateLocation) -> None:
    if location.state_authority_lock_path.name != COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME:
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK)
    try:
        expected = location.state_root / COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME
        if location.state_authority_lock_path != expected:
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK)
    except TypeError:
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK) from None


def _validate_root_for_lock(root: Path) -> Path:
    try:
        return _validate_state_root(root)
    except SQLiteStateError as exc:
        if exc.error_class in {
            SQLiteStateErrorCode.UNSAFE_STATE_ROOT.value,
            SQLiteStateErrorCode.UNSUPPORTED_FILESYSTEM.value,
        }:
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK) from None
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_FAILED) from None


def _open_root_descriptor(root: Path) -> _OwnedDescriptor:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        descriptor = _open_owned_descriptor(root, flags)
        os.set_inheritable(descriptor.descriptor, False)
        metadata = os.fstat(descriptor.descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK)
        _reject_unsafe_owner(metadata, SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
        if stat.S_IMODE(metadata.st_mode) & 0o077:
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK)
        return descriptor
    except StateAuthorityLockError:
        if "descriptor" in locals():
            descriptor._close()
        raise
    except (OSError, SQLiteStateError):
        if "descriptor" in locals():
            descriptor._close()
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK) from None


def _open_lock_file_at(root_descriptor: int) -> int:
    lock_name = COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME
    for _attempt in range(2):
        try:
            existing = os.stat(lock_name, dir_fd=root_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            descriptor = _create_lock_file_at(root_descriptor)
            if descriptor is None:
                continue
            try:
                _validate_lock_metadata(os.fstat(descriptor.descriptor))
                os.set_inheritable(descriptor.descriptor, False)
                return descriptor.transfer()
            except Exception:
                descriptor._close()
                raise
        except OSError:
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK) from None
        _validate_lock_metadata(existing)
        descriptor = _open_existing_lock_file_at(root_descriptor)
        try:
            opened = os.fstat(descriptor.descriptor)
            _validate_lock_metadata(opened)
            if (opened.st_dev, opened.st_ino) != (existing.st_dev, existing.st_ino):
                raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK)
            os.set_inheritable(descriptor.descriptor, False)
            return descriptor.transfer()
        except Exception:
            descriptor._close()
            raise
    raise StateAuthorityLockError(StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_FAILED)


def _create_lock_file_at(root_descriptor: int) -> _OwnedDescriptor | None:
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    with _restrictive_umask():
        try:
            return _open_owned_descriptor(
                COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME,
                flags,
                _PRIVATE_FILE_MODE,
                dir_fd=root_descriptor,
            )
        except FileExistsError:
            return None
        except OSError:
            raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK) from None


def _open_existing_lock_file_at(root_descriptor: int) -> _OwnedDescriptor:
    flags = os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        return _open_owned_descriptor(
            COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME,
            flags,
            dir_fd=root_descriptor,
        )
    except OSError:
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK) from None


def _open_owned_descriptor(
    path: str | bytes | Path,
    flags: int,
    mode: int | None = None,
    *,
    dir_fd: int | None = None,
) -> _OwnedDescriptor:
    try:
        if mode is None:
            return _OwnedDescriptor(os.open(path, flags, dir_fd=dir_fd))
        return _OwnedDescriptor(
            os.open(
                path,
                flags,
                mode,
                dir_fd=dir_fd,
            )
        )
    except OSError:
        raise


def _close_resource_descriptor(descriptor: int, *, release_lock: bool) -> None:
    if descriptor < 0:
        return
    if release_lock:
        _unlock_authority_descriptor_with_proof(descriptor)
    _close_raw_descriptor(descriptor)


def _unlock_authority_descriptor_with_proof(descriptor: int) -> None:
    fcntl.flock(descriptor, fcntl.LOCK_UN)  # type: ignore[union-attr]


def _reclaim_detached_descriptor_once(descriptor: int) -> None:
    if type(descriptor) is not int or descriptor < 0:
        raise ValueError("invalid detached descriptor")
    os.close(descriptor)


def _close_raw_descriptor(descriptor: int) -> None:
    if descriptor < 0:
        return
    try:
        os.close(descriptor)
    except OSError:
        pass


def _close_inherited_descriptor_after_fork(descriptor: int) -> None:
    if descriptor < 0:
        return
    try:
        os.close(descriptor)
    except OSError:
        pass


def _mark_resource_closed_after_fork(resource: _StateAuthorityLockResource, descriptor: int) -> None:
    resource._mark_closed_after_fork(descriptor)
    _close_inherited_descriptor_after_fork(descriptor)


def _validate_lock_metadata(metadata: os.stat_result) -> None:
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK)
    try:
        _reject_unsafe_owner(metadata, SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
    except SQLiteStateError:
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK) from None
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK)
    if getattr(metadata, "st_nlink", 1) != 1:
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.UNSAFE_AUTHORITY_LOCK)


def _lock_identity(descriptor: int) -> tuple[tuple[int, int], _FilesystemObjectIdentity]:
    try:
        metadata = os.fstat(descriptor)
    except OSError:
        raise StateAuthorityLockError(StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_FAILED) from None
    identity = _filesystem_identity_for_stat(metadata)
    return (identity._registry_key(), identity)


def _active_resource_for_locked(identity: tuple[int, int]) -> _StateAuthorityLockResource | None:
    resource = _ACTIVE_LOCK_RESOURCES.get(identity)
    return resource


def _remove_active_resource(identity: tuple[int, int], resource: _StateAuthorityLockResource) -> None:
    if _ACTIVE_LOCK_RESOURCES.get(identity) is resource:
        _ACTIVE_LOCK_RESOURCES.pop(identity, None)


def _register_at_fork_once_locked() -> None:
    global _AT_FORK_REGISTERED
    if _AT_FORK_REGISTERED:
        return
    os.register_at_fork(
        before=_at_fork_before,
        after_in_parent=_at_fork_parent,
        after_in_child=_at_fork_child,
    )
    _AT_FORK_REGISTERED = True


def _at_fork_before() -> None:
    global _AT_FORK_SNAPSHOT
    _LIFECYCLE_GATE.acquire()
    _AT_FORK_SNAPSHOT = tuple(
        (resource, resource._descriptor)
        for resource in _ACTIVE_LOCK_RESOURCES.values()
        if resource._descriptor >= 0
    )


def _at_fork_parent() -> None:
    global _AT_FORK_SNAPSHOT
    _AT_FORK_SNAPSHOT = ()
    _LIFECYCLE_GATE.release()


def _at_fork_child() -> None:
    global _ACTIVE_LOCK_RESOURCES, _AT_FORK_SNAPSHOT, _LIFECYCLE_GATE
    snapshot = _AT_FORK_SNAPSHOT
    _ACTIVE_LOCK_RESOURCES = {}
    _AT_FORK_SNAPSHOT = ()
    for resource, descriptor in snapshot:
        _mark_resource_closed_after_fork(resource, descriptor)
    _LIFECYCLE_GATE = allocate_lock()


def _finalize_resource(resource: _StateAuthorityLockResource) -> None:
    try:
        resource.cleanup_from_finalizer()
    except BaseException:
        pass


__all__ = [
    "StateAuthorityLock",
    "StateAuthorityLockError",
    "StateAuthorityLockErrorReason",
    "acquire_state_authority_lock",
]
