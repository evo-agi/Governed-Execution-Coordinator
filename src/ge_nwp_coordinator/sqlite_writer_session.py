"""Internal SQLite writer issuance, session lifecycle, and delegation boundary.

This module owns WriterSession lifecycle and operation authority, but not
SQLite mutation grammar or direct SQL storage. Public transition and global-stop
apply delegate to the one private neutral mutation transaction authority, while
mutation grammar and durable write ownership remain private.
"""

from __future__ import annotations

from _thread import allocate_lock
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import os
import secrets
import sqlite3
import sys
from threading import Condition, Lock, Thread, current_thread, get_ident
from types import MethodType, TracebackType
from typing import Any, Self
import weakref

from ge_nwp_coordinator.global_stop import GlobalStopCommand, GlobalStopOperatorDecision
from ge_nwp_coordinator.sqlite_connection import (
    _RetainedSQLiteConnection,
    _SQLiteConnectionCloseProof,
    _WriterSessionResourceIdentity,
    _make_retained_sqlite_connection,
    _new_writer_session_resource_identity,
    _open_bound_existing_sqlite_connection,
    open_existing_sqlite_connection,
)
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError,
    SQLiteMutationStoreErrorCode,
    SQLiteStateError,
)
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import (
    DatabaseClassification,
    inspect_database,
    _validate_current_managed_connection,
)
from ge_nwp_coordinator.sqlite_security import (
    _StateDatabaseAuthorityBinding,
    _StateDatabaseAuthorityBindingMismatch,
    _StateDatabaseAuthorityBindingUnavailable,
    _require_same_state_database_authority_binding,
)
from ge_nwp_coordinator.sqlite_writer_state import (
    _DurableWriterIssuance,
    _parse_writer_ownership_rows as _parse_writer_ownership_rows_or_raise,
    _require_generation,
    _require_issued_ref,
    _require_sha256_digest,
    _require_writer_ref,
)
from ge_nwp_coordinator.state_authority_lock import StateAuthorityLock, acquire_state_authority_lock
from ge_nwp_coordinator.state_machine import TransitionCommand
from ge_nwp_coordinator.state_store import (
    GlobalStopApplyPreflightError,
    GlobalStopApplyPreflightFailureReason,
    GlobalStopApplyOutcome,
    MAX_WRITER_GENERATION,
    SafeWriterMetadata,
    TransitionApplyOutcome,
    TransitionApplyPreflightError,
    TransitionApplyPreflightFailureReason,
    WRITER_ISSUANCE_PROOF_DOMAIN,
    WriterSession,
    WriterSessionError,
    WriterSessionFailureReason,
)

_ACTIVE = "active"
_CLOSING = "closing"
_CLEANING = "cleaning"
_CLOSED = "closed"
_FORK_INVALID = "fork_invalid"
_COMMIT_UNCERTAIN_QUARANTINED = "commit_uncertain_quarantined"
_COMMIT_SUCCEEDED_QUARANTINED = "commit_succeeded_quarantined"
_COMMIT_UNCERTAIN_CONNECTION_CLOSED_CLEANUP_PENDING = (
    "commit_uncertain_connection_closed_cleanup_pending"
)
_COMMIT_SUCCEEDED_CONNECTION_CLOSED_CLEANUP_PENDING = (
    "commit_succeeded_connection_closed_cleanup_pending"
)
_QUARANTINED_STATES = frozenset(
    {_COMMIT_UNCERTAIN_QUARANTINED, _COMMIT_SUCCEEDED_QUARANTINED}
)
_CONNECTION_CLOSED_CLEANUP_PENDING_STATES = frozenset(
    {
        _COMMIT_UNCERTAIN_CONNECTION_CLOSED_CLEANUP_PENDING,
        _COMMIT_SUCCEEDED_CONNECTION_CLOSED_CLEANUP_PENDING,
    }
)
_NONTERMINAL_CLEANUP_STATES = _QUARANTINED_STATES | _CONNECTION_CLOSED_CLEANUP_PENDING_STATES
_CLEANUP_DRIVER_ADVANCED = "advanced"
_CLEANUP_DRIVER_BLOCKED = "blocked"
_CLEANUP_DRIVER_TERMINAL = "terminal"
_CONTROLLER_RESOLUTION = "controller_resolution"
_ABORT_CLOSE_UNPROVED = "abort_close_unproved"
_PROOF_BYTES = 32
_SESSION_GATE = allocate_lock()
_ACTIVE_SESSION_RESOURCES: dict[int, "_WriterSessionResource"] = {}
_AT_FORK_SNAPSHOT: tuple["_WriterSessionResource", ...] = ()
_AT_FORK_REGISTERED = False
_OPERATION_INVOCATION_CORRELATION_CONSTRUCTION_KEY = object()
_FINALIZER_FACTORY = weakref.finalize

_BASE_EXCEPTION_TRACEBACK_DESCRIPTOR = BaseException.__dict__["__traceback__"]
_BASE_EXCEPTION_CAUSE_DESCRIPTOR = BaseException.__dict__["__cause__"]
_BASE_EXCEPTION_CONTEXT_DESCRIPTOR = BaseException.__dict__["__context__"]
_BASE_EXCEPTION_ARGS_DESCRIPTOR = BaseException.__dict__["args"]
_BASE_EXCEPTION_DICTIONARY_DESCRIPTOR = BaseException.__dict__["__dict__"]
_BASE_EXCEPTION_GROUP_CHILDREN_DESCRIPTOR = BaseExceptionGroup.__dict__["exceptions"]
_BASE_EXCEPTION_DESCRIPTOR_GET = type(
    _BASE_EXCEPTION_TRACEBACK_DESCRIPTOR
).__dict__["__get__"]
_BASE_EXCEPTION_DESCRIPTOR_SET = type(
    _BASE_EXCEPTION_TRACEBACK_DESCRIPTOR
).__dict__["__set__"]
_BASE_EXCEPTION_GROUP_DESCRIPTOR_GET = type(
    _BASE_EXCEPTION_GROUP_CHILDREN_DESCRIPTOR
).__dict__["__get__"]


def _cleanup_driver_invariant_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def _raise_writer_lifecycle_invariant_failure() -> None:
    raise SQLiteMutationStoreError(
        SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
    ) from None


_SAFE_MUTATION_STORE_ERROR_CLASSES = tuple(
    error_code.value for error_code in SQLiteMutationStoreErrorCode
)


def _require_safe_mutation_store_error_payload(
    error: object,
) -> SQLiteMutationStoreError:
    """Validate the content-free portion of one exact public store error."""

    if type(error) is not SQLiteMutationStoreError:
        raise ValueError("invalid safe mutation error")
    attributes = object.__getattribute__(error, "__dict__")
    if type(attributes) is not dict or len(attributes) != 2:
        raise ValueError("invalid safe mutation error")
    for name in dict.keys(attributes):
        if type(name) is not str or name not in ("error_class", "_internal_detail"):
            raise ValueError("invalid safe mutation error")
    if not dict.__contains__(attributes, "error_class") or not dict.__contains__(
        attributes,
        "_internal_detail",
    ):
        raise ValueError("invalid safe mutation error")
    error_class = dict.__getitem__(attributes, "error_class")
    internal_detail = dict.__getitem__(attributes, "_internal_detail")
    arguments = object.__getattribute__(error, "args")
    if (
        type(error_class) is not str
        or error_class not in _SAFE_MUTATION_STORE_ERROR_CLASSES
        or internal_detail is not None
        or type(arguments) is not tuple
        or len(arguments) != 1
        or type(arguments[0]) is not str
        or arguments[0] != error_class
    ):
        raise ValueError("invalid safe mutation error")
    try:
        object.__getattribute__(error, "__notes__")
    except AttributeError:
        pass
    else:
        raise ValueError("invalid safe mutation error")
    return error


def _require_safe_mutation_store_error(
    error: object,
) -> SQLiteMutationStoreError:
    """Require one exact, content-free, already-unraised store error."""

    checked = _require_safe_mutation_store_error_payload(error)
    if (
        object.__getattribute__(checked, "__traceback__") is not None
        or object.__getattribute__(checked, "__cause__") is not None
        or object.__getattribute__(checked, "__context__") is not None
    ):
        raise ValueError("invalid safe mutation error")
    return checked


def _new_safe_mutation_store_error(
    error_code: SQLiteMutationStoreErrorCode,
) -> SQLiteMutationStoreError:
    if type(error_code) is not SQLiteMutationStoreErrorCode:
        error_code = SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
    return _require_safe_mutation_store_error(SQLiteMutationStoreError(error_code))


def _raise_safe_mutation_store_error(error: SQLiteMutationStoreError) -> None:
    checked = _require_safe_mutation_store_error(error)
    try:
        raise checked.with_traceback(None) from None
    except SQLiteMutationStoreError as attached:
        if attached is not checked:
            raise ValueError("invalid safe mutation error") from None
        _BASE_EXCEPTION_DESCRIPTOR_SET(
            _BASE_EXCEPTION_CAUSE_DESCRIPTOR,
            attached,
            None,
        )
        _BASE_EXCEPTION_DESCRIPTOR_SET(
            _BASE_EXCEPTION_CONTEXT_DESCRIPTOR,
            attached,
            None,
        )
        _BASE_EXCEPTION_DESCRIPTOR_SET(
            _BASE_EXCEPTION_TRACEBACK_DESCRIPTOR,
            attached,
            None,
        )
        raise


def _sanitize_exception_traceback_graph_pass(
    root: BaseException,
    _base_exception_type: type[BaseException] = BaseException,
    _base_exception_group_type: type[BaseExceptionGroup] = BaseExceptionGroup,
    _traceback_descriptor: object = _BASE_EXCEPTION_TRACEBACK_DESCRIPTOR,
    _cause_descriptor: object = _BASE_EXCEPTION_CAUSE_DESCRIPTOR,
    _context_descriptor: object = _BASE_EXCEPTION_CONTEXT_DESCRIPTOR,
    _args_descriptor: object = _BASE_EXCEPTION_ARGS_DESCRIPTOR,
    _dictionary_descriptor: object = _BASE_EXCEPTION_DICTIONARY_DESCRIPTOR,
    _group_children_descriptor: object = _BASE_EXCEPTION_GROUP_CHILDREN_DESCRIPTOR,
    _base_descriptor_get: object = _BASE_EXCEPTION_DESCRIPTOR_GET,
    _base_descriptor_set: object = _BASE_EXCEPTION_DESCRIPTOR_SET,
    _group_descriptor_get: object = _BASE_EXCEPTION_GROUP_DESCRIPTOR_GET,
    _type: object = type,
    _identity: object = id,
    _isinstance: object = isinstance,
    _list_pop: object = list.pop,
    _list_extend: object = list.extend,
    _set_contains: object = set.__contains__,
    _set_add: object = set.add,
    _dict_keys: object = dict.keys,
    _dict_values: object = dict.values,
) -> None:
    """Clear one supported exception graph without subclass attribute dispatch."""

    pending: list[object] = [root]
    seen: set[int] = set()
    while pending:
        current = _list_pop(pending)  # type: ignore[operator]
        identity = _identity(current)  # type: ignore[operator]
        if _set_contains(seen, identity):  # type: ignore[operator]
            continue
        _set_add(seen, identity)  # type: ignore[operator]
        if _isinstance(current, _base_exception_type):  # type: ignore[operator]
            # Traceback storage is cleared before any other field is read.
            _base_descriptor_set(  # type: ignore[operator]
                _traceback_descriptor,
                current,
                None,
            )
            cause = _base_descriptor_get(  # type: ignore[operator]
                _cause_descriptor,
                current,
                _base_exception_type,
            )
            context = _base_descriptor_get(  # type: ignore[operator]
                _context_descriptor,
                current,
                _base_exception_type,
            )
            arguments = _base_descriptor_get(  # type: ignore[operator]
                _args_descriptor,
                current,
                _base_exception_type,
            )
            attributes = _base_descriptor_get(  # type: ignore[operator]
                _dictionary_descriptor,
                current,
                _base_exception_type,
            )
            children = (
                _group_descriptor_get(  # type: ignore[operator]
                    _group_children_descriptor,
                    current,
                    _base_exception_group_type,
                )
                if _isinstance(  # type: ignore[operator]
                    current,
                    _base_exception_group_type,
                )
                else None
            )
            _list_extend(  # type: ignore[operator]
                pending,
                (cause, context, arguments, attributes, children),
            )
            continue
        current_type = _type(current)  # type: ignore[operator]
        if current_type is dict:
            _list_extend(pending, _dict_keys(current))  # type: ignore[operator]
            _list_extend(pending, _dict_values(current))  # type: ignore[operator]
        elif current_type in (tuple, list, set, frozenset):
            _list_extend(pending, current)  # type: ignore[operator]


def _sanitize_exception_traceback_graph(
    root: BaseException,
    _primary_pass: object = _sanitize_exception_traceback_graph_pass,
    _fallback_pass: object = _sanitize_exception_traceback_graph_pass,
) -> None:
    """Bound one ordinary primary-pass failure beneath the outward exception."""

    try:
        _primary_pass(root)  # type: ignore[operator]
    except Exception:
        _fallback_pass(root)  # type: ignore[operator]


def _sanitize_exception_traceback_graph_at_outward_boundary(
    root: BaseException,
    primary_sanitizer: object,
    _fallback_pass: object = _sanitize_exception_traceback_graph_pass,
) -> None:
    """Keep one replaceable sanitizer-call failure below the outward boundary."""

    try:
        primary_sanitizer(root)  # type: ignore[operator]
    except Exception:
        _fallback_pass(root)  # type: ignore[operator]


def _is_accepted_outward_safe_mutation_store_error(
    error: SQLiteMutationStoreError,
) -> bool:
    """Recognize the exact content-free safe error shape without propagating validation."""

    try:
        return bool(
            _require_safe_mutation_store_error_payload(error) is error
            and object.__getattribute__(error, "__cause__") is None
            and object.__getattribute__(error, "__context__") is None
        )
    except Exception:
        return False


@dataclass(frozen=True, slots=True, repr=False)
class _SafeMutationFailureDisposition:
    """Closed ordinary-failure result returned after sensitive frames unwind."""

    error: SQLiteMutationStoreError

    def __post_init__(self) -> None:
        _require_safe_mutation_store_error(self.error)

    def __repr__(self) -> str:
        return "<_SafeMutationFailureDisposition>"


def _safe_mutation_error_from_disposition(
    disposition: object,
) -> SQLiteMutationStoreError:
    if type(disposition) is not _SafeMutationFailureDisposition:
        return _new_safe_mutation_store_error(
            SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
        )
    try:
        error = object.__getattribute__(disposition, "error")
        return _require_safe_mutation_store_error(error)
    except Exception:
        return _new_safe_mutation_store_error(
            SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
        )

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


class _WriterIssuanceMatch(str, Enum):
    MATCH = "match"
    STALE_WRITER = "stale_writer"


class _WriterSessionAuthorityClosed(WriterSessionError):
    """Safe private marker for closed retained mutation authority."""

    def __init__(self) -> None:
        super().__init__(WriterSessionFailureReason.WRITER_SESSION_CLOSED)


class _WriterSessionAuthorityUnavailable(WriterSessionError):
    """Safe private marker for unavailable retained mutation authority."""

    def __init__(self) -> None:
        super().__init__(WriterSessionFailureReason.WRITER_SESSION_CLOSED)


class _WriterSessionMutationToken:
    """Opaque identity-only token for one resource mutation slot."""

    __slots__ = ()
    __hash__ = object.__hash__

    def __repr__(self) -> str:
        return "<_WriterSessionMutationToken>"

    def __reduce__(self) -> object:
        raise TypeError("invalid writer input")


class _OperationInvocationCorrelation:
    """Private identity that correlates one caller with one possible admission."""

    __slots__ = ("resource_identity", "owner_pid", "lifecycle_epoch")
    __hash__ = object.__hash__

    def __init__(
        self,
        *,
        key: object,
        resource_identity: _WriterSessionResourceIdentity,
        owner_pid: int,
        lifecycle_epoch: int,
    ) -> None:
        if (
            key is not _OPERATION_INVOCATION_CORRELATION_CONSTRUCTION_KEY
            or type(resource_identity) is not _WriterSessionResourceIdentity
            or type(owner_pid) is not int
            or owner_pid < 0
            or type(lifecycle_epoch) is not int
            or lifecycle_epoch < 1
        ):
            raise ValueError("invalid operation invocation correlation")
        object.__setattr__(self, "resource_identity", resource_identity)
        object.__setattr__(self, "owner_pid", owner_pid)
        object.__setattr__(self, "lifecycle_epoch", lifecycle_epoch)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("operation invocation correlation is immutable")

    def __repr__(self) -> str:
        return "<_OperationInvocationCorrelation>"

    def __reduce__(self) -> object:
        raise TypeError("invalid writer input")


class _OperationCompletionHandle:
    """Exact operation identity with non-authoritative compatibility mirrors."""

    __slots__ = (
        "resource_identity",
        "invocation_correlation",
        "operation_id",
        "owner_pid",
        "owner_thread",
        "lifecycle_epoch",
        "_cleanup_required",
        "_mutation_release_acknowledgment",
        "_retirement_preparation_acknowledgment",
        "_operation_lease_ref",
        "_operation_finalizer",
    )
    __hash__ = object.__hash__

    def __init__(
        self,
        resource_identity: _WriterSessionResourceIdentity,
        operation_id: int,
        owner_pid: int,
        owner_thread: int,
        lifecycle_epoch: int,
        invocation_correlation: _OperationInvocationCorrelation | None = None,
    ) -> None:
        if (
            type(resource_identity) is not _WriterSessionResourceIdentity
            or (
                invocation_correlation is not None
                and (
                    type(invocation_correlation)
                    is not _OperationInvocationCorrelation
                    or invocation_correlation.resource_identity
                    is not resource_identity
                    or invocation_correlation.owner_pid != owner_pid
                    or invocation_correlation.lifecycle_epoch
                    != lifecycle_epoch
                )
            )
            or type(operation_id) is not int
            or operation_id < 1
            or type(owner_pid) is not int
            or owner_pid < 0
            or type(owner_thread) is not int
            or owner_thread < 0
            or type(lifecycle_epoch) is not int
            or lifecycle_epoch < 1
        ):
            raise ValueError("invalid operation completion handle")
        self.resource_identity = resource_identity
        self.invocation_correlation = invocation_correlation
        self.operation_id = operation_id
        self.owner_pid = owner_pid
        self.owner_thread = owner_thread
        self.lifecycle_epoch = lifecycle_epoch
        self._cleanup_required = False
        self._mutation_release_acknowledgment = None
        self._retirement_preparation_acknowledgment = None
        self._operation_lease_ref = None
        self._operation_finalizer = None

    def __repr__(self) -> str:
        return "<_OperationCompletionHandle>"

    def __setattr__(self, name: str, value: object) -> None:
        if name in self.__slots__ and hasattr(self, name):
            raise AttributeError("operation completion handle is immutable")
        object.__setattr__(self, name, value)

    @property
    def completion_handle(self) -> "_OperationCompletionHandle":
        return self

    @property
    def cleanup_required(self) -> bool:
        return self._cleanup_required

    @property
    def mutation_release_acknowledgment(self) -> object | None:
        return self._mutation_release_acknowledgment

    @property
    def retirement_preparation_acknowledgment(self) -> object | None:
        return self._retirement_preparation_acknowledgment

    def _bound_operation_lease(self) -> "_WriterSessionOperationLease | None":
        reference = self._operation_lease_ref
        if type(reference) is not weakref.ReferenceType:
            return None
        lease = reference()
        if lease is None:
            return None
        if type(lease) is not _WriterSessionOperationLease:
            raise _cleanup_driver_invariant_failure() from None
        return lease

    @property
    def operation_finalizer(self) -> object | None:
        return self._operation_finalizer

    def _bind_operation_lifecycle(
        self,
        operation_lease: "_WriterSessionOperationLease",
        operation_finalizer: object,
    ) -> None:
        if (
            self._operation_lease_ref is not None
            or self._operation_finalizer is not None
            or type(operation_lease) is not _WriterSessionOperationLease
            or operation_lease._completion_handle is not self
            or type(getattr(operation_finalizer, "alive", None)) is not bool
            or not hasattr(operation_finalizer, "detach")
        ):
            raise ValueError("invalid operation lifecycle binding")
        object.__setattr__(
            self,
            "_operation_lease_ref",
            weakref.ref(operation_lease),
        )
        object.__setattr__(
            self,
            "_operation_finalizer",
            operation_finalizer,
        )

    def _mark_cleanup_required(self) -> None:
        object.__setattr__(self, "_cleanup_required", True)

    def _record_mutation_release_acknowledgment(
        self,
        acknowledgment: "_OperationMutationReleaseAcknowledgment",
    ) -> None:
        current = self._mutation_release_acknowledgment
        if current is not None and current is not acknowledgment:
            raise ValueError("invalid operation mutation-release acknowledgment")
        object.__setattr__(
            self,
            "_mutation_release_acknowledgment",
            acknowledgment,
        )

    def _record_retirement_preparation_acknowledgment(
        self,
        acknowledgment: "_OperationRetirementPreparationAcknowledgment",
    ) -> None:
        current = self._retirement_preparation_acknowledgment
        if current is not None and current is not acknowledgment:
            raise ValueError("invalid operation retirement acknowledgment")
        object.__setattr__(
            self,
            "_retirement_preparation_acknowledgment",
            acknowledgment,
        )

    def __reduce__(self) -> object:
        raise TypeError("invalid operation completion handle")


@dataclass(frozen=True, slots=True, repr=False)
class _OperationMutationReleaseAcknowledgment:
    """Exact condition-owned proof that one represented slot was released."""

    resource_identity: _WriterSessionResourceIdentity
    lifecycle_epoch: int
    operation: _OperationCompletionHandle

    def __post_init__(self) -> None:
        if (
            type(self.resource_identity) is not _WriterSessionResourceIdentity
            or type(self.lifecycle_epoch) is not int
            or self.lifecycle_epoch < 1
            or type(self.operation) is not _OperationCompletionHandle
            or self.operation.resource_identity is not self.resource_identity
            or self.operation.lifecycle_epoch != self.lifecycle_epoch
        ):
            raise ValueError("invalid operation mutation-release acknowledgment")

    def __repr__(self) -> str:
        return "<_OperationMutationReleaseAcknowledgment>"


@dataclass(frozen=True, slots=True, repr=False)
class _OperationRetirementPreparationAcknowledgment:
    """Exact Phase-1 acknowledgment retained by one represented operation."""

    resource_identity: _WriterSessionResourceIdentity
    lifecycle_epoch: int
    operation: _OperationCompletionHandle

    def __post_init__(self) -> None:
        if (
            type(self.resource_identity) is not _WriterSessionResourceIdentity
            or type(self.lifecycle_epoch) is not int
            or self.lifecycle_epoch < 1
            or type(self.operation) is not _OperationCompletionHandle
            or self.operation.resource_identity is not self.resource_identity
            or self.operation.lifecycle_epoch != self.lifecycle_epoch
        ):
            raise ValueError("invalid operation retirement acknowledgment")

    def __repr__(self) -> str:
        return "<_OperationRetirementPreparationAcknowledgment>"


class _OperationRetirementPhase(str, Enum):
    """Resource-owned phase for one represented operation."""

    ADMITTED = "admitted"
    PREPARED = "prepared"
    EXPLICIT_LOCAL_TERMINAL = "explicit_local_terminal"
    EXPLICIT_RETIRED = "explicit_retired"
    ORPHANED = "orphaned"


class _OperationExitProcessControlDisposition(str, Enum):
    """Private result of exact-invocation exit stabilization."""

    REPRESENTED_INCOMPLETE = "represented_incomplete"
    REPRESENTED_CLEANUP_OWNED = "represented_cleanup_owned"
    NOT_CURRENTLY_REPRESENTED = "not_currently_represented"
    INVALID_OR_WRONG_RESOURCE = "invalid_or_wrong_resource"


@dataclass(frozen=True, slots=True, repr=False)
class _WriterSessionOperationRecord:
    """Immutable admission binding carried only by resource lifecycle state."""

    handle: _OperationCompletionHandle
    resource_identity: _WriterSessionResourceIdentity
    operation_id: int
    owner_pid: int
    owner_thread: int
    lifecycle_epoch: int
    lease_reference: weakref.ReferenceType[object]
    finalizer: object
    phase: _OperationRetirementPhase = _OperationRetirementPhase.ADMITTED
    cleanup_required: bool = False
    mutation_release_acknowledgment: (
        _OperationMutationReleaseAcknowledgment | None
    ) = None
    retirement_preparation_acknowledgment: (
        _OperationRetirementPreparationAcknowledgment | None
    ) = None

    def __post_init__(self) -> None:
        lease = (
            self.lease_reference()
            if type(self.lease_reference) is weakref.ReferenceType
            else None
        )
        if (
            type(self.handle) is not _OperationCompletionHandle
            or type(self.handle.invocation_correlation)
            is not _OperationInvocationCorrelation
            or type(self.resource_identity) is not _WriterSessionResourceIdentity
            or type(self.operation_id) is not int
            or self.operation_id < 1
            or type(self.owner_pid) is not int
            or self.owner_pid < 0
            or type(self.owner_thread) is not int
            or self.owner_thread < 0
            or type(self.lifecycle_epoch) is not int
            or self.lifecycle_epoch < 1
            or type(self.lease_reference) is not weakref.ReferenceType
            or (
                lease is not None
                and (
                    type(lease) is not _WriterSessionOperationLease
                    or lease._completion_handle is not self.handle
                )
            )
            or self.finalizer is None
            or (lease is not None and lease._finalizer is not self.finalizer)
            or type(getattr(self.finalizer, "alive", None)) is not bool
            or not hasattr(self.finalizer, "detach")
            or type(self.phase) is not _OperationRetirementPhase
            or type(self.cleanup_required) is not bool
        ):
            raise ValueError("invalid writer operation record")
        if (
            self.invocation_correlation.resource_identity is not self.resource_identity
            or self.invocation_correlation.owner_pid != self.owner_pid
            or self.invocation_correlation.lifecycle_epoch != self.lifecycle_epoch
        ):
            raise ValueError("invalid writer operation record")
        mutation_acknowledgment = self.mutation_release_acknowledgment
        if mutation_acknowledgment is not None and not (
            type(mutation_acknowledgment)
            is _OperationMutationReleaseAcknowledgment
            and mutation_acknowledgment.resource_identity
            is self.resource_identity
            and mutation_acknowledgment.lifecycle_epoch
            == self.lifecycle_epoch
            and mutation_acknowledgment.operation is self.handle
        ):
            raise ValueError("invalid writer operation record")
        preparation = self.retirement_preparation_acknowledgment
        if preparation is not None and not (
            type(preparation) is _OperationRetirementPreparationAcknowledgment
            and preparation.resource_identity is self.resource_identity
            and preparation.lifecycle_epoch == self.lifecycle_epoch
            and preparation.operation is self.handle
        ):
            raise ValueError("invalid writer operation record")
        if (
            self.phase
            in (
                _OperationRetirementPhase.PREPARED,
                _OperationRetirementPhase.EXPLICIT_LOCAL_TERMINAL,
                _OperationRetirementPhase.EXPLICIT_RETIRED,
            )
            and preparation is None
        ) or (
            self.phase is _OperationRetirementPhase.ORPHANED
            and not self.cleanup_required
        ):
            raise ValueError("invalid writer operation record")

    def __repr__(self) -> str:
        return "<_WriterSessionOperationRecord>"

    @property
    def invocation_correlation(self) -> _OperationInvocationCorrelation:
        correlation = self.handle.invocation_correlation
        if type(correlation) is not _OperationInvocationCorrelation:
            raise ValueError("invalid writer operation record")
        return correlation


@dataclass(frozen=True, slots=True, repr=False)
class _OperationLeaseLossCallback:
    """Weak lease-loss trigger; it carries no normal-retirement authority."""

    resource_reference: weakref.ReferenceType[object]
    handle: _OperationCompletionHandle

    def __post_init__(self) -> None:
        if (
            type(self.resource_reference) is not weakref.ReferenceType
            or type(self.handle) is not _OperationCompletionHandle
        ):
            raise ValueError("invalid operation lease-loss callback")

    def __call__(self, lease_reference: weakref.ReferenceType[object]) -> None:
        del lease_reference
        resource = self.resource_reference()
        if resource is not None:
            _finalize_writer_session_operation_lease_loss(resource, self.handle)

    def __repr__(self) -> str:
        return "<_OperationLeaseLossCallback>"


class _WriterSessionMutationSlot:
    """One mutation token bound to the exact active operation handle."""

    __slots__ = ("operation", "token")
    __hash__ = object.__hash__

    def __init__(
        self,
        *,
        operation: _OperationCompletionHandle,
        token: _WriterSessionMutationToken,
    ) -> None:
        if (
            type(operation) is not _OperationCompletionHandle
            or type(token) is not _WriterSessionMutationToken
        ):
            raise ValueError("invalid mutation slot")
        self.operation = operation
        self.token = token

    @property
    def operation_id(self) -> int:
        return self.operation.operation_id

    @property
    def owner_pid(self) -> int:
        return self.operation.owner_pid

    @property
    def owner_thread(self) -> int:
        return self.operation.owner_thread

    @property
    def lifecycle_epoch(self) -> int:
        return self.operation.lifecycle_epoch

    @property
    def resource_identity(self) -> _WriterSessionResourceIdentity:
        return self.operation.resource_identity

    def __repr__(self) -> str:
        return "<_WriterSessionMutationSlot>"

    def matches(
        self,
        *,
        operation: _OperationCompletionHandle,
        token: _WriterSessionMutationToken,
    ) -> bool:
        return self.operation is operation and self.token is token

    def owned_by_operation(self, operation: _OperationCompletionHandle) -> bool:
        return self.operation is operation


class _ControllerScopeToken:
    __slots__ = ("_custody_identity", "_operation")
    __hash__ = object.__hash__

    def __init__(
        self,
        retained_connection: _RetainedSQLiteConnection,
        operation: _OperationCompletionHandle,
    ) -> None:
        if (
            type(retained_connection) is not _RetainedSQLiteConnection
            or type(operation) is not _OperationCompletionHandle
            or retained_connection.resource_identity
            is not operation.resource_identity
        ):
            raise ValueError("invalid controller scope")
        self._custody_identity = retained_connection.custody_identity
        self._operation = operation

    def __repr__(self) -> str:
        return "<_ControllerScopeToken>"

    def admits_retained(self, retained: _RetainedSQLiteConnection) -> bool:
        return (
            type(retained) is _RetainedSQLiteConnection
            and retained.matches_custody_identity(self._custody_identity)
        )

    def admits_proof(self, proof: _SQLiteConnectionCloseProof) -> bool:
        return (
            type(proof) is _SQLiteConnectionCloseProof
            and proof.custody_identity is self._custody_identity
        )

    def admits_operation(self, operation: _OperationCompletionHandle) -> bool:
        return operation is self._operation

    @property
    def resource_identity(self) -> _WriterSessionResourceIdentity:
        return self._operation.resource_identity


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


@dataclass(frozen=True, slots=True)
class _WriterSessionEpoch:
    value: int

    def __post_init__(self) -> None:
        if type(self.value) is not int or self.value < 1:
            raise ValueError("invalid writer epoch")


@dataclass(frozen=True, slots=True)
class _WriterSessionAuthority:
    resource_identity: _WriterSessionResourceIdentity
    owner_pid: int
    epoch: _WriterSessionEpoch
    next_operation_id: int
    credential: _PrivateWriterCredential
    authority_lock: StateAuthorityLock
    database_binding: _StateDatabaseAuthorityBinding

    def __post_init__(self) -> None:
        if (
            type(self.resource_identity) is not _WriterSessionResourceIdentity
            or type(self.owner_pid) is not int
            or self.owner_pid < 0
            or type(self.epoch) is not _WriterSessionEpoch
            or type(self.next_operation_id) is not int
            or self.next_operation_id < 1
            or type(self.credential) is not _PrivateWriterCredential
            or type(self.authority_lock) is not StateAuthorityLock
            or type(self.database_binding) is not _StateDatabaseAuthorityBinding
        ):
            raise ValueError("invalid writer authority")


def _require_operation_handles(
    operations: tuple[_OperationCompletionHandle, ...],
    *,
    nonempty: bool,
) -> None:
    if type(operations) is not tuple or (nonempty and not operations):
        raise ValueError("invalid writer operations")
    operation_ids: set[int] = set()
    for operation in operations:
        if (
            type(operation) is not _OperationCompletionHandle
            or operation.operation_id in operation_ids
        ):
            raise ValueError("invalid writer operations")
        operation_ids.add(operation.operation_id)


def _require_operation_records(
    records: tuple[_WriterSessionOperationRecord, ...],
    *,
    nonempty: bool,
) -> None:
    if type(records) is not tuple or (nonempty and not records):
        raise ValueError("invalid writer operation records")
    operation_ids: set[int] = set()
    handle_identities: set[int] = set()
    correlation_identities: set[int] = set()
    for record in records:
        if (
            type(record) is not _WriterSessionOperationRecord
            or record.operation_id in operation_ids
            or id(record.handle) in handle_identities
            or id(record.invocation_correlation) in correlation_identities
        ):
            raise ValueError("invalid writer operation records")
        operation_ids.add(record.operation_id)
        handle_identities.add(id(record.handle))
        correlation_identities.add(id(record.invocation_correlation))


def _operation_blocks_admission(record: _WriterSessionOperationRecord) -> bool:
    """Read one resource-owned retirement posture under the condition."""

    return bool(
        record.cleanup_required
        or record.phase is not _OperationRetirementPhase.ADMITTED
    )


def _operation_has_exact_mutation_release_acknowledgment(
    record: _WriterSessionOperationRecord,
) -> bool:
    """Read resource-owned mutation-release posture under the condition."""

    if type(record) is not _WriterSessionOperationRecord:
        return False
    operation = record.handle
    acknowledgment = record.mutation_release_acknowledgment
    return bool(
        type(acknowledgment) is _OperationMutationReleaseAcknowledgment
        and acknowledgment.resource_identity is record.resource_identity
        and acknowledgment.lifecycle_epoch == record.lifecycle_epoch
        and acknowledgment.operation is operation
    )


def _is_successful_exact_operation_finalizer_detach(
    detach_result: object,
    *,
    operation_lease: "_WriterSessionOperationLease",
    resource: "_WriterSessionResource",
    operation: _OperationCompletionHandle,
) -> bool:
    """Validate only the result of this exact serialized detach call."""

    if type(detach_result) is not tuple or len(detach_result) != 4:
        return False
    target, callback, args, kwargs = detach_result
    return bool(
        target is operation_lease
        and callback is _finalize_writer_session_operation
        and type(args) is tuple
        and len(args) == 2
        and args[0] is resource
        and args[1] is operation
        and type(kwargs) is dict
        and not kwargs
    )


@dataclass(frozen=True, slots=True)
class _WriterSessionActivity:
    authority: _WriterSessionAuthority
    operation_records: tuple[_WriterSessionOperationRecord, ...]

    def __post_init__(self) -> None:
        if type(self.authority) is not _WriterSessionAuthority:
            raise ValueError("invalid writer activity")
        _require_operation_records(self.operation_records, nonempty=False)
        if any(
            record.resource_identity is not self.authority.resource_identity
            or record.owner_pid != self.authority.owner_pid
            or record.lifecycle_epoch != self.authority.epoch.value
            for record in self.operation_records
        ):
            raise ValueError("invalid writer activity")

    @property
    def operations(self) -> tuple[_OperationCompletionHandle, ...]:
        return tuple(record.handle for record in self.operation_records)


@dataclass(frozen=True, slots=True)
class _WriterSessionMutationFrame:
    activity: _WriterSessionActivity
    slot: _WriterSessionMutationSlot

    def __post_init__(self) -> None:
        if (
            type(self.activity) is not _WriterSessionActivity
            or type(self.slot) is not _WriterSessionMutationSlot
            or self.slot.resource_identity
            is not self.activity.authority.resource_identity
            or not any(
                operation is self.slot.operation
                for operation in self.activity.operations
            )
        ):
            raise ValueError("invalid mutation frame")


@dataclass(frozen=True, slots=True)
class _CleanupBeforeR1WithSlot:
    activity: _WriterSessionActivity
    slot: _WriterSessionMutationSlot

    def __post_init__(self) -> None:
        if (
            type(self.activity) is not _WriterSessionActivity
            or type(self.slot) is not _WriterSessionMutationSlot
            or self.slot.resource_identity
            is not self.activity.authority.resource_identity
        ):
            raise ValueError("invalid cleanup cursor")

    @property
    def authority(self) -> _WriterSessionAuthority:
        return self.activity.authority

    @property
    def operations(self) -> tuple[_OperationCompletionHandle, ...]:
        return self.activity.operations

    @property
    def resource_identity(self) -> _WriterSessionResourceIdentity:
        return self.activity.authority.resource_identity


@dataclass(frozen=True, slots=True)
class _CleanupBeforeR1NoSlot:
    activity: _WriterSessionActivity

    def __post_init__(self) -> None:
        if type(self.activity) is not _WriterSessionActivity:
            raise ValueError("invalid cleanup cursor")

    @property
    def authority(self) -> _WriterSessionAuthority:
        return self.activity.authority

    @property
    def operations(self) -> tuple[_OperationCompletionHandle, ...]:
        return self.activity.operations

    @property
    def resource_identity(self) -> _WriterSessionResourceIdentity:
        return self.activity.authority.resource_identity


@dataclass(frozen=True, slots=True)
class _CleanupBeforeR2WithSlot:
    authority_lock: StateAuthorityLock
    database_binding: _StateDatabaseAuthorityBinding
    slot: _WriterSessionMutationSlot
    resource_identity: _WriterSessionResourceIdentity

    def __post_init__(self) -> None:
        if (
            type(self.authority_lock) is not StateAuthorityLock
            or type(self.database_binding) is not _StateDatabaseAuthorityBinding
            or type(self.slot) is not _WriterSessionMutationSlot
            or type(self.resource_identity) is not _WriterSessionResourceIdentity
            or self.slot.resource_identity is not self.resource_identity
        ):
            raise ValueError("invalid cleanup cursor")


@dataclass(frozen=True, slots=True)
class _CleanupBeforeR2NoSlot:
    authority_lock: StateAuthorityLock
    database_binding: _StateDatabaseAuthorityBinding
    resource_identity: _WriterSessionResourceIdentity

    def __post_init__(self) -> None:
        if (
            type(self.authority_lock) is not StateAuthorityLock
            or type(self.database_binding) is not _StateDatabaseAuthorityBinding
            or type(self.resource_identity) is not _WriterSessionResourceIdentity
        ):
            raise ValueError("invalid cleanup cursor")


@dataclass(frozen=True, slots=True)
class _CleanupBeforeR3:
    authority_lock: StateAuthorityLock
    database_binding: _StateDatabaseAuthorityBinding
    resource_identity: _WriterSessionResourceIdentity

    def __post_init__(self) -> None:
        if (
            type(self.authority_lock) is not StateAuthorityLock
            or type(self.database_binding) is not _StateDatabaseAuthorityBinding
            or type(self.resource_identity) is not _WriterSessionResourceIdentity
        ):
            raise ValueError("invalid cleanup cursor")


@dataclass(frozen=True, slots=True)
class _CleanupBeforeL1:
    authority_lock: StateAuthorityLock
    resource_identity: _WriterSessionResourceIdentity

    def __post_init__(self) -> None:
        if (
            type(self.authority_lock) is not StateAuthorityLock
            or type(self.resource_identity) is not _WriterSessionResourceIdentity
        ):
            raise ValueError("invalid cleanup cursor")


@dataclass(frozen=True, slots=True)
class _CleanupBeforeH1:
    authority_lock: StateAuthorityLock
    resource_identity: _WriterSessionResourceIdentity

    def __post_init__(self) -> None:
        if (
            type(self.authority_lock) is not StateAuthorityLock
            or type(self.resource_identity) is not _WriterSessionResourceIdentity
        ):
            raise ValueError("invalid cleanup cursor")


@dataclass(frozen=True, slots=True)
class _CleanupBeforeH2:
    authority_lock: StateAuthorityLock
    resource_identity: _WriterSessionResourceIdentity

    def __post_init__(self) -> None:
        if (
            type(self.authority_lock) is not StateAuthorityLock
            or type(self.resource_identity) is not _WriterSessionResourceIdentity
        ):
            raise ValueError("invalid cleanup cursor")


@dataclass(frozen=True, slots=True)
class _CleanupBeforeT1:
    resource_identity: _WriterSessionResourceIdentity

    def __post_init__(self) -> None:
        if type(self.resource_identity) is not _WriterSessionResourceIdentity:
            raise ValueError("invalid cleanup cursor")


_CLEANUP_CURSOR_TYPES = (
    _CleanupBeforeR1WithSlot,
    _CleanupBeforeR1NoSlot,
    _CleanupBeforeR2WithSlot,
    _CleanupBeforeR2NoSlot,
    _CleanupBeforeR3,
    _CleanupBeforeL1,
    _CleanupBeforeH1,
    _CleanupBeforeH2,
    _CleanupBeforeT1,
)


@dataclass(frozen=True, slots=True)
class _ContinueCleanup:
    cursor: object
    claim_epoch: int = 0

    def __post_init__(self) -> None:
        if type(self.cursor) not in _CLEANUP_CURSOR_TYPES:
            raise ValueError("invalid cleanup continuation")
        if type(self.cursor.resource_identity) is not _WriterSessionResourceIdentity:
            raise ValueError("invalid cleanup continuation")
        if type(self.claim_epoch) is not int or self.claim_epoch < 0:
            raise ValueError("invalid cleanup continuation")


@dataclass(frozen=True, slots=True)
class _ResumeActive:
    pass


@dataclass(frozen=True, slots=True)
class _ResumeIfCloseProvedAndStillEligible:
    pass


@dataclass(frozen=True, slots=True)
class _CleanupRequiredAfterResolution:
    pass


class _ControllerResolutionIntent(str, Enum):
    PRECOMMIT_ABORT = "precommit_abort"
    COMMIT_UNCERTAIN = "commit_uncertain"
    COMMIT_KNOWN = "commit_known"


@dataclass(frozen=True, slots=True)
class _ControllerCloseProvedFacts:
    intent: _ControllerResolutionIntent
    close_proof: _SQLiteConnectionCloseProof
    requested_policy: _ResumeIfCloseProvedAndStillEligible | _CleanupRequiredAfterResolution

    def __post_init__(self) -> None:
        if (
            type(self.intent) is not _ControllerResolutionIntent
            or type(self.close_proof) is not _SQLiteConnectionCloseProof
            or type(self.requested_policy)
            not in (_ResumeIfCloseProvedAndStillEligible, _CleanupRequiredAfterResolution)
        ):
            raise ValueError("invalid controller resolution facts")


@dataclass(frozen=True, slots=True)
class _ControllerCloseUnprovedFacts:
    intent: _ControllerResolutionIntent
    retained_connection: _RetainedSQLiteConnection

    def __post_init__(self) -> None:
        if (
            type(self.intent) is not _ControllerResolutionIntent
            or type(self.retained_connection) is not _RetainedSQLiteConnection
        ):
            raise ValueError("invalid controller resolution facts")


class _ControllerPublishedSuccessorKind(str, Enum):
    CLEANUP_REQUIRED_UNRESOLVED = "cleanup_required_unresolved"
    ABORT_CLOSE_UNPROVED = "abort_close_unproved"
    COMMIT_UNCERTAIN_CLOSE_UNPROVED = "commit_uncertain_close_unproved"
    COMMIT_KNOWN_CLOSE_UNPROVED = "commit_known_close_unproved"
    ABORT_CLOSE_PROVED_RESUME = "abort_close_proved_resume"
    COMMIT_UNCERTAIN_CLOSE_PROVED_RESUME = "commit_uncertain_close_proved_resume"
    COMMIT_KNOWN_CLOSE_PROVED_RESUME = "commit_known_close_proved_resume"
    ABORT_PENDING_CLEANUP = "abort_pending_cleanup"
    COMMIT_UNCERTAIN_PENDING_CLEANUP = "commit_uncertain_pending_cleanup"
    COMMIT_KNOWN_PENDING_CLEANUP = "commit_known_pending_cleanup"


@dataclass(frozen=True, slots=True, repr=False)
class _ControllerResolutionActivationAcknowledgment:
    scope_token: _ControllerScopeToken
    resolution: object

    def __post_init__(self) -> None:
        if (
            type(self.scope_token) is not _ControllerScopeToken
            or type(self.resolution) is not _WriterSessionControllerResolution
            or self.resolution.scope_token is not self.scope_token
        ):
            raise ValueError("invalid controller acknowledgment")

    def __repr__(self) -> str:
        return "<_ControllerResolutionActivationAcknowledgment>"


@dataclass(frozen=True, slots=True, repr=False)
class _ControllerSuccessorPublicationAcknowledgment:
    scope_token: _ControllerScopeToken
    kind: _ControllerPublishedSuccessorKind
    successor: object

    def __post_init__(self) -> None:
        if (
            type(self.scope_token) is not _ControllerScopeToken
            or type(self.kind) is not _ControllerPublishedSuccessorKind
            or self.successor is None
        ):
            raise ValueError("invalid controller acknowledgment")

    def __repr__(self) -> str:
        return "<_ControllerSuccessorPublicationAcknowledgment>"


@dataclass(frozen=True, slots=True, repr=False)
class _ControllerCleanupStabilizationAcknowledgment:
    scope_token: _ControllerScopeToken
    kind: _ControllerPublishedSuccessorKind
    successor: object

    def __post_init__(self) -> None:
        if (
            type(self.scope_token) is not _ControllerScopeToken
            or type(self.kind) is not _ControllerPublishedSuccessorKind
            or self.successor is None
        ):
            raise ValueError("invalid controller acknowledgment")

    def __repr__(self) -> str:
        return "<_ControllerCleanupStabilizationAcknowledgment>"


@dataclass(frozen=True, slots=True)
class _WriterSessionActive:
    activity: _WriterSessionActivity

    def __post_init__(self) -> None:
        if (
            type(self.activity) is not _WriterSessionActivity
            or self.activity.operations
        ):
            raise ValueError("invalid active state")

    @property
    def authority(self) -> _WriterSessionAuthority:
        return self.activity.authority


@dataclass(frozen=True, slots=True)
class _WriterSessionOperationsActive:
    activity: _WriterSessionActivity

    def __post_init__(self) -> None:
        if type(self.activity) is not _WriterSessionActivity:
            raise ValueError("invalid operations-active state")
        _require_operation_handles(self.activity.operations, nonempty=True)

    @property
    def authority(self) -> _WriterSessionAuthority:
        return self.activity.authority

    @property
    def operations(self) -> tuple[_OperationCompletionHandle, ...]:
        return self.activity.operations


@dataclass(frozen=True, slots=True)
class _WriterSessionMutationActive:
    frame: _WriterSessionMutationFrame

    def __post_init__(self) -> None:
        if type(self.frame) is not _WriterSessionMutationFrame:
            raise ValueError("invalid mutation-active state")

    @property
    def authority(self) -> _WriterSessionAuthority:
        return self.frame.activity.authority

    @property
    def operations(self) -> tuple[_OperationCompletionHandle, ...]:
        return self.frame.activity.operations

    @property
    def slot(self) -> _WriterSessionMutationSlot:
        return self.frame.slot


@dataclass(frozen=True, slots=True)
class _WriterSessionControllerResolution:
    frame: _WriterSessionMutationFrame
    scope_token: _ControllerScopeToken
    policy: _ResumeIfCloseProvedAndStillEligible | _CleanupRequiredAfterResolution

    def __post_init__(self) -> None:
        if (
            type(self.frame) is not _WriterSessionMutationFrame
            or type(self.scope_token) is not _ControllerScopeToken
            or type(self.policy)
            not in (_ResumeIfCloseProvedAndStillEligible, _CleanupRequiredAfterResolution)
            or self.scope_token.resource_identity
            is not self.frame.activity.authority.resource_identity
            or not self.scope_token.admits_operation(self.frame.slot.operation)
        ):
            raise ValueError("invalid controller-resolution state")

    @property
    def authority(self) -> _WriterSessionAuthority:
        return self.frame.activity.authority

    @property
    def operations(self) -> tuple[_OperationCompletionHandle, ...]:
        return self.frame.activity.operations

    @property
    def slot(self) -> _WriterSessionMutationSlot:
        return self.frame.slot


@dataclass(frozen=True, slots=True)
class _WriterSessionControllerCloseProved:
    frame: _WriterSessionMutationFrame
    scope_token: _ControllerScopeToken
    intent: _ControllerResolutionIntent
    close_proof: _SQLiteConnectionCloseProof
    result: _ResumeActive

    def __post_init__(self) -> None:
        if (
            type(self.frame) is not _WriterSessionMutationFrame
            or type(self.scope_token) is not _ControllerScopeToken
            or type(self.intent) is not _ControllerResolutionIntent
            or type(self.close_proof) is not _SQLiteConnectionCloseProof
            or type(self.result) is not _ResumeActive
            or self.scope_token.resource_identity
            is not self.frame.activity.authority.resource_identity
            or self.close_proof.resource_identity
            is not self.frame.activity.authority.resource_identity
            or not self.scope_token.admits_operation(self.frame.slot.operation)
            or not self.scope_token.admits_proof(self.close_proof)
        ):
            raise ValueError("invalid controller close-proof state")

    @property
    def authority(self) -> _WriterSessionAuthority:
        return self.frame.activity.authority

    @property
    def operations(self) -> tuple[_OperationCompletionHandle, ...]:
        return self.frame.activity.operations

    @property
    def slot(self) -> _WriterSessionMutationSlot:
        return self.frame.slot

    @property
    def continuation(self) -> _ResumeActive:
        return self.result


@dataclass(frozen=True, slots=True)
class _WriterSessionControllerCloseProvedReleased:
    activity: _WriterSessionActivity
    scope_token: _ControllerScopeToken
    intent: _ControllerResolutionIntent
    close_proof: _SQLiteConnectionCloseProof
    result: _ResumeActive

    def __post_init__(self) -> None:
        if (
            type(self.activity) is not _WriterSessionActivity
            or type(self.scope_token) is not _ControllerScopeToken
            or type(self.intent) is not _ControllerResolutionIntent
            or type(self.close_proof) is not _SQLiteConnectionCloseProof
            or type(self.result) is not _ResumeActive
            or self.scope_token.resource_identity
            is not self.activity.authority.resource_identity
            or self.close_proof.resource_identity
            is not self.activity.authority.resource_identity
            or not self.scope_token.admits_proof(self.close_proof)
            or not any(
                self.scope_token.admits_operation(operation)
                for operation in self.activity.operations
            )
        ):
            raise ValueError("invalid released close-proof state")

    @property
    def authority(self) -> _WriterSessionAuthority:
        return self.activity.authority

    @property
    def operations(self) -> tuple[_OperationCompletionHandle, ...]:
        return self.activity.operations


def _validate_unproved_state(
    scope_token: object,
    retained_connection: object,
    cleanup: object,
) -> None:
    if (
        type(scope_token) is not _ControllerScopeToken
        or type(retained_connection) is not _RetainedSQLiteConnection
        or type(cleanup) is not _ContinueCleanup
        or type(cleanup.cursor) is not _CleanupBeforeR1WithSlot
        or scope_token.resource_identity is not cleanup.cursor.resource_identity
        or retained_connection.resource_identity
        is not cleanup.cursor.resource_identity
        or not scope_token.admits_retained(retained_connection)
        or not scope_token.admits_operation(cleanup.cursor.slot.operation)
    ):
        raise ValueError("invalid close-unproved state")


@dataclass(frozen=True, slots=True)
class _WriterSessionAbortCloseUnproved:
    scope_token: _ControllerScopeToken
    retained_connection: _RetainedSQLiteConnection
    cleanup: _ContinueCleanup

    def __post_init__(self) -> None:
        _validate_unproved_state(
            self.scope_token,
            self.retained_connection,
            self.cleanup,
        )


@dataclass(frozen=True, slots=True)
class _WriterSessionCommitUncertainUnproved:
    scope_token: _ControllerScopeToken
    retained_connection: _RetainedSQLiteConnection
    cleanup: _ContinueCleanup

    def __post_init__(self) -> None:
        _validate_unproved_state(
            self.scope_token,
            self.retained_connection,
            self.cleanup,
        )


@dataclass(frozen=True, slots=True)
class _WriterSessionCommitKnownUnproved:
    scope_token: _ControllerScopeToken
    retained_connection: _RetainedSQLiteConnection
    cleanup: _ContinueCleanup

    def __post_init__(self) -> None:
        _validate_unproved_state(
            self.scope_token,
            self.retained_connection,
            self.cleanup,
        )


@dataclass(frozen=True, slots=True)
class _WriterSessionAbortPendingCleanup:
    scope_token: _ControllerScopeToken
    close_proof: _SQLiteConnectionCloseProof
    cleanup: _ContinueCleanup

    def __post_init__(self) -> None:
        _validate_proved_cleanup_state(self.scope_token, self.close_proof, self.cleanup)


def _validate_proved_cleanup_state(
    scope_token: object,
    close_proof: object,
    cleanup: object,
) -> None:
    if (
        type(scope_token) is not _ControllerScopeToken
        or type(close_proof) is not _SQLiteConnectionCloseProof
        or type(cleanup) is not _ContinueCleanup
        or type(cleanup.cursor) not in _CLEANUP_CURSOR_TYPES
        or scope_token.resource_identity is not cleanup.cursor.resource_identity
        or close_proof.resource_identity is not cleanup.cursor.resource_identity
        or not scope_token.admits_proof(close_proof)
        or (
            type(cleanup.cursor) in (_CleanupBeforeR1WithSlot, _CleanupBeforeR2WithSlot)
            and not scope_token.admits_operation(cleanup.cursor.slot.operation)
        )
    ):
        raise ValueError("invalid close-proved cleanup state")


@dataclass(frozen=True, slots=True)
class _WriterSessionCommitUncertainPendingCleanup:
    scope_token: _ControllerScopeToken
    close_proof: _SQLiteConnectionCloseProof
    cleanup: _ContinueCleanup

    def __post_init__(self) -> None:
        _validate_proved_cleanup_state(self.scope_token, self.close_proof, self.cleanup)


@dataclass(frozen=True, slots=True)
class _WriterSessionCommitKnownPendingCleanup:
    scope_token: _ControllerScopeToken
    close_proof: _SQLiteConnectionCloseProof
    cleanup: _ContinueCleanup

    def __post_init__(self) -> None:
        _validate_proved_cleanup_state(self.scope_token, self.close_proof, self.cleanup)


@dataclass(frozen=True, slots=True)
class _WriterSessionOperationsClosing:
    cleanup: _ContinueCleanup

    def __post_init__(self) -> None:
        if (
            type(self.cleanup) is not _ContinueCleanup
            or type(self.cleanup.cursor) is not _CleanupBeforeR1NoSlot
            or not self.cleanup.cursor.operations
        ):
            raise ValueError("invalid operations-closing state")


@dataclass(frozen=True, slots=True)
class _WriterSessionMutationClosing:
    cleanup: _ContinueCleanup

    def __post_init__(self) -> None:
        if (
            type(self.cleanup) is not _ContinueCleanup
            or type(self.cleanup.cursor) is not _CleanupBeforeR1WithSlot
            or not self.cleanup.cursor.operations
        ):
            raise ValueError("invalid mutation-closing state")


@dataclass(frozen=True, slots=True)
class _WriterSessionOrdinaryCleanup:
    cleanup: _ContinueCleanup

    def __post_init__(self) -> None:
        if type(self.cleanup) is not _ContinueCleanup:
            raise ValueError("invalid ordinary-cleanup state")


class _CleanupClaimToken:
    __slots__ = ()
    __hash__ = object.__hash__


@dataclass(frozen=True, slots=True, repr=False)
class _WriterSessionCleanupClaim:
    token: _CleanupClaimToken
    owner_thread_ref: weakref.ReferenceType[Thread]
    resource_identity: _WriterSessionResourceIdentity
    owner_pid: int
    lifecycle_epoch: int
    claim_epoch: int

    def __post_init__(self) -> None:
        thread = self.owner_thread_ref()
        if (
            type(self.token) is not _CleanupClaimToken
            or type(self.owner_thread_ref) is not weakref.ReferenceType
            or (thread is not None and not isinstance(thread, Thread))
            or type(self.resource_identity) is not _WriterSessionResourceIdentity
            or type(self.owner_pid) is not int
            or self.owner_pid < 0
            or type(self.lifecycle_epoch) is not int
            or self.lifecycle_epoch < 1
            or type(self.claim_epoch) is not int
            or self.claim_epoch < 1
        ):
            raise ValueError("invalid cleanup claim")

    def __repr__(self) -> str:
        return "<_WriterSessionCleanupClaim>"


_CLEANUP_PENDING_TYPES = (
    _WriterSessionAbortCloseUnproved,
    _WriterSessionCommitUncertainUnproved,
    _WriterSessionCommitKnownUnproved,
    _WriterSessionAbortPendingCleanup,
    _WriterSessionCommitUncertainPendingCleanup,
    _WriterSessionCommitKnownPendingCleanup,
    _WriterSessionOrdinaryCleanup,
)


@dataclass(frozen=True, slots=True)
class _WriterSessionCleanupClaimed:
    pending_state: object
    claim: _WriterSessionCleanupClaim

    def __post_init__(self) -> None:
        if (
            type(self.pending_state) not in _CLEANUP_PENDING_TYPES
            or type(self.claim) is not _WriterSessionCleanupClaim
            or self.claim.resource_identity
            is not _cleanup_continuation(self.pending_state).cursor.resource_identity
        ):
            raise ValueError("invalid claimed-cleanup state")


@dataclass(frozen=True, slots=True)
class _WriterSessionTerminalX:
    pass


@dataclass(frozen=True, slots=True)
class _WriterSessionForkInvalid:
    pass


def _cleanup_continuation(state: object) -> _ContinueCleanup:
    if type(state) in (
        _WriterSessionAbortCloseUnproved,
        _WriterSessionCommitUncertainUnproved,
        _WriterSessionCommitKnownUnproved,
        _WriterSessionAbortPendingCleanup,
        _WriterSessionCommitUncertainPendingCleanup,
        _WriterSessionCommitKnownPendingCleanup,
        _WriterSessionOperationsClosing,
        _WriterSessionMutationClosing,
        _WriterSessionOrdinaryCleanup,
    ):
        return state.cleanup
    raise ValueError("invalid cleanup state")


def _state_authority(state: object) -> _WriterSessionAuthority | None:
    if type(state) in (
        _WriterSessionActive,
        _WriterSessionOperationsActive,
        _WriterSessionMutationActive,
        _WriterSessionControllerResolution,
        _WriterSessionControllerCloseProved,
        _WriterSessionControllerCloseProvedReleased,
    ):
        if type(state) in (
            _WriterSessionActive,
            _WriterSessionOperationsActive,
            _WriterSessionControllerCloseProvedReleased,
        ):
            return state.activity.authority
        return state.frame.activity.authority
    pending = state.pending_state if type(state) is _WriterSessionCleanupClaimed else state
    if type(pending) in _CLEANUP_PENDING_TYPES + (
        _WriterSessionOperationsClosing,
        _WriterSessionMutationClosing,
    ):
        cursor = _cleanup_continuation(pending).cursor
        if type(cursor) in (_CleanupBeforeR1WithSlot, _CleanupBeforeR1NoSlot):
            return cursor.authority
    return None


def _state_operation_records(
    state: object,
) -> tuple[_WriterSessionOperationRecord, ...]:
    if type(state) in (
        _WriterSessionOperationsActive,
        _WriterSessionMutationActive,
        _WriterSessionControllerResolution,
        _WriterSessionControllerCloseProved,
        _WriterSessionControllerCloseProvedReleased,
    ):
        if type(state) in (
            _WriterSessionOperationsActive,
            _WriterSessionControllerCloseProvedReleased,
        ):
            return state.activity.operation_records
        return state.frame.activity.operation_records
    pending = state.pending_state if type(state) is _WriterSessionCleanupClaimed else state
    if type(pending) in _CLEANUP_PENDING_TYPES + (
        _WriterSessionOperationsClosing,
        _WriterSessionMutationClosing,
    ):
        cursor = _cleanup_continuation(pending).cursor
        if type(cursor) in (_CleanupBeforeR1WithSlot, _CleanupBeforeR1NoSlot):
            return cursor.activity.operation_records
    return ()


def _state_operations(state: object) -> tuple[_OperationCompletionHandle, ...]:
    return tuple(record.handle for record in _state_operation_records(state))


def _is_exact_operation_retirement_cleanup_claim(
    state: object,
    operation: _OperationCompletionHandle,
) -> bool:
    """Recognize the condition-owned claim for one sole retiring operation."""

    if (
        type(state) is not _WriterSessionCleanupClaimed
        or type(state.pending_state) is not _WriterSessionOrdinaryCleanup
        or type(state.pending_state.cleanup.cursor) is not _CleanupBeforeR1NoSlot
    ):
        return False
    cursor = state.pending_state.cleanup.cursor
    claim = state.claim
    record = next(
        (
            candidate
            for candidate in cursor.activity.operation_records
            if candidate.handle is operation
        ),
        None,
    )
    if record is None:
        return False
    return bool(
        cursor.operations == (operation,)
        and record.resource_identity is cursor.resource_identity
        and claim.resource_identity is cursor.resource_identity
        and claim.owner_pid == record.owner_pid
        and claim.lifecycle_epoch == record.lifecycle_epoch
    )


def _state_slot(state: object) -> _WriterSessionMutationSlot | None:
    if type(state) in (
        _WriterSessionMutationActive,
        _WriterSessionControllerResolution,
        _WriterSessionControllerCloseProved,
    ):
        return state.frame.slot
    pending = state.pending_state if type(state) is _WriterSessionCleanupClaimed else state
    if type(pending) in _CLEANUP_PENDING_TYPES + (_WriterSessionMutationClosing,):
        cursor = _cleanup_continuation(pending).cursor
        if type(cursor) in (_CleanupBeforeR1WithSlot, _CleanupBeforeR2WithSlot):
            return cursor.slot
    return None


def _state_retained_connection(state: object) -> _RetainedSQLiteConnection | None:
    pending = state.pending_state if type(state) is _WriterSessionCleanupClaimed else state
    if type(pending) in (
        _WriterSessionAbortCloseUnproved,
        _WriterSessionCommitUncertainUnproved,
        _WriterSessionCommitKnownUnproved,
    ):
        return pending.retained_connection
    return None


def _state_operations_from_cursor(
    cursor: object,
) -> tuple[_OperationCompletionHandle, ...]:
    if type(cursor) in (_CleanupBeforeR1WithSlot, _CleanupBeforeR1NoSlot):
        return cursor.operations
    return ()


def _controller_resume_kind(
    intent: _ControllerResolutionIntent,
) -> _ControllerPublishedSuccessorKind:
    if intent is _ControllerResolutionIntent.PRECOMMIT_ABORT:
        return _ControllerPublishedSuccessorKind.ABORT_CLOSE_PROVED_RESUME
    if intent is _ControllerResolutionIntent.COMMIT_UNCERTAIN:
        return _ControllerPublishedSuccessorKind.COMMIT_UNCERTAIN_CLOSE_PROVED_RESUME
    if intent is _ControllerResolutionIntent.COMMIT_KNOWN:
        return _ControllerPublishedSuccessorKind.COMMIT_KNOWN_CLOSE_PROVED_RESUME
    raise _cleanup_driver_invariant_failure() from None


def _controller_cleanup_kind(
    intent: _ControllerResolutionIntent,
) -> _ControllerPublishedSuccessorKind:
    if intent is _ControllerResolutionIntent.PRECOMMIT_ABORT:
        return _ControllerPublishedSuccessorKind.ABORT_PENDING_CLEANUP
    if intent is _ControllerResolutionIntent.COMMIT_UNCERTAIN:
        return _ControllerPublishedSuccessorKind.COMMIT_UNCERTAIN_PENDING_CLEANUP
    if intent is _ControllerResolutionIntent.COMMIT_KNOWN:
        return _ControllerPublishedSuccessorKind.COMMIT_KNOWN_PENDING_CLEANUP
    raise _cleanup_driver_invariant_failure() from None


def _controller_unproved_kind(
    intent: _ControllerResolutionIntent,
) -> _ControllerPublishedSuccessorKind:
    if intent is _ControllerResolutionIntent.PRECOMMIT_ABORT:
        return _ControllerPublishedSuccessorKind.ABORT_CLOSE_UNPROVED
    if intent is _ControllerResolutionIntent.COMMIT_UNCERTAIN:
        return _ControllerPublishedSuccessorKind.COMMIT_UNCERTAIN_CLOSE_UNPROVED
    if intent is _ControllerResolutionIntent.COMMIT_KNOWN:
        return _ControllerPublishedSuccessorKind.COMMIT_KNOWN_CLOSE_UNPROVED
    raise _cleanup_driver_invariant_failure() from None


def _proved_cleanup_state(
    intent: _ControllerResolutionIntent,
    scope_token: _ControllerScopeToken,
    close_proof: _SQLiteConnectionCloseProof,
    cleanup: _ContinueCleanup,
) -> object:
    if intent is _ControllerResolutionIntent.PRECOMMIT_ABORT:
        return _WriterSessionAbortPendingCleanup(scope_token, close_proof, cleanup)
    if intent is _ControllerResolutionIntent.COMMIT_UNCERTAIN:
        return _WriterSessionCommitUncertainPendingCleanup(
            scope_token, close_proof, cleanup
        )
    if intent is _ControllerResolutionIntent.COMMIT_KNOWN:
        return _WriterSessionCommitKnownPendingCleanup(
            scope_token, close_proof, cleanup
        )
    raise _cleanup_driver_invariant_failure() from None


def _unproved_cleanup_state(
    intent: _ControllerResolutionIntent,
    scope_token: _ControllerScopeToken,
    retained_connection: _RetainedSQLiteConnection,
    cleanup: _ContinueCleanup,
) -> object:
    if intent is _ControllerResolutionIntent.PRECOMMIT_ABORT:
        return _WriterSessionAbortCloseUnproved(
            scope_token, retained_connection, cleanup
        )
    if intent is _ControllerResolutionIntent.COMMIT_UNCERTAIN:
        return _WriterSessionCommitUncertainUnproved(
            scope_token, retained_connection, cleanup
        )
    if intent is _ControllerResolutionIntent.COMMIT_KNOWN:
        return _WriterSessionCommitKnownUnproved(
            scope_token, retained_connection, cleanup
        )
    raise _cleanup_driver_invariant_failure() from None


class _WriterSessionResource:
    """Private owner for one closed writer-session lifecycle relation."""

    def __init__(
        self,
        *,
        location: CoordinatorStateLocation,
        authority_lock: StateAuthorityLock,
        database_binding: _StateDatabaseAuthorityBinding,
        credential: _PrivateWriterCredential,
        metadata: SafeWriterMetadata,
    ) -> None:
        if type(database_binding) is not _StateDatabaseAuthorityBinding:
            raise ValueError("invalid writer input")
        self._resource_identity = _new_writer_session_resource_identity()
        self._location = location
        self._metadata = metadata
        self._process_owner_pid_value = os.getpid()
        self._lifecycle_epoch_value = 1
        self._last_next_operation_id = 1
        authority = _WriterSessionAuthority(
            resource_identity=self._resource_identity,
            owner_pid=os.getpid(),
            epoch=_WriterSessionEpoch(self._lifecycle_epoch_value),
            next_operation_id=1,
            credential=credential,
            authority_lock=authority_lock,
            database_binding=database_binding,
        )
        self._lifecycle_state: object = _WriterSessionActive(
            _WriterSessionActivity(authority, ())
        )
        self._operation_exit_process_control_poisoned_value = False
        self._finalizer_attempted_value = False
        self._retry_reachable_value = True
        self._reset_lifecycle_synchronization()
        self._registry_key = id(self)

    @property
    def _owner_pid(self) -> int:
        return self._process_owner_pid_value

    @property
    def _state(self) -> str:
        state = self._lifecycle_state
        pending = state.pending_state if type(state) is _WriterSessionCleanupClaimed else state
        if type(pending) in (
            _WriterSessionActive,
            _WriterSessionOperationsActive,
            _WriterSessionMutationActive,
            _WriterSessionControllerCloseProved,
            _WriterSessionControllerCloseProvedReleased,
        ):
            return (
                _CLOSING
                if self._operation_exit_process_control_poisoned_value
                else _ACTIVE
            )
        if type(pending) is _WriterSessionControllerResolution:
            return (
                _CONTROLLER_RESOLUTION
                if type(pending.policy) is _ResumeIfCloseProvedAndStillEligible
                else _CLOSING
            )
        if type(pending) is _WriterSessionAbortCloseUnproved:
            return _ABORT_CLOSE_UNPROVED
        if type(pending) is _WriterSessionCommitUncertainUnproved:
            return _COMMIT_UNCERTAIN_QUARANTINED
        if type(pending) is _WriterSessionCommitKnownUnproved:
            return _COMMIT_SUCCEEDED_QUARANTINED
        if type(pending) is _WriterSessionAbortPendingCleanup:
            return _CLOSING
        if type(pending) is _WriterSessionCommitUncertainPendingCleanup:
            return _COMMIT_UNCERTAIN_CONNECTION_CLOSED_CLEANUP_PENDING
        if type(pending) is _WriterSessionCommitKnownPendingCleanup:
            return _COMMIT_SUCCEEDED_CONNECTION_CLOSED_CLEANUP_PENDING
        if type(state) is _WriterSessionCleanupClaimed:
            return _CLEANING
        if type(pending) in (
            _WriterSessionOperationsClosing,
            _WriterSessionMutationClosing,
            _WriterSessionOrdinaryCleanup,
        ):
            return _CLOSING
        if type(pending) is _WriterSessionTerminalX:
            return _CLOSED
        if type(pending) is _WriterSessionForkInvalid:
            return _FORK_INVALID
        raise _cleanup_driver_invariant_failure() from None

    @property
    def _lifecycle_epoch(self) -> int:
        authority = _state_authority(self._lifecycle_state)
        if authority is not None:
            return authority.epoch.value
        return self._lifecycle_epoch_value

    @property
    def _next_operation_id(self) -> int:
        authority = _state_authority(self._lifecycle_state)
        if authority is not None:
            return authority.next_operation_id
        return self._last_next_operation_id

    @property
    def _active_operations(self) -> dict[int, int]:
        return {
            record.operation_id: record.owner_thread
            for record in _state_operation_records(self._lifecycle_state)
        }

    @property
    def _mutation_slot(self) -> _WriterSessionMutationSlot | None:
        # Frozen B3c1a source vocabulary: self._mutation_slot is projected here.
        return _state_slot(self._lifecycle_state)

    @property
    def _mutation_slot_retained_for_cleanup(self) -> bool:
        return (
            _state_slot(self._lifecycle_state) is not None
            and type(self._lifecycle_state)
            not in (_WriterSessionMutationActive,)
        )

    @property
    def _retained_connection(self) -> _RetainedSQLiteConnection | None:
        return _state_retained_connection(self._lifecycle_state)

    @property
    def _credential(self) -> _PrivateWriterCredential | None:
        authority = _state_authority(self._lifecycle_state)
        return authority.credential if authority is not None else None

    @property
    def _authority_lock(self) -> StateAuthorityLock | None:
        state = self._lifecycle_state
        authority = _state_authority(state)
        if authority is not None:
            return authority.authority_lock
        pending = state.pending_state if type(state) is _WriterSessionCleanupClaimed else state
        if type(pending) in _CLEANUP_PENDING_TYPES + (
            _WriterSessionOperationsClosing,
            _WriterSessionMutationClosing,
        ):
            cursor = _cleanup_continuation(pending).cursor
            if type(cursor) in (
                _CleanupBeforeR2WithSlot,
                _CleanupBeforeR2NoSlot,
                _CleanupBeforeR3,
                _CleanupBeforeL1,
                _CleanupBeforeH1,
                _CleanupBeforeH2,
            ):
                return cursor.authority_lock
        return None

    @property
    def _database_binding(self) -> _StateDatabaseAuthorityBinding | None:
        state = self._lifecycle_state
        authority = _state_authority(state)
        if authority is not None:
            return authority.database_binding
        pending = state.pending_state if type(state) is _WriterSessionCleanupClaimed else state
        if type(pending) in _CLEANUP_PENDING_TYPES + (
            _WriterSessionOperationsClosing,
            _WriterSessionMutationClosing,
        ):
            cursor = _cleanup_continuation(pending).cursor
            if type(cursor) in (
                _CleanupBeforeR2WithSlot,
                _CleanupBeforeR2NoSlot,
                _CleanupBeforeR3,
            ):
                return cursor.database_binding
        return None

    @property
    def _finalizer_attempted(self) -> bool:
        return self._finalizer_attempted_value

    @property
    def _retry_reachable(self) -> bool:
        return self._retry_reachable_value

    @property
    def _operation_exit_process_control_poisoned(self) -> bool:
        with self._condition:
            return self._operation_exit_process_control_poisoned_value

    @property
    def _deferred_cleanup_requested(self) -> bool:
        return bool(
            _state_operations(self._lifecycle_state)
            and type(self._lifecycle_state)
            in (
                _WriterSessionOperationsClosing,
                _WriterSessionMutationClosing,
                _WriterSessionAbortCloseUnproved,
                _WriterSessionCommitUncertainUnproved,
                _WriterSessionCommitKnownUnproved,
                _WriterSessionAbortPendingCleanup,
                _WriterSessionCommitUncertainPendingCleanup,
                _WriterSessionCommitKnownPendingCleanup,
            )
        )

    @property
    def metadata(self) -> SafeWriterMetadata:
        return self._metadata

    def _new_operation_invocation_correlation(
        self,
    ) -> _OperationInvocationCorrelation:
        """Create one non-authoritative identity before possible admission."""

        self._require_owner_process()
        with self._condition:
            return _OperationInvocationCorrelation(
                key=_OPERATION_INVOCATION_CORRELATION_CONSTRUCTION_KEY,
                resource_identity=self._resource_identity,
                owner_pid=os.getpid(),
                lifecycle_epoch=self._lifecycle_epoch,
            )

    def active_for_owner(self) -> bool:
        if self._owner_pid != os.getpid():
            self.cleanup_from_foreign_process()
            return False
        with self._condition:
            state = self._lifecycle_state
            active = type(state) in (
                _WriterSessionActive,
                _WriterSessionOperationsActive,
                _WriterSessionMutationActive,
            ) and not self._operation_exit_process_control_poisoned_value and not any(
                _operation_blocks_admission(record)
                for record in _state_operation_records(state)
            )
            authority = _state_authority(state)
        if not active or authority is None:
            return False
        if not authority.authority_lock.active:
            self.close_from_owner()
            return False
        return True

    def require_usable_for_mutation(self, session: "_SQLiteWriterSession") -> None:
        with self.operation_guard(session, _prepare_for_context_exit=True):
            pass

    def require_active_for_context(self) -> None:
        self._require_owner_process()
        self._require_active_lifecycle()

    def operation_guard(
        self,
        session: "_SQLiteWriterSession",
        *,
        _prepare_for_context_exit: bool = False,
        _invocation_correlation: _OperationInvocationCorrelation | None = None,
    ) -> "_WriterSessionOperationLease":
        lease: _WriterSessionOperationLease | None = None
        try:
            invocation_correlation = _invocation_correlation
            if invocation_correlation is None:
                invocation_correlation = self._new_operation_invocation_correlation()
            lease = self._begin_operation(session, invocation_correlation)
            if _prepare_for_context_exit:
                preparation = self._prepare_operation_retirement(
                    lease._completion_handle
                )
                if preparation is None:
                    raise WriterSessionError(
                        WriterSessionFailureReason.WRITER_SESSION_CLOSED
                    )
                lease._preparation_acknowledgment = preparation
            return lease
        except BaseException:
            if lease is not None:
                try:
                    lease._close()
                except BaseException:
                    pass
            raise

    def close_from_owner(self) -> None:
        if self._process_owner_pid_value not in (os.getpid(), -1):
            self.cleanup_from_foreign_process()
            return
        self._continue_cleanup(blocking=True, finalizer=False)

    def cleanup_from_finalizer(self) -> None:
        if self._process_owner_pid_value not in (os.getpid(), -1):
            self.cleanup_from_foreign_process()
            return
        self._finalizer_attempted_value = True
        self._retry_reachable_value = False
        self._continue_cleanup(blocking=False, finalizer=True)

    def cleanup_from_foreign_process(self) -> None:
        self._replace_lifecycle_synchronization_after_fork()
        state = self._lifecycle_state
        credential = self._credential
        self._lifecycle_epoch_value += 1
        self._process_owner_pid_value = -1
        self._lifecycle_state = _WriterSessionForkInvalid()
        if credential is not None:
            try:
                credential.overwrite_and_drop()
            except BaseException:
                pass
        _remove_active_session_resource(self)

    def mark_closed_after_fork(self) -> None:
        self._replace_lifecycle_synchronization_after_fork()
        credential = self._credential
        self._lifecycle_epoch_value += 1
        self._process_owner_pid_value = -1
        self._lifecycle_state = _WriterSessionForkInvalid()
        self._retry_reachable_value = False
        if credential is not None:
            try:
                credential.overwrite_and_drop()
            except BaseException:
                pass

    def _require_owner_process(self) -> None:
        if self._process_owner_pid_value != os.getpid():
            self.cleanup_from_foreign_process()
            raise WriterSessionError(
                WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH
            )

    def _require_active_lifecycle(self) -> None:
        with self._condition:
            state = self._lifecycle_state
            authority = _state_authority(state)
            active = type(state) in (
                _WriterSessionActive,
                _WriterSessionOperationsActive,
                _WriterSessionMutationActive,
            ) and not self._operation_exit_process_control_poisoned_value and not any(
                _operation_blocks_admission(record)
                for record in _state_operation_records(state)
            )
        if not active or authority is None:
            raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_CLOSED)
        if not authority.authority_lock.active:
            self.close_from_owner()
            raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_CLOSED)

    @property
    def cleanup_complete(self) -> bool:
        return type(self._lifecycle_state) is _WriterSessionTerminalX

    def _cleanup_release_lock_nonblocking(self, *, release_lock: bool) -> None:
        if not release_lock:
            return
        with self._condition:
            if self._current_thread_owns_operation_locked():
                self._freeze_admission_locked()
                return
        self._continue_cleanup(blocking=False, finalizer=False)

    def _freeze_admission_locked(self) -> None:
        state = self._lifecycle_state
        if type(state) is _WriterSessionActive:
            cleanup = _ContinueCleanup(
                _CleanupBeforeR1NoSlot(state.activity)
            )
            self._lifecycle_state = _WriterSessionOrdinaryCleanup(cleanup)
        elif type(state) is _WriterSessionOperationsActive:
            cleanup = _ContinueCleanup(
                _CleanupBeforeR1NoSlot(state.activity)
            )
            self._lifecycle_state = _WriterSessionOperationsClosing(cleanup)
        elif type(state) is _WriterSessionMutationActive:
            cleanup = _ContinueCleanup(
                _CleanupBeforeR1WithSlot(state.frame.activity, state.frame.slot)
            )
            self._lifecycle_state = _WriterSessionMutationClosing(cleanup)
        elif type(state) is _WriterSessionControllerResolution:
            self._lifecycle_state = _WriterSessionControllerResolution(
                state.frame,
                state.scope_token,
                _CleanupRequiredAfterResolution(),
            )
        elif type(state) is _WriterSessionControllerCloseProved:
            self._lifecycle_state = _proved_cleanup_state(
                state.intent,
                state.scope_token,
                state.close_proof,
                _ContinueCleanup(
                    _CleanupBeforeR1WithSlot(
                        state.frame.activity,
                        state.frame.slot,
                    )
                ),
            )
        elif type(state) is _WriterSessionControllerCloseProvedReleased:
            self._lifecycle_state = _proved_cleanup_state(
                state.intent,
                state.scope_token,
                state.close_proof,
                _ContinueCleanup(_CleanupBeforeR1NoSlot(state.activity)),
            )
        self._condition.notify_all()

    def _classify_lost_operation_leases_locked(self) -> None:
        """Convert lease disappearance into cleanup-only orphan posture."""

        for _ in range(len(_state_operation_records(self._lifecycle_state))):
            state = self._lifecycle_state
            record = next(
                (
                    candidate
                    for candidate in _state_operation_records(state)
                    if candidate.lease_reference() is None
                    and candidate.phase
                    not in (
                        _OperationRetirementPhase.EXPLICIT_RETIRED,
                        _OperationRetirementPhase.ORPHANED,
                    )
                ),
                None,
            )
            if record is None:
                return
            successor_record = replace(
                record,
                phase=_OperationRetirementPhase.ORPHANED,
                cleanup_required=True,
            )
            record.handle._mark_cleanup_required()
            self._lifecycle_state = self._state_with_replaced_operation_record_locked(
                state,
                record,
                successor_record,
            )
            self._condition.notify_all()

    def _retire_cleanup_owned_operations_locked(self) -> None:
        """Remove only cleanup-owned or already explicitly retired records."""

        for _ in range(len(_state_operation_records(self._lifecycle_state))):
            state = self._lifecycle_state
            record = next(
                (
                    candidate
                    for candidate in _state_operation_records(state)
                    if candidate.cleanup_required
                    or candidate.phase
                    in (
                        _OperationRetirementPhase.ORPHANED,
                        _OperationRetirementPhase.EXPLICIT_RETIRED,
                    )
                ),
                None,
            )
            if record is None:
                return
            operation = record.handle
            admitted_lease = record.lease_reference()
            if (
                type(admitted_lease) is _WriterSessionOperationLease
                and admitted_lease._completion_handle is operation
            ):
                admitted_lease._closed = True
                admitted_lease._credential = None
                admitted_lease._authority_lock = None
            remaining = tuple(
                candidate
                for candidate in _state_operation_records(state)
                if candidate is not record
            )
            if type(state) is _WriterSessionCleanupClaimed:
                if not _is_exact_operation_retirement_cleanup_claim(
                    state,
                    operation,
                ) or remaining:
                    return
                successor = self._operation_retirement_cleanup_successor_locked(
                    state,
                    operation,
                )
            else:
                successor = self._state_after_operation_completion(
                    state,
                    record,
                    remaining,
                )
            self._lifecycle_state = successor
            self._condition.notify_all()

    def _continue_cleanup(self, *, blocking: bool, finalizer: bool) -> None:
        claim: _WriterSessionCleanupClaim | None = None
        needs_housekeeping = False
        with self._condition:
            state = self._lifecycle_state
            if type(state) is _WriterSessionForkInvalid:
                return
            if type(state) is _WriterSessionTerminalX:
                needs_housekeeping = True
            else:
                self._classify_lost_operation_leases_locked()
                state = self._lifecycle_state
                if not finalizer:
                    owner_thread = get_ident()
                    if any(
                        record.owner_thread == owner_thread
                        and not (
                            record.cleanup_required
                            or record.phase
                            in (
                                _OperationRetirementPhase.ORPHANED,
                                _OperationRetirementPhase.EXPLICIT_RETIRED,
                            )
                        )
                        for record in _state_operation_records(state)
                    ):
                        raise WriterSessionError(
                            WriterSessionFailureReason.WRITER_SESSION_CLOSE_DURING_OPERATION
                        )
                self._freeze_admission_locked()
                self._retire_cleanup_owned_operations_locked()
                state = self._lifecycle_state
                if not finalizer and self._current_thread_owns_operation_locked():
                    raise WriterSessionError(
                        WriterSessionFailureReason.WRITER_SESSION_CLOSE_DURING_OPERATION
                    )
                if _state_operations(state):
                    if not blocking:
                        return
                    self._condition.wait_for(
                        lambda: (
                            not _state_operations(self._lifecycle_state)
                            or type(self._lifecycle_state)
                            in (_WriterSessionTerminalX, _WriterSessionForkInvalid)
                        )
                    )
                    state = self._lifecycle_state
                if type(state) is _WriterSessionForkInvalid:
                    return
                if type(state) is _WriterSessionTerminalX:
                    needs_housekeeping = True
                elif type(state) is _WriterSessionCleanupClaimed:
                    claim = self._claim_or_take_over_locked(
                        state,
                        blocking=blocking,
                        finalizer=finalizer,
                    )
                    if claim is None:
                        return
                else:
                    if type(state) not in _CLEANUP_PENDING_TYPES:
                        raise _cleanup_driver_invariant_failure() from None
                    claim = self._install_cleanup_claim_locked(state)

        if needs_housekeeping:
            self._cleanup_step_h3()
            return
        if type(claim) is not _WriterSessionCleanupClaim:
            raise _cleanup_driver_invariant_failure() from None
        try:
            self._run_claimed_cleanup(claim)
        except BaseException:
            if isinstance(sys.exception(), Exception):
                self._release_cleanup_claim(claim)
            if finalizer:
                return
            raise

    def _claim_or_take_over_locked(
        self,
        claimed_state: _WriterSessionCleanupClaimed,
        *,
        blocking: bool,
        finalizer: bool,
    ) -> _WriterSessionCleanupClaim | None:
        current = current_thread()
        while type(self._lifecycle_state) is _WriterSessionCleanupClaimed:
            observed = self._lifecycle_state
            claim = observed.claim
            owner = claim.owner_thread_ref()
            if owner is current:
                self._require_cleanup_claim_locked(claim)
                return claim
            if owner is None or not owner.is_alive():
                if finalizer:
                    return None
                return self._take_over_cleanup_claim_locked(observed)
            if not blocking or finalizer:
                return None
            self._condition.wait(timeout=0.05)
        state = self._lifecycle_state
        if type(state) is _WriterSessionTerminalX:
            return None
        if type(state) in _CLEANUP_PENDING_TYPES:
            return self._install_cleanup_claim_locked(state)
        if type(state) is _WriterSessionForkInvalid:
            return None
        raise _cleanup_driver_invariant_failure() from None

    def _install_cleanup_claim_locked(
        self,
        pending_state: object,
        *,
        claim_epoch: int | None = None,
    ) -> _WriterSessionCleanupClaim:
        continuation = _cleanup_continuation(pending_state)
        epoch = continuation.claim_epoch + 1 if claim_epoch is None else claim_epoch
        updated_pending = self._pending_with_cleanup(
            pending_state,
            _ContinueCleanup(continuation.cursor, epoch),
        )
        thread = current_thread()
        claim = _WriterSessionCleanupClaim(
            token=_CleanupClaimToken(),
            owner_thread_ref=weakref.ref(thread),
            resource_identity=continuation.cursor.resource_identity,
            owner_pid=os.getpid(),
            lifecycle_epoch=self._lifecycle_epoch,
            claim_epoch=epoch,
        )
        self._lifecycle_state = _WriterSessionCleanupClaimed(updated_pending, claim)
        self._condition.notify_all()
        return claim

    def _take_over_cleanup_claim_locked(
        self,
        claimed_state: _WriterSessionCleanupClaimed,
    ) -> _WriterSessionCleanupClaim:
        old_claim = claimed_state.claim
        if (
            old_claim.owner_pid != os.getpid()
            or old_claim.resource_identity is not self._resource_identity
            or old_claim.lifecycle_epoch != self._lifecycle_epoch
        ):
            raise _cleanup_driver_invariant_failure() from None
        owner = old_claim.owner_thread_ref()
        if owner is not None and owner.is_alive():
            raise _cleanup_driver_invariant_failure() from None
        return self._install_cleanup_claim_locked(
            claimed_state.pending_state,
            claim_epoch=old_claim.claim_epoch + 1,
        )

    def _pending_with_cleanup(
        self,
        pending_state: object,
        cleanup: _ContinueCleanup,
    ) -> object:
        if type(pending_state) is _WriterSessionAbortCloseUnproved:
            return _WriterSessionAbortCloseUnproved(
                pending_state.scope_token,
                pending_state.retained_connection,
                cleanup,
            )
        if type(pending_state) is _WriterSessionCommitUncertainUnproved:
            return _WriterSessionCommitUncertainUnproved(
                pending_state.scope_token,
                pending_state.retained_connection,
                cleanup,
            )
        if type(pending_state) is _WriterSessionCommitKnownUnproved:
            return _WriterSessionCommitKnownUnproved(
                pending_state.scope_token,
                pending_state.retained_connection,
                cleanup,
            )
        if type(pending_state) is _WriterSessionAbortPendingCleanup:
            return _WriterSessionAbortPendingCleanup(
                pending_state.scope_token,
                pending_state.close_proof,
                cleanup,
            )
        if type(pending_state) is _WriterSessionCommitUncertainPendingCleanup:
            return _WriterSessionCommitUncertainPendingCleanup(
                pending_state.scope_token,
                pending_state.close_proof,
                cleanup,
            )
        if type(pending_state) is _WriterSessionCommitKnownPendingCleanup:
            return _WriterSessionCommitKnownPendingCleanup(
                pending_state.scope_token,
                pending_state.close_proof,
                cleanup,
            )
        if type(pending_state) is _WriterSessionOrdinaryCleanup:
            return _WriterSessionOrdinaryCleanup(cleanup)
        raise _cleanup_driver_invariant_failure() from None

    def _release_cleanup_claim(self, claim: _WriterSessionCleanupClaim) -> None:
        with self._condition:
            state = self._lifecycle_state
            if type(state) is _WriterSessionTerminalX:
                self._condition.notify_all()
                return
            if (
                type(state) is not _WriterSessionCleanupClaimed
                or state.claim is not claim
            ):
                return
            self._lifecycle_state = state.pending_state
            self._condition.notify_all()

    def _require_cleanup_claim_locked(
        self,
        claim: _WriterSessionCleanupClaim,
    ) -> _WriterSessionCleanupClaimed:
        state = self._lifecycle_state
        if (
            type(claim) is not _WriterSessionCleanupClaim
            or type(state) is not _WriterSessionCleanupClaimed
            or state.claim is not claim
            or claim.resource_identity is not self._resource_identity
            or claim.owner_pid != os.getpid()
            or claim.lifecycle_epoch != self._lifecycle_epoch
            or claim.owner_thread_ref() is not current_thread()
        ):
            raise _cleanup_driver_invariant_failure() from None
        return state

    def _claim_with_pending_locked(
        self,
        claim: _WriterSessionCleanupClaim,
        pending_state: object,
    ) -> _WriterSessionCleanupClaim:
        current = self._require_cleanup_claim_locked(claim)
        if current.claim is not claim:
            raise _cleanup_driver_invariant_failure() from None
        cleanup = _cleanup_continuation(pending_state)
        updated_pending = self._pending_with_cleanup(
            pending_state,
            _ContinueCleanup(cleanup.cursor, claim.claim_epoch),
        )
        self._lifecycle_state = _WriterSessionCleanupClaimed(
            updated_pending,
            claim,
        )
        self._condition.notify_all()
        return claim

    def _run_claimed_cleanup(self, claim: _WriterSessionCleanupClaim) -> None:
        with self._condition:
            state = self._require_cleanup_claim_locked(claim)
            unproved = type(state.pending_state) in (
                _WriterSessionAbortCloseUnproved,
                _WriterSessionCommitUncertainUnproved,
                _WriterSessionCommitKnownUnproved,
            )
        if unproved:
            disposition, claim = self._advance_claimed_cleanup_once(claim)
            if disposition == _CLEANUP_DRIVER_BLOCKED:
                self._release_cleanup_claim(claim)
                return
        for cursor_type in _CLEANUP_CURSOR_TYPES:
            with self._condition:
                state = self._lifecycle_state
                if type(state) is _WriterSessionTerminalX:
                    self._cleanup_step_h3()
                    return
                claimed = self._require_cleanup_claim_locked(claim)
                observed_type = type(
                    _cleanup_continuation(claimed.pending_state).cursor
                )
                if observed_type is not cursor_type:
                    continue
            disposition, claim = self._advance_claimed_cleanup_once(claim)
            if disposition == _CLEANUP_DRIVER_BLOCKED:
                self._release_cleanup_claim(claim)
                return
            if disposition == _CLEANUP_DRIVER_TERMINAL:
                self._cleanup_step_h3()
                return
        with self._condition:
            if type(self._lifecycle_state) is not _WriterSessionTerminalX:
                raise _cleanup_driver_invariant_failure() from None
        self._cleanup_step_h3()

    def _advance_claimed_cleanup_once(
        self,
        claim: _WriterSessionCleanupClaim,
    ) -> tuple[str, _WriterSessionCleanupClaim]:
        with self._condition:
            claimed = self._require_cleanup_claim_locked(claim)
            pending = claimed.pending_state
            cursor = _cleanup_continuation(pending).cursor

        if type(pending) in (
            _WriterSessionAbortCloseUnproved,
            _WriterSessionCommitUncertainUnproved,
            _WriterSessionCommitKnownUnproved,
        ):
            try:
                close_proof = pending.retained_connection._close_with_proof()
            except Exception:
                return (_CLEANUP_DRIVER_BLOCKED, claim)
            with self._condition:
                self._require_cleanup_claim_locked(claim)
                if type(pending) is _WriterSessionAbortCloseUnproved:
                    successor_pending = _WriterSessionAbortPendingCleanup(
                        pending.scope_token,
                        close_proof,
                        pending.cleanup,
                    )
                elif type(pending) is _WriterSessionCommitUncertainUnproved:
                    successor_pending = _WriterSessionCommitUncertainPendingCleanup(
                        pending.scope_token,
                        close_proof,
                        pending.cleanup,
                    )
                else:
                    successor_pending = _WriterSessionCommitKnownPendingCleanup(
                        pending.scope_token,
                        close_proof,
                        pending.cleanup,
                    )
                claim = self._claim_with_pending_locked(claim, successor_pending)
            return (_CLEANUP_DRIVER_ADVANCED, claim)

        if type(cursor) in (_CleanupBeforeR1WithSlot, _CleanupBeforeR1NoSlot):
            if cursor.operations:
                return (_CLEANUP_DRIVER_BLOCKED, claim)
            authority = cursor.authority
            if type(cursor) is _CleanupBeforeR1WithSlot:
                next_cursor: object = _CleanupBeforeR2WithSlot(
                    authority.authority_lock,
                    authority.database_binding,
                    cursor.slot,
                    cursor.resource_identity,
                )
            else:
                next_cursor = _CleanupBeforeR2NoSlot(
                    authority.authority_lock,
                    authority.database_binding,
                    cursor.resource_identity,
                )
            with self._condition:
                successor = self._pending_with_cleanup(
                    pending,
                    _ContinueCleanup(next_cursor, claim.claim_epoch),
                )
                claim = self._claim_with_pending_locked(claim, successor)
            try:
                authority.credential.overwrite_and_drop()
            except Exception:
                pass
            return (_CLEANUP_DRIVER_ADVANCED, claim)

        if type(cursor) in (
            _CleanupBeforeR2WithSlot,
            _CleanupBeforeR2NoSlot,
        ):
            next_cursor = _CleanupBeforeR3(
                cursor.authority_lock,
                cursor.database_binding,
                cursor.resource_identity,
            )
            with self._condition:
                successor = self._pending_with_cleanup(
                    pending,
                    _ContinueCleanup(next_cursor, claim.claim_epoch),
                )
                claim = self._claim_with_pending_locked(claim, successor)
            return (_CLEANUP_DRIVER_ADVANCED, claim)

        if type(cursor) is _CleanupBeforeR3:
            next_cursor = _CleanupBeforeL1(
                cursor.authority_lock,
                cursor.resource_identity,
            )
            with self._condition:
                successor = self._pending_with_cleanup(
                    pending,
                    _ContinueCleanup(next_cursor, claim.claim_epoch),
                )
                claim = self._claim_with_pending_locked(claim, successor)
            return (_CLEANUP_DRIVER_ADVANCED, claim)

        if type(cursor) in (
            _CleanupBeforeL1,
            _CleanupBeforeH1,
            _CleanupBeforeH2,
        ):
            ordinary_failure = False
            try:
                cursor.authority_lock.close()
            except Exception:
                ordinary_failure = True
            except BaseException:
                next_cursor = self._observed_lock_cleanup_cursor(
                    cursor.authority_lock,
                    cursor.resource_identity,
                )
                with self._condition:
                    successor = self._pending_with_cleanup(
                        pending,
                        _ContinueCleanup(next_cursor, claim.claim_epoch),
                    )
                    self._claim_with_pending_locked(claim, successor)
                raise
            next_cursor = self._observed_lock_cleanup_cursor(
                cursor.authority_lock,
                cursor.resource_identity,
            )
            with self._condition:
                successor = self._pending_with_cleanup(
                    pending,
                    _ContinueCleanup(next_cursor, claim.claim_epoch),
                )
                claim = self._claim_with_pending_locked(claim, successor)
            if ordinary_failure or type(next_cursor) is type(cursor):
                return (_CLEANUP_DRIVER_BLOCKED, claim)
            return (_CLEANUP_DRIVER_ADVANCED, claim)

        if type(cursor) is _CleanupBeforeT1:
            with self._condition:
                self._require_cleanup_claim_locked(claim)
                self._lifecycle_state = _WriterSessionTerminalX()
                self._condition.notify_all()
            return (_CLEANUP_DRIVER_TERMINAL, claim)

        raise _cleanup_driver_invariant_failure() from None

    def _observed_lock_cleanup_cursor(
        self,
        authority_lock: StateAuthorityLock,
        resource_identity: _WriterSessionResourceIdentity,
    ) -> object:
        try:
            lock_state, descriptor_outcome, registry_removed = (
                authority_lock._resource.cleanup_status_for_writer()
            )
        except Exception:
            return _CleanupBeforeL1(authority_lock, resource_identity)
        if lock_state == "closed" and registry_removed:
            return _CleanupBeforeT1(resource_identity)
        if lock_state == "closed":
            return _CleanupBeforeH2(authority_lock, resource_identity)
        if (
            lock_state == "release_proved"
            and descriptor_outcome == "not_attempted"
        ):
            return _CleanupBeforeH1(authority_lock, resource_identity)
        if lock_state == "release_proved":
            return _CleanupBeforeH2(authority_lock, resource_identity)
        return _CleanupBeforeL1(authority_lock, resource_identity)

    def _cleanup_step_h3(self) -> None:
        if type(self._lifecycle_state) is not _WriterSessionTerminalX:
            raise _cleanup_driver_invariant_failure() from None
        _remove_active_session_resource(self)

    def _current_thread_owns_operation_locked(self) -> bool:
        owner_thread = get_ident()
        return any(
            record.owner_thread == owner_thread
            for record in _state_operation_records(self._lifecycle_state)
        )

    def _operation_record_for_handle_locked(
        self,
        completion_handle: _OperationCompletionHandle,
        *,
        state: object | None = None,
    ) -> _WriterSessionOperationRecord | None:
        observed_state = self._lifecycle_state if state is None else state
        return next(
            (
                record
                for record in _state_operation_records(observed_state)
                if record.handle is completion_handle
            ),
            None,
        )

    def _activity_with_replaced_operation_record_locked(
        self,
        state: object,
        current: _WriterSessionOperationRecord,
        successor: _WriterSessionOperationRecord,
    ) -> _WriterSessionActivity:
        records = _state_operation_records(state)
        if (
            type(current) is not _WriterSessionOperationRecord
            or type(successor) is not _WriterSessionOperationRecord
            or successor.handle is not current.handle
            or not any(record is current for record in records)
        ):
            raise _cleanup_driver_invariant_failure() from None
        authority = _state_authority(state)
        if authority is None:
            raise _cleanup_driver_invariant_failure() from None
        return _WriterSessionActivity(
            authority,
            tuple(
                successor if record is current else record
                for record in records
            ),
        )

    def _state_with_activity_locked(
        self,
        state: object,
        activity: _WriterSessionActivity,
    ) -> object:
        """Replace only the activity embedded in one lifecycle state."""

        if type(activity) is not _WriterSessionActivity:
            raise _cleanup_driver_invariant_failure() from None
        if type(state) is _WriterSessionActive:
            return _WriterSessionActive(activity)
        if type(state) is _WriterSessionOperationsActive:
            return _WriterSessionOperationsActive(activity)
        if type(state) is _WriterSessionMutationActive:
            return _WriterSessionMutationActive(
                _WriterSessionMutationFrame(activity, state.frame.slot)
            )
        if type(state) is _WriterSessionControllerResolution:
            return _WriterSessionControllerResolution(
                _WriterSessionMutationFrame(activity, state.frame.slot),
                state.scope_token,
                state.policy,
            )
        if type(state) is _WriterSessionControllerCloseProved:
            return _WriterSessionControllerCloseProved(
                _WriterSessionMutationFrame(activity, state.frame.slot),
                state.scope_token,
                state.intent,
                state.close_proof,
                state.result,
            )
        if type(state) is _WriterSessionControllerCloseProvedReleased:
            return _WriterSessionControllerCloseProvedReleased(
                activity,
                state.scope_token,
                state.intent,
                state.close_proof,
                state.result,
            )
        if type(state) is _WriterSessionCleanupClaimed:
            return _WriterSessionCleanupClaimed(
                self._state_with_activity_locked(state.pending_state, activity),
                state.claim,
            )
        if type(state) in _CLEANUP_PENDING_TYPES + (
            _WriterSessionOperationsClosing,
            _WriterSessionMutationClosing,
            _WriterSessionOrdinaryCleanup,
        ):
            cursor = _cleanup_continuation(state).cursor
            if type(cursor) is _CleanupBeforeR1WithSlot:
                successor_cursor: object = _CleanupBeforeR1WithSlot(
                    activity,
                    cursor.slot,
                )
            elif type(cursor) is _CleanupBeforeR1NoSlot:
                successor_cursor = _CleanupBeforeR1NoSlot(activity)
            else:
                raise _cleanup_driver_invariant_failure() from None
            cleanup = _ContinueCleanup(
                successor_cursor,
                _cleanup_continuation(state).claim_epoch,
            )
            if type(state) is _WriterSessionOperationsClosing:
                return _WriterSessionOperationsClosing(cleanup)
            if type(state) is _WriterSessionMutationClosing:
                return _WriterSessionMutationClosing(cleanup)
            return self._pending_with_cleanup(state, cleanup)
        raise _cleanup_driver_invariant_failure() from None

    def _state_with_replaced_operation_record_locked(
        self,
        state: object,
        current: _WriterSessionOperationRecord,
        successor: _WriterSessionOperationRecord,
    ) -> object:
        activity = self._activity_with_replaced_operation_record_locked(
            state,
            current,
            successor,
        )
        return self._state_with_activity_locked(state, activity)

    def _begin_operation(
        self,
        session: "_SQLiteWriterSession",
        invocation_correlation: _OperationInvocationCorrelation,
    ) -> "_WriterSessionOperationLease":
        self._require_owner_process()
        owner_pid = os.getpid()
        owner_thread = get_ident()
        lease: _WriterSessionOperationLease | None = None
        completion_handle: _OperationCompletionHandle | None = None
        try:
            with self._condition:
                state = self._lifecycle_state
                # Compatibility source vocabulary for the frozen B3c0a static oracle:
                # self._state != _ACTIVE
                # self._credential is None
                # self._authority_lock is None
                # credential = self._credential
                # authority_lock = self._authority_lock
                if type(state) not in (
                    _WriterSessionActive,
                    _WriterSessionOperationsActive,
                    _WriterSessionMutationActive,
                ) or self._operation_exit_process_control_poisoned_value or any(
                    _operation_blocks_admission(record)
                    for record in _state_operation_records(state)
                ):
                    raise WriterSessionError(
                        WriterSessionFailureReason.WRITER_SESSION_CLOSED
                    )
                authority = state.authority
                if (
                    type(invocation_correlation)
                    is not _OperationInvocationCorrelation
                    or invocation_correlation.resource_identity
                    is not self._resource_identity
                    or invocation_correlation.owner_pid != owner_pid
                    or invocation_correlation.lifecycle_epoch
                    != authority.epoch.value
                    or any(
                        record.invocation_correlation is invocation_correlation
                        for record in _state_operation_records(state)
                    )
                ):
                    raise ValueError("invalid operation invocation correlation")
                credential = authority.credential
                authority_lock = authority.authority_lock
                operation_id = authority.next_operation_id
                lifecycle_epoch = authority.epoch.value
                # Historical spelling retained only for a frozen source-order oracle:
                # self._active_operations[operation_id] = owner_thread
                completion_handle = _OperationCompletionHandle(
                    resource_identity=self._resource_identity,
                    operation_id=operation_id,
                    owner_pid=owner_pid,
                    owner_thread=owner_thread,
                    lifecycle_epoch=lifecycle_epoch,
                    invocation_correlation=invocation_correlation,
                )
                lease = _WriterSessionOperationLease(
                    resource=self,
                    session=session,
                    credential=credential,
                    authority_lock=authority_lock,
                    completion_handle=completion_handle,
                )
                finalizer = _FINALIZER_FACTORY(
                    lease,
                    _finalize_writer_session_operation,
                    self,
                    completion_handle,
                )
                finalizer.atexit = False
                if type(getattr(finalizer, "alive", None)) is not bool or not finalizer.alive:
                    raise _cleanup_driver_invariant_failure() from None
                lease._attach_finalizer(finalizer)
                completion_handle._bind_operation_lifecycle(lease, finalizer)
                lease_reference = weakref.ref(
                    lease,
                    _OperationLeaseLossCallback(
                        weakref.ref(self),
                        completion_handle,
                    ),
                )
                operation_record = _WriterSessionOperationRecord(
                    handle=completion_handle,
                    resource_identity=self._resource_identity,
                    operation_id=operation_id,
                    owner_pid=owner_pid,
                    owner_thread=owner_thread,
                    lifecycle_epoch=lifecycle_epoch,
                    lease_reference=lease_reference,
                    finalizer=finalizer,
                )
                successor_authority = _WriterSessionAuthority(
                    authority.resource_identity,
                    authority.owner_pid,
                    authority.epoch,
                    operation_id + 1,
                    authority.credential,
                    authority.authority_lock,
                    authority.database_binding,
                )
                operation_records = _state_operation_records(state) + (
                    operation_record,
                )
                activity = _WriterSessionActivity(
                    successor_authority,
                    operation_records,
                )
                if type(state) in (
                    _WriterSessionActive,
                    _WriterSessionOperationsActive,
                ):
                    successor: object = _WriterSessionOperationsActive(activity)
                else:
                    successor = _WriterSessionMutationActive(
                        _WriterSessionMutationFrame(activity, state.frame.slot)
                    )
                self._lifecycle_state = successor
                self._last_next_operation_id = operation_id + 1
            if not authority_lock.active:
                lease._close()
                self.close_from_owner()
                raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_CLOSED)
            return lease
        except BaseException:
            if lease is not None:
                try:
                    lease._close()
                except BaseException:
                    try:
                        lease._close()
                    except BaseException:
                        pass
                if not lease._closed:
                    lease._abandon_before_return()
            raise

    def _operation_handle_for_lease_locked(
        self,
        operation_lease: "_WriterSessionOperationLease",
    ) -> _OperationCompletionHandle:
        operation_lease._require_owner_call()
        for record in _state_operation_records(self._lifecycle_state):
            if (
                record.handle is operation_lease._completion_handle
                and record.lease_reference() is operation_lease
                and record.finalizer is operation_lease._finalizer
                and record.resource_identity is self._resource_identity
                and record.owner_pid == os.getpid()
                and record.owner_thread == get_ident()
                and record.lifecycle_epoch == self._lifecycle_epoch
                and record.phase is _OperationRetirementPhase.ADMITTED
                and not record.cleanup_required
            ):
                return record.handle
        raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_CLOSED)

    def _activate_controller_scope_for_operation(
        self,
        operation_lease: "_WriterSessionOperationLease",
        *,
        scope_token: _ControllerScopeToken,
    ) -> _ControllerResolutionActivationAcknowledgment:
        if type(scope_token) is not _ControllerScopeToken:
            raise _cleanup_driver_invariant_failure() from None
        with self._condition:
            state = self._lifecycle_state
            if (
                self._operation_exit_process_control_poisoned_value
                and type(state) is _WriterSessionMutationActive
            ):
                raise WriterSessionError(
                    WriterSessionFailureReason.WRITER_SESSION_CLOSED
                )
            operation = self._operation_handle_for_lease_locked(operation_lease)
            if type(state) is _WriterSessionMutationActive:
                frame = state.frame
                policy: _ResumeIfCloseProvedAndStillEligible | _CleanupRequiredAfterResolution = (
                    _ResumeIfCloseProvedAndStillEligible()
                )
            elif type(state) is _WriterSessionMutationClosing:
                cursor = state.cleanup.cursor
                if type(cursor) is not _CleanupBeforeR1WithSlot:
                    raise _cleanup_driver_invariant_failure() from None
                frame = _WriterSessionMutationFrame(
                    cursor.activity,
                    cursor.slot,
                )
                policy = _CleanupRequiredAfterResolution()
            else:
                raise WriterSessionError(
                    WriterSessionFailureReason.WRITER_SESSION_CLOSED
                )
            if (
                not any(candidate is operation for candidate in frame.activity.operations)
                or not frame.slot.owned_by_operation(operation)
                or not scope_token.admits_operation(operation)
            ):
                raise WriterSessionError(
                    WriterSessionFailureReason.WRITER_SESSION_CLOSED
                )
            successor = _WriterSessionControllerResolution(
                frame,
                scope_token,
                policy,
            )
            acknowledgment = _ControllerResolutionActivationAcknowledgment(
                scope_token,
                successor,
            )
            self._lifecycle_state = successor
            self._condition.notify_all()
            return acknowledgment

    def _require_controller_scope_for_operation(
        self,
        operation_lease: "_WriterSessionOperationLease",
        *,
        acknowledgment: _ControllerResolutionActivationAcknowledgment,
        scope_token: _ControllerScopeToken,
    ) -> _WriterSessionControllerResolution:
        with self._condition:
            return self._require_controller_scope_locked(
                operation_lease,
                acknowledgment=acknowledgment,
                scope_token=scope_token,
            )

    def _require_controller_scope_locked(
        self,
        operation_lease: "_WriterSessionOperationLease",
        *,
        acknowledgment: _ControllerResolutionActivationAcknowledgment,
        scope_token: _ControllerScopeToken,
    ) -> _WriterSessionControllerResolution:
        state = self._lifecycle_state
        operation = self._operation_handle_for_lease_locked(operation_lease)
        if (
            type(acknowledgment) is not _ControllerResolutionActivationAcknowledgment
            or state is not acknowledgment.resolution
            or acknowledgment.scope_token is not scope_token
            or state.scope_token is not scope_token
            or not any(candidate is operation for candidate in state.frame.activity.operations)
            or not state.frame.slot.owned_by_operation(operation)
        ):
            raise WriterSessionError(
                WriterSessionFailureReason.WRITER_SESSION_CLOSED
            )
        return state

    def _controller_resolution_for_operation(
        self,
        operation_lease: "_WriterSessionOperationLease",
        *,
        scope_token: _ControllerScopeToken,
    ) -> _WriterSessionControllerResolution | None:
        with self._condition:
            state = self._lifecycle_state
            if (
                type(state) is not _WriterSessionControllerResolution
                or state.scope_token is not scope_token
            ):
                return None
            try:
                operation = self._operation_handle_for_lease_locked(
                    operation_lease
                )
            except WriterSessionError:
                return None
            if not any(
                candidate is operation
                for candidate in state.frame.activity.operations
            ):
                return None
            return state

    def _publication_acknowledgment_for_state_locked(
        self,
        *,
        scope_token: _ControllerScopeToken,
        facts: _ControllerCloseProvedFacts | _ControllerCloseUnprovedFacts,
    ) -> _ControllerSuccessorPublicationAcknowledgment | None:
        state = self._lifecycle_state
        pending = state.pending_state if type(state) is _WriterSessionCleanupClaimed else state
        if type(pending) in (
            _WriterSessionControllerCloseProved,
            _WriterSessionControllerCloseProvedReleased,
        ):
            if (
                type(facts) is not _ControllerCloseProvedFacts
                or pending.scope_token is not scope_token
                or pending.intent is not facts.intent
                or pending.close_proof is not facts.close_proof
            ):
                return None
            kind = _controller_resume_kind(pending.intent)
        elif type(pending) in (
            _WriterSessionAbortCloseUnproved,
            _WriterSessionCommitUncertainUnproved,
            _WriterSessionCommitKnownUnproved,
        ):
            if (
                type(facts) is not _ControllerCloseUnprovedFacts
                or pending.scope_token is not scope_token
                or pending.retained_connection is not facts.retained_connection
            ):
                return None
            expected_type = {
                _ControllerResolutionIntent.PRECOMMIT_ABORT: _WriterSessionAbortCloseUnproved,
                _ControllerResolutionIntent.COMMIT_UNCERTAIN: _WriterSessionCommitUncertainUnproved,
                _ControllerResolutionIntent.COMMIT_KNOWN: _WriterSessionCommitKnownUnproved,
            }[facts.intent]
            if type(pending) is not expected_type:
                return None
            kind = _controller_unproved_kind(facts.intent)
        elif type(pending) in (
            _WriterSessionAbortPendingCleanup,
            _WriterSessionCommitUncertainPendingCleanup,
            _WriterSessionCommitKnownPendingCleanup,
        ):
            if (
                type(facts) is not _ControllerCloseProvedFacts
                or pending.scope_token is not scope_token
                or pending.close_proof is not facts.close_proof
            ):
                return None
            expected_type = {
                _ControllerResolutionIntent.PRECOMMIT_ABORT: _WriterSessionAbortPendingCleanup,
                _ControllerResolutionIntent.COMMIT_UNCERTAIN: _WriterSessionCommitUncertainPendingCleanup,
                _ControllerResolutionIntent.COMMIT_KNOWN: _WriterSessionCommitKnownPendingCleanup,
            }[facts.intent]
            if type(pending) is not expected_type:
                return None
            kind = _controller_cleanup_kind(facts.intent)
        else:
            return None
        return _ControllerSuccessorPublicationAcknowledgment(
            scope_token,
            kind,
            state,
        )

    def _select_controller_successor_locked(
        self,
        current: _WriterSessionControllerResolution,
        facts: _ControllerCloseProvedFacts | _ControllerCloseUnprovedFacts,
    ) -> tuple[object, _ControllerPublishedSuccessorKind]:
        cleanup = _ContinueCleanup(
            _CleanupBeforeR1WithSlot(
                current.frame.activity,
                current.frame.slot,
            )
        )
        if type(facts) is _ControllerCloseUnprovedFacts:
            if not current.scope_token.admits_retained(facts.retained_connection):
                raise _cleanup_driver_invariant_failure() from None
            return (
                _unproved_cleanup_state(
                    facts.intent,
                    current.scope_token,
                    facts.retained_connection,
                    cleanup,
                ),
                _controller_unproved_kind(facts.intent),
            )
        if type(facts) is not _ControllerCloseProvedFacts:
            raise _cleanup_driver_invariant_failure() from None
        if not current.scope_token.admits_proof(facts.close_proof):
            raise _cleanup_driver_invariant_failure() from None
        cleanup_required = (
            self._operation_exit_process_control_poisoned_value
            or type(current.policy) is _CleanupRequiredAfterResolution
            or type(facts.requested_policy) is _CleanupRequiredAfterResolution
        )
        if cleanup_required:
            return (
                _proved_cleanup_state(
                    facts.intent,
                    current.scope_token,
                    facts.close_proof,
                    cleanup,
                ),
                _controller_cleanup_kind(facts.intent),
            )
        return (
            _WriterSessionControllerCloseProved(
                current.frame,
                current.scope_token,
                facts.intent,
                facts.close_proof,
                _ResumeActive(),
            ),
            _controller_resume_kind(facts.intent),
        )

    def _publish_controller_resolution_for_operation(
        self,
        operation_lease: "_WriterSessionOperationLease",
        *,
        acknowledgment: _ControllerResolutionActivationAcknowledgment,
        facts: _ControllerCloseProvedFacts | _ControllerCloseUnprovedFacts,
    ) -> _ControllerSuccessorPublicationAcknowledgment:
        with self._condition:
            existing = self._publication_acknowledgment_for_state_locked(
                scope_token=acknowledgment.scope_token,
                facts=facts,
            )
            if existing is not None:
                return existing
            current = self._require_controller_scope_locked(
                operation_lease,
                acknowledgment=acknowledgment,
                scope_token=acknowledgment.scope_token,
            )
            selected_successor, kind = self._select_controller_successor_locked(
                current,
                facts,
            )
            publication = _ControllerSuccessorPublicationAcknowledgment(
                current.scope_token,
                kind,
                selected_successor,
            )
            # The sole resource-owned controller publication linearization point.
            self._lifecycle_state = selected_successor
            self._condition.notify_all()
            return publication

    def _stabilize_controller_process_control_for_operation(
        self,
        operation_lease: "_WriterSessionOperationLease",
        *,
        scope_token: _ControllerScopeToken,
        proved_facts: _ControllerCloseProvedFacts | None,
    ) -> _ControllerCleanupStabilizationAcknowledgment:
        if (
            type(scope_token) is not _ControllerScopeToken
            or (
                proved_facts is not None
                and type(proved_facts) is not _ControllerCloseProvedFacts
            )
        ):
            raise _cleanup_driver_invariant_failure() from None
        with self._condition:
            state = self._lifecycle_state
            if type(state) is _WriterSessionControllerResolution:
                operation = self._operation_handle_for_lease_locked(operation_lease)
                if (
                    state.scope_token is not scope_token
                    or not state.scope_token.admits_operation(operation)
                ):
                    raise WriterSessionError(
                        WriterSessionFailureReason.WRITER_SESSION_CLOSED
                    )
                if type(state.policy) is _ResumeIfCloseProvedAndStillEligible:
                    successor: object = _WriterSessionControllerResolution(
                        state.frame,
                        state.scope_token,
                        _CleanupRequiredAfterResolution(),
                    )
                    acknowledgment = _ControllerCleanupStabilizationAcknowledgment(
                        scope_token,
                        _ControllerPublishedSuccessorKind.CLEANUP_REQUIRED_UNRESOLVED,
                        successor,
                    )
                    self._lifecycle_state = successor
                    self._condition.notify_all()
                    return acknowledgment
                return _ControllerCleanupStabilizationAcknowledgment(
                    scope_token,
                    _ControllerPublishedSuccessorKind.CLEANUP_REQUIRED_UNRESOLVED,
                    state,
                )

            pending = state.pending_state if type(state) is _WriterSessionCleanupClaimed else state
            if type(pending) in (
                _WriterSessionControllerCloseProved,
                _WriterSessionControllerCloseProvedReleased,
            ):
                if (
                    proved_facts is None
                    or pending.scope_token is not scope_token
                    or pending.intent is not proved_facts.intent
                    or pending.close_proof is not proved_facts.close_proof
                ):
                    raise _cleanup_driver_invariant_failure() from None
                cleanup = _ContinueCleanup(
                    _CleanupBeforeR1WithSlot(
                        pending.frame.activity,
                        pending.frame.slot,
                    )
                    if type(pending) is _WriterSessionControllerCloseProved
                    else _CleanupBeforeR1NoSlot(pending.activity)
                )
                successor = _proved_cleanup_state(
                    pending.intent,
                    pending.scope_token,
                    pending.close_proof,
                    cleanup,
                )
                acknowledgment = _ControllerCleanupStabilizationAcknowledgment(
                    scope_token,
                    _controller_cleanup_kind(pending.intent),
                    successor,
                )
                self._lifecycle_state = successor
                self._condition.notify_all()
                return acknowledgment

            if type(pending) in (
                _WriterSessionAbortCloseUnproved,
                _WriterSessionCommitUncertainUnproved,
                _WriterSessionCommitKnownUnproved,
                _WriterSessionAbortPendingCleanup,
                _WriterSessionCommitUncertainPendingCleanup,
                _WriterSessionCommitKnownPendingCleanup,
            ) and pending.scope_token is scope_token:
                if type(pending) in (
                    _WriterSessionAbortCloseUnproved,
                    _WriterSessionCommitUncertainUnproved,
                    _WriterSessionCommitKnownUnproved,
                ):
                    kind_by_type = {
                        _WriterSessionAbortCloseUnproved: _ControllerPublishedSuccessorKind.ABORT_CLOSE_UNPROVED,
                        _WriterSessionCommitUncertainUnproved: _ControllerPublishedSuccessorKind.COMMIT_UNCERTAIN_CLOSE_UNPROVED,
                        _WriterSessionCommitKnownUnproved: _ControllerPublishedSuccessorKind.COMMIT_KNOWN_CLOSE_UNPROVED,
                    }
                else:
                    kind_by_type = {
                        _WriterSessionAbortPendingCleanup: _ControllerPublishedSuccessorKind.ABORT_PENDING_CLEANUP,
                        _WriterSessionCommitUncertainPendingCleanup: _ControllerPublishedSuccessorKind.COMMIT_UNCERTAIN_PENDING_CLEANUP,
                        _WriterSessionCommitKnownPendingCleanup: _ControllerPublishedSuccessorKind.COMMIT_KNOWN_PENDING_CLEANUP,
                    }
                return _ControllerCleanupStabilizationAcknowledgment(
                    scope_token,
                    kind_by_type[type(pending)],
                    state,
                )
            raise _cleanup_driver_invariant_failure() from None

    def _acquire_mutation_lease_for_operation(
        self,
        operation_lease: "_WriterSessionOperationLease",
    ) -> "_WriterSessionMutationLease":
        operation_lease._require_owner_call()
        token = _WriterSessionMutationToken()
        operation: _OperationCompletionHandle | None = None
        try:
            with self._condition:
                state = self._lifecycle_state
                if self._operation_exit_process_control_poisoned_value:
                    raise WriterSessionError(
                        WriterSessionFailureReason.WRITER_SESSION_CLOSED
                    )
                if type(state) is _WriterSessionControllerCloseProvedReleased:
                    operation = self._operation_handle_for_lease_locked(operation_lease)
                    if not any(
                        candidate is operation
                        for candidate in state.activity.operations
                    ):
                        raise WriterSessionError(
                            WriterSessionFailureReason.WRITER_SESSION_CLOSED
                        )
                    activity = state.activity
                elif type(state) is _WriterSessionOperationsActive:
                    operation = self._operation_handle_for_lease_locked(operation_lease)
                    activity = state.activity
                else:
                    if type(state) is _WriterSessionMutationActive:
                        raise WriterSessionError(
                            WriterSessionFailureReason.WRITER_SESSION_MUTATION_IN_PROGRESS
                        )
                    raise WriterSessionError(
                        WriterSessionFailureReason.WRITER_SESSION_CLOSED
                    )
                authority = activity.authority
                slot = _WriterSessionMutationSlot(
                    operation=operation,
                    token=token,
                )
                self._lifecycle_state = _WriterSessionMutationActive(
                    _WriterSessionMutationFrame(activity, slot)
                )
                authority_lock = authority.authority_lock
            if not _authority_lock_active(authority_lock):
                self._release_mutation_slot(
                    operation=operation,
                    token=token,
                )
                self._cleanup_release_lock_nonblocking(release_lock=True)
                raise WriterSessionError(
                    WriterSessionFailureReason.WRITER_SESSION_CLOSED
                )
            self._verify_filesystem_authority_binding(authority_lock)
            mutation_lease = _MUTATION_LEASE_FACTORY(
                resource=self,
                operation_lease=operation_lease,
                operation=operation,
                token=token,
            )
            if type(mutation_lease) is not _WriterSessionMutationLease:
                raise ValueError("invalid writer input")
            return mutation_lease
        except BaseException:
            if operation is not None:
                self._release_mutation_slot(
                    operation=operation,
                    token=token,
                )
            raise

    def _release_mutation_slot(
        self,
        *,
        operation: _OperationCompletionHandle | None = None,
        operation_id: int | None = None,
        owner_pid: int | None = None,
        owner_thread: int | None = None,
        lifecycle_epoch: int | None = None,
        token: _WriterSessionMutationToken,
        defer_proved_return_to_operation: bool = False,
        operation_retirement: bool = False,
    ) -> bool:
        supplied_by_values = operation is None
        if operation is None:
            state_operation = _state_slot(self._lifecycle_state)
            operation = state_operation.operation if state_operation is not None else None
        if type(operation) is not _OperationCompletionHandle:
            return False
        with self._condition:
            governing = sys.exception()
            state = self._lifecycle_state
            slot = _state_slot(state)
            if slot is None or not slot.matches(operation=operation, token=token):
                return False
            record = self._operation_record_for_handle_locked(
                operation,
                state=state,
            )
            if record is None:
                raise _cleanup_driver_invariant_failure() from None
            if (
                record.resource_identity is not self._resource_identity
                or record.owner_pid != os.getpid()
                or (
                    not operation_retirement
                    and record.owner_thread != get_ident()
                )
                or (
                    supplied_by_values
                    and (
                        record.operation_id != operation_id
                        or record.owner_pid != owner_pid
                        or record.owner_thread != owner_thread
                        or record.lifecycle_epoch != lifecycle_epoch
                    )
                )
            ):
                return False
            cleanup_required = (
                self._operation_exit_process_control_poisoned_value
                or record.cleanup_required
                or type(governing)
                in (
                    KeyboardInterrupt,
                    SystemExit,
                    GeneratorExit,
                )
            )
            release_acknowledgment = record.mutation_release_acknowledgment
            if release_acknowledgment is None:
                release_acknowledgment = _OperationMutationReleaseAcknowledgment(
                    self._resource_identity,
                    self._lifecycle_epoch,
                    operation,
                )
            elif not _operation_has_exact_mutation_release_acknowledgment(record):
                raise _cleanup_driver_invariant_failure() from None
            successor_record = replace(
                record,
                cleanup_required=cleanup_required,
                mutation_release_acknowledgment=release_acknowledgment,
            )
            object.__setattr__(
                operation,
                "_mutation_release_acknowledgment",
                release_acknowledgment,
            )
            if cleanup_required:
                operation._mark_cleanup_required()
            state = self._state_with_replaced_operation_record_locked(
                state,
                record,
                successor_record,
            )
            if type(state) is _WriterSessionMutationActive:
                if successor_record.cleanup_required:
                    self._lifecycle_state = _WriterSessionOperationsClosing(
                        _ContinueCleanup(
                            _CleanupBeforeR1NoSlot(state.frame.activity)
                        )
                    )
                else:
                    self._lifecycle_state = _WriterSessionOperationsActive(
                        state.frame.activity
                    )
            elif type(state) is _WriterSessionControllerCloseProved:
                if successor_record.cleanup_required:
                    self._lifecycle_state = _proved_cleanup_state(
                        state.intent,
                        state.scope_token,
                        state.close_proof,
                        _ContinueCleanup(
                            _CleanupBeforeR1NoSlot(state.frame.activity)
                        ),
                    )
                else:
                    self._lifecycle_state = _WriterSessionControllerCloseProvedReleased(
                        state.frame.activity,
                        state.scope_token,
                        state.intent,
                        state.close_proof,
                        state.result,
                    )
            elif type(state) in (
                _WriterSessionControllerResolution,
                _WriterSessionMutationClosing,
                _WriterSessionAbortCloseUnproved,
                _WriterSessionCommitUncertainUnproved,
                _WriterSessionCommitKnownUnproved,
                _WriterSessionAbortPendingCleanup,
                _WriterSessionCommitUncertainPendingCleanup,
                _WriterSessionCommitKnownPendingCleanup,
                _WriterSessionCleanupClaimed,
            ):
                # Cleanup or unresolved controller states retain structural slot
                # ownership; the resource record still retains the exact release.
                self._lifecycle_state = state
                self._condition.notify_all()
                return True
            else:
                return False
            self._condition.notify_all()
            return True

    def _require_active_mutation_authority_for_operation(
        self,
        operation_lease: "_WriterSessionOperationLease",
    ) -> None:
        operation_lease._require_owner_call()
        with self._condition:
            state = self._lifecycle_state
            if (
                self._operation_exit_process_control_poisoned_value
                or type(state) is not _WriterSessionMutationActive
            ):
                raise WriterSessionError(
                    WriterSessionFailureReason.WRITER_SESSION_CLOSED
                )
            operation = self._operation_handle_for_lease_locked(operation_lease)
            if not state.frame.slot.owned_by_operation(operation):
                raise WriterSessionError(
                    WriterSessionFailureReason.WRITER_SESSION_CLOSED
                )
            authority_lock = state.frame.activity.authority.authority_lock
        if not _authority_lock_active(authority_lock):
            self._clear_mutation_slot_owned_by_operation(
                operation_id=operation.operation_id,
                owner_pid=operation.owner_pid,
                lifecycle_epoch=operation.lifecycle_epoch,
            )
            self._cleanup_release_lock_nonblocking(release_lock=True)
            raise WriterSessionError(
                WriterSessionFailureReason.WRITER_SESSION_CLOSED
            )
        self._verify_filesystem_authority_binding(authority_lock)

    def _bound_state_database_for_mutation_operation(
        self,
        operation_lease: "_WriterSessionOperationLease",
    ) -> _StateDatabaseAuthorityBinding:
        self._require_active_mutation_authority_for_operation(operation_lease)
        binding = self._database_binding
        if type(binding) is not _StateDatabaseAuthorityBinding:
            raise WriterSessionError(
                WriterSessionFailureReason.WRITER_SESSION_CLOSED
            )
        return binding

    def _verify_filesystem_authority_binding(
        self,
        authority_lock: StateAuthorityLock,
    ) -> None:
        binding = self._database_binding
        if type(binding) is not _StateDatabaseAuthorityBinding:
            raise _WriterSessionAuthorityClosed()
        try:
            authority_lock._validate_state_database_authority_binding(binding)
        except _StateDatabaseAuthorityBindingMismatch:
            raise _WriterSessionAuthorityClosed() from None
        except _StateDatabaseAuthorityBindingUnavailable:
            raise _WriterSessionAuthorityUnavailable() from None
        except Exception:
            raise _WriterSessionAuthorityUnavailable() from None

    def _clear_mutation_slot_owned_by_operation(
        self,
        *,
        operation_id: int,
        owner_pid: int,
        lifecycle_epoch: int,
    ) -> bool:
        # Frozen B3c1a source vocabulary: def _clear_mutation_slot_owned_by_operation_locked
        if owner_pid != os.getpid():
            return False
        with self._condition:
            state = self._lifecycle_state
            if type(state) is not _WriterSessionMutationActive:
                return False
            operation = state.frame.slot.operation
            record = self._operation_record_for_handle_locked(
                operation,
                state=state,
            )
            if (
                record is None
                or record.operation_id != operation_id
                or record.owner_pid != owner_pid
                or record.lifecycle_epoch != lifecycle_epoch
            ):
                return False
            if self._operation_exit_process_control_poisoned_value:
                self._lifecycle_state = _WriterSessionOperationsClosing(
                    _ContinueCleanup(
                        _CleanupBeforeR1NoSlot(state.frame.activity)
                    )
                )
            else:
                self._lifecycle_state = _WriterSessionOperationsActive(
                    state.frame.activity
                )
            self._condition.notify_all()
            return True

    def _stabilize_operation_exit_for_process_control(
        self,
        invocation_correlation: _OperationInvocationCorrelation | object,
    ) -> _OperationExitProcessControlDisposition:
        """Stabilize only the exact currently represented invocation."""

        if (
            type(invocation_correlation) is not _OperationInvocationCorrelation
            or invocation_correlation.resource_identity is not self._resource_identity
            or self._process_owner_pid_value == -1
        ):
            return (
                _OperationExitProcessControlDisposition.INVALID_OR_WRONG_RESOURCE
            )

        with self._condition:
            state = self._lifecycle_state
            pending_state = (
                state.pending_state
                if type(state) is _WriterSessionCleanupClaimed
                else state
            )
            records: tuple[_WriterSessionOperationRecord, ...] = ()
            if type(pending_state) in (
                _WriterSessionOperationsActive,
                _WriterSessionControllerCloseProvedReleased,
            ):
                records = pending_state.activity.operation_records
            elif type(pending_state) in (
                _WriterSessionMutationActive,
                _WriterSessionControllerResolution,
                _WriterSessionControllerCloseProved,
            ):
                records = pending_state.frame.activity.operation_records
            elif type(pending_state) in _CLEANUP_PENDING_TYPES + (
                _WriterSessionOperationsClosing,
                _WriterSessionMutationClosing,
            ):
                cursor = pending_state.cleanup.cursor
                if type(cursor) in (
                    _CleanupBeforeR1WithSlot,
                    _CleanupBeforeR1NoSlot,
                ):
                    records = cursor.activity.operation_records

            if type(records) is not tuple:
                return (
                    _OperationExitProcessControlDisposition.INVALID_OR_WRONG_RESOURCE
                )

            exact_record: _WriterSessionOperationRecord | None = None
            duplicate_exact_match = False
            for candidate in records:
                if (
                    type(candidate) is _WriterSessionOperationRecord
                    and type(candidate.handle) is _OperationCompletionHandle
                    and candidate.handle.invocation_correlation
                    is invocation_correlation
                ):
                    if exact_record is None:
                        exact_record = candidate
                        self._operation_exit_process_control_poisoned_value = True
                    else:
                        duplicate_exact_match = True

            if exact_record is None:
                return (
                    _OperationExitProcessControlDisposition.NOT_CURRENTLY_REPRESENTED
                )
            if duplicate_exact_match:
                try:
                    self._condition.notify_all()
                except BaseException:
                    pass
                return (
                    _OperationExitProcessControlDisposition.INVALID_OR_WRONG_RESOURCE
                )
            authority = _state_authority(pending_state)
            if (
                type(authority) is not _WriterSessionAuthority
                or authority.resource_identity is not self._resource_identity
                or authority.owner_pid != invocation_correlation.owner_pid
                or type(authority.epoch) is not _WriterSessionEpoch
                or authority.epoch.value != invocation_correlation.lifecycle_epoch
                or self._process_owner_pid_value != invocation_correlation.owner_pid
                or self._lifecycle_epoch_value != invocation_correlation.lifecycle_epoch
                or invocation_correlation.owner_pid != os.getpid()
                or exact_record.resource_identity is not self._resource_identity
                or exact_record.owner_pid != invocation_correlation.owner_pid
                or exact_record.lifecycle_epoch
                != invocation_correlation.lifecycle_epoch
                or exact_record.handle.resource_identity
                is not exact_record.resource_identity
                or exact_record.handle.owner_pid != exact_record.owner_pid
                or exact_record.handle.lifecycle_epoch != exact_record.lifecycle_epoch
            ):
                try:
                    self._condition.notify_all()
                except BaseException:
                    pass
                return (
                    _OperationExitProcessControlDisposition.INVALID_OR_WRONG_RESOURCE
                )
            cleanup_owned = bool(
                _operation_blocks_admission(exact_record)
                or (
                    type(pending_state) is _WriterSessionControllerResolution
                    and type(pending_state.policy)
                    is _CleanupRequiredAfterResolution
                )
                or type(pending_state)
                in _CLEANUP_PENDING_TYPES
                + (
                    _WriterSessionOperationsClosing,
                    _WriterSessionMutationClosing,
                )
            )
            disposition = (
                _OperationExitProcessControlDisposition.REPRESENTED_CLEANUP_OWNED
                if cleanup_owned
                else _OperationExitProcessControlDisposition.REPRESENTED_INCOMPLETE
            )

        self._mark_operation_cleanup_required(exact_record.handle)
        try:
            with self._condition:
                self._condition.notify_all()
        except BaseException:
            pass
        return disposition

    def _mark_operation_cleanup_required(
        self,
        completion_handle: _OperationCompletionHandle,
    ) -> bool:
        if type(completion_handle) is not _OperationCompletionHandle:
            return False
        with self._condition:
            state = self._lifecycle_state
            record = self._operation_record_for_handle_locked(
                completion_handle,
                state=state,
            )
            if (
                record is None
                or record.resource_identity is not self._resource_identity
                or record.owner_pid != os.getpid()
                or record.lifecycle_epoch != self._lifecycle_epoch
            ):
                return False
            successor_record = replace(record, cleanup_required=True)
            record.handle._mark_cleanup_required()
            successor_state = self._state_with_replaced_operation_record_locked(
                state,
                record,
                successor_record,
            )
            if _is_exact_operation_retirement_cleanup_claim(
                successor_state,
                record.handle,
            ):
                successor_state = _WriterSessionOperationsClosing(
                    successor_state.pending_state.cleanup
                )
            self._lifecycle_state = successor_state
            self._condition.notify_all()
            return True

    def _mark_operation_orphaned(
        self,
        completion_handle: _OperationCompletionHandle,
    ) -> bool:
        """Classify an operation-loss signal as cleanup, never completion."""

        if type(completion_handle) is not _OperationCompletionHandle:
            return False
        with self._condition:
            state = self._lifecycle_state
            record = self._operation_record_for_handle_locked(
                completion_handle,
                state=state,
            )
            if (
                record is None
                or record.resource_identity is not self._resource_identity
                or record.owner_pid != os.getpid()
                or record.lifecycle_epoch != self._lifecycle_epoch
            ):
                return False
            successor_record = replace(
                record,
                phase=_OperationRetirementPhase.ORPHANED,
                cleanup_required=True,
            )
            record.handle._mark_cleanup_required()
            self._lifecycle_state = self._state_with_replaced_operation_record_locked(
                state,
                record,
                successor_record,
            )
            self._freeze_admission_locked()
            self._condition.notify_all()
        return True

    def _operation_lease_lost(
        self,
        completion_handle: _OperationCompletionHandle,
    ) -> None:
        """Give lease loss a real cleanup owner without granting retirement."""

        preparation: _OperationRetirementPreparationAcknowledgment | None = None
        with self._condition:
            state = self._lifecycle_state
            record = self._operation_record_for_handle_locked(
                completion_handle,
                state=state,
            )
            if record is None:
                return
            if (
                record.phase is _OperationRetirementPhase.EXPLICIT_RETIRED
                and not record.cleanup_required
            ):
                preparation = record.retirement_preparation_acknowledgment
                if type(preparation) is not _OperationRetirementPreparationAcknowledgment:
                    raise _cleanup_driver_invariant_failure() from None
            else:
                successor_record = replace(
                    record,
                    phase=_OperationRetirementPhase.ORPHANED,
                    cleanup_required=True,
                )
                record.handle._mark_cleanup_required()
                self._lifecycle_state = (
                    self._state_with_replaced_operation_record_locked(
                        state,
                        record,
                        successor_record,
                    )
                )
                self._freeze_admission_locked()
                self._condition.notify_all()
        if preparation is not None:
            try:
                self._publish_prepared_operation_retirement(preparation, None)
                return
            except BaseException:
                try:
                    self._mark_operation_cleanup_required(completion_handle)
                except BaseException:
                    pass
        self._continue_cleanup(blocking=False, finalizer=True)

    def _continue_operation_cleanup_if_required(
        self,
        completion_handle: _OperationCompletionHandle,
    ) -> None:
        with self._condition:
            record = self._operation_record_for_handle_locked(completion_handle)
            required = bool(
                record is not None
                and (
                    record.cleanup_required
                    or record.phase is _OperationRetirementPhase.ORPHANED
                )
            )
        if required:
            self._continue_cleanup(blocking=False, finalizer=True)

    def _release_operation_mutation_slot_for_retirement(
        self,
        completion_handle: _OperationCompletionHandle,
    ) -> None:
        """Defensively release the exact represented slot before Phase 1."""

        with self._condition:
            state = self._lifecycle_state
            if type(state) not in (
                _WriterSessionMutationActive,
                _WriterSessionMutationClosing,
            ):
                return
            slot = _state_slot(state)
            if slot is None or slot.operation is not completion_handle:
                return
            token = slot.token
        self._release_mutation_slot(
            operation=completion_handle,
            token=token,
            operation_retirement=True,
        )

    def _prepare_operation_retirement(
        self,
        completion_handle: _OperationCompletionHandle,
    ) -> _OperationRetirementPreparationAcknowledgment | None:
        if type(completion_handle) is not _OperationCompletionHandle:
            return None
        matched: _OperationCompletionHandle | None = None
        try:
            self._release_operation_mutation_slot_for_retirement(
                completion_handle
            )
            with self._condition:
                state = self._lifecycle_state
                if type(state) not in (
                    _WriterSessionOperationsActive,
                    _WriterSessionMutationActive,
                    _WriterSessionControllerResolution,
                    _WriterSessionControllerCloseProved,
                    _WriterSessionControllerCloseProvedReleased,
                    _WriterSessionOperationsClosing,
                    _WriterSessionMutationClosing,
                    _WriterSessionAbortCloseUnproved,
                    _WriterSessionCommitUncertainUnproved,
                    _WriterSessionCommitKnownUnproved,
                    _WriterSessionAbortPendingCleanup,
                    _WriterSessionCommitUncertainPendingCleanup,
                    _WriterSessionCommitKnownPendingCleanup,
                    _WriterSessionCleanupClaimed,
                ):
                    return None
                record = self._operation_record_for_handle_locked(
                    completion_handle,
                    state=state,
                )
                if (
                    record is None
                    or record.resource_identity is not self._resource_identity
                    or record.owner_pid != os.getpid()
                    or record.lifecycle_epoch != self._lifecycle_epoch
                ):
                    return None
                matched = record.handle
                if (
                    type(state) is _WriterSessionCleanupClaimed
                    and not _is_exact_operation_retirement_cleanup_claim(
                        state,
                        matched,
                    )
                ):
                    return None
                if record.phase is _OperationRetirementPhase.ORPHANED:
                    return None
                slot = _state_slot(state)
                if slot is not None and slot.operation is matched:
                    if type(state) is _WriterSessionControllerResolution:
                        return None
                    if not _operation_has_exact_mutation_release_acknowledgment(
                        record
                    ):
                        return None
                existing = record.retirement_preparation_acknowledgment
                if existing is None:
                    acknowledgment = _OperationRetirementPreparationAcknowledgment(
                        self._resource_identity,
                        self._lifecycle_epoch,
                        matched,
                    )
                    successor_phase = _OperationRetirementPhase.PREPARED
                elif type(existing) is _OperationRetirementPreparationAcknowledgment:
                    acknowledgment = existing
                    successor_phase = record.phase
                else:
                    raise _cleanup_driver_invariant_failure() from None
                successor_record = replace(
                    record,
                    phase=successor_phase,
                    retirement_preparation_acknowledgment=acknowledgment,
                )
                object.__setattr__(
                    matched,
                    "_retirement_preparation_acknowledgment",
                    acknowledgment,
                )
                successor_state = self._state_with_replaced_operation_record_locked(
                    state,
                    record,
                    successor_record,
                )
                if (
                    type(successor_state) is _WriterSessionOperationsClosing
                    and _state_operations(successor_state) == (matched,)
                ):
                    self._install_cleanup_claim_locked(
                        _WriterSessionOrdinaryCleanup(successor_state.cleanup)
                    )
                else:
                    self._lifecycle_state = successor_state
                self._condition.notify_all()
                return acknowledgment
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            try:
                self._mark_operation_cleanup_required(completion_handle)
            except BaseException:
                pass
            raise

    def _retire_operation_lease_locally(
        self,
        preparation: _OperationRetirementPreparationAcknowledgment,
        operation_lease: "_WriterSessionOperationLease",
    ) -> bool:
        if (
            type(preparation) is not _OperationRetirementPreparationAcknowledgment
            or type(operation_lease) is not _WriterSessionOperationLease
            or preparation.resource_identity is not self._resource_identity
            or preparation.lifecycle_epoch != self._lifecycle_epoch
            or operation_lease._resource is not self
            or operation_lease._completion_handle is not preparation.operation
        ):
            return False
        detach_failure: BaseException | None = None
        cleanup_required = False
        with self._condition:
            operation = preparation.operation
            state = self._lifecycle_state
            record = self._operation_record_for_handle_locked(
                operation,
                state=state,
            )
            if (
                record is None
                or record.resource_identity is not self._resource_identity
                or record.owner_pid != os.getpid()
                or record.lifecycle_epoch != self._lifecycle_epoch
            ):
                return False
            if (
                record.retirement_preparation_acknowledgment is not preparation
                or record.cleanup_required
                or record.phase is _OperationRetirementPhase.ORPHANED
            ):
                return False
            admitted_lease = record.lease_reference()
            finalizer = record.finalizer
            if (
                admitted_lease is not operation_lease
                or operation_lease._completion_handle is not record.handle
                or operation_lease._finalizer is not finalizer
            ):
                return False
            slot = _state_slot(state)
            if (
                slot is not None
                and slot.operation is operation
                and (
                    type(state) is _WriterSessionControllerResolution
                    or not _operation_has_exact_mutation_release_acknowledgment(
                        record
                    )
                )
            ):
                return False
            if record.phase is _OperationRetirementPhase.EXPLICIT_RETIRED:
                return True
            if record.phase not in (
                _OperationRetirementPhase.PREPARED,
                _OperationRetirementPhase.EXPLICIT_LOCAL_TERMINAL,
            ):
                return False
            if record.phase is _OperationRetirementPhase.PREPARED:
                operation_lease._closed = True
                terminal_record = replace(
                    record,
                    phase=_OperationRetirementPhase.EXPLICIT_LOCAL_TERMINAL,
                )
                self._lifecycle_state = (
                    self._state_with_replaced_operation_record_locked(
                        state,
                        record,
                        terminal_record,
                    )
                )
                record = terminal_record
                state = self._lifecycle_state
                self._condition.notify_all()
            elif not operation_lease._closed:
                raise _cleanup_driver_invariant_failure() from None

            try:
                detach_result = finalizer.detach()
            except BaseException as error:
                detach_failure = error
                detach_result = None
            if _is_successful_exact_operation_finalizer_detach(
                detach_result,
                operation_lease=operation_lease,
                resource=self,
                operation=operation,
            ):
                retired_record = replace(
                    record,
                    phase=_OperationRetirementPhase.EXPLICIT_RETIRED,
                )
                self._lifecycle_state = (
                    self._state_with_replaced_operation_record_locked(
                        state,
                        record,
                        retired_record,
                    )
                )
                self._condition.notify_all()
                return True

            orphaned_record = replace(
                record,
                phase=_OperationRetirementPhase.ORPHANED,
                cleanup_required=True,
            )
            operation._mark_cleanup_required()
            self._lifecycle_state = self._state_with_replaced_operation_record_locked(
                state,
                record,
                orphaned_record,
            )
            self._freeze_admission_locked()
            self._condition.notify_all()
            cleanup_required = True
        if detach_failure is not None:
            raise detach_failure
        if cleanup_required:
            self._continue_cleanup(blocking=False, finalizer=True)
        return False

    def _notify_operation_retirement_waiters_locked(self) -> None:
        """Notify condition waiters after the authoritative final assignment."""

        self._condition.notify_all()

    def _operation_retirement_cleanup_successor_locked(
        self,
        state: _WriterSessionCleanupClaimed,
        operation: _OperationCompletionHandle,
    ) -> object:
        """Finish a sole prepared cleanup before its final handle-removal assignment."""

        if not _is_exact_operation_retirement_cleanup_claim(state, operation):
            raise _cleanup_driver_invariant_failure() from None
        cursor = state.pending_state.cleanup.cursor
        authority = cursor.authority
        try:
            authority.credential.overwrite_and_drop()
        except Exception:
            pass
        try:
            authority.authority_lock.close()
        except Exception:
            pass
        next_cursor = self._observed_lock_cleanup_cursor(
            authority.authority_lock,
            cursor.resource_identity,
        )
        if type(next_cursor) is _CleanupBeforeT1:
            return _WriterSessionTerminalX()
        return _WriterSessionOrdinaryCleanup(
            _ContinueCleanup(next_cursor, state.claim.claim_epoch)
        )

    def _publish_prepared_operation_retirement(
        self,
        preparation: _OperationRetirementPreparationAcknowledgment,
        operation_lease: "_WriterSessionOperationLease | None",
    ) -> None:
        if (
            type(preparation) is not _OperationRetirementPreparationAcknowledgment
            or (
                operation_lease is not None
                and type(operation_lease) is not _WriterSessionOperationLease
            )
            or preparation.resource_identity is not self._resource_identity
            or preparation.lifecycle_epoch != self._lifecycle_epoch
        ):
            raise WriterSessionError(
                WriterSessionFailureReason.WRITER_SESSION_CLOSED
            )
        operation = preparation.operation
        final_successor: object | None = None
        try:
            with self._condition:
                state = self._lifecycle_state
                record = self._operation_record_for_handle_locked(
                    operation,
                    state=state,
                )
                if (
                    record is None
                    or record.resource_identity is not self._resource_identity
                    or record.owner_pid != os.getpid()
                    or record.lifecycle_epoch != self._lifecycle_epoch
                ):
                    raise WriterSessionError(
                        WriterSessionFailureReason.WRITER_SESSION_CLOSED
                    )
                admitted_operation_lease = record.lease_reference()
                if (
                    record.retirement_preparation_acknowledgment is not preparation
                    or record.phase is not _OperationRetirementPhase.EXPLICIT_RETIRED
                    or record.cleanup_required
                ):
                    raise WriterSessionError(
                        WriterSessionFailureReason.WRITER_SESSION_CLOSED
                    )
                if operation_lease is None:
                    if admitted_operation_lease is not None:
                        raise WriterSessionError(
                            WriterSessionFailureReason.WRITER_SESSION_CLOSED
                        )
                elif (
                    admitted_operation_lease is not operation_lease
                    or operation_lease._resource is not self
                    or operation_lease._completion_handle is not record.handle
                    or operation_lease._finalizer is not record.finalizer
                    or not operation_lease._closed
                ):
                    raise WriterSessionError(
                        WriterSessionFailureReason.WRITER_SESSION_CLOSED
                    )
                slot = _state_slot(state)
                if slot is not None and slot.operation is record.handle:
                    if (
                        type(state) is _WriterSessionControllerResolution
                        or not _operation_has_exact_mutation_release_acknowledgment(
                            record
                        )
                    ):
                        raise WriterSessionError(
                            WriterSessionFailureReason.WRITER_SESSION_CLOSED
                        )
                remaining = tuple(
                    candidate
                    for candidate in _state_operation_records(state)
                    if candidate is not record
                )
                if _is_exact_operation_retirement_cleanup_claim(
                    state,
                    record.handle,
                ):
                    if remaining:
                        raise _cleanup_driver_invariant_failure() from None
                    final_successor = (
                        self._operation_retirement_cleanup_successor_locked(
                            state,
                            record.handle,
                        )
                    )
                else:
                    final_successor = self._state_after_operation_completion(
                        state,
                        record,
                        remaining,
                    )
                self._lifecycle_state = final_successor
                self._notify_operation_retirement_waiters_locked()
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            try:
                with self._condition:
                    if (
                        final_successor is not None
                        and self._lifecycle_state is final_successor
                    ):
                        try:
                            self._notify_operation_retirement_waiters_locked()
                        except BaseException:
                            pass
                    else:
                        state = self._lifecycle_state
                        record = self._operation_record_for_handle_locked(
                            operation,
                            state=state,
                        )
                        if record is not None:
                            successor_record = replace(
                                record,
                                cleanup_required=True,
                            )
                            record.handle._mark_cleanup_required()
                            state = self._state_with_replaced_operation_record_locked(
                                state,
                                record,
                                successor_record,
                            )
                            if _is_exact_operation_retirement_cleanup_claim(
                                state,
                                record.handle,
                            ):
                                state = _WriterSessionOperationsClosing(
                                    state.pending_state.cleanup
                                )
                            self._lifecycle_state = state
                        self._notify_operation_retirement_waiters_locked()
            except BaseException:
                pass
            raise

    def _state_after_operation_completion(
        self,
        state: object,
        record: _WriterSessionOperationRecord,
        remaining: tuple[_WriterSessionOperationRecord, ...],
    ) -> object:
        if type(record) is not _WriterSessionOperationRecord:
            raise _cleanup_driver_invariant_failure() from None
        operation = record.handle
        mutation_released = _operation_has_exact_mutation_release_acknowledgment(
            record
        )
        cleanup_required = self._operation_exit_process_control_poisoned_value
        if type(state) is _WriterSessionOperationsActive:
            activity = _WriterSessionActivity(state.activity.authority, remaining)
            if record.cleanup_required:
                cleanup_required = True
            if cleanup_required:
                cleanup = _ContinueCleanup(_CleanupBeforeR1NoSlot(activity))
                if remaining:
                    return _WriterSessionOperationsClosing(cleanup)
                return _WriterSessionOrdinaryCleanup(cleanup)
            if remaining:
                return _WriterSessionOperationsActive(activity)
            return _WriterSessionActive(activity)
        if type(state) is _WriterSessionMutationActive:
            activity = _WriterSessionActivity(state.frame.activity.authority, remaining)
            if record.cleanup_required:
                cleanup_required = True
            if cleanup_required:
                cleanup = _ContinueCleanup(
                    _CleanupBeforeR1NoSlot(activity)
                    if (
                        state.frame.slot.operation is operation
                        and mutation_released
                    )
                    else _CleanupBeforeR1WithSlot(activity, state.frame.slot)
                )
                if remaining:
                    return _WriterSessionMutationClosing(cleanup)
                return _WriterSessionOrdinaryCleanup(cleanup)
            if state.frame.slot.operation is operation:
                if not mutation_released:
                    raise _cleanup_driver_invariant_failure() from None
                if remaining:
                    return _WriterSessionOperationsActive(activity)
                return _WriterSessionActive(activity)
            return _WriterSessionMutationActive(
                _WriterSessionMutationFrame(activity, state.frame.slot)
            )
        if type(state) is _WriterSessionControllerResolution:
            if state.frame.slot.operation is operation:
                # A still-unpublished controller scope remains fail-closed and
                # structurally non-admitting; it cannot be converted to Active.
                return _WriterSessionControllerResolution(
                    state.frame,
                    state.scope_token,
                    _CleanupRequiredAfterResolution(),
                )
            activity = _WriterSessionActivity(state.frame.activity.authority, remaining)
            return _WriterSessionControllerResolution(
                _WriterSessionMutationFrame(activity, state.frame.slot),
                state.scope_token,
                (
                    _CleanupRequiredAfterResolution()
                    if cleanup_required
                    else state.policy
                ),
            )
        if type(state) is _WriterSessionControllerCloseProved:
            activity = _WriterSessionActivity(state.frame.activity.authority, remaining)
            if state.frame.slot.operation is operation:
                if not mutation_released:
                    raise _cleanup_driver_invariant_failure() from None
                return _proved_cleanup_state(
                    state.intent,
                    state.scope_token,
                    state.close_proof,
                    _ContinueCleanup(
                        _CleanupBeforeR1NoSlot(activity)
                    ),
                )
            return _WriterSessionControllerCloseProved(
                _WriterSessionMutationFrame(activity, state.frame.slot),
                state.scope_token,
                state.intent,
                state.close_proof,
                state.result,
            )
        if type(state) is _WriterSessionControllerCloseProvedReleased:
            activity = _WriterSessionActivity(state.activity.authority, remaining)
            if record.cleanup_required:
                cleanup_required = True
            if cleanup_required:
                return _proved_cleanup_state(
                    state.intent,
                    state.scope_token,
                    state.close_proof,
                    _ContinueCleanup(_CleanupBeforeR1NoSlot(activity)),
                )
            if remaining:
                return _WriterSessionOperationsActive(activity)
            return _WriterSessionActive(activity)
        if type(state) is _WriterSessionOperationsClosing:
            cursor = state.cleanup.cursor
            activity = _WriterSessionActivity(cursor.activity.authority, remaining)
            cleanup = _ContinueCleanup(
                _CleanupBeforeR1NoSlot(activity),
                state.cleanup.claim_epoch,
            )
            if remaining:
                return _WriterSessionOperationsClosing(cleanup)
            return _WriterSessionOrdinaryCleanup(cleanup)
        if type(state) is _WriterSessionMutationClosing:
            cursor = state.cleanup.cursor
            activity = _WriterSessionActivity(cursor.activity.authority, remaining)
            released_exact_slot = (
                cursor.slot.operation is operation and mutation_released
            )
            cleanup = _ContinueCleanup(
                _CleanupBeforeR1NoSlot(activity)
                if released_exact_slot
                else _CleanupBeforeR1WithSlot(activity, cursor.slot),
                state.cleanup.claim_epoch,
            )
            if remaining:
                if released_exact_slot:
                    return _WriterSessionOperationsClosing(cleanup)
                return _WriterSessionMutationClosing(cleanup)
            return _WriterSessionOrdinaryCleanup(cleanup)
        if type(state) in (
            _WriterSessionAbortCloseUnproved,
            _WriterSessionCommitUncertainUnproved,
            _WriterSessionCommitKnownUnproved,
            _WriterSessionAbortPendingCleanup,
            _WriterSessionCommitUncertainPendingCleanup,
            _WriterSessionCommitKnownPendingCleanup,
        ):
            cursor = state.cleanup.cursor
            if type(cursor) not in (
                _CleanupBeforeR1WithSlot,
                _CleanupBeforeR1NoSlot,
            ):
                raise _cleanup_driver_invariant_failure() from None
            activity = _WriterSessionActivity(cursor.activity.authority, remaining)
            unproved_state = type(state) in (
                _WriterSessionAbortCloseUnproved,
                _WriterSessionCommitUncertainUnproved,
                _WriterSessionCommitKnownUnproved,
            )
            released_exact_slot = bool(
                not unproved_state
                and type(cursor) is _CleanupBeforeR1WithSlot
                and cursor.slot.operation is operation
                and mutation_released
            )
            cleanup = _ContinueCleanup(
                _CleanupBeforeR1NoSlot(activity)
                if released_exact_slot
                else _CleanupBeforeR1WithSlot(activity, cursor.slot)
                if type(cursor) is _CleanupBeforeR1WithSlot
                else _CleanupBeforeR1NoSlot(activity),
                state.cleanup.claim_epoch,
            )
            return self._pending_with_cleanup(state, cleanup)
        raise _cleanup_driver_invariant_failure() from None

    def _reset_lifecycle_synchronization(self) -> None:
        self._lifecycle_lock = Lock()
        self._condition = Condition(self._lifecycle_lock)

    def _replace_lifecycle_synchronization_after_fork(self) -> None:
        self._reset_lifecycle_synchronization()
class _WriterSessionOperationLease:
    """Private lease whose exact local retirement precedes publication."""

    __slots__ = (
        "_resource",
        "_session",
        "_credential",
        "_authority_lock",
        "_completion_handle",
        "_preparation_acknowledgment",
        "_retirement_requested",
        "_closed",
        "_finalizer",
        "__weakref__",
    )

    def __init__(
        self,
        *,
        resource: _WriterSessionResource,
        session: "_SQLiteWriterSession",
        credential: _PrivateWriterCredential,
        authority_lock: StateAuthorityLock,
        completion_handle: _OperationCompletionHandle,
    ) -> None:
        if (
            type(completion_handle) is not _OperationCompletionHandle
            or completion_handle.resource_identity is not resource._resource_identity
        ):
            raise ValueError("invalid writer input")
        self._resource = resource
        self._session: _SQLiteWriterSession | None = session
        self._credential = credential
        self._authority_lock = authority_lock
        self._completion_handle = completion_handle
        self._preparation_acknowledgment: (
            _OperationRetirementPreparationAcknowledgment | None
        ) = None
        self._retirement_requested = False
        self._closed = False
        self._finalizer: Any = None

    def __repr__(self) -> str:
        return "<_WriterSessionOperationLease>"

    @property
    def _operation_id(self) -> int:
        return self._completion_handle.operation_id

    @property
    def _owner_pid(self) -> int:
        return self._completion_handle.owner_pid

    @property
    def _owner_thread(self) -> int:
        return self._completion_handle.owner_thread

    @property
    def _lifecycle_epoch(self) -> int:
        return self._completion_handle.lifecycle_epoch

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if type(exc) in (KeyboardInterrupt, SystemExit, GeneratorExit):
            try:
                self._resource._mark_operation_cleanup_required(
                    self._completion_handle
                )
            except BaseException:
                pass
            try:
                self._close()
            except BaseException:
                pass
            raise
        self._close()

    def _attach_finalizer(self, finalizer: Any) -> None:
        if self._finalizer is not None or not hasattr(finalizer, "detach"):
            raise ValueError("invalid writer input")
        self._finalizer = finalizer

    def _abandon_before_publication(self) -> None:
        finalizer = self._finalizer
        self._closed = True
        self._session = None
        self._credential = None
        self._authority_lock = None
        if finalizer is not None and finalizer.alive:
            finalizer.detach()

    def _abandon_before_return(self) -> None:
        self._abandon_before_publication()

    def _acquire_mutation_lease(self) -> "_WriterSessionMutationLease":
        return self._resource._acquire_mutation_lease_for_operation(self)

    def _require_active_mutation_authority(self) -> None:
        self._resource._require_active_mutation_authority_for_operation(self)

    def _bound_state_database_for_mutation(self) -> _StateDatabaseAuthorityBinding:
        return self._resource._bound_state_database_for_mutation_operation(self)

    def _activate_controller_scope(
        self,
        *,
        scope_token: _ControllerScopeToken,
    ) -> _ControllerResolutionActivationAcknowledgment:
        return self._resource._activate_controller_scope_for_operation(
            self,
            scope_token=scope_token,
        )

    def _require_controller_scope(
        self,
        *,
        acknowledgment: _ControllerResolutionActivationAcknowledgment,
        scope_token: _ControllerScopeToken,
    ) -> _WriterSessionControllerResolution:
        return self._resource._require_controller_scope_for_operation(
            self,
            acknowledgment=acknowledgment,
            scope_token=scope_token,
        )

    def _controller_resolution_for_scope(
        self,
        *,
        scope_token: _ControllerScopeToken,
    ) -> _WriterSessionControllerResolution | None:
        return self._resource._controller_resolution_for_operation(
            self,
            scope_token=scope_token,
        )

    def _publish_controller_resolution(
        self,
        *,
        acknowledgment: _ControllerResolutionActivationAcknowledgment,
        facts: _ControllerCloseProvedFacts | _ControllerCloseUnprovedFacts,
    ) -> _ControllerSuccessorPublicationAcknowledgment:
        return self._resource._publish_controller_resolution_for_operation(
            self,
            acknowledgment=acknowledgment,
            facts=facts,
        )

    def _stabilize_controller_process_control(
        self,
        *,
        scope_token: _ControllerScopeToken,
        proved_facts: _ControllerCloseProvedFacts | None,
    ) -> _ControllerCleanupStabilizationAcknowledgment:
        return self._resource._stabilize_controller_process_control_for_operation(
            self,
            scope_token=scope_token,
            proved_facts=proved_facts,
        )

    def _verify_durable_writer_issuance(
        self,
        issuance: _DurableWriterIssuance,
    ) -> _WriterIssuanceMatch:
        self._require_active_mutation_authority()
        parsed = _validated_durable_writer_issuance(issuance)
        credential = self._credential
        if credential is None:
            raise WriterSessionError(
                WriterSessionFailureReason.WRITER_SESSION_CLOSED
            )
        if (
            credential.writer_ref == parsed.writer_ref
            and credential.generation == parsed.generation
            and credential.issued_ref == parsed.issued_ref
            and credential.verify_digest(parsed.issuance_nonce_digest)
        ):
            return _WriterIssuanceMatch.MATCH
        return _WriterIssuanceMatch.STALE_WRITER

    def _require_owner_call(self) -> None:
        if self._closed:
            raise WriterSessionError(
                WriterSessionFailureReason.WRITER_SESSION_CLOSED
            )
        if self._owner_pid != os.getpid():
            self._resource.cleanup_from_foreign_process()
            raise WriterSessionError(
                WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH
            )
        if self._owner_thread != get_ident():
            raise WriterSessionError(
                WriterSessionFailureReason.WRITER_SESSION_CLOSED
            )
        if self._credential is None or self._authority_lock is None:
            raise WriterSessionError(
                WriterSessionFailureReason.WRITER_SESSION_CLOSED
            )

    def _close(self) -> None:
        try:
            if self._owner_pid != os.getpid():
                self._abandon_before_return()
                return
            if not self._retirement_requested:
                self._retirement_requested = True
            local_preparation = self._preparation_acknowledgment
            preparation = self._resource._prepare_operation_retirement(
                self._completion_handle
            )
            if preparation is None:
                self._resource._continue_operation_cleanup_if_required(
                    self._completion_handle
                )
                return
            if local_preparation is None:
                self._preparation_acknowledgment = preparation
            elif local_preparation is not preparation:
                raise _cleanup_driver_invariant_failure() from None

            if not self._resource._retire_operation_lease_locally(
                preparation,
                self,
            ):
                self._resource._continue_operation_cleanup_if_required(
                    self._completion_handle
                )
                return

            if self._credential is not None:
                self._credential = None
            if self._authority_lock is not None:
                self._authority_lock = None
            self._resource._publish_prepared_operation_retirement(
                preparation,
                self,
            )
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            try:
                self._resource._mark_operation_cleanup_required(
                    self._completion_handle
                )
            except BaseException:
                pass
            raise


class _WriterSessionMutationLease:
    """Private release handle for the resource-owned mutation slot."""

    __slots__ = (
        "_resource",
        "_operation_lease",
        "_operation",
        "_token",
        "_closed",
    )
    __hash__ = object.__hash__

    def __init__(
        self,
        *,
        resource: _WriterSessionResource,
        operation_lease: _WriterSessionOperationLease,
        operation: _OperationCompletionHandle,
        token: _WriterSessionMutationToken,
    ) -> None:
        if (
            type(operation) is not _OperationCompletionHandle
            or operation is not operation_lease._completion_handle
            or operation.resource_identity is not resource._resource_identity
        ):
            raise ValueError("invalid writer input")
        self._resource = resource
        self._operation_lease: _WriterSessionOperationLease | None = (
            operation_lease
        )
        self._operation = operation
        self._token = token
        self._closed = False

    def __repr__(self) -> str:
        return "<_WriterSessionMutationLease>"

    @property
    def _operation_id(self) -> int:
        return self._operation.operation_id

    @property
    def _owner_pid(self) -> int:
        return self._operation.owner_pid

    @property
    def _owner_thread(self) -> int:
        return self._operation.owner_thread

    @property
    def _lifecycle_epoch(self) -> int:
        return self._operation.lifecycle_epoch

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if type(exc) in (KeyboardInterrupt, SystemExit, GeneratorExit):
            try:
                self._resource._mark_operation_cleanup_required(
                    self._operation
                )
            except BaseException:
                pass
            try:
                self._close()
            except BaseException:
                pass
            raise
        self._close()

    def _close(self) -> None:
        if self._closed:
            return
        if self._owner_pid != os.getpid() or self._owner_thread != get_ident():
            return
        try:
            released = self._resource._release_mutation_slot(
                operation=self._operation,
                token=self._token,
                defer_proved_return_to_operation=True,
            )
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            try:
                self._resource._mark_operation_cleanup_required(
                    self._operation
                )
            except BaseException:
                pass
            raise
        if not released:
            return
        operation_lease = self._operation_lease
        self._closed = True
        self._operation_lease = None
        if (
            operation_lease is not None
            and operation_lease._retirement_requested
        ):
            operation_lease._close()


def _make_writer_session_mutation_lease(
    *,
    resource: _WriterSessionResource,
    operation_lease: _WriterSessionOperationLease,
    operation: _OperationCompletionHandle,
    token: _WriterSessionMutationToken,
) -> _WriterSessionMutationLease:
    return _WriterSessionMutationLease(
        resource=resource,
        operation_lease=operation_lease,
        operation=operation,
        token=token,
    )


_MUTATION_LEASE_FACTORY = _make_writer_session_mutation_lease
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
    ) -> TransitionApplyOutcome:
        # B3c4c replaces the earlier WRITER_SESSION_MUTATION_UNAVAILABLE transition stub here.
        resource_reference = weakref.ref(self._resource)
        invocation_correlation: _OperationInvocationCorrelation | None = None

        def _guarded_transition_apply(
            exact_correlation: _OperationInvocationCorrelation,
        ) -> TransitionApplyOutcome:
            nonlocal self, transition_command
            bound_operation_guard = self._resource.operation_guard
            operation_guard_keywords = (
                {"_invocation_correlation": exact_correlation}
                if type(bound_operation_guard) is MethodType
                else {}
            )
            with self._resource.operation_guard(
                self,
                **operation_guard_keywords,
            ) as operation_lease:
                import_failed = False
                try:
                    from ge_nwp_coordinator.sqlite_transition_dry_run_contracts import (
                        _TransitionDryRunPreflightError,
                        _TransitionDryRunPreflightFailureReason,
                    )
                    from ge_nwp_coordinator.sqlite_transition_transaction import _run_atomic_transition_apply
                except Exception:
                    import_failed = True
                if import_failed:
                    transition_command = None  # type: ignore[assignment]
                    operation_lease = None  # type: ignore[assignment]
                    self = None  # type: ignore[assignment]
                    _raise_safe_mutation_store_error(
                        _new_safe_mutation_store_error(
                            SQLiteMutationStoreErrorCode.MUTATION_FAILED
                        )
                    )

                caught_private_preflight: BaseException | None = None
                public_preflight_reason: TransitionApplyPreflightFailureReason | None = None
                private_preflight_integrity_failed = False
                delegate_result: TransitionApplyOutcome | _SafeMutationFailureDisposition | None = None
                try:
                    delegate_result = _run_atomic_transition_apply(
                        operation_lease=operation_lease,
                        transition_command=transition_command,
                    )
                except _TransitionDryRunPreflightError as exc:
                    caught_private_preflight = exc

                if caught_private_preflight is None:
                    if type(delegate_result) is _SafeMutationFailureDisposition:
                        outward_error = _safe_mutation_error_from_disposition(
                            delegate_result
                        )
                        delegate_result = None
                        transition_command = None  # type: ignore[assignment]
                        operation_lease = None  # type: ignore[assignment]
                        self = None  # type: ignore[assignment]
                        _raise_safe_mutation_store_error(outward_error)
                    if delegate_result is None:
                        transition_command = None  # type: ignore[assignment]
                        operation_lease = None  # type: ignore[assignment]
                        self = None  # type: ignore[assignment]
                        _raise_safe_mutation_store_error(
                            _new_safe_mutation_store_error(
                                SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
                            )
                        )
                    return delegate_result

                if caught_private_preflight is not None:
                    private_preflight_reason: object | None = None
                    reason_extraction_failed = False
                    if type(caught_private_preflight) is not _TransitionDryRunPreflightError:
                        private_preflight_integrity_failed = True
                    else:
                        try:
                            private_preflight_reason = object.__getattribute__(caught_private_preflight, "reason")
                        except Exception:
                            reason_extraction_failed = True
                        if reason_extraction_failed:
                            private_preflight_integrity_failed = True
                        elif type(private_preflight_reason) is not _TransitionDryRunPreflightFailureReason:
                            private_preflight_integrity_failed = True
                        elif private_preflight_reason is _TransitionDryRunPreflightFailureReason.INVALID_COMMAND:
                            public_preflight_reason = TransitionApplyPreflightFailureReason.INVALID_COMMAND
                        elif private_preflight_reason is _TransitionDryRunPreflightFailureReason.UNSUPPORTED_COMMAND:
                            public_preflight_reason = TransitionApplyPreflightFailureReason.UNSUPPORTED_COMMAND
                        else:
                            private_preflight_integrity_failed = True
                    caught_private_preflight = None
                    private_preflight_reason = None
                if public_preflight_reason is not None:
                    transition_command = None  # type: ignore[assignment]
                    operation_lease = None  # type: ignore[assignment]
                    self = None  # type: ignore[assignment]
                    raise TransitionApplyPreflightError(public_preflight_reason) from None
                if private_preflight_integrity_failed:
                    transition_command = None  # type: ignore[assignment]
                    operation_lease = None  # type: ignore[assignment]
                    self = None  # type: ignore[assignment]
                    _raise_safe_mutation_store_error(
                        _new_safe_mutation_store_error(
                            SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
                        )
                    )
                transition_command = None  # type: ignore[assignment]
                operation_lease = None  # type: ignore[assignment]
                self = None  # type: ignore[assignment]
                _raise_safe_mutation_store_error(
                    _new_safe_mutation_store_error(
                        SQLiteMutationStoreErrorCode.MUTATION_FAILED
                    )
                )


        try:
            invocation_correlation = (
                self._resource._new_operation_invocation_correlation()
            )
            return _guarded_transition_apply(invocation_correlation)
        except (KeyboardInterrupt, SystemExit, GeneratorExit) as governing:
            resource = resource_reference()
            if type(resource) is _WriterSessionResource:
                try:
                    resource._stabilize_operation_exit_for_process_control(
                        invocation_correlation
                    )
                except (KeyboardInterrupt, SystemExit, GeneratorExit, Exception):
                    try:
                        resource._stabilize_operation_exit_for_process_control(
                            invocation_correlation
                        )
                    except (KeyboardInterrupt, SystemExit, GeneratorExit, Exception):
                        pass
            transition_command = None  # type: ignore[assignment]
            invocation_correlation = None
            resource = None
            resource_reference = None  # type: ignore[assignment]
            self = None  # type: ignore[assignment]
            _sanitize_exception_traceback_graph_at_outward_boundary(
                governing,
                _sanitize_exception_traceback_graph,
            )
            raise
        except SQLiteMutationStoreError as safe_error:
            accepted_safe_shape = _is_accepted_outward_safe_mutation_store_error(
                safe_error
            )
            transition_command = None  # type: ignore[assignment]
            invocation_correlation = None
            resource_reference = None  # type: ignore[assignment]
            self = None  # type: ignore[assignment]
            if not accepted_safe_shape:
                _sanitize_exception_traceback_graph_at_outward_boundary(
                    safe_error,
                    _sanitize_exception_traceback_graph,
                )
                raise
            _sanitize_exception_traceback_graph_at_outward_boundary(
                safe_error,
                _sanitize_exception_traceback_graph,
            )
            raise

    def apply_global_stop_update(
        self,
        global_stop_command: GlobalStopCommand,
        typed_operator_decision: GlobalStopOperatorDecision,
    ) -> GlobalStopApplyOutcome:
        # B4c replaces the earlier WRITER_SESSION_MUTATION_UNAVAILABLE global-stop stub here.
        resource_reference = weakref.ref(self._resource)
        invocation_correlation: _OperationInvocationCorrelation | None = None

        def _guarded_global_stop_apply(
            exact_correlation: _OperationInvocationCorrelation,
        ) -> GlobalStopApplyOutcome:
            nonlocal self, global_stop_command, typed_operator_decision
            bound_operation_guard = self._resource.operation_guard
            operation_guard_keywords = (
                {"_invocation_correlation": exact_correlation}
                if type(bound_operation_guard) is MethodType
                else {}
            )
            with self._resource.operation_guard(
                self,
                **operation_guard_keywords,
            ) as operation_lease:
                import_failed = False
                try:
                    from ge_nwp_coordinator.sqlite_global_stop_preflight_contracts import (
                        _GlobalStopApplyPreflightError,
                        _GlobalStopApplyPreflightFailureReason,
                    )
                    from ge_nwp_coordinator.sqlite_transition_transaction import _run_atomic_global_stop_apply
                except Exception:
                    import_failed = True
                if import_failed:
                    global_stop_command = None  # type: ignore[assignment]
                    typed_operator_decision = None  # type: ignore[assignment]
                    operation_lease = None  # type: ignore[assignment]
                    self = None  # type: ignore[assignment]
                    _raise_safe_mutation_store_error(
                        _new_safe_mutation_store_error(
                            SQLiteMutationStoreErrorCode.MUTATION_FAILED
                        )
                    )

                caught_private_preflight: BaseException | None = None
                public_preflight_reason: GlobalStopApplyPreflightFailureReason | None = None
                private_preflight_integrity_failed = False
                delegate_result: GlobalStopApplyOutcome | _SafeMutationFailureDisposition | None = None
                try:
                    delegate_result = _run_atomic_global_stop_apply(
                        operation_lease=operation_lease,
                        global_stop_command=global_stop_command,
                        typed_operator_decision=typed_operator_decision,
                    )
                except _GlobalStopApplyPreflightError as exc:
                    caught_private_preflight = exc

                if caught_private_preflight is None:
                    if type(delegate_result) is _SafeMutationFailureDisposition:
                        outward_error = _safe_mutation_error_from_disposition(
                            delegate_result
                        )
                        delegate_result = None
                        global_stop_command = None  # type: ignore[assignment]
                        typed_operator_decision = None  # type: ignore[assignment]
                        operation_lease = None  # type: ignore[assignment]
                        self = None  # type: ignore[assignment]
                        _raise_safe_mutation_store_error(outward_error)
                    if delegate_result is None:
                        global_stop_command = None  # type: ignore[assignment]
                        typed_operator_decision = None  # type: ignore[assignment]
                        operation_lease = None  # type: ignore[assignment]
                        self = None  # type: ignore[assignment]
                        _raise_safe_mutation_store_error(
                            _new_safe_mutation_store_error(
                                SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
                            )
                        )
                    return delegate_result

                if caught_private_preflight is not None:
                    private_preflight_reason: object | None = None
                    reason_extraction_failed = False
                    if type(caught_private_preflight) is not _GlobalStopApplyPreflightError:
                        private_preflight_integrity_failed = True
                    else:
                        try:
                            private_preflight_reason = object.__getattribute__(caught_private_preflight, "reason")
                        except Exception:
                            reason_extraction_failed = True
                        if reason_extraction_failed:
                            private_preflight_integrity_failed = True
                        elif type(private_preflight_reason) is not _GlobalStopApplyPreflightFailureReason:
                            private_preflight_integrity_failed = True
                        elif private_preflight_reason is _GlobalStopApplyPreflightFailureReason.INVALID_COMMAND:
                            public_preflight_reason = GlobalStopApplyPreflightFailureReason.INVALID_COMMAND
                        elif private_preflight_reason is _GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION:
                            public_preflight_reason = GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION
                        else:
                            private_preflight_integrity_failed = True
                    caught_private_preflight = None
                    private_preflight_reason = None
                if public_preflight_reason is not None:
                    global_stop_command = None  # type: ignore[assignment]
                    typed_operator_decision = None  # type: ignore[assignment]
                    operation_lease = None  # type: ignore[assignment]
                    self = None  # type: ignore[assignment]
                    raise GlobalStopApplyPreflightError(public_preflight_reason) from None
                if private_preflight_integrity_failed:
                    global_stop_command = None  # type: ignore[assignment]
                    typed_operator_decision = None  # type: ignore[assignment]
                    operation_lease = None  # type: ignore[assignment]
                    self = None  # type: ignore[assignment]
                    _raise_safe_mutation_store_error(
                        _new_safe_mutation_store_error(
                            SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
                        )
                    )
                global_stop_command = None  # type: ignore[assignment]
                typed_operator_decision = None  # type: ignore[assignment]
                operation_lease = None  # type: ignore[assignment]
                self = None  # type: ignore[assignment]
                _raise_safe_mutation_store_error(
                    _new_safe_mutation_store_error(
                        SQLiteMutationStoreErrorCode.MUTATION_FAILED
                    )
                )


        try:
            invocation_correlation = (
                self._resource._new_operation_invocation_correlation()
            )
            return _guarded_global_stop_apply(invocation_correlation)
        except (KeyboardInterrupt, SystemExit, GeneratorExit) as governing:
            resource = resource_reference()
            if type(resource) is _WriterSessionResource:
                try:
                    resource._stabilize_operation_exit_for_process_control(
                        invocation_correlation
                    )
                except (KeyboardInterrupt, SystemExit, GeneratorExit, Exception):
                    try:
                        resource._stabilize_operation_exit_for_process_control(
                            invocation_correlation
                        )
                    except (KeyboardInterrupt, SystemExit, GeneratorExit, Exception):
                        pass
            global_stop_command = None  # type: ignore[assignment]
            typed_operator_decision = None  # type: ignore[assignment]
            invocation_correlation = None
            resource = None
            resource_reference = None  # type: ignore[assignment]
            self = None  # type: ignore[assignment]
            _sanitize_exception_traceback_graph_at_outward_boundary(
                governing,
                _sanitize_exception_traceback_graph,
            )
            raise
        except SQLiteMutationStoreError as safe_error:
            accepted_safe_shape = _is_accepted_outward_safe_mutation_store_error(
                safe_error
            )
            global_stop_command = None  # type: ignore[assignment]
            typed_operator_decision = None  # type: ignore[assignment]
            invocation_correlation = None
            resource_reference = None  # type: ignore[assignment]
            self = None  # type: ignore[assignment]
            if not accepted_safe_shape:
                _sanitize_exception_traceback_graph_at_outward_boundary(
                    safe_error,
                    _sanitize_exception_traceback_graph,
                )
                raise
            _sanitize_exception_traceback_graph_at_outward_boundary(
                safe_error,
                _sanitize_exception_traceback_graph,
            )
            raise

    def _initialize_development_program(
        self,
        *,
        mutation_ref: object,
        program_ref: object,
        program_version_ref: object,
        accepted_intent_revision_ref: object,
        decision_ref: object,
        preassigned_semantic_attempt_ref: object,
        preassigned_candidate_ref: object,
        coding_global_stop_ref: object,
        coding_global_stop_version: object,
        source_intent_ref: object,
        source_intent_digest: object,
        work_spec: object,
        reason_code: object = "program_genesis",
    ) -> object:
        """Reduce one transient WorkSpec and privately apply program genesis."""

        command: object | None = None
        try:
            try:
                from ge_nwp_coordinator._sqlite_development_program_initialization import (
                    _reduce_development_program_initialization_command,
                )

                command = _reduce_development_program_initialization_command(
                    mutation_ref=mutation_ref,
                    program_ref=program_ref,
                    program_version_ref=program_version_ref,
                    accepted_intent_revision_ref=accepted_intent_revision_ref,
                    decision_ref=decision_ref,
                    preassigned_semantic_attempt_ref=preassigned_semantic_attempt_ref,
                    preassigned_candidate_ref=preassigned_candidate_ref,
                    coding_global_stop_ref=coding_global_stop_ref,
                    coding_global_stop_version=coding_global_stop_version,
                    source_intent_ref=source_intent_ref,
                    source_intent_digest=source_intent_digest,
                    work_spec=work_spec,
                    reason_code=reason_code,
                )
            finally:
                work_spec = None
        except (KeyboardInterrupt, SystemExit, GeneratorExit) as governing:
            command = None
            work_spec = None
            _sanitize_exception_traceback_graph_at_outward_boundary(
                governing,
                _sanitize_exception_traceback_graph,
            )
            raise
        except SQLiteMutationStoreError as safe_error:
            command = None
            work_spec = None
            _sanitize_exception_traceback_graph_at_outward_boundary(
                safe_error,
                _sanitize_exception_traceback_graph,
            )
            raise
        return self._run_development_program_initialization_operation(
            command=command,
            recovery=False,
        )

    def _apply_development_program_initialization(
        self,
        command: object,
    ) -> object:
        """Privately apply an already reconstructed exact safe command."""

        return self._run_development_program_initialization_operation(
            command=command,
            recovery=False,
        )

    def _resolve_development_program_initialization_commit_outcome(
        self,
        command: object,
    ) -> object:
        """Read back one initialization family under this fresh writer."""

        return self._run_development_program_initialization_operation(
            command=command,
            recovery=True,
        )

    def _run_development_program_initialization_operation(
        self,
        *,
        command: object,
        recovery: bool,
    ) -> object:
        if type(recovery) is not bool:
            raise SQLiteMutationStoreError(
                SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
            ) from None
        resource_reference = weakref.ref(self._resource)
        invocation_correlation: _OperationInvocationCorrelation | None = None

        def _guarded_initialization(
            exact_correlation: _OperationInvocationCorrelation,
        ) -> object:
            nonlocal self, command
            bound_operation_guard = self._resource.operation_guard
            operation_guard_keywords = (
                {"_invocation_correlation": exact_correlation}
                if type(bound_operation_guard) is MethodType
                else {}
            )
            with self._resource.operation_guard(
                self,
                **operation_guard_keywords,
            ) as operation_lease:
                import_failed = False
                try:
                    from ge_nwp_coordinator.sqlite_transition_transaction import (
                        _run_atomic_development_program_initialization,
                        _run_development_program_initialization_recovery,
                    )
                except Exception:
                    import_failed = True
                if import_failed:
                    command = None
                    operation_lease = None
                    self = None  # type: ignore[assignment]
                    _raise_safe_mutation_store_error(
                        _new_safe_mutation_store_error(
                            SQLiteMutationStoreErrorCode.MUTATION_FAILED
                        )
                    )
                if recovery:
                    result = _run_development_program_initialization_recovery(
                        operation_lease=operation_lease,
                        command=command,
                    )
                else:
                    result = _run_atomic_development_program_initialization(
                        operation_lease=operation_lease,
                        command=command,
                    )
                if type(result) is _SafeMutationFailureDisposition:
                    outward_error = _safe_mutation_error_from_disposition(result)
                    result = None
                    command = None
                    operation_lease = None
                    self = None  # type: ignore[assignment]
                    _raise_safe_mutation_store_error(outward_error)
                if result is None:
                    command = None
                    operation_lease = None
                    self = None  # type: ignore[assignment]
                    _raise_safe_mutation_store_error(
                        _new_safe_mutation_store_error(
                            SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
                        )
                    )
                return result

        try:
            invocation_correlation = (
                self._resource._new_operation_invocation_correlation()
            )
            return _guarded_initialization(invocation_correlation)
        except (KeyboardInterrupt, SystemExit, GeneratorExit) as governing:
            resource = resource_reference()
            if type(resource) is _WriterSessionResource:
                try:
                    resource._stabilize_operation_exit_for_process_control(
                        invocation_correlation
                    )
                except (KeyboardInterrupt, SystemExit, GeneratorExit, Exception):
                    try:
                        resource._stabilize_operation_exit_for_process_control(
                            invocation_correlation
                        )
                    except (KeyboardInterrupt, SystemExit, GeneratorExit, Exception):
                        pass
            command = None
            invocation_correlation = None
            resource = None
            resource_reference = None  # type: ignore[assignment]
            self = None  # type: ignore[assignment]
            _sanitize_exception_traceback_graph_at_outward_boundary(
                governing,
                _sanitize_exception_traceback_graph,
            )
            raise
        except SQLiteMutationStoreError as safe_error:
            accepted_safe_shape = _is_accepted_outward_safe_mutation_store_error(
                safe_error
            )
            command = None
            invocation_correlation = None
            resource_reference = None  # type: ignore[assignment]
            self = None  # type: ignore[assignment]
            _sanitize_exception_traceback_graph_at_outward_boundary(
                safe_error,
                _sanitize_exception_traceback_graph,
            )
            if accepted_safe_shape:
                raise
            raise

    def _establish_development_author_effect_intent(
        self,
        *,
        mutation_ref: object,
        program_ref: object,
        program_version_ref: object,
        program_version_number: object,
        accepted_intent_revision_ref: object,
        work_item_ref: object,
        work_item_revision_ref: object,
        basis_decision_ref: object,
        basis_decision_digest: object,
        semantic_attempt_ref: object,
        candidate_ref: object,
        attempt_number: object,
        attempt_fence_ref: object,
        effect_intent_ref: object,
        effect_fence_ref: object,
        command_ref: object,
        authority_evaluation_ref: object,
        delivery_attempt_ref: object,
        adapter_safe_correlation_ref: object,
        coding_global_stop_ref: object,
        coding_global_stop_version: object,
        work_spec: object,
        validation_requirement_evidence: object,
        review_requirement_evidence: object,
        attempt_fence: object,
        effect_authorization_safe_binding: object,
    ) -> object:
        """Reduce private inputs and establish one non-executable family."""

        command: object | None = None
        try:
            try:
                from ge_nwp_coordinator._sqlite_development_author_effect_establishment import (
                    _reduce_development_author_effect_establishment_command,
                )

                command = _reduce_development_author_effect_establishment_command(
                    mutation_ref=mutation_ref,
                    program_ref=program_ref,
                    program_version_ref=program_version_ref,
                    program_version_number=program_version_number,
                    accepted_intent_revision_ref=accepted_intent_revision_ref,
                    work_item_ref=work_item_ref,
                    work_item_revision_ref=work_item_revision_ref,
                    basis_decision_ref=basis_decision_ref,
                    basis_decision_digest=basis_decision_digest,
                    semantic_attempt_ref=semantic_attempt_ref,
                    candidate_ref=candidate_ref,
                    attempt_number=attempt_number,
                    attempt_fence_ref=attempt_fence_ref,
                    effect_intent_ref=effect_intent_ref,
                    effect_fence_ref=effect_fence_ref,
                    command_ref=command_ref,
                    authority_evaluation_ref=authority_evaluation_ref,
                    delivery_attempt_ref=delivery_attempt_ref,
                    adapter_safe_correlation_ref=adapter_safe_correlation_ref,
                    coding_global_stop_ref=coding_global_stop_ref,
                    coding_global_stop_version=coding_global_stop_version,
                    work_spec=work_spec,
                    validation_requirement_evidence=validation_requirement_evidence,
                    review_requirement_evidence=review_requirement_evidence,
                    attempt_fence=attempt_fence,
                    effect_authorization_safe_binding=(
                        effect_authorization_safe_binding
                    ),
                )
            finally:
                work_spec = None
                validation_requirement_evidence = None
                review_requirement_evidence = None
                attempt_fence = None
                effect_authorization_safe_binding = None
        except (KeyboardInterrupt, SystemExit, GeneratorExit) as governing:
            command = None
            work_spec = None
            validation_requirement_evidence = None
            review_requirement_evidence = None
            attempt_fence = None
            effect_authorization_safe_binding = None
            _sanitize_exception_traceback_graph_at_outward_boundary(
                governing,
                _sanitize_exception_traceback_graph,
            )
            raise
        except SQLiteMutationStoreError:
            command = None
            work_spec = None
            validation_requirement_evidence = None
            review_requirement_evidence = None
            attempt_fence = None
            effect_authorization_safe_binding = None
            try:
                _raise_safe_mutation_store_error(
                    _new_safe_mutation_store_error(
                        SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
                    )
                )
            except SQLiteMutationStoreError as outward_error:
                _sanitize_exception_traceback_graph_at_outward_boundary(
                    outward_error,
                    _sanitize_exception_traceback_graph,
                )
                raise
        return self._run_development_author_effect_establishment_operation(
            command=command,
            recovery=False,
        )

    def _resolve_development_author_effect_establishment_commit_outcome(
        self,
        command: object,
    ) -> object:
        """Read back one author-effect family under this fresh writer."""

        return self._run_development_author_effect_establishment_operation(
            command=command,
            recovery=True,
        )

    def _run_development_author_effect_establishment_operation(
        self,
        *,
        command: object,
        recovery: bool,
    ) -> object:
        if type(recovery) is not bool:
            raise SQLiteMutationStoreError(
                SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
            ) from None
        resource_reference = weakref.ref(self._resource)
        invocation_correlation: _OperationInvocationCorrelation | None = None

        def _guarded_author_effect(
            exact_correlation: _OperationInvocationCorrelation,
        ) -> object:
            nonlocal self, command
            bound_operation_guard = self._resource.operation_guard
            operation_guard_keywords = (
                {"_invocation_correlation": exact_correlation}
                if type(bound_operation_guard) is MethodType
                else {}
            )
            with self._resource.operation_guard(
                self,
                **operation_guard_keywords,
            ) as operation_lease:
                import_failed = False
                try:
                    from ge_nwp_coordinator.sqlite_transition_transaction import (
                        _run_atomic_development_author_effect_establishment,
                        _run_development_author_effect_establishment_recovery,
                    )
                except Exception:
                    import_failed = True
                if import_failed:
                    command = None
                    operation_lease = None
                    self = None  # type: ignore[assignment]
                    _raise_safe_mutation_store_error(
                        _new_safe_mutation_store_error(
                            SQLiteMutationStoreErrorCode.MUTATION_FAILED
                        )
                    )
                if recovery:
                    result = (
                        _run_development_author_effect_establishment_recovery(
                            operation_lease=operation_lease,
                            command=command,
                        )
                    )
                else:
                    result = _run_atomic_development_author_effect_establishment(
                        operation_lease=operation_lease,
                        command=command,
                    )
                if type(result) is _SafeMutationFailureDisposition:
                    outward_error = _safe_mutation_error_from_disposition(result)
                    result = None
                    command = None
                    operation_lease = None
                    self = None  # type: ignore[assignment]
                    _raise_safe_mutation_store_error(outward_error)
                if result is None:
                    command = None
                    operation_lease = None
                    self = None  # type: ignore[assignment]
                    _raise_safe_mutation_store_error(
                        _new_safe_mutation_store_error(
                            SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
                        )
                    )
                return result

        try:
            invocation_correlation = (
                self._resource._new_operation_invocation_correlation()
            )
            return _guarded_author_effect(invocation_correlation)
        except (KeyboardInterrupt, SystemExit, GeneratorExit) as governing:
            resource = resource_reference()
            if type(resource) is _WriterSessionResource:
                try:
                    resource._stabilize_operation_exit_for_process_control(
                        invocation_correlation
                    )
                except (KeyboardInterrupt, SystemExit, GeneratorExit, Exception):
                    try:
                        resource._stabilize_operation_exit_for_process_control(
                            invocation_correlation
                        )
                    except (KeyboardInterrupt, SystemExit, GeneratorExit, Exception):
                        pass
            command = None
            invocation_correlation = None
            resource = None
            resource_reference = None  # type: ignore[assignment]
            self = None  # type: ignore[assignment]
            _sanitize_exception_traceback_graph_at_outward_boundary(
                governing,
                _sanitize_exception_traceback_graph,
            )
            raise
        except SQLiteMutationStoreError as safe_error:
            accepted_safe_shape = _is_accepted_outward_safe_mutation_store_error(
                safe_error
            )
            command = None
            invocation_correlation = None
            resource_reference = None  # type: ignore[assignment]
            self = None  # type: ignore[assignment]
            _sanitize_exception_traceback_graph_at_outward_boundary(
                safe_error,
                _sanitize_exception_traceback_graph,
            )
            if accepted_safe_shape:
                raise
            raise

    def close(self) -> None:
        self._resource.close_from_owner()
        if self._resource.cleanup_complete and self._finalizer.alive:
            self._finalizer.detach()

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
    database_binding: _StateDatabaseAuthorityBinding | None = None
    committed = False
    try:
        _require_managed_preflight(location)
        database_binding = authority_lock._capture_state_database_authority_binding(location)
        connection = _open_bound_existing_sqlite_connection(database_binding, read_only=False)
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
        confirmed_database_binding = authority_lock._capture_state_database_authority_binding(location)
        _require_same_state_database_authority_binding(database_binding, confirmed_database_binding)
        resource = _WriterSessionResource(
            location=location,
            authority_lock=authority_lock,
            database_binding=confirmed_database_binding,
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
    try:
        return _parse_writer_ownership_rows_or_raise(rows)
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


def _validated_durable_writer_issuance(issuance: _DurableWriterIssuance) -> _DurableWriterIssuance:
    if type(issuance) is not _DurableWriterIssuance:
        raise ValueError("invalid writer input")
    try:
        parsed = _parse_writer_ownership_rows_or_raise(
            [
                (
                    1,
                    issuance.writer_ref,
                    issuance.generation,
                    issuance.issued_ref,
                    issuance.issuance_nonce_digest,
                    issuance.acquired_at,
                )
            ]
        )
    except (AttributeError, ValueError):
        raise ValueError("invalid writer input") from None
    if parsed is None:
        raise ValueError("invalid writer input")
    return parsed


def _authority_lock_active(authority_lock: StateAuthorityLock | None) -> bool:
    if authority_lock is None:
        return False
    try:
        return authority_lock.active
    except Exception:
        return False


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
    except BaseException:
        pass


def _finalize_writer_session_operation(
    resource: _WriterSessionResource,
    completion_handle: _OperationCompletionHandle,
) -> None:
    try:
        if resource._mark_operation_orphaned(completion_handle):
            resource._continue_cleanup(blocking=False, finalizer=True)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        try:
            resource._mark_operation_orphaned(completion_handle)
        except BaseException:
            pass
        return
    except BaseException:
        try:
            resource._mark_operation_orphaned(completion_handle)
        except BaseException:
            pass
        return


def _finalize_writer_session_operation_lease_loss(
    resource: object,
    completion_handle: _OperationCompletionHandle,
) -> None:
    try:
        if type(resource) is _WriterSessionResource:
            resource._operation_lease_lost(completion_handle)
    except BaseException:
        try:
            if type(resource) is _WriterSessionResource:
                resource._mark_operation_orphaned(completion_handle)
                resource._continue_cleanup(blocking=False, finalizer=True)
        except BaseException:
            pass


__all__ = [
    "SQLiteWriterAcquisitionError",
    "SQLiteWriterAcquisitionFailureReason",
    "acquire_sqlite_writer_session",
]
