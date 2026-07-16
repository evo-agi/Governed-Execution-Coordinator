"""Forward-only packaged SQLite migration runner for B1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
from importlib import resources
import re
import sqlite3
from typing import Any, Iterable

from ge_nwp_coordinator.sqlite_connection import (
    apply_observational_connection_posture,
    open_existing_sqlite_connection,
    open_sqlite_connection,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteStateError, SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_security import existing_state_database_path

CURRENT_APPLICATION_SCHEMA = 1
MIGRATION_PACKAGE = "ge_nwp_coordinator.sqlite_migrations"
SQLITE_HEADER = b"SQLite format 3\x00"
ROLLBACK_JOURNAL_FILE_FORMAT_VERSION = 1
RFC3339_UTC_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

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
    ABSENT = "absent"
    EMPTY = "empty"
    MANAGED = "managed"
    UNKNOWN = "unknown"


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
    reason: str | None = None


@dataclass(frozen=True)
class _MigrationHistoryRow:
    migration_id: str
    sequence: int
    schema_digest: str
    applied_at: str
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
    """Observe the fixed database path without creating or mutating it."""

    catalog = load_migration_catalog()
    database_path = existing_state_database_path(location)
    if database_path is None:
        return _inspection(DatabaseClassification.ABSENT, catalog)
    file_state = _classify_existing_file_header(database_path)
    if file_state is not None:
        return _inspection(file_state[0], catalog, reason=file_state[1])
    try:
        connection = open_existing_sqlite_connection(location, read_only=True)
    except SQLiteStateError as exc:
        return _inspection(DatabaseClassification.UNKNOWN, catalog, reason=exc.error_class)
    try:
        try:
            return _inspect_open_database(connection, catalog)
        except SQLiteStateError as exc:
            return _inspection(DatabaseClassification.UNKNOWN, catalog, reason=exc.error_class)
    finally:
        connection.close()


def initialize_database(location: CoordinatorStateLocation) -> DatabaseInspection:
    """Explicitly create or initialize the local administrative database."""

    catalog = load_migration_catalog()
    preflight = inspect_database(location)
    if preflight.classification is DatabaseClassification.MANAGED:
        if preflight.current_sequence != catalog.latest_sequence:
            raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE)
        return preflight
    if preflight.classification is DatabaseClassification.UNKNOWN:
        _raise_inspection_failure(preflight)

    connection = open_sqlite_connection(location)
    try:
        classification = _classify_open_database(connection, catalog, verify_managed=False)
        if classification is DatabaseClassification.EMPTY:
            migration = _required_migration(catalog, 1)
            _apply_migration(connection, migration)
        elif classification is not DatabaseClassification.MANAGED:
            raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_NOT_EMPTY_UNMANAGED)
        inspection = _inspect_open_database(connection, catalog)
        if inspection.current_sequence != catalog.latest_sequence:
            raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE)
        return inspection
    finally:
        connection.close()


def migrate_database(location: CoordinatorStateLocation) -> DatabaseInspection:
    """Explicitly migrate an existing managed database through packaged migrations."""

    catalog = load_migration_catalog()
    preflight = inspect_database(location)
    if preflight.classification in {DatabaseClassification.ABSENT, DatabaseClassification.EMPTY}:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_MISSING)
    if preflight.classification is DatabaseClassification.UNKNOWN:
        _raise_inspection_failure(preflight)
    if preflight.current_sequence == catalog.latest_sequence:
        return preflight

    connection = open_existing_sqlite_connection(location, read_only=False)
    try:
        connection.execute("BEGIN IMMEDIATE")
        try:
            inspection = _inspect_open_database(connection, catalog)
            while inspection.current_sequence < catalog.latest_sequence:
                migration = _required_migration(catalog, inspection.current_sequence + 1)
                _apply_migration_in_transaction(connection, migration, fresh_install=False)
                inspection = _inspect_open_database(connection, catalog)
            connection.execute("COMMIT")
            return inspection
        except Exception:
            _rollback(connection)
            raise
    except SQLiteStateError:
        raise
    except sqlite3.Error:
        _rollback(connection)
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED) from None
    finally:
        connection.close()


def validate_database(location: CoordinatorStateLocation) -> DatabaseInspection:
    """Observationally validate an existing managed database when present."""

    inspection = inspect_database(location)
    if inspection.classification is DatabaseClassification.MANAGED and inspection.current_sequence != inspection.latest_sequence:
        raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE)
    return inspection


def _inspect_open_database(
    connection: sqlite3.Connection,
    catalog: MigrationCatalog,
) -> DatabaseInspection:
    classification = _classify_open_database(connection, catalog, verify_managed=True)
    if classification is DatabaseClassification.EMPTY:
        return _inspection(classification, catalog)
    rows = _validate_migration_history(connection, catalog)
    current = rows[-1]
    _verify_schema_for_migration(connection, _required_migration(catalog, current.sequence))
    _verify_managed_state_invariants(connection)
    return DatabaseInspection(
        classification=DatabaseClassification.MANAGED,
        current_sequence=current.sequence,
        latest_sequence=catalog.latest_sequence,
        current_migration_id=current.migration_id,
    )


def _inspection(
    classification: DatabaseClassification,
    catalog: MigrationCatalog,
    *,
    reason: str | None = None,
) -> DatabaseInspection:
    return DatabaseInspection(
        classification=classification,
        current_sequence=0,
        latest_sequence=catalog.latest_sequence,
        current_migration_id=None,
        reason=reason,
    )


def _raise_inspection_failure(inspection: DatabaseInspection) -> None:
    reason = inspection.reason or SQLiteStateErrorCode.DATABASE_NOT_EMPTY_UNMANAGED.value
    try:
        raise SQLiteStateError(reason)
    except ValueError:
        raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_NOT_EMPTY_UNMANAGED) from None


def _classify_existing_file_header(database_path: Any) -> tuple[DatabaseClassification, str | None] | None:
    try:
        size = database_path.stat().st_size
        with database_path.open("rb") as handle:
            header = handle.read(100)
    except OSError:
        raise SQLiteStateError(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE) from None
    if size == 0:
        return (DatabaseClassification.EMPTY, None)
    if len(header) < len(SQLITE_HEADER) or not header.startswith(SQLITE_HEADER):
        return (DatabaseClassification.UNKNOWN, SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE.value)
    if len(header) >= 20 and (
        header[18] != ROLLBACK_JOURNAL_FILE_FORMAT_VERSION
        or header[19] != ROLLBACK_JOURNAL_FILE_FORMAT_VERSION
    ):
        return (DatabaseClassification.UNKNOWN, SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE.value)
    return None


def _classify_open_database(
    connection: sqlite3.Connection,
    catalog: MigrationCatalog,
    *,
    verify_managed: bool,
) -> DatabaseClassification:
    posture = apply_observational_connection_posture(connection)
    if posture.journal_mode != "delete":
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    objects = _user_schema_objects(connection)
    if not objects:
        return DatabaseClassification.EMPTY
    if ("table", "schema_migrations") not in objects:
        raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_NOT_EMPTY_UNMANAGED)
    if verify_managed:
        rows = _validate_migration_history(connection, catalog)
        current = rows[-1]
        _verify_schema_for_migration(connection, _required_migration(catalog, current.sequence))
        _verify_managed_state_invariants(connection)
    return DatabaseClassification.MANAGED


def _user_schema_objects(connection: sqlite3.Connection) -> set[tuple[str, str]]:
    try:
        rows = connection.execute(
            """
            SELECT type, name
            FROM sqlite_schema
            WHERE type IN ('table', 'index', 'view', 'trigger')
              AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID) from None
    return {(str(row[0]), str(row[1])) for row in rows}


def _user_tables(connection: sqlite3.Connection) -> set[str]:
    return {name for object_type, name in _user_schema_objects(connection) if object_type == "table"}


def _validate_migration_history(
    connection: sqlite3.Connection,
    catalog: MigrationCatalog,
) -> tuple[_MigrationHistoryRow, ...]:
    try:
        rows = connection.execute(
            """
            SELECT migration_id, sequence, schema_digest, applied_at, min_app_schema, max_app_schema
            FROM schema_migrations
            ORDER BY sequence, migration_id
            """
        ).fetchall()
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID) from None
    if not rows:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_MISSING)
    history = tuple(_history_row(row) for row in rows)
    seen_sequences: set[int] = set()
    seen_ids: set[str] = set()
    for index, row in enumerate(history, start=1):
        if row.sequence in seen_sequences or row.migration_id in seen_ids:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
        seen_sequences.add(row.sequence)
        seen_ids.add(row.migration_id)
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
        if row.min_app_schema != migration.min_app_schema or row.max_app_schema != migration.max_app_schema:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    return history


def _history_row(row: Iterable[Any]) -> _MigrationHistoryRow:
    values = tuple(row)
    if len(values) != 6:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    migration_id, sequence, schema_digest, applied_at, min_app_schema, max_app_schema = values
    if not isinstance(migration_id, str) or not isinstance(schema_digest, str) or not isinstance(applied_at, str):
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    if not isinstance(sequence, int) or not isinstance(min_app_schema, int) or not isinstance(max_app_schema, int):
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    if sequence < 1 or min_app_schema < 0 or max_app_schema < min_app_schema:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    _verify_timestamp(applied_at, SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    return _MigrationHistoryRow(
        migration_id=migration_id,
        sequence=sequence,
        schema_digest=schema_digest,
        applied_at=applied_at,
        min_app_schema=min_app_schema,
        max_app_schema=max_app_schema,
    )


def _apply_migration(connection: sqlite3.Connection, migration: MigrationDefinition) -> None:
    if migration.destructive:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    try:
        connection.execute("BEGIN IMMEDIATE")
        try:
            _apply_migration_in_transaction(connection, migration, fresh_install=True)
            connection.execute("COMMIT")
        except Exception:
            _rollback(connection)
            raise
    except SQLiteStateError:
        raise
    except sqlite3.Error:
        _rollback(connection)
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED) from None


def _apply_migration_in_transaction(
    connection: sqlite3.Connection,
    migration: MigrationDefinition,
    *,
    fresh_install: bool,
) -> None:
    if migration.destructive:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    try:
        for statement in _migration_statements(migration.sql_text):
            connection.execute(statement)
        _verify_schema_for_migration(connection, migration, fresh_install=fresh_install)
        _insert_migration_row(connection, migration)
    except SQLiteStateError:
        raise
    except sqlite3.Error:
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
    if _schema_manifest(connection) != _expected_schema_manifest(migration.sql_text):
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_FINGERPRINT_MISMATCH)
    if fresh_install:
        _verify_global_stop_clear_seed(connection)
        _verify_empty_bootstrap_tables(connection)
    _verify_foreign_key_posture(connection)


def _expected_schema_manifest(sql_text: str) -> tuple[Any, ...]:
    connection = sqlite3.connect(":memory:", isolation_level=None)
    try:
        apply_observational_connection_posture(connection)
        connection.execute("BEGIN IMMEDIATE")
        for statement in _migration_statements(sql_text):
            connection.execute(statement)
        manifest = _schema_manifest(connection)
        connection.execute("ROLLBACK")
        return manifest
    except SQLiteStateError:
        raise
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
    finally:
        connection.close()


def _schema_manifest(connection: sqlite3.Connection) -> tuple[Any, ...]:
    try:
        schema_rows = connection.execute(
            """
            SELECT type, name, tbl_name, sql
            FROM sqlite_schema
            WHERE type IN ('table', 'index', 'view', 'trigger')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY type, name
            """
        ).fetchall()
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
    manifest: list[Any] = [
        (
            "schema",
            str(object_type),
            str(name),
            str(table_name),
            _normalize_schema_sql(sql),
        )
        for object_type, name, table_name, sql in schema_rows
    ]
    tables = sorted(str(name) for object_type, name, _table_name, _sql in schema_rows if object_type == "table")
    for table_name in tables:
        manifest.append(("table_xinfo", table_name, _pragma_rows(connection, f"PRAGMA table_xinfo({_quote_identifier(table_name)})")))
        manifest.append(
            (
                "foreign_key_list",
                table_name,
                _pragma_rows(connection, f"PRAGMA foreign_key_list({_quote_identifier(table_name)})"),
            )
        )
        index_rows = _pragma_rows(connection, f"PRAGMA index_list({_quote_identifier(table_name)})")
        manifest.append(("index_list", table_name, index_rows))
        for index_row in index_rows:
            index_name = str(index_row[1])
            manifest.append(
                (
                    "index_xinfo",
                    table_name,
                    index_name,
                    _pragma_rows(connection, f"PRAGMA index_xinfo({_quote_identifier(index_name)})"),
                )
            )
    return tuple(manifest)


def _pragma_rows(connection: sqlite3.Connection, statement: str) -> tuple[tuple[Any, ...], ...]:
    try:
        return tuple(tuple(row) for row in connection.execute(statement).fetchall())
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _normalize_schema_sql(sql: Any) -> str:
    if sql is None:
        return ""
    return " ".join(str(sql).split())


def _verify_global_stop_clear_seed(connection: sqlite3.Connection) -> None:
    try:
        rows = connection.execute(
            """
            SELECT singleton_id, schema_id, version, active, stop_id, reason_class,
                   issuer_ref, issued_at, operator_decision_ref, updated_at
            FROM global_stop_current
            """
        ).fetchall()
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
    if rows != [
        (
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
    ]:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)


def _verify_empty_bootstrap_tables(connection: sqlite3.Connection) -> None:
    for table_name in EMPTY_AFTER_BOOTSTRAP_TABLES:
        try:
            count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        except sqlite3.Error:
            raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
        if count != 0:
            raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)


def _verify_managed_state_invariants(connection: sqlite3.Connection) -> None:
    _verify_global_stop_current_shape(connection)
    _verify_writer_ownership_shape(connection)


def _verify_global_stop_current_shape(connection: sqlite3.Connection) -> None:
    try:
        rows = connection.execute(
            """
            SELECT singleton_id, schema_id, version, active, stop_id, reason_class,
                   issuer_ref, issued_at, operator_decision_ref, updated_at
            FROM global_stop_current
            """
        ).fetchall()
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
    if len(rows) != 1:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    (
        singleton_id,
        schema_id,
        version,
        active,
        stop_id,
        reason_class,
        issuer_ref,
        issued_at,
        operator_decision_ref,
        updated_at,
    ) = rows[0]
    if singleton_id != 1 or schema_id != "governed-execution.nwp-global-stop.v1":
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    if not _is_non_negative_int(version) or active not in (0, 1):
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    _verify_timestamp(updated_at, SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    if active == 0:
        if any(value is not None for value in (stop_id, reason_class, issuer_ref, issued_at, operator_decision_ref)):
            raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
        return
    if not (
        _bounded_text(stop_id)
        and reason_class in {"operator_stop", "policy_stop", "safety_stop"}
        and _bounded_text(issuer_ref)
        and _bounded_text(operator_decision_ref)
    ):
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    _verify_timestamp(issued_at, SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)


def _verify_writer_ownership_shape(connection: sqlite3.Connection) -> None:
    try:
        rows = connection.execute(
            """
            SELECT singleton_id, writer_ref, generation, issued_ref, issuance_nonce_digest, acquired_at
            FROM writer_ownership
            """
        ).fetchall()
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
    if len(rows) > 1:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    if not rows:
        return
    singleton_id, writer_ref, generation, issued_ref, issuance_nonce_digest, acquired_at = rows[0]
    if singleton_id != 1:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    if not (_bounded_text(writer_ref) and _is_non_negative_int(generation) and _bounded_text(issued_ref)):
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    if not _is_sha256_hex(issuance_nonce_digest):
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    _verify_timestamp(acquired_at, SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)


def _verify_foreign_key_posture(connection: sqlite3.Connection) -> None:
    try:
        row = connection.execute("PRAGMA foreign_keys").fetchone()
    except sqlite3.Error:
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
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED) from None


def _required_migration(catalog: MigrationCatalog, sequence: int) -> MigrationDefinition:
    migration = catalog.by_sequence(sequence)
    if migration is None:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_GAP)
    return migration


def _rollback(connection: sqlite3.Connection) -> None:
    try:
        connection.execute("ROLLBACK")
    except sqlite3.Error:
        pass


def _verify_timestamp(value: Any, error_class: SQLiteStateErrorCode) -> None:
    if not isinstance(value, str) or RFC3339_UTC_Z.fullmatch(value) is None:
        raise SQLiteStateError(error_class)
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise SQLiteStateError(error_class) from None


def _bounded_text(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 96


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_sha256_hex(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and value == value.lower() and all(c in "0123456789abcdef" for c in value)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
