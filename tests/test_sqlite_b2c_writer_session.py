from __future__ import annotations

import gc
import hashlib
import inspect
import multiprocessing as mp
import os
from pathlib import Path
import sqlite3
import weakref

import pytest

import ge_nwp_coordinator
import ge_nwp_coordinator.sqlite_writer_session as writer_module
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import (
    DatabaseClassification,
    initialize_database,
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
    StateAuthorityLockErrorReason,
    acquire_state_authority_lock,
)
from ge_nwp_coordinator.state_store import MAX_WRITER_GENERATION, WriterSessionError, WriterSessionFailureReason


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MIGRATION_0001_CHECKSUM = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"


def _location(tmp_path: Path) -> CoordinatorStateLocation:
    return CoordinatorStateLocation.from_trusted_root(tmp_path / "state")


def _writer_rows(location: CoordinatorStateLocation) -> list[tuple[object, ...]]:
    with sqlite3.connect(location.database_path) as connection:
        return connection.execute(
            """
            SELECT singleton_id, writer_ref, generation, issued_ref, issuance_nonce_digest, acquired_at
            FROM writer_ownership
            ORDER BY singleton_id
            """
        ).fetchall()


def _writer_generation(location: CoordinatorStateLocation) -> int:
    rows = _writer_rows(location)
    assert len(rows) == 1
    return int(rows[0][2])


def _insert_writer_row(
    location: CoordinatorStateLocation,
    *,
    writer_ref: str = "writer-existing",
    generation: int = 1,
    issued_ref: str = "issuance-existing",
    digest: str = "a" * 64,
    acquired_at: str = "2026-07-16T00:00:00Z",
) -> None:
    with sqlite3.connect(location.database_path) as connection:
        connection.execute(
            """
            INSERT INTO writer_ownership
                (singleton_id, writer_ref, generation, issued_ref, issuance_nonce_digest, acquired_at)
            VALUES (1, ?, ?, ?, ?, ?)
            """,
            (writer_ref, generation, issued_ref, digest, acquired_at),
        )
        connection.commit()


def _insert_malformed_writer_row_ignoring_checks(location: CoordinatorStateLocation, digest: str) -> None:
    with sqlite3.connect(location.database_path) as connection:
        connection.execute("PRAGMA ignore_check_constraints = ON")
        connection.execute(
            """
            INSERT INTO writer_ownership
                (singleton_id, writer_ref, generation, issued_ref, issuance_nonce_digest, acquired_at)
            VALUES (1, 'writer-existing', 1, 'issuance-existing', ?, '2026-07-16T00:00:00Z')
            """,
            (digest,),
        )
        connection.commit()


def _attempt_writer_acquisition(root: str, sender) -> None:
    location = CoordinatorStateLocation.from_trusted_root(Path(root))
    try:
        session = acquire_sqlite_writer_session(location)
    except StateAuthorityLockError as exc:
        sender.send(exc.reason.value)
    except SQLiteWriterAcquisitionError as exc:
        sender.send(exc.reason.value)
    else:
        try:
            sender.send(f"acquired:{session.metadata.generation}")
        finally:
            session.close()
    finally:
        sender.close()


def _crash_after_writer_acquisition(root: str, sender) -> None:
    location = CoordinatorStateLocation.from_trusted_root(Path(root))
    session = acquire_sqlite_writer_session(location)
    sender.send(session.metadata.generation)
    os._exit(0)


def _run_writer_attempt(location: CoordinatorStateLocation) -> str:
    context = mp.get_context("fork")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_attempt_writer_acquisition, args=(str(location.state_root), sender))
    process.start()
    sender.close()
    result = receiver.recv()
    receiver.close()
    process.join(5)
    assert process.exitcode == 0
    return result


def test_absent_empty_and_unknown_databases_refuse_without_writer_row_or_lock(tmp_path: Path) -> None:
    absent = _location(tmp_path / "absent")
    with pytest.raises(SQLiteWriterAcquisitionError) as absent_error:
        acquire_sqlite_writer_session(absent)
    assert absent_error.value.reason is SQLiteWriterAcquisitionFailureReason.DATABASE_NOT_MANAGED
    assert not absent.state_root.exists()

    empty = _location(tmp_path / "empty")
    empty.state_root.mkdir(mode=0o700, parents=True)
    empty.database_path.write_bytes(b"")
    empty.database_path.chmod(0o600)
    with pytest.raises(SQLiteWriterAcquisitionError) as empty_error:
        acquire_sqlite_writer_session(empty)
    assert empty_error.value.reason is SQLiteWriterAcquisitionFailureReason.DATABASE_NOT_MANAGED
    assert not empty.state_authority_lock_path.exists()

    unknown = _location(tmp_path / "unknown")
    unknown.state_root.mkdir(mode=0o700, parents=True)
    unknown.database_path.write_bytes(b"not-sqlite")
    unknown.database_path.chmod(0o600)
    with pytest.raises(SQLiteWriterAcquisitionError) as unknown_error:
        acquire_sqlite_writer_session(unknown)
    assert unknown_error.value.reason is SQLiteWriterAcquisitionFailureReason.DATABASE_NOT_MANAGED
    assert not unknown.state_authority_lock_path.exists()


def test_managed_database_acquires_and_increments_generations(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)

    session = acquire_sqlite_writer_session(location)
    assert session.active is True
    assert session.metadata.generation == 1
    assert session.metadata.writer_ref.startswith("writer-")
    assert session.metadata.issued_ref.startswith("issuance-")
    assert _writer_generation(location) == 1
    first_row = _writer_rows(location)[0]

    session.close()
    assert session.active is False
    assert _writer_rows(location)[0] == first_row

    generations: list[int] = []
    for _index in range(4):
        next_session = acquire_sqlite_writer_session(location)
        generations.append(next_session.metadata.generation)
        next_session.close()

    assert generations == [2, 3, 4, 5]
    assert _writer_generation(location) == 5
    assert len(_writer_rows(location)) == 1


def test_generation_zero_malformed_row_and_max_generation_fail_closed(tmp_path: Path) -> None:
    zero_location = _location(tmp_path / "zero")
    initialize_database(zero_location)
    _insert_writer_row(zero_location, generation=0)
    assert validate_database(zero_location).classification is DatabaseClassification.MANAGED

    with pytest.raises(SQLiteWriterAcquisitionError) as zero_error:
        acquire_sqlite_writer_session(zero_location)
    assert zero_error.value.reason is SQLiteWriterAcquisitionFailureReason.WRITER_STATE_MALFORMED

    max_location = _location(tmp_path / "max")
    initialize_database(max_location)
    _insert_writer_row(max_location, generation=MAX_WRITER_GENERATION)
    with pytest.raises(SQLiteWriterAcquisitionError) as max_error:
        acquire_sqlite_writer_session(max_location)
    assert max_error.value.reason is SQLiteWriterAcquisitionFailureReason.WRITER_GENERATION_EXHAUSTED
    assert _writer_generation(max_location) == MAX_WRITER_GENERATION


def test_malformed_digest_row_uses_writer_state_malformed_reason(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    _insert_malformed_writer_row_ignoring_checks(location, "B" * 64)

    with pytest.raises(SQLiteWriterAcquisitionError) as exc_info:
        acquire_sqlite_writer_session(location)
    assert exc_info.value.reason is SQLiteWriterAcquisitionFailureReason.WRITER_STATE_MALFORMED


def test_writer_row_parser_rejects_malformed_singleton_shapes() -> None:
    valid_digest = "b" * 64
    valid_time = "2026-07-16T00:00:00Z"
    malformed_rows = (
        [(1, "writer-a", True, "issuance-a", valid_digest, valid_time)],
        [(2, "writer-a", 1, "issuance-a", valid_digest, valid_time)],
        [(1, "writer-a", -1, "issuance-a", valid_digest, valid_time)],
        [(1, "writer-a", 1, "issuance-a", "B" * 64, valid_time)],
        [(1, "writer-a", 1, "issuance-a", valid_digest, "not-a-time")],
        [(1, "writer-a", 1, "issuance-a", valid_digest, valid_time, "extra")],
        [
            (1, "writer-a", 1, "issuance-a", valid_digest, valid_time),
            (1, "writer-b", 2, "issuance-b", valid_digest, valid_time),
        ],
    )
    for rows in malformed_rows:
        with pytest.raises(SQLiteWriterAcquisitionError) as exc_info:
            writer_module._parse_writer_ownership_rows(rows)
        assert exc_info.value.reason is SQLiteWriterAcquisitionFailureReason.WRITER_STATE_MALFORMED


def test_proof_digest_vector_verification_and_safe_containment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vector = writer_module._compute_issuance_proof_digest(
        "writer-vector",
        42,
        "issuance-vector",
        bytes(range(32)),
    )
    assert vector == "9294210209ece3194e8bf1396d1bb17e17d946dd36bcf0e3bdfb501b21399e5a"

    compare_calls: list[tuple[str, str]] = []
    original_compare = writer_module.hmac.compare_digest

    def tracking_compare(left: str, right: str) -> bool:
        compare_calls.append((left, right))
        return original_compare(left, right)

    monkeypatch.setattr(writer_module.hmac, "compare_digest", tracking_compare)
    assert writer_module._verify_issuance_proof_digest(
        "writer-vector",
        42,
        "issuance-vector",
        bytes(range(32)),
        vector,
    )
    assert compare_calls

    location = _location(tmp_path)
    initialize_database(location)
    proof = bytearray(b"P" * 32)
    monkeypatch.setattr(writer_module, "_generate_private_proof", lambda: proof)

    session = acquire_sqlite_writer_session(location)
    row = _writer_rows(location)[0]
    stored_digest = str(row[4])
    assert stored_digest == writer_module._compute_issuance_proof_digest(
        session.metadata.writer_ref,
        session.metadata.generation,
        session.metadata.issued_ref,
        proof,
    )
    assert writer_module._verify_issuance_proof_digest(
        session.metadata.writer_ref,
        session.metadata.generation,
        session.metadata.issued_ref,
        proof,
        stored_digest,
    )
    assert not writer_module._verify_issuance_proof_digest(
        session.metadata.writer_ref,
        session.metadata.generation,
        session.metadata.issued_ref,
        bytearray(b"Q" * 32),
        stored_digest,
    )
    serialized_row = repr(row)
    assert "50" * 32 not in serialized_row
    assert b"P" * 32 not in location.database_path.read_bytes()
    assert "proof" not in repr(session.metadata).lower()
    assert "digest" not in repr(session.metadata).lower()
    assert "proof" not in repr(session._resource._credential).lower()
    assert "digest" not in repr(session._resource._credential).lower()
    assert stored_digest not in repr(session.metadata)

    buffer = session._resource._credential._proof
    assert buffer is proof
    session.close()
    assert set(proof) == {0}


def test_precommit_failure_overwrites_proof_leaves_no_row_and_releases_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    proof = bytearray(b"A" * 32)
    monkeypatch.setattr(writer_module, "_generate_private_proof", lambda: proof)

    def fail_before_write(*args, **kwargs) -> None:
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_ACQUISITION_FAILED)

    monkeypatch.setattr(writer_module, "_write_durable_writer_issuance", fail_before_write)
    with pytest.raises(SQLiteWriterAcquisitionError) as exc_info:
        acquire_sqlite_writer_session(location)
    assert exc_info.value.reason is SQLiteWriterAcquisitionFailureReason.WRITER_ACQUISITION_FAILED
    assert _writer_rows(location) == []
    assert set(proof) == {0}
    with acquire_state_authority_lock(location):
        pass


def test_failure_after_row_write_before_commit_rolls_back_and_clears_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    proof = bytearray(b"B" * 32)
    monkeypatch.setattr(writer_module, "_generate_private_proof", lambda: proof)

    def fail_after_write(*args, **kwargs) -> None:
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_ACQUISITION_FAILED)

    monkeypatch.setattr(writer_module, "_require_persisted_matches", fail_after_write)
    with pytest.raises(SQLiteWriterAcquisitionError):
        acquire_sqlite_writer_session(location)
    assert _writer_rows(location) == []
    assert set(proof) == {0}


def test_postcommit_session_publication_failure_consumes_generation_and_releases_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    proof = bytearray(b"C" * 32)
    monkeypatch.setattr(writer_module, "_generate_private_proof", lambda: proof)
    original_factory = writer_module._SESSION_FACTORY

    def fail_publication(resource) -> object:
        raise RuntimeError("test publication failure")

    monkeypatch.setattr(writer_module, "_SESSION_FACTORY", fail_publication)
    with pytest.raises(SQLiteWriterAcquisitionError) as exc_info:
        acquire_sqlite_writer_session(location)
    assert exc_info.value.reason is SQLiteWriterAcquisitionFailureReason.WRITER_ACQUISITION_FAILED
    assert _writer_generation(location) == 1
    assert set(proof) == {0}

    monkeypatch.setattr(writer_module, "_SESSION_FACTORY", original_factory)
    next_session = acquire_sqlite_writer_session(location)
    try:
        assert next_session.metadata.generation == 2
    finally:
        next_session.close()


def test_writer_update_uses_expected_previous_generation_and_keeps_singleton(tmp_path: Path) -> None:
    source = Path(writer_module.__file__).read_text(encoding="utf-8")
    assert "WHERE singleton_id = 1 AND generation = ?" in source
    assert "cursor.rowcount != 1" in source

    location = _location(tmp_path)
    initialize_database(location)
    first = acquire_sqlite_writer_session(location)
    first.close()
    second = acquire_sqlite_writer_session(location)
    second.close()

    rows = _writer_rows(location)
    assert len(rows) == 1
    assert rows[0][0] == 1
    assert rows[0][2] == 2


def test_active_writer_session_blocks_initialize_and_migrate_but_not_validate(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    try:
        with pytest.raises(StateAuthorityLockError) as initialize_error:
            initialize_database(location)
        assert initialize_error.value.reason is StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_BUSY

        with pytest.raises(StateAuthorityLockError) as migrate_error:
            migrate_database(location)
        assert migrate_error.value.reason is StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_BUSY

        assert validate_database(location).classification is DatabaseClassification.MANAGED
    finally:
        session.close()


def test_abandoned_session_finalizer_releases_lock_and_clears_registry(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    reference = weakref.ref(session)
    key = session._resource._registry_key

    del session
    gc.collect()

    assert reference() is None
    assert key not in writer_module._ACTIVE_SESSION_RESOURCES
    assert _run_writer_attempt(location) == "acquired:2"


def test_cross_process_exclusion_and_process_crash_generation_skip(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    try:
        assert _run_writer_attempt(location) == "state_authority_lock_busy"
    finally:
        session.close()

    crash_location = _location(tmp_path / "crash")
    initialize_database(crash_location)
    context = mp.get_context("fork")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_crash_after_writer_acquisition, args=(str(crash_location.state_root), sender))
    process.start()
    sender.close()
    assert receiver.recv() == 1
    receiver.close()
    process.join(5)
    assert process.exitcode == 0

    next_session = acquire_sqlite_writer_session(crash_location)
    try:
        assert next_session.metadata.generation == 2
    finally:
        next_session.close()


def test_session_lifecycle_context_manager_and_mutation_unavailable_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    assert session.active is True
    assert session.metadata.generation == 1

    with session as entered:
        assert entered is session

    assert session.active is False
    assert session.metadata.generation == 1
    session.close()
    with pytest.raises(WriterSessionError) as closed_enter:
        session.__enter__()
    assert closed_enter.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED

    active = acquire_sqlite_writer_session(location)
    calls = 0

    def fail_if_sqlite_opens(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("mutation path opened SQLite")

    monkeypatch.setattr(writer_module, "open_existing_sqlite_connection", fail_if_sqlite_opens)
    with pytest.raises(WriterSessionError) as mutation_error:
        active.apply_transition(None, None)  # type: ignore[arg-type]
    assert mutation_error.value.reason is WriterSessionFailureReason.WRITER_SESSION_MUTATION_UNAVAILABLE
    with pytest.raises(WriterSessionError) as global_stop_error:
        active.apply_global_stop_update(None, None)  # type: ignore[arg-type]
    assert global_stop_error.value.reason is WriterSessionFailureReason.WRITER_SESSION_MUTATION_UNAVAILABLE
    assert calls == 0
    active.close()
    with pytest.raises(WriterSessionError) as closed_mutation:
        active.apply_transition(None, None)  # type: ignore[arg-type]
    assert closed_mutation.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED


def test_process_mismatch_fails_locally_without_private_detail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    owner_pid = os.getpid()
    monkeypatch.setattr(writer_module.os, "getpid", lambda: owner_pid + 1)

    with pytest.raises(WriterSessionError) as exc_info:
        session.apply_transition(None, None)  # type: ignore[arg-type]
    assert exc_info.value.reason is WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH
    assert str(owner_pid) not in str(exc_info.value)


def test_fork_child_session_is_invalidated_and_parent_remains_active(tmp_path: Path) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        try:
            try:
                session.apply_transition(None, None)  # type: ignore[arg-type]
            except WriterSessionError as exc:
                reason = exc.reason.value
            else:
                reason = "unexpected-active"
            proof_state = "cleared" if session._resource._credential is None else "kept"
            os.write(write_fd, f"{reason}:{proof_state}".encode("ascii"))
        finally:
            os.close(write_fd)
            os._exit(0)

    os.close(write_fd)
    child_result = os.read(read_fd, 256).decode("ascii")
    os.close(read_fd)
    waited_pid, status = os.waitpid(child_pid, 0)
    assert waited_pid == child_pid
    assert status == 0
    assert child_result == "writer_session_process_mismatch:cleared"
    assert session.active is True
    assert _run_writer_attempt(location) == "state_authority_lock_busy"
    session.close()
    assert _run_writer_attempt(location) == "acquired:2"


def test_fork_child_does_not_prolong_lock_after_parent_close(tmp_path: Path) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    child_ready_read, child_ready_write = os.pipe()
    release_read, release_write = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(child_ready_read)
        os.close(release_write)
        try:
            os.write(child_ready_write, b"ready")
            os.read(release_read, 1)
        finally:
            os.close(child_ready_write)
            os.close(release_read)
            os._exit(0)

    os.close(child_ready_write)
    os.close(release_read)
    assert os.read(child_ready_read, 5) == b"ready"
    os.close(child_ready_read)
    session.close()
    assert _run_writer_attempt(location) == "acquired:2"
    os.write(release_write, b"x")
    os.close(release_write)
    waited_pid, status = os.waitpid(child_pid, 0)
    assert waited_pid == child_pid
    assert status == 0


def test_fork_child_callback_does_not_unlock_or_acquire_inherited_locks() -> None:
    source = "\n".join(
        inspect.getsource(function)
        for function in (
            writer_module._at_fork_child,
            writer_module._WriterSessionResource.mark_closed_after_fork,
            writer_module._PrivateWriterCredential.overwrite_and_drop,
            writer_module._overwrite_proof_buffer,
        )
    )
    assert "LOCK_UN" not in source
    assert ".acquire(" not in source


def test_runtime_boundaries_exports_schema_and_no_b3_b4_surfaces() -> None:
    package_exports = set(ge_nwp_coordinator.__all__)
    assert "acquire_sqlite_writer_session" not in package_exports
    assert "SQLiteWriterAcquisitionError" not in package_exports
    assert "_SQLiteWriterSession" not in package_exports
    assert not hasattr(ge_nwp_coordinator, "acquire_sqlite_writer_session")
    assert not hasattr(ge_nwp_coordinator, "_SQLiteWriterSession")

    source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src").rglob("*.py"))
    for forbidden in (
        "def current_writer",
        "def read_latest_writer_issuance",
        "get_writer_credential",
        "get_writer_proof",
        "get_writer_digest",
        "class SQLiteStateStore",
        "class SqliteStateStore",
        "INSERT INTO transition_events",
        "INSERT INTO global_stop_events",
        "UPDATE work_items",
        "UPDATE global_stop_current",
        "CoordinatorService",
        "Scheduler",
        "QueueConsumer",
        "subprocess",
        "socket",
        "requests",
        "urllib",
    ):
        assert forbidden not in source

    migrations = sorted(path.name for path in (ROOT / "src/ge_nwp_coordinator/sqlite_migrations").glob("*.sql"))
    assert migrations == ["0001_initial.sql"]
    migration_bytes = (ROOT / "src/ge_nwp_coordinator/sqlite_migrations/0001_initial.sql").read_bytes()
    assert hashlib.sha256(migration_bytes).hexdigest() == EXPECTED_MIGRATION_0001_CHECKSUM
