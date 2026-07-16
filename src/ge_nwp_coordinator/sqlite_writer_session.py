"""Internal SQLite writer issuance and session acquisition for B2c.

This module deliberately does not implement transition or global-stop
mutation storage. Active mutation calls fail locally until B3/B4 provide the
atomic apply boundary.
"""

from __future__ import annotations

from _thread import allocate_lock
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from types import TracebackType
from typing import Any, Self
import weakref

from ge_nwp_coordinator.global_stop import GlobalStopCommand, GlobalStopOperatorDecision
from ge_nwp_coordinator.models import require_contract_ref
from ge_nwp_coordinator.sqlite_connection import open_existing_sqlite_connection
from ge_nwp_coordinator.sqlite_errors import SQLiteStateError
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import (
    DatabaseClassification,
    inspect_database,
    _validate_current_managed_connection,
)
from ge_nwp_coordinator.state_authority_lock import StateAuthorityLock, acquire_state_authority_lock
from ge_nwp_coordinator.state_machine import TransitionCommand, TransitionContext
from ge_nwp_coordinator.state_store import (
    GlobalStopApplyOutcome,
    MAX_WRITER_GENERATION,
    SafeWriterMetadata,
    TransitionApplyOutcome,
    WRITER_ISSUANCE_PROOF_DOMAIN,
    WriterSession,
    WriterSessionError,
    WriterSessionFailureReason,
)

_ACTIVE = "active"
_CLOSING = "closing"
_CLOSED = "closed"
_PROOF_BYTES = 32
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_RFC3339_UTC_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_SESSION_GATE = allocate_lock()
_ACTIVE_SESSION_RESOURCES: dict[int, "_WriterSessionResource"] = {}
_AT_FORK_SNAPSHOT: tuple["_WriterSessionResource", ...] = ()
_AT_FORK_REGISTERED = False
_FINALIZER_FACTORY = weakref.finalize


class SQLiteWriterAcquisitionFailureReason(str, Enum):
    DATABASE_NOT_MANAGED = "database_not_managed"
    WRITER_GENERATION_EXHAUSTED = "writer_generation_exhausted"
    WRITER_STATE_MALFORMED = "writer_state_malformed"
    WRITER_ACQUISITION_FAILED = "writer_acquisition_failed"


class SQLiteWriterAcquisitionError(RuntimeError):
    """Closed writer-acquisition failure whose string form is only the reason."""

    def __init__(self, reason: SQLiteWriterAcquisitionFailureReason | str) -> None:
        normalized = SQLiteWriterAcquisitionFailureReason(reason)
        self.reason = normalized
        super().__init__(normalized.value)


@dataclass(frozen=True, repr=False)
class _DurableWriterIssuance:
    writer_ref: str
    generation: int
    issued_ref: str
    issuance_nonce_digest: str
    acquired_at: str

    def metadata(self) -> SafeWriterMetadata:
        return SafeWriterMetadata(
            writer_ref=self.writer_ref,
            generation=self.generation,
            issued_ref=self.issued_ref,
            acquired_at=self.acquired_at,
        )

    def __repr__(self) -> str:
        return "<_DurableWriterIssuance>"


class _PrivateWriterCredential:
    """Memory-only private issuance proof held by an active session resource."""

    __slots__ = ("writer_ref", "generation", "issued_ref", "_proof")
    __hash__ = object.__hash__

    def __init__(self, *, writer_ref: str, generation: int, issued_ref: str, proof: bytearray) -> None:
        self.writer_ref = _require_writer_ref(writer_ref)
        self.generation = _require_generation(generation)
        self.issued_ref = _require_issued_ref(issued_ref)
        if not isinstance(proof, bytearray) or len(proof) != _PROOF_BYTES:
            raise ValueError("invalid writer input")
        self._proof: bytearray | None = proof

    def __repr__(self) -> str:
        return "<_PrivateWriterCredential>"

    def __eq__(self, other: object) -> bool:
        return self is other

    def verify_digest(self, digest: str) -> bool:
        proof = self._proof
        if proof is None:
            return False
        return _verify_issuance_proof_digest(
            self.writer_ref,
            self.generation,
            self.issued_ref,
            proof,
            digest,
        )

    def overwrite_and_drop(self) -> None:
        proof = self._proof
        if proof is not None:
            _overwrite_proof_buffer(proof)
        self._proof = None


class _WriterSessionResource:
    """Private owner for the lock, private credential, and lifecycle state."""

    def __init__(
        self,
        *,
        location: CoordinatorStateLocation,
        authority_lock: StateAuthorityLock,
        credential: _PrivateWriterCredential,
        metadata: SafeWriterMetadata,
    ) -> None:
        self._location = location
        self._authority_lock: StateAuthorityLock | None = authority_lock
        self._credential: _PrivateWriterCredential | None = credential
        self._metadata = metadata
        self._owner_pid = os.getpid()
        self._state = _ACTIVE
        self._mutex = allocate_lock()
        self._registry_key = id(self)

    @property
    def metadata(self) -> SafeWriterMetadata:
        return self._metadata

    def active_for_owner(self) -> bool:
        if self._owner_pid != os.getpid():
            self.cleanup_from_foreign_process()
            return False
        self._mutex.acquire()
        try:
            active = self._state == _ACTIVE and self._credential is not None and self._authority_lock is not None
        finally:
            self._mutex.release()
        if not active:
            return False
        lock = self._authority_lock
        return bool(lock is not None and lock.active)

    def require_usable_for_mutation(self) -> None:
        self._require_owner_process()
        self._require_active_lifecycle()

    def require_active_for_context(self) -> None:
        self._require_owner_process()
        self._require_active_lifecycle()

    def close_from_owner(self) -> None:
        if self._owner_pid != os.getpid():
            self.cleanup_from_foreign_process()
            return
        self._cleanup_release_lock(release_lock=True)

    def cleanup_from_finalizer(self) -> None:
        if self._owner_pid != os.getpid():
            self.cleanup_from_foreign_process()
            return
        self._cleanup_release_lock(release_lock=True)

    def cleanup_from_foreign_process(self) -> None:
        self._mutex.acquire()
        try:
            self._state = _CLOSED
            self._owner_pid = -1
            credential = self._credential
            self._credential = None
            self._authority_lock = None
        finally:
            self._mutex.release()
        if credential is not None:
            credential.overwrite_and_drop()
        _remove_active_session_resource(self)

    def mark_closed_after_fork(self) -> None:
        self._state = _CLOSED
        self._owner_pid = -1
        credential = self._credential
        self._credential = None
        self._authority_lock = None
        if credential is not None:
            credential.overwrite_and_drop()

    def _require_owner_process(self) -> None:
        if self._owner_pid != os.getpid():
            self.cleanup_from_foreign_process()
            raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH)

    def _require_active_lifecycle(self) -> None:
        self._mutex.acquire()
        try:
            active = self._state == _ACTIVE and self._credential is not None and self._authority_lock is not None
        finally:
            self._mutex.release()
        if not active:
            raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_CLOSED)
        lock = self._authority_lock
        if lock is None or not lock.active:
            self.close_from_owner()
            raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_CLOSED)

    def _cleanup_release_lock(self, *, release_lock: bool) -> None:
        self._mutex.acquire()
        try:
            if self._state == _CLOSED and self._credential is None and self._authority_lock is None:
                return
            self._state = _CLOSING
            credential = self._credential
            authority_lock = self._authority_lock
            self._credential = None
            self._authority_lock = None
            self._state = _CLOSED
        finally:
            self._mutex.release()
        if credential is not None:
            credential.overwrite_and_drop()
        if release_lock and authority_lock is not None:
            authority_lock.close()
        _remove_active_session_resource(self)


class _SQLiteWriterSession(WriterSession):
    """Internal concrete writer session for B2c acquisition only."""

    def __init__(self, resource: _WriterSessionResource) -> None:
        self._resource = resource
        _register_active_session_resource(resource)
        try:
            self._finalizer = _FINALIZER_FACTORY(self, _finalize_writer_session_resource, resource)
            self._finalizer.atexit = False
        except Exception:
            resource.close_from_owner()
            raise

    @property
    def metadata(self) -> SafeWriterMetadata:
        return self._resource.metadata

    @property
    def active(self) -> bool:
        return self._resource.active_for_owner()

    def apply_transition(
        self,
        transition_command: TransitionCommand,
        typed_context: TransitionContext,
    ) -> TransitionApplyOutcome:
        self._resource.require_usable_for_mutation()
        raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_MUTATION_UNAVAILABLE)

    def apply_global_stop_update(
        self,
        global_stop_command: GlobalStopCommand,
        typed_operator_decision: GlobalStopOperatorDecision,
    ) -> GlobalStopApplyOutcome:
        self._resource.require_usable_for_mutation()
        raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_MUTATION_UNAVAILABLE)

    def close(self) -> None:
        if self._finalizer.alive:
            self._finalizer()

    def __enter__(self) -> Self:
        self._resource.require_active_for_context()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def acquire_sqlite_writer_session(location: CoordinatorStateLocation) -> WriterSession:
    """Acquire an internal SQLite-backed writer session for a managed database."""

    _require_managed_preflight(location)
    authority_lock = acquire_state_authority_lock(location)
    connection: sqlite3.Connection | None = None
    credential: _PrivateWriterCredential | None = None
    committed = False
    try:
        _require_managed_preflight(location)
        connection = open_existing_sqlite_connection(location, read_only=False)
        connection.execute("BEGIN IMMEDIATE")
        try:
            _validate_current_managed_connection(connection)
            current = _read_durable_writer_issuance(connection)
            generation = _next_writer_generation(current)
            writer_ref = _generate_writer_ref()
            issued_ref = _generate_issued_ref()
            proof = _generate_private_proof()
            credential = _PrivateWriterCredential(
                writer_ref=writer_ref,
                generation=generation,
                issued_ref=issued_ref,
                proof=proof,
            )
            digest = _compute_issuance_proof_digest(writer_ref, generation, issued_ref, proof)
            acquired_at = _utc_now()
            _write_durable_writer_issuance(
                connection,
                current=current,
                writer_ref=writer_ref,
                generation=generation,
                issued_ref=issued_ref,
                issuance_nonce_digest=digest,
                acquired_at=acquired_at,
            )
            persisted = _read_durable_writer_issuance(connection)
            if persisted is None:
                raise SQLiteWriterAcquisitionError(
                    SQLiteWriterAcquisitionFailureReason.WRITER_ACQUISITION_FAILED
                )
            _require_persisted_matches(
                persisted,
                writer_ref=writer_ref,
                generation=generation,
                issued_ref=issued_ref,
                acquired_at=acquired_at,
            )
            if not credential.verify_digest(persisted.issuance_nonce_digest):
                raise SQLiteWriterAcquisitionError(
                    SQLiteWriterAcquisitionFailureReason.WRITER_ACQUISITION_FAILED
                )
            connection.execute("COMMIT")
            committed = True
        except Exception:
            if not committed:
                _rollback(connection)
            raise
        finally:
            connection.close()
            connection = None
        resource = _WriterSessionResource(
            location=location,
            authority_lock=authority_lock,
            credential=credential,
            metadata=SafeWriterMetadata(
                writer_ref=writer_ref,
                generation=generation,
                issued_ref=issued_ref,
                acquired_at=acquired_at,
            ),
        )
        credential = None
        try:
            return _SESSION_FACTORY(resource)
        except Exception:
            resource.close_from_owner()
            raise SQLiteWriterAcquisitionError(
                SQLiteWriterAcquisitionFailureReason.WRITER_ACQUISITION_FAILED
            ) from None
    except SQLiteWriterAcquisitionError:
        if credential is not None:
            credential.overwrite_and_drop()
        if connection is not None:
            connection.close()
        authority_lock.close()
        raise
    except SQLiteStateError:
        if credential is not None:
            credential.overwrite_and_drop()
        if connection is not None:
            _rollback(connection)
            connection.close()
        authority_lock.close()
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.DATABASE_NOT_MANAGED) from None
    except sqlite3.Error:
        if credential is not None:
            credential.overwrite_and_drop()
        if connection is not None:
            _rollback(connection)
            connection.close()
        authority_lock.close()
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_ACQUISITION_FAILED) from None
    except Exception:
        if credential is not None:
            credential.overwrite_and_drop()
        if connection is not None:
            _rollback(connection)
            connection.close()
        authority_lock.close()
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_ACQUISITION_FAILED) from None


def _require_managed_preflight(location: CoordinatorStateLocation) -> None:
    inspection = inspect_database(location)
    if (
        inspection.classification is not DatabaseClassification.MANAGED
        or inspection.current_sequence != inspection.latest_sequence
    ):
        if inspection.classification is DatabaseClassification.UNKNOWN:
            _raise_writer_state_malformed_if_present(location)
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.DATABASE_NOT_MANAGED)


def _raise_writer_state_malformed_if_present(location: CoordinatorStateLocation) -> None:
    connection: sqlite3.Connection | None = None
    try:
        connection = open_existing_sqlite_connection(location, read_only=True)
        _read_durable_writer_issuance(connection)
    except SQLiteWriterAcquisitionError as exc:
        if exc.reason is SQLiteWriterAcquisitionFailureReason.WRITER_STATE_MALFORMED:
            raise
    except SQLiteStateError:
        return
    except sqlite3.Error:
        return
    finally:
        if connection is not None:
            connection.close()


def _read_durable_writer_issuance(connection: sqlite3.Connection) -> _DurableWriterIssuance | None:
    try:
        rows = connection.execute(
            """
            SELECT singleton_id, writer_ref, generation, issued_ref, issuance_nonce_digest, acquired_at
            FROM writer_ownership
            ORDER BY singleton_id
            """
        ).fetchall()
    except sqlite3.Error:
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_STATE_MALFORMED) from None
    return _parse_writer_ownership_rows(rows)


def _parse_writer_ownership_rows(rows: Any) -> _DurableWriterIssuance | None:
    if not isinstance(rows, list | tuple):
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_STATE_MALFORMED)
    if len(rows) > 1:
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_STATE_MALFORMED)
    if not rows:
        return None
    try:
        row = tuple(rows[0])
    except TypeError:
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_STATE_MALFORMED) from None
    if len(row) != 6:
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_STATE_MALFORMED)
    singleton_id, writer_ref, generation, issued_ref, issuance_nonce_digest, acquired_at = row
    try:
        if singleton_id != 1 or isinstance(singleton_id, bool):
            raise ValueError("malformed singleton")
        return _DurableWriterIssuance(
            writer_ref=_require_writer_ref(writer_ref),
            generation=_require_generation(generation),
            issued_ref=_require_issued_ref(issued_ref),
            issuance_nonce_digest=_require_sha256_digest(issuance_nonce_digest),
            acquired_at=_require_utc_timestamp(acquired_at),
        )
    except ValueError:
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_STATE_MALFORMED) from None


def _next_writer_generation(current: _DurableWriterIssuance | None) -> int:
    if current is None:
        return 1
    if current.generation >= MAX_WRITER_GENERATION:
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_GENERATION_EXHAUSTED)
    return current.generation + 1


def _write_durable_writer_issuance(
    connection: sqlite3.Connection,
    *,
    current: _DurableWriterIssuance | None,
    writer_ref: str,
    generation: int,
    issued_ref: str,
    issuance_nonce_digest: str,
    acquired_at: str,
) -> None:
    try:
        if current is None:
            cursor = connection.execute(
                """
                INSERT INTO writer_ownership
                    (singleton_id, writer_ref, generation, issued_ref, issuance_nonce_digest, acquired_at)
                VALUES (1, ?, ?, ?, ?, ?)
                """,
                (writer_ref, generation, issued_ref, issuance_nonce_digest, acquired_at),
            )
        else:
            cursor = connection.execute(
                """
                UPDATE writer_ownership
                SET writer_ref = ?, generation = ?, issued_ref = ?,
                    issuance_nonce_digest = ?, acquired_at = ?
                WHERE singleton_id = 1 AND generation = ?
                """,
                (
                    writer_ref,
                    generation,
                    issued_ref,
                    issuance_nonce_digest,
                    acquired_at,
                    current.generation,
                ),
            )
    except sqlite3.Error:
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_ACQUISITION_FAILED) from None
    if cursor.rowcount != 1:
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_ACQUISITION_FAILED)


def _require_persisted_matches(
    persisted: _DurableWriterIssuance,
    *,
    writer_ref: str,
    generation: int,
    issued_ref: str,
    acquired_at: str,
) -> None:
    if (
        persisted.writer_ref != writer_ref
        or persisted.generation != generation
        or persisted.issued_ref != issued_ref
        or persisted.acquired_at != acquired_at
    ):
        raise SQLiteWriterAcquisitionError(SQLiteWriterAcquisitionFailureReason.WRITER_ACQUISITION_FAILED)


def _generate_writer_ref() -> str:
    return "writer-" + secrets.token_hex(16)


def _generate_issued_ref() -> str:
    return "issuance-" + secrets.token_hex(16)


def _generate_private_proof() -> bytearray:
    return bytearray(secrets.token_bytes(_PROOF_BYTES))


def _compute_issuance_proof_digest(
    writer_ref: str,
    generation: int,
    issued_ref: str,
    proof: bytes | bytearray,
) -> str:
    writer_ref = _require_writer_ref(writer_ref)
    generation = _require_generation(generation)
    issued_ref = _require_issued_ref(issued_ref)
    _require_proof(proof)
    digest = hashlib.sha256()
    digest.update(WRITER_ISSUANCE_PROOF_DOMAIN.encode("utf-8"))
    digest.update(b"\x00")
    digest.update(writer_ref.encode("utf-8"))
    digest.update(b"\x00")
    digest.update(str(generation).encode("ascii"))
    digest.update(b"\x00")
    digest.update(issued_ref.encode("utf-8"))
    digest.update(b"\x00")
    digest.update(proof)
    return digest.hexdigest()


def _verify_issuance_proof_digest(
    writer_ref: str,
    generation: int,
    issued_ref: str,
    proof: bytes | bytearray,
    expected_digest: str,
) -> bool:
    expected = _require_sha256_digest(expected_digest)
    actual = _compute_issuance_proof_digest(writer_ref, generation, issued_ref, proof)
    return hmac.compare_digest(actual, expected)


def _require_writer_ref(value: Any) -> str:
    return require_contract_ref(value, "writer_ref")


def _require_issued_ref(value: Any) -> str:
    return require_contract_ref(value, "issued_ref")


def _require_generation(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1 or value > MAX_WRITER_GENERATION:
        raise ValueError("invalid writer generation")
    return value


def _require_sha256_digest(value: Any) -> str:
    if not isinstance(value, str) or _SHA256_HEX_RE.fullmatch(value) is None:
        raise ValueError("invalid writer input")
    return value


def _require_utc_timestamp(value: Any) -> str:
    if not isinstance(value, str) or _RFC3339_UTC_Z_RE.fullmatch(value) is None:
        raise ValueError("invalid writer timestamp")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ValueError("invalid writer timestamp") from None
    return value


def _require_proof(proof: Any) -> None:
    if not isinstance(proof, bytes | bytearray) or len(proof) != _PROOF_BYTES:
        raise ValueError("invalid writer input")


def _overwrite_proof_buffer(proof: bytearray) -> None:
    for index in range(len(proof)):
        proof[index] = 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rollback(connection: sqlite3.Connection) -> None:
    try:
        connection.execute("ROLLBACK")
    except sqlite3.Error:
        pass


def _make_sqlite_writer_session(resource: _WriterSessionResource) -> WriterSession:
    return _SQLiteWriterSession(resource)


_SESSION_FACTORY = _make_sqlite_writer_session


def _register_active_session_resource(resource: _WriterSessionResource) -> None:
    _SESSION_GATE.acquire()
    try:
        _register_at_fork_once_locked()
        _ACTIVE_SESSION_RESOURCES[resource._registry_key] = resource
    finally:
        _SESSION_GATE.release()


def _remove_active_session_resource(resource: _WriterSessionResource) -> None:
    _SESSION_GATE.acquire()
    try:
        if _ACTIVE_SESSION_RESOURCES.get(resource._registry_key) is resource:
            _ACTIVE_SESSION_RESOURCES.pop(resource._registry_key, None)
    finally:
        _SESSION_GATE.release()


def _register_at_fork_once_locked() -> None:
    global _AT_FORK_REGISTERED
    if _AT_FORK_REGISTERED:
        return
    os.register_at_fork(
        before=_at_fork_before,
        after_in_parent=_at_fork_parent,
        after_in_child=_at_fork_child,
    )
    _AT_FORK_REGISTERED = True


def _at_fork_before() -> None:
    global _AT_FORK_SNAPSHOT
    _SESSION_GATE.acquire()
    _AT_FORK_SNAPSHOT = tuple(_ACTIVE_SESSION_RESOURCES.values())


def _at_fork_parent() -> None:
    global _AT_FORK_SNAPSHOT
    _AT_FORK_SNAPSHOT = ()
    _SESSION_GATE.release()


def _at_fork_child() -> None:
    global _ACTIVE_SESSION_RESOURCES, _AT_FORK_SNAPSHOT, _SESSION_GATE
    snapshot = _AT_FORK_SNAPSHOT
    _ACTIVE_SESSION_RESOURCES = {}
    _AT_FORK_SNAPSHOT = ()
    for resource in snapshot:
        resource.mark_closed_after_fork()
    _SESSION_GATE = allocate_lock()


def _finalize_writer_session_resource(resource: _WriterSessionResource) -> None:
    try:
        resource.cleanup_from_finalizer()
    except Exception:
        pass


__all__ = [
    "SQLiteWriterAcquisitionError",
    "SQLiteWriterAcquisitionFailureReason",
    "acquire_sqlite_writer_session",
]
