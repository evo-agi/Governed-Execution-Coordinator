from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

import pytest

from ge_nwp_coordinator.sqlite_connection import (
    DEFAULT_BUSY_TIMEOUT_MS,
    apply_connection_posture,
    _open_sqlite_connection,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteStateError
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import initialize_database


def _location(tmp_path: Path) -> CoordinatorStateLocation:
    return CoordinatorStateLocation.from_trusted_root(tmp_path / "state")


def test_connection_posture_is_applied_and_verified(tmp_path: Path) -> None:
    with closing(_open_sqlite_connection(_location(tmp_path))) as connection, connection:
        posture = apply_connection_posture(connection)

        assert posture.foreign_keys is True
        assert posture.journal_mode == "delete"
        assert posture.synchronous == "full"
        assert posture.locking_mode == "normal"
        assert posture.busy_timeout_ms == DEFAULT_BUSY_TIMEOUT_MS
        assert posture.extension_loading_disabled is True
        assert posture.explicit_transaction_control is True
        if posture.trusted_schema_supported:
            assert posture.trusted_schema is False


def test_foreign_keys_are_enforced(tmp_path: Path) -> None:
    with closing(_open_sqlite_connection(_location(tmp_path))) as connection, connection:
        connection.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE child (parent_id INTEGER REFERENCES parent(id))")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO child (parent_id) VALUES (1)")


def test_extension_loading_remains_disabled(tmp_path: Path) -> None:
    with closing(_open_sqlite_connection(_location(tmp_path))) as connection, connection:
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("SELECT load_extension('not-a-real-extension')")


def test_bounded_busy_timeout_is_required(tmp_path: Path) -> None:
    with pytest.raises(SQLiteStateError, match="sqlite_posture_unavailable"):
        _open_sqlite_connection(_location(tmp_path), busy_timeout_ms=0)

    with pytest.raises(SQLiteStateError, match="sqlite_posture_unavailable"):
        _open_sqlite_connection(_location(tmp_path), busy_timeout_ms=30001)


def test_rollback_journal_mode_leaves_no_wal_shm_or_journal_after_commit(tmp_path: Path) -> None:
    location = _location(tmp_path)

    initialize_database(location)

    assert location.database_path.exists()
    assert not location.database_path.with_name(location.database_path.name + "-wal").exists()
    assert not location.database_path.with_name(location.database_path.name + "-shm").exists()
    assert not location.database_path.with_name(location.database_path.name + "-journal").exists()
