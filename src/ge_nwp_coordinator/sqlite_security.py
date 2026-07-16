"""Filesystem preparation for the local SQLite state database."""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import stat
from typing import Iterator

from ge_nwp_coordinator.sqlite_errors import SQLiteStateError, SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_location import (
    COORDINATOR_DATABASE_FILENAME,
    CoordinatorStateLocation,
)

_PRIVATE_DIR_MODE = 0o700
_PRIVATE_FILE_MODE = 0o600


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
    try:
        metadata = os.lstat(root)
    except OSError:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT) from None
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    _reject_unsafe_owner(metadata, SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_STATE_ROOT)
    return root.resolve(strict=True)


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
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
    _reject_unsafe_owner(metadata, SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)


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
