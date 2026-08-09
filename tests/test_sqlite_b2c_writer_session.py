from __future__ import annotations

import ast
import gc
import hashlib
import inspect
import multiprocessing as mp
import os
from pathlib import Path
import select
import signal
import sqlite3
import threading
import time
import traceback
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
    StateAuthorityLock,
    StateAuthorityLockError,
    StateAuthorityLockErrorReason,
    acquire_state_authority_lock,
)
from ge_nwp_coordinator.state_store import (
    GlobalStopApplyPreflightError,
    GlobalStopApplyPreflightFailureReason,
    MAX_WRITER_GENERATION,
    TransitionApplyPreflightError,
    TransitionApplyPreflightFailureReason,
    WriterSessionError,
    WriterSessionFailureReason,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MIGRATION_0001_CHECKSUM = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"


def _contains_requests_client_usage(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name == "requests" or alias.name.startswith("requests.")
            for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and (
            node.module == "requests"
            or (node.module or "").startswith("requests.")
        ):
            return True
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "requests"
        ):
            return True
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        if node.args[0].value != "requests":
            continue
        if isinstance(function, ast.Name) and function.id == "__import__":
            return True
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "importlib"
            and function.attr == "import_module"
        ):
            return True
    return False


def _assert_no_requests_client_usage(paths: tuple[Path, ...]) -> None:
    accepted = (
        "class Example:\n    max_pull_requests = 1\n"
        "payload = {'max_pull_requests': 1}\n"
        "def max_pull_requests() -> int:\n    return 1\n"
    )
    rejected = (
        "import requests\n",
        "import requests as rq\nrq.get(...)\n",
        "from requests import get\nget(...)\n",
        "from requests import get as http_get\nhttp_get(...)\n",
        "requests.get(...)\n",
        "__import__('requests')\n",
        "importlib.import_module('requests')\n",
    )
    assert not _contains_requests_client_usage(accepted)
    assert all(_contains_requests_client_usage(source) for source in rejected)
    assert not any(
        _contains_requests_client_usage(path.read_text(encoding="utf-8"))
        for path in paths
    )


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


def _operation_count(resource) -> int:
    return len(resource._active_operations)


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


def _insert_writer_row_ignoring_checks(
    location: CoordinatorStateLocation,
    *,
    generation: object,
    writer_ref: str = "writer-existing",
    issued_ref: str = "issuance-existing",
    digest: str = "a" * 64,
    acquired_at: str = "2026-07-16T00:00:00Z",
) -> None:
    with sqlite3.connect(location.database_path) as connection:
        connection.execute("PRAGMA ignore_check_constraints = ON")
        connection.execute(
            """
            INSERT INTO writer_ownership
                (singleton_id, writer_ref, generation, issued_ref, issuance_nonce_digest, acquired_at)
            VALUES (1, ?, ?, ?, ?, ?)
            """,
            (writer_ref, generation, issued_ref, digest, acquired_at),
        )
        connection.commit()


def _wait_for_child_result(pid: int, read_fd: int, *, timeout: float = 3.0) -> str:
    os.set_blocking(read_fd, False)
    deadline = time.monotonic() + timeout
    chunks: list[bytes] = []
    while time.monotonic() < deadline:
        ready, _, _ = select.select([read_fd], [], [], 0.05)
        if ready:
            try:
                chunk = os.read(read_fd, 4096)
            except BlockingIOError:
                chunk = b""
            if chunk:
                chunks.append(chunk)
        waited_pid, status = os.waitpid(pid, os.WNOHANG)
        if waited_pid:
            assert status == 0
            return b"".join(chunks).decode("ascii")
    os.kill(pid, signal.SIGKILL)
    os.waitpid(pid, 0)
    pytest.fail("child did not finish before timeout")


def _read_pipe_message(read_fd: int, *, timeout: float = 3.0) -> str:
    os.set_blocking(read_fd, False)
    deadline = time.monotonic() + timeout
    chunks: list[bytes] = []
    while time.monotonic() < deadline:
        ready, _, _ = select.select([read_fd], [], [], 0.05)
        if ready:
            try:
                chunk = os.read(read_fd, 4096)
            except BlockingIOError:
                chunk = b""
            if chunk:
                chunks.append(chunk)
                return b"".join(chunks).decode("ascii")
    pytest.fail("child did not write before timeout")


def _hold_condition(resource, held: threading.Event, release: threading.Event) -> None:
    resource._condition.acquire()
    try:
        held.set()
        assert release.wait(10)
    finally:
        resource._condition.release()


def _wait_for_event(event: threading.Event, *, timeout: float = 2.0) -> None:
    assert event.wait(timeout)


def _join_thread(thread: threading.Thread, *, timeout: float = 2.0) -> None:
    thread.join(timeout)
    assert not thread.is_alive()


def _render_exception_graph(exc: BaseException) -> str:
    rendered: list[str] = []
    pending = [exc]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        rendered.extend(
            (
                type(current).__name__,
                str(current),
                repr(current),
                repr(current.args),
                repr(getattr(current, "__notes__", None)),
                "".join(traceback.format_exception(type(current), current, current.__traceback__)),
            )
        )
        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)
    return "\n".join(rendered)


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
    zero_inspection = validate_database(zero_location)
    assert zero_inspection.classification is DatabaseClassification.UNKNOWN
    assert zero_inspection.reason == "schema_verification_failed"

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


def test_writer_generation_semantics_match_between_validation_and_acquisition(tmp_path: Path) -> None:
    absent_row_location = _location(tmp_path / "absent-row")
    initialize_database(absent_row_location)
    assert validate_database(absent_row_location).classification is DatabaseClassification.MANAGED
    first = acquire_sqlite_writer_session(absent_row_location)
    assert first.metadata.generation == 1
    first.close()

    generation_one_location = _location(tmp_path / "generation-one")
    initialize_database(generation_one_location)
    _insert_writer_row(generation_one_location, generation=1)
    assert validate_database(generation_one_location).classification is DatabaseClassification.MANAGED
    second = acquire_sqlite_writer_session(generation_one_location)
    assert second.metadata.generation == 2
    second.close()

    max_location = _location(tmp_path / "maximum")
    initialize_database(max_location)
    _insert_writer_row(max_location, generation=MAX_WRITER_GENERATION)
    assert validate_database(max_location).classification is DatabaseClassification.MANAGED
    with pytest.raises(SQLiteWriterAcquisitionError) as max_error:
        acquire_sqlite_writer_session(max_location)
    assert max_error.value.reason is SQLiteWriterAcquisitionFailureReason.WRITER_GENERATION_EXHAUSTED

    malformed_generations = (0, -1, str(MAX_WRITER_GENERATION + 1))
    for index, generation in enumerate(malformed_generations):
        location = _location(tmp_path / f"malformed-{index}")
        initialize_database(location)
        _insert_writer_row_ignoring_checks(location, generation=generation)
        inspection = validate_database(location)
        assert inspection.classification is DatabaseClassification.UNKNOWN
        assert inspection.reason == "schema_verification_failed"
        with pytest.raises(SQLiteWriterAcquisitionError) as exc_info:
            acquire_sqlite_writer_session(location)
        assert exc_info.value.reason is SQLiteWriterAcquisitionFailureReason.WRITER_STATE_MALFORMED


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
        [(1, "writer-a", 0, "issuance-a", valid_digest, valid_time)],
        [(1, "writer-a", True, "issuance-a", valid_digest, valid_time)],
        [(2, "writer-a", 1, "issuance-a", valid_digest, valid_time)],
        [(1, "writer-a", -1, "issuance-a", valid_digest, valid_time)],
        [(1, "writer-a", MAX_WRITER_GENERATION + 1, "issuance-a", valid_digest, valid_time)],
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


def test_foreign_process_cleanup_clears_authority_and_active_registry_idempotently(tmp_path: Path) -> None:
    location = _location(tmp_path / "primary")
    other_location = _location(tmp_path / "other")
    initialize_database(location)
    initialize_database(other_location)
    session = acquire_sqlite_writer_session(location)
    other_session = acquire_sqlite_writer_session(other_location)
    resource = session._resource
    other_resource = other_session._resource
    registry_key = resource._registry_key
    other_registry_key = other_resource._registry_key
    proof = resource._credential._proof
    retained_lock = resource._authority_lock
    prior_generation = session.metadata.generation

    try:
        assert writer_module._ACTIVE_SESSION_RESOURCES.get(registry_key) is resource
        assert writer_module._ACTIVE_SESSION_RESOURCES.get(other_registry_key) is other_resource

        resource.cleanup_from_foreign_process()

        assert resource._state == writer_module._FORK_INVALID
        assert resource._owner_pid == -1
        assert resource._credential is None
        assert resource._authority_lock is None
        assert resource._database_binding is None
        assert resource._mutation_slot is None
        assert _operation_count(resource) == 0
        assert set(proof) == {0}
        assert registry_key not in writer_module._ACTIVE_SESSION_RESOURCES
        assert writer_module._ACTIVE_SESSION_RESOURCES.get(other_registry_key) is other_resource

        resource.cleanup_from_foreign_process()

        assert registry_key not in writer_module._ACTIVE_SESSION_RESOURCES
        assert writer_module._ACTIVE_SESSION_RESOURCES.get(other_registry_key) is other_resource
    finally:
        if retained_lock is not None:
            retained_lock.close()
        session.close()
        other_session.close()

    next_session = acquire_sqlite_writer_session(location)
    try:
        assert next_session.metadata.generation == prior_generation + 1
    finally:
        next_session.close()


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
    with pytest.raises(TransitionApplyPreflightError) as mutation_error:
        active.apply_transition(None)  # type: ignore[arg-type]
    assert mutation_error.value.reason is TransitionApplyPreflightFailureReason.INVALID_COMMAND
    with pytest.raises(GlobalStopApplyPreflightError) as global_stop_error:
        active.apply_global_stop_update(None, None)  # type: ignore[arg-type]
    assert global_stop_error.value.reason is GlobalStopApplyPreflightFailureReason.INVALID_COMMAND
    assert calls == 0
    active.close()
    with pytest.raises(WriterSessionError) as closed_mutation:
        active.apply_transition(None)  # type: ignore[arg-type]
    assert closed_mutation.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED
    assert _operation_count(active._resource) == 0


def test_process_mismatch_fails_locally_without_private_detail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    owner_pid = os.getpid()
    resource = session._resource
    registry_key = resource._registry_key
    proof = resource._credential._proof
    retained_lock = resource._authority_lock

    with monkeypatch.context() as pid_patch:
        pid_patch.setattr(writer_module.os, "getpid", lambda: owner_pid + 1)
        with pytest.raises(WriterSessionError) as exc_info:
            session.apply_transition(None)  # type: ignore[arg-type]
    assert exc_info.value.reason is WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH
    assert str(owner_pid) not in str(exc_info.value)
    assert registry_key not in writer_module._ACTIVE_SESSION_RESOURCES
    assert resource._state == writer_module._FORK_INVALID
    assert resource._credential is None
    assert resource._authority_lock is None
    assert resource._database_binding is None
    assert resource._mutation_slot is None
    assert set(proof) == {0}
    assert _operation_count(resource) == 0
    assert str(registry_key) not in _render_exception_graph(exc_info.value)
    if retained_lock is not None:
        retained_lock.close()
    session.close()


@pytest.mark.parametrize("mutation_method_name", ("apply_transition", "apply_global_stop_update"))
def test_inactive_retained_lock_mutation_method_unwinds_registration_and_closes_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation_method_name: str,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    prior_generation = session.metadata.generation
    resource = session._resource
    registry_key = resource._registry_key
    proof = resource._credential._proof
    retained_lock = resource._authority_lock
    assert retained_lock is not None
    assert isinstance(retained_lock, StateAuthorityLock)
    assert retained_lock is resource._authority_lock

    sqlite_open_calls = 0

    def fail_if_sqlite_opens(*args, **kwargs):
        nonlocal sqlite_open_calls
        sqlite_open_calls += 1
        raise AssertionError("mutation path opened SQLite")

    with monkeypatch.context() as mutation_guard:
        mutation_guard.setattr(writer_module, "open_existing_sqlite_connection", fail_if_sqlite_opens)
        retained_lock.close()
        assert retained_lock.active is False

        result: dict[str, object | None] = {"returned": None, "error": None}

        def invoke_mutation_method() -> None:
            try:
                if mutation_method_name == "apply_transition":
                    result["returned"] = session.apply_transition(None)  # type: ignore[arg-type]
                else:
                    result["returned"] = session.apply_global_stop_update(None, None)  # type: ignore[arg-type]
            except BaseException as exc:  # noqa: BLE001 - test must capture thread failures
                result["error"] = exc

        mutation_thread = threading.Thread(target=invoke_mutation_method)
        mutation_thread.start()
        _join_thread(mutation_thread)

        error = result["error"]
        assert isinstance(error, WriterSessionError)
        assert error.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED
        assert error.reason is not WriterSessionFailureReason.WRITER_SESSION_MUTATION_UNAVAILABLE
        assert result["returned"] is None
        assert _operation_count(resource) == 0
        assert session.active is False
        assert resource._state == writer_module._CLOSED
        assert resource._credential is None
        assert resource._authority_lock is None
        assert set(proof) == {0}
        assert retained_lock.active is False
        assert sqlite_open_calls == 0
        assert registry_key not in writer_module._ACTIVE_SESSION_RESOURCES

    next_session = acquire_sqlite_writer_session(location)
    try:
        later_registry_key = next_session._resource._registry_key
        assert next_session.metadata.generation == prior_generation + 1
        assert next_session.metadata.writer_ref.startswith("writer-")
        assert next_session.metadata.issued_ref.startswith("issuance-")
    finally:
        next_session.close()
    assert later_registry_key not in writer_module._ACTIVE_SESSION_RESOURCES


def test_foreign_process_cleanup_replaces_locked_session_synchronization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    registry_key = resource._registry_key
    proof = resource._credential._proof
    retained_lock = resource._authority_lock
    old_condition = resource._condition
    old_condition.acquire()
    owner_pid = os.getpid()
    results: list[str] = []

    def call_active_with_foreign_pid() -> None:
        try:
            results.append(str(session.active))
        except BaseException as exc:  # noqa: BLE001 - test must surface unexpected safe class
            results.append(exc.__class__.__name__)

    try:
        with monkeypatch.context() as pid_patch:
            pid_patch.setattr(writer_module.os, "getpid", lambda: owner_pid + 1)
            thread = threading.Thread(target=call_active_with_foreign_pid)
            thread.start()
            thread.join(1)
            assert not thread.is_alive()
            assert results == ["False"]
            assert resource._condition is not old_condition
            assert resource._state == writer_module._FORK_INVALID
            assert resource._credential is None
            assert resource._authority_lock is None
            assert resource._database_binding is None
            assert resource._mutation_slot is None
            assert set(proof) == {0}
            assert _operation_count(resource) == 0
            assert registry_key not in writer_module._ACTIVE_SESSION_RESOURCES
    finally:
        old_condition.release()
        if retained_lock is not None:
            retained_lock.close()
        session.close()


def test_nested_operation_leases_are_independent_identities(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource

    first = resource.operation_guard(session)
    second = resource.operation_guard(session)
    assert _operation_count(resource) == 2

    first._close()
    first._close()
    assert _operation_count(resource) == 1
    assert session.active is True

    second._close()
    assert _operation_count(resource) == 0
    session.close()
    assert _run_writer_attempt(location) == "acquired:2"


def test_same_thread_close_during_operation_fails_without_releasing_authority(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    proof = resource._credential._proof
    lease = resource.operation_guard(session)

    with pytest.raises(WriterSessionError) as exc_info:
        session.close()
    assert exc_info.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSE_DURING_OPERATION
    assert resource._state == writer_module._ACTIVE
    assert _operation_count(resource) == 1
    assert resource._credential is not None
    assert resource._authority_lock is not None
    assert set(proof) != {0}
    assert _run_writer_attempt(location) == "state_authority_lock_busy"

    lease._close()
    session.close()
    assert resource._state == writer_module._CLOSED
    assert set(proof) == {0}
    assert _run_writer_attempt(location) == "acquired:2"


def test_operation_guard_close_waits_and_retains_authority_until_exit(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    proof = resource._credential._proof
    lease = resource.operation_guard(session)
    assert _operation_count(resource) == 1

    close_finished = threading.Event()

    def close_session() -> None:
        session.close()
        close_finished.set()

    closer = threading.Thread(target=close_session)
    closer.start()
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        with resource._condition:
            if resource._state == writer_module._CLOSING:
                break
        time.sleep(0.01)
    assert resource._state == writer_module._CLOSING
    assert not close_finished.is_set()
    assert session.active is False
    assert resource._credential is not None
    assert resource._authority_lock is not None
    assert set(proof) != {0}
    assert _run_writer_attempt(location) == "state_authority_lock_busy"

    with pytest.raises(WriterSessionError) as closing_error:
        session.apply_transition(None)  # type: ignore[arg-type]
    assert closing_error.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED
    assert _operation_count(resource) == 1

    lease._close()
    closer.join(2)
    assert close_finished.is_set()
    assert _operation_count(resource) == 0
    assert resource._state == writer_module._CLOSED
    assert resource._credential is None
    assert resource._authority_lock is None
    assert set(proof) == {0}
    session.close()
    assert _run_writer_attempt(location) == "acquired:2"


def test_concurrent_close_waits_until_authoritative_cleanup_completes(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    authority_lock = resource._authority_lock
    original_close = authority_lock.close
    cleanup_started = threading.Event()
    release_cleanup = threading.Event()
    cleanup_done = threading.Event()
    first_done = threading.Event()
    second_done = threading.Event()
    close_call_count = 0
    close_call_lock = threading.Lock()

    def slow_authority_close() -> None:
        nonlocal close_call_count
        with close_call_lock:
            close_call_count += 1
        cleanup_started.set()
        _wait_for_event(release_cleanup, timeout=5.0)
        try:
            original_close()
        finally:
            cleanup_done.set()

    authority_lock.close = slow_authority_close

    first = threading.Thread(target=lambda: (session.close(), first_done.set()))
    first.start()
    _wait_for_event(cleanup_started)
    assert resource._state == writer_module._CLEANING

    second = threading.Thread(target=lambda: (session.close(), second_done.set()))
    second.start()
    second_returned_before_cleanup = second_done.wait(0.25)
    assert second_returned_before_cleanup is False
    assert cleanup_done.is_set() is False
    assert resource._state == writer_module._CLEANING
    with pytest.raises(StateAuthorityLockError) as busy_error:
        acquire_state_authority_lock(location)
    assert busy_error.value.reason is StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_BUSY

    release_cleanup.set()
    _join_thread(first)
    _join_thread(second)
    assert first_done.is_set()
    assert second_done.is_set()
    assert cleanup_done.is_set()
    assert resource._state == writer_module._CLOSED
    assert close_call_count == 1
    assert _run_writer_attempt(location) == "acquired:2"


def test_many_concurrent_close_callers_share_one_cleanup(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    authority_lock = resource._authority_lock
    original_close = authority_lock.close
    start = threading.Barrier(6)
    close_call_count = 0
    close_call_lock = threading.Lock()
    errors: list[BaseException] = []

    def counted_authority_close() -> None:
        nonlocal close_call_count
        with close_call_lock:
            close_call_count += 1
        time.sleep(0.05)
        original_close()

    authority_lock.close = counted_authority_close

    def close_session() -> None:
        try:
            start.wait(2)
            session.close()
        except BaseException as exc:  # noqa: BLE001 - test collects thread failures
            errors.append(exc)

    threads = [threading.Thread(target=close_session) for _index in range(5)]
    for thread in threads:
        thread.start()
    start.wait(2)
    for thread in threads:
        _join_thread(thread)

    assert errors == []
    assert resource._state == writer_module._CLOSED
    assert close_call_count == 1
    session.close()
    assert close_call_count == 1
    assert _run_writer_attempt(location) == "acquired:2"


def test_finalizer_defers_cleanup_for_active_operation_without_waiting(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    proof = resource._credential._proof
    lease = resource.operation_guard(session)

    writer_module._finalize_writer_session_resource(resource)
    assert resource._state == writer_module._CLOSING
    assert resource._deferred_cleanup_requested is True
    assert resource._credential is not None
    assert resource._authority_lock is not None
    assert set(proof) != {0}
    assert _run_writer_attempt(location) == "state_authority_lock_busy"

    lease._close()
    assert resource._state == writer_module._CLOSED
    assert resource._credential is None
    assert resource._authority_lock is None
    assert set(proof) == {0}
    assert _run_writer_attempt(location) == "acquired:2"


def test_close_waits_for_last_operation_owned_deferred_cleanup(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    lease = resource.operation_guard(session)
    authority_lock = resource._authority_lock
    original_close = authority_lock.close
    cleanup_started = threading.Event()
    release_cleanup = threading.Event()
    cleanup_done = threading.Event()
    close_done = threading.Event()
    lease_done = threading.Event()
    close_call_count = 0

    def slow_authority_close() -> None:
        nonlocal close_call_count
        close_call_count += 1
        cleanup_started.set()
        _wait_for_event(release_cleanup, timeout=5.0)
        original_close()
        cleanup_done.set()

    authority_lock.close = slow_authority_close

    writer_module._finalize_writer_session_resource(resource)
    assert resource._state == writer_module._CLOSING
    assert resource._deferred_cleanup_requested is True

    closer = threading.Thread(target=lambda: (session.close(), close_done.set()))
    closer.start()
    time.sleep(0.05)
    assert close_done.is_set() is False

    releaser = threading.Thread(target=lambda: (lease._close(), lease_done.set()))
    releaser.start()
    _wait_for_event(cleanup_started)
    assert resource._state == writer_module._CLEANING
    assert close_done.is_set() is False
    with pytest.raises(StateAuthorityLockError) as busy_error:
        acquire_state_authority_lock(location)
    assert busy_error.value.reason is StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_BUSY

    release_cleanup.set()
    _join_thread(releaser)
    _join_thread(closer)
    assert lease_done.is_set()
    assert close_done.is_set()
    assert cleanup_done.is_set()
    assert close_call_count == 1
    assert resource._state == writer_module._CLOSED
    assert _run_writer_attempt(location) == "acquired:2"


def test_close_waits_when_resource_finalizer_owns_cleanup(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    authority_lock = resource._authority_lock
    original_close = authority_lock.close
    cleanup_started = threading.Event()
    release_cleanup = threading.Event()
    finalizer_done = threading.Event()
    close_done = threading.Event()
    close_call_count = 0

    def slow_authority_close() -> None:
        nonlocal close_call_count
        close_call_count += 1
        cleanup_started.set()
        _wait_for_event(release_cleanup, timeout=5.0)
        original_close()

    authority_lock.close = slow_authority_close

    finalizer_thread = threading.Thread(
        target=lambda: (writer_module._finalize_writer_session_resource(resource), finalizer_done.set())
    )
    finalizer_thread.start()
    _wait_for_event(cleanup_started)
    assert resource._state == writer_module._CLEANING

    closer = threading.Thread(target=lambda: (session.close(), close_done.set()))
    closer.start()
    assert close_done.wait(0.25) is False
    with pytest.raises(StateAuthorityLockError) as busy_error:
        acquire_state_authority_lock(location)
    assert busy_error.value.reason is StateAuthorityLockErrorReason.STATE_AUTHORITY_LOCK_BUSY

    release_cleanup.set()
    _join_thread(finalizer_thread)
    _join_thread(closer)
    assert finalizer_done.is_set()
    assert close_done.is_set()
    assert close_call_count == 1
    assert resource._state == writer_module._CLOSED
    session.close()
    assert close_call_count == 1
    assert _run_writer_attempt(location) == "acquired:2"


def test_operation_lease_retains_wrapper_and_authority_until_exit(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    proof = resource._credential._proof
    lease = resource.operation_guard(session)
    session_ref = weakref.ref(session)

    session = None
    gc.collect()
    assert session_ref() is not None
    assert _operation_count(resource) == 1
    assert resource._state == writer_module._ACTIVE
    assert resource._credential is not None
    assert resource._authority_lock is not None
    assert set(proof) != {0}
    assert _run_writer_attempt(location) == "state_authority_lock_busy"

    lease._close()
    lease = None
    gc.collect()
    assert _operation_count(resource) == 0
    assert resource._state == writer_module._CLOSED
    assert resource._credential is None
    assert resource._authority_lock is None
    assert set(proof) == {0}
    assert _run_writer_attempt(location) == "acquired:2"


def test_abandoned_operation_lease_and_wrapper_cleanup_converges(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    proof = resource._credential._proof
    lease = resource.operation_guard(session)
    session_ref = weakref.ref(session)
    lease_ref = weakref.ref(lease)

    session = None
    lease = None
    gc.collect()

    assert session_ref() is None
    assert lease_ref() is None
    assert _operation_count(resource) == 0
    assert resource._state == writer_module._CLOSED
    assert resource._credential is None
    assert resource._authority_lock is None
    assert set(proof) == {0}
    assert _run_writer_attempt(location) == "acquired:2"


def test_public_mutation_methods_enter_and_exit_operation_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    entered = 0
    exited = 0
    original_guard = resource.operation_guard

    class TrackingGuard:
        def __init__(self, owner_session):
            self._lease = original_guard(owner_session)

        def __enter__(self):
            nonlocal entered
            entered += 1
            return self._lease.__enter__()

        def __exit__(self, exc_type, exc, traceback):
            nonlocal exited
            exited += 1
            return self._lease.__exit__(exc_type, exc, traceback)

    monkeypatch.setattr(resource, "operation_guard", TrackingGuard)
    with pytest.raises(TransitionApplyPreflightError) as transition_error:
        session.apply_transition(None)  # type: ignore[arg-type]
    assert transition_error.value.reason is TransitionApplyPreflightFailureReason.INVALID_COMMAND
    with pytest.raises(GlobalStopApplyPreflightError) as global_stop_error:
        session.apply_global_stop_update(None, None)  # type: ignore[arg-type]
    assert global_stop_error.value.reason is GlobalStopApplyPreflightFailureReason.INVALID_COMMAND
    assert entered == 2
    assert exited == 2
    assert _operation_count(resource) == 0
    session.close()


def test_fork_child_session_is_invalidated_and_parent_remains_active(tmp_path: Path) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    registry_key = session._resource._registry_key
    assert writer_module._ACTIVE_SESSION_RESOURCES.get(registry_key) is session._resource
    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        try:
            try:
                session.apply_transition(None)  # type: ignore[arg-type]
            except WriterSessionError as exc:
                reason = exc.reason.value
            else:
                reason = "unexpected-active"
            proof_state = "cleared" if session._resource._credential is None else "kept"
            registry_state = "registry-empty" if writer_module._ACTIVE_SESSION_RESOURCES == {} else "registry-kept"
            os.write(write_fd, f"{reason}:{proof_state}:{registry_state}".encode("ascii"))
        finally:
            os.close(write_fd)
            os._exit(0)

    os.close(write_fd)
    child_result = os.read(read_fd, 256).decode("ascii")
    os.close(read_fd)
    waited_pid, status = os.waitpid(child_pid, 0)
    assert waited_pid == child_pid
    assert status == 0
    assert child_result == "writer_session_process_mismatch:cleared:registry-empty"
    assert writer_module._ACTIVE_SESSION_RESOURCES.get(registry_key) is session._resource
    assert session.active is True
    assert _run_writer_attempt(location) == "state_authority_lock_busy"
    session.close()
    assert registry_key not in writer_module._ACTIVE_SESSION_RESOURCES
    assert _run_writer_attempt(location) == "acquired:2"


def test_fork_child_operation_with_inherited_locked_session_sync_does_not_hang(tmp_path: Path) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    lease = resource.operation_guard(session)
    old_condition = resource._condition
    copied_epoch = lease._lifecycle_epoch
    held = threading.Event()
    release = threading.Event()
    holder = threading.Thread(target=_hold_condition, args=(resource, held, release), daemon=True)
    holder.start()
    assert held.wait(2)

    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        try:
            try:
                session.apply_transition(None)  # type: ignore[arg-type]
            except WriterSessionError as exc:
                reason = exc.reason.value
            else:
                reason = "unexpected-active"
            fresh_sync = session._resource._condition is not old_condition
            active_count = _operation_count(session._resource)
            stale_lease = copied_epoch != session._resource._lifecycle_epoch
            proof_state = "cleared" if session._resource._credential is None else "kept"
            os.write(write_fd, f"{reason}:{fresh_sync}:{active_count}:{stale_lease}:{proof_state}".encode("ascii"))
        finally:
            os.close(write_fd)
            os._exit(0)

    os.close(write_fd)
    try:
        child_result = _wait_for_child_result(child_pid, read_fd)
    finally:
        os.close(read_fd)
        release.set()
        holder.join(2)
    assert child_result == "writer_session_process_mismatch:True:0:True:cleared"
    assert resource._condition is old_condition
    assert _operation_count(resource) == 1
    assert session.active is True
    lease._close()
    session.close()


def test_fork_child_copied_operation_lease_exit_and_finalizer_are_noops(tmp_path: Path) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    exit_lease = resource.operation_guard(session)
    finalizer_lease = resource.operation_guard(session)
    exit_epoch = exit_lease._lifecycle_epoch
    finalizer_epoch = finalizer_lease._lifecycle_epoch

    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        try:
            try:
                exit_lease._close()
                exit_lease._close()
                exit_result = "exit-ok"
            except BaseException as exc:  # noqa: BLE001 - raw lifecycle errors must fail the test
                exit_result = f"exit-{exc.__class__.__name__}"
            try:
                finalizer_lease = None
                gc.collect()
                finalizer_result = "finalizer-ok"
            except BaseException as exc:  # noqa: BLE001
                finalizer_result = f"finalizer-{exc.__class__.__name__}"
            try:
                session.apply_transition(None)  # type: ignore[arg-type]
            except WriterSessionError as exc:
                session_result = exc.reason.value
            else:
                session_result = "unexpected-active"
            active_count = _operation_count(session._resource)
            stale_epochs = (
                exit_epoch != session._resource._lifecycle_epoch
                and finalizer_epoch != session._resource._lifecycle_epoch
            )
            os.write(
                write_fd,
                f"{exit_result}:{finalizer_result}:{session_result}:{active_count}:{stale_epochs}".encode("ascii"),
            )
        finally:
            os.close(write_fd)
            os._exit(0)

    os.close(write_fd)
    try:
        child_result = _wait_for_child_result(child_pid, read_fd)
    finally:
        os.close(read_fd)
    assert child_result == "exit-ok:finalizer-ok:writer_session_process_mismatch:0:True"
    assert _operation_count(resource) == 2
    assert session.active is True
    exit_lease._close()
    finalizer_lease._close()
    assert _operation_count(resource) == 0
    session.close()


def test_fork_child_finalizer_with_inherited_locked_session_sync_does_not_hang_or_prolong_lock(tmp_path: Path) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    old_condition = resource._condition
    held = threading.Event()
    release_holder = threading.Event()
    holder = threading.Thread(target=_hold_condition, args=(resource, held, release_holder), daemon=True)
    holder.start()
    assert held.wait(2)

    result_read, result_write = os.pipe()
    release_child_read, release_child_write = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(result_read)
        os.close(release_child_write)
        try:
            session.close()
            fresh_sync = session._resource._condition is not old_condition
            active_count = _operation_count(session._resource)
            os.write(result_write, f"closed:{fresh_sync}:{active_count}".encode("ascii"))
            os.read(release_child_read, 1)
        finally:
            os.close(result_write)
            os.close(release_child_read)
            os._exit(0)

    os.close(result_write)
    os.close(release_child_read)
    try:
        child_result = _read_pipe_message(result_read)
    finally:
        os.close(result_read)
        release_holder.set()
        holder.join(2)
    assert child_result == "closed:True:0"
    assert session.active is True
    assert _run_writer_attempt(location) == "state_authority_lock_busy"
    session.close()
    assert _run_writer_attempt(location) == "acquired:2"
    os.write(release_child_write, b"x")
    os.close(release_child_write)
    waited_pid, status = os.waitpid(child_pid, 0)
    assert waited_pid == child_pid
    assert status == 0


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
    source_paths = tuple(
        path
        for path in (ROOT / "src").rglob("*.py")
        if path.name
        not in {
            "sqlite_transition_write_contracts.py",
            "sqlite_global_stop_write_contracts.py",
        }
    )
    _assert_no_requests_client_usage(source_paths)
    package_exports = set(ge_nwp_coordinator.__all__)
    assert "acquire_sqlite_writer_session" not in package_exports
    assert "SQLiteWriterAcquisitionError" not in package_exports
    assert "_SQLiteWriterSession" not in package_exports
    assert "_WriterSessionOperationLease" not in package_exports
    assert "_PrivateWriterCredential" not in package_exports
    assert not hasattr(ge_nwp_coordinator, "acquire_sqlite_writer_session")
    assert not hasattr(ge_nwp_coordinator, "_SQLiteWriterSession")
    assert not hasattr(ge_nwp_coordinator, "_WriterSessionOperationLease")
    assert not hasattr(ge_nwp_coordinator, "_PrivateWriterCredential")

    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in source_paths
    )
    for forbidden in (
        "def current_writer",
        "def read_latest_writer_issuance",
        "get_writer_credential",
        "get_writer_proof",
        "get_writer_digest",
        "get_operation_guard",
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
        "urllib",
    ):
        assert forbidden not in source

    migrations = sorted(path.name for path in (ROOT / "src/ge_nwp_coordinator/sqlite_migrations").glob("*.sql"))
    assert migrations == ["0001_initial.sql"]
    migration_bytes = (ROOT / "src/ge_nwp_coordinator/sqlite_migrations/0001_initial.sql").read_bytes()
    assert hashlib.sha256(migration_bytes).hexdigest() == EXPECTED_MIGRATION_0001_CHECKSUM


def test_operation_guard_credential_and_proof_are_not_public_projection_surfaces(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    lease = session._resource.operation_guard(session)
    try:
        serialized = repr((session.metadata, lease, session._resource._credential)).lower()
        assert "proof" not in repr(session.metadata).lower()
        assert "digest" not in repr(session.metadata).lower()
        assert "proof" not in serialized
        assert "digest" not in serialized
        assert not hasattr(lease, "to_dict")
        assert not hasattr(lease, "metadata")
        assert not hasattr(session._resource._credential, "to_dict")
    finally:
        lease._close()
        session.close()
