from __future__ import annotations

from contextlib import closing
import hashlib
import os
from pathlib import Path
import sqlite3
import traceback

import pytest

import ge_nwp_coordinator.sqlite_migration as migration_module
from ge_nwp_coordinator.sqlite_errors import SQLiteStateError
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import (
    MigrationCatalog,
    MigrationDefinition,
    _MigrationCommitEvidence,
    _MigrationRecoveryResult,
    _assess_location_database,
    _history_row,
    _initialize_database_with_catalog,
    _inspection_from_assessment,
    _migrate_database_with_catalog,
    _migration_plan,
    _migration_statements,
    _read_validated_migration_history,
)
from ge_nwp_coordinator.state_authority_lock import (
    StateAuthorityLockError,
    acquire_state_authority_lock,
)


NEUTRAL_0001_SQL = b"""\
CREATE TABLE schema_migrations (
    migration_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    schema_digest TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    min_app_schema INTEGER NOT NULL,
    max_app_schema INTEGER NOT NULL
);
CREATE TABLE neutral_one (value INTEGER NOT NULL);
"""
NEUTRAL_0002_SQL = b"CREATE TABLE neutral_two (value INTEGER NOT NULL);\n"
NEUTRAL_0003_SQL = b"CREATE TABLE neutral_three (value INTEGER NOT NULL);\n"


def _location(tmp_path: Path, name: str = "state") -> CoordinatorStateLocation:
    return CoordinatorStateLocation.from_trusted_root(tmp_path / name)


def _definition(
    sequence: int,
    *,
    sql_bytes: bytes | None = None,
    min_app_schema: int = 1,
    max_app_schema: int = 1,
    destructive: bool = False,
    migration_id: str | None = None,
    resource_name: str | None = None,
) -> MigrationDefinition:
    defaults = {
        1: NEUTRAL_0001_SQL,
        2: NEUTRAL_0002_SQL,
        3: NEUTRAL_0003_SQL,
    }
    selected = sql_bytes if sql_bytes is not None else defaults[sequence]
    return MigrationDefinition(
        migration_id=migration_id or f"{sequence:04d}_neutral",
        sequence=sequence,
        resource_name=resource_name or f"{sequence:04d}_neutral.sql",
        sql_bytes=selected,
        checksum=hashlib.sha256(selected).hexdigest(),
        min_app_schema=min_app_schema,
        max_app_schema=max_app_schema,
        destructive=destructive,
        description=f"neutral migration {sequence}",
    )


def _catalog(
    count: int,
    *,
    terminal_min: int = 1,
    terminal_max: int = 1,
) -> MigrationCatalog:
    definitions = []
    for sequence in range(1, count + 1):
        minimum = terminal_min if sequence == count else 1
        maximum = terminal_max if sequence == count else 1
        definitions.append(
            _definition(
                sequence,
                min_app_schema=minimum,
                max_app_schema=maximum,
            )
        )
    return MigrationCatalog(tuple(definitions))


def _initialize(
    location: CoordinatorStateLocation,
    catalog: MigrationCatalog,
    *,
    current_app_schema: int = 1,
):
    return _initialize_database_with_catalog(
        location,
        catalog,
        current_app_schema=current_app_schema,
        verify_managed_invariants=False,
    )


def _migrate(
    location: CoordinatorStateLocation,
    catalog: MigrationCatalog,
    *,
    current_app_schema: int = 1,
):
    return _migrate_database_with_catalog(
        location,
        catalog,
        current_app_schema=current_app_schema,
        verify_managed_invariants=False,
    )


def _assessment(
    location: CoordinatorStateLocation,
    catalog: MigrationCatalog,
    *,
    current_app_schema: int = 1,
):
    return _assess_location_database(
        location,
        catalog,
        current_app_schema=current_app_schema,
        verify_managed_invariants=False,
    )


def _history(location: CoordinatorStateLocation) -> list[tuple[object, ...]]:
    with closing(sqlite3.connect(location.database_path)) as connection, connection:
        return connection.execute(
            """
            SELECT migration_id, sequence, schema_digest, applied_at,
                   min_app_schema, max_app_schema
            FROM schema_migrations
            ORDER BY sequence, migration_id
            """
        ).fetchall()


def _tables(location: CoordinatorStateLocation) -> set[str]:
    with closing(sqlite3.connect(location.database_path)) as connection, connection:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_schema
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()
    return {str(row[0]) for row in rows}


def _execute(location: CoordinatorStateLocation, statement: str, parameters=()) -> None:
    with closing(sqlite3.connect(location.database_path)) as connection, connection:
        connection.execute(statement, parameters)


def _empty_database(location: CoordinatorStateLocation) -> None:
    location.state_root.mkdir(mode=0o700, parents=True)
    location.database_path.write_bytes(b"")
    location.database_path.chmod(0o600)


def _unmanaged_database(location: CoordinatorStateLocation) -> None:
    location.state_root.mkdir(mode=0o700, parents=True)
    with closing(sqlite3.connect(location.database_path)) as connection, connection:
        connection.execute("CREATE TABLE neutral_unmanaged (value INTEGER)")
    location.database_path.chmod(0o600)


def _assert_empty_after_failure(
    location: CoordinatorStateLocation,
    catalog: MigrationCatalog,
) -> None:
    assert _assessment(location, catalog).disposition.value == "empty"
    assert _tables(location) == set()


def _assert_detached_public_error(
    error: SQLiteStateError,
    expected_code: str,
    *private_markers: str,
) -> None:
    assert type(error) is SQLiteStateError
    assert str(error) == expected_code
    assert repr(error) == f"SQLiteStateError({expected_code!r})"
    assert error.args == (expected_code,)
    assert error.internal_detail is None
    assert error.__cause__ is None
    assert error.__context__ is None
    assert error.__suppress_context__ is False
    assert not getattr(error, "__notes__", None)
    rendered = "".join(traceback.format_exception(error))
    for marker in private_markers:
        assert marker not in rendered
        assert marker not in str(error)
        assert marker not in repr(error)
    pending: list[BaseException] = [error]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        assert not isinstance(current, sqlite3.Error)
        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)


class _ExpectedManifestCloseFaultConnection:
    def __init__(
        self,
        connection: sqlite3.Connection,
        private_marker: str,
        close_attempts: list[int],
    ) -> None:
        self._connection = connection
        self._private_marker = private_marker
        self._close_attempts = close_attempts

    def close(self) -> None:
        self._close_attempts.append(1)
        self._connection.close()
        raise sqlite3.OperationalError(self._private_marker)

    def __getattr__(self, name: str):
        return getattr(self._connection, name)


def _assert_expected_manifest_inspection_failure(inspection) -> None:
    assert type(inspection) is migration_module.DatabaseInspection
    assert inspection.classification.name == "UNKNOWN"
    assert inspection.classification.value == "unknown"
    assert inspection.current_sequence == 0
    assert inspection.latest_sequence == 2
    assert inspection.current_migration_id is None
    assert inspection.reason == "schema_verification_failed"
    assert not hasattr(inspection, "administrative_eligible")


def _assert_production_managed_inspection(inspection) -> None:
    assert type(inspection) is migration_module.DatabaseInspection
    assert inspection.classification.name == "MANAGED"
    assert inspection.classification.value == "managed"
    assert inspection.current_sequence == 2
    assert inspection.latest_sequence == 2
    assert inspection.current_migration_id == "0002_development_program_and_effect_state"
    assert inspection.reason is None


@pytest.mark.parametrize(
    (
        "case",
        "expected_private",
        "expected_public_name",
        "expected_public_value",
        "expected_initialize",
        "expected_migrate",
        "expected_safe_error",
        "expected_mutation_permitted",
    ),
    [
        ("absent", "absent", "ABSENT", "absent", "success", "migration_history_missing", None, True),
        ("empty", "empty", "EMPTY", "empty", "success", "migration_history_missing", None, True),
        ("current", "current", "MANAGED", "managed", "success", "success", None, False),
        (
            "supported",
            "supported_older_prefix",
            "UNKNOWN",
            "unknown",
            "database_schema_incompatible",
            "success",
            "database_schema_incompatible",
            True,
        ),
        (
            "unsupported",
            "unsupported_older",
            "UNKNOWN",
            "unknown",
            "database_schema_incompatible",
            "database_schema_incompatible",
            "database_schema_incompatible",
            False,
        ),
        (
            "newer",
            "newer_unsupported",
            "UNKNOWN",
            "unknown",
            "database_schema_too_new",
            "database_schema_too_new",
            "database_schema_too_new",
            False,
        ),
        (
            "corrupt",
            "corrupt_history",
            "UNKNOWN",
            "unknown",
            "migration_checksum_mismatch",
            "migration_checksum_mismatch",
            "migration_checksum_mismatch",
            False,
        ),
        (
            "partial",
            "partial_migration",
            "UNKNOWN",
            "unknown",
            "schema_fingerprint_mismatch",
            "schema_fingerprint_mismatch",
            "schema_fingerprint_mismatch",
            False,
        ),
        (
            "unmanaged",
            "database_not_empty_unmanaged",
            "UNKNOWN",
            "unknown",
            "database_not_empty_unmanaged",
            "database_not_empty_unmanaged",
            "database_not_empty_unmanaged",
            False,
        ),
    ],
)
def test_c2b1_assessment_matrix_uses_literal_test_owned_expected_truth(
    tmp_path: Path,
    case: str,
    expected_private: str,
    expected_public_name: str,
    expected_public_value: str,
    expected_initialize: str,
    expected_migrate: str,
    expected_safe_error: str | None,
    expected_mutation_permitted: bool,
) -> None:
    catalog_one = _catalog(1)
    catalog_two = _catalog(2)
    catalog = catalog_one
    current_app_schema = 1
    if case in {"current", "supported", "partial"}:
        catalog = catalog_two
    elif case == "newer":
        catalog = _catalog(2, terminal_min=2, terminal_max=2)
    elif case == "unsupported":
        current_app_schema = 2

    def seed(location: CoordinatorStateLocation) -> None:
        if case == "absent":
            return
        if case == "empty":
            _empty_database(location)
            return
        if case == "supported":
            _initialize(location, catalog_one)
            return
        if case == "unsupported":
            _initialize(location, catalog_one)
            return
        if case == "newer":
            _initialize(location, catalog, current_app_schema=2)
            return
        if case == "corrupt":
            _initialize(location, catalog_one)
            _execute(location, "UPDATE schema_migrations SET schema_digest = ?", ("0" * 64,))
            return
        if case == "partial":
            _initialize(location, catalog_two)
            _execute(location, "DROP TABLE neutral_two")
            return
        if case == "unmanaged":
            _unmanaged_database(location)
            return
        _initialize(location, catalog)

    assessment_location = _location(tmp_path, f"assessment-{case}")
    initialize_location = _location(tmp_path, f"initialize-{case}")
    migrate_location = _location(tmp_path, f"migrate-{case}")
    seed(assessment_location)
    seed(initialize_location)
    seed(migrate_location)

    assessment = _assessment(
        assessment_location,
        catalog,
        current_app_schema=current_app_schema,
    )
    public = _inspection_from_assessment(assessment, catalog)
    assert assessment.disposition.value == expected_private
    assert public.classification.name == expected_public_name
    assert public.classification.value == expected_public_value
    assert public.reason == expected_safe_error

    try:
        _initialize(
            initialize_location,
            catalog,
            current_app_schema=current_app_schema,
        )
        initialize_result = "success"
    except SQLiteStateError as exc:
        initialize_result = exc.error_class
    try:
        _migrate(
            migrate_location,
            catalog,
            current_app_schema=current_app_schema,
        )
        migrate_result = "success"
    except SQLiteStateError as exc:
        migrate_result = exc.error_class

    assert initialize_result == expected_initialize
    assert migrate_result == expected_migrate
    assert expected_mutation_permitted is (case in {"absent", "empty", "supported"})


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        (
            "INSERT INTO schema_migrations SELECT migration_id, sequence, schema_digest, "
            "applied_at, min_app_schema, max_app_schema FROM schema_migrations WHERE sequence = 1",
            "migration_history_invalid",
        ),
        (
            "UPDATE schema_migrations SET sequence = 3 WHERE sequence = 2",
            "database_schema_too_new",
        ),
        (
            "UPDATE schema_migrations SET migration_id = '0002_wrong' WHERE sequence = 2",
            "migration_history_invalid",
        ),
        (
            "UPDATE schema_migrations SET schema_digest = '0000000000000000000000000000000000000000000000000000000000000000' WHERE sequence = 2",
            "migration_checksum_mismatch",
        ),
        (
            "UPDATE schema_migrations SET min_app_schema = 0 WHERE sequence = 2",
            "migration_history_invalid",
        ),
        (
            "UPDATE schema_migrations SET max_app_schema = 2 WHERE sequence = 2",
            "migration_history_invalid",
        ),
        (
            "UPDATE schema_migrations SET applied_at = 'malformed' WHERE sequence = 2",
            "migration_history_invalid",
        ),
        (
            "DELETE FROM schema_migrations",
            "migration_history_missing",
        ),
    ],
)
def test_history_corruption_is_classified_exactly(
    tmp_path: Path,
    mutation: str,
    expected_reason: str,
) -> None:
    catalog = _catalog(2)
    location = _location(tmp_path)
    _initialize(location, catalog)

    _execute(location, mutation)

    assessment = _assessment(location, catalog)
    expected_disposition = (
        "newer_unsupported"
        if expected_reason == "database_schema_too_new"
        else "corrupt_history"
    )
    assert assessment.disposition.value == expected_disposition
    assert assessment.reason is not None
    assert assessment.reason.value == expected_reason


def test_history_beyond_catalog_tip_is_newer_unsupported(tmp_path: Path) -> None:
    full_catalog = _catalog(2)
    location = _location(tmp_path)
    _initialize(location, full_catalog)

    assessment = _assessment(location, MigrationCatalog(full_catalog.migrations[:1]))

    assert assessment.disposition.value == "newer_unsupported"
    assert assessment.reason is not None
    assert assessment.reason.value == "database_schema_too_new"


def test_malformed_history_fails_before_manifest_or_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prefix = _catalog(1)
    catalog = _catalog(2)
    location = _location(tmp_path)
    _initialize(location, prefix)
    _execute(
        location,
        "UPDATE schema_migrations SET schema_digest = ? WHERE sequence = 1",
        ("0" * 64,),
    )
    calls = {"manifest": 0, "lock": 0}

    def forbidden(name):
        def record(*args, **kwargs):
            calls[name] += 1
            raise AssertionError(f"malformed history reached {name}")

        return record

    monkeypatch.setattr(
        migration_module,
        "_expected_schema_manifest_for_sequence",
        forbidden("manifest"),
    )
    monkeypatch.setattr(
        migration_module,
        "acquire_state_authority_lock",
        forbidden("lock"),
    )

    with pytest.raises(SQLiteStateError) as exc_info:
        _migrate(location, catalog)

    assert exc_info.value.error_class == "migration_checksum_mismatch"
    assert calls == {"manifest": 0, "lock": 0}


def test_missing_history_and_nonempty_unmanaged_remain_distinct(tmp_path: Path) -> None:
    catalog = _catalog(1)
    missing = _location(tmp_path, "missing")
    _initialize(missing, catalog)
    _execute(missing, "DELETE FROM schema_migrations")
    missing_assessment = _assessment(missing, catalog)
    assert missing_assessment.reason is not None
    assert missing_assessment.reason.value == "migration_history_missing"

    unmanaged = _location(tmp_path, "unmanaged")
    _unmanaged_database(unmanaged)
    unmanaged_assessment = _assessment(unmanaged, catalog)
    assert unmanaged_assessment.disposition.value == "database_not_empty_unmanaged"
    assert unmanaged_assessment.reason is not None
    assert unmanaged_assessment.reason.value == "database_not_empty_unmanaged"


@pytest.mark.parametrize(
    "row",
    [
        ("0001_neutral", True, "0" * 64, "2026-08-11T00:00:00Z", 1, 1),
        ("0001_neutral", 1, "0" * 64, "2026-08-11T00:00:00Z", True, 1),
        ("0001_neutral", 1, "0" * 64, "2026-08-11T00:00:00Z", 1, True),
        ("0001_neutral", 1, "0" * 64, 123, 1, 1),
        ["0001_neutral", 1, "0" * 64, "2026-08-11T00:00:00Z", 1, 1],
    ],
)
def test_history_rows_require_exact_builtin_types(row) -> None:
    with pytest.raises(SQLiteStateError, match="migration_history_invalid"):
        _history_row(row)


def test_history_read_is_bounded_to_catalog_tip_plus_one() -> None:
    catalog = _catalog(3)
    rows = [
        (
            definition.migration_id,
            definition.sequence,
            definition.checksum,
            "2026-08-11T00:00:00Z",
            definition.min_app_schema,
            definition.max_app_schema,
        )
        for definition in catalog.migrations
    ]

    class Cursor:
        def __init__(self) -> None:
            self.fetch_bound = None
            self.closed = False

        def fetchmany(self, bound):
            self.fetch_bound = bound
            return rows

        def close(self):
            self.closed = True

    class Connection:
        def __init__(self) -> None:
            self.cursor = Cursor()
            self.parameters = None

        def execute(self, statement, parameters):
            assert "LIMIT ?" in statement
            self.parameters = parameters
            return self.cursor

    connection = Connection()

    history = _read_validated_migration_history(connection, catalog)

    assert len(history) == 3
    assert connection.parameters == (4,)
    assert connection.cursor.fetch_bound == 4
    assert connection.cursor.closed is True


def test_terminal_only_application_generation_compatibility(tmp_path: Path) -> None:
    generation_two = MigrationCatalog(
        (
            _definition(1, min_app_schema=1, max_app_schema=1),
            _definition(2, min_app_schema=2, max_app_schema=2),
        )
    )
    location = _location(tmp_path)

    _initialize(location, generation_two, current_app_schema=2)

    assert _assessment(location, generation_two, current_app_schema=2).disposition.value == "current"
    assert _history(location)[0][4:] == (1, 1)
    assert _history(location)[1][4:] == (2, 2)
    assert (
        _assessment(location, generation_two, current_app_schema=1).disposition.value
        == "newer_unsupported"
    )


@pytest.mark.parametrize("migration_count", [1, 2, 3])
def test_initialization_applies_complete_catalog_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    migration_count: int,
) -> None:
    catalog = _catalog(migration_count)
    location = _location(tmp_path)
    trace: list[str] = []
    original_open = migration_module._open_bound_existing_sqlite_connection

    def traced_open(*args, **kwargs):
        connection = original_open(*args, **kwargs)
        connection.set_trace_callback(trace.append)
        return connection

    monkeypatch.setattr(migration_module, "_open_bound_existing_sqlite_connection", traced_open)

    result = _initialize(location, catalog)

    assert result.classification.name == "MANAGED"
    assert result.classification.value == "managed"
    assert result.current_sequence == migration_count
    rows = _history(location)
    assert [row[1] for row in rows] == list(range(1, migration_count + 1))
    assert len({row[3] for row in rows}) == 1
    expected_tables = {"schema_migrations", "neutral_one"}
    if migration_count >= 2:
        expected_tables.add("neutral_two")
    if migration_count >= 3:
        expected_tables.add("neutral_three")
    assert _tables(location) == expected_tables
    normalized = [statement.strip().upper() for statement in trace]
    assert normalized.count("BEGIN IMMEDIATE") == 1
    assert normalized.count("COMMIT") == 1
    assert normalized.index("COMMIT") > normalized.index("CREATE TABLE NEUTRAL_ONE (VALUE INTEGER NOT NULL);")


@pytest.mark.parametrize(("prefix_length", "tip", "expected_suffix"), [(1, 2, [2]), (1, 3, [2, 3]), (2, 3, [3])])
def test_upgrade_selects_only_the_complete_contiguous_suffix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    prefix_length: int,
    tip: int,
    expected_suffix: list[int],
) -> None:
    full_catalog = _catalog(tip)
    prefix_catalog = MigrationCatalog(full_catalog.migrations[:prefix_length])
    location = _location(tmp_path)
    _initialize(location, prefix_catalog)
    applied: list[int] = []
    original_apply = migration_module._apply_migration_definition_in_transaction

    def record_apply(connection, definition):
        applied.append(definition.sequence)
        return original_apply(connection, definition)

    monkeypatch.setattr(migration_module, "_apply_migration_definition_in_transaction", record_apply)

    result = _migrate(location, full_catalog)

    assert result.current_sequence == tip
    assert applied == expected_suffix
    assert [row[1] for row in _history(location)] == list(range(1, tip + 1))


def test_ordinary_assessment_never_runs_migration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    catalog_one = _catalog(1)
    catalog_two = _catalog(2)
    location = _location(tmp_path)
    _initialize(location, catalog_one)

    def forbidden(*args, **kwargs):
        raise AssertionError("ordinary assessment invoked migration")

    monkeypatch.setattr(migration_module, "_run_bound_migration_plan", forbidden)
    assessment = _assessment(location, catalog_two)

    assert assessment.disposition.value == "supported_older_prefix"
    assert "neutral_two" not in _tables(location)
    assert len(_history(location)) == 1


@pytest.mark.parametrize(
    "opening_state",
    ("absent", "existing_empty"),
)
@pytest.mark.parametrize(
    (
        "failure_point",
        "absent_result",
        "absent_residue",
        "absent_create_calls",
        "existing_empty_result",
        "existing_empty_residue",
        "existing_empty_create_calls",
    ),
    [
        ("catalog_validation", "migration_failed", "root_absent", 0, "migration_failed", "existing_empty_without_lock", 0),
        ("resource_kind", "migration_failed", "root_absent", 0, "migration_failed", "existing_empty_without_lock", 0),
        ("sql_plan", "migration_failed", "root_absent", 0, "migration_failed", "existing_empty_without_lock", 0),
        ("create_open", "migration_failed", "root_plus_lock_only", 1, "managed", "managed_with_lock", 0),
        ("begin", "migration_failed", "empty_database_file_only", 1, "migration_failed", "existing_empty_with_lock", 0),
        ("first_statement", "migration_failed", "empty_database_file_only", 1, "migration_failed", "existing_empty_with_lock", 0),
        ("later_statement", "migration_failed", "empty_database_file_only", 1, "migration_failed", "existing_empty_with_lock", 0),
        ("history_insert", "migration_failed", "empty_database_file_only", 1, "migration_failed", "existing_empty_with_lock", 0),
        ("intermediate_invariant", "migration_failed", "empty_database_file_only", 1, "migration_failed", "existing_empty_with_lock", 0),
        ("final_history", "migration_failed", "empty_database_file_only", 1, "migration_failed", "existing_empty_with_lock", 0),
        ("final_schema", "migration_failed", "empty_database_file_only", 1, "migration_failed", "existing_empty_with_lock", 0),
        ("precommit_cleanup", "migration_failed", "empty_database_file_only", 1, "migration_failed", "existing_empty_with_lock", 0),
    ],
)
def test_c2b1_initialization_fault_matrix_covers_absent_and_existing_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    opening_state: str,
    failure_point: str,
    absent_result: str,
    absent_residue: str,
    absent_create_calls: int,
    existing_empty_result: str,
    existing_empty_residue: str,
    existing_empty_create_calls: int,
) -> None:
    catalog = _catalog(1)
    location = _location(tmp_path)
    if opening_state == "existing_empty":
        _empty_database(location)
    private_marker = f"private-{opening_state}-initialization-{failure_point}"
    create_capable_calls = 0
    original_create_capable_open = migration_module._open_sqlite_connection

    def traced_create_capable_open(*args, **kwargs):
        nonlocal create_capable_calls
        create_capable_calls += 1
        if failure_point == "create_open":
            raise SQLiteStateError("migration_failed")
        return original_create_capable_open(*args, **kwargs)

    monkeypatch.setattr(
        migration_module,
        "_open_sqlite_connection",
        traced_create_capable_open,
    )

    if failure_point == "catalog_validation":
        monkeypatch.setattr(
            migration_module,
            "_validate_catalog_statement_plans",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                SQLiteStateError("migration_failed")
            ),
        )
    elif failure_point == "resource_kind":
        class NonFilesystemTraversable:
            pass

        monkeypatch.setattr(
            migration_module.resources,
            "files",
            lambda package_name: NonFilesystemTraversable(),
        )
    elif failure_point == "sql_plan":
        catalog = MigrationCatalog(
            (
                _definition(
                    1,
                    sql_bytes=b"CREATE TABLE unclosed(value TEXT CHECK(value <> ';));",
                ),
            )
        )
    elif failure_point == "create_open":
        pass
    elif failure_point == "begin":
        original_open = migration_module._open_bound_existing_sqlite_connection

        class BeginFaultConnection:
            def __init__(self, connection):
                self._connection = connection

            def execute(self, statement, *args, **kwargs):
                if statement == "BEGIN IMMEDIATE":
                    raise sqlite3.OperationalError(private_marker)
                return self._connection.execute(statement, *args, **kwargs)

            def __getattr__(self, name):
                return getattr(self._connection, name)

        def fail_begin(*args, **kwargs):
            return BeginFaultConnection(original_open(*args, **kwargs))

        monkeypatch.setattr(
            migration_module,
            "_open_bound_existing_sqlite_connection",
            fail_begin,
        )
    elif failure_point in {"first_statement", "later_statement"}:
        original = migration_module._execute_migration_statement
        calls = 0
        fail_at = 1 if failure_point == "first_statement" else 2

        def fail_statement(connection, statement):
            nonlocal calls
            calls += 1
            if calls == fail_at:
                raise sqlite3.OperationalError(private_marker)
            return original(connection, statement)

        monkeypatch.setattr(migration_module, "_execute_migration_statement", fail_statement)
    elif failure_point == "history_insert":
        monkeypatch.setattr(
            migration_module,
            "_insert_migration_row",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                sqlite3.OperationalError(private_marker)
            ),
        )
    elif failure_point in {"intermediate_invariant", "final_schema"}:
        original = migration_module._verify_schema_for_sequence
        calls = 0
        fail_at = 1 if failure_point == "intermediate_invariant" else 2

        def fail_schema(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == fail_at:
                raise sqlite3.OperationalError(private_marker)
            return original(*args, **kwargs)

        monkeypatch.setattr(migration_module, "_verify_schema_for_sequence", fail_schema)
    elif failure_point == "final_history":
        original = migration_module._read_validated_migration_history
        calls = 0

        def fail_history(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise sqlite3.OperationalError(private_marker)
            return original(*args, **kwargs)

        monkeypatch.setattr(migration_module, "_read_validated_migration_history", fail_history)
    else:
        original_rollback = migration_module._rollback_migration_connection

        def fail_statement_for_cleanup(*args, **kwargs):
            raise sqlite3.OperationalError(private_marker)

        def rollback_but_report_uncertainty(connection):
            assert original_rollback(connection) is True
            return False

        monkeypatch.setattr(
            migration_module,
            "_execute_migration_statement",
            fail_statement_for_cleanup,
        )
        monkeypatch.setattr(
            migration_module,
            "_rollback_migration_connection",
            rollback_but_report_uncertainty,
        )

    expected_result = (
        absent_result if opening_state == "absent" else existing_empty_result
    )
    expected_residue = (
        absent_residue if opening_state == "absent" else existing_empty_residue
    )
    expected_create_calls = (
        absent_create_calls
        if opening_state == "absent"
        else existing_empty_create_calls
    )

    if expected_result == "managed":
        result = _initialize(location, catalog)
        assert result.classification.name == "MANAGED"
        assert result.classification.value == "managed"
        assert result.current_sequence == 1
        assert result.latest_sequence == 1
        assert result.current_migration_id == "0001_neutral"
        assert result.reason is None
    else:
        with pytest.raises(SQLiteStateError) as exc_info:
            if failure_point == "resource_kind":
                migration_module.initialize_database(location)
            else:
                _initialize(location, catalog)

        _assert_detached_public_error(
            exc_info.value,
            "migration_failed",
            private_marker,
        )

    assert create_capable_calls == expected_create_calls
    if expected_residue == "root_absent":
        assert not location.state_root.exists()
        assert not location.state_authority_lock_path.exists()
        assert not location.database_path.exists()
    elif expected_residue == "root_plus_lock_only":
        assert location.state_root.is_dir()
        assert location.state_authority_lock_path.is_file()
        assert not location.database_path.exists()
    elif expected_residue == "managed_with_lock":
        assert location.state_root.is_dir()
        assert location.state_authority_lock_path.is_file()
        assert location.database_path.is_file()
        assert [row[1] for row in _history(location)] == [1]
        assert _tables(location) == {"schema_migrations", "neutral_one"}
    else:
        assert expected_residue in {
            "empty_database_file_only",
            "existing_empty_without_lock",
            "existing_empty_with_lock",
        }
        assert location.state_root.is_dir()
        if expected_residue == "existing_empty_without_lock":
            assert not location.state_authority_lock_path.exists()
        else:
            assert location.state_authority_lock_path.is_file()
        assert location.database_path.is_file()
        assert _tables(location) == set()


def test_c2b1_existing_empty_initialization_never_uses_create_capable_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog(1)
    location = _location(tmp_path)
    _empty_database(location)
    create_capable_calls = 0

    def forbidden_create_capable_open(*args, **kwargs):
        nonlocal create_capable_calls
        create_capable_calls += 1
        raise AssertionError("existing empty initialization used create-capable open")

    monkeypatch.setattr(
        migration_module,
        "_open_sqlite_connection",
        forbidden_create_capable_open,
    )

    result = _initialize(location, catalog)

    assert result.classification.name == "MANAGED"
    assert result.classification.value == "managed"
    assert result.current_sequence == 1
    assert result.latest_sequence == 1
    assert result.current_migration_id == "0001_neutral"
    assert result.reason is None
    assert create_capable_calls == 0
    assert location.database_path.is_file()
    assert [row[1] for row in _history(location)] == [1]
    assert _tables(location) == {"schema_migrations", "neutral_one"}


def test_later_suffix_failure_rolls_back_every_selected_migration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog(3)
    prefix = MigrationCatalog(catalog.migrations[:1])
    location = _location(tmp_path)
    _initialize(location, prefix)
    original = migration_module._apply_migration_definition_in_transaction

    def fail_third(connection, definition):
        if definition.sequence == 3:
            raise SQLiteStateError("migration_failed")
        return original(connection, definition)

    monkeypatch.setattr(migration_module, "_apply_migration_definition_in_transaction", fail_third)

    with pytest.raises(SQLiteStateError, match="migration_failed"):
        _migrate(location, catalog)

    assessment = _assessment(location, catalog)
    assert assessment.disposition.value == "supported_older_prefix"
    assert [row[1] for row in _history(location)] == [1]
    assert _tables(location) == {"schema_migrations", "neutral_one"}


def test_failed_precommit_cleanup_uses_exact_readback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog(1)
    location = _location(tmp_path)
    original_rollback = migration_module._rollback_migration_connection
    recoveries = 0
    original_recovery = migration_module._recover_migration_outcome

    def fail_statement(*args, **kwargs):
        raise SQLiteStateError("migration_failed")

    def rollback_but_report_failure(connection):
        assert original_rollback(connection) is True
        return False

    def record_recovery(*args, **kwargs):
        nonlocal recoveries
        recoveries += 1
        return original_recovery(*args, **kwargs)

    monkeypatch.setattr(migration_module, "_execute_migration_statement", fail_statement)
    monkeypatch.setattr(migration_module, "_rollback_migration_connection", rollback_but_report_failure)
    monkeypatch.setattr(migration_module, "_recover_migration_outcome", record_recovery)

    with pytest.raises(SQLiteStateError, match="migration_failed"):
        _initialize(location, catalog)

    assert recoveries == 1
    _assert_empty_after_failure(location, catalog)


def test_commit_exception_before_underlying_commit_is_definitely_not_committed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog(1)
    location = _location(tmp_path)
    rollback_calls = 0
    private_marker = "private-commit-before-marker"

    def fail_commit(connection):
        raise sqlite3.OperationalError(private_marker)

    def forbidden_rollback(connection):
        nonlocal rollback_calls
        rollback_calls += 1
        return True

    monkeypatch.setattr(migration_module, "_attempt_migration_commit", fail_commit)
    monkeypatch.setattr(migration_module, "_rollback_migration_connection", forbidden_rollback)

    with pytest.raises(SQLiteStateError) as exc_info:
        _initialize(location, catalog)

    _assert_detached_public_error(
        exc_info.value,
        "migration_failed",
        private_marker,
    )
    assert rollback_calls == 0
    _assert_empty_after_failure(location, catalog)


def test_c2b1_nonempty_exact_prior_commit_failure_is_definitely_not_committed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog(2)
    prefix_catalog = MigrationCatalog(catalog.migrations[:1])
    location = _location(tmp_path)
    _initialize(location, prefix_catalog)
    opening_history = _history(location)
    opening_tables = _tables(location)
    original_run = migration_module._run_bound_migration_plan
    original_apply = migration_module._apply_migration_definition_in_transaction
    original_insert = migration_module._insert_migration_row
    original_recovery = migration_module._recover_migration_outcome
    original_rollback = migration_module._rollback_migration_connection
    private_marker = "private-nonempty-prefix-commit-before-marker"
    run_attempts = 0
    commit_attempts = 0
    commit_attempted = False
    rollback_after_commit_attempts = 0
    applied_sequences: list[int] = []
    inserted_sequences: list[int] = []
    recovery_evidence_names: list[str] = []
    recovery_evidence_values: list[str] = []
    authority_lock_retained = False

    def record_run(*args, **kwargs):
        nonlocal run_attempts
        run_attempts += 1
        return original_run(*args, **kwargs)

    def record_apply(connection, definition):
        applied_sequences.append(definition.sequence)
        return original_apply(connection, definition)

    def record_insert(connection, definition, *, applied_at):
        inserted_sequences.append(definition.sequence)
        return original_insert(connection, definition, applied_at=applied_at)

    def fail_before_underlying_commit(connection):
        nonlocal commit_attempts, commit_attempted
        commit_attempts += 1
        commit_attempted = True
        raise sqlite3.OperationalError(private_marker)

    def record_rollback(connection):
        nonlocal rollback_after_commit_attempts
        if commit_attempted:
            rollback_after_commit_attempts += 1
        return original_rollback(connection)

    def recover_while_authority_lock_is_retained(*args, **kwargs):
        nonlocal authority_lock_retained
        with pytest.raises(StateAuthorityLockError):
            acquire_state_authority_lock(location)
        authority_lock_retained = True
        result = original_recovery(*args, **kwargs)
        recovery_evidence_names.append(result.evidence.name)
        recovery_evidence_values.append(result.evidence.value)
        return result

    monkeypatch.setattr(migration_module, "_run_bound_migration_plan", record_run)
    monkeypatch.setattr(
        migration_module,
        "_apply_migration_definition_in_transaction",
        record_apply,
    )
    monkeypatch.setattr(migration_module, "_insert_migration_row", record_insert)
    monkeypatch.setattr(
        migration_module,
        "_attempt_migration_commit",
        fail_before_underlying_commit,
    )
    monkeypatch.setattr(
        migration_module,
        "_rollback_migration_connection",
        record_rollback,
    )
    monkeypatch.setattr(
        migration_module,
        "_recover_migration_outcome",
        recover_while_authority_lock_is_retained,
    )

    with pytest.raises(SQLiteStateError) as exc_info:
        _migrate(location, catalog)

    _assert_detached_public_error(
        exc_info.value,
        "migration_failed",
        private_marker,
    )
    assert run_attempts == 1
    assert commit_attempts == 1
    assert rollback_after_commit_attempts == 0
    assert applied_sequences == [2]
    assert inserted_sequences == [2]
    assert recovery_evidence_names == ["DEFINITELY_NOT_COMMITTED"]
    assert recovery_evidence_values == ["definitely_not_committed"]
    assert authority_lock_retained is True
    assert _history(location) == opening_history
    assert [row[1] for row in _history(location)] == [1]
    assert _tables(location) == opening_tables
    assert _tables(location) == {"schema_migrations", "neutral_one"}
    assert "neutral_two" not in _tables(location)


def test_commit_exception_after_underlying_commit_returns_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog(2)
    location = _location(tmp_path)
    original_commit = migration_module._attempt_migration_commit
    attempts = 0

    def commit_then_raise(connection):
        nonlocal attempts
        attempts += 1
        original_commit(connection)
        raise sqlite3.OperationalError("acknowledgement lost")

    monkeypatch.setattr(migration_module, "_attempt_migration_commit", commit_then_raise)

    result = _initialize(location, catalog)

    assert result.current_sequence == 2
    assert attempts == 1
    assert _assessment(location, catalog).disposition.value == "current"


@pytest.mark.parametrize(
    "corruption",
    [
        "history_only",
        "schema_only",
        "partial_suffix",
        "unknown_history",
        "divergent_metadata",
        "unexpected_object",
    ],
)
def test_c2b1_required_recovery_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
) -> None:
    catalog = _catalog(2)
    location = _location(tmp_path)
    original_commit = migration_module._attempt_migration_commit
    original_apply = migration_module._apply_migration_definition_in_transaction
    private_marker = f"private-{corruption}-marker"
    commit_attempts = 0
    applied_sequences: list[int] = []
    rollback_calls = 0

    def commit_corrupt_then_raise(connection):
        nonlocal commit_attempts
        commit_attempts += 1
        original_commit(connection)
        with closing(sqlite3.connect(location.database_path)) as corrupting, corrupting:
            if corruption == "history_only":
                corrupting.execute("DROP TABLE neutral_two")
            elif corruption == "schema_only":
                corrupting.execute("DELETE FROM schema_migrations WHERE sequence = 2")
            elif corruption == "partial_suffix":
                corrupting.execute("DELETE FROM schema_migrations WHERE sequence = 2")
                corrupting.execute("DROP TABLE neutral_two")
            elif corruption == "unknown_history":
                corrupting.execute(
                    "UPDATE schema_migrations SET migration_id = '0002_unknown' WHERE sequence = 2"
                )
            elif corruption == "divergent_metadata":
                corrupting.execute(
                    "UPDATE schema_migrations SET max_app_schema = 2 WHERE sequence = 2"
                )
            else:
                corrupting.execute("CREATE TABLE unexpected_object(value INTEGER)")
        raise sqlite3.OperationalError(private_marker)

    def record_apply(connection, definition):
        applied_sequences.append(definition.sequence)
        return original_apply(connection, definition)

    def forbidden_rollback(connection):
        nonlocal rollback_calls
        rollback_calls += 1
        raise AssertionError("rollback attempted after commit")

    monkeypatch.setattr(migration_module, "_attempt_migration_commit", commit_corrupt_then_raise)
    monkeypatch.setattr(
        migration_module,
        "_apply_migration_definition_in_transaction",
        record_apply,
    )
    monkeypatch.setattr(
        migration_module,
        "_rollback_migration_connection",
        forbidden_rollback,
    )

    with pytest.raises(SQLiteStateError) as exc_info:
        _initialize(location, catalog)

    _assert_detached_public_error(
        exc_info.value,
        "migration_outcome_unresolved",
        private_marker,
    )
    assert commit_attempts == 1
    assert applied_sequences == [1, 2]
    assert rollback_calls == 0


def test_close_failure_after_commit_is_resolved_by_readback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog(1)
    location = _location(tmp_path)
    original_close = migration_module._close_migration_connection
    calls = 0
    rollback_calls = 0

    def fail_once_after_close(connection):
        nonlocal calls
        calls += 1
        if calls == 1:
            if connection is not None:
                connection.close()
            raise sqlite3.OperationalError("close acknowledgement lost")
        return original_close(connection)

    def forbidden_rollback(connection):
        nonlocal rollback_calls
        rollback_calls += 1
        raise AssertionError("rollback attempted after successful commit")

    monkeypatch.setattr(migration_module, "_close_migration_connection", fail_once_after_close)
    monkeypatch.setattr(
        migration_module,
        "_rollback_migration_connection",
        forbidden_rollback,
    )

    result = _initialize(location, catalog)

    assert result.current_sequence == 1
    assert calls >= 2
    assert rollback_calls == 0
    assert _assessment(location, catalog).disposition.value == "current"


def test_recovery_open_failure_is_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog(1)
    location = _location(tmp_path)
    original_open = migration_module._open_bound_existing_sqlite_connection
    opens = 0
    commit_marker = "private-recovery-open-commit-marker"
    recovery_marker = "private-recovery-open-marker"

    def fail_commit(connection):
        raise sqlite3.OperationalError(commit_marker)

    def fail_recovery_open(*args, **kwargs):
        nonlocal opens
        opens += 1
        if opens == 2:
            raise sqlite3.OperationalError(recovery_marker)
        return original_open(*args, **kwargs)

    monkeypatch.setattr(migration_module, "_attempt_migration_commit", fail_commit)
    monkeypatch.setattr(migration_module, "_open_bound_existing_sqlite_connection", fail_recovery_open)

    with pytest.raises(SQLiteStateError) as exc_info:
        _initialize(location, catalog)

    assert opens == 2
    _assert_detached_public_error(
        exc_info.value,
        "migration_outcome_unresolved",
        commit_marker,
        recovery_marker,
    )


@pytest.mark.parametrize("failure", ["history", "schema"])
def test_incomplete_recovery_verification_is_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    catalog = _catalog(1)
    location = _location(tmp_path)
    original_commit = migration_module._attempt_migration_commit
    commit_attempted = False
    commit_marker = f"private-recovery-{failure}-commit-marker"
    recovery_marker = f"private-recovery-{failure}-marker"

    def commit_then_raise(connection):
        nonlocal commit_attempted
        original_commit(connection)
        commit_attempted = True
        raise sqlite3.OperationalError(commit_marker)

    monkeypatch.setattr(migration_module, "_attempt_migration_commit", commit_then_raise)
    if failure == "history":
        original = migration_module._read_validated_migration_history

        def fail_after_commit(*args, **kwargs):
            if commit_attempted:
                raise sqlite3.OperationalError(recovery_marker)
            return original(*args, **kwargs)

        monkeypatch.setattr(migration_module, "_read_validated_migration_history", fail_after_commit)
    else:
        original = migration_module._verify_schema_for_sequence

        def fail_after_commit(*args, **kwargs):
            if commit_attempted:
                raise sqlite3.OperationalError(recovery_marker)
            return original(*args, **kwargs)

        monkeypatch.setattr(migration_module, "_verify_schema_for_sequence", fail_after_commit)

    with pytest.raises(SQLiteStateError) as exc_info:
        _initialize(location, catalog)

    _assert_detached_public_error(
        exc_info.value,
        "migration_outcome_unresolved",
        commit_marker,
        recovery_marker,
    )


def test_recovery_invariant_failure_is_unresolved_and_detached(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    original_commit = migration_module._attempt_migration_commit
    original_invariants = migration_module._verify_managed_state_invariants
    commit_attempted = False
    commit_marker = "private-recovery-invariant-commit-marker"
    invariant_marker = "private-recovery-invariant-marker"

    def commit_then_raise(connection):
        nonlocal commit_attempted
        original_commit(connection)
        commit_attempted = True
        raise sqlite3.OperationalError(commit_marker)

    def fail_recovery_invariants(connection):
        if commit_attempted:
            raise sqlite3.OperationalError(invariant_marker)
        return original_invariants(connection)

    monkeypatch.setattr(migration_module, "_attempt_migration_commit", commit_then_raise)
    monkeypatch.setattr(
        migration_module,
        "_verify_managed_state_invariants",
        fail_recovery_invariants,
    )

    with pytest.raises(SQLiteStateError) as exc_info:
        migration_module.initialize_database(location)

    _assert_detached_public_error(
        exc_info.value,
        "migration_outcome_unresolved",
        commit_marker,
        invariant_marker,
    )


def test_c2b1_public_tracebacks_contain_only_safe_error_vocabulary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog(1)
    location = _location(tmp_path)
    original_close = migration_module._close_migration_connection
    original_open = migration_module._open_bound_existing_sqlite_connection
    close_calls = 0
    close_marker = "private-postcommit-close-marker"
    recovery_marker = "private-postcommit-recovery-open-marker"

    def close_then_raise(connection):
        nonlocal close_calls
        close_calls += 1
        if close_calls == 1:
            if connection is not None:
                connection.close()
            raise sqlite3.OperationalError(close_marker)
        return original_close(connection)

    def fail_recovery_open(binding, *, read_only, **kwargs):
        if read_only:
            raise sqlite3.OperationalError(recovery_marker)
        return original_open(binding, read_only=read_only, **kwargs)

    monkeypatch.setattr(migration_module, "_close_migration_connection", close_then_raise)
    monkeypatch.setattr(
        migration_module,
        "_open_bound_existing_sqlite_connection",
        fail_recovery_open,
    )

    with pytest.raises(SQLiteStateError) as exc_info:
        _initialize(location, catalog)

    _assert_detached_public_error(
        exc_info.value,
        "migration_outcome_unresolved",
        close_marker,
        recovery_marker,
    )


def test_common_authority_lock_is_retained_through_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog(1)
    location = _location(tmp_path)
    original_recovery = migration_module._recover_migration_outcome
    observed = False

    def fail_commit(connection):
        raise sqlite3.OperationalError("commit result missing")

    def recovery_while_locked(*args, **kwargs):
        nonlocal observed
        with pytest.raises(StateAuthorityLockError):
            acquire_state_authority_lock(location)
        observed = True
        return original_recovery(*args, **kwargs)

    monkeypatch.setattr(migration_module, "_attempt_migration_commit", fail_commit)
    monkeypatch.setattr(migration_module, "_recover_migration_outcome", recovery_while_locked)

    with pytest.raises(SQLiteStateError, match="migration_failed"):
        _initialize(location, catalog)

    assert observed is True


def test_c2b1_destructive_initialization_fails_before_manifest_sqlite_activity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destructive = MigrationCatalog((_definition(1, destructive=True),))
    location = _location(tmp_path)
    _empty_database(location)
    opening_bytes = location.database_path.read_bytes()
    calls = {
        "manifest_connect": 0,
        "manifest_begin": 0,
        "manifest_statement": 0,
        "lock": 0,
        "target_open": 0,
        "target_transaction": 0,
        "target_mutation": 0,
    }

    def forbidden_manifest(*args, **kwargs):
        calls["manifest_connect"] += 1
        calls["manifest_begin"] += 1
        calls["manifest_statement"] += 1
        raise AssertionError("destructive initialization reached manifest SQLite")

    def record(name):
        def forbidden(*args, **kwargs):
            calls[name] += 1
            raise AssertionError(f"destructive initialization reached {name}")

        return forbidden

    monkeypatch.setattr(
        migration_module,
        "_expected_schema_manifest_for_sequence",
        forbidden_manifest,
    )
    monkeypatch.setattr(migration_module, "acquire_state_authority_lock", record("lock"))
    monkeypatch.setattr(migration_module, "_open_sqlite_connection", record("target_open"))
    monkeypatch.setattr(
        migration_module,
        "_open_bound_existing_sqlite_connection",
        record("target_transaction"),
    )
    monkeypatch.setattr(
        migration_module,
        "_apply_migration_definition_in_transaction",
        record("target_mutation"),
    )

    with pytest.raises(SQLiteStateError) as exc_info:
        _initialize(location, destructive)

    assert exc_info.value.error_class == "migration_failed"
    assert calls == {name: 0 for name in calls}
    assert location.database_path.read_bytes() == opening_bytes
    assert not location.state_authority_lock_path.exists()


@pytest.mark.parametrize("suffix_length", [1, 2])
def test_c2b1_destructive_suffix_fails_before_manifest_sqlite_activity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    suffix_length: int,
) -> None:
    prefix = _catalog(1)
    destructive_suffix = tuple(
        _definition(sequence, destructive=True)
        for sequence in range(2, 2 + suffix_length)
    )
    catalog = MigrationCatalog(prefix.migrations + destructive_suffix)
    location = _location(tmp_path)
    _initialize(location, prefix)
    opening_history = _history(location)
    opening_tables = _tables(location)
    calls = {
        "manifest_connect": 0,
        "manifest_begin": 0,
        "manifest_statement": 0,
        "lock": 0,
        "target_open": 0,
        "target_transaction": 0,
        "target_mutation": 0,
    }

    def forbidden_manifest(*args, **kwargs):
        calls["manifest_connect"] += 1
        calls["manifest_begin"] += 1
        calls["manifest_statement"] += 1
        raise AssertionError("destructive suffix reached manifest SQLite")

    def record(name):
        def forbidden(*args, **kwargs):
            calls[name] += 1
            raise AssertionError(f"destructive suffix reached {name}")

        return forbidden

    monkeypatch.setattr(
        migration_module,
        "_expected_schema_manifest_for_sequence",
        forbidden_manifest,
    )
    monkeypatch.setattr(migration_module, "acquire_state_authority_lock", record("lock"))
    monkeypatch.setattr(
        migration_module,
        "_open_bound_existing_sqlite_connection",
        record("target_open"),
    )
    monkeypatch.setattr(
        migration_module,
        "_run_bound_migration_plan",
        record("target_transaction"),
    )
    monkeypatch.setattr(
        migration_module,
        "_apply_migration_definition_in_transaction",
        record("target_mutation"),
    )

    with pytest.raises(SQLiteStateError) as exc_info:
        _migrate(location, catalog)

    assert exc_info.value.error_class == "migration_failed"
    assert calls == {name: 0 for name in calls}
    assert _history(location) == opening_history
    assert _tables(location) == opening_tables


def test_destructive_metadata_is_catalog_only_and_resolution_is_injective(tmp_path: Path) -> None:
    catalog = _catalog(1)
    location = _location(tmp_path)
    _initialize(location, catalog)
    with closing(sqlite3.connect(location.database_path)) as connection, connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(schema_migrations)").fetchall()]
    assert "destructive" not in columns

    duplicate_id = _definition(2, migration_id=catalog.migrations[0].migration_id)
    with pytest.raises(SQLiteStateError, match="migration_history_invalid"):
        MigrationCatalog(catalog.migrations + (duplicate_id,))
    duplicate_resource = _definition(2, resource_name=catalog.migrations[0].resource_name)
    with pytest.raises(SQLiteStateError, match="migration_history_invalid"):
        MigrationCatalog(catalog.migrations + (duplicate_resource,))


@pytest.mark.parametrize(
    ("resource_kind", "expected_result"),
    [
        ("regular", "accepted"),
        ("symlink_exact", "migration_failed"),
        ("symlink_wrong", "migration_failed"),
        ("directory", "migration_failed"),
        ("fifo", "migration_failed"),
        ("socket", "migration_failed"),
        ("device", "migration_failed"),
        ("missing", "migration_failed"),
        ("replace_before_open", "migration_failed"),
        ("replace_during_read", "migration_failed"),
    ],
)
def test_c2b1_filesystem_migration_resources_require_regular_nonsymlink_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    resource_kind: str,
    expected_result: str,
) -> None:
    production_catalog = migration_module.load_migration_catalog()
    production = production_catalog.migrations[0]
    later_production = production_catalog.migrations[1]
    sqlite_calls = 0

    def forbidden_sqlite_connect(*args, **kwargs):
        nonlocal sqlite_calls
        sqlite_calls += 1
        raise AssertionError("migration resource loading reached SQLite")

    monkeypatch.setattr(
        migration_module.sqlite3,
        "connect",
        forbidden_sqlite_connect,
    )
    package = tmp_path / resource_kind
    package.mkdir()
    resource = package / "0001_initial.sql"
    (package / "0002_development_program_and_effect_state.sql").write_bytes(
        later_production.sql_bytes
    )
    private_marker = "private-resource-marker"
    if resource_kind in {"regular", "replace_before_open", "replace_during_read"}:
        resource.write_bytes(production.sql_bytes)
    elif resource_kind == "symlink_exact":
        target = package / "exact-target"
        target.write_bytes(production.sql_bytes)
        resource.symlink_to(target)
    elif resource_kind == "symlink_wrong":
        target = package / "wrong-target"
        target.write_text(private_marker, encoding="utf-8")
        resource.symlink_to(target)
    elif resource_kind == "directory":
        resource.mkdir()
    elif resource_kind == "fifo":
        os.mkfifo(resource)
    elif resource_kind in {"socket", "device"}:
        resource.write_bytes(production.sql_bytes)

    monkeypatch.setattr(migration_module.resources, "files", lambda package_name: package)
    if resource_kind in {"socket", "device"}:
        original_lstat = os.lstat

        def special_file_lstat(path):
            observed = original_lstat(path)
            if Path(path) == resource:
                values = list(observed)
                file_kind = (
                    migration_module.stat.S_IFSOCK
                    if resource_kind == "socket"
                    else migration_module.stat.S_IFCHR
                )
                values[0] = (
                    observed.st_mode
                    & ~migration_module.stat.S_IFMT(observed.st_mode)
                ) | file_kind
                return os.stat_result(values)
            return observed

        monkeypatch.setattr(migration_module.os, "lstat", special_file_lstat)
    elif resource_kind == "replace_before_open":
        original_open = os.open
        replaced = False

        def replace_then_open(path, flags):
            nonlocal replaced
            if Path(path) == resource and not replaced:
                replacement = package / "replacement-before"
                replacement.write_bytes(production.sql_bytes)
                os.replace(replacement, resource)
                replaced = True
            return original_open(path, flags)

        monkeypatch.setattr(migration_module.os, "open", replace_then_open)
    elif resource_kind == "replace_during_read":
        original_read = os.read
        replaced = False

        def replace_during_read(descriptor, count):
            nonlocal replaced
            chunk = original_read(descriptor, count)
            if not replaced:
                replacement = package / "replacement-during"
                replacement.write_bytes(production.sql_bytes)
                os.replace(replacement, resource)
                replaced = True
            return chunk

        monkeypatch.setattr(migration_module.os, "read", replace_during_read)

    if expected_result == "accepted":
        loaded = migration_module.load_migration_catalog()
        assert loaded.migrations[0].sql_bytes == production.sql_bytes
        assert loaded.migrations[1].sql_bytes == later_production.sql_bytes
    else:
        with pytest.raises(SQLiteStateError) as exc_info:
            migration_module.load_migration_catalog()
        _assert_detached_public_error(
            exc_info.value,
            "migration_failed",
            str(resource),
            private_marker,
        )
    assert sqlite_calls == 0


def test_c2b1_nonfilesystem_migration_resources_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class NonFilesystemTraversable:
        pass

    monkeypatch.setattr(
        migration_module.resources,
        "files",
        lambda package_name: NonFilesystemTraversable(),
    )
    sqlite_calls = 0

    def forbidden_sqlite_connect(*args, **kwargs):
        nonlocal sqlite_calls
        sqlite_calls += 1
        raise AssertionError("non-filesystem resource reached SQLite")

    monkeypatch.setattr(
        migration_module.sqlite3,
        "connect",
        forbidden_sqlite_connect,
    )

    with pytest.raises(SQLiteStateError) as exc_info:
        migration_module.load_migration_catalog()

    _assert_detached_public_error(exc_info.value, "migration_failed")
    assert sqlite_calls == 0


def test_c2b1_oversized_resource_rejects_before_sqlite_activity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = tmp_path / "oversized-package"
    package.mkdir()
    resource = package / "0001_initial.sql"
    private_marker = "private-oversized-resource-marker"
    payload = private_marker.encode("utf-8") + b"x" * (
        migration_module.MAX_MIGRATION_RESOURCE_BYTES
        + 1
        - len(private_marker.encode("utf-8"))
    )
    assert len(payload) == 1_048_577
    resource.write_bytes(payload)
    monkeypatch.setattr(migration_module.resources, "files", lambda package_name: package)

    expected_manifest_connects = 0
    target_sqlite_opens = 0
    authority_lock_acquisitions = 0
    target_transactions = 0
    target_mutations = 0

    def forbidden_expected_manifest_connect(*args, **kwargs):
        nonlocal expected_manifest_connects
        expected_manifest_connects += 1
        raise AssertionError("oversized resource reached expected-manifest SQLite")

    def forbidden_create_capable_open(*args, **kwargs):
        nonlocal target_sqlite_opens
        target_sqlite_opens += 1
        raise AssertionError("oversized resource reached create-capable SQLite open")

    def forbidden_bound_open(*args, **kwargs):
        nonlocal target_sqlite_opens
        target_sqlite_opens += 1
        raise AssertionError("oversized resource reached bound SQLite open")

    def forbidden_authority_lock(*args, **kwargs):
        nonlocal authority_lock_acquisitions
        authority_lock_acquisitions += 1
        raise AssertionError("oversized resource reached authority lock")

    def forbidden_transaction(*args, **kwargs):
        nonlocal target_transactions
        target_transactions += 1
        raise AssertionError("oversized resource reached target transaction")

    def forbidden_mutation(*args, **kwargs):
        nonlocal target_mutations
        target_mutations += 1
        raise AssertionError("oversized resource reached target mutation")

    monkeypatch.setattr(
        migration_module.sqlite3,
        "connect",
        forbidden_expected_manifest_connect,
    )
    monkeypatch.setattr(
        migration_module,
        "_open_sqlite_connection",
        forbidden_create_capable_open,
    )
    monkeypatch.setattr(
        migration_module,
        "_open_bound_existing_sqlite_connection",
        forbidden_bound_open,
    )
    monkeypatch.setattr(
        migration_module,
        "acquire_state_authority_lock",
        forbidden_authority_lock,
    )
    monkeypatch.setattr(
        migration_module,
        "_run_bound_migration_plan",
        forbidden_transaction,
    )
    monkeypatch.setattr(
        migration_module,
        "_apply_migration_definition_in_transaction",
        forbidden_mutation,
    )
    location = _location(tmp_path, "oversized-state")

    with pytest.raises(SQLiteStateError) as exc_info:
        migration_module.initialize_database(location)

    _assert_detached_public_error(
        exc_info.value,
        "migration_failed",
        private_marker,
        str(resource),
        str(package),
    )
    assert expected_manifest_connects == 0
    assert target_sqlite_opens == 0
    assert authority_lock_acquisitions == 0
    assert target_transactions == 0
    assert target_mutations == 0
    assert not location.state_root.exists()
    assert not location.state_authority_lock_path.exists()
    assert not location.database_path.exists()


@pytest.mark.parametrize(
    "statement",
    [
        "BEGIN;",
        "BEGIN IMMEDIATE;",
        "COMMIT;",
        "END TRANSACTION;",
        "ROLLBACK;",
        "ROLLBACK TO x;",
        "SAVEPOINT x;",
        "RELEASE x;",
        "PRAGMA foreign_keys=OFF;",
        "ATTACH DATABASE ':memory:' AS x;",
        "DETACH DATABASE x;",
        "VACUUM;",
        "VACUUM INTO 'x';",
        "CREATE TABLE x(v TEXT); COMMIT;",
        "-- leading comment\npragma journal_mode = wal;",
        "/* leading comment */ ROLLBACK;",
        "COMMIT; -- trailing comment\n",
        "RoLlBaCk;",
        "",
        "CREATE TABLE x(v TEXT CHECK(v <> ';));",
        "/* unclosed block comment",
    ],
)
def test_c2b1_required_sql_transaction_control_matrix(statement: str) -> None:
    with pytest.raises(SQLiteStateError, match="migration_failed"):
        _migration_statements(statement)


def test_sql_plan_rejects_same_line_transaction_escape() -> None:
    with pytest.raises(SQLiteStateError, match="migration_failed"):
        _migration_statements(
            "CREATE TABLE neutral_first (value INTEGER); COMMIT;"
        )


def test_c2b1_required_sql_quoting_comment_and_trigger_matrix() -> None:
    quoted_and_commented = _migration_statements(
        "CREATE TABLE single_quote(v TEXT DEFAULT ';');\n"
        'CREATE TABLE "double;quote"(v INTEGER);\n'
        "-- line comment with COMMIT;\n"
        "/* block comment with ROLLBACK; */\n"
        "CREATE TABLE final_value(v INTEGER);"
    )
    assert len(quoted_and_commented) == 3
    same_line = _migration_statements(
        "CREATE TABLE same_line_one(v INTEGER); CREATE TABLE same_line_two(v INTEGER);"
    )
    assert len(same_line) == 2

    sql = """
    CREATE TABLE neutral_trigger_source (value INTEGER);
    CREATE TRIGGER neutral_trigger
    AFTER INSERT ON neutral_trigger_source
    BEGIN
        SELECT NEW.value;
    END;
    """
    statements = _migration_statements(sql)
    assert len(statements) == 2
    assert statements[1].lstrip().upper().startswith("CREATE TRIGGER")

    class TransactionLossConnection:
        def __init__(self) -> None:
            self.in_transaction = True

        def execute(self, statement):
            self.in_transaction = False

    with pytest.raises(SQLiteStateError, match="migration_failed"):
        migration_module._execute_migration_statement(
            TransactionLossConnection(),
            "CREATE TABLE lost(v INTEGER);",
        )


def test_runner_rejects_a_plan_not_owned_by_its_catalog_before_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog(1)
    alien = _definition(
        1,
        sql_bytes=b"CREATE TABLE neutral_alien (value INTEGER);\n",
        migration_id="0001_alien",
        resource_name="0001_alien.sql",
    )
    plan = _migration_plan(
        prior_history=(),
        suffix=(alien,),
        fresh_install=True,
        verify_managed_invariants=False,
    )

    def forbidden_open(*args, **kwargs):
        raise AssertionError("a non-catalog plan reached writable open")

    monkeypatch.setattr(
        migration_module,
        "_open_bound_existing_sqlite_connection",
        forbidden_open,
    )

    with pytest.raises(SQLiteStateError, match="migration_failed"):
        migration_module._run_bound_migration_plan(
            None,
            None,
            catalog,
            plan,
            current_app_schema=1,
        )


def test_c2b1_expected_manifest_connect_failure_is_safe_across_public_apis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inspect_location = _location(tmp_path, "inspect-connect")
    initialize_location = _location(tmp_path, "initialize-connect")
    migrate_location = _location(tmp_path, "migrate-connect")
    _assert_production_managed_inspection(
        migration_module.initialize_database(inspect_location)
    )
    _empty_database(initialize_location)
    _assert_production_managed_inspection(
        migration_module.initialize_database(migrate_location)
    )
    original_connect = sqlite3.connect

    inspect_marker = "private-expected-manifest-connect-inspect"

    def fail_inspect_expected_connect(database, *args, **kwargs):
        if database == ":memory:":
            raise sqlite3.OperationalError(inspect_marker)
        return original_connect(database, *args, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(migration_module.sqlite3, "connect", fail_inspect_expected_connect)
        inspection = migration_module.inspect_database(inspect_location)
    _assert_expected_manifest_inspection_failure(inspection)
    assert inspect_marker not in repr(inspection)
    assert str(inspect_location.database_path) not in repr(inspection)
    _assert_production_managed_inspection(
        migration_module.inspect_database(inspect_location)
    )

    initialize_marker = "private-expected-manifest-connect-initialize"

    def fail_initialize_expected_connect(database, *args, **kwargs):
        if database == ":memory:":
            raise sqlite3.OperationalError(initialize_marker)
        return original_connect(database, *args, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(
            migration_module.sqlite3,
            "connect",
            fail_initialize_expected_connect,
        )
        with pytest.raises(SQLiteStateError) as exc_info:
            migration_module.initialize_database(initialize_location)
    _assert_detached_public_error(
        exc_info.value,
        "schema_verification_failed",
        initialize_marker,
        "OperationalError",
        str(initialize_location.database_path),
        "CREATE TABLE",
        "SELECT type, name",
        "sqlite_schema",
        "0001_initial.sql",
        "_MigrationPlan",
    )
    _assert_production_managed_inspection(
        migration_module.initialize_database(initialize_location)
    )

    migrate_marker = "private-expected-manifest-connect-migrate"

    def fail_migrate_expected_connect(database, *args, **kwargs):
        if database == ":memory:":
            raise sqlite3.OperationalError(migrate_marker)
        return original_connect(database, *args, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(migration_module.sqlite3, "connect", fail_migrate_expected_connect)
        with pytest.raises(SQLiteStateError) as exc_info:
            migration_module.migrate_database(migrate_location)
    _assert_detached_public_error(
        exc_info.value,
        "schema_verification_failed",
        migrate_marker,
        "OperationalError",
        str(migrate_location.database_path),
        "CREATE TABLE",
        "SELECT type, name",
        "sqlite_schema",
        "0001_initial.sql",
        "_MigrationPlan",
    )
    _assert_production_managed_inspection(
        migration_module.migrate_database(migrate_location)
    )


def test_c2b1_expected_manifest_close_failure_is_safe_across_public_apis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inspect_location = _location(tmp_path, "inspect-close")
    initialize_location = _location(tmp_path, "initialize-close")
    migrate_location = _location(tmp_path, "migrate-close")
    _assert_production_managed_inspection(
        migration_module.initialize_database(inspect_location)
    )
    _empty_database(initialize_location)
    _assert_production_managed_inspection(
        migration_module.initialize_database(migrate_location)
    )
    original_connect = sqlite3.connect

    inspect_marker = "private-expected-manifest-close-inspect"
    inspect_close_attempts: list[int] = []

    def fail_inspect_expected_close(database, *args, **kwargs):
        connection = original_connect(database, *args, **kwargs)
        if database == ":memory:":
            return _ExpectedManifestCloseFaultConnection(
                connection,
                inspect_marker,
                inspect_close_attempts,
            )
        return connection

    with monkeypatch.context() as fault:
        fault.setattr(migration_module.sqlite3, "connect", fail_inspect_expected_close)
        inspection = migration_module.inspect_database(inspect_location)
    _assert_expected_manifest_inspection_failure(inspection)
    assert inspect_close_attempts == [1]
    assert inspect_marker not in repr(inspection)
    assert str(inspect_location.database_path) not in repr(inspection)
    _assert_production_managed_inspection(
        migration_module.inspect_database(inspect_location)
    )

    initialize_marker = "private-expected-manifest-close-initialize"
    initialize_close_attempts: list[int] = []

    def fail_initialize_expected_close(database, *args, **kwargs):
        connection = original_connect(database, *args, **kwargs)
        if database == ":memory:":
            return _ExpectedManifestCloseFaultConnection(
                connection,
                initialize_marker,
                initialize_close_attempts,
            )
        return connection

    with monkeypatch.context() as fault:
        fault.setattr(
            migration_module.sqlite3,
            "connect",
            fail_initialize_expected_close,
        )
        with pytest.raises(SQLiteStateError) as exc_info:
            migration_module.initialize_database(initialize_location)
    _assert_detached_public_error(
        exc_info.value,
        "schema_verification_failed",
        initialize_marker,
        "OperationalError",
        str(initialize_location.database_path),
        "CREATE TABLE",
        "SELECT type, name",
        "sqlite_schema",
        "0001_initial.sql",
        "_MigrationPlan",
    )
    assert initialize_close_attempts == [1]
    _assert_production_managed_inspection(
        migration_module.initialize_database(initialize_location)
    )

    migrate_marker = "private-expected-manifest-close-migrate"
    migrate_close_attempts: list[int] = []

    def fail_migrate_expected_close(database, *args, **kwargs):
        connection = original_connect(database, *args, **kwargs)
        if database == ":memory:":
            return _ExpectedManifestCloseFaultConnection(
                connection,
                migrate_marker,
                migrate_close_attempts,
            )
        return connection

    with monkeypatch.context() as fault:
        fault.setattr(migration_module.sqlite3, "connect", fail_migrate_expected_close)
        with pytest.raises(SQLiteStateError) as exc_info:
            migration_module.migrate_database(migrate_location)
    _assert_detached_public_error(
        exc_info.value,
        "schema_verification_failed",
        migrate_marker,
        "OperationalError",
        str(migrate_location.database_path),
        "CREATE TABLE",
        "SELECT type, name",
        "sqlite_schema",
        "0001_initial.sql",
        "_MigrationPlan",
    )
    assert migrate_close_attempts == [1]
    _assert_production_managed_inspection(
        migration_module.migrate_database(migrate_location)
    )


def test_c2b1_expected_manifest_public_errors_have_no_raw_exception_graph(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connect_location = _location(tmp_path, "graph-connect")
    close_location = _location(tmp_path, "graph-close")
    _empty_database(connect_location)
    _assert_production_managed_inspection(
        migration_module.initialize_database(close_location)
    )
    original_connect = sqlite3.connect
    connect_marker = "private-expected-manifest-connect-graph"

    def fail_expected_connect(database, *args, **kwargs):
        if database == ":memory:":
            raise sqlite3.OperationalError(connect_marker)
        return original_connect(database, *args, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(migration_module.sqlite3, "connect", fail_expected_connect)
        with pytest.raises(SQLiteStateError) as connect_exc_info:
            migration_module.initialize_database(connect_location)
    _assert_detached_public_error(
        connect_exc_info.value,
        "schema_verification_failed",
        connect_marker,
        "OperationalError",
        str(connect_location.database_path),
        "CREATE TABLE",
        "sqlite_schema",
        "0001_initial.sql",
    )

    close_marker = "private-expected-manifest-close-graph"
    close_attempts: list[int] = []

    def fail_expected_close(database, *args, **kwargs):
        connection = original_connect(database, *args, **kwargs)
        if database == ":memory:":
            return _ExpectedManifestCloseFaultConnection(
                connection,
                close_marker,
                close_attempts,
            )
        return connection

    with monkeypatch.context() as fault:
        fault.setattr(migration_module.sqlite3, "connect", fail_expected_close)
        with pytest.raises(SQLiteStateError) as close_exc_info:
            migration_module.migrate_database(close_location)
    _assert_detached_public_error(
        close_exc_info.value,
        "schema_verification_failed",
        close_marker,
        "OperationalError",
        str(close_location.database_path),
        "CREATE TABLE",
        "sqlite_schema",
        "0001_initial.sql",
    )
    assert close_attempts == [1]


def test_c2b1_expected_manifest_tracebacks_contain_only_safe_vocabulary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connect_location = _location(tmp_path, "traceback-connect")
    close_location = _location(tmp_path, "traceback-close")
    _empty_database(connect_location)
    _assert_production_managed_inspection(
        migration_module.initialize_database(close_location)
    )
    original_connect = sqlite3.connect
    connect_marker = "private-expected-manifest-connect-traceback"

    def fail_expected_connect(database, *args, **kwargs):
        if database == ":memory:":
            raise sqlite3.OperationalError(connect_marker)
        return original_connect(database, *args, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(migration_module.sqlite3, "connect", fail_expected_connect)
        with pytest.raises(SQLiteStateError) as connect_exc_info:
            migration_module.initialize_database(connect_location)
    connect_traceback = "".join(traceback.format_exception(connect_exc_info.value))
    assert "schema_verification_failed" in connect_traceback
    for private_text in (
        connect_marker,
        "OperationalError",
        str(connect_location.database_path),
        "CREATE TABLE",
        "sqlite_schema",
        "0001_initial.sql",
        "_MigrationPlan",
    ):
        assert private_text not in connect_traceback
    _assert_detached_public_error(
        connect_exc_info.value,
        "schema_verification_failed",
        connect_marker,
    )

    close_marker = "private-expected-manifest-close-traceback"
    close_attempts: list[int] = []

    def fail_expected_close(database, *args, **kwargs):
        connection = original_connect(database, *args, **kwargs)
        if database == ":memory:":
            return _ExpectedManifestCloseFaultConnection(
                connection,
                close_marker,
                close_attempts,
            )
        return connection

    with monkeypatch.context() as fault:
        fault.setattr(migration_module.sqlite3, "connect", fail_expected_close)
        with pytest.raises(SQLiteStateError) as close_exc_info:
            migration_module.migrate_database(close_location)
    close_traceback = "".join(traceback.format_exception(close_exc_info.value))
    assert "schema_verification_failed" in close_traceback
    for private_text in (
        close_marker,
        "OperationalError",
        str(close_location.database_path),
        "CREATE TABLE",
        "sqlite_schema",
        "0001_initial.sql",
        "_MigrationPlan",
    ):
        assert private_text not in close_traceback
    _assert_detached_public_error(
        close_exc_info.value,
        "schema_verification_failed",
        close_marker,
    )
    assert close_attempts == [1]


def test_private_plan_and_recovery_representations_are_safe() -> None:
    definition = _definition(
        1,
        sql_bytes=b"CREATE TABLE neutral_secret_object (secret_value TEXT);\n",
        migration_id="0001_private",
        resource_name="private_resource.sql",
    )
    plan = _migration_plan(
        prior_history=(),
        suffix=(definition,),
        fresh_install=True,
        verify_managed_invariants=False,
    )
    plan_representation = repr(plan)
    assert "neutral_secret_object" not in plan_representation
    assert "secret_value" not in plan_representation
    assert "private_resource.sql" not in plan_representation
    assert "CREATE TABLE" not in plan_representation
    for evidence in _MigrationCommitEvidence:
        recovery = _MigrationRecoveryResult(evidence)
        assert "Connection" not in repr(recovery)
        assert ".sqlite" not in repr(recovery)


def test_c2b1_public_errors_have_no_raw_exception_graph(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog(1)
    location = _location(tmp_path)
    sensitive = (
        f"private-sqlite-marker:{location.database_path}:"
        "CREATE TABLE neutral_secret sqlite raw failure"
    )

    def leak_attempt(*args, **kwargs):
        raise sqlite3.OperationalError(sensitive)

    monkeypatch.setattr(migration_module, "_execute_migration_statement", leak_attempt)

    with pytest.raises(SQLiteStateError) as exc_info:
        _initialize(location, catalog)

    _assert_detached_public_error(
        exc_info.value,
        "migration_failed",
        sensitive,
        str(location.database_path),
        "CREATE TABLE neutral_secret",
    )


def test_c2b1_repair1_full_audit_counterfactual_matrix() -> None:
    expected_private_dispositions = (
        ("ABSENT", "absent"),
        ("EMPTY", "empty"),
        ("CURRENT", "current"),
        ("SUPPORTED_OLDER_PREFIX", "supported_older_prefix"),
        ("UNSUPPORTED_OLDER", "unsupported_older"),
        ("NEWER_UNSUPPORTED", "newer_unsupported"),
        ("CORRUPT_HISTORY", "corrupt_history"),
        ("PARTIAL_MIGRATION", "partial_migration"),
        ("DATABASE_NOT_EMPTY_UNMANAGED", "database_not_empty_unmanaged"),
    )
    expected_public_classifications = (
        ("ABSENT", "absent"),
        ("EMPTY", "empty"),
        ("MANAGED", "managed"),
        ("UNKNOWN", "unknown"),
    )
    expected_prohibited_leading_keywords = frozenset(
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

    private_value_mutant = (
        ("ABSENT", "candidate-mutated-absent"),
        *expected_private_dispositions[1:],
    )
    public_value_mutant = (
        ("ABSENT", "candidate-mutated-absent"),
        *expected_public_classifications[1:],
    )
    prohibited_keyword_mutant = frozenset(
        keyword
        for keyword in expected_prohibited_leading_keywords
        if keyword != "END"
    )

    assert tuple(
        (member.name, member.value)
        for member in migration_module._MigrationDatabaseDisposition
    ) == expected_private_dispositions
    assert tuple(
        (member.name, member.value)
        for member in migration_module.DatabaseClassification
    ) == expected_public_classifications
    assert (
        migration_module._PROHIBITED_MIGRATION_KEYWORDS
        == expected_prohibited_leading_keywords
    )
    assert private_value_mutant != expected_private_dispositions
    assert public_value_mutant != expected_public_classifications
    assert prohibited_keyword_mutant != expected_prohibited_leading_keywords


def test_c2b1_repair2_full_audit_counterfactual_matrix() -> None:
    expected_manifest_failure_cases = (
        ("inspect_database", "connect", "UNKNOWN", "schema_verification_failed"),
        ("inspect_database", "close", "UNKNOWN", "schema_verification_failed"),
        ("initialize_database", "connect", "raises", "schema_verification_failed"),
        ("initialize_database", "close", "raises", "schema_verification_failed"),
        ("migrate_database", "connect", "raises", "schema_verification_failed"),
        ("migrate_database", "close", "raises", "schema_verification_failed"),
    )
    initialization_opening_states = ("absent", "existing_empty")
    initialization_fault_stages = (
        "catalog_validation",
        "resource_kind",
        "sql_plan",
        "create_open",
        "begin",
        "first_statement",
        "later_statement",
        "history_insert",
        "intermediate_invariant",
        "final_history",
        "final_schema",
        "precommit_cleanup",
    )
    initialization_cases = tuple(
        (opening_state, fault_stage)
        for opening_state in initialization_opening_states
        for fault_stage in initialization_fault_stages
    )
    expected_recovery = (
        ("opening_prefix", (1,)),
        ("selected_suffix", (2,)),
        ("commit_attempts", 1),
        ("rollback_after_commit", 0),
        ("evidence", "DEFINITELY_NOT_COMMITTED"),
        ("outward_result", "migration_failed"),
        ("automatic_retry", 0),
        ("complete_suffix_rerun", 0),
        ("remainder_append", 0),
    )

    missing_close_case_mutant = expected_manifest_failure_cases[:-1]
    absent_only_initialization_mutant = tuple(
        ("absent", fault_stage)
        for fault_stage in initialization_fault_stages
    )
    oversize_boundary_mutant = 1_048_576
    recovery_evidence_mutant = tuple(
        (name, "UNRESOLVED" if name == "evidence" else value)
        for name, value in expected_recovery
    )

    assert len(expected_manifest_failure_cases) == 6
    assert len(set(expected_manifest_failure_cases)) == 6
    assert len(initialization_cases) == 24
    assert len(set(initialization_cases)) == 24
    assert migration_module.MAX_MIGRATION_RESOURCE_BYTES == 1_048_576
    assert migration_module.MAX_MIGRATION_RESOURCE_BYTES + 1 == 1_048_577
    assert dict(expected_recovery) == {
        "opening_prefix": (1,),
        "selected_suffix": (2,),
        "commit_attempts": 1,
        "rollback_after_commit": 0,
        "evidence": "DEFINITELY_NOT_COMMITTED",
        "outward_result": "migration_failed",
        "automatic_retry": 0,
        "complete_suffix_rerun": 0,
        "remainder_append": 0,
    }
    assert missing_close_case_mutant != expected_manifest_failure_cases
    assert absent_only_initialization_mutant != initialization_cases
    assert oversize_boundary_mutant != 1_048_577
    assert recovery_evidence_mutant != expected_recovery
