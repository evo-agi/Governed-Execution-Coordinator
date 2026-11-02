"""F1 observation, bounded engine rollback, and refusal controls."""
from __future__ import annotations

import hashlib
from contextlib import closing
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import subprocess
import sys

import pytest

import ge_nwp_coordinator.sqlite_connection as connection_module
import ge_nwp_coordinator.sqlite_migration as migration_module
import ge_nwp_coordinator.sqlite_security as security_module
import ge_nwp_coordinator.sqlite_writer_session as writer_module
from ge_nwp_coordinator.sqlite_errors import SQLiteStateError, SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import (
    DatabaseClassification,
    initialize_database,
    inspect_database,
    migrate_database,
    validate_database,
)
from ge_nwp_coordinator.sqlite_writer_session import (
    SQLiteWriterAcquisitionError,
    SQLiteWriterAcquisitionFailureReason,
    acquire_sqlite_writer_session,
)
from ge_nwp_coordinator.state_authority_lock import (
    StateAuthorityLockError,
    acquire_state_authority_lock,
)


_CHILD = r'''
import os, sqlite3, sys
os.umask(0o077)
connection = sqlite3.connect(sys.argv[1], isolation_level=None)
connection.execute("PRAGMA journal_mode=DELETE")
connection.execute("PRAGMA cache_size=10")
if sys.argv[2] == "attached":
    connection.execute("ATTACH DATABASE ? AS aux", (sys.argv[3],))
    connection.execute("PRAGMA aux.journal_mode=DELETE")
    connection.execute("PRAGMA aux.cache_size=10")
    connection.execute("CREATE TABLE aux.fixture_other(x TEXT)")
connection.execute("BEGIN IMMEDIATE")
if sys.argv[2] == "interrupted_issuance":
    connection.execute("UPDATE writer_ownership SET generation = 2 WHERE singleton_id = 1")
connection.execute("CREATE TABLE fixture_spill(x TEXT)")
for index in range(6000):
    connection.execute("INSERT INTO fixture_spill(x) VALUES (?)", ("x" * 1000 + str(index),))
if sys.argv[2] == "attached":
    connection.execute("INSERT INTO aux.fixture_other(x) VALUES ('other')")
os._exit(0)
'''


def _journal(location: CoordinatorStateLocation) -> Path:
    return location.state_root / (location.database_path.name + "-journal")


def _hot_location(
    tmp_path: Path, *, attached: bool = False, older_prefix: bool = False,
    interrupted_issuance: bool = False,
) -> tuple[CoordinatorStateLocation, Path]:
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "state")
    if older_prefix:
        catalog = migration_module.load_migration_catalog()
        migration_module._initialize_database_with_catalog(
            location, migration_module.MigrationCatalog(catalog.migrations[:4]),
            current_app_schema=2, verify_managed_invariants=True,
        )
    else:
        assert initialize_database(location).classification is DatabaseClassification.MANAGED
        session = acquire_sqlite_writer_session(location)
        assert session.metadata.generation == 1
        session.close()
    external = tmp_path / "task-owned-external.sqlite"
    child = subprocess.Popen(
        [sys.executable, "-B", "-c", _CHILD, str(location.database_path),
         "attached" if attached else "interrupted_issuance" if interrupted_issuance else "plain", str(external)],
        cwd=tmp_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        _stdout, stderr = child.communicate(timeout=25)
    except subprocess.TimeoutExpired:
        child.terminate()
        try:
            child.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.communicate(timeout=5)
        pytest.fail("owned fixture child needed test rescue")
    assert child.returncode == 0, stderr.decode("utf-8", errors="replace")
    assert _journal(location).is_file() and _journal(location).stat().st_size >= 512
    if attached:
        assert external.with_name(external.name + "-journal").is_file()
    return location, external


def _inventory(root: Path) -> dict[str, tuple[int, int, int, int, int, str]]:
    result = {}
    for path in root.iterdir():
        metadata = path.lstat()
        result[path.name] = (
            metadata.st_ino, metadata.st_size, stat.S_IMODE(metadata.st_mode),
            metadata.st_mtime_ns, metadata.st_ctime_ns,
            hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "",
        )
    return result


def test_engine_hot_journal_observation_and_administration_are_nonmutating(tmp_path: Path) -> None:
    location, _external = _hot_location(tmp_path)
    before = _inventory(location.state_root)
    for _ in range(3):
        for observe in (inspect_database, validate_database):
            inspection = observe(location)
            assert inspection.classification is DatabaseClassification.UNKNOWN
            assert inspection.reason == "recovery_needed"
    for administer in (initialize_database, migrate_database):
        with pytest.raises(SQLiteStateError) as refusal:
            administer(location)
        assert refusal.value.error_class == "recovery_needed"
    raw = sqlite3.connect(location.database_path.as_uri() + "?mode=ro", uri=True)
    try:
        with pytest.raises(sqlite3.Error) as engine:
            raw.execute("PRAGMA journal_mode").fetchone()
        assert type(engine.value.sqlite_errorcode) is int
        assert engine.value.sqlite_errorcode == 776
    finally:
        raw.close()
    assert _inventory(location.state_root) == before
    session = acquire_sqlite_writer_session(location)
    try:
        assert session.metadata.generation == 2
        with session._resource.operation_guard(session):
            assert session.active
    finally:
        session.close()
    assert not _journal(location).exists()
    with closing(sqlite3.connect(location.database_path.as_uri() + "?mode=ro", uri=True)) as recovered:
        assert recovered.execute("SELECT generation FROM writer_ownership").fetchone() == (2,)
        assert recovered.execute(
            "SELECT count(*) FROM sqlite_schema WHERE name='fixture_spill'"
        ).fetchone() == (0,)
    with acquire_state_authority_lock(location):
        pass


def test_precommit_attached_origin_recovers_main_without_touching_sibling(tmp_path: Path) -> None:
    location, external = _hot_location(tmp_path, attached=True)
    assert inspect_database(location).reason == "recovery_needed"
    sibling_journal = external.with_name(external.name + "-journal")
    sibling_before = {
        "database": _inventory(tmp_path)[external.name],
        "journal": _inventory(tmp_path)[sibling_journal.name],
    }
    session = acquire_sqlite_writer_session(location)
    try:
        assert session.metadata.generation == 2
    finally:
        session.close()
    sibling_after = {
        "database": _inventory(tmp_path)[external.name],
        "journal": _inventory(tmp_path)[sibling_journal.name],
    }
    assert sibling_after == sibling_before
    with closing(sqlite3.connect(location.database_path.as_uri() + "?mode=ro", uri=True)) as recovered:
        assert recovered.execute("SELECT generation FROM writer_ownership").fetchone() == (2,)
        assert recovered.execute(
            "SELECT count(*) FROM sqlite_schema WHERE name='fixture_spill'"
        ).fetchone() == (0,)


def test_recovery_of_exact_older_prefix_changes_storage_but_does_not_issue(
    tmp_path: Path,
) -> None:
    location, _external = _hot_location(tmp_path, older_prefix=True)
    assert inspect_database(location).reason == "recovery_needed"
    with pytest.raises(SQLiteWriterAcquisitionError) as refusal:
        acquire_sqlite_writer_session(location)
    assert refusal.value.reason is SQLiteWriterAcquisitionFailureReason.DATABASE_NOT_MANAGED
    assert not _journal(location).exists()
    with closing(sqlite3.connect(location.database_path.as_uri() + "?mode=ro", uri=True)) as recovered:
        assert recovered.execute("SELECT max(sequence) FROM schema_migrations").fetchone() == (4,)
        assert recovered.execute("SELECT count(*) FROM writer_ownership").fetchone() == (0,)
        assert recovered.execute(
            "SELECT count(*) FROM sqlite_schema WHERE name='fixture_spill'"
        ).fetchone() == (0,)
    with acquire_state_authority_lock(location):
        pass
    upgraded = migrate_database(location)
    assert upgraded.current_sequence == upgraded.latest_sequence == 9


def test_uncommitted_interrupted_issuance_is_rolled_back_before_next_generation(
    tmp_path: Path,
) -> None:
    location, _external = _hot_location(tmp_path, interrupted_issuance=True)
    assert inspect_database(location).reason == "recovery_needed"
    session = acquire_sqlite_writer_session(location)
    try:
        assert session.metadata.generation == 2
    finally:
        session.close()
    with closing(sqlite3.connect(location.database_path.as_uri() + "?mode=ro", uri=True)) as recovered:
        assert recovered.execute("SELECT count(*),max(generation) FROM writer_ownership").fetchone() == (1, 2)
        assert recovered.execute(
            "SELECT count(*) FROM sqlite_schema WHERE name='fixture_spill'"
        ).fetchone() == (0,)


def test_machine_classification_requires_exact_numeric_extended_result() -> None:
    for code, expected in ((776, True), (8, False), (None, False), (True, False), ("776", False)):
        error = sqlite3.OperationalError("SQLITE_READONLY_ROLLBACK text is not authority")
        error.sqlite_errorcode = code
        assert connection_module._is_engine_reported_readonly_rollback(error) is expected


def test_nonempty_super_journal_tail_refuses_before_writable_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _external = _hot_location(tmp_path)
    assert inspect_database(location).reason == "recovery_needed"
    journal = _journal(location)
    name = b"task-owned-super-journal"
    magic = bytes.fromhex("d9d505f920a163d7")
    # A finite structural tail control. It is not an engine-generated crash.
    with journal.open("ab") as handle:
        handle.write(name + len(name).to_bytes(4, "big") + sum(name).to_bytes(4, "big") + magic)
    assert inspect_database(location).reason == "recovery_needed"
    before = _inventory(location.state_root)
    reached = []
    original_guard = writer_module._bound_hot_rollback_journal
    original_open = writer_module._open_bound_existing_sqlite_connection

    def record_guard(binding):
        reached.append("guard")
        return original_guard(binding)

    def forbid_recovery_open(*args, **kwargs):
        if kwargs.get("recovery"):
            reached.append("writable_open")
            pytest.fail("super-journal dependency reached writable recovery")
        return original_open(*args, **kwargs)

    monkeypatch.setattr(writer_module, "_bound_hot_rollback_journal", record_guard)
    monkeypatch.setattr(writer_module, "_open_bound_existing_sqlite_connection", forbid_recovery_open)
    with pytest.raises(SQLiteWriterAcquisitionError) as refusal:
        acquire_sqlite_writer_session(location)
    assert refusal.value.reason is SQLiteWriterAcquisitionFailureReason.RECOVERY_UNSAFE
    assert reached == ["guard"]
    assert _inventory(location.state_root) == before
    with acquire_state_authority_lock(location):
        pass


@pytest.mark.parametrize(
    "case", [
        "mode", "hardlink", "symlink", "wal_sidecar", "shm_sidecar",
        "auxiliary_journal", "partial_tail",
    ],
)
def test_unsupported_journal_arrangements_refuse_before_writable_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str,
) -> None:
    location, _external = _hot_location(tmp_path)
    journal = _journal(location)
    if case == "mode":
        journal.chmod(0o644)
    elif case == "hardlink":
        os.link(journal, tmp_path / "task-owned-journal-alias")
    elif case == "symlink":
        held = tmp_path / "held-journal"
        journal.rename(held)
        journal.symlink_to(held)
    elif case in ("wal_sidecar", "shm_sidecar", "auxiliary_journal"):
        sidecar_name = {
            "wal_sidecar": location.database_path.name + "-wal",
            "shm_sidecar": location.database_path.name + "-shm",
            "auxiliary_journal": "task-owned-sibling-journal",
        }[case]
        sidecar = location.state_root / sidecar_name
        sidecar.write_bytes(b"unsupported-sidecar")
        sidecar.chmod(0o600)
    else:
        with journal.open("ab") as handle:
            handle.write(bytes.fromhex("d9d505f9"))
    before = _inventory(location.state_root)
    recovery_opens = []
    guard_hits = []
    original_open = writer_module._open_bound_existing_sqlite_connection
    original_guard = writer_module._bound_hot_rollback_journal

    def record_guard(binding):
        guard_hits.append(True)
        return original_guard(binding)

    def forbid_recovery_open(*args, **kwargs):
        if kwargs.get("recovery"):
            recovery_opens.append(True)
            pytest.fail("unsupported journal reached writable recovery")
        return original_open(*args, **kwargs)

    monkeypatch.setattr(writer_module, "_open_bound_existing_sqlite_connection", forbid_recovery_open)
    monkeypatch.setattr(writer_module, "_bound_hot_rollback_journal", record_guard)
    with pytest.raises((SQLiteWriterAcquisitionError, SQLiteStateError, StateAuthorityLockError)):
        acquire_sqlite_writer_session(location)
    assert recovery_opens == []
    if case in ("wal_sidecar", "shm_sidecar", "auxiliary_journal"):
        assert guard_hits == [True]
    assert _inventory(location.state_root) == before
    with acquire_state_authority_lock(location):
        pass


@pytest.mark.parametrize("case", ["directory", "fifo"])
def test_nonregular_journal_is_refused_by_bound_checker(
    tmp_path: Path, case: str,
) -> None:
    location, _external = _hot_location(tmp_path)
    journal = _journal(location)
    held = tmp_path / "task-owned-held-journal"
    with acquire_state_authority_lock(location) as lock:
        binding = lock._capture_state_database_authority_binding(location)
        journal.rename(held)
        if case == "directory":
            journal.mkdir(mode=0o700)
        else:
            os.mkfifo(journal, 0o600)
        try:
            with pytest.raises(SQLiteStateError) as refusal:
                with security_module._bound_hot_rollback_journal(binding):
                    pytest.fail("nonregular journal reached recovery")
            assert refusal.value.error_class == "recovery_unsafe"
        finally:
            if case == "directory":
                journal.rmdir()
            else:
                journal.unlink()
            held.rename(journal)
    with acquire_state_authority_lock(location):
        pass


@pytest.mark.parametrize("case", ["root", "lock", "database"])
def test_unsafe_bound_file_modes_refuse_without_issuance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str,
) -> None:
    location, _external = _hot_location(tmp_path)
    target = {
        "root": location.state_root,
        "lock": location.state_authority_lock_path,
        "database": location.database_path,
    }[case]
    target.chmod(0o755 if case == "root" else 0o644)
    recovery_opens = []
    original_open = writer_module._open_bound_existing_sqlite_connection

    def forbid_recovery_open(*args, **kwargs):
        if kwargs.get("recovery"):
            recovery_opens.append(True)
            pytest.fail("unsafe metadata reached writable recovery")
        return original_open(*args, **kwargs)

    monkeypatch.setattr(writer_module, "_open_bound_existing_sqlite_connection", forbid_recovery_open)
    try:
        with pytest.raises((SQLiteWriterAcquisitionError, SQLiteStateError, StateAuthorityLockError)):
            acquire_sqlite_writer_session(location)
        assert recovery_opens == []
    finally:
        target.chmod(0o700 if case == "root" else 0o600)
    with acquire_state_authority_lock(location):
        pass


def test_journal_disappearance_after_locked_recheck_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _external = _hot_location(tmp_path)
    assert inspect_database(location).reason == "recovery_needed"
    original_guard = writer_module._bound_hot_rollback_journal
    reached = []

    def remove_at_guard(binding):
        reached.append("guard")
        _journal(location).unlink()
        return original_guard(binding)

    monkeypatch.setattr(writer_module, "_bound_hot_rollback_journal", remove_at_guard)
    with pytest.raises(SQLiteWriterAcquisitionError) as refusal:
        acquire_sqlite_writer_session(location)
    assert reached == ["guard"]
    assert refusal.value.reason is SQLiteWriterAcquisitionFailureReason.RECOVERY_UNSAFE
    with acquire_state_authority_lock(location):
        pass


def test_journal_change_during_structural_check_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _external = _hot_location(tmp_path)
    assert inspect_database(location).reason == "recovery_needed"
    original_pread = security_module.os.pread
    changed = []

    def change_after_header(descriptor: int, count: int, offset: int) -> bytes:
        data = original_pread(descriptor, count, offset)
        if count == 28 and offset == 0 and not changed:
            changed.append(True)
            with _journal(location).open("ab") as handle:
                handle.write(b"changed-after-header")
        return data

    monkeypatch.setattr(security_module.os, "pread", change_after_header)
    with pytest.raises(SQLiteWriterAcquisitionError) as refusal:
        acquire_sqlite_writer_session(location)
    assert changed == [True]
    assert refusal.value.reason is SQLiteWriterAcquisitionFailureReason.RECOVERY_UNSAFE
    with acquire_state_authority_lock(location):
        pass


def test_journal_replacement_during_structural_check_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _external = _hot_location(tmp_path)
    assert inspect_database(location).reason == "recovery_needed"
    journal = _journal(location)
    held = tmp_path / "replaced-journal-original"
    original_pread = security_module.os.pread
    replaced = []

    def replace_after_header(descriptor: int, count: int, offset: int) -> bytes:
        data = original_pread(descriptor, count, offset)
        if count == 28 and offset == 0 and not replaced:
            replaced.append(True)
            journal.rename(held)
            shutil.copyfile(held, journal)
            journal.chmod(0o600)
        return data

    monkeypatch.setattr(security_module.os, "pread", replace_after_header)
    with pytest.raises(SQLiteWriterAcquisitionError) as refusal:
        acquire_sqlite_writer_session(location)
    assert replaced == [True]
    assert refusal.value.reason is SQLiteWriterAcquisitionFailureReason.RECOVERY_UNSAFE
    with acquire_state_authority_lock(location):
        pass


@pytest.mark.parametrize("case", ["root", "lock", "database"])
def test_bound_object_replacement_after_locked_recheck_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str,
) -> None:
    location, _external = _hot_location(tmp_path)
    assert inspect_database(location).reason == "recovery_needed"
    original_guard = writer_module._bound_hot_rollback_journal
    displaced = tmp_path / (case + "-displaced")
    reached = []

    def replace_at_guard(binding):
        reached.append(True)
        if case == "root":
            location.state_root.rename(displaced)
            location.state_root.mkdir(mode=0o700)
        else:
            target = location.state_authority_lock_path if case == "lock" else location.database_path
            target.rename(displaced)
            target.write_bytes(b"")
            target.chmod(0o600)
        return original_guard(binding)

    monkeypatch.setattr(writer_module, "_bound_hot_rollback_journal", replace_at_guard)
    try:
        with pytest.raises(SQLiteWriterAcquisitionError) as refusal:
            acquire_sqlite_writer_session(location)
        assert reached == [True]
        assert refusal.value.reason is SQLiteWriterAcquisitionFailureReason.RECOVERY_UNSAFE
    finally:
        if case == "root":
            location.state_root.rmdir()
            displaced.rename(location.state_root)
        else:
            target = location.state_authority_lock_path if case == "lock" else location.database_path
            target.unlink()
            displaced.rename(target)
    with acquire_state_authority_lock(location):
        pass


def test_recovery_private_file_owner_rule_rejects_foreign_uid_metadata(tmp_path: Path) -> None:
    location, _external = _hot_location(tmp_path)
    metadata = list(_journal(location).lstat())
    metadata[stat.ST_UID] = os.getuid() + 1
    with pytest.raises(SQLiteStateError) as refusal:
        security_module._require_recovery_private_file(os.stat_result(metadata))
    assert refusal.value.error_class == "recovery_unsafe"


@pytest.mark.parametrize("case", ["zeroed", "truncated"])
def test_malformed_journal_header_refuses_at_structural_guard(
    tmp_path: Path, case: str,
) -> None:
    location, _external = _hot_location(tmp_path)
    journal = _journal(location)
    with journal.open("r+b") as handle:
        if case == "zeroed":
            handle.write(b"\x00" * 8)
        else:
            handle.truncate(16)
    with acquire_state_authority_lock(location) as lock:
        binding = lock._capture_state_database_authority_binding(location)
        with pytest.raises(SQLiteStateError) as refusal:
            with security_module._bound_hot_rollback_journal(binding):
                pytest.fail("malformed journal admitted")
        assert refusal.value.error_class == "recovery_unsafe"


@pytest.mark.parametrize("case", ["open", "read"])
def test_recovery_open_or_posture_read_failure_is_unresolved_and_releases_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str,
) -> None:
    location, _external = _hot_location(tmp_path)
    assert inspect_database(location).reason == "recovery_needed"
    reached = []
    if case == "open":
        original_open = writer_module._open_bound_existing_sqlite_connection

        def fail_recovery_open(*args, **kwargs):
            if kwargs.get("recovery"):
                reached.append("open")
                raise sqlite3.OperationalError("test-owned recovery open failure")
            return original_open(*args, **kwargs)

        monkeypatch.setattr(writer_module, "_open_bound_existing_sqlite_connection", fail_recovery_open)
    else:
        original_posture = connection_module.apply_observational_connection_posture
        calls = 0

        def fail_third_posture(connection, *, busy_timeout_ms=5000):
            nonlocal calls
            calls += 1
            if calls == 3:
                reached.append("read")
                raise sqlite3.OperationalError("test-owned recovery read failure")
            return original_posture(connection, busy_timeout_ms=busy_timeout_ms)

        monkeypatch.setattr(connection_module, "apply_observational_connection_posture", fail_third_posture)
    with pytest.raises(SQLiteWriterAcquisitionError) as refusal:
        acquire_sqlite_writer_session(location)
    assert reached == [case]
    assert refusal.value.reason is SQLiteWriterAcquisitionFailureReason.RECOVERY_UNRESOLVED
    assert str(location.database_path) not in str(refusal.value)
    with acquire_state_authority_lock(location):
        pass


def test_post_recovery_operational_inspection_failure_is_unresolved_without_issuance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _external = _hot_location(tmp_path)
    assert inspect_database(location).reason == "recovery_needed"
    original_inspect = writer_module.inspect_database
    inspections = []

    def fail_only_post_recovery_inspection(current_location):
        assert current_location is location
        inspections.append(True)
        if len(inspections) == 3:
            assert not _journal(location).exists()
            return migration_module.DatabaseInspection(
                classification=DatabaseClassification.UNKNOWN,
                current_sequence=0,
                latest_sequence=5,
                current_migration_id=None,
                reason="sqlite_posture_unavailable",
            )
        return original_inspect(current_location)

    monkeypatch.setattr(writer_module, "inspect_database", fail_only_post_recovery_inspection)
    with pytest.raises(SQLiteWriterAcquisitionError) as refusal:
        acquire_sqlite_writer_session(location)
    assert refusal.value.reason is SQLiteWriterAcquisitionFailureReason.RECOVERY_UNRESOLVED
    assert len(inspections) == 3
    assert not _journal(location).exists()
    with closing(sqlite3.connect(location.database_path.as_uri() + "?mode=ro", uri=True)) as recovered:
        assert recovered.execute("SELECT generation FROM writer_ownership").fetchone() == (1,)
        assert recovered.execute(
            "SELECT count(*) FROM sqlite_schema WHERE name='fixture_spill'"
        ).fetchone() == (0,)
    with acquire_state_authority_lock(location):
        pass
    monkeypatch.undo()
    next_session = acquire_sqlite_writer_session(location)
    try:
        assert next_session.metadata.generation == 2
    finally:
        next_session.close()


def test_recovery_connection_close_failure_remains_unresolved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _external = _hot_location(tmp_path)
    original_open = writer_module._open_bound_existing_sqlite_connection
    close_calls = []

    class FailFirstClose:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def close(self) -> None:
            close_calls.append(True)
            if len(close_calls) == 1:
                raise sqlite3.OperationalError("test-owned first close failure")
            self.connection.close()

    def wrap_recovery(*args, **kwargs):
        connection = original_open(*args, **kwargs)
        return FailFirstClose(connection) if kwargs.get("recovery") else connection

    monkeypatch.setattr(writer_module, "_open_bound_existing_sqlite_connection", wrap_recovery)
    with pytest.raises(SQLiteWriterAcquisitionError) as refusal:
        acquire_sqlite_writer_session(location)
    assert refusal.value.reason is SQLiteWriterAcquisitionFailureReason.RECOVERY_UNRESOLVED
    assert len(close_calls) == 2
    with acquire_state_authority_lock(location):
        pass
    monkeypatch.undo()
    next_session = acquire_sqlite_writer_session(location)
    try:
        assert next_session.metadata.generation == 2
    finally:
        next_session.close()


def test_recovery_journal_descriptor_close_failure_is_not_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _external = _hot_location(tmp_path)
    journal_inode = _journal(location).stat().st_ino
    original_close = security_module.os.close
    failed = []

    def fail_after_actual_journal_close(descriptor: int) -> None:
        inode = os.fstat(descriptor).st_ino
        original_close(descriptor)
        if inode == journal_inode and not failed:
            failed.append(True)
            raise OSError("test-owned journal descriptor close failure")

    monkeypatch.setattr(security_module.os, "close", fail_after_actual_journal_close)
    with pytest.raises(SQLiteWriterAcquisitionError) as refusal:
        acquire_sqlite_writer_session(location)
    assert failed == [True]
    assert refusal.value.reason is SQLiteWriterAcquisitionFailureReason.RECOVERY_UNRESOLVED
    with acquire_state_authority_lock(location):
        pass


def test_post_recovery_binding_failure_does_not_issue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _external = _hot_location(tmp_path)
    reached = []

    def fail_post_recovery_binding(_binding):
        reached.append(True)
        raise security_module._StateDatabaseAuthorityBindingMismatch(
            SQLiteStateErrorCode.UNSAFE_DATABASE_FILE
        )

    monkeypatch.setattr(writer_module, "_validate_state_database_authority_binding", fail_post_recovery_binding)
    with pytest.raises(SQLiteWriterAcquisitionError) as refusal:
        acquire_sqlite_writer_session(location)
    assert reached == [True]
    assert refusal.value.reason is SQLiteWriterAcquisitionFailureReason.RECOVERY_UNRESOLVED
    assert not _journal(location).exists()
    with closing(sqlite3.connect(location.database_path.as_uri() + "?mode=ro", uri=True)) as recovered:
        assert recovered.execute("SELECT generation FROM writer_ownership").fetchone() == (1,)
    with acquire_state_authority_lock(location):
        pass


@pytest.mark.parametrize("interrupt_type", [KeyboardInterrupt, SystemExit, GeneratorExit])
def test_process_control_at_writable_recovery_boundary_releases_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, interrupt_type: type[BaseException],
) -> None:
    location, _external = _hot_location(tmp_path)
    reached = []
    original_open = writer_module._open_bound_existing_sqlite_connection

    def interrupt_recovery(*args, **kwargs):
        if kwargs.get("recovery"):
            reached.append(True)
            raise interrupt_type
        return original_open(*args, **kwargs)

    monkeypatch.setattr(writer_module, "_open_bound_existing_sqlite_connection", interrupt_recovery)
    with pytest.raises(interrupt_type):
        acquire_sqlite_writer_session(location)
    assert reached == [True]
    with acquire_state_authority_lock(location):
        pass


def test_wal_posture_refuses_without_creating_sidecars(tmp_path: Path) -> None:
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "wal-state")
    initialize_database(location)
    connection = sqlite3.connect(location.database_path, isolation_level=None)
    try:
        assert connection.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
    finally:
        connection.close()
    before = _inventory(location.state_root)
    inspection = inspect_database(location)
    assert inspection.classification is DatabaseClassification.UNKNOWN
    assert inspection.reason != "recovery_needed"
    with pytest.raises(SQLiteWriterAcquisitionError) as blocked:
        acquire_sqlite_writer_session(location)
    assert blocked.value.reason is SQLiteWriterAcquisitionFailureReason.DATABASE_NOT_MANAGED
    assert _inventory(location.state_root) == before


def test_common_lock_holder_prevents_even_blocked_recovery_entry(tmp_path: Path) -> None:
    location, _external = _hot_location(tmp_path)
    before = _inventory(location.state_root)
    with acquire_state_authority_lock(location):
        with pytest.raises(StateAuthorityLockError):
            acquire_sqlite_writer_session(location)
    assert _inventory(location.state_root) == before


@pytest.mark.parametrize("interrupt_type", [KeyboardInterrupt, SystemExit, GeneratorExit])
def test_process_control_at_locked_recheck_releases_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, interrupt_type: type[BaseException]
) -> None:
    location, _external = _hot_location(tmp_path)
    original = writer_module._require_managed_preflight
    calls = 0
    def interrupt_second(current):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise interrupt_type
        return original(current)
    monkeypatch.setattr(writer_module, "_require_managed_preflight", interrupt_second)
    with pytest.raises(interrupt_type):
        acquire_sqlite_writer_session(location)
    assert calls == 2
    with acquire_state_authority_lock(location):
        pass
    assert inspect_database(location).reason == "recovery_needed"
