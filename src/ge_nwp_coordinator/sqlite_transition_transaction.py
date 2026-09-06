"""Private Coordinator mutation transaction controller for fenced mutations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
import sqlite3
from threading import get_ident
from typing import Any

from ge_nwp_coordinator.global_stop import (
    GlobalStopCommand,
    GlobalStopEvaluation,
    GlobalStopEvaluationKind,
    GlobalStopEvent,
    GlobalStopOperatorDecision,
    GlobalStopState,
    evaluate_global_stop_update,
)
from ge_nwp_coordinator.lease import derive_lease_runtime_decision
from ge_nwp_coordinator.persistence_contracts import (
    AdmittedBacklogRecordEnvelope,
    AuthorizationReceiptEnvelope,
    DependencyReceiptEnvelope,
    GlobalStopCurrentRecordEnvelope,
    GlobalStopOperatorDecisionReceiptEnvelope,
    LeaseIdentityRecordEnvelope,
    WorkItemRecordEnvelope,
    match_global_stop_event_idempotency,
    match_transition_event_idempotency,
    next_global_stop_event_sequence,
    next_transition_event_sequence,
    normalize_transaction_timestamp,
)
from ge_nwp_coordinator.sqlite_connection import (
    _RetainedSQLiteConnection,
    _SQLiteConnectionCloseProof,
    _make_retained_sqlite_connection,
    _open_bound_existing_sqlite_connection,
)
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError,
    SQLiteMutationStoreErrorCode,
    SQLiteStateError,
)
from ge_nwp_coordinator.sqlite_migration import (
    _is_operational_validation_error,
    _validate_current_managed_connection,
)
from ge_nwp_coordinator.sqlite_security import (
    _StateDatabaseAuthorityBinding,
    _StateDatabaseAuthorityBindingMismatch,
    _StateDatabaseAuthorityBindingUnavailable,
    _validate_state_database_authority_binding,
)
from ge_nwp_coordinator.sqlite_global_stop_preflight_contracts import (
    _bind_global_stop_operator_decision_receipt,
    _validate_global_stop_apply_preflight,
)
from ge_nwp_coordinator.sqlite_global_stop_readers import (
    _read_global_stop_event_for_idempotency,
    _read_global_stop_event_max_sequence,
    _read_global_stop_operator_decision_receipt,
)
from ge_nwp_coordinator.sqlite_global_stop_write_contracts import (
    _ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SPEC,
    _GLOBAL_STOP_EVENT_INSERT_SPEC,
    _AcceptedGlobalStopCurrentCasValues,
    _GlobalStopEventInsertValues,
    _GlobalStopWritePlan,
    _global_stop_write_plan,
)
from ge_nwp_coordinator.sqlite_mutation_transaction_contracts import (
    _MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS,
    _MutationCommitResolutionState,
)
from ge_nwp_coordinator.sqlite_transition_dry_run_contracts import (
    _bind_b3c3_transition_authority,
    _BoundTransitionAuthority,
    _RollbackOnlyTransitionDryRunResult,
    _RollbackOnlyTransitionDryRunResultKind,
    _require_initialized_transition_evaluation,
    _require_initialized_work_item_record,
    _validate_transition_dry_run_preflight,
)
from ge_nwp_coordinator.sqlite_transition_event_readers import (
    _read_transition_event_for_idempotency,
    _read_transition_event_max_sequence,
)
from ge_nwp_coordinator.sqlite_transition_read_scope import (
    _read_admitted_backlog,
    _read_authorization_receipt,
    _read_current_work_item,
    _read_dependency_receipt,
    _read_global_stop_current,
    _read_lease_identity_record,
)
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _MutationReadCapabilityError,
    _MutationReadCapabilityFailureReason,
)
from ge_nwp_coordinator.sqlite_writer_session import (
    _CleanupRequiredAfterResolution,
    _ControllerCloseProvedFacts,
    _ControllerCloseUnprovedFacts,
    _ControllerResolutionActivationAcknowledgment,
    _ControllerResolutionIntent,
    _ControllerScopeToken,
    _ControllerSuccessorPublicationAcknowledgment,
    _ResumeIfCloseProvedAndStillEligible,
    _SafeMutationFailureDisposition,
    _require_safe_mutation_store_error_payload,
    _WriterIssuanceMatch,
    _WriterSessionControllerResolution,
    _WriterSessionOperationLease,
    _WriterSessionAuthorityClosed,
    _WriterSessionAuthorityUnavailable,
)
from ge_nwp_coordinator.sqlite_writer_state import (
    _DurableWriterIssuance,
    _parse_writer_ownership_rows,
)
from ge_nwp_coordinator.sqlite_transition_write_contracts import (
    _ACCEPTED_WORK_ITEM_CAS_SPEC,
    _TRANSITION_EVENT_INSERT_SPEC,
    _AcceptedWorkItemCasValues,
    _TransitionEventInsertValues,
    _TransitionWritePlan,
    _transition_write_plan,
)
from ge_nwp_coordinator.state_machine import (
    DependencyDecision,
    TransitionCommand,
    TransitionContext,
    TransitionEvaluation,
    TransitionEvaluationKind,
    TransitionEvent,
    WorkItemRecord,
    WorkItemState,
    evaluate_transition,
)
from ge_nwp_coordinator.state_store import (
    CommittedGlobalStopUpdate,
    CommittedTransition,
    GlobalStopApplyOutcome,
    GlobalStopConflict,
    TransitionApplyOutcome,
    TransitionConflict,
    WriterSessionError,
)

_CONTROLLER_CONSTRUCTION_KEY = object()
_CAPABILITY_CONSTRUCTION_KEY = object()
_SQLITE_COMMIT_FAILED = object()
_SQLITE_COMMIT_NOT_RETURNED = object()

_CONTROLLER_NEW = "NEW"
_CONTROLLER_TRANSACTION_ACTIVE = "TRANSACTION_ACTIVE"
_CONTROLLER_FENCED = "FENCED"
_CONTROLLER_CAPABILITY_ACTIVE = "CAPABILITY_ACTIVE"
_CONTROLLER_RESOLVING = "RESOLVING"
_CONTROLLER_CLOSED = "CLOSED"
_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED = "COMMIT_UNCERTAIN_QUARANTINED"
_CONTROLLER_COMMIT_SUCCEEDED_QUARANTINED = "COMMIT_SUCCEEDED_QUARANTINED"
_CONTROLLER_COMMIT_UNCERTAIN_CONNECTION_CLOSED_CLEANUP_PENDING = (
    "COMMIT_UNCERTAIN_CONNECTION_CLOSED_CLEANUP_PENDING"
)
_CONTROLLER_COMMIT_SUCCEEDED_CONNECTION_CLOSED_CLEANUP_PENDING = (
    "COMMIT_SUCCEEDED_CONNECTION_CLOSED_CLEANUP_PENDING"
)


class _ControllerConnectionScope:
    """Controller-exclusive connection custody validated by one resource token."""

    __slots__ = (
        "_activation_acknowledgment",
        "_close_proved",
        "_operation_lease",
        "_owner_pid",
        "_owner_thread",
        "_proved_facts",
        "_publication_acknowledgment",
        "_resolved",
        "_retained_connection",
        "_scope_token",
    )
    __hash__ = object.__hash__

    def __init__(
        self,
        *,
        operation_lease: _WriterSessionOperationLease,
        connection: sqlite3.Connection,
    ) -> None:
        if (
            type(operation_lease) is not _WriterSessionOperationLease
            or not isinstance(connection, sqlite3.Connection)
        ):
            raise _mutation_failed()
        self._operation_lease = operation_lease
        self._close_proved: bool | None = None
        self._retained_connection: _RetainedSQLiteConnection | None = (
            _make_retained_sqlite_connection(
                connection,
                operation_lease._completion_handle.resource_identity,
            )
        )
        self._scope_token = _ControllerScopeToken(
            self._retained_connection,
            operation_lease._completion_handle,
        )
        self._activation_acknowledgment: _ControllerResolutionActivationAcknowledgment | None = None
        self._owner_pid = os.getpid()
        self._owner_thread = get_ident()
        self._proved_facts: _ControllerCloseProvedFacts | None = None
        self._publication_acknowledgment: _ControllerSuccessorPublicationAcknowledgment | None = None
        self._resolved = False

    def __repr__(self) -> str:
        return "<_ControllerConnectionScope>"

    def __reduce__(self) -> object:
        raise TypeError("invalid controller input")

    def activate(self) -> _ControllerResolutionActivationAcknowledgment:
        if self._resolved:
            raise _mutation_failed()
        acknowledgment = self._activation_acknowledgment
        if type(acknowledgment) is not _ControllerResolutionActivationAcknowledgment:
            try:
                acknowledgment = self._operation_lease._activate_controller_scope(
                    scope_token=self._scope_token,
                )
                self._activation_acknowledgment = acknowledgment
            except BaseException:
                observed = self._operation_lease._controller_resolution_for_scope(
                    scope_token=self._scope_token,
                )
                if type(observed) is _WriterSessionControllerResolution:
                    self._activation_acknowledgment = (
                        _ControllerResolutionActivationAcknowledgment(
                            self._scope_token,
                            observed,
                        )
                    )
                raise
        return acknowledgment

    def commit(self) -> object | None:
        connection = self._borrow_connection()
        return _commit_transaction(connection)

    def rollback(self) -> SQLiteMutationStoreError | None:
        connection = self._borrow_connection()
        return _rollback_transaction(connection)

    def close_after_commit(
        self,
        *,
        commit_succeeded: bool,
        force_cleanup: bool,
    ) -> bool:
        if self._resolved:
            if force_cleanup:
                self.stabilize_process_control()
            return self._close_proved is True
        self._validated_activation()
        retained_connection = self._retained_connection
        if type(retained_connection) is not _RetainedSQLiteConnection:
            raise _mutation_failed()
        intent = (
            _ControllerResolutionIntent.COMMIT_KNOWN
            if commit_succeeded
            else _ControllerResolutionIntent.COMMIT_UNCERTAIN
        )
        try:
            close_proof = retained_connection._close_with_proof()
        except Exception:
            self._publish_facts(
                _ControllerCloseUnprovedFacts(intent, retained_connection)
            )
            return False
        except BaseException:
            try:
                self._publish_facts(
                    _ControllerCloseUnprovedFacts(intent, retained_connection)
                )
            except BaseException:
                try:
                    self._operation_lease._stabilize_controller_process_control(
                        scope_token=self._scope_token,
                        proved_facts=None,
                    )
                except BaseException:
                    pass
            raise
        facts = _ControllerCloseProvedFacts(
            intent,
            close_proof,
            _CleanupRequiredAfterResolution()
            if force_cleanup
            else _ResumeIfCloseProvedAndStillEligible(),
        )
        self._proved_facts = facts
        self._publish_facts(facts)
        return True

    def close_before_commit(self) -> bool:
        if self._resolved:
            return self._close_proved is True
        self._validated_activation()
        retained_connection = self._retained_connection
        if type(retained_connection) is not _RetainedSQLiteConnection:
            raise _mutation_failed()
        intent = _ControllerResolutionIntent.PRECOMMIT_ABORT
        try:
            close_proof = retained_connection._close_with_proof()
        except Exception:
            self._publish_facts(
                _ControllerCloseUnprovedFacts(intent, retained_connection)
            )
            return False
        except BaseException:
            try:
                self._publish_facts(
                    _ControllerCloseUnprovedFacts(intent, retained_connection)
                )
            except BaseException:
                try:
                    self._operation_lease._stabilize_controller_process_control(
                        scope_token=self._scope_token,
                        proved_facts=None,
                    )
                except BaseException:
                    pass
            raise
        facts = _ControllerCloseProvedFacts(
            intent,
            close_proof,
            _ResumeIfCloseProvedAndStillEligible(),
        )
        self._proved_facts = facts
        self._publish_facts(facts)
        return True

    def stabilize_process_control(self) -> None:
        self._operation_lease._stabilize_controller_process_control(
            scope_token=self._scope_token,
            proved_facts=self._proved_facts,
        )

    def _validated_activation(self) -> _WriterSessionControllerResolution:
        if (
            self._resolved
            or self._owner_pid != os.getpid()
            or self._owner_thread != get_ident()
            or type(self._activation_acknowledgment)
            is not _ControllerResolutionActivationAcknowledgment
        ):
            raise _mutation_failed()
        try:
            return self._operation_lease._require_controller_scope(
                acknowledgment=self._activation_acknowledgment,
                scope_token=self._scope_token,
            )
        except WriterSessionError:
            observed = self._operation_lease._controller_resolution_for_scope(
                scope_token=self._scope_token,
            )
            if type(observed) is not _WriterSessionControllerResolution:
                raise _mutation_failed() from None
            self._activation_acknowledgment = (
                _ControllerResolutionActivationAcknowledgment(
                    self._scope_token,
                    observed,
                )
            )
            return observed

    def _borrow_connection(self) -> sqlite3.Connection:
        self._validated_activation()
        retained_connection = self._retained_connection
        if type(retained_connection) is not _RetainedSQLiteConnection:
            raise _mutation_failed()
        try:
            return retained_connection._borrow_exact_connection()
        except Exception:
            raise _mutation_failed() from None

    def _publish_facts(
        self,
        facts: _ControllerCloseProvedFacts | _ControllerCloseUnprovedFacts,
    ) -> None:
        if self._resolved:
            acknowledgment = self._publication_acknowledgment
            if type(acknowledgment) is not _ControllerSuccessorPublicationAcknowledgment:
                raise _mutation_failed()
            return
        activation = self._activation_acknowledgment
        if type(activation) is not _ControllerResolutionActivationAcknowledgment:
            raise _mutation_failed()
        try:
            acknowledgment = self._operation_lease._publish_controller_resolution(
                acknowledgment=activation,
                facts=facts,
            )
        except Exception:
            observed = self._operation_lease._controller_resolution_for_scope(
                scope_token=self._scope_token,
            )
            if type(observed) is _WriterSessionControllerResolution:
                activation = _ControllerResolutionActivationAcknowledgment(
                    self._scope_token,
                    observed,
                )
                self._activation_acknowledgment = activation
            acknowledgment = self._operation_lease._publish_controller_resolution(
                acknowledgment=activation,
                facts=facts,
            )
        except BaseException:
            try:
                acknowledgment = self._operation_lease._publish_controller_resolution(
                    acknowledgment=activation,
                    facts=facts,
                )
                if type(facts) is _ControllerCloseProvedFacts:
                    try:
                        self._operation_lease._stabilize_controller_process_control(
                            scope_token=self._scope_token,
                            proved_facts=facts,
                        )
                    except BaseException:
                        pass
                self._accept_publication_acknowledgment(acknowledgment, facts)
            except BaseException:
                pass
            raise
        self._accept_publication_acknowledgment(acknowledgment, facts)

    def _accept_publication_acknowledgment(
        self,
        acknowledgment: object,
        facts: _ControllerCloseProvedFacts | _ControllerCloseUnprovedFacts,
    ) -> None:
        if (
            type(acknowledgment) is not _ControllerSuccessorPublicationAcknowledgment
            or acknowledgment.scope_token is not self._scope_token
        ):
            raise _mutation_failed()
        self._publication_acknowledgment = acknowledgment
        self._close_proved = type(facts) is _ControllerCloseProvedFacts
        # Connection aliases clear only after the exact resource acknowledgment.
        self._retained_connection = None
        self._activation_acknowledgment = None
        self._resolved = True


_SQLITE_INTEGRITY_PRIMARY_RESULT_CODES = frozenset(
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


@dataclass(frozen=True, slots=True)
class _WriterOwnershipQuerySpec:
    query_id: str
    table_name: str
    columns: tuple[str, ...]
    sql: str

    def __post_init__(self) -> None:
        if self.query_id != "writer_ownership_fencing":
            raise ValueError("invalid writer query")
        if self.table_name != "writer_ownership":
            raise ValueError("invalid writer query")
        if self.columns != (
            "singleton_id",
            "writer_ref",
            "generation",
            "issued_ref",
            "issuance_nonce_digest",
            "acquired_at",
        ):
            raise ValueError("invalid writer query")
        if self.sql != _writer_ownership_select_sql(table_name=self.table_name, columns=self.columns):
            raise ValueError("invalid writer query")


def _writer_ownership_select_sql(*, table_name: str, columns: tuple[str, ...]) -> str:
    return "SELECT\n    " + ",\n    ".join(columns) + f"\nFROM {table_name}\nORDER BY singleton_id\nLIMIT 2"


_WRITER_OWNERSHIP_SELECT = _WriterOwnershipQuerySpec(
    query_id="writer_ownership_fencing",
    table_name="writer_ownership",
    columns=(
        "singleton_id",
        "writer_ref",
        "generation",
        "issued_ref",
        "issuance_nonce_digest",
        "acquired_at",
    ),
    sql="""SELECT
    singleton_id,
    writer_ref,
    generation,
    issued_ref,
    issuance_nonce_digest,
    acquired_at
FROM writer_ownership
ORDER BY singleton_id
LIMIT 2""",
)


@dataclass(frozen=True, slots=True, repr=False)
class _FreshTransitionEvaluation:
    """Private fresh evaluator output awaiting durable write planning."""

    source_record: WorkItemRecord = field(repr=False)
    evaluation: TransitionEvaluation = field(repr=False)
    transaction_timestamp: str

    def __post_init__(self) -> None:
        source_record = _require_initialized_work_item_record(self.source_record)
        evaluation = _require_initialized_transition_evaluation(self.evaluation)
        timestamp = normalize_transaction_timestamp(self.transaction_timestamp)
        if evaluation.kind is TransitionEvaluationKind.PRE_APPLY_INVALID:
            raise _database_integrity_failure()
        if evaluation.kind not in (TransitionEvaluationKind.ACCEPTED, TransitionEvaluationKind.DOMAIN_REJECTED):
            raise _database_integrity_failure()
        if type(evaluation.event) is not TransitionEvent:
            raise _database_integrity_failure()
        object.__setattr__(self, "source_record", source_record)
        object.__setattr__(self, "evaluation", evaluation)
        object.__setattr__(self, "transaction_timestamp", timestamp)

    def __repr__(self) -> str:
        return "<_FreshTransitionEvaluation>"


@dataclass(frozen=True, slots=True, repr=False)
class _FreshGlobalStopEvaluation:
    """Private fresh global-stop evaluator output awaiting durable write planning."""

    source_state: GlobalStopState = field(repr=False)
    evaluation: GlobalStopEvaluation = field(repr=False)
    transaction_timestamp: str

    def __post_init__(self) -> None:
        source_state = _require_initialized_global_stop_state_for_mutation(self.source_state)
        evaluation = _require_initialized_global_stop_evaluation_for_mutation(self.evaluation)
        timestamp = normalize_transaction_timestamp(self.transaction_timestamp)
        if evaluation.kind is GlobalStopEvaluationKind.PRE_APPLY_INVALID:
            raise _database_integrity_failure()
        if evaluation.kind not in (GlobalStopEvaluationKind.ACCEPTED, GlobalStopEvaluationKind.DOMAIN_REJECTED):
            raise _database_integrity_failure()
        event = evaluation.event
        if type(event) is not GlobalStopEvent:
            raise _database_integrity_failure()
        if event.source_version != source_state.version:
            raise _database_integrity_failure()
        if evaluation.kind is GlobalStopEvaluationKind.ACCEPTED:
            if evaluation.state.version != source_state.version + 1:
                raise _database_integrity_failure()
        elif evaluation.state != source_state:
            raise _database_integrity_failure()
        object.__setattr__(self, "source_state", source_state)
        object.__setattr__(self, "evaluation", evaluation)
        object.__setattr__(self, "transaction_timestamp", timestamp)

    def __repr__(self) -> str:
        return "<_FreshGlobalStopEvaluation>"


class _MutationCapabilityState:
    """Controller-owned mutable state for one transaction epoch."""

    __slots__ = ("_active", "_connection", "_connection_identity", "_epoch", "_permanently_expired")
    __hash__ = object.__hash__

    def __init__(self, *, connection: sqlite3.Connection, epoch: object) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("invalid capability input")
        self._active = True
        self._connection: sqlite3.Connection | None = connection
        self._connection_identity = id(connection)
        self._epoch = epoch
        self._permanently_expired = False

    def __repr__(self) -> str:
        return "<_MutationCapabilityState>"

    def __reduce__(self) -> object:
        raise TypeError("invalid capability input")

    def invalidate(self, *, key: object, epoch: object) -> None:
        if key is not _CAPABILITY_CONSTRUCTION_KEY or epoch is not self._epoch:
            raise ValueError("invalid capability input")
        self._active = False
        self._permanently_expired = True
        self._epoch = None
        self._connection = None
        self._connection_identity = None

    def borrow(self, *, epoch: object, connection_identity: int) -> sqlite3.Connection:
        if self._permanently_expired or not self._active:
            raise _capability_error(_MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED)
        if epoch is not self._epoch:
            raise _capability_error(_MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED)
        connection = self._connection
        if type(connection) is not sqlite3.Connection or id(connection) != connection_identity:
            raise _capability_error(_MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE)
        unavailable = False
        try:
            in_transaction = connection.in_transaction
        except Exception:
            unavailable = True
            in_transaction = False
        if unavailable:
            raise _capability_error(_MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE)
        if in_transaction is not True:
            raise _capability_error(_MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED)
        return connection


class _SQLiteMutationReadCapability:
    """Nominal private mutation-read capability for one active transaction."""

    __slots__ = ("_connection_identity", "_epoch", "_owner_pid", "_owner_thread", "_state")
    __hash__ = object.__hash__

    def __init__(
        self,
        *,
        key: object,
        connection: sqlite3.Connection,
        epoch: object,
        owner_pid: int,
        owner_thread: int,
        state: _MutationCapabilityState,
    ) -> None:
        if key is not _CAPABILITY_CONSTRUCTION_KEY:
            raise ValueError("invalid capability input")
        if type(connection) is not sqlite3.Connection or type(state) is not _MutationCapabilityState:
            raise ValueError("invalid capability input")
        if type(owner_pid) is not int or type(owner_thread) is not int:
            raise ValueError("invalid capability input")
        self._state = state
        self._epoch = epoch
        self._connection_identity = id(connection)
        self._owner_pid = owner_pid
        self._owner_thread = owner_thread

    def __repr__(self) -> str:
        return "<_SQLiteMutationReadCapability>"

    def __reduce__(self) -> object:
        raise TypeError("invalid capability input")

    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        if self._owner_pid != os.getpid():
            raise _capability_error(_MutationReadCapabilityFailureReason.PROCESS_MISMATCH)
        if self._owner_thread != get_ident():
            raise _capability_error(_MutationReadCapabilityFailureReason.THREAD_MISMATCH)
        state = self._state
        if type(state) is not _MutationCapabilityState:
            raise _capability_error(_MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE)
        unavailable = False
        try:
            connection = state.borrow(epoch=self._epoch, connection_identity=self._connection_identity)
        except _MutationReadCapabilityError:
            raise
        except Exception:
            unavailable = True
            connection = None
        if unavailable or type(connection) is not sqlite3.Connection:
            raise _capability_error(_MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE)
        return connection


class _CoordinatorMutationTransactionController:
    """Private single-use transaction controller for Coordinator mutation entries."""

    __slots__ = (
        "_capability",
        "_capability_state",
        "_commit_attempt_started",
        "_connection",
        "_connection_scope",
        "_epoch",
        "_operation_lease",
        "_owner_pid",
        "_owner_thread",
        "_resolution_state",
        "_state",
        "_transaction_began",
    )
    __hash__ = object.__hash__

    def __init__(
        self,
        *,
        key: object,
        operation_lease: _WriterSessionOperationLease,
    ) -> None:
        if key is not _CONTROLLER_CONSTRUCTION_KEY:
            raise _mutation_failed()
        if type(operation_lease) is not _WriterSessionOperationLease:
            raise _mutation_failed()
        self._operation_lease = operation_lease
        self._owner_pid = os.getpid()
        self._owner_thread = get_ident()
        self._state = _CONTROLLER_NEW
        self._resolution_state = _MutationCommitResolutionState.NEW
        self._commit_attempt_started = False
        self._connection: sqlite3.Connection | None = None
        self._connection_scope: _ControllerConnectionScope | None = None
        self._transaction_began = False
        self._epoch: object | None = None
        self._capability_state: _MutationCapabilityState | None = None
        self._capability: _SQLiteMutationReadCapability | None = None

    def __repr__(self) -> str:
        return "<_CoordinatorMutationTransactionController>"

    def __reduce__(self) -> object:
        raise TypeError("invalid controller input")

    def run(self) -> _WriterIssuanceMatch:
        result = self._run_writer_fencing_transaction()
        if type(result) is not _WriterIssuanceMatch:
            raise _mutation_failed()
        return result

    def run_transition_dry_run(
        self,
        *,
        transition_command: TransitionCommand,
    ) -> _RollbackOnlyTransitionDryRunResult:
        if type(transition_command) is not TransitionCommand:
            raise _mutation_failed()
        result = self._run_transition_dry_run_transaction(transition_command=transition_command)
        if type(result) is not _RollbackOnlyTransitionDryRunResult:
            raise _mutation_failed()
        return result

    def run_atomic_transition_apply(
        self,
        *,
        transition_command: TransitionCommand,
    ) -> TransitionApplyOutcome:
        if type(transition_command) is not TransitionCommand:
            raise _mutation_failed()
        result = self._run_atomic_transition_apply_transaction(transition_command=transition_command)
        if type(result) not in (CommittedTransition, TransitionConflict):
            raise _mutation_failed()
        return result

    def run_atomic_global_stop_apply(
        self,
        *,
        global_stop_command: GlobalStopCommand,
        typed_operator_decision: GlobalStopOperatorDecision,
    ) -> GlobalStopApplyOutcome:
        if type(global_stop_command) is not GlobalStopCommand:
            raise _mutation_failed()
        if type(typed_operator_decision) is not GlobalStopOperatorDecision:
            raise _mutation_failed()
        result = self._run_atomic_global_stop_apply_transaction(
            global_stop_command=global_stop_command,
            typed_operator_decision=typed_operator_decision,
        )
        if type(result) not in (CommittedGlobalStopUpdate, GlobalStopConflict):
            raise _mutation_failed()
        return result

    def _run_writer_fencing_transaction(self) -> _WriterIssuanceMatch:
        self._require_new_owner()
        mutation_lease = self._acquire_controller_mutation_lease()
        planned_result: _WriterIssuanceMatch | None = None
        planned_exception: BaseException | None = None
        cleanup_exception: SQLiteMutationStoreError | None = None
        try:
            try:
                planned_result = self._run_until_writer_fencing_resolution()
            except _WriterSessionAuthorityClosed:
                planned_exception = _database_integrity_failure()
            except _WriterSessionAuthorityUnavailable:
                planned_exception = _mutation_failed()
            except WriterSessionError as exc:
                planned_exception = exc
            except SQLiteMutationStoreError as exc:
                planned_exception = exc
            except Exception:
                planned_exception = _mutation_failed()
            except BaseException:
                if not self._commit_attempt_started:
                    try:
                        self._resolve_rollback_before_commit()
                    except BaseException:
                        pass
                raise
            cleanup_exception = self._resolve_rollback_before_commit()
        finally:
            mutation_lease._close()

        if cleanup_exception is not None:
            raise cleanup_exception
        if planned_exception is not None:
            raise planned_exception
        if planned_result is None:
            raise _mutation_failed()
        return planned_result

    def _run_transition_dry_run_transaction(
        self,
        *,
        transition_command: TransitionCommand,
    ) -> _RollbackOnlyTransitionDryRunResult:
        self._require_new_owner()
        mutation_lease = self._acquire_controller_mutation_lease()
        planned_result: _RollbackOnlyTransitionDryRunResult | None = None
        planned_exception: BaseException | None = None
        cleanup_exception: SQLiteMutationStoreError | None = None
        try:
            try:
                planned_result = _dry_run_result_from_transition_resolution(
                    self._run_until_transition_resolution(transition_command)
                )
            except _WriterSessionAuthorityClosed:
                planned_exception = _database_integrity_failure()
            except _WriterSessionAuthorityUnavailable:
                planned_exception = _mutation_failed()
            except WriterSessionError as exc:
                planned_exception = exc
            except SQLiteMutationStoreError as exc:
                planned_exception = exc
            except Exception:
                planned_exception = _mutation_failed()
            except BaseException:
                if not self._commit_attempt_started:
                    try:
                        self._resolve_rollback_before_commit()
                    except BaseException:
                        pass
                raise
            cleanup_exception = self._resolve_rollback_before_commit()
        finally:
            mutation_lease._close()

        if cleanup_exception is not None:
            raise cleanup_exception
        if planned_exception is not None:
            raise planned_exception
        if planned_result is None:
            raise _mutation_failed()
        return planned_result

    def _run_atomic_transition_apply_transaction(
        self,
        *,
        transition_command: TransitionCommand,
    ) -> TransitionApplyOutcome:
        self._require_new_owner()
        mutation_lease = self._acquire_controller_mutation_lease()
        planned_result: TransitionApplyOutcome | None = None
        planned_exception: BaseException | None = None
        cleanup_exception: SQLiteMutationStoreError | None = None
        try:
            try:
                resolution = self._run_until_transition_resolution(transition_command)
                if type(resolution) is _FreshTransitionEvaluation:
                    planned_result = self._commit_fresh_transition(resolution)
                elif type(resolution) in (CommittedTransition, TransitionConflict):
                    planned_result = resolution
                    cleanup_exception = self._resolve_rollback_before_commit()
                else:
                    planned_exception = _database_integrity_failure()
            except _WriterSessionAuthorityClosed:
                planned_exception = _database_integrity_failure()
            except _WriterSessionAuthorityUnavailable:
                planned_exception = _mutation_failed()
            except WriterSessionError as exc:
                planned_exception = exc
            except SQLiteMutationStoreError as exc:
                planned_exception = exc
            except Exception:
                planned_exception = _mutation_failed()
            except BaseException:
                if not self._commit_attempt_started:
                    try:
                        self._resolve_rollback_before_commit()
                    except BaseException:
                        pass
                raise
            if planned_exception is not None and not self._commit_attempt_started:
                cleanup_exception = self._resolve_rollback_before_commit()
        finally:
            mutation_lease._close()

        if cleanup_exception is not None:
            raise cleanup_exception
        if planned_exception is not None:
            raise planned_exception
        if planned_result is None:
            raise _mutation_failed()
        return planned_result

    def _run_atomic_global_stop_apply_transaction(
        self,
        *,
        global_stop_command: GlobalStopCommand,
        typed_operator_decision: GlobalStopOperatorDecision,
    ) -> GlobalStopApplyOutcome:
        self._require_new_owner()
        mutation_lease = self._acquire_controller_mutation_lease()
        planned_result: GlobalStopApplyOutcome | None = None
        planned_exception: BaseException | None = None
        cleanup_exception: SQLiteMutationStoreError | None = None
        try:
            try:
                resolution = self._run_until_global_stop_resolution(
                    global_stop_command,
                    typed_operator_decision,
                )
                if type(resolution) is _FreshGlobalStopEvaluation:
                    planned_result = self._commit_fresh_global_stop(resolution)
                elif type(resolution) in (CommittedGlobalStopUpdate, GlobalStopConflict):
                    planned_result = resolution
                    cleanup_exception = self._resolve_rollback_before_commit()
                else:
                    planned_exception = _database_integrity_failure()
            except _WriterSessionAuthorityClosed:
                planned_exception = _database_integrity_failure()
            except _WriterSessionAuthorityUnavailable:
                planned_exception = _mutation_failed()
            except WriterSessionError as exc:
                planned_exception = exc
            except SQLiteMutationStoreError as exc:
                planned_exception = exc
            except Exception:
                planned_exception = _mutation_failed()
            except BaseException:
                if not self._commit_attempt_started:
                    try:
                        self._resolve_rollback_before_commit()
                    except BaseException:
                        pass
                raise
            if planned_exception is not None and not self._commit_attempt_started:
                cleanup_exception = self._resolve_rollback_before_commit()
        finally:
            mutation_lease._close()

        if cleanup_exception is not None:
            raise cleanup_exception
        if planned_exception is not None:
            raise planned_exception
        if planned_result is None:
            raise _mutation_failed()
        return planned_result

    def _acquire_controller_mutation_lease(self) -> Any:
        mutation_lease_failed = False
        mutation_lease_exception: SQLiteMutationStoreError | None = None
        try:
            mutation_lease = self._operation_lease._acquire_mutation_lease()
        except _WriterSessionAuthorityClosed:
            mutation_lease_exception = _database_integrity_failure()
            mutation_lease = None
        except _WriterSessionAuthorityUnavailable:
            mutation_lease_exception = _mutation_failed()
            mutation_lease = None
        except WriterSessionError:
            raise
        except Exception:
            mutation_lease_failed = True
            mutation_lease = None
        if mutation_lease_exception is not None:
            raise mutation_lease_exception
        if mutation_lease_failed or mutation_lease is None:
            raise _mutation_failed()
        return mutation_lease

    def _require_new_owner(self) -> None:
        if self._state != _CONTROLLER_NEW:
            raise _mutation_failed()
        if self._resolution_state is not _MutationCommitResolutionState.NEW:
            raise _mutation_failed()
        if self._owner_pid != os.getpid() or self._owner_thread != get_ident():
            raise _mutation_failed()

    def _run_until_writer_fencing_resolution(self) -> _WriterIssuanceMatch:
        binding = self._operation_lease._bound_state_database_for_mutation()
        connection = _open_controller_connection(binding)
        self._connection = connection
        _begin_immediate(connection)
        self._transaction_began = True
        self._state = _CONTROLLER_TRANSACTION_ACTIVE
        self._set_resolution_state(_MutationCommitResolutionState.TRANSACTION_ACTIVE)
        _validate_bound_database_for_mutation(binding)
        _validate_managed_connection_for_mutation(connection)
        issuance = _read_writer_ownership_for_fencing(connection)
        result = self._operation_lease._verify_durable_writer_issuance(issuance)
        if result is _WriterIssuanceMatch.MATCH:
            self._state = _CONTROLLER_FENCED
            self._set_resolution_state(_MutationCommitResolutionState.FENCED)
            self._epoch = object()
            self._capability_state = _MutationCapabilityState(connection=connection, epoch=self._epoch)
            self._capability = _create_sqlite_mutation_read_capability(
                connection=connection,
                epoch=self._epoch,
                owner_pid=self._owner_pid,
                owner_thread=self._owner_thread,
                state=self._capability_state,
            )
            self._state = _CONTROLLER_CAPABILITY_ACTIVE
            self._set_resolution_state(_MutationCommitResolutionState.CAPABILITY_ACTIVE)
            return _WriterIssuanceMatch.MATCH
        if result is _WriterIssuanceMatch.STALE_WRITER:
            self._state = _CONTROLLER_FENCED
            self._set_resolution_state(_MutationCommitResolutionState.FENCED)
            return _WriterIssuanceMatch.STALE_WRITER
        raise _mutation_failed()

    def _run_until_transition_resolution(
        self,
        command: TransitionCommand,
    ) -> CommittedTransition | TransitionConflict | _FreshTransitionEvaluation:
        fencing = self._run_until_writer_fencing_resolution()
        if fencing is _WriterIssuanceMatch.STALE_WRITER:
            return TransitionConflict("stale_writer_token")
        if fencing is not _WriterIssuanceMatch.MATCH:
            raise _mutation_failed()

        capability = self._capability
        if type(capability) is not _SQLiteMutationReadCapability:
            raise _mutation_failed()
        existing = _read_transition_event_for_idempotency(
            capability,
            command.work_item_id,
            command.idempotency_key,
        )
        matched = match_transition_event_idempotency(existing, command)
        if type(matched) is CommittedTransition:
            return matched
        if type(matched) is TransitionConflict:
            return matched
        if matched is not None:
            raise _database_integrity_failure()

        current_envelope = _read_current_work_item(capability, command.work_item_id)
        if current_envelope is None:
            return TransitionConflict("work_item_not_found")
        if type(current_envelope) is not WorkItemRecordEnvelope:
            raise _database_integrity_failure()
        current_record = current_envelope.record
        if current_record.version != command.expected_version:
            return TransitionConflict("expected_version_conflict")

        lease_identity_envelope = _read_lease_identity_record(capability, command.lease_identity_decision_ref)
        if lease_identity_envelope is None:
            return TransitionConflict("validation_failed")
        if type(lease_identity_envelope) is not LeaseIdentityRecordEnvelope:
            raise _database_integrity_failure()

        backlog_envelope = _read_admitted_backlog(capability, current_record.backlog_id)
        if backlog_envelope is None:
            raise _database_integrity_failure()
        if type(backlog_envelope) is not AdmittedBacklogRecordEnvelope:
            raise _database_integrity_failure()

        authorization_envelope = _read_authorization_receipt(capability, command.authorization_decision_ref)
        if authorization_envelope is None:
            return TransitionConflict("validation_failed")
        if type(authorization_envelope) is not AuthorizationReceiptEnvelope:
            raise _database_integrity_failure()

        if command.target_state is WorkItemState.READY:
            dependency_ref = command.dependency_decision_ref
            if dependency_ref is None:
                return TransitionConflict("validation_failed")
            dependency_envelope = _read_dependency_receipt(capability, dependency_ref)
            if dependency_envelope is None:
                return TransitionConflict("validation_failed")
            if type(dependency_envelope) is not DependencyReceiptEnvelope:
                raise _database_integrity_failure()
            dependency = dependency_envelope.decision
        else:
            dependency = DependencyDecision()

        global_stop_envelope = _read_global_stop_current(capability)
        if type(global_stop_envelope) is not GlobalStopCurrentRecordEnvelope:
            raise _database_integrity_failure()

        bound = _bind_b3c3_transition_authority(
            command=command,
            current_record=current_record,
            standing_lease=lease_identity_envelope.reconstruction.lease,
            admitted_backlog=backlog_envelope.backlog,
            lease_identity=lease_identity_envelope.reconstruction.validation,
            authorization=authorization_envelope.decision,
            dependency=dependency,
            global_stop=global_stop_envelope.state,
        )
        if type(bound) is TransitionConflict:
            return bound
        if type(bound) is not _BoundTransitionAuthority:
            raise _database_integrity_failure()

        timestamp = _capture_transaction_timestamp()
        evaluation = _evaluate_bound_transition(command=command, bound_authority=bound, timestamp=timestamp)
        return _FreshTransitionEvaluation(
            source_record=bound.current_record,
            evaluation=evaluation,
            transaction_timestamp=timestamp,
        )

    def _run_until_global_stop_resolution(
        self,
        command: GlobalStopCommand,
        typed_operator_decision: GlobalStopOperatorDecision,
    ) -> CommittedGlobalStopUpdate | GlobalStopConflict | _FreshGlobalStopEvaluation:
        fencing = self._run_until_writer_fencing_resolution()
        if fencing is _WriterIssuanceMatch.STALE_WRITER:
            return GlobalStopConflict("stale_writer_token")
        if fencing is not _WriterIssuanceMatch.MATCH:
            raise _mutation_failed()

        capability = self._capability
        if type(capability) is not _SQLiteMutationReadCapability:
            raise _mutation_failed()
        existing = _read_global_stop_event_for_idempotency(capability, command.idempotency_key)
        matched = match_global_stop_event_idempotency(existing, command)
        if type(matched) is CommittedGlobalStopUpdate:
            return matched
        if type(matched) is GlobalStopConflict:
            return matched
        if matched is not None:
            raise _database_integrity_failure()

        current_envelope = _read_global_stop_current(capability)
        if type(current_envelope) is not GlobalStopCurrentRecordEnvelope:
            raise _database_integrity_failure()
        current_state = current_envelope.state
        if type(current_state) is not GlobalStopState:
            raise _database_integrity_failure()
        if current_state.version != command.expected_version:
            return GlobalStopConflict("expected_version_conflict")

        receipt_envelope = _read_global_stop_operator_decision_receipt(
            capability,
            command.operator_decision_ref,
        )
        if receipt_envelope is not None and type(receipt_envelope) is not GlobalStopOperatorDecisionReceiptEnvelope:
            raise _database_integrity_failure()
        bound_decision = _bind_global_stop_operator_decision_receipt(
            command=command,
            typed_operator_decision=typed_operator_decision,
            receipt=receipt_envelope,
        )
        if type(bound_decision) is GlobalStopConflict:
            return bound_decision
        if type(bound_decision) is not GlobalStopOperatorDecision:
            raise _database_integrity_failure()

        evaluation = _evaluate_bound_global_stop_update(
            state=current_state,
            command=command,
            operator_decision=bound_decision,
        )
        timestamp = _capture_transaction_timestamp()
        return _FreshGlobalStopEvaluation(
            source_state=current_state,
            evaluation=evaluation,
            transaction_timestamp=timestamp,
        )

    def _commit_fresh_transition(
        self,
        fresh: _FreshTransitionEvaluation,
    ) -> CommittedTransition:
        if type(fresh) is not _FreshTransitionEvaluation:
            raise _database_integrity_failure()
        capability = self._capability
        connection = self._connection
        if type(capability) is not _SQLiteMutationReadCapability or type(connection) is not sqlite3.Connection:
            raise _mutation_failed()
        if self._resolution_state is not _MutationCommitResolutionState.CAPABILITY_ACTIVE:
            raise _mutation_failed()

        maximum_sequence = _read_transition_event_max_sequence(capability)
        event_sequence = next_transition_event_sequence(maximum_sequence)
        plan = _transition_write_plan(
            fresh.evaluation,
            source_record=fresh.source_record,
            event_sequence=event_sequence,
            transaction_timestamp=fresh.transaction_timestamp,
        )
        plan = _require_exact_transition_write_plan(plan)
        planned_transition = _require_fresh_planned_transition(plan.planned_transition)
        self._set_resolution_state(_MutationCommitResolutionState.PLANNED_OUTCOME)

        _execute_transition_event_insert(connection, plan.event_insert)
        if plan.accepted_work_item_cas is not None:
            _execute_accepted_work_item_cas(connection, plan.accepted_work_item_cas)
        self._set_resolution_state(_MutationCommitResolutionState.WRITES_PERFORMED)

        del connection
        committed = self._commit_after_fresh_writes(planned_transition)
        if type(committed) is not CommittedTransition:
            raise _database_integrity_failure()
        return committed

    def _commit_fresh_global_stop(
        self,
        fresh: _FreshGlobalStopEvaluation,
    ) -> CommittedGlobalStopUpdate:
        if type(fresh) is not _FreshGlobalStopEvaluation:
            raise _database_integrity_failure()
        capability = self._capability
        connection = self._connection
        if type(capability) is not _SQLiteMutationReadCapability or type(connection) is not sqlite3.Connection:
            raise _mutation_failed()
        if self._resolution_state is not _MutationCommitResolutionState.CAPABILITY_ACTIVE:
            raise _mutation_failed()

        maximum_sequence = _read_global_stop_event_max_sequence(capability)
        event_sequence = next_global_stop_event_sequence(maximum_sequence)
        plan = _global_stop_write_plan(
            fresh.evaluation,
            source_state=fresh.source_state,
            event_sequence=event_sequence,
            transaction_timestamp=fresh.transaction_timestamp,
        )
        plan = _require_exact_global_stop_write_plan(plan)
        planned_update = _require_fresh_planned_global_stop_update(plan.planned_update)
        self._set_resolution_state(_MutationCommitResolutionState.PLANNED_OUTCOME)

        _execute_global_stop_event_insert(connection, plan.event_insert)
        if plan.accepted_global_stop_current_cas is not None:
            _execute_accepted_global_stop_current_cas(connection, plan.accepted_global_stop_current_cas)
        self._set_resolution_state(_MutationCommitResolutionState.WRITES_PERFORMED)

        del connection
        committed = self._commit_after_fresh_writes(planned_update)
        if type(committed) is not CommittedGlobalStopUpdate:
            raise _database_integrity_failure()
        return committed

    def _commit_after_fresh_writes(
        self,
        planned_result: object,
    ) -> object:
        invalidation_failure = self._invalidate_capability_for_resolution()
        if invalidation_failure is not None:
            raise invalidation_failure
        self._set_resolution_state(
            _MutationCommitResolutionState.CAPABILITY_INVALIDATED
        )
        self._prepare_controller_scope()
        commit_observation: object = _SQLITE_COMMIT_NOT_RETURNED
        try:
            self._set_resolution_state(
                _MutationCommitResolutionState.COMMIT_ATTEMPT_STARTED
            )
            self._commit_attempt_started = True
            scope = self._connection_scope
            if type(scope) is not _ControllerConnectionScope:
                raise _mutation_failed()
            try:
                commit_observation = scope.commit()
            except Exception:
                commit_observation = _commit_outcome_unknown()
            if commit_observation is not None:
                try:
                    checked_commit_error = _require_safe_mutation_store_error_payload(
                        commit_observation
                    )
                    if (
                        object.__getattribute__(
                            checked_commit_error,
                            "error_class",
                        )
                        != SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN.value
                    ):
                        raise ValueError("invalid commit failure")
                    commit_observation = checked_commit_error
                except Exception:
                    commit_observation = _commit_outcome_unknown()
            self._transaction_began = False
            if commit_observation is not None:
                try:
                    self._set_resolution_state(
                        _MutationCommitResolutionState.COMMIT_OUTCOME_UNKNOWN
                    )
                except SQLiteMutationStoreError:
                    pass
                self._close_after_commit_resolution(
                    commit_succeeded=False,
                    force_cleanup=False,
                )
                raise commit_observation from None

            try:
                self._set_resolution_state(
                    _MutationCommitResolutionState.COMMIT_SUCCEEDED
                )
            except SQLiteMutationStoreError:
                self._close_after_commit_resolution(
                    commit_succeeded=True,
                    force_cleanup=False,
                )
                return planned_result
            self._close_after_commit_resolution(
                commit_succeeded=True,
                force_cleanup=False,
            )
            return planned_result
        except Exception:
            raise
        except BaseException:
            if not self._commit_attempt_started:
                raise
            self._stabilize_process_control_commit_resolution(
                commit_succeeded=commit_observation is None,
            )
            raise

    def _stabilize_process_control_commit_resolution(
        self,
        *,
        commit_succeeded: bool,
    ) -> None:
        self._transaction_began = False
        target_state = (
            _MutationCommitResolutionState.COMMIT_SUCCEEDED
            if commit_succeeded
            else _MutationCommitResolutionState.COMMIT_OUTCOME_UNKNOWN
        )
        try:
            self._set_resolution_state(target_state)
        except SQLiteMutationStoreError:
            pass
        scope = self._connection_scope
        try:
            self._close_after_commit_resolution(
                commit_succeeded=commit_succeeded,
                force_cleanup=True,
            )
            return
        except BaseException:
            pass
        if type(scope) is _ControllerConnectionScope:
            try:
                scope.stabilize_process_control()
                return
            except BaseException:
                pass
        try:
            self._close_after_commit_resolution(
                commit_succeeded=commit_succeeded,
                force_cleanup=True,
            )
        except BaseException:
            if type(scope) is _ControllerConnectionScope:
                try:
                    scope.stabilize_process_control()
                except BaseException:
                    pass

    def _prepare_controller_scope(self) -> _ControllerConnectionScope:
        scope = self._connection_scope
        if type(scope) is _ControllerConnectionScope:
            self._connection = None
            if not scope._resolved:
                scope.activate()
            return scope
        connection = self._connection
        if not isinstance(connection, sqlite3.Connection):
            raise _mutation_failed()
        scope = _ControllerConnectionScope(
            operation_lease=self._operation_lease,
            connection=connection,
        )
        try:
            self._connection_scope = scope
            self._connection = None
            connection = None
            scope.activate()
        except BaseException:
            if self._connection_scope is scope:
                self._connection = None
            raise
        return scope

    def _resolve_rollback_before_commit(
        self,
    ) -> SQLiteMutationStoreError | None:
        if self._commit_attempt_started:
            self._close_after_commit_resolution(
                commit_succeeded=False,
                force_cleanup=True,
            )
            return _commit_outcome_unknown()
        self._state = _CONTROLLER_RESOLVING
        cleanup_failure: SQLiteMutationStoreError | None = None
        capability_invalidated = (
            self._resolution_state
            is _MutationCommitResolutionState.CAPABILITY_INVALIDATED
        )
        rollback_resolved = False
        if self._capability is not None:
            invalidation_failure = self._invalidate_capability_for_resolution()
            if invalidation_failure is not None:
                cleanup_failure = invalidation_failure
            else:
                try:
                    self._set_resolution_state(
                        _MutationCommitResolutionState.CAPABILITY_INVALIDATED
                    )
                    capability_invalidated = True
                except SQLiteMutationStoreError as exc:
                    cleanup_failure = exc

        if self._transaction_began or self._connection is not None:
            try:
                scope = self._prepare_controller_scope()
            except Exception:
                return cleanup_failure or _mutation_failed()
            if self._transaction_began:
                try:
                    rollback_failure = scope.rollback()
                except Exception:
                    rollback_failure = _mutation_failed()
                except BaseException:
                    try:
                        scope.close_before_commit()
                    except BaseException:
                        pass
                    self._transaction_began = False
                    raise
                if rollback_failure is not None:
                    cleanup_failure = rollback_failure
                elif capability_invalidated:
                    try:
                        self._set_resolution_state(
                            _MutationCommitResolutionState.ROLLBACK_RESOLVED
                        )
                        rollback_resolved = True
                    except SQLiteMutationStoreError as exc:
                        cleanup_failure = exc
            self._transaction_began = False
            try:
                close_proved = scope.close_before_commit()
            except Exception:
                close_proved = False
                cleanup_failure = cleanup_failure or _mutation_failed()
            if close_proved:
                self._connection_scope = None
                if rollback_resolved:
                    try:
                        self._set_resolution_state(
                            _MutationCommitResolutionState.CLOSED
                        )
                    except SQLiteMutationStoreError as exc:
                        cleanup_failure = cleanup_failure or exc
            else:
                self._connection_scope = None
                cleanup_failure = cleanup_failure or _mutation_failed()
        elif self._connection_scope is not None:
            scope = self._connection_scope
            try:
                close_proved = scope.close_before_commit()
            except Exception:
                close_proved = False
            self._connection_scope = None
            if not close_proved:
                cleanup_failure = cleanup_failure or _mutation_failed()
        self._connection = None
        self._state = _CONTROLLER_CLOSED
        return cleanup_failure

    def _invalidate_capability_for_resolution(self) -> SQLiteMutationStoreError | None:
        capability = self._capability
        if capability is None:
            return None
        try:
            invalidation_failure = _invalidate_sqlite_mutation_read_capability(
                capability,
                state=self._capability_state,
                epoch=self._epoch,
            )
        except Exception:
            invalidation_failure = _mutation_failed()
        self._capability = None
        self._capability_state = None
        self._epoch = None
        return invalidation_failure

    def _close_after_commit_resolution(
        self,
        *,
        commit_succeeded: bool,
        force_cleanup: bool,
    ) -> None:
        scope = self._connection_scope
        if type(scope) is not _ControllerConnectionScope:
            raise _mutation_failed()
        try:
            try:
                close_proved = scope.close_after_commit(
                    commit_succeeded=commit_succeeded,
                    force_cleanup=force_cleanup,
                )
            except Exception:
                close_proved = scope.close_after_commit(
                    commit_succeeded=commit_succeeded,
                    force_cleanup=force_cleanup,
                )
        finally:
            if scope._resolved:
                close_proved = scope._close_proved
                if close_proved:
                    if force_cleanup:
                        self._state = (
                            _CONTROLLER_COMMIT_SUCCEEDED_CONNECTION_CLOSED_CLEANUP_PENDING
                            if commit_succeeded
                            else _CONTROLLER_COMMIT_UNCERTAIN_CONNECTION_CLOSED_CLEANUP_PENDING
                        )
                    else:
                        self._state = _CONTROLLER_CLOSED
                else:
                    self._state = (
                        _CONTROLLER_COMMIT_SUCCEEDED_QUARANTINED
                        if commit_succeeded
                        else _CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED
                    )
        if close_proved:
            try:
                self._set_resolution_state(
                    _MutationCommitResolutionState.CLOSED
                )
            except SQLiteMutationStoreError:
                pass
    def _set_resolution_state(self, state: _MutationCommitResolutionState) -> None:
        current_state = self._resolution_state
        if type(current_state) is not _MutationCommitResolutionState:
            raise _database_integrity_failure()
        if type(state) is not _MutationCommitResolutionState:
            raise _database_integrity_failure()
        if (current_state, state) not in _MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS:
            raise _database_integrity_failure()
        self._resolution_state = state


def _run_rollback_only_writer_fencing(
    *,
    operation_lease: _WriterSessionOperationLease,
) -> _WriterIssuanceMatch:
    if type(operation_lease) is not _WriterSessionOperationLease:
        raise _mutation_failed()
    controller = _CoordinatorMutationTransactionController(
        key=_CONTROLLER_CONSTRUCTION_KEY,
        operation_lease=operation_lease,
    )
    return controller.run()


def _run_rollback_only_transition_dry_run(
    *,
    operation_lease: _WriterSessionOperationLease,
    transition_command: TransitionCommand,
) -> _RollbackOnlyTransitionDryRunResult:
    if type(operation_lease) is not _WriterSessionOperationLease:
        raise _mutation_failed()
    checked_command = _validate_transition_dry_run_preflight(transition_command)
    controller = _CoordinatorMutationTransactionController(
        key=_CONTROLLER_CONSTRUCTION_KEY,
        operation_lease=operation_lease,
    )
    return controller.run_transition_dry_run(transition_command=checked_command)


def _run_atomic_transition_apply(
    *,
    operation_lease: _WriterSessionOperationLease,
    transition_command: TransitionCommand,
) -> TransitionApplyOutcome | _SafeMutationFailureDisposition:
    if type(operation_lease) is not _WriterSessionOperationLease:
        return _new_safe_mutation_failure_disposition(
            SQLiteMutationStoreErrorCode.MUTATION_FAILED
        )
    controller: _CoordinatorMutationTransactionController | None = None
    try:
        checked_command = _validate_transition_dry_run_preflight(transition_command)
        controller = _CoordinatorMutationTransactionController(
            key=_CONTROLLER_CONSTRUCTION_KEY,
            operation_lease=operation_lease,
        )
        result = controller.run_atomic_transition_apply(transition_command=checked_command)
    except SQLiteMutationStoreError as error:
        disposition = _safe_mutation_failure_disposition(error)
        error = None
        controller = None
        checked_command = None
        transition_command = None  # type: ignore[assignment]
        operation_lease = None  # type: ignore[assignment]
        return disposition
    controller = None
    checked_command = None
    transition_command = None  # type: ignore[assignment]
    operation_lease = None  # type: ignore[assignment]
    return result


def _run_atomic_global_stop_apply(
    *,
    operation_lease: _WriterSessionOperationLease,
    global_stop_command: GlobalStopCommand,
    typed_operator_decision: GlobalStopOperatorDecision,
) -> GlobalStopApplyOutcome | _SafeMutationFailureDisposition:
    if type(operation_lease) is not _WriterSessionOperationLease:
        return _new_safe_mutation_failure_disposition(
            SQLiteMutationStoreErrorCode.MUTATION_FAILED
        )
    controller: _CoordinatorMutationTransactionController | None = None
    try:
        preflight = _validate_global_stop_apply_preflight(
            global_stop_command,
            typed_operator_decision,
        )
        controller = _CoordinatorMutationTransactionController(
            key=_CONTROLLER_CONSTRUCTION_KEY,
            operation_lease=operation_lease,
        )
        result = controller.run_atomic_global_stop_apply(
            global_stop_command=preflight.command,
            typed_operator_decision=preflight.typed_operator_decision,
        )
    except SQLiteMutationStoreError as error:
        disposition = _safe_mutation_failure_disposition(error)
        error = None
        controller = None
        preflight = None
        global_stop_command = None  # type: ignore[assignment]
        typed_operator_decision = None  # type: ignore[assignment]
        operation_lease = None  # type: ignore[assignment]
        return disposition
    controller = None
    preflight = None
    global_stop_command = None  # type: ignore[assignment]
    typed_operator_decision = None  # type: ignore[assignment]
    operation_lease = None  # type: ignore[assignment]
    return result


def _safe_mutation_failure_disposition(
    error: SQLiteMutationStoreError,
) -> _SafeMutationFailureDisposition:
    try:
        checked = _require_safe_mutation_store_error_payload(error)
        if BaseException.with_traceback(checked, None) is not checked:
            raise ValueError("invalid safe mutation error")
        checked.__cause__ = None
        checked.__context__ = None
        return _SafeMutationFailureDisposition(checked)
    except Exception:
        return _new_safe_mutation_failure_disposition(
            SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
        )


def _new_safe_mutation_failure_disposition(
    error_code: SQLiteMutationStoreErrorCode,
) -> _SafeMutationFailureDisposition:
    if type(error_code) is not SQLiteMutationStoreErrorCode:
        error_code = SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
    return _SafeMutationFailureDisposition(SQLiteMutationStoreError(error_code))


def _utc_transaction_timestamp() -> str:
    failed = False
    timestamp: str | None = None
    try:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        timestamp = normalize_transaction_timestamp(now)
    except Exception:
        failed = True
    if failed or timestamp is None:
        raise _mutation_failed()
    return timestamp


def _capture_transaction_timestamp() -> str:
    failed = False
    timestamp: str | None = None
    try:
        raw_timestamp = _utc_transaction_timestamp()
        timestamp = normalize_transaction_timestamp(raw_timestamp)
    except SQLiteMutationStoreError:
        raise
    except Exception:
        failed = True
    if failed or timestamp is None:
        raise _mutation_failed()
    return timestamp


def _evaluate_bound_transition(
    *,
    command: TransitionCommand,
    bound_authority: _BoundTransitionAuthority,
    timestamp: str,
) -> TransitionEvaluation:
    context_failed = False
    context: TransitionContext | None = None
    try:
        lease_runtime = derive_lease_runtime_decision(bound_authority.standing_lease, timestamp)
        context = TransitionContext(
            lease_identity=bound_authority.lease_identity,
            authorization=bound_authority.authorization,
            lease_runtime=lease_runtime,
            global_stop=bound_authority.global_stop,
            dependency_decision=bound_authority.dependency,
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        context_failed = True
    if context_failed or context is None:
        raise _database_integrity_failure()
    evaluator_failed = False
    evaluation: TransitionEvaluation | None = None
    try:
        evaluation = evaluate_transition(bound_authority.current_record, command, context)
    except SQLiteMutationStoreError:
        raise
    except Exception:
        evaluator_failed = True
    if evaluator_failed:
        raise _mutation_failed()
    if type(evaluation) is not TransitionEvaluation:
        raise _database_integrity_failure()
    if evaluation.kind is TransitionEvaluationKind.PRE_APPLY_INVALID:
        raise _database_integrity_failure()
    if evaluation.kind in (TransitionEvaluationKind.ACCEPTED, TransitionEvaluationKind.DOMAIN_REJECTED):
        return evaluation
    raise _database_integrity_failure()


def _evaluate_bound_global_stop_update(
    *,
    state: GlobalStopState,
    command: GlobalStopCommand,
    operator_decision: GlobalStopOperatorDecision,
) -> GlobalStopEvaluation:
    evaluator_failed = False
    evaluation: GlobalStopEvaluation | None = None
    try:
        safe_state = _require_initialized_global_stop_state_for_mutation(state)
        safe_command = _require_initialized_global_stop_command_for_mutation(command)
        safe_decision = _require_initialized_global_stop_operator_decision_for_mutation(operator_decision)
        evaluation = evaluate_global_stop_update(safe_state, safe_command, safe_decision)
    except SQLiteMutationStoreError:
        raise
    except Exception:
        evaluator_failed = True
    if evaluator_failed:
        raise _mutation_failed()
    if type(evaluation) is not GlobalStopEvaluation:
        raise _database_integrity_failure()
    if evaluation.kind is GlobalStopEvaluationKind.PRE_APPLY_INVALID:
        raise _database_integrity_failure()
    if evaluation.kind in (GlobalStopEvaluationKind.ACCEPTED, GlobalStopEvaluationKind.DOMAIN_REJECTED):
        return evaluation
    raise _database_integrity_failure()


def _require_initialized_global_stop_command_for_mutation(value: object) -> GlobalStopCommand:
    try:
        if type(value) is not GlobalStopCommand:
            raise _database_integrity_failure()
        return GlobalStopCommand(
            schema_id=object.__getattribute__(value, "schema_id"),
            action=object.__getattribute__(value, "action"),
            idempotency_key=object.__getattribute__(value, "idempotency_key"),
            expected_version=object.__getattribute__(value, "expected_version"),
            source_stop_id=object.__getattribute__(value, "source_stop_id"),
            stop_id=object.__getattribute__(value, "stop_id"),
            reason_class=object.__getattribute__(value, "reason_class"),
            issuer_ref=object.__getattribute__(value, "issuer_ref"),
            issued_at=object.__getattribute__(value, "issued_at"),
            operator_decision_ref=object.__getattribute__(value, "operator_decision_ref"),
            canonical_command_digest=object.__getattribute__(value, "canonical_command_digest"),
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure()


def _require_initialized_global_stop_operator_decision_for_mutation(
    value: object,
) -> GlobalStopOperatorDecision:
    try:
        if type(value) is not GlobalStopOperatorDecision:
            raise _database_integrity_failure()
        return GlobalStopOperatorDecision(
            schema_id=object.__getattribute__(value, "schema_id"),
            decision_ref=object.__getattribute__(value, "decision_ref"),
            authorized=object.__getattribute__(value, "authorized"),
            reason=object.__getattribute__(value, "reason"),
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure()


def _require_initialized_global_stop_state_for_mutation(value: object) -> GlobalStopState:
    try:
        if type(value) is not GlobalStopState:
            raise _database_integrity_failure()
        return GlobalStopState(
            schema_id=object.__getattribute__(value, "schema_id"),
            version=object.__getattribute__(value, "version"),
            active=object.__getattribute__(value, "active"),
            stop_id=object.__getattribute__(value, "stop_id"),
            reason_class=object.__getattribute__(value, "reason_class"),
            issuer_ref=object.__getattribute__(value, "issuer_ref"),
            issued_at=object.__getattribute__(value, "issued_at"),
            operator_decision_ref=object.__getattribute__(value, "operator_decision_ref"),
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure()


def _require_initialized_global_stop_event_for_mutation(value: object) -> GlobalStopEvent:
    try:
        if type(value) is not GlobalStopEvent:
            raise _database_integrity_failure()
        return GlobalStopEvent(
            schema_id=object.__getattribute__(value, "schema_id"),
            event_ref=object.__getattribute__(value, "event_ref"),
            command_digest=object.__getattribute__(value, "command_digest"),
            idempotency_key=object.__getattribute__(value, "idempotency_key"),
            action=object.__getattribute__(value, "action"),
            source_version=object.__getattribute__(value, "source_version"),
            resulting_version=object.__getattribute__(value, "resulting_version"),
            outcome=object.__getattribute__(value, "outcome"),
            reason=object.__getattribute__(value, "reason"),
            operator_decision_ref=object.__getattribute__(value, "operator_decision_ref"),
            resulting_global_stop_ref=object.__getattribute__(value, "resulting_global_stop_ref"),
            resulting_status=object.__getattribute__(value, "resulting_status"),
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure()


def _require_initialized_global_stop_evaluation_for_mutation(value: object) -> GlobalStopEvaluation:
    try:
        if type(value) is not GlobalStopEvaluation:
            raise _database_integrity_failure()
        event = object.__getattribute__(value, "event")
        if event is not None:
            event = _require_initialized_global_stop_event_for_mutation(event)
        return GlobalStopEvaluation(
            kind=object.__getattribute__(value, "kind"),
            state=_require_initialized_global_stop_state_for_mutation(object.__getattribute__(value, "state")),
            event=event,
            reason=object.__getattribute__(value, "reason"),
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure()


def _dry_run_result_from_transition_resolution(
    resolution: CommittedTransition | TransitionConflict | _FreshTransitionEvaluation,
) -> _RollbackOnlyTransitionDryRunResult:
    if type(resolution) is CommittedTransition:
        return _RollbackOnlyTransitionDryRunResult(
            kind=_RollbackOnlyTransitionDryRunResultKind.EXACT_REPLAY,
            replayed_transition=resolution,
        )
    if type(resolution) is TransitionConflict:
        return _RollbackOnlyTransitionDryRunResult(
            kind=_RollbackOnlyTransitionDryRunResultKind.APPLY_CONFLICT,
            conflict=resolution,
        )
    if type(resolution) is _FreshTransitionEvaluation:
        evaluation = resolution.evaluation
        if evaluation.kind is TransitionEvaluationKind.ACCEPTED:
            return _RollbackOnlyTransitionDryRunResult(
                kind=_RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED,
                evaluation=evaluation,
            )
        if evaluation.kind is TransitionEvaluationKind.DOMAIN_REJECTED:
            return _RollbackOnlyTransitionDryRunResult(
                kind=_RollbackOnlyTransitionDryRunResultKind.DOMAIN_REJECTED_EVALUATION_NOT_PERSISTED,
                evaluation=evaluation,
            )
    raise _database_integrity_failure()


def _dry_run_conflict(conflict_class: str) -> _RollbackOnlyTransitionDryRunResult:
    return _RollbackOnlyTransitionDryRunResult(
        kind=_RollbackOnlyTransitionDryRunResultKind.APPLY_CONFLICT,
        conflict=TransitionConflict(conflict_class),
    )


def _create_sqlite_mutation_read_capability(
    *,
    connection: sqlite3.Connection,
    epoch: object,
    owner_pid: int,
    owner_thread: int,
    state: _MutationCapabilityState,
) -> _SQLiteMutationReadCapability:
    return _SQLiteMutationReadCapability(
        key=_CAPABILITY_CONSTRUCTION_KEY,
        connection=connection,
        epoch=epoch,
        owner_pid=owner_pid,
        owner_thread=owner_thread,
        state=state,
    )


def _invalidate_sqlite_mutation_read_capability(
    capability: _SQLiteMutationReadCapability,
    *,
    state: _MutationCapabilityState | None,
    epoch: object | None,
) -> SQLiteMutationStoreError | None:
    if type(capability) is not _SQLiteMutationReadCapability or type(state) is not _MutationCapabilityState:
        return _mutation_failed()
    try:
        state.invalidate(key=_CAPABILITY_CONSTRUCTION_KEY, epoch=epoch)
    except Exception:
        return _mutation_failed()
    return None


def _open_controller_connection(binding: _StateDatabaseAuthorityBinding) -> sqlite3.Connection:
    connection: sqlite3.Connection | None = None
    failure: SQLiteMutationStoreError | None = None
    try:
        connection = _open_bound_existing_sqlite_connection(binding, read_only=False)
    except _StateDatabaseAuthorityBindingMismatch:
        failure = _database_integrity_failure()
    except _StateDatabaseAuthorityBindingUnavailable:
        failure = _mutation_failed()
    except (sqlite3.Error, OSError, Exception):
        failure = _mutation_failed()
    if failure is not None:
        if connection is not None:
            _close_connection(connection)
        raise failure
    if not isinstance(connection, sqlite3.Connection):
        if connection is not None:
            _close_connection(connection)
        raise _mutation_failed()
    return connection


def _validate_bound_database_for_mutation(binding: _StateDatabaseAuthorityBinding) -> None:
    failure: SQLiteMutationStoreError | None = None
    try:
        _validate_state_database_authority_binding(binding)
    except _StateDatabaseAuthorityBindingMismatch:
        failure = _database_integrity_failure()
    except _StateDatabaseAuthorityBindingUnavailable:
        failure = _mutation_failed()
    except SQLiteStateError:
        failure = _database_integrity_failure()
    except Exception:
        failure = _mutation_failed()
    if failure is not None:
        raise failure


def _begin_immediate(connection: sqlite3.Connection) -> None:
    failed = False
    try:
        connection.execute("BEGIN IMMEDIATE")
        if connection.in_transaction is not True:
            failed = True
    except (sqlite3.Error, Exception):
        failed = True
    if failed:
        raise _mutation_failed()


def _validate_managed_connection_for_mutation(connection: sqlite3.Connection) -> None:
    integrity_failed = False
    operational_failed = False
    try:
        _validate_current_managed_connection(connection)
    except SQLiteStateError as exc:
        if _is_operational_validation_error(exc):
            operational_failed = True
        else:
            integrity_failed = True
    except sqlite3.Error as exc:
        if _sqlite_primary_result_code(exc) in _SQLITE_INTEGRITY_PRIMARY_RESULT_CODES:
            integrity_failed = True
        else:
            operational_failed = True
    except Exception:
        operational_failed = True
    if integrity_failed:
        raise _database_integrity_failure()
    if operational_failed:
        raise _mutation_failed()


def _read_writer_ownership_for_fencing(connection: sqlite3.Connection) -> _DurableWriterIssuance:
    rows = _fetch_writer_ownership_rows(connection)
    if type(rows) is not list:
        raise _database_integrity_failure()
    if any(type(row) is not tuple for row in rows):
        raise _database_integrity_failure()
    malformed = False
    try:
        issuance = _parse_writer_ownership_rows(rows)
    except ValueError:
        malformed = True
        issuance = None
    if malformed:
        raise _database_integrity_failure()
    if issuance is None or type(issuance) is not _DurableWriterIssuance:
        raise _database_integrity_failure()
    return issuance


def _fetch_writer_ownership_rows(connection: sqlite3.Connection) -> list[tuple[Any, ...]]:
    cursor: Any | None = None
    sqlite_failure: SQLiteMutationStoreError | None = None
    rows: Any | None = None
    try:
        cursor = connection.execute(_WRITER_OWNERSHIP_SELECT.sql)
        rows = cursor.fetchmany(2)
    except sqlite3.Error as raw_sqlite_error:
        sqlite_failure = _classify_sqlite_writer_select_error(raw_sqlite_error)
    except Exception:
        sqlite_failure = _mutation_failed()
    finally:
        if cursor is not None:
            close_failure = _close_cursor_safely(cursor)
            if sqlite_failure is None and close_failure is not None:
                sqlite_failure = close_failure
    if sqlite_failure is not None:
        raise sqlite_failure
    if rows is None:
        raise _database_integrity_failure()
    return rows


def _close_cursor_safely(cursor: Any) -> SQLiteMutationStoreError | None:
    try:
        cursor.close()
    except sqlite3.Error:
        return _mutation_failed()
    except Exception:
        return _mutation_failed()
    return None


def _require_exact_transition_write_plan(value: object) -> _TransitionWritePlan:
    if type(value) is not _TransitionWritePlan:
        raise _database_integrity_failure()
    try:
        return _TransitionWritePlan(
            planned_transition=value.planned_transition,
            event_insert=value.event_insert,
            accepted_work_item_cas=value.accepted_work_item_cas,
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure()


def _require_exact_transition_event_insert_values(value: object) -> _TransitionEventInsertValues:
    if type(value) is not _TransitionEventInsertValues:
        raise _database_integrity_failure()
    try:
        checked = _TransitionEventInsertValues(
            spec=value.spec,
            parameters=value.parameters,
            event=value.event,
            replay_record=value.replay_record,
            event_sequence=value.event_sequence,
            created_at=value.created_at,
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure()
    if type(checked.spec) is not type(_TRANSITION_EVENT_INSERT_SPEC) or checked.spec is not _TRANSITION_EVENT_INSERT_SPEC:
        raise _database_integrity_failure()
    if checked.spec.sql != _TRANSITION_EVENT_INSERT_SPEC.sql:
        raise _database_integrity_failure()
    return checked


def _require_exact_accepted_work_item_cas_values(value: object) -> _AcceptedWorkItemCasValues:
    if type(value) is not _AcceptedWorkItemCasValues:
        raise _database_integrity_failure()
    try:
        checked = _AcceptedWorkItemCasValues(
            spec=value.spec,
            parameters=value.parameters,
            source_record=value.source_record,
            resulting_record=value.resulting_record,
            updated_at=value.updated_at,
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure()
    if type(checked.spec) is not type(_ACCEPTED_WORK_ITEM_CAS_SPEC) or checked.spec is not _ACCEPTED_WORK_ITEM_CAS_SPEC:
        raise _database_integrity_failure()
    if checked.spec.sql != _ACCEPTED_WORK_ITEM_CAS_SPEC.sql:
        raise _database_integrity_failure()
    return checked


def _require_fresh_planned_transition(value: object) -> CommittedTransition:
    try:
        checked = CommittedTransition(record=value.record, event=value.event, replayed=value.replayed)  # type: ignore[union-attr]
    except Exception:
        raise _database_integrity_failure()
    if checked.replayed is not False:
        raise _database_integrity_failure()
    return checked


def _require_exact_global_stop_write_plan(value: object) -> _GlobalStopWritePlan:
    if type(value) is not _GlobalStopWritePlan:
        raise _database_integrity_failure()
    try:
        return _GlobalStopWritePlan(
            planned_update=value.planned_update,
            event_insert=value.event_insert,
            accepted_global_stop_current_cas=value.accepted_global_stop_current_cas,
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure()


def _require_exact_global_stop_event_insert_values(value: object) -> _GlobalStopEventInsertValues:
    if type(value) is not _GlobalStopEventInsertValues:
        raise _database_integrity_failure()
    try:
        checked = _GlobalStopEventInsertValues(
            spec=value.spec,
            parameters=value.parameters,
            event=value.event,
            replay_state=value.replay_state,
            event_sequence=value.event_sequence,
            created_at=value.created_at,
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure()
    if type(checked.spec) is not type(_GLOBAL_STOP_EVENT_INSERT_SPEC) or checked.spec is not _GLOBAL_STOP_EVENT_INSERT_SPEC:
        raise _database_integrity_failure()
    if checked.spec.sql != _GLOBAL_STOP_EVENT_INSERT_SPEC.sql:
        raise _database_integrity_failure()
    return checked


def _require_exact_accepted_global_stop_current_cas_values(
    value: object,
) -> _AcceptedGlobalStopCurrentCasValues:
    if type(value) is not _AcceptedGlobalStopCurrentCasValues:
        raise _database_integrity_failure()
    try:
        checked = _AcceptedGlobalStopCurrentCasValues(
            spec=value.spec,
            parameters=value.parameters,
            source_state=value.source_state,
            resulting_state=value.resulting_state,
            updated_at=value.updated_at,
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure()
    if (
        type(checked.spec) is not type(_ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SPEC)
        or checked.spec is not _ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SPEC
    ):
        raise _database_integrity_failure()
    if checked.spec.sql != _ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SPEC.sql:
        raise _database_integrity_failure()
    return checked


def _require_fresh_planned_global_stop_update(value: object) -> CommittedGlobalStopUpdate:
    if type(value) is not CommittedGlobalStopUpdate:
        raise _database_integrity_failure()
    try:
        checked = CommittedGlobalStopUpdate(
            state=value.state,
            event=value.event,
            replayed=value.replayed,
        )
    except Exception:
        raise _database_integrity_failure()
    if checked.replayed is not False:
        raise _database_integrity_failure()
    return checked


def _execute_transition_event_insert(
    connection: sqlite3.Connection,
    values: _TransitionEventInsertValues,
) -> None:
    if type(connection) is not sqlite3.Connection:
        raise _mutation_failed()
    checked = _require_exact_transition_event_insert_values(values)
    cursor: Any | None = None
    sqlite_failure: SQLiteMutationStoreError | None = None
    try:
        cursor = connection.execute(checked.spec.sql, checked.parameters)
    except sqlite3.Error as raw_sqlite_error:
        sqlite_failure = _classify_sqlite_write_error(raw_sqlite_error)
    except Exception:
        sqlite_failure = _mutation_failed()
    finally:
        if cursor is not None:
            close_failure = _close_cursor_safely(cursor)
            if sqlite_failure is None and close_failure is not None:
                sqlite_failure = close_failure
    if sqlite_failure is not None:
        raise sqlite_failure


def _execute_accepted_work_item_cas(
    connection: sqlite3.Connection,
    values: _AcceptedWorkItemCasValues,
) -> None:
    if type(connection) is not sqlite3.Connection:
        raise _mutation_failed()
    checked = _require_exact_accepted_work_item_cas_values(values)
    cursor: Any | None = None
    sqlite_failure: SQLiteMutationStoreError | None = None
    rowcount: Any | None = None
    try:
        cursor = connection.execute(checked.spec.sql, checked.parameters)
        rowcount = cursor.rowcount
    except sqlite3.Error as raw_sqlite_error:
        sqlite_failure = _classify_sqlite_write_error(raw_sqlite_error)
    except Exception:
        sqlite_failure = _mutation_failed()
    finally:
        if cursor is not None:
            close_failure = _close_cursor_safely(cursor)
            if sqlite_failure is None and close_failure is not None:
                sqlite_failure = close_failure
    if sqlite_failure is not None:
        raise sqlite_failure
    if type(rowcount) is not int or rowcount != 1:
        raise _database_integrity_failure()


def _execute_global_stop_event_insert(
    connection: sqlite3.Connection,
    values: _GlobalStopEventInsertValues,
) -> None:
    if type(connection) is not sqlite3.Connection:
        raise _mutation_failed()
    checked = _require_exact_global_stop_event_insert_values(values)
    cursor: Any | None = None
    sqlite_failure: SQLiteMutationStoreError | None = None
    try:
        cursor = connection.execute(checked.spec.sql, checked.parameters)
    except sqlite3.Error as raw_sqlite_error:
        sqlite_failure = _classify_sqlite_write_error(raw_sqlite_error)
    except Exception:
        sqlite_failure = _mutation_failed()
    finally:
        if cursor is not None:
            close_failure = _close_cursor_safely(cursor)
            if sqlite_failure is None and close_failure is not None:
                sqlite_failure = close_failure
    if sqlite_failure is not None:
        raise sqlite_failure


def _execute_accepted_global_stop_current_cas(
    connection: sqlite3.Connection,
    values: _AcceptedGlobalStopCurrentCasValues,
) -> None:
    if type(connection) is not sqlite3.Connection:
        raise _mutation_failed()
    checked = _require_exact_accepted_global_stop_current_cas_values(values)
    cursor: Any | None = None
    sqlite_failure: SQLiteMutationStoreError | None = None
    rowcount: Any | None = None
    try:
        cursor = connection.execute(checked.spec.sql, checked.parameters)
        rowcount = cursor.rowcount
    except sqlite3.Error as raw_sqlite_error:
        sqlite_failure = _classify_sqlite_write_error(raw_sqlite_error)
    except Exception:
        sqlite_failure = _mutation_failed()
    finally:
        if cursor is not None:
            close_failure = _close_cursor_safely(cursor)
            if sqlite_failure is None and close_failure is not None:
                sqlite_failure = close_failure
    if sqlite_failure is not None:
        raise sqlite_failure
    if type(rowcount) is not int or rowcount != 1:
        raise _database_integrity_failure()


def _rollback_transaction(connection: sqlite3.Connection) -> SQLiteMutationStoreError | None:
    try:
        connection.execute("ROLLBACK")
    except (sqlite3.Error, Exception):
        return _mutation_failed()
    return None


def _commit_transaction(connection: sqlite3.Connection) -> object | None:
    try:
        connection.execute("COMMIT")
    except sqlite3.Error:
        return _SQLITE_COMMIT_FAILED
    except Exception:
        return _SQLITE_COMMIT_FAILED
    return None


def _close_connection(connection: sqlite3.Connection) -> SQLiteMutationStoreError | None:
    try:
        connection.close()
    except (sqlite3.Error, Exception):
        return _mutation_failed()
    return None


def _classify_sqlite_writer_select_error(error: sqlite3.Error) -> SQLiteMutationStoreError:
    primary_code = _sqlite_primary_result_code(error)
    if primary_code in _SQLITE_INTEGRITY_PRIMARY_RESULT_CODES:
        return _database_integrity_failure()
    return _mutation_failed()


def _classify_sqlite_write_error(error: sqlite3.Error) -> SQLiteMutationStoreError:
    primary_code = _sqlite_primary_result_code(error)
    if primary_code in _SQLITE_INTEGRITY_PRIMARY_RESULT_CODES:
        return _database_integrity_failure()
    return _mutation_failed()


def _sqlite_primary_result_code(error: sqlite3.Error) -> int | None:
    code = getattr(error, "sqlite_errorcode", None)
    if type(code) is not int:
        return None
    return code & 0xFF


def _database_integrity_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def _mutation_failed() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)


def _commit_outcome_unknown() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN)


def _capability_error(
    reason: _MutationReadCapabilityFailureReason,
) -> _MutationReadCapabilityError:
    return _MutationReadCapabilityError(reason)
