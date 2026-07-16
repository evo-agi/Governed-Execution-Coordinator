from __future__ import annotations

import hashlib
from importlib import resources
from pathlib import Path
import sqlite3

import pytest

from ge_nwp_coordinator.sqlite_connection import open_sqlite_connection
from ge_nwp_coordinator.sqlite_errors import SQLiteStateError
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import (
    DatabaseClassification,
    MigrationDefinition,
    _apply_migration,
    _user_tables,
    initialize_database,
    inspect_database,
    load_migration_catalog,
    migrate_database,
    validate_database,
)


EXPECTED_TABLES = {
    "schema_migrations",
    "writer_ownership",
    "lease_identity_records",
    "authorization_decision_receipts",
    "admitted_backlogs",
    "dependency_decision_receipts",
    "global_stop_operator_decision_receipts",
    "work_items",
    "transition_events",
    "global_stop_current",
    "global_stop_events",
}


def _location(tmp_path: Path) -> CoordinatorStateLocation:
    return CoordinatorStateLocation.from_trusted_root(tmp_path / "state")


def _managed_history_database(
    tmp_path: Path,
    rows: list[tuple[str, int, str, int, int]],
) -> CoordinatorStateLocation:
    location = _location(tmp_path)
    location.state_root.mkdir(mode=0o700, parents=True)
    connection = sqlite3.connect(location.database_path)
    try:
        connection.execute(
            """
            CREATE TABLE schema_migrations (
                migration_id TEXT,
                sequence INTEGER,
                schema_digest TEXT,
                applied_at TEXT,
                min_app_schema INTEGER,
                max_app_schema INTEGER
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO schema_migrations
                (migration_id, sequence, schema_digest, applied_at, min_app_schema, max_app_schema)
            VALUES (?, ?, ?, '2026-07-16T00:00:00Z', ?, ?)
            """,
            rows,
        )
        connection.commit()
    finally:
        connection.close()
    location.database_path.chmod(0o600)
    return location


def _table_names(location: CoordinatorStateLocation) -> set[str]:
    connection = sqlite3.connect(location.database_path)
    try:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        return {row[0] for row in rows}
    finally:
        connection.close()


def _count(location: CoordinatorStateLocation, table_name: str) -> int:
    connection = sqlite3.connect(location.database_path)
    try:
        return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    finally:
        connection.close()


def test_empty_database_initializes_with_migration_0001(tmp_path: Path) -> None:
    location = _location(tmp_path)

    inspection = initialize_database(location)

    assert inspection.classification is DatabaseClassification.MANAGED
    assert inspection.current_sequence == 1
    assert inspection.latest_sequence == 1
    assert inspection.current_migration_id == "0001_initial"
    assert _table_names(location) == EXPECTED_TABLES


def test_authoritative_migration_row_matches_packaged_checksum(tmp_path: Path) -> None:
    location = _location(tmp_path)
    catalog = load_migration_catalog()

    initialize_database(location)

    connection = sqlite3.connect(location.database_path)
    try:
        row = connection.execute(
            "SELECT migration_id, sequence, schema_digest, min_app_schema, max_app_schema FROM schema_migrations"
        ).fetchone()
    finally:
        connection.close()
    migration = catalog.migrations[0]
    assert row == ("0001_initial", 1, migration.checksum, 1, 1)


def test_repeated_initialize_is_idempotent_validation(tmp_path: Path) -> None:
    location = _location(tmp_path)

    first = initialize_database(location)
    second = initialize_database(location)

    assert first == second
    assert _count(location, "schema_migrations") == 1


def test_managed_current_database_validates(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)

    inspection = validate_database(location)

    assert inspection.classification is DatabaseClassification.MANAGED
    assert inspection.current_sequence == inspection.latest_sequence == 1


def test_user_tables_without_schema_migrations_block(tmp_path: Path) -> None:
    location = _location(tmp_path)
    location.state_root.mkdir(mode=0o700, parents=True)
    connection = sqlite3.connect(location.database_path)
    try:
        connection.execute("CREATE TABLE caller_table (value TEXT)")
        connection.commit()
    finally:
        connection.close()
    location.database_path.chmod(0o600)

    with pytest.raises(SQLiteStateError, match="database_not_empty_unmanaged"):
        inspect_database(location)


def test_migration_checksum_mismatch_blocks(tmp_path: Path) -> None:
    location = _managed_history_database(tmp_path, [("0001_initial", 1, "0" * 64, 1, 1)])

    with pytest.raises(SQLiteStateError, match="migration_checksum_mismatch"):
        inspect_database(location)


def test_migration_sequence_gap_and_duplicate_sequence_block(tmp_path: Path) -> None:
    catalog = load_migration_catalog()
    valid = catalog.migrations[0]
    gap = _managed_history_database(tmp_path / "gap", [(valid.migration_id, 2, valid.checksum, 1, 1)])
    with pytest.raises(SQLiteStateError, match="migration_gap"):
        inspect_database(gap)

    duplicate = _managed_history_database(
        tmp_path / "duplicate",
        [
            (valid.migration_id, 1, valid.checksum, 1, 1),
            (valid.migration_id, 1, valid.checksum, 1, 1),
        ],
    )
    with pytest.raises(SQLiteStateError, match="migration_history_invalid"):
        inspect_database(duplicate)


def test_unknown_and_newer_schema_block(tmp_path: Path) -> None:
    catalog = load_migration_catalog()
    valid = catalog.migrations[0]
    unknown = _managed_history_database(tmp_path / "unknown", [("0001_other", 1, valid.checksum, 1, 1)])
    with pytest.raises(SQLiteStateError, match="migration_history_invalid"):
        inspect_database(unknown)

    too_new = _managed_history_database(
        tmp_path / "too-new",
        [
            (valid.migration_id, 1, valid.checksum, 1, 1),
            ("0002_future", 2, "f" * 64, 1, 2),
        ],
    )
    with pytest.raises(SQLiteStateError, match="database_schema_too_new"):
        inspect_database(too_new)


def test_application_compatibility_bounds_block(tmp_path: Path) -> None:
    catalog = load_migration_catalog()
    valid = catalog.migrations[0]
    too_new = _managed_history_database(tmp_path / "too-new-app", [(valid.migration_id, 1, valid.checksum, 2, 2)])
    with pytest.raises(SQLiteStateError, match="database_schema_too_new"):
        inspect_database(too_new)

    incompatible = _managed_history_database(
        tmp_path / "incompatible",
        [(valid.migration_id, 1, valid.checksum, 0, 0)],
    )
    with pytest.raises(SQLiteStateError, match="database_schema_incompatible"):
        inspect_database(incompatible)


def test_migration_history_missing_blocks(tmp_path: Path) -> None:
    location = _managed_history_database(tmp_path, [])

    with pytest.raises(SQLiteStateError, match="migration_history_missing"):
        inspect_database(location)


def test_migrate_refuses_empty_database_instead_of_implicit_initialization(tmp_path: Path) -> None:
    with pytest.raises(SQLiteStateError, match="migration_history_missing"):
        migrate_database(_location(tmp_path))


def test_failing_migration_rolls_back_schema_and_history(tmp_path: Path) -> None:
    location = _location(tmp_path)
    bad = MigrationDefinition(
        migration_id="0001_initial",
        sequence=1,
        resource_name="bad.sql",
        sql_bytes=b"CREATE TABLE schema_migrations (migration_id TEXT);\nCREATE TABLE stray (value INTEGER);\n",
        checksum="0" * 64,
        min_app_schema=1,
        max_app_schema=1,
        destructive=False,
        description="bad migration for rollback test",
    )

    connection = open_sqlite_connection(location)
    try:
        with pytest.raises(SQLiteStateError, match="schema_verification_failed"):
            _apply_migration(connection, bad)
        assert _user_tables(connection) == set()
    finally:
        connection.close()


def test_initial_migration_does_not_seed_writer_events_work_or_authorization(tmp_path: Path) -> None:
    location = _location(tmp_path)

    initialize_database(location)

    for table_name in (
        "writer_ownership",
        "lease_identity_records",
        "authorization_decision_receipts",
        "admitted_backlogs",
        "dependency_decision_receipts",
        "global_stop_operator_decision_receipts",
        "work_items",
        "transition_events",
        "global_stop_events",
    ):
        assert _count(location, table_name) == 0


def test_global_stop_initialization_is_canonical_clear_state(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    connection = sqlite3.connect(location.database_path)
    try:
        row = connection.execute(
            """
            SELECT singleton_id, schema_id, version, active, stop_id, reason_class,
                   issuer_ref, issued_at, operator_decision_ref
            FROM global_stop_current
            """
        ).fetchone()
    finally:
        connection.close()

    assert row == (1, "governed-execution.nwp-global-stop.v1", 0, 0, None, None, None, None, None)


def test_no_report_or_private_payload_tables_are_created(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)

    serialized_tables = " ".join(sorted(_table_names(location))).lower()
    for fragment in ("report", "prompt", "credential", "endpoint", "path", "worker", "bridge"):
        assert fragment not in serialized_tables


def test_packaged_migration_resource_and_checksum_are_exact() -> None:
    catalog = load_migration_catalog()
    migration = catalog.migrations[0]
    resource = resources.files("ge_nwp_coordinator.sqlite_migrations").joinpath(migration.resource_name)
    raw = resource.read_bytes()

    assert migration.sql_bytes == raw
    assert migration.checksum == hashlib.sha256(raw).hexdigest()
    assert "PRAGMA" not in migration.sql_text
    assert migration.destructive is False


def test_arbitrary_migration_path_is_not_a_public_operation() -> None:
    public_names = {
        "inspect_database",
        "initialize_database",
        "migrate_database",
        "validate_database",
        "load_migration_catalog",
    }
    import ge_nwp_coordinator.sqlite_migration as module

    for name in public_names:
        function = getattr(module, name)
        assert "path" not in function.__code__.co_varnames
        assert "sql" not in function.__code__.co_varnames
