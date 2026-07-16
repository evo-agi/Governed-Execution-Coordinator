"""Forward-only packaged SQLite migration runner for B1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
from importlib import resources
import sqlite3
from typing import Any, Iterable

from ge_nwp_coordinator.sqlite_connection import open_sqlite_connection
from ge_nwp_coordinator.sqlite_errors import SQLiteStateError, SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation

CURRENT_APPLICATION_SCHEMA = 1
MIGRATION_PACKAGE = "ge_nwp_coordinator.sqlite_migrations"

EXPECTED_TABLES = frozenset(
    {
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
)

EXPECTED_TRIGGERS = frozenset(
    {
        "schema_migrations_no_update",
        "schema_migrations_no_delete",
        "lease_identity_records_no_update",
        "lease_identity_records_no_delete",
        "authorization_decision_receipts_no_update",
        "authorization_decision_receipts_no_delete",
        "admitted_backlogs_no_update",
        "admitted_backlogs_no_delete",
        "dependency_decision_receipts_no_update",
        "dependency_decision_receipts_no_delete",
        "global_stop_operator_decision_receipts_no_update",
        "global_stop_operator_decision_receipts_no_delete",
        "transition_events_no_update",
        "transition_events_no_delete",
        "global_stop_events_no_update",
        "global_stop_events_no_delete",
    }
)

EMPTY_AFTER_BOOTSTRAP_TABLES = frozenset(
    {
        "writer_ownership",
        "lease_identity_records",
        "authorization_decision_receipts",
        "admitted_backlogs",
        "dependency_decision_receipts",
        "global_stop_operator_decision_receipts",
        "work_items",
        "transition_events",
        "global_stop_events",
    }
)


class DatabaseClassification(str, Enum):
    EMPTY = "empty"
    MANAGED = "managed"


@dataclass(frozen=True)
class MigrationDefinition:
    migration_id: str
    sequence: int
    resource_name: str
    sql_bytes: bytes
    checksum: str
    min_app_schema: int
    max_app_schema: int
    destructive: bool
    description: str

    @property
    def sql_text(self) -> str:
        return self.sql_bytes.decode("utf-8")


@dataclass(frozen=True)
class MigrationCatalog:
    migrations: tuple[MigrationDefinition, ...]

    def __post_init__(self) -> None:
        by_sequence: dict[int, MigrationDefinition] = {}
        by_id: set[str] = set()
        for migration in self.migrations:
            if migration.sequence in by_sequence or migration.migration_id in by_id:
                raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
            by_sequence[migration.sequence] = migration
            by_id.add(migration.migration_id)
        if tuple(sorted(by_sequence)) != tuple(range(1, len(self.migrations) + 1)):
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_GAP)

    @property
    def latest_sequence(self) -> int:
        return len(self.migrations)

    def by_sequence(self, sequence: int) -> MigrationDefinition | None:
        for migration in self.migrations:
            if migration.sequence == sequence:
                return migration
        return None


@dataclass(frozen=True)
class DatabaseInspection:
    classification: DatabaseClassification
    current_sequence: int
    latest_sequence: int
    current_migration_id: str | None


@dataclass(frozen=True)
class _MigrationHistoryRow:
    migration_id: str
    sequence: int
    schema_digest: str
    min_app_schema: int
    max_app_schema: int


def load_migration_catalog() -> MigrationCatalog:
    sql_bytes = resources.files(MIGRATION_PACKAGE).joinpath("0001_initial.sql").read_bytes()
    checksum = hashlib.sha256(sql_bytes).hexdigest()
    return MigrationCatalog(
        migrations=(
            MigrationDefinition(
                migration_id="0001_initial",
                sequence=1,
                resource_name="0001_initial.sql",
                sql_bytes=sql_bytes,
                checksum=checksum,
                min_app_schema=1,
                max_app_schema=1,
                destructive=False,
                description="Initial local SQLite Coordinator state schema",
            ),
        )
    )


def inspect_database(location: CoordinatorStateLocation) -> DatabaseInspection:
    catalog = load_migration_catalog()
    connection = open_sqlite_connection(location)
    try:
        return _inspect_open_database(connection, catalog)
    finally:
        connection.close()


def initialize_database(location: CoordinatorStateLocation) -> DatabaseInspection:
    catalog = load_migration_catalog()
    connection = open_sqlite_connection(location)
    try:
        classification = _classify_database(connection)
        if classification is DatabaseClassification.EMPTY:
            migration = _required_migration(catalog, 1)
            _apply_migration(connection, migration)
        inspection = _inspect_open_database(connection, catalog)
        if inspection.current_sequence != catalog.latest_sequence:
            raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE)
        return inspection
    finally:
        connection.close()


def migrate_database(location: CoordinatorStateLocation) -> DatabaseInspection:
    catalog = load_migration_catalog()
    connection = open_sqlite_connection(location)
    try:
        if _classify_database(connection) is DatabaseClassification.EMPTY:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_MISSING)
        inspection = _inspect_open_database(connection, catalog)
        while inspection.current_sequence < catalog.latest_sequence:
            migration = _required_migration(catalog, inspection.current_sequence + 1)
            _apply_migration(connection, migration)
            inspection = _inspect_open_database(connection, catalog)
        return inspection
    finally:
        connection.close()


def validate_database(location: CoordinatorStateLocation) -> DatabaseInspection:
    inspection = inspect_database(location)
    if inspection.classification is DatabaseClassification.EMPTY:
        return inspection
    if inspection.current_sequence != inspection.latest_sequence:
        raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE)
    return inspection


def _inspect_open_database(
    connection: sqlite3.Connection,
    catalog: MigrationCatalog,
) -> DatabaseInspection:
    classification = _classify_database(connection)
    if classification is DatabaseClassification.EMPTY:
        return DatabaseInspection(
            classification=classification,
            current_sequence=0,
            latest_sequence=catalog.latest_sequence,
            current_migration_id=None,
        )
    rows = _validate_migration_history(connection, catalog)
    current = rows[-1]
    if current.sequence == catalog.latest_sequence:
        _verify_schema_for_migration(connection, _required_migration(catalog, current.sequence))
    return DatabaseInspection(
        classification=classification,
        current_sequence=current.sequence,
        latest_sequence=catalog.latest_sequence,
        current_migration_id=current.migration_id,
    )


def _classify_database(connection: sqlite3.Connection) -> DatabaseClassification:
    tables = _user_tables(connection)
    if not tables:
        return DatabaseClassification.EMPTY
    if "schema_migrations" in tables:
        return DatabaseClassification.MANAGED
    raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_NOT_EMPTY_UNMANAGED)


def _user_tables(connection: sqlite3.Connection) -> set[str]:
    try:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()
    except sqlite3.DatabaseError:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID) from None
    return {str(row[0]) for row in rows}


def _validate_migration_history(
    connection: sqlite3.Connection,
    catalog: MigrationCatalog,
) -> tuple[_MigrationHistoryRow, ...]:
    try:
        rows = connection.execute(
            """
            SELECT migration_id, sequence, schema_digest, min_app_schema, max_app_schema
            FROM schema_migrations
            ORDER BY sequence
            """
        ).fetchall()
    except sqlite3.DatabaseError:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID) from None
    if not rows:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_MISSING)
    history = tuple(_history_row(row) for row in rows)
    seen_sequences: set[int] = set()
    for index, row in enumerate(history, start=1):
        if row.sequence in seen_sequences:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
        seen_sequences.add(row.sequence)
        if row.sequence != index:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_GAP)
        migration = catalog.by_sequence(row.sequence)
        if migration is None:
            raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW)
        if row.migration_id != migration.migration_id:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
        if row.schema_digest != migration.checksum:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_CHECKSUM_MISMATCH)
        if row.min_app_schema > CURRENT_APPLICATION_SCHEMA:
            raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW)
        if row.max_app_schema < CURRENT_APPLICATION_SCHEMA:
            raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE)
    return history


def _history_row(row: Iterable[Any]) -> _MigrationHistoryRow:
    values = tuple(row)
    if len(values) != 5:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    migration_id, sequence, schema_digest, min_app_schema, max_app_schema = values
    if not isinstance(migration_id, str) or not isinstance(schema_digest, str):
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    if not isinstance(sequence, int) or not isinstance(min_app_schema, int) or not isinstance(max_app_schema, int):
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    if sequence < 1 or min_app_schema < 0 or max_app_schema < min_app_schema:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    return _MigrationHistoryRow(
        migration_id=migration_id,
        sequence=sequence,
        schema_digest=schema_digest,
        min_app_schema=min_app_schema,
        max_app_schema=max_app_schema,
    )


def _apply_migration(connection: sqlite3.Connection, migration: MigrationDefinition) -> None:
    if migration.destructive:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    try:
        connection.execute("BEGIN IMMEDIATE")
        try:
            for statement in _migration_statements(migration.sql_text):
                connection.execute(statement)
            _verify_schema_for_migration(connection, migration, fresh_install=True)
            _insert_migration_row(connection, migration)
            connection.execute("COMMIT")
        except Exception:
            _rollback(connection)
            raise
    except SQLiteStateError:
        raise
    except sqlite3.DatabaseError:
        _rollback(connection)
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED) from None


def _migration_statements(sql_text: str) -> tuple[str, ...]:
    statements: list[str] = []
    pending: list[str] = []
    for line in sql_text.splitlines(keepends=True):
        pending.append(line)
        candidate = "".join(pending)
        if sqlite3.complete_statement(candidate):
            statement = candidate.strip()
            if statement:
                statements.append(statement)
            pending = []
    if "".join(pending).strip():
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    return tuple(statements)


def _verify_schema_for_migration(
    connection: sqlite3.Connection,
    migration: MigrationDefinition,
    *,
    fresh_install: bool = False,
) -> None:
    if migration.sequence != 1:
        return
    if _user_tables(connection) != EXPECTED_TABLES:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    if _triggers(connection) != EXPECTED_TRIGGERS:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    if fresh_install:
        _verify_global_stop_clear_seed(connection)
        _verify_empty_bootstrap_tables(connection)
    _verify_foreign_key_posture(connection)


def _triggers(connection: sqlite3.Connection) -> set[str]:
    try:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger'"
        ).fetchall()
    except sqlite3.DatabaseError:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
    return {str(row[0]) for row in rows}


def _verify_global_stop_clear_seed(connection: sqlite3.Connection) -> None:
    try:
        rows = connection.execute(
            """
            SELECT singleton_id, schema_id, version, active, stop_id, reason_class,
                   issuer_ref, issued_at, operator_decision_ref
            FROM global_stop_current
            """
        ).fetchall()
    except sqlite3.DatabaseError:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
    if rows != [(1, "governed-execution.nwp-global-stop.v1", 0, 0, None, None, None, None, None)]:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)


def _verify_empty_bootstrap_tables(connection: sqlite3.Connection) -> None:
    for table_name in EMPTY_AFTER_BOOTSTRAP_TABLES:
        try:
            count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        except sqlite3.DatabaseError:
            raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
        if count != 0:
            raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)


def _verify_foreign_key_posture(connection: sqlite3.Connection) -> None:
    try:
        row = connection.execute("PRAGMA foreign_keys").fetchone()
    except sqlite3.DatabaseError:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
    if row is None or int(row[0]) != 1:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)


def _insert_migration_row(connection: sqlite3.Connection, migration: MigrationDefinition) -> None:
    try:
        connection.execute(
            """
            INSERT INTO schema_migrations
                (migration_id, sequence, schema_digest, applied_at, min_app_schema, max_app_schema)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                migration.migration_id,
                migration.sequence,
                migration.checksum,
                _utc_now(),
                migration.min_app_schema,
                migration.max_app_schema,
            ),
        )
    except sqlite3.DatabaseError:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED) from None


def _required_migration(catalog: MigrationCatalog, sequence: int) -> MigrationDefinition:
    migration = catalog.by_sequence(sequence)
    if migration is None:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_GAP)
    return migration


def _rollback(connection: sqlite3.Connection) -> None:
    try:
        connection.execute("ROLLBACK")
    except sqlite3.DatabaseError:
        pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
