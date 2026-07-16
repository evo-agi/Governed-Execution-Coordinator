from __future__ import annotations

import os
from pathlib import Path
import stat

import pytest

from ge_nwp_coordinator.sqlite_errors import SQLiteStateError
from ge_nwp_coordinator.sqlite_location import (
    COORDINATOR_DATABASE_FILENAME,
    CoordinatorStateLocation,
    require_fixed_database_filename,
)
from ge_nwp_coordinator.sqlite_security import prepare_state_database


def _location(root: Path) -> CoordinatorStateLocation:
    return CoordinatorStateLocation.from_trusted_root(root)


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.lstat().st_mode)


def test_prepare_creates_private_root_and_database_file(tmp_path: Path) -> None:
    location = _location(tmp_path / "state")

    database_path = prepare_state_database(location)

    assert database_path == location.database_path
    assert location.state_root.is_dir()
    assert database_path.is_file()
    assert _mode(location.state_root) == 0o700
    assert _mode(database_path) == 0o600
    assert location.state_authority_lock_path.name == "coordinator-state.migration.lock"
    assert location.backup_directory_path.name == "backups"
    assert not location.state_authority_lock_path.exists()
    assert not location.backup_directory_path.exists()


def test_rejects_symlink_root_without_echoing_path(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    root = tmp_path / "state-link"
    root.symlink_to(target, target_is_directory=True)
    location = _location(root)

    with pytest.raises(SQLiteStateError) as exc_info:
        prepare_state_database(location)

    assert exc_info.value.error_class == "unsafe_state_root"
    assert str(root) not in str(exc_info.value)


def test_rejects_non_directory_root(tmp_path: Path) -> None:
    root = tmp_path / "state"
    root.write_text("not a directory", encoding="utf-8")

    with pytest.raises(SQLiteStateError, match="unsafe_state_root"):
        prepare_state_database(_location(root))


def test_rejects_unsafe_root_permissions(tmp_path: Path) -> None:
    root = tmp_path / "state"
    root.mkdir(mode=0o700)
    root.chmod(0o755)

    with pytest.raises(SQLiteStateError, match="unsafe_state_root"):
        prepare_state_database(_location(root))


def test_rejects_symlink_database_and_non_regular_database(tmp_path: Path) -> None:
    root = tmp_path / "state"
    root.mkdir(mode=0o700)
    target = tmp_path / "outside.sqlite"
    target.write_text("", encoding="utf-8")
    (root / COORDINATOR_DATABASE_FILENAME).symlink_to(target)

    with pytest.raises(SQLiteStateError, match="unsafe_database_file"):
        prepare_state_database(_location(root))

    (root / COORDINATOR_DATABASE_FILENAME).unlink()
    directory_db = root / COORDINATOR_DATABASE_FILENAME
    directory_db.mkdir(mode=0o700)
    with pytest.raises(SQLiteStateError, match="unsafe_database_file"):
        prepare_state_database(_location(root))


def test_rejects_fifo_database_when_supported(tmp_path: Path) -> None:
    if not hasattr(os, "mkfifo"):
        pytest.skip("fifo creation is not available on this platform")
    root = tmp_path / "state"
    root.mkdir(mode=0o700)
    os.mkfifo(root / COORDINATOR_DATABASE_FILENAME, 0o600)

    with pytest.raises(SQLiteStateError, match="unsafe_database_file"):
        prepare_state_database(_location(root))


def test_rejects_existing_database_with_group_or_other_permissions(tmp_path: Path) -> None:
    root = tmp_path / "state"
    root.mkdir(mode=0o700)
    database_path = root / COORDINATOR_DATABASE_FILENAME
    database_path.write_text("", encoding="utf-8")
    database_path.chmod(0o640)

    with pytest.raises(SQLiteStateError, match="unsafe_database_file"):
        prepare_state_database(_location(root))


def test_rejects_traversal_or_alternate_database_filename(tmp_path: Path) -> None:
    root = tmp_path / "state"
    location = CoordinatorStateLocation(
        state_root=root,
        database_path=root.parent / COORDINATOR_DATABASE_FILENAME,
        state_authority_lock_path=root / "coordinator-state.migration.lock",
        backup_directory_path=root / "backups",
    )

    with pytest.raises(SQLiteStateError, match="unsafe_database_file"):
        prepare_state_database(location)

    with pytest.raises(SQLiteStateError, match="unsafe_database_file"):
        require_fixed_database_filename("alternate.sqlite")


def test_rejects_repository_checkout_root(tmp_path: Path) -> None:
    root = tmp_path / "checkout" / "state"
    (tmp_path / "checkout" / ".git").mkdir(parents=True)

    with pytest.raises(SQLiteStateError, match="unsafe_state_root"):
        prepare_state_database(_location(root))


def test_default_location_can_be_redirected_for_tests_without_creating_real_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))

    location = CoordinatorStateLocation.default()

    assert str(location.state_root).startswith(str(home))
    assert not location.state_root.exists()
    prepare_state_database(location)
    assert location.state_root.exists()


def test_safe_errors_do_not_echo_paths(tmp_path: Path) -> None:
    root = tmp_path / "unsafe-root"
    root.mkdir(mode=0o755)

    with pytest.raises(SQLiteStateError) as exc_info:
        prepare_state_database(_location(root))

    assert str(root) not in str(exc_info.value)
    assert exc_info.value.error_class == "unsafe_state_root"
