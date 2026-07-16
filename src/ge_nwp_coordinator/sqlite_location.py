"""Fixed local state-location policy for B1 SQLite administration."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys

from ge_nwp_coordinator.sqlite_errors import SQLiteStateError, SQLiteStateErrorCode

COORDINATOR_STATE_COMPONENT = "nwp-coordinator"
COORDINATOR_DATABASE_FILENAME = "coordinator-state.sqlite"
COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME = "coordinator-state.migration.lock"
COORDINATOR_BACKUP_DIRECTORY = "backups"


@dataclass(frozen=True)
class CoordinatorStateLocation:
    """Code-owned local paths for one Coordinator SQLite state root."""

    state_root: Path
    database_path: Path
    state_authority_lock_path: Path
    backup_directory_path: Path

    @classmethod
    def default(cls) -> "CoordinatorStateLocation":
        return cls.from_trusted_root(_default_state_root())

    @classmethod
    def from_trusted_root(cls, state_root: os.PathLike[str] | str) -> "CoordinatorStateLocation":
        root = Path(state_root).expanduser()
        return cls(
            state_root=root,
            database_path=_fixed_child(root, COORDINATOR_DATABASE_FILENAME, SQLiteStateErrorCode.UNSAFE_DATABASE_FILE),
            state_authority_lock_path=_fixed_child(
                root,
                COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME,
                SQLiteStateErrorCode.UNSAFE_STATE_ROOT,
            ),
            backup_directory_path=_fixed_child(root, COORDINATOR_BACKUP_DIRECTORY, SQLiteStateErrorCode.UNSAFE_STATE_ROOT),
        )


def require_fixed_database_filename(filename: str) -> str:
    if filename != COORDINATOR_DATABASE_FILENAME:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
    return filename


def _default_state_root() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "NWP Coordinator" / "state"
    if os.name == "nt":
        return home / "AppData" / "Local" / "NWP Coordinator" / "state"
    return home / ".local" / "state" / COORDINATOR_STATE_COMPONENT


def _fixed_child(root: Path, child_name: str, error_class: SQLiteStateErrorCode) -> Path:
    if Path(child_name).name != child_name or child_name in {"", ".", ".."}:
        raise SQLiteStateError(error_class)
    return root / child_name
