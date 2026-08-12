from __future__ import annotations

import hashlib
import multiprocessing as mp
from pathlib import Path
import sqlite3
import stat
import threading

import pytest

import ge_nwp_coordinator.sqlite_migration as sqlite_migration
from ge_nwp_coordinator.sqlite_errors import SQLiteStateError
from ge_nwp_coordinator.sqlite_errors import SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import (
    DatabaseClassification,
    MigrationCatalog,
    MigrationDefinition,
    _initialize_database_with_catalog,
    initialize_database,
    inspect_database,
    migrate_database,
    validate_database,
)
from ge_nwp_coordinator.state_authority_lock import (
    StateAuthorityLockError,
    StateAuthorityLockErrorReason,
    acquire_state_authority_lock,
)


def _location(tmp_path: Path) -> CoordinatorStateLocation:
    return CoordinatorStateLocation.from_trusted_root(tmp_path / "state")


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.lstat().st_mode)


def _digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _count(location: CoordinatorStateLocation, table_name: str) -> int:
    with sqlite3.connect(location.database_path) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


def _hold_lock(root: str, ready_sender, release_receiver) -> None:
    location = CoordinatorStateLocation.from_trusted_root(Path(root))
    try:
        with acquire_state_authority_lock(location):
            ready_sender.send("acquired")
            release_receiver.recv()
    finally:
        ready_sender.close()
        release_receiver.close()


def _start_holder(location: CoordinatorStateLocation):
    context = mp.get_context("fork")
    ready_receiver, ready_sender = context.Pipe(duplex=False)
    release_receiver, release_sender = context.Pipe(duplex=False)
    process = context.Process(target=_hold_lock, args=(str(location.state_root), ready_sender, release_receiver))
    process.start()
    ready_sender.close()
    release_receiver.close()
    assert ready_receiver.recv() == "acquired"
    ready_receiver.close()
    return process, release_sender


def _release_holder(process, release_sender) -> None:
    release_sender.send("release")
    release_sender.close()
    process.join(5)
    assert process.exitcode == 0


def test_inspect_and_validate_absent_do_not_create_lock_file(tmp_path: Path) -> None:
    location = _location(tmp_path)

    assert inspect_database(location).classification is DatabaseClassification.ABSENT
    assert validate_database(location).classification is DatabaseClassification.ABSENT

    assert not location.state_root.exists()
    assert not location.database_path.exists()
    assert not location.state_authority_lock_path.exists()


def test_initialize_creates_and_uses_state_authority_lock(tmp_path: Path) -> None:
    location = _location(tmp_path)

    inspection = initialize_database(location)

    assert inspection.classification is DatabaseClassification.MANAGED
    assert location.database_path.exists()
    assert location.state_authority_lock_path.exists()
    assert _mode(location.state_root) == 0o700
    assert _mode(location.state_authority_lock_path) == 0o600
    assert _count(location, "writer_ownership") == 0


def test_initialize_while_lock_held_fails_safely_without_database_mutation(tmp_path: Path) -> None:
    location = _location(tmp_path)
    holder, release_sender = _start_holder(location)
    try:
        with pytest.raises(StateAuthorityLockError) as exc_info:
            initialize_database(location)
    finally:
        _release_holder(holder, release_sender)

    assert exc_info.value.reason is StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_BUSY
    assert not location.database_path.exists()
    assert location.state_authority_lock_path.exists()


def test_initialize_exception_after_lock_releases_resource(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)

    def fail_apply(*args, **kwargs):
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)

    monkeypatch.setattr(sqlite_migration, "_apply_migration_definition_in_transaction", fail_apply)
    with pytest.raises(SQLiteStateError, match="migration_failed"):
        initialize_database(location)

    with acquire_state_authority_lock(location):
        pass


def test_initialize_commit_recovery_retains_common_lock_and_reopens_bound_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    original_commit = sqlite_migration._attempt_migration_commit
    original_open = sqlite_migration._open_bound_existing_sqlite_connection
    original_recovery = sqlite_migration._recover_migration_outcome
    open_modes: list[bool] = []
    recovery_observed = False

    def commit_then_raise(connection):
        original_commit(connection)
        raise sqlite3.OperationalError("commit acknowledgement unavailable")

    def record_bound_open(binding, *, read_only, **kwargs):
        open_modes.append(read_only)
        return original_open(binding, read_only=read_only, **kwargs)

    def recover_while_lock_retained(*args, **kwargs):
        nonlocal recovery_observed
        with pytest.raises(StateAuthorityLockError):
            acquire_state_authority_lock(location)
        recovery_observed = True
        return original_recovery(*args, **kwargs)

    monkeypatch.setattr(sqlite_migration, "_attempt_migration_commit", commit_then_raise)
    monkeypatch.setattr(sqlite_migration, "_open_bound_existing_sqlite_connection", record_bound_open)
    monkeypatch.setattr(sqlite_migration, "_recover_migration_outcome", recover_while_lock_retained)

    result = initialize_database(location)

    assert result.classification is DatabaseClassification.MANAGED
    assert open_modes == [False, True]
    assert recovery_observed is True


def test_destructive_catalog_is_refused_before_common_lock_or_writable_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    sql_bytes = b"CREATE TABLE neutral_destructive_probe (value INTEGER);\n"
    definition = MigrationDefinition(
        migration_id="0001_neutral_destructive_probe",
        sequence=1,
        resource_name="0001_neutral_destructive_probe.sql",
        sql_bytes=sql_bytes,
        checksum=hashlib.sha256(sql_bytes).hexdigest(),
        min_app_schema=1,
        max_app_schema=1,
        destructive=True,
        description="neutral destructive preflight probe",
    )
    calls: list[str] = []
    monkeypatch.setattr(
        sqlite_migration,
        "acquire_state_authority_lock",
        lambda *args, **kwargs: calls.append("lock"),
    )
    monkeypatch.setattr(
        sqlite_migration,
        "_open_sqlite_connection",
        lambda *args, **kwargs: calls.append("writable"),
    )
    monkeypatch.setattr(
        sqlite_migration,
        "_expected_schema_manifest_for_sequence",
        lambda *args, **kwargs: calls.append("manifest"),
    )

    with pytest.raises(SQLiteStateError, match="migration_failed"):
        _initialize_database_with_catalog(
            location,
            MigrationCatalog((definition,)),
            current_app_schema=1,
            verify_managed_invariants=False,
        )

    assert calls == []
    assert not location.state_root.exists()


def test_migrate_while_lock_held_fails_safely_without_migration_change(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    before = _digest(location.database_path)
    holder, release_sender = _start_holder(location)
    try:
        with pytest.raises(StateAuthorityLockError) as exc_info:
            migrate_database(location)
    finally:
        _release_holder(holder, release_sender)

    assert exc_info.value.reason is StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_BUSY
    assert _digest(location.database_path) == before
    assert _count(location, "schema_migrations") == 1
    assert _count(location, "writer_ownership") == 0


def test_migrate_exception_after_lock_releases_resource(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    original_assess = sqlite_migration._assess_location_database
    calls = 0

    def fail_locked_assessment(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls >= 2:
            raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_FAILED)
        return original_assess(*args, **kwargs)

    monkeypatch.setattr(sqlite_migration, "_assess_location_database", fail_locked_assessment)
    with pytest.raises(SQLiteStateError, match="migration_failed"):
        migrate_database(location)

    with acquire_state_authority_lock(location):
        pass


def test_unknown_database_is_rejected_before_lock_creation_or_posture_mutation(tmp_path: Path) -> None:
    location = _location(tmp_path)
    location.state_root.mkdir(mode=0o700, parents=True)
    location.database_path.write_bytes(b"not-a-sqlite-database")
    location.database_path.chmod(0o600)
    before = _digest(location.database_path)

    with pytest.raises(SQLiteStateError, match="sqlite_posture_unavailable"):
        initialize_database(location)

    assert _digest(location.database_path) == before
    assert not location.state_authority_lock_path.exists()


def test_migrate_absent_empty_or_unknown_refuses_without_lock_creation(tmp_path: Path) -> None:
    absent = _location(tmp_path / "absent")
    with pytest.raises(SQLiteStateError, match="migration_history_missing"):
        migrate_database(absent)
    assert not absent.state_root.exists()
    assert not absent.state_authority_lock_path.exists()

    empty = _location(tmp_path / "empty")
    empty.state_root.mkdir(mode=0o700, parents=True)
    empty.database_path.write_bytes(b"")
    empty.database_path.chmod(0o600)
    with pytest.raises(SQLiteStateError, match="migration_history_missing"):
        migrate_database(empty)
    assert not empty.state_authority_lock_path.exists()

    unknown = _location(tmp_path / "unknown")
    unknown.state_root.mkdir(mode=0o700, parents=True)
    unknown.database_path.write_bytes(b"not-sqlite")
    unknown.database_path.chmod(0o600)
    with pytest.raises(SQLiteStateError, match="sqlite_posture_unavailable"):
        migrate_database(unknown)
    assert not unknown.state_authority_lock_path.exists()


def test_validate_remains_observational_while_state_authority_lock_is_held(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    before = _digest(location.database_path)

    with acquire_state_authority_lock(location):
        inspection = validate_database(location)

    assert inspection.classification is DatabaseClassification.MANAGED
    assert _digest(location.database_path) == before


def test_two_simultaneous_initialize_calls_do_not_partially_initialize(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    entered = threading.Event()
    release = threading.Event()
    original = sqlite_migration._apply_migration_definition_in_transaction

    def slow_apply(connection, migration):
        entered.set()
        assert release.wait(5)
        return original(connection, migration)

    monkeypatch.setattr(sqlite_migration, "_apply_migration_definition_in_transaction", slow_apply)
    results: list[str] = []

    def call_initialize() -> None:
        try:
            initialize_database(location)
            results.append("managed")
        except StateAuthorityLockError as exc:
            results.append(exc.reason.value)

    first = threading.Thread(target=call_initialize)
    first.start()
    assert entered.wait(5)
    second = threading.Thread(target=call_initialize)
    second.start()
    second.join(5)
    release.set()
    first.join(5)

    assert sorted(results) == ["managed", "state_authority_lock_busy"]
    assert validate_database(location).classification is DatabaseClassification.MANAGED
    assert _count(location, "schema_migrations") == 1
    assert _count(location, "writer_ownership") == 0


def test_two_simultaneous_migrate_calls_do_not_partially_migrate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    before = _digest(location.database_path)
    entered = threading.Event()
    release = threading.Event()
    original_open = sqlite_migration.open_existing_sqlite_connection
    call_count = 0
    pause_used = False
    counter_lock = threading.Lock()

    def slow_open(*args, **kwargs):
        nonlocal call_count, pause_used
        with counter_lock:
            call_count += 1
            # C2B1 Repair 1 performs history-only and complete assessment before
            # locking, then repeats both under the common authority lock. The
            # third observational open is therefore the first lock-held read.
            should_pause = call_count >= 3 and not pause_used
            if should_pause:
                pause_used = True
        if should_pause:
            entered.set()
            assert release.wait(5)
        return original_open(*args, **kwargs)

    monkeypatch.setattr(sqlite_migration, "open_existing_sqlite_connection", slow_open)
    results: list[str] = []

    def call_migrate() -> None:
        try:
            migrate_database(location)
            results.append("managed")
        except StateAuthorityLockError as exc:
            results.append(exc.reason.value)

    first = threading.Thread(target=call_migrate)
    first.start()
    assert entered.wait(5)
    second = threading.Thread(target=call_migrate)
    second.start()
    second.join(5)
    release.set()
    first.join(5)

    assert sorted(results) == ["managed", "state_authority_lock_busy"]
    assert _digest(location.database_path) == before
    assert validate_database(location).classification is DatabaseClassification.MANAGED
    assert _count(location, "schema_migrations") == 1
    assert _count(location, "writer_ownership") == 0
