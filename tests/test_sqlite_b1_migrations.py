from __future__ import annotations

import hashlib
from importlib import resources
from pathlib import Path
import sqlite3
import stat

import pytest

from ge_nwp_coordinator.sqlite_connection import _open_sqlite_connection
from ge_nwp_coordinator.sqlite_errors import SQLiteStateError
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import (
    DatabaseClassification,
    MigrationDefinition,
    _apply_migration,
    _migration_statements,
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


def _table_names(location: CoordinatorStateLocation) -> set[str]:
    with sqlite3.connect(location.database_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    return {row[0] for row in rows}


def _schema_objects(location: CoordinatorStateLocation) -> set[tuple[str, str]]:
    with sqlite3.connect(location.database_path) as connection:
        rows = connection.execute(
            """
            SELECT type, name
            FROM sqlite_schema
            WHERE type IN ('table', 'index', 'view', 'trigger') AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()
    return {(row[0], row[1]) for row in rows}


def _count(location: CoordinatorStateLocation, table_name: str) -> int:
    with sqlite3.connect(location.database_path) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


def _file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mode(path: Path) -> int | None:
    if not path.exists():
        return None
    return stat.S_IMODE(path.lstat().st_mode)


def _header_versions(path: Path) -> tuple[int, int] | None:
    if not path.exists() or path.stat().st_size < 20:
        return None
    header = path.read_bytes()[:20]
    if not header.startswith(b"SQLite format 3\x00"):
        return None
    return (header[18], header[19])


def _insert_history_rows(
    connection: sqlite3.Connection,
    rows: list[tuple[str, int, str, str, int, int]],
) -> None:
    connection.executemany(
        """
        INSERT INTO schema_migrations
            (migration_id, sequence, schema_digest, applied_at, min_app_schema, max_app_schema)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def _catalog_row(
    *,
    migration_id: str | None = None,
    sequence: int = 1,
    checksum: str | None = None,
    applied_at: str = "2026-07-16T00:00:00Z",
    min_app_schema: int = 1,
    max_app_schema: int = 1,
) -> tuple[str, int, str, str, int, int]:
    migration = load_migration_catalog().migrations[0]
    return (
        migration_id or migration.migration_id,
        sequence,
        checksum or migration.checksum,
        applied_at,
        min_app_schema,
        max_app_schema,
    )


def _database_from_migration(
    tmp_path: Path,
    *,
    transform=None,
    rows: list[tuple[str, int, str, str, int, int]] | None = None,
) -> CoordinatorStateLocation:
    location = _location(tmp_path)
    migration = load_migration_catalog().migrations[0]
    connection = _open_sqlite_connection(location)
    try:
        connection.execute("BEGIN IMMEDIATE")
        for statement in _migration_statements(migration.sql_text):
            transformed = transform(statement) if transform is not None else statement
            if transformed is not None:
                connection.execute(transformed)
        _insert_history_rows(connection, rows if rows is not None else [_catalog_row()])
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()
    return location


def _minimal_history_database(
    tmp_path: Path,
    rows: list[tuple[str, int, str, str, int, int]],
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
        _insert_history_rows(connection, rows)
        connection.commit()
    finally:
        connection.close()
    location.database_path.chmod(0o600)
    return location


def _direct_execute(location: CoordinatorStateLocation, *statements: str) -> None:
    with sqlite3.connect(location.database_path) as connection:
        for statement in statements:
            connection.execute(statement)
        connection.commit()


def _set_wal(location: CoordinatorStateLocation) -> None:
    with sqlite3.connect(location.database_path) as connection:
        connection.execute("PRAGMA journal_mode=WAL").fetchone()
        connection.execute("CREATE TABLE IF NOT EXISTS journal_probe (value INTEGER)")
        connection.execute("DROP TABLE journal_probe")
        connection.commit()
    location.database_path.chmod(0o600)


def _assert_unknown(inspection, reason: str | None = None) -> None:
    assert inspection.classification is DatabaseClassification.UNKNOWN
    if reason is not None:
        assert inspection.reason == reason


def test_inspect_and_validate_missing_database_are_observational(tmp_path: Path) -> None:
    location = _location(tmp_path)

    inspected = inspect_database(location)
    validated = validate_database(location)

    assert inspected.classification is DatabaseClassification.ABSENT
    assert validated.classification is DatabaseClassification.ABSENT
    assert not location.state_root.exists()
    assert not location.database_path.exists()


def test_migrate_missing_database_refuses_without_creating_artifacts(tmp_path: Path) -> None:
    location = _location(tmp_path)

    with pytest.raises(SQLiteStateError, match="migration_history_missing"):
        migrate_database(location)

    assert not location.state_root.exists()
    assert not location.database_path.exists()


def test_existing_empty_sqlite_database_classifies_empty_without_mutation(tmp_path: Path) -> None:
    location = _location(tmp_path)
    location.state_root.mkdir(mode=0o700, parents=True)
    with sqlite3.connect(location.database_path):
        pass
    location.database_path.chmod(0o600)
    before = (_file_digest(location.database_path), location.database_path.stat().st_size)

    inspection = inspect_database(location)

    assert inspection.classification is DatabaseClassification.EMPTY
    assert (_file_digest(location.database_path), location.database_path.stat().st_size) == before


def test_view_only_database_is_unknown_not_empty(tmp_path: Path) -> None:
    location = _location(tmp_path)
    location.state_root.mkdir(mode=0o700, parents=True)
    _direct_execute(location, "CREATE VIEW caller_view AS SELECT 1 AS value")
    location.database_path.chmod(0o600)

    _assert_unknown(inspect_database(location), "database_not_empty_unmanaged")
    assert ("view", "caller_view") in _schema_objects(location)


def test_unknown_wal_database_is_not_rewritten_by_inspection(tmp_path: Path) -> None:
    location = _location(tmp_path)
    location.state_root.mkdir(mode=0o700, parents=True)
    _direct_execute(location, "CREATE TABLE caller_table (value TEXT)")
    _set_wal(location)
    before = (_file_digest(location.database_path), _header_versions(location.database_path))

    _assert_unknown(inspect_database(location), "sqlite_posture_unavailable")

    assert (_file_digest(location.database_path), _header_versions(location.database_path)) == before


def test_managed_wal_database_is_not_rewritten_by_inspection(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    _set_wal(location)
    before = (_file_digest(location.database_path), _header_versions(location.database_path))

    _assert_unknown(validate_database(location), "sqlite_posture_unavailable")

    assert (_file_digest(location.database_path), _header_versions(location.database_path)) == before


def test_initialize_database_installs_migration_0001(tmp_path: Path) -> None:
    location = _location(tmp_path)

    inspection = initialize_database(location)

    assert inspection.classification is DatabaseClassification.MANAGED
    assert inspection.current_sequence == 1
    assert inspection.latest_sequence == 1
    assert inspection.current_migration_id == "0001_initial"
    assert _table_names(location) == EXPECTED_TABLES
    assert _mode(location.state_root) == 0o700
    assert _mode(location.database_path) == 0o600


def test_authoritative_migration_row_matches_packaged_catalog(tmp_path: Path) -> None:
    location = _location(tmp_path)
    catalog = load_migration_catalog()

    initialize_database(location)

    with sqlite3.connect(location.database_path) as connection:
        row = connection.execute(
            "SELECT migration_id, sequence, schema_digest, min_app_schema, max_app_schema FROM schema_migrations"
        ).fetchone()
    migration = catalog.migrations[0]
    assert row == ("0001_initial", 1, migration.checksum, 1, 1)


def test_repeated_initialize_is_idempotent_for_valid_current_database(tmp_path: Path) -> None:
    location = _location(tmp_path)

    first = initialize_database(location)
    second = initialize_database(location)

    assert first == second
    assert _count(location, "schema_migrations") == 1


def test_managed_current_database_validates_observationally(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    before = _file_digest(location.database_path)

    inspection = validate_database(location)

    assert inspection.classification is DatabaseClassification.MANAGED
    assert inspection.current_sequence == inspection.latest_sequence == 1
    assert _file_digest(location.database_path) == before


@pytest.mark.parametrize(
    ("rows", "reason"),
    [
        ([ _catalog_row(checksum="0" * 64) ], "migration_checksum_mismatch"),
        ([ _catalog_row(sequence=2) ], "migration_gap"),
        ([ _catalog_row(migration_id="0001_other") ], "migration_history_invalid"),
        ([ _catalog_row(migration_id="0002_future", sequence=2, checksum="f" * 64, max_app_schema=2) ], "migration_gap"),
        ([ _catalog_row(min_app_schema=2, max_app_schema=2) ], "database_schema_too_new"),
        ([ _catalog_row(min_app_schema=0, max_app_schema=0) ], "database_schema_incompatible"),
        ([ _catalog_row(min_app_schema=0, max_app_schema=1) ], "migration_history_invalid"),
        ([ _catalog_row(min_app_schema=1, max_app_schema=2) ], "migration_history_invalid"),
        ([ _catalog_row(applied_at="not-a-real-timestamp") ], "migration_history_invalid"),
    ],
)
def test_migration_history_catalog_equality_blocks(tmp_path: Path, rows, reason: str) -> None:
    location = _database_from_migration(tmp_path, rows=rows)

    _assert_unknown(inspect_database(location), reason)


def test_migration_history_missing_duplicate_and_unknown_rows_block(tmp_path: Path) -> None:
    missing = _database_from_migration(tmp_path / "missing", rows=[])
    _assert_unknown(inspect_database(missing), "migration_history_missing")

    duplicate = _minimal_history_database(tmp_path / "duplicate", [_catalog_row(), _catalog_row()])
    _assert_unknown(inspect_database(duplicate), "migration_history_invalid")

    unknown = _minimal_history_database(tmp_path / "unknown", [_catalog_row(), _catalog_row(migration_id="0002_future", sequence=2, checksum="f" * 64)])
    _assert_unknown(inspect_database(unknown), "database_schema_too_new")


def _remove_writer_singleton_check(statement: str) -> str:
    if statement.startswith("CREATE TABLE writer_ownership"):
        return statement.replace("singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1)", "singleton_id INTEGER PRIMARY KEY")
    return statement


def _alter_writer_column_type(statement: str) -> str:
    if statement.startswith("CREATE TABLE writer_ownership"):
        return statement.replace("writer_ref TEXT NOT NULL CHECK", "writer_ref BLOB CHECK")
    return statement


def _alter_writer_nullability(statement: str) -> str:
    if statement.startswith("CREATE TABLE writer_ownership"):
        return statement.replace("acquired_at TEXT NOT NULL CHECK", "acquired_at TEXT CHECK")
    return statement


def _replace_append_only_trigger_body(statement: str) -> str:
    if statement.startswith("CREATE TRIGGER transition_events_no_update"):
        return "CREATE TRIGGER transition_events_no_update BEFORE UPDATE ON transition_events BEGIN SELECT 1; END"
    return statement


def _remove_work_items_foreign_key(statement: str) -> str:
    if statement.startswith("CREATE TABLE work_items"):
        return statement.replace("backlog_id TEXT NOT NULL REFERENCES admitted_backlogs(backlog_id)", "backlog_id TEXT NOT NULL")
    return statement


def _extra_schema_migrations_column(statement: str) -> str:
    if "CREATE TABLE schema_migrations" in statement:
        return statement.replace(
            "max_app_schema INTEGER NOT NULL CHECK (max_app_schema >= min_app_schema)",
            "max_app_schema INTEGER NOT NULL CHECK (max_app_schema >= min_app_schema), extra_history_note TEXT",
        )
    return statement


def _remove_writer_column(statement: str) -> str:
    if statement.startswith("CREATE TABLE writer_ownership"):
        return statement.replace(",\n    acquired_at TEXT NOT NULL CHECK (length(acquired_at) BETWEEN 20 AND 64)", "")
    return statement


def _remove_required_unique_constraint(statement: str) -> str:
    if "CREATE TABLE schema_migrations" in statement:
        return statement.replace("sequence INTEGER NOT NULL UNIQUE CHECK", "sequence INTEGER NOT NULL CHECK")
    return statement


@pytest.mark.parametrize(
    "transform",
    [
        _remove_writer_singleton_check,
        _alter_writer_column_type,
        _alter_writer_nullability,
        _replace_append_only_trigger_body,
        _remove_work_items_foreign_key,
        _extra_schema_migrations_column,
        _remove_writer_column,
        _remove_required_unique_constraint,
    ],
)
def test_schema_manifest_rejects_drifted_packaged_schema(tmp_path: Path, transform) -> None:
    location = _database_from_migration(tmp_path, transform=transform)

    _assert_unknown(validate_database(location), "schema_fingerprint_mismatch")


@pytest.mark.parametrize(
    "statement",
    [
        "CREATE VIEW caller_view AS SELECT 1 AS value",
        "CREATE INDEX caller_index ON work_items (lease_id)",
        "CREATE TABLE caller_table (value INTEGER)",
        "CREATE TRIGGER caller_trigger BEFORE INSERT ON work_items BEGIN SELECT 1; END",
        "DROP TRIGGER transition_events_no_delete",
    ],
)
def test_schema_manifest_rejects_unexpected_or_missing_objects(tmp_path: Path, statement: str) -> None:
    location = _location(tmp_path)
    initialize_database(location)

    _direct_execute(location, statement)

    _assert_unknown(validate_database(location), "schema_fingerprint_mismatch")


def test_schema_drift_with_correct_history_checksum_is_not_accepted(tmp_path: Path) -> None:
    location = _database_from_migration(tmp_path, transform=_remove_work_items_foreign_key)

    inspection = validate_database(location)

    _assert_unknown(inspection, "schema_fingerprint_mismatch")


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

    connection = _open_sqlite_connection(location)
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
    with sqlite3.connect(location.database_path) as connection:
        row = connection.execute(
            """
            SELECT singleton_id, schema_id, version, active, stop_id, reason_class,
                   issuer_ref, issued_at, operator_decision_ref, updated_at
            FROM global_stop_current
            """
        ).fetchone()

    assert row == (
        1,
        "governed-execution.nwp-global-stop.v1",
        0,
        0,
        None,
        None,
        None,
        None,
        None,
        "1970-01-01T00:00:00Z",
    )


def test_global_stop_current_singleton_is_required_for_managed_validation(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)

    _direct_execute(location, "DELETE FROM global_stop_current")

    _assert_unknown(validate_database(location), "schema_verification_failed")


def test_malformed_global_stop_shape_is_rejected(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)

    _direct_execute(
        location,
        "PRAGMA ignore_check_constraints = ON",
        "UPDATE global_stop_current SET active = 1 WHERE singleton_id = 1",
        "PRAGMA ignore_check_constraints = OFF",
    )

    _assert_unknown(validate_database(location), "schema_verification_failed")


def test_future_nonzero_clear_global_stop_shape_is_valid(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)

    _direct_execute(location, "UPDATE global_stop_current SET version = 1, updated_at = '2026-07-16T00:00:00Z' WHERE singleton_id = 1")

    assert validate_database(location).classification is DatabaseClassification.MANAGED


def test_future_active_global_stop_shape_is_valid_when_receipt_exists(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    digest = "a" * 64
    _direct_execute(
        location,
        """
        INSERT INTO global_stop_operator_decision_receipts
            (decision_ref, authorized, reason, schema_id, canonical_json, canonical_digest, created_at)
        VALUES
            ('operator-decision-1', 1, 'accepted',
             'governed-execution.nwp-global-stop-operator-decision.v1', '{}',
             'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
             '2026-07-16T00:00:00Z')
        """,
        """
        UPDATE global_stop_current
        SET version = 1, active = 1, stop_id = 'stop-1', reason_class = 'operator_stop',
            issuer_ref = 'operator-policy', issued_at = '2026-07-16T00:00:00Z',
            operator_decision_ref = 'operator-decision-1', updated_at = '2026-07-16T00:00:00Z'
        WHERE singleton_id = 1
        """,
    )
    assert digest

    assert validate_database(location).classification is DatabaseClassification.MANAGED


def test_writer_ownership_cardinality_and_shape_are_checked(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    _direct_execute(
        location,
        """
        INSERT INTO writer_ownership
            (singleton_id, writer_ref, generation, issued_ref, issuance_nonce_digest, acquired_at)
        VALUES
            (1, 'writer-main', 1, 'issued-1',
             'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
             '2026-07-16T00:00:00Z')
        """,
    )

    assert validate_database(location).classification is DatabaseClassification.MANAGED


def test_writer_ownership_generation_semantics_are_checked_above_schema(tmp_path: Path) -> None:
    for generation in (0, -1, "9223372036854775808"):
        location = _location(tmp_path / f"generation-{generation}")
        initialize_database(location)
        _direct_execute(
            location,
            "PRAGMA ignore_check_constraints = ON",
            f"""
            INSERT INTO writer_ownership
                (singleton_id, writer_ref, generation, issued_ref, issuance_nonce_digest, acquired_at)
            VALUES
                (1, 'writer-main', {generation!r}, 'issued-1',
                 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
                 '2026-07-16T00:00:00Z')
            """,
        )

        _assert_unknown(validate_database(location), "schema_verification_failed")


def test_no_report_or_private_payload_tables_are_created(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)

    serialized_tables = " ".join(sorted(_table_names(location))).lower()
    for fragment in ("report", "prompt", "credential", "endpoint", "path", "worker", "bridge"):
        assert fragment not in serialized_tables


def test_safe_results_and_errors_do_not_expose_paths_sql_or_sqlite_text(tmp_path: Path) -> None:
    malformed = _location(tmp_path / "malformed")
    malformed.state_root.mkdir(mode=0o700, parents=True)
    malformed.database_path.write_bytes(b"not-a-sqlite-db")
    malformed.database_path.chmod(0o600)

    inspection = inspect_database(malformed)
    _assert_unknown(inspection, "sqlite_posture_unavailable")
    assert str(tmp_path) not in repr(inspection)
    assert "not-a-sqlite-db" not in repr(inspection)

    inaccessible = _location(tmp_path / "inaccessible")
    inaccessible.state_root.mkdir(mode=0o700, parents=True)
    inaccessible.database_path.write_bytes(b"")
    inaccessible.database_path.chmod(0o000)
    try:
        with pytest.raises(SQLiteStateError) as exc_info:
            initialize_database(inaccessible)
    finally:
        inaccessible.database_path.chmod(0o600)
    rendered = str(exc_info.value) + repr(exc_info.value)
    assert str(tmp_path) not in rendered
    assert "unable to open" not in rendered
    assert "CREATE TABLE" not in rendered


def test_packaged_migration_resource_and_checksum_are_exact() -> None:
    catalog = load_migration_catalog()
    migration = catalog.migrations[0]
    resource = resources.files("ge_nwp_coordinator.sqlite_migrations").joinpath(migration.resource_name)
    raw = resource.read_bytes()

    assert migration.sql_bytes == raw
    assert migration.checksum == hashlib.sha256(raw).hexdigest()
    assert migration.checksum == "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"
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
