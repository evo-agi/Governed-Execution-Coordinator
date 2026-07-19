"""Filesystem preparation for the local SQLite state database."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import stat
from typing import Iterator

from ge_nwp_coordinator.sqlite_errors import SQLiteStateError, SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_location import (
    COORDINATOR_DATABASE_FILENAME,
    COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME,
    CoordinatorStateLocation,
)

_PRIVATE_DIR_MODE = 0o700
_PRIVATE_FILE_MODE = 0o600


class _StateDatabaseAuthorityBindingMismatch(SQLiteStateError):
    """Private marker for structural filesystem-authority drift."""


class _StateDatabaseAuthorityBindingUnavailable(SQLiteStateError):
    """Private marker for operational filesystem-authority checks."""


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class _FilesystemObjectIdentity:
    """Hidden `(st_dev, st_ino)` identity for one filesystem object."""

    _device: int
    _inode: int

    def __post_init__(self) -> None:
        if (
            type(self._device) is not int
            or type(self._inode) is not int
            or self._device < 0
            or self._inode < 0
        ):
            raise ValueError("invalid filesystem identity")

    def __repr__(self) -> str:
        return "<_FilesystemObjectIdentity>"

    __hash__ = None  # type: ignore[assignment]

    def __reduce__(self) -> object:
        raise TypeError("invalid filesystem identity")

    def _matches(self, metadata: os.stat_result) -> bool:
        return self._device == metadata.st_dev and self._inode == metadata.st_ino

    def _same_identity_as(self, other: "_FilesystemObjectIdentity") -> bool:
        return (
            type(other) is _FilesystemObjectIdentity
            and self._device == other._device
            and self._inode == other._inode
        )

    def _registry_key(self) -> tuple[int, int]:
        return (self._device, self._inode)


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class _StateDatabaseAuthorityBinding:
    """Hidden root/lock/database identity binding for one state location."""

    _location: CoordinatorStateLocation
    _state_root_identity: _FilesystemObjectIdentity
    _authority_lock_file_identity: _FilesystemObjectIdentity
    _database_file_identity: _FilesystemObjectIdentity

    def __post_init__(self) -> None:
        if type(self._location) is not CoordinatorStateLocation:
            raise ValueError("invalid state database binding")
        for identity in (
            self._state_root_identity,
            self._authority_lock_file_identity,
            self._database_file_identity,
        ):
            if type(identity) is not _FilesystemObjectIdentity:
                raise ValueError("invalid state database binding")

    def __repr__(self) -> str:
        return "<_StateDatabaseAuthorityBinding>"

    __hash__ = None  # type: ignore[assignment]

    def __reduce__(self) -> object:
        raise TypeError("invalid state database binding")

    def _same_authority_as(self, other: "_StateDatabaseAuthorityBinding") -> bool:
        return (
            type(other) is _StateDatabaseAuthorityBinding
            and self._location is other._location
            and self._state_root_identity._same_identity_as(other._state_root_identity)
            and self._authority_lock_file_identity._same_identity_as(other._authority_lock_file_identity)
            and self._database_file_identity._same_identity_as(other._database_file_identity)
        )

    def _location_for_private_open(self) -> CoordinatorStateLocation:
        return self._location


def prepare_state_database(location: CoordinatorStateLocation) -> Path:
    """Create and validate the state root and fixed database file."""

    if not isinstance(location, CoordinatorStateLocation):
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    _reject_network_like_root(location.state_root)
    _assert_fixed_database_path(location)
    _reject_repository_checkout(location.state_root)
    if location.state_root.is_symlink():
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    with _restrictive_umask():
        try:
            location.state_root.mkdir(mode=_PRIVATE_DIR_MODE, parents=True, exist_ok=True)
        except OSError:
            raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT) from None
    root = _validate_state_root(location.state_root)
    database_path = _confined_database_path(root, location.database_path)
    _prepare_database_file(database_path)
    return database_path


def existing_state_database_path(location: CoordinatorStateLocation) -> Path | None:
    """Validate an existing fixed database path without creating anything."""

    if not isinstance(location, CoordinatorStateLocation):
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    _reject_network_like_root(location.state_root)
    _assert_fixed_database_path(location)
    _reject_repository_checkout(location.state_root)
    if location.state_root.is_symlink():
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    if not location.state_root.exists():
        return None
    root = _validate_state_root(location.state_root)
    database_path = _confined_database_path(root, location.database_path)
    try:
        metadata = os.lstat(database_path)
    except FileNotFoundError:
        return None
    except OSError:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE) from None
    _validate_database_metadata(metadata)
    return database_path.resolve(strict=True)


def _filesystem_identity_for_stat(metadata: os.stat_result) -> _FilesystemObjectIdentity:
    return _FilesystemObjectIdentity(
        _device=int(metadata.st_dev),
        _inode=int(metadata.st_ino),
    )


def _capture_state_database_authority_binding(
    location: CoordinatorStateLocation,
    *,
    state_root_identity: _FilesystemObjectIdentity,
    authority_lock_file_identity: _FilesystemObjectIdentity,
) -> _StateDatabaseAuthorityBinding:
    try:
        if type(location) is not CoordinatorStateLocation:
            raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
        if type(state_root_identity) is not _FilesystemObjectIdentity:
            raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
        if type(authority_lock_file_identity) is not _FilesystemObjectIdentity:
            raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)

        _assert_fixed_database_path(location)
        _assert_fixed_authority_lock_path(location)
        root, root_metadata = _validated_state_root_with_metadata(location.state_root)
        if not state_root_identity._matches(root_metadata):
            raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)

        lock_path = _confined_authority_lock_path(root, location.state_authority_lock_path)
        lock_metadata = _path_lstat_or_mismatch(lock_path, SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
        _validate_authority_lock_metadata(lock_metadata)
        if not authority_lock_file_identity._matches(lock_metadata):
            raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)

        database_path = _confined_database_path(root, location.database_path)
        database_metadata = _path_lstat_or_mismatch(database_path, SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
        _validate_database_metadata(database_metadata)
    except (_StateDatabaseAuthorityBindingMismatch, _StateDatabaseAuthorityBindingUnavailable):
        raise
    except SQLiteStateError as exc:
        raise _StateDatabaseAuthorityBindingMismatch(exc.error_class) from None

    return _StateDatabaseAuthorityBinding(
        _location=location,
        _state_root_identity=state_root_identity,
        _authority_lock_file_identity=authority_lock_file_identity,
        _database_file_identity=_filesystem_identity_for_stat(database_metadata),
    )


def _validate_state_database_authority_binding(binding: _StateDatabaseAuthorityBinding) -> None:
    if type(binding) is not _StateDatabaseAuthorityBinding:
        raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
    current = _capture_state_database_authority_binding(
        binding._location,
        state_root_identity=binding._state_root_identity,
        authority_lock_file_identity=binding._authority_lock_file_identity,
    )
    if not binding._same_authority_as(current):
        raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)


def _require_same_state_database_authority_binding(
    expected: _StateDatabaseAuthorityBinding,
    actual: _StateDatabaseAuthorityBinding,
) -> None:
    if type(expected) is not _StateDatabaseAuthorityBinding or type(actual) is not _StateDatabaseAuthorityBinding:
        raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
    if not expected._same_authority_as(actual):
        raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)


def _open_bound_root_descriptor(binding: _StateDatabaseAuthorityBinding) -> int:
    if type(binding) is not _StateDatabaseAuthorityBinding:
        raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(binding._location.state_root, flags)
        os.set_inheritable(descriptor, False)
        metadata = os.fstat(descriptor)
    except OSError:
        if "descriptor" in locals():
            _close_descriptor(descriptor)
        raise _StateDatabaseAuthorityBindingUnavailable(SQLiteStateErrorCode.UNSAFE_STATE_ROOT) from None
    try:
        _validate_state_root_metadata(metadata)
        if not binding._state_root_identity._matches(metadata):
            raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
        return descriptor
    except SQLiteStateError as exc:
        _close_descriptor(descriptor)
        raise _StateDatabaseAuthorityBindingMismatch(exc.error_class) from None
    except Exception:
        _close_descriptor(descriptor)
        raise


def _open_bound_database_descriptor(
    binding: _StateDatabaseAuthorityBinding,
    *,
    root_descriptor: int,
) -> int:
    if type(binding) is not _StateDatabaseAuthorityBinding:
        raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
    flags = os.O_RDONLY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(COORDINATOR_DATABASE_FILENAME, flags, dir_fd=root_descriptor)
        os.set_inheritable(descriptor, False)
        metadata = os.fstat(descriptor)
    except OSError:
        if "descriptor" in locals():
            _close_descriptor(descriptor)
        raise _StateDatabaseAuthorityBindingUnavailable(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE) from None
    try:
        _validate_database_metadata(metadata)
        if not binding._database_file_identity._matches(metadata):
            raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
        return descriptor
    except SQLiteStateError as exc:
        _close_descriptor(descriptor)
        raise _StateDatabaseAuthorityBindingMismatch(exc.error_class) from None
    except Exception:
        _close_descriptor(descriptor)
        raise


def _close_descriptor(descriptor: int) -> None:
    if descriptor < 0:
        return
    try:
        os.close(descriptor)
    except OSError:
        pass


def _assert_fixed_database_path(location: CoordinatorStateLocation) -> None:
    if location.database_path.name != COORDINATOR_DATABASE_FILENAME:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
    try:
        expected = location.state_root / COORDINATOR_DATABASE_FILENAME
        if location.database_path != expected:
            raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
    except TypeError:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE) from None


def _reject_network_like_root(root: Path) -> None:
    text = str(root)
    if text.startswith("//") or text.startswith("\\\\"):
        raise SQLiteStateError(SQLiteStateErrorCode.UNSUPPORTED_FILESYSTEM)


def _reject_repository_checkout(root: Path) -> None:
    probe = root.resolve(strict=False)
    for candidate in (probe, *probe.parents):
        if (candidate / ".git").exists():
            raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)


def _validate_state_root(root: Path) -> Path:
    resolved, _metadata = _validated_state_root_with_metadata(root)
    return resolved


def _validated_state_root_with_metadata(root: Path) -> tuple[Path, os.stat_result]:
    try:
        metadata = os.lstat(root)
    except OSError:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT) from None
    _validate_state_root_metadata(metadata)
    try:
        resolved = root.resolve(strict=True)
    except OSError:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT) from None
    return resolved, metadata


def _validate_state_root_metadata(metadata: os.stat_result) -> None:
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    _reject_unsafe_owner(metadata, SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)


def _confined_database_path(root: Path, database_path: Path) -> Path:
    if database_path.name != COORDINATOR_DATABASE_FILENAME:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
    try:
        parent = database_path.parent.resolve(strict=True)
    except OSError:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE) from None
    if parent != root:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
    resolved = database_path.resolve(strict=False)
    try:
        if os.path.commonpath((str(root), str(resolved))) != str(root):
            raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
    except ValueError:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE) from None
    return database_path


def _assert_fixed_authority_lock_path(location: CoordinatorStateLocation) -> None:
    if location.state_authority_lock_path.name != COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    try:
        expected = location.state_root / COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME
        if location.state_authority_lock_path != expected:
            raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    except TypeError:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT) from None


def _confined_authority_lock_path(root: Path, lock_path: Path) -> Path:
    if lock_path.name != COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME:
        raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    try:
        parent = lock_path.parent.resolve(strict=True)
    except OSError:
        raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_STATE_ROOT) from None
    if parent != root:
        raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    resolved = lock_path.resolve(strict=False)
    try:
        if os.path.commonpath((str(root), str(resolved))) != str(root):
            raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    except ValueError:
        raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_STATE_ROOT) from None
    return lock_path


def _prepare_database_file(database_path: Path) -> None:
    try:
        metadata = os.lstat(database_path)
    except FileNotFoundError:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        with _restrictive_umask():
            try:
                descriptor = os.open(database_path, flags, _PRIVATE_FILE_MODE)
            except OSError:
                raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE) from None
            else:
                os.close(descriptor)
        metadata = _database_lstat(database_path)
    except OSError:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE) from None
    _validate_database_metadata(metadata)


def _database_lstat(database_path: Path) -> os.stat_result:
    try:
        return os.lstat(database_path)
    except OSError:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE) from None


def _validate_database_metadata(metadata: os.stat_result) -> None:
    _validate_private_regular_file_metadata(metadata, SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)


def _validate_authority_lock_metadata(metadata: os.stat_result) -> None:
    _validate_private_regular_file_metadata(metadata, SQLiteStateErrorCode.UNSAFE_STATE_ROOT)


def _validate_private_regular_file_metadata(metadata: os.stat_result, error_class: SQLiteStateErrorCode) -> None:
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise SQLiteStateError(error_class)
    _reject_unsafe_owner(metadata, error_class)
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise SQLiteStateError(error_class)
    if getattr(metadata, "st_nlink", 1) != 1:
        raise SQLiteStateError(error_class)


def _path_lstat_or_mismatch(path: Path, error_class: SQLiteStateErrorCode) -> os.stat_result:
    try:
        return os.lstat(path)
    except FileNotFoundError:
        raise _StateDatabaseAuthorityBindingMismatch(error_class) from None
    except OSError:
        raise _StateDatabaseAuthorityBindingUnavailable(error_class) from None


def _reject_unsafe_owner(metadata: os.stat_result, error_class: SQLiteStateErrorCode) -> None:
    getuid = getattr(os, "getuid", None)
    if getuid is None:
        return
    if metadata.st_uid != getuid():
        raise SQLiteStateError(error_class)


@contextmanager
def _restrictive_umask() -> Iterator[None]:
    old_umask = os.umask(0o077)
    try:
        yield
    finally:
        os.umask(old_umask)
