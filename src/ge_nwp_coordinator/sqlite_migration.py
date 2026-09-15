"""Forward-only packaged SQLite migration runner for Coordinator state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
from importlib import resources
import os
from pathlib import Path
import re
import sqlite3
import stat
from typing import Any, Iterable

from ge_nwp_coordinator.sqlite_connection import (
    apply_connection_posture,
    apply_observational_connection_posture,
    open_existing_sqlite_connection,
    _is_operational_posture_error,
    _open_bound_existing_sqlite_connection,
    _open_sqlite_connection,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteStateError, SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_security import existing_state_database_path
from ge_nwp_coordinator.sqlite_writer_state import _parse_writer_ownership_rows
from ge_nwp_coordinator.state_authority_lock import acquire_state_authority_lock

CURRENT_APPLICATION_SCHEMA = 2
MIGRATION_PACKAGE = "ge_nwp_coordinator.sqlite_migrations"
SQLITE_HEADER = b"SQLite format 3\x00"
ROLLBACK_JOURNAL_FILE_FORMAT_VERSION = 1
MAX_MIGRATION_RESOURCE_BYTES = 1_048_576
MIGRATION_RESOURCE_READ_CHUNK_BYTES = 65_536
_C2B2_MIGRATION_ID = "0002_development_program_and_effect_state"
_SECTION41_MIGRATION_ID = "0003_cognitive_proposal_and_selection_state"
_SQLITE_STRICT_MINIMUM_VERSION = (3, 37, 0)
RFC3339_UTC_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_SQLITE_VALIDATION_OPERATIONAL_PRIMARY_RESULT_CODES = frozenset(
    code
    for code in (
        getattr(sqlite3, "SQLITE_BUSY", None),
        getattr(sqlite3, "SQLITE_LOCKED", None),
        getattr(sqlite3, "SQLITE_NOMEM", None),
        getattr(sqlite3, "SQLITE_READONLY", None),
        getattr(sqlite3, "SQLITE_INTERRUPT", None),
        getattr(sqlite3, "SQLITE_IOERR", None),
        getattr(sqlite3, "SQLITE_FULL", None),
        getattr(sqlite3, "SQLITE_CANTOPEN", None),
        getattr(sqlite3, "SQLITE_PROTOCOL", None),
    )
    if type(code) is int
)
_SQLITE_VALIDATION_INTEGRITY_PRIMARY_RESULT_CODES = frozenset(
    code
    for code in (
        getattr(sqlite3, "SQLITE_ERROR", None),
        getattr(sqlite3, "SQLITE_SCHEMA", None),
        getattr(sqlite3, "SQLITE_CORRUPT", None),
        getattr(sqlite3, "SQLITE_NOTADB", None),
        getattr(sqlite3, "SQLITE_MISMATCH", None),
        getattr(sqlite3, "SQLITE_CONSTRAINT", None),
    )
    if type(code) is int
)

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
        "development_program_heads",
        "development_program_versions",
        "development_accepted_intent_revisions",
        "development_work_item_heads",
        "development_work_item_revisions",
        "development_program_version_work_items",
        "development_revision_edges",
        "development_work_spec_bindings",
        "development_semantic_attempts",
        "development_attempt_fences",
        "development_authority_evaluations",
        "development_effect_intents",
        "development_effect_fences",
        "development_author_commands",
        "development_effect_heads",
        "development_delivery_attempts",
        "development_delivery_heads",
        "development_decisions",
        "development_mutation_receipts",
        "development_model_source_invocations",
        "development_pre_execution_planning_contexts",
        "development_private_proposal_artifact_bindings",
        "development_model_proposals",
        "development_pre_execution_plan_projections",
        "development_model_proposal_evidence_bindings",
        "development_pre_execution_dispositions",
        "development_pre_execution_selection_heads",
        "development_cognitive_mutation_receipts",
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

_EMPTY_AFTER_C2B2_MIGRATION_TABLES = frozenset(
    {
        "development_program_heads",
        "development_program_versions",
        "development_accepted_intent_revisions",
        "development_work_item_heads",
        "development_work_item_revisions",
        "development_program_version_work_items",
        "development_revision_edges",
        "development_work_spec_bindings",
        "development_semantic_attempts",
        "development_attempt_fences",
        "development_authority_evaluations",
        "development_effect_intents",
        "development_effect_fences",
        "development_author_commands",
        "development_effect_heads",
        "development_delivery_attempts",
        "development_delivery_heads",
        "development_decisions",
        "development_mutation_receipts",
    }
)

_EMPTY_AFTER_SECTION41_MIGRATION_TABLES = frozenset(
    {
        "development_model_source_invocations",
        "development_pre_execution_planning_contexts",
        "development_private_proposal_artifact_bindings",
        "development_model_proposals",
        "development_pre_execution_plan_projections",
        "development_model_proposal_evidence_bindings",
        "development_pre_execution_dispositions",
        "development_pre_execution_selection_heads",
        "development_cognitive_mutation_receipts",
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
        if type(self.migrations) is not tuple or not self.migrations:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
        by_sequence: dict[int, MigrationDefinition] = {}
        by_id: set[str] = set()
        resources_seen: set[str] = set()
        projections: set[tuple[int, str, str, int, int]] = set()
        for expected_sequence, migration in enumerate(self.migrations, start=1):
            _validate_migration_definition(migration)
            if (
                migration.sequence != expected_sequence
                or migration.sequence in by_sequence
                or migration.migration_id in by_id
                or migration.resource_name in resources_seen
            ):
                raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
            projection = _migration_persisted_projection(migration)
            if projection in projections:
                raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
            by_sequence[migration.sequence] = migration
            by_id.add(migration.migration_id)
            resources_seen.add(migration.resource_name)
            projections.add(projection)
        if tuple(sorted(by_sequence)) != tuple(range(1, len(self.migrations) + 1)):
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_GAP)

    @property
    def latest_sequence(self) -> int:
        return len(self.migrations)

    def by_sequence(self, sequence: int) -> MigrationDefinition | None:
        if type(sequence) is not int:
            return None
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


@dataclass(frozen=True, slots=True, repr=False)
class _MigrationHistoryRow:
    migration_id: str
    sequence: int
    schema_digest: str
    applied_at: str
    min_app_schema: int
    max_app_schema: int

    def __repr__(self) -> str:
        return "<_MigrationHistoryRow>"


class _MigrationDatabaseDisposition(str, Enum):
    ABSENT = "absent"
    EMPTY = "empty"
    CURRENT = "current"
    SUPPORTED_OLDER_PREFIX = "supported_older_prefix"
    UNSUPPORTED_OLDER = "unsupported_older"
    NEWER_UNSUPPORTED = "newer_unsupported"
    CORRUPT_HISTORY = "corrupt_history"
    PARTIAL_MIGRATION = "partial_migration"
    DATABASE_NOT_EMPTY_UNMANAGED = "database_not_empty_unmanaged"


class _MigrationTransactionPhase(str, Enum):
    NEW = "new"
    TRANSACTION_ACTIVE = "transaction_active"
    COMMIT_ATTEMPTED = "commit_attempted"
    COMMIT_RETURNED = "commit_returned"
    RECOVERING = "recovering"
    CLOSED = "closed"


class _MigrationCommitEvidence(str, Enum):
    COMMITTED_EXACT = "committed_exact"
    DEFINITELY_NOT_COMMITTED = "definitely_not_committed"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True, repr=False)
class _MigrationDatabaseAssessment:
    disposition: _MigrationDatabaseDisposition
    history: tuple[_MigrationHistoryRow, ...] = ()
    reason: SQLiteStateErrorCode | None = None

    @property
    def current_sequence(self) -> int:
        return self.history[-1].sequence if self.history else 0

    @property
    def current_migration_id(self) -> str | None:
        return self.history[-1].migration_id if self.history else None

    def __repr__(self) -> str:
        return f"<_MigrationDatabaseAssessment disposition={self.disposition.value!r}>"


@dataclass(frozen=True, slots=True, repr=False)
class _MigrationPlan:
    prior_history: tuple[_MigrationHistoryRow, ...]
    suffix: tuple[MigrationDefinition, ...] = field(repr=False)
    target_sequence: int
    applied_at: str
    fresh_install: bool
    verify_managed_invariants: bool

    def __repr__(self) -> str:
        return (
            "<_MigrationPlan "
            f"prior_sequence={len(self.prior_history)} "
            f"suffix_length={len(self.suffix)} "
            f"target_sequence={self.target_sequence}>"
        )


@dataclass(frozen=True, slots=True, repr=False)
class _MigrationRecoveryResult:
    evidence: _MigrationCommitEvidence

    def __repr__(self) -> str:
        return f"<_MigrationRecoveryResult evidence={self.evidence.value!r}>"


@dataclass(frozen=True, slots=True, repr=False)
class _PackagedMigrationSpec:
    migration_id: str
    sequence: int
    resource_name: str
    literal_checksum: str
    min_app_schema: int
    max_app_schema: int
    destructive: bool
    description: str


_PACKAGED_MIGRATION_SPECS = (
    _PackagedMigrationSpec(
        migration_id="0001_initial",
        sequence=1,
        resource_name="0001_initial.sql",
        literal_checksum="1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148",
        min_app_schema=1,
        max_app_schema=1,
        destructive=False,
        description="Initial local SQLite Coordinator state schema",
    ),
    _PackagedMigrationSpec(
        migration_id=_C2B2_MIGRATION_ID,
        sequence=2,
        resource_name="0002_development_program_and_effect_state.sql",
        literal_checksum="5859f49994b1467db71911fb60db4f1cfc562af7517dc6e4d81b5b29ca44d56c",
        min_app_schema=2,
        max_app_schema=2,
        destructive=False,
        description="Durable development program and effect state schema",
    ),
    _PackagedMigrationSpec(
        migration_id=_SECTION41_MIGRATION_ID,
        sequence=3,
        resource_name="0003_cognitive_proposal_and_selection_state.sql",
        literal_checksum="b5c7cac8e074b77ab369579f1f8015f547f1a2776b4b09d612e56280f16c1579",
        min_app_schema=2,
        max_app_schema=2,
        destructive=False,
        description="Cognitive proposal and pre-execution selection state schema",
    ),
)


class _SQLiteOperationalValidationError(SQLiteStateError):
    """Private marker that preserves operational validation origin."""


def _is_operational_validation_error(error: SQLiteStateError) -> bool:
    return isinstance(error, _SQLiteOperationalValidationError) or _is_operational_posture_error(error)


def _validation_sqlite_state_error(
    error: sqlite3.Error,
    error_class: SQLiteStateErrorCode,
) -> SQLiteStateError:
    code = getattr(error, "sqlite_errorcode", None)
    if type(code) is not int:
        return _SQLiteOperationalValidationError(error_class)
    primary_code = code & 0xFF
    if primary_code in _SQLITE_VALIDATION_INTEGRITY_PRIMARY_RESULT_CODES:
        return SQLiteStateError(error_class)
    if primary_code in _SQLITE_VALIDATION_OPERATIONAL_PRIMARY_RESULT_CODES:
        return _SQLiteOperationalValidationError(error_class)
    return _SQLiteOperationalValidationError(error_class)


def load_migration_catalog() -> MigrationCatalog:
    catalog, error = _load_migration_catalog_result()
    if error is not None or catalog is None:
        raise SQLiteStateError(error or SQLiteStateErrorCode.MIGRATION_FAILED)
    return catalog


def _load_migration_catalog_result() -> tuple[MigrationCatalog | None, SQLiteStateErrorCode | None]:
    try:
        package = resources.files(MIGRATION_PACKAGE)
        if not isinstance(package, Path):
            return (None, SQLiteStateErrorCode.MIGRATION_FAILED)
        package_metadata = os.lstat(package)
        if stat.S_ISLNK(package_metadata.st_mode) or not stat.S_ISDIR(package_metadata.st_mode):
            return (None, SQLiteStateErrorCode.MIGRATION_FAILED)
        actual_resources = tuple(
            sorted(
                entry.name
                for entry in package.iterdir()
                if entry.name.endswith(".sql")
            )
        )
        expected_resources = tuple(spec.resource_name for spec in _PACKAGED_MIGRATION_SPECS)
        if actual_resources != expected_resources:
            return (None, SQLiteStateErrorCode.MIGRATION_FAILED)
        definitions: list[MigrationDefinition] = []
        for spec in _PACKAGED_MIGRATION_SPECS:
            sql_bytes = _read_filesystem_migration_resource(package, spec.resource_name)
            checksum = hashlib.sha256(sql_bytes).hexdigest()
            if checksum != spec.literal_checksum:
                return (None, SQLiteStateErrorCode.MIGRATION_FAILED)
            definition = MigrationDefinition(
                migration_id=spec.migration_id,
                sequence=spec.sequence,
                resource_name=spec.resource_name,
                sql_bytes=sql_bytes,
                checksum=checksum,
                min_app_schema=spec.min_app_schema,
                max_app_schema=spec.max_app_schema,
                destructive=spec.destructive,
                description=spec.description,
            )
            _migration_statements(definition.sql_text)
            definitions.append(definition)
        return (MigrationCatalog(migrations=tuple(definitions)), None)
    except SQLiteStateError as exc:
        try:
            return (None, SQLiteStateErrorCode(exc.error_class))
        except ValueError:
            return (None, SQLiteStateErrorCode.MIGRATION_FAILED)
    except (OSError, UnicodeError, ValueError, TypeError):
        return (None, SQLiteStateErrorCode.MIGRATION_FAILED)


def _read_filesystem_migration_resource(package: Path, resource_name: str) -> bytes:
    resource = package.joinpath(resource_name)
    descriptor: int | None = None
    payload: bytes | None = None
    valid = True
    before_identity: tuple[int, int, int, int, int, int] | None = None
    try:
        before = os.lstat(resource)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            valid = False
        else:
            before_identity = _migration_resource_identity(before)
        if valid:
            flags = os.O_RDONLY
            flags |= getattr(os, "O_CLOEXEC", 0)
            flags |= getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(resource, flags)
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or _migration_resource_identity(opened) != before_identity
                or opened.st_size > MAX_MIGRATION_RESOURCE_BYTES
            ):
                valid = False
        chunks: list[bytes] = []
        total = 0
        while valid and descriptor is not None:
            chunk = os.read(descriptor, MIGRATION_RESOURCE_READ_CHUNK_BYTES)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_MIGRATION_RESOURCE_BYTES:
                valid = False
                break
            chunks.append(chunk)
        if valid and descriptor is not None:
            after_opened = os.fstat(descriptor)
            after_path = os.lstat(resource)
            if (
                stat.S_ISLNK(after_path.st_mode)
                or not stat.S_ISREG(after_path.st_mode)
                or _migration_resource_identity(after_opened) != before_identity
                or _migration_resource_identity(after_path) != before_identity
            ):
                valid = False
            else:
                payload = b"".join(chunks)
    except (OSError, ValueError, TypeError):
        valid = False
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                valid = False
    if not valid or payload is None or not (1 <= len(payload) <= MAX_MIGRATION_RESOURCE_BYTES):
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    return payload


def _migration_resource_identity(metadata: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _validate_migration_definition(migration: MigrationDefinition) -> None:
    if type(migration) is not MigrationDefinition:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    if (
        type(migration.migration_id) is not str
        or not (1 <= len(migration.migration_id) <= 96)
        or type(migration.sequence) is not int
        or migration.sequence < 1
        or type(migration.resource_name) is not str
        or len(migration.resource_name) > 96
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.sql", migration.resource_name) is None
        or type(migration.sql_bytes) is not bytes
        or not (1 <= len(migration.sql_bytes) <= 1_048_576)
        or type(migration.checksum) is not str
        or re.fullmatch(r"[0-9a-f]{64}", migration.checksum) is None
        or hashlib.sha256(migration.sql_bytes).hexdigest() != migration.checksum
        or type(migration.min_app_schema) is not int
        or type(migration.max_app_schema) is not int
        or migration.min_app_schema < 0
        or migration.max_app_schema < migration.min_app_schema
        or type(migration.destructive) is not bool
        or type(migration.description) is not str
        or not (1 <= len(migration.description) <= 256)
    ):
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    decode_failed = False
    try:
        migration.sql_bytes.decode("utf-8")
    except UnicodeError:
        decode_failed = True
    if decode_failed:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)


def _migration_persisted_projection(
    migration: MigrationDefinition,
) -> tuple[int, str, str, int, int]:
    return (
        migration.sequence,
        migration.migration_id,
        migration.checksum,
        migration.min_app_schema,
        migration.max_app_schema,
    )


def inspect_database(location: CoordinatorStateLocation) -> DatabaseInspection:
    """Observe the fixed database path without creating or mutating it."""

    inspection: DatabaseInspection | None = None
    pending_error: SQLiteStateErrorCode | None = None
    try:
        catalog = load_migration_catalog()
        assessment = _assess_location_database(
            location,
            catalog,
            current_app_schema=CURRENT_APPLICATION_SCHEMA,
            verify_managed_invariants=True,
        )
        inspection = _inspection_from_assessment(assessment, catalog)
    except SQLiteStateError as exc:
        pending_error = _safe_state_error_code(exc)
    if pending_error is not None:
        raise SQLiteStateError(pending_error)
    if inspection is None:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    return inspection


def initialize_database(location: CoordinatorStateLocation) -> DatabaseInspection:
    """Explicitly create or initialize the local administrative database."""

    inspection: DatabaseInspection | None = None
    pending_error: SQLiteStateErrorCode | None = None
    try:
        inspection = _initialize_database_with_catalog(
            location,
            load_migration_catalog(),
            current_app_schema=CURRENT_APPLICATION_SCHEMA,
            verify_managed_invariants=True,
        )
    except SQLiteStateError as exc:
        pending_error = _safe_state_error_code(exc)
    if pending_error is not None:
        raise SQLiteStateError(pending_error)
    if inspection is None:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    return inspection


def migrate_database(location: CoordinatorStateLocation) -> DatabaseInspection:
    """Explicitly migrate an exact supported prefix through packaged migrations."""

    inspection: DatabaseInspection | None = None
    pending_error: SQLiteStateErrorCode | None = None
    try:
        inspection = _migrate_database_with_catalog(
            location,
            load_migration_catalog(),
            current_app_schema=CURRENT_APPLICATION_SCHEMA,
            verify_managed_invariants=True,
        )
    except SQLiteStateError as exc:
        pending_error = _safe_state_error_code(exc)
    if pending_error is not None:
        raise SQLiteStateError(pending_error)
    if inspection is None:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    return inspection


def validate_database(location: CoordinatorStateLocation) -> DatabaseInspection:
    """Observationally validate an existing managed database when present."""

    return inspect_database(location)


def _validate_current_managed_connection(connection: sqlite3.Connection) -> DatabaseInspection:
    """Validate that an already-open connection is at the current managed schema."""

    catalog = load_migration_catalog()
    assessment = _assess_open_database(
        connection,
        catalog,
        current_app_schema=CURRENT_APPLICATION_SCHEMA,
        verify_managed_invariants=True,
        preserve_operational_errors=True,
    )
    if assessment.disposition is not _MigrationDatabaseDisposition.CURRENT:
        _raise_assessment_failure(assessment)
    return _inspection_from_assessment(assessment, catalog)


def _initialize_database_with_catalog(
    location: CoordinatorStateLocation,
    catalog: MigrationCatalog,
    *,
    current_app_schema: int,
    verify_managed_invariants: bool,
) -> DatabaseInspection:
    _require_application_schema(current_app_schema)
    _validate_catalog_statement_plans(catalog)
    _require_catalog_terminal_compatibility(catalog, current_app_schema)
    candidate = _assess_location_database_history_only(
        location,
        catalog,
        current_app_schema=current_app_schema,
    )
    if candidate.disposition not in {
        _MigrationDatabaseDisposition.ABSENT,
        _MigrationDatabaseDisposition.EMPTY,
        _MigrationDatabaseDisposition.CURRENT,
    }:
        _raise_assessment_failure(candidate)
    _require_sqlite_runtime_for_administrative_catalog_target(catalog)
    initial_suffix = (
        catalog.migrations
        if candidate.disposition is not _MigrationDatabaseDisposition.CURRENT
        else ()
    )
    _validate_selected_suffix(initial_suffix)
    preflight = _assess_location_database(
        location,
        catalog,
        current_app_schema=current_app_schema,
        verify_managed_invariants=verify_managed_invariants,
    )
    if preflight.disposition not in {
        _MigrationDatabaseDisposition.ABSENT,
        _MigrationDatabaseDisposition.EMPTY,
        _MigrationDatabaseDisposition.CURRENT,
    }:
        _raise_assessment_failure(preflight)

    with acquire_state_authority_lock(location) as authority_lock:
        locked_candidate = _assess_location_database_history_only(
            location,
            catalog,
            current_app_schema=current_app_schema,
        )
        if locked_candidate.disposition not in {
            _MigrationDatabaseDisposition.ABSENT,
            _MigrationDatabaseDisposition.EMPTY,
            _MigrationDatabaseDisposition.CURRENT,
        }:
            _raise_assessment_failure(locked_candidate)
        locked_suffix = (
            catalog.migrations
            if locked_candidate.disposition is not _MigrationDatabaseDisposition.CURRENT
            else ()
        )
        _validate_selected_suffix(locked_suffix)
        locked = _assess_location_database(
            location,
            catalog,
            current_app_schema=current_app_schema,
            verify_managed_invariants=verify_managed_invariants,
        )
        if locked.disposition is _MigrationDatabaseDisposition.CURRENT:
            return _inspection_from_assessment(locked, catalog)
        if locked.disposition not in {
            _MigrationDatabaseDisposition.ABSENT,
            _MigrationDatabaseDisposition.EMPTY,
        }:
            _raise_assessment_failure(locked)
        _validate_selected_suffix(catalog.migrations)
        if locked.disposition is _MigrationDatabaseDisposition.ABSENT:
            bootstrap_connection = _open_sqlite_connection(location)
            bootstrap_close_failed = False
            try:
                bootstrap_connection.close()
            except Exception:
                bootstrap_close_failed = True
            if bootstrap_close_failed:
                raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
        binding = authority_lock._capture_state_database_authority_binding(location)
        plan = _migration_plan(
            prior_history=(),
            suffix=catalog.migrations,
            fresh_install=True,
            verify_managed_invariants=verify_managed_invariants,
        )
        return _run_bound_migration_plan(
            authority_lock,
            binding,
            catalog,
            plan,
            current_app_schema=current_app_schema,
        )


def _migrate_database_with_catalog(
    location: CoordinatorStateLocation,
    catalog: MigrationCatalog,
    *,
    current_app_schema: int,
    verify_managed_invariants: bool,
) -> DatabaseInspection:
    _require_application_schema(current_app_schema)
    _validate_catalog_statement_plans(catalog)
    _require_catalog_terminal_compatibility(catalog, current_app_schema)
    candidate = _assess_location_database_history_only(
        location,
        catalog,
        current_app_schema=current_app_schema,
    )
    if candidate.disposition in {
        _MigrationDatabaseDisposition.ABSENT,
        _MigrationDatabaseDisposition.EMPTY,
    }:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_MISSING)
    if candidate.disposition not in {
        _MigrationDatabaseDisposition.CURRENT,
        _MigrationDatabaseDisposition.SUPPORTED_OLDER_PREFIX,
    }:
        _raise_assessment_failure(candidate)
    _require_sqlite_runtime_for_administrative_catalog_target(catalog)
    preflight_suffix = catalog.migrations[candidate.current_sequence :]
    _validate_selected_suffix(preflight_suffix)
    preflight = _assess_location_database(
        location,
        catalog,
        current_app_schema=current_app_schema,
        verify_managed_invariants=verify_managed_invariants,
    )
    if preflight.disposition not in {
        _MigrationDatabaseDisposition.CURRENT,
        _MigrationDatabaseDisposition.SUPPORTED_OLDER_PREFIX,
    }:
        _raise_assessment_failure(preflight)

    with acquire_state_authority_lock(location) as authority_lock:
        locked_candidate = _assess_location_database_history_only(
            location,
            catalog,
            current_app_schema=current_app_schema,
        )
        if locked_candidate.disposition is _MigrationDatabaseDisposition.CURRENT:
            locked_suffix: tuple[MigrationDefinition, ...] = ()
        elif locked_candidate.disposition is _MigrationDatabaseDisposition.SUPPORTED_OLDER_PREFIX:
            locked_suffix = catalog.migrations[locked_candidate.current_sequence :]
        else:
            _raise_assessment_failure(locked_candidate)
        _validate_selected_suffix(locked_suffix)
        locked = _assess_location_database(
            location,
            catalog,
            current_app_schema=current_app_schema,
            verify_managed_invariants=verify_managed_invariants,
        )
        if locked.disposition is _MigrationDatabaseDisposition.CURRENT:
            return _inspection_from_assessment(locked, catalog)
        if locked.disposition is not _MigrationDatabaseDisposition.SUPPORTED_OLDER_PREFIX:
            _raise_assessment_failure(locked)
        suffix = catalog.migrations[locked.current_sequence :]
        if suffix != locked_suffix:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
        binding = authority_lock._capture_state_database_authority_binding(location)
        plan = _migration_plan(
            prior_history=locked.history,
            suffix=suffix,
            fresh_install=False,
            verify_managed_invariants=verify_managed_invariants,
        )
        return _run_bound_migration_plan(
            authority_lock,
            binding,
            catalog,
            plan,
            current_app_schema=current_app_schema,
        )


def _inspect_open_database(
    connection: sqlite3.Connection,
    catalog: MigrationCatalog,
) -> DatabaseInspection:
    assessment = _assess_open_database(
        connection,
        catalog,
        current_app_schema=CURRENT_APPLICATION_SCHEMA,
        verify_managed_invariants=True,
    )
    return _inspection_from_assessment(assessment, catalog)


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


def _inspection_from_assessment(
    assessment: _MigrationDatabaseAssessment,
    catalog: MigrationCatalog,
) -> DatabaseInspection:
    if assessment.disposition is _MigrationDatabaseDisposition.ABSENT:
        return _inspection(DatabaseClassification.ABSENT, catalog)
    if assessment.disposition is _MigrationDatabaseDisposition.EMPTY:
        return _inspection(DatabaseClassification.EMPTY, catalog)
    if assessment.disposition is _MigrationDatabaseDisposition.CURRENT:
        return DatabaseInspection(
            classification=DatabaseClassification.MANAGED,
            current_sequence=assessment.current_sequence,
            latest_sequence=catalog.latest_sequence,
            current_migration_id=assessment.current_migration_id,
        )
    reason = assessment.reason or _default_error_for_disposition(assessment.disposition)
    return DatabaseInspection(
        classification=DatabaseClassification.UNKNOWN,
        current_sequence=0,
        latest_sequence=catalog.latest_sequence,
        current_migration_id=None,
        reason=reason.value,
    )


def _raise_assessment_failure(assessment: _MigrationDatabaseAssessment) -> None:
    reason = assessment.reason or _default_error_for_disposition(assessment.disposition)
    raise SQLiteStateError(reason)


def _default_error_for_disposition(
    disposition: _MigrationDatabaseDisposition,
) -> SQLiteStateErrorCode:
    if disposition is _MigrationDatabaseDisposition.SUPPORTED_OLDER_PREFIX:
        return SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE
    if disposition is _MigrationDatabaseDisposition.UNSUPPORTED_OLDER:
        return SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE
    if disposition is _MigrationDatabaseDisposition.NEWER_UNSUPPORTED:
        return SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW
    if disposition is _MigrationDatabaseDisposition.CORRUPT_HISTORY:
        return SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID
    if disposition is _MigrationDatabaseDisposition.PARTIAL_MIGRATION:
        return SQLiteStateErrorCode.SCHEMA_FINGERPRINT_MISMATCH
    if disposition is _MigrationDatabaseDisposition.DATABASE_NOT_EMPTY_UNMANAGED:
        return SQLiteStateErrorCode.DATABASE_NOT_EMPTY_UNMANAGED
    if disposition in {
        _MigrationDatabaseDisposition.ABSENT,
        _MigrationDatabaseDisposition.EMPTY,
    }:
        return SQLiteStateErrorCode.MIGRATION_HISTORY_MISSING
    return SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE


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


def _assess_location_database(
    location: CoordinatorStateLocation,
    catalog: MigrationCatalog,
    *,
    current_app_schema: int,
    verify_managed_invariants: bool,
) -> _MigrationDatabaseAssessment:
    database_path = existing_state_database_path(location)
    if database_path is None:
        return _MigrationDatabaseAssessment(_MigrationDatabaseDisposition.ABSENT)
    file_state = _classify_existing_file_header(database_path)
    if file_state is not None:
        if file_state[0] is DatabaseClassification.EMPTY:
            return _MigrationDatabaseAssessment(_MigrationDatabaseDisposition.EMPTY)
        reason = SQLiteStateErrorCode(file_state[1] or SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.CORRUPT_HISTORY,
            reason=reason,
        )
    try:
        connection = open_existing_sqlite_connection(location, read_only=True)
    except SQLiteStateError as exc:
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.CORRUPT_HISTORY,
            reason=SQLiteStateErrorCode(exc.error_class),
        )
    try:
        return _assess_open_database(
            connection,
            catalog,
            current_app_schema=current_app_schema,
            verify_managed_invariants=verify_managed_invariants,
        )
    finally:
        try:
            connection.close()
        except sqlite3.Error:
            pass


def _assess_location_database_history_only(
    location: CoordinatorStateLocation,
    catalog: MigrationCatalog,
    *,
    current_app_schema: int,
) -> _MigrationDatabaseAssessment:
    """Resolve an administrative candidate prefix without deriving a schema manifest."""

    database_path = existing_state_database_path(location)
    if database_path is None:
        return _MigrationDatabaseAssessment(_MigrationDatabaseDisposition.ABSENT)
    file_state = _classify_existing_file_header(database_path)
    if file_state is not None:
        if file_state[0] is DatabaseClassification.EMPTY:
            return _MigrationDatabaseAssessment(_MigrationDatabaseDisposition.EMPTY)
        reason = SQLiteStateErrorCode(file_state[1] or SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.CORRUPT_HISTORY,
            reason=reason,
        )
    try:
        connection = open_existing_sqlite_connection(location, read_only=True)
    except SQLiteStateError as exc:
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.CORRUPT_HISTORY,
            reason=SQLiteStateErrorCode(exc.error_class),
        )
    try:
        return _assess_open_database_history_only(
            connection,
            catalog,
            current_app_schema=current_app_schema,
        )
    finally:
        try:
            connection.close()
        except sqlite3.Error:
            pass


def _assess_open_database_history_only(
    connection: sqlite3.Connection,
    catalog: MigrationCatalog,
    *,
    current_app_schema: int,
) -> _MigrationDatabaseAssessment:
    _require_application_schema(current_app_schema)
    try:
        posture = apply_observational_connection_posture(connection)
        if posture.journal_mode != "delete":
            raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
        has_objects = _has_any_user_schema_object(connection)
        has_history_table = _has_schema_migrations_table(connection)
    except SQLiteStateError as exc:
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.CORRUPT_HISTORY,
            reason=SQLiteStateErrorCode(exc.error_class),
        )
    if not has_objects:
        return _MigrationDatabaseAssessment(_MigrationDatabaseDisposition.EMPTY)
    if not has_history_table:
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.DATABASE_NOT_EMPTY_UNMANAGED,
            reason=SQLiteStateErrorCode.DATABASE_NOT_EMPTY_UNMANAGED,
        )
    try:
        history = _read_validated_migration_history(connection, catalog)
    except SQLiteStateError as exc:
        code = SQLiteStateErrorCode(exc.error_class)
        disposition = (
            _MigrationDatabaseDisposition.NEWER_UNSUPPORTED
            if code is SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW
            else _MigrationDatabaseDisposition.CORRUPT_HISTORY
        )
        return _MigrationDatabaseAssessment(disposition, reason=code)
    current = history[-1]
    if len(history) == catalog.latest_sequence:
        if current.min_app_schema > current_app_schema:
            return _MigrationDatabaseAssessment(
                _MigrationDatabaseDisposition.NEWER_UNSUPPORTED,
                history=history,
                reason=SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW,
            )
        if current.max_app_schema < current_app_schema:
            return _MigrationDatabaseAssessment(
                _MigrationDatabaseDisposition.UNSUPPORTED_OLDER,
                history=history,
                reason=SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE,
            )
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.CURRENT,
            history=history,
        )
    target = _required_migration(catalog, catalog.latest_sequence)
    if target.min_app_schema > current_app_schema:
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.NEWER_UNSUPPORTED,
            history=history,
            reason=SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW,
        )
    if target.max_app_schema < current_app_schema:
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.UNSUPPORTED_OLDER,
            history=history,
            reason=SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE,
        )
    return _MigrationDatabaseAssessment(
        _MigrationDatabaseDisposition.SUPPORTED_OLDER_PREFIX,
        history=history,
        reason=SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE,
    )


def _has_any_user_schema_object(connection: sqlite3.Connection) -> bool:
    rows = _bounded_query_rows(
        connection,
        """
        SELECT type, name
        FROM sqlite_schema
        WHERE type IN ('table', 'index', 'view', 'trigger')
          AND name NOT LIKE 'sqlite_%'
        ORDER BY type, name
        LIMIT 1
        """,
        (),
        1,
        error_class=SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID,
    )
    return bool(rows)


def _has_schema_migrations_table(connection: sqlite3.Connection) -> bool:
    rows = _bounded_query_rows(
        connection,
        """
        SELECT name
        FROM sqlite_schema
        WHERE type = 'table' AND name = 'schema_migrations'
        LIMIT 1
        """,
        (),
        1,
        error_class=SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID,
    )
    return bool(rows)


def _assess_open_database(
    connection: sqlite3.Connection,
    catalog: MigrationCatalog,
    *,
    current_app_schema: int,
    verify_managed_invariants: bool,
    preserve_operational_errors: bool = False,
) -> _MigrationDatabaseAssessment:
    _require_application_schema(current_app_schema)
    try:
        posture = apply_observational_connection_posture(connection)
        if posture.journal_mode != "delete":
            raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
        has_objects = _has_any_user_schema_object(connection)
        has_history_table = _has_schema_migrations_table(connection)
    except SQLiteStateError as exc:
        if preserve_operational_errors and _is_operational_validation_error(exc):
            raise
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.CORRUPT_HISTORY,
            reason=SQLiteStateErrorCode(exc.error_class),
        )
    if not has_objects:
        return _MigrationDatabaseAssessment(_MigrationDatabaseDisposition.EMPTY)
    if not has_history_table:
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.DATABASE_NOT_EMPTY_UNMANAGED,
            reason=SQLiteStateErrorCode.DATABASE_NOT_EMPTY_UNMANAGED,
        )
    try:
        history = _read_validated_migration_history(connection, catalog)
    except SQLiteStateError as exc:
        if preserve_operational_errors and _is_operational_validation_error(exc):
            raise
        code = SQLiteStateErrorCode(exc.error_class)
        disposition = (
            _MigrationDatabaseDisposition.NEWER_UNSUPPORTED
            if code is SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW
            else _MigrationDatabaseDisposition.CORRUPT_HISTORY
        )
        return _MigrationDatabaseAssessment(disposition, reason=code)
    current = history[-1]
    try:
        _verify_schema_for_sequence(
            connection,
            catalog,
            current.sequence,
            verify_managed_invariants=verify_managed_invariants,
            fresh_install=False,
        )
    except SQLiteStateError as exc:
        if preserve_operational_errors and _is_operational_validation_error(exc):
            raise
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.PARTIAL_MIGRATION,
            history=history,
            reason=SQLiteStateErrorCode(exc.error_class),
        )
    if len(history) == catalog.latest_sequence:
        if current.min_app_schema > current_app_schema:
            return _MigrationDatabaseAssessment(
                _MigrationDatabaseDisposition.NEWER_UNSUPPORTED,
                history=history,
                reason=SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW,
            )
        if current.max_app_schema < current_app_schema:
            return _MigrationDatabaseAssessment(
                _MigrationDatabaseDisposition.UNSUPPORTED_OLDER,
                history=history,
                reason=SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE,
            )
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.CURRENT,
            history=history,
        )
    target = _required_migration(catalog, catalog.latest_sequence)
    if target.min_app_schema > current_app_schema:
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.NEWER_UNSUPPORTED,
            history=history,
            reason=SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW,
        )
    if target.max_app_schema < current_app_schema:
        return _MigrationDatabaseAssessment(
            _MigrationDatabaseDisposition.UNSUPPORTED_OLDER,
            history=history,
            reason=SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE,
        )
    return _MigrationDatabaseAssessment(
        _MigrationDatabaseDisposition.SUPPORTED_OLDER_PREFIX,
        history=history,
        reason=SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE,
    )


def _classify_open_database(
    connection: sqlite3.Connection,
    catalog: MigrationCatalog,
    *,
    verify_managed: bool,
) -> DatabaseClassification:
    assessment = _assess_open_database(
        connection,
        catalog,
        current_app_schema=CURRENT_APPLICATION_SCHEMA,
        verify_managed_invariants=verify_managed,
    )
    return _inspection_from_assessment(assessment, catalog).classification


def _user_schema_objects(
    connection: sqlite3.Connection,
    *,
    catalog: MigrationCatalog,
) -> set[tuple[str, str]]:
    expected_manifest = _expected_schema_manifest_for_sequence(catalog, catalog.latest_sequence)
    maximum_objects = sum(1 for item in expected_manifest if item[0] == "schema") + 1
    try:
        rows = _bounded_query_rows(
            connection,
            """
            SELECT type, name
            FROM sqlite_schema
            WHERE type IN ('table', 'index', 'view', 'trigger')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY type, name
            LIMIT ?
            """,
            (maximum_objects,),
            maximum_objects,
            error_class=SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID,
        )
    except sqlite3.Error as exc:
        raise _validation_sqlite_state_error(exc, SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID) from None
    if any(
        type(row) is not tuple
        or len(row) != 2
        or type(row[0]) is not str
        or type(row[1]) is not str
        for row in rows
    ):
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    return {(row[0], row[1]) for row in rows}


def _user_tables(connection: sqlite3.Connection) -> set[str]:
    maximum_tables = len(EXPECTED_TABLES) + 1
    rows = _bounded_query_rows(
        connection,
        """
        SELECT name
        FROM sqlite_schema
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        LIMIT ?
        """,
        (maximum_tables,),
        maximum_tables,
        error_class=SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID,
    )
    if any(type(row) is not tuple or len(row) != 1 or type(row[0]) is not str for row in rows):
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    return {row[0] for row in rows}


def _validate_migration_history(
    connection: sqlite3.Connection,
    catalog: MigrationCatalog,
) -> tuple[_MigrationHistoryRow, ...]:
    """Compatibility wrapper for exact current-catalog history validation."""

    history = _read_validated_migration_history(connection, catalog)
    terminal = history[-1]
    if terminal.min_app_schema > CURRENT_APPLICATION_SCHEMA:
        raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW)
    if terminal.max_app_schema < CURRENT_APPLICATION_SCHEMA:
        raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE)
    return history


def _read_validated_migration_history(
    connection: sqlite3.Connection,
    catalog: MigrationCatalog,
) -> tuple[_MigrationHistoryRow, ...]:
    """Read and validate at most the catalog tip plus one history row."""

    limit = catalog.latest_sequence + 1
    rows = _bounded_query_rows(
        connection,
        """
        SELECT migration_id, sequence, schema_digest, applied_at, min_app_schema, max_app_schema
        FROM schema_migrations
        ORDER BY sequence, migration_id
        LIMIT ?
        """,
        (limit,),
        limit,
        error_class=SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID,
    )
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
        if row.sequence > catalog.latest_sequence:
            raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW)
        if row.sequence != index:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_GAP)
        migration = catalog.by_sequence(row.sequence)
        if migration is None:
            raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW)
        if row.migration_id != migration.migration_id:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
        if row.schema_digest != migration.checksum:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_CHECKSUM_MISMATCH)
        if row.min_app_schema != migration.min_app_schema or row.max_app_schema != migration.max_app_schema:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    return history


def _history_row(row: Iterable[Any]) -> _MigrationHistoryRow:
    if type(row) is not tuple:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    values = tuple(row)
    if len(values) != 6:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    migration_id, sequence, schema_digest, applied_at, min_app_schema, max_app_schema = values
    if type(migration_id) is not str or type(schema_digest) is not str or type(applied_at) is not str:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    if type(sequence) is not int or type(min_app_schema) is not int or type(max_app_schema) is not int:
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


def _migration_statements(sql_text: str) -> tuple[str, ...]:
    if type(sql_text) is not str:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    statements: list[str] = []
    pending: list[str] = []
    for character in sql_text:
        pending.append(character)
        if character != ";":
            continue
        candidate = "".join(pending)
        if sqlite3.complete_statement(candidate):
            statement = candidate.strip()
            if statement:
                _validate_migration_statement(statement)
                statements.append(statement)
            pending = []
    if "".join(pending).strip() or not statements:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    return tuple(statements)


_PROHIBITED_MIGRATION_KEYWORDS = frozenset(
    {
        "BEGIN",
        "COMMIT",
        "END",
        "ROLLBACK",
        "SAVEPOINT",
        "RELEASE",
        "PRAGMA",
        "ATTACH",
        "DETACH",
        "VACUUM",
    }
)


def _validate_migration_statement(statement: str) -> None:
    keyword = _top_level_sql_keyword(statement)
    if keyword is None or keyword in _PROHIBITED_MIGRATION_KEYWORDS:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)


def _top_level_sql_keyword(statement: str) -> str | None:
    offset = 0
    length = len(statement)
    while offset < length:
        while offset < length and statement[offset].isspace():
            offset += 1
        if statement.startswith("--", offset):
            newline = statement.find("\n", offset + 2)
            if newline < 0:
                return None
            offset = newline + 1
            continue
        if statement.startswith("/*", offset):
            end = statement.find("*/", offset + 2)
            if end < 0:
                raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
            offset = end + 2
            continue
        break
    match = re.match(r"[A-Za-z]+", statement[offset:])
    return match.group(0).upper() if match is not None else None


def _validate_selected_suffix(suffix: tuple[MigrationDefinition, ...]) -> None:
    if type(suffix) is not tuple:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    previous_sequence: int | None = None
    for migration in suffix:
        definition_invalid = False
        try:
            _validate_migration_definition(migration)
        except SQLiteStateError:
            definition_invalid = True
        if definition_invalid:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
        if previous_sequence is not None and migration.sequence != previous_sequence + 1:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
        if migration.destructive:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
        _migration_statements(migration.sql_text)
        previous_sequence = migration.sequence


def _require_sqlite_runtime_for_selected_migrations(
    migrations: tuple[MigrationDefinition, ...],
) -> None:
    if type(migrations) is not tuple:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    if any(migration.migration_id == _C2B2_MIGRATION_ID for migration in migrations):
        _require_sqlite_strict_runtime()


def _require_sqlite_runtime_for_administrative_catalog_target(
    catalog: MigrationCatalog,
) -> None:
    """Gate the maximum catalog capability before an administrative effect."""

    if type(catalog) is not MigrationCatalog:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    _require_sqlite_runtime_for_selected_migrations(catalog.migrations)


def _require_sqlite_runtime_for_schema_prefix(
    catalog: MigrationCatalog,
    sequence: int,
) -> None:
    if type(catalog) is not MigrationCatalog or type(sequence) is not int:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    _require_sqlite_runtime_for_selected_migrations(catalog.migrations[:sequence])


def _require_sqlite_strict_runtime() -> None:
    version = sqlite3.sqlite_version_info
    if (
        type(version) is not tuple
        or len(version) != 3
        or any(type(component) is not int or component < 0 for component in version)
        or version < _SQLITE_STRICT_MINIMUM_VERSION
    ):
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)


def _validate_catalog_statement_plans(catalog: MigrationCatalog) -> None:
    if type(catalog) is not MigrationCatalog:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    for migration in catalog.migrations:
        definition_invalid = False
        try:
            _validate_migration_definition(migration)
            _migration_statements(migration.sql_text)
        except SQLiteStateError:
            definition_invalid = True
        if definition_invalid:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)


def _require_application_schema(current_app_schema: int) -> None:
    if type(current_app_schema) is not int or current_app_schema < 0:
        raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE)


def _require_catalog_terminal_compatibility(
    catalog: MigrationCatalog,
    current_app_schema: int,
) -> None:
    terminal = _required_migration(catalog, catalog.latest_sequence)
    if terminal.min_app_schema > current_app_schema:
        raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW)
    if terminal.max_app_schema < current_app_schema:
        raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE)


def _migration_plan(
    *,
    prior_history: tuple[_MigrationHistoryRow, ...],
    suffix: tuple[MigrationDefinition, ...],
    fresh_install: bool,
    verify_managed_invariants: bool,
) -> _MigrationPlan:
    if type(prior_history) is not tuple or type(suffix) is not tuple or not suffix:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    if type(fresh_install) is not bool or type(verify_managed_invariants) is not bool:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    if fresh_install is not (len(prior_history) == 0):
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    _validate_selected_suffix(suffix)
    expected_first = len(prior_history) + 1
    if suffix[0].sequence != expected_first:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    for index, row in enumerate(prior_history, start=1):
        if type(row) is not _MigrationHistoryRow or row.sequence != index:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    applied_at = _utc_now()
    _verify_timestamp(applied_at, SQLiteStateErrorCode.MIGRATION_FAILED)
    return _MigrationPlan(
        prior_history=prior_history,
        suffix=suffix,
        target_sequence=suffix[-1].sequence,
        applied_at=applied_at,
        fresh_install=fresh_install,
        verify_managed_invariants=verify_managed_invariants,
    )


def _planned_history(plan: _MigrationPlan) -> tuple[_MigrationHistoryRow, ...]:
    appended = tuple(
        _MigrationHistoryRow(
            migration_id=migration.migration_id,
            sequence=migration.sequence,
            schema_digest=migration.checksum,
            applied_at=plan.applied_at,
            min_app_schema=migration.min_app_schema,
            max_app_schema=migration.max_app_schema,
        )
        for migration in plan.suffix
    )
    return plan.prior_history + appended


def _run_bound_migration_plan(
    authority_lock: Any,
    binding: Any,
    catalog: MigrationCatalog,
    plan: _MigrationPlan,
    *,
    current_app_schema: int,
) -> DatabaseInspection:
    _validate_plan_against_catalog(catalog, plan)
    phase = _MigrationTransactionPhase.NEW
    connection: sqlite3.Connection | None = None
    completed_history = _planned_history(plan)
    pending_error: SQLiteStateErrorCode | None = None
    pending_recovery: _MigrationRecoveryResult | None = None
    try:
        connection = _open_bound_existing_sqlite_connection(binding, read_only=False)
        apply_connection_posture(connection)
        connection.execute("BEGIN IMMEDIATE")
        if connection.in_transaction is not True:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
        phase = _MigrationTransactionPhase.TRANSACTION_ACTIVE
        _validate_migration_binding(authority_lock, binding)
        _revalidate_plan_opening_state(
            connection,
            catalog,
            plan,
            current_app_schema=current_app_schema,
        )
        for offset, migration in enumerate(plan.suffix, start=1):
            _apply_migration_definition_in_transaction(connection, migration)
            _insert_migration_row(connection, migration, applied_at=plan.applied_at)
            expected_history = completed_history[: len(plan.prior_history) + offset]
            if _read_validated_migration_history(connection, catalog) != expected_history:
                raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
            _verify_schema_for_sequence(
                connection,
                catalog,
                migration.sequence,
                verify_managed_invariants=plan.verify_managed_invariants,
                fresh_install=plan.fresh_install,
            )
            _verify_applied_migration_zero_seed_invariants(
                connection,
                migration,
                fresh_install=plan.fresh_install,
                verify_managed_invariants=plan.verify_managed_invariants,
            )
            if connection.in_transaction is not True:
                raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
        if _read_validated_migration_history(connection, catalog) != completed_history:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
        _verify_schema_for_sequence(
            connection,
            catalog,
            plan.target_sequence,
            verify_managed_invariants=plan.verify_managed_invariants,
            fresh_install=plan.fresh_install,
        )
        terminal = completed_history[-1]
        if terminal.min_app_schema > current_app_schema:
            raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW)
        if terminal.max_app_schema < current_app_schema:
            raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE)
        _validate_migration_binding(authority_lock, binding)
        phase = _MigrationTransactionPhase.COMMIT_ATTEMPTED
        _attempt_migration_commit(connection)
        phase = _MigrationTransactionPhase.COMMIT_RETURNED
    except Exception as exc:
        if phase in {
            _MigrationTransactionPhase.COMMIT_ATTEMPTED,
            _MigrationTransactionPhase.COMMIT_RETURNED,
        }:
            _abandon_migration_connection(connection)
            connection = None
            phase = _MigrationTransactionPhase.RECOVERING
            pending_recovery = _recover_migration_outcome(
                binding,
                catalog,
                plan,
                current_app_schema=current_app_schema,
            )
        else:
            rollback_succeeded = _rollback_migration_connection(connection)
            close_succeeded = _close_migration_connection_safely(connection)
            connection = None
            if rollback_succeeded and close_succeeded:
                pending_error = _safe_state_error_code(exc)
            else:
                phase = _MigrationTransactionPhase.RECOVERING
                recovery = _recover_migration_outcome(
                    binding,
                    catalog,
                    plan,
                    current_app_schema=current_app_schema,
                )
                if recovery.evidence is _MigrationCommitEvidence.DEFINITELY_NOT_COMMITTED:
                    pending_error = _safe_state_error_code(exc)
                else:
                    pending_recovery = recovery
    if pending_error is not None:
        raise SQLiteStateError(pending_error)
    if pending_recovery is not None:
        return _resolve_migration_recovery_result(pending_recovery, catalog, plan)
    close_recovery: _MigrationRecoveryResult | None = None
    try:
        _close_migration_connection(connection)
        connection = None
        phase = _MigrationTransactionPhase.CLOSED
    except Exception:
        _abandon_migration_connection(connection)
        connection = None
        phase = _MigrationTransactionPhase.RECOVERING
        close_recovery = _recover_migration_outcome(
            binding,
            catalog,
            plan,
            current_app_schema=current_app_schema,
        )
    if close_recovery is not None:
        return _resolve_migration_recovery_result(close_recovery, catalog, plan)
    return _successful_plan_inspection(catalog, plan)


def _validate_plan_against_catalog(
    catalog: MigrationCatalog,
    plan: _MigrationPlan,
) -> None:
    if type(catalog) is not MigrationCatalog or type(plan) is not _MigrationPlan:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    if (
        type(plan.prior_history) is not tuple
        or type(plan.suffix) is not tuple
        or not plan.suffix
        or type(plan.target_sequence) is not int
        or type(plan.applied_at) is not str
        or type(plan.fresh_install) is not bool
        or type(plan.verify_managed_invariants) is not bool
    ):
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    _verify_timestamp(plan.applied_at, SQLiteStateErrorCode.MIGRATION_FAILED)
    if (
        plan.fresh_install is not (len(plan.prior_history) == 0)
        or plan.target_sequence != catalog.latest_sequence
        or plan.suffix != catalog.migrations[len(plan.prior_history) :]
    ):
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    _validate_selected_suffix(plan.suffix)
    for expected_sequence, row in enumerate(plan.prior_history, start=1):
        if type(row) is not _MigrationHistoryRow or row.sequence != expected_sequence:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
        migration = catalog.by_sequence(expected_sequence)
        if migration is None or (
            row.migration_id,
            row.sequence,
            row.schema_digest,
            row.min_app_schema,
            row.max_app_schema,
        ) != (
            migration.migration_id,
            migration.sequence,
            migration.checksum,
            migration.min_app_schema,
            migration.max_app_schema,
        ):
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
        _verify_timestamp(row.applied_at, SQLiteStateErrorCode.MIGRATION_FAILED)


def _revalidate_plan_opening_state(
    connection: sqlite3.Connection,
    catalog: MigrationCatalog,
    plan: _MigrationPlan,
    *,
    current_app_schema: int,
) -> None:
    objects = _user_schema_objects(connection, catalog=catalog)
    if not plan.prior_history:
        if objects:
            raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_NOT_EMPTY_UNMANAGED)
        return
    history = _read_validated_migration_history(connection, catalog)
    if history != plan.prior_history:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_INVALID)
    terminal = history[-1]
    _verify_schema_for_sequence(
        connection,
        catalog,
        terminal.sequence,
        verify_managed_invariants=plan.verify_managed_invariants,
        fresh_install=False,
    )
    target = _required_migration(catalog, catalog.latest_sequence)
    if target.min_app_schema > current_app_schema:
        raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW)
    if target.max_app_schema < current_app_schema:
        raise SQLiteStateError(SQLiteStateErrorCode.DATABASE_SCHEMA_INCOMPATIBLE)


def _apply_migration_definition_in_transaction(
    connection: sqlite3.Connection,
    migration: MigrationDefinition,
) -> None:
    try:
        for statement in _migration_statements(migration.sql_text):
            _execute_migration_statement(connection, statement)
    except SQLiteStateError:
        raise
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED) from None


def _execute_migration_statement(
    connection: sqlite3.Connection,
    statement: str,
) -> None:
    try:
        connection.execute(statement)
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED) from None
    if connection.in_transaction is not True:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)


def _validate_migration_binding(authority_lock: Any, binding: Any) -> None:
    try:
        authority_lock._validate_state_database_authority_binding(binding)
    except Exception:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED) from None


def _attempt_migration_commit(connection: sqlite3.Connection) -> None:
    connection.execute("COMMIT")


def _close_migration_connection(connection: sqlite3.Connection | None) -> None:
    if connection is not None:
        connection.close()


def _abandon_migration_connection(connection: sqlite3.Connection | None) -> None:
    if connection is None:
        return
    try:
        _close_migration_connection(connection)
    except Exception:
        pass


def _rollback_migration_connection(connection: sqlite3.Connection | None) -> bool:
    if connection is None:
        return True
    try:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        return connection.in_transaction is False
    except Exception:
        return False


def _close_migration_connection_safely(connection: sqlite3.Connection | None) -> bool:
    try:
        _close_migration_connection(connection)
        return True
    except Exception:
        return False


def _safe_state_error_code(error: Exception) -> SQLiteStateErrorCode:
    if isinstance(error, SQLiteStateError):
        try:
            return SQLiteStateErrorCode(error.error_class)
        except ValueError:
            return SQLiteStateErrorCode.MIGRATION_FAILED
    return SQLiteStateErrorCode.MIGRATION_FAILED


def _resolve_migration_recovery(
    binding: Any,
    catalog: MigrationCatalog,
    plan: _MigrationPlan,
    *,
    current_app_schema: int,
) -> DatabaseInspection:
    result = _recover_migration_outcome(
        binding,
        catalog,
        plan,
        current_app_schema=current_app_schema,
    )
    return _resolve_migration_recovery_result(result, catalog, plan)


def _resolve_migration_recovery_result(
    result: _MigrationRecoveryResult,
    catalog: MigrationCatalog,
    plan: _MigrationPlan,
) -> DatabaseInspection:
    if result.evidence is _MigrationCommitEvidence.COMMITTED_EXACT:
        return _successful_plan_inspection(catalog, plan)
    if result.evidence is _MigrationCommitEvidence.DEFINITELY_NOT_COMMITTED:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_OUTCOME_UNRESOLVED)


def _successful_plan_inspection(
    catalog: MigrationCatalog,
    plan: _MigrationPlan,
) -> DatabaseInspection:
    return DatabaseInspection(
        classification=DatabaseClassification.MANAGED,
        current_sequence=plan.target_sequence,
        latest_sequence=catalog.latest_sequence,
        current_migration_id=plan.suffix[-1].migration_id,
    )


def _recover_migration_outcome(
    binding: Any,
    catalog: MigrationCatalog,
    plan: _MigrationPlan,
    *,
    current_app_schema: int,
) -> _MigrationRecoveryResult:
    connection: sqlite3.Connection | None = None
    result = _MigrationRecoveryResult(_MigrationCommitEvidence.UNRESOLVED)
    try:
        connection = _open_bound_existing_sqlite_connection(binding, read_only=True)
        objects = _user_schema_objects(connection, catalog=catalog)
        if not objects:
            if not plan.prior_history:
                result = _MigrationRecoveryResult(
                    _MigrationCommitEvidence.DEFINITELY_NOT_COMMITTED
                )
        elif ("table", "schema_migrations") in objects:
            history = _read_validated_migration_history(connection, catalog)
            intended = _planned_history(plan)
            if history == intended:
                _verify_schema_for_sequence(
                    connection,
                    catalog,
                    plan.target_sequence,
                    verify_managed_invariants=plan.verify_managed_invariants,
                    fresh_install=plan.fresh_install,
                )
                for migration in plan.suffix:
                    _verify_applied_migration_zero_seed_invariants(
                        connection,
                        migration,
                        fresh_install=plan.fresh_install,
                        verify_managed_invariants=plan.verify_managed_invariants,
                    )
                terminal = history[-1]
                if terminal.min_app_schema <= current_app_schema <= terminal.max_app_schema:
                    result = _MigrationRecoveryResult(
                        _MigrationCommitEvidence.COMMITTED_EXACT
                    )
            elif history == plan.prior_history and plan.prior_history:
                _verify_schema_for_sequence(
                    connection,
                    catalog,
                    len(plan.prior_history),
                    verify_managed_invariants=plan.verify_managed_invariants,
                    fresh_install=False,
                )
                result = _MigrationRecoveryResult(
                    _MigrationCommitEvidence.DEFINITELY_NOT_COMMITTED
                )
    except Exception:
        result = _MigrationRecoveryResult(_MigrationCommitEvidence.UNRESOLVED)
    if not _close_migration_connection_safely(connection):
        return _MigrationRecoveryResult(_MigrationCommitEvidence.UNRESOLVED)
    return result


def _verify_schema_for_sequence(
    connection: sqlite3.Connection,
    catalog: MigrationCatalog,
    sequence: int,
    *,
    verify_managed_invariants: bool,
    fresh_install: bool,
) -> None:
    if (
        type(sequence) is not int
        or sequence < 0
        or sequence > catalog.latest_sequence
        or type(fresh_install) is not bool
    ):
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    expected_manifest = _expected_schema_manifest_for_sequence(catalog, sequence)
    _verify_live_schema_manifest(connection, expected_manifest)
    if sequence == 0:
        return
    if verify_managed_invariants:
        _verify_managed_state_invariants(connection)
    _verify_foreign_key_posture(connection)


def _expected_schema_manifest_for_sequence(
    catalog: MigrationCatalog,
    sequence: int,
) -> tuple[Any, ...]:
    if type(catalog) is not MigrationCatalog or type(sequence) is not int:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    if sequence < 0 or sequence > catalog.latest_sequence:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    _require_sqlite_runtime_for_schema_prefix(catalog, sequence)
    connection: sqlite3.Connection | None = None
    manifest: tuple[Any, ...] | None = None
    pending_error: SQLiteStateErrorCode | None = None
    try:
        try:
            connection = sqlite3.connect(":memory:", isolation_level=None)
            apply_observational_connection_posture(connection)
            connection.execute("BEGIN IMMEDIATE")
            for migration in catalog.migrations[:sequence]:
                for statement in _migration_statements(migration.sql_text):
                    connection.execute(statement)
                    if connection.in_transaction is not True:
                        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
            manifest = _schema_manifest(connection)
            connection.execute("ROLLBACK")
        except SQLiteStateError as exc:
            pending_error = _safe_state_error_code(exc)
        except sqlite3.Error:
            pending_error = SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED
    finally:
        if connection is not None:
            close_failed = False
            try:
                connection.close()
            except sqlite3.Error:
                close_failed = True
            connection = None
            if close_failed:
                pending_error = SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED
    if pending_error is not None:
        raise SQLiteStateError(pending_error)
    if manifest is None:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    return manifest


def _verify_live_schema_manifest(
    connection: sqlite3.Connection,
    expected_manifest: tuple[Any, ...],
) -> None:
    expected_schema = tuple(item for item in expected_manifest if item[0] == "schema")
    schema_limit = len(expected_schema) + 1
    schema_rows = _bounded_query_rows(
        connection,
        """
        SELECT type, name, tbl_name, sql
        FROM sqlite_schema
        WHERE type IN ('table', 'index', 'view', 'trigger')
          AND name NOT LIKE 'sqlite_%'
        ORDER BY type, name
        LIMIT ?
        """,
        (schema_limit,),
        schema_limit,
        error_class=SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED,
    )
    if any(
        len(row) != 4
        or type(row[0]) is not str
        or type(row[1]) is not str
        or type(row[2]) is not str
        or (row[3] is not None and type(row[3]) is not str)
        for row in schema_rows
    ):
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    actual_schema = tuple(
        (
            "schema",
            str(object_type),
            str(name),
            str(table_name),
            _normalize_schema_sql(sql),
        )
        for object_type, name, table_name, sql in schema_rows
    )
    if actual_schema != expected_schema:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_FINGERPRINT_MISMATCH)

    for expected_item in expected_manifest[len(expected_schema) :]:
        kind = expected_item[0]
        if kind == "table_xinfo" and len(expected_item) == 3:
            statement = f"PRAGMA table_xinfo({_quote_identifier(expected_item[1])})"
            actual_rows = _bounded_pragma_rows(
                connection,
                statement,
                expected_rows=expected_item[2],
            )
            actual_item = (kind, expected_item[1], actual_rows)
        elif kind == "foreign_key_list" and len(expected_item) == 3:
            statement = f"PRAGMA foreign_key_list({_quote_identifier(expected_item[1])})"
            actual_rows = _bounded_pragma_rows(
                connection,
                statement,
                expected_rows=expected_item[2],
            )
            actual_item = (kind, expected_item[1], actual_rows)
        elif kind == "index_list" and len(expected_item) == 3:
            statement = f"PRAGMA index_list({_quote_identifier(expected_item[1])})"
            actual_rows = _bounded_pragma_rows(
                connection,
                statement,
                expected_rows=expected_item[2],
            )
            actual_item = (kind, expected_item[1], actual_rows)
        elif kind == "index_xinfo" and len(expected_item) == 4:
            statement = f"PRAGMA index_xinfo({_quote_identifier(expected_item[2])})"
            actual_rows = _bounded_pragma_rows(
                connection,
                statement,
                expected_rows=expected_item[3],
            )
            actual_item = (kind, expected_item[1], expected_item[2], actual_rows)
        else:
            raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
        if actual_item != expected_item:
            raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_FINGERPRINT_MISMATCH)


def _bounded_pragma_rows(
    connection: sqlite3.Connection,
    statement: str,
    *,
    expected_rows: tuple[tuple[Any, ...], ...],
) -> tuple[tuple[Any, ...], ...]:
    limit = len(expected_rows) + 1
    return _bounded_query_rows(
        connection,
        statement,
        (),
        limit,
        error_class=SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED,
    )


def _bounded_query_rows(
    connection: sqlite3.Connection,
    statement: str,
    parameters: tuple[Any, ...],
    limit: int,
    *,
    error_class: SQLiteStateErrorCode,
) -> tuple[tuple[Any, ...], ...]:
    if type(limit) is not int or limit < 1:
        raise SQLiteStateError(error_class)
    cursor: sqlite3.Cursor | None = None
    rows: Any = None
    try:
        cursor = connection.execute(statement, parameters)
        rows = cursor.fetchmany(limit)
    except sqlite3.Error as exc:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        raise _validation_sqlite_state_error(exc, error_class) from None
    except Exception:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        raise SQLiteStateError(error_class) from None
    try:
        cursor.close()
    except Exception:
        raise SQLiteStateError(error_class) from None
    if type(rows) is not list or len(rows) > limit:
        raise SQLiteStateError(error_class)
    if any(type(row) is not tuple for row in rows):
        raise SQLiteStateError(error_class)
    return tuple(rows)


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
    except sqlite3.Error as exc:
        raise _validation_sqlite_state_error(exc, SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
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
    except sqlite3.Error as exc:
        raise _validation_sqlite_state_error(exc, SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None


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
    except sqlite3.Error as exc:
        raise _validation_sqlite_state_error(exc, SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
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


def _verify_applied_migration_zero_seed_invariants(
    connection: sqlite3.Connection,
    migration: MigrationDefinition,
    *,
    fresh_install: bool,
    verify_managed_invariants: bool,
) -> None:
    if (
        type(migration) is not MigrationDefinition
        or type(fresh_install) is not bool
        or type(verify_managed_invariants) is not bool
    ):
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    if not verify_managed_invariants:
        return
    if fresh_install and migration.migration_id == "0001_initial":
        _verify_global_stop_clear_seed(connection)
        _verify_empty_bootstrap_tables(connection)
    if migration.migration_id == _C2B2_MIGRATION_ID:
        _verify_empty_c2b2_migration_tables(connection)
    if migration.migration_id == _SECTION41_MIGRATION_ID:
        _verify_empty_section41_migration_tables(connection)


def _verify_empty_bootstrap_tables(connection: sqlite3.Connection) -> None:
    _verify_empty_tables(connection, EMPTY_AFTER_BOOTSTRAP_TABLES)


def _verify_empty_c2b2_migration_tables(connection: sqlite3.Connection) -> None:
    _verify_empty_tables(connection, _EMPTY_AFTER_C2B2_MIGRATION_TABLES)


def _verify_empty_section41_migration_tables(connection: sqlite3.Connection) -> None:
    _verify_empty_tables(connection, _EMPTY_AFTER_SECTION41_MIGRATION_TABLES)


def _verify_empty_tables(
    connection: sqlite3.Connection,
    table_names: frozenset[str],
) -> None:
    if type(table_names) is not frozenset or any(type(name) is not str for name in table_names):
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)
    for table_name in table_names:
        try:
            count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        except sqlite3.Error as exc:
            raise _validation_sqlite_state_error(exc, SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
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
    except sqlite3.Error as exc:
        raise _validation_sqlite_state_error(exc, SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
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
    except sqlite3.Error as exc:
        raise _validation_sqlite_state_error(exc, SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
    try:
        _parse_writer_ownership_rows(rows)
    except ValueError:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)


def _verify_foreign_key_posture(connection: sqlite3.Connection) -> None:
    try:
        row = connection.execute("PRAGMA foreign_keys").fetchone()
    except sqlite3.Error as exc:
        raise _validation_sqlite_state_error(exc, SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED) from None
    if row is None or int(row[0]) != 1:
        raise SQLiteStateError(SQLiteStateErrorCode.SCHEMA_VERIFICATION_FAILED)


def _insert_migration_row(
    connection: sqlite3.Connection,
    migration: MigrationDefinition,
    *,
    applied_at: str,
) -> None:
    _verify_timestamp(applied_at, SQLiteStateErrorCode.MIGRATION_FAILED)
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
                applied_at,
                migration.min_app_schema,
                migration.max_app_schema,
            ),
        )
        if connection.in_transaction is not True:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
    except SQLiteStateError:
        raise
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED) from None


def _required_migration(catalog: MigrationCatalog, sequence: int) -> MigrationDefinition:
    migration = catalog.by_sequence(sequence)
    if migration is None:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_GAP)
    return migration


def _verify_timestamp(value: Any, error_class: SQLiteStateErrorCode) -> None:
    if type(value) is not str or RFC3339_UTC_Z.fullmatch(value) is None:
        raise SQLiteStateError(error_class)
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise SQLiteStateError(error_class) from None


def _bounded_text(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 96


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0




def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
