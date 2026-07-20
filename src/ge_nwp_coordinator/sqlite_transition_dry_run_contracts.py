"""Pure private B3c3 rollback-only transition dry-run contracts."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
from types import MappingProxyType
from typing import Callable, TypeVar

from ge_nwp_coordinator.backlog import FiniteBacklog, WorkItem
from ge_nwp_coordinator.global_stop import GlobalStopReasonClass, GlobalStopState
from ge_nwp_coordinator.lease import (
    AuthorizationDecision,
    AuthorizationModel,
    LeaseIdentityValidation,
    LeaseRuntimeDecision,
    LeaseRuntimeStatus,
    LeaseRevocationState,
    Permission,
    StandingLease,
)
from ge_nwp_coordinator.models import ValidationIssue
from ge_nwp_coordinator.persistence_contracts import (
    B3AuthorizationModelHandling,
    classify_authorization_model_for_b3,
    validate_b3_work_item_authority_binding,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from ge_nwp_coordinator.state_machine import (
    DependencyDecision,
    TransitionCommand,
    TransitionEvaluation,
    TransitionEvaluationKind,
    TransitionEvent,
    TransitionEventOutcome,
    WorkItemRecord,
    WorkItemState,
)
from ge_nwp_coordinator.state_store import CommittedTransition, TransitionConflict

_T = TypeVar("_T")


class _TransitionDryRunPreflightFailureReason(str, Enum):
    INVALID_COMMAND = "transition_dry_run_invalid_command"
    UNSUPPORTED_COMMAND = "transition_dry_run_unsupported_command"


class _TransitionDryRunPreflightError(RuntimeError):
    """Safe private command-local dry-run preflight failure."""

    __slots__ = ("reason",)

    def __init__(self, reason: _TransitionDryRunPreflightFailureReason) -> None:
        if type(reason) is not _TransitionDryRunPreflightFailureReason:
            raise ValueError("invalid_field_type:transition_dry_run_preflight.reason") from None
        self.reason = reason
        super().__init__(reason.value)

    def __repr__(self) -> str:
        return "<_TransitionDryRunPreflightError>"


def _validate_transition_dry_run_preflight(command: TransitionCommand) -> TransitionCommand:
    if type(command) is not TransitionCommand:
        raise _TransitionDryRunPreflightError(_TransitionDryRunPreflightFailureReason.INVALID_COMMAND)
    invalid = False
    try:
        checked = _require_initialized_transition_command(command)
    except Exception:
        invalid = True
    if invalid:
        raise _TransitionDryRunPreflightError(_TransitionDryRunPreflightFailureReason.INVALID_COMMAND)
    if checked.target_state is not WorkItemState.READY and checked.dependency_decision_ref is not None:
        raise _TransitionDryRunPreflightError(_TransitionDryRunPreflightFailureReason.UNSUPPORTED_COMMAND)
    if checked.budget_cost != 0:
        raise _TransitionDryRunPreflightError(_TransitionDryRunPreflightFailureReason.UNSUPPORTED_COMMAND)
    return command


class _RollbackOnlyTransitionDryRunResultKind(str, Enum):
    EXACT_REPLAY = "exact_replay"
    APPLY_CONFLICT = "apply_conflict"
    ACCEPTED_EVALUATION_NOT_PERSISTED = "accepted_evaluation_not_persisted"
    DOMAIN_REJECTED_EVALUATION_NOT_PERSISTED = "domain_rejected_evaluation_not_persisted"


_B3C3_DRY_RUN_CONFLICT_CLASSES = frozenset(
    {
        "stale_writer_token",
        "idempotency_key_reuse_conflict",
        "work_item_not_found",
        "expected_version_conflict",
        "validation_failed",
    }
)


@dataclass(frozen=True, slots=True, repr=False)
class _RollbackOnlyTransitionDryRunResult:
    kind: _RollbackOnlyTransitionDryRunResultKind
    replayed_transition: CommittedTransition | None = field(default=None, repr=False)
    conflict: TransitionConflict | None = field(default=None, repr=False)
    evaluation: TransitionEvaluation | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        def validate() -> None:
            if type(self.kind) is not _RollbackOnlyTransitionDryRunResultKind:
                raise ValueError("invalid_kind")
            object.__setattr__(self, "kind", self.kind)
            payload_count = sum(
                payload is not None
                for payload in (
                    self.replayed_transition,
                    self.conflict,
                    self.evaluation,
                )
            )
            if payload_count != 1:
                raise ValueError("invalid_payload_count")
            if self.kind is _RollbackOnlyTransitionDryRunResultKind.EXACT_REPLAY:
                self._validate_exact_replay()
                return
            if self.kind is _RollbackOnlyTransitionDryRunResultKind.APPLY_CONFLICT:
                self._validate_apply_conflict()
                return
            if self.kind is _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED:
                self._validate_evaluation(TransitionEvaluationKind.ACCEPTED)
                return
            if self.kind is _RollbackOnlyTransitionDryRunResultKind.DOMAIN_REJECTED_EVALUATION_NOT_PERSISTED:
                self._validate_evaluation(TransitionEvaluationKind.DOMAIN_REJECTED)
                return
            raise ValueError("invalid_kind")

        _collapse_private_contract_failure(validate)

    def __repr__(self) -> str:
        return f"<_RollbackOnlyTransitionDryRunResult kind={self.kind.value}>"

    def _validate_exact_replay(self) -> None:
        replayed = self.replayed_transition
        if self.conflict is not None or self.evaluation is not None:
            raise _database_integrity_failure()
        replayed = _require_initialized_committed_transition(replayed)
        if replayed.replayed is not True:
            raise _database_integrity_failure()
        object.__setattr__(self, "replayed_transition", replayed)

    def _validate_apply_conflict(self) -> None:
        conflict = self.conflict
        if self.replayed_transition is not None or self.evaluation is not None:
            raise _database_integrity_failure()
        conflict = _require_initialized_transition_conflict(conflict)
        if conflict.conflict_class not in _B3C3_DRY_RUN_CONFLICT_CLASSES:
            raise _database_integrity_failure()
        object.__setattr__(self, "conflict", conflict)

    def _validate_evaluation(self, expected_kind: TransitionEvaluationKind) -> None:
        evaluation = self.evaluation
        if self.replayed_transition is not None or self.conflict is not None:
            raise _database_integrity_failure()
        evaluation = _require_initialized_transition_evaluation(evaluation)
        if evaluation.kind is not expected_kind:
            raise _database_integrity_failure()
        if evaluation.kind is TransitionEvaluationKind.PRE_APPLY_INVALID:
            raise _database_integrity_failure()
        object.__setattr__(self, "evaluation", evaluation)


@dataclass(frozen=True, slots=True, repr=False)
class _BoundTransitionAuthority:
    current_record: WorkItemRecord = field(repr=False)
    standing_lease: StandingLease = field(repr=False)
    lease_identity: LeaseIdentityValidation = field(repr=False)
    authorization: AuthorizationDecision = field(repr=False)
    dependency: DependencyDecision = field(repr=False)
    global_stop: GlobalStopState = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "current_record", _require_initialized_work_item_record(self.current_record))
        object.__setattr__(self, "standing_lease", _require_initialized_standing_lease(self.standing_lease))
        object.__setattr__(self, "lease_identity", _require_initialized_lease_identity(self.lease_identity))
        object.__setattr__(self, "authorization", _require_initialized_authorization(self.authorization))
        object.__setattr__(self, "dependency", _require_initialized_dependency(self.dependency))
        object.__setattr__(self, "global_stop", _require_initialized_global_stop(self.global_stop))

    def __repr__(self) -> str:
        return "<_BoundTransitionAuthority>"


def _bind_b3c3_transition_authority(
    *,
    command: TransitionCommand,
    current_record: WorkItemRecord,
    standing_lease: StandingLease,
    admitted_backlog: FiniteBacklog,
    lease_identity: LeaseIdentityValidation,
    authorization: AuthorizationDecision,
    dependency: DependencyDecision,
    global_stop: GlobalStopState,
) -> _BoundTransitionAuthority | TransitionConflict:
    ordinary_failure = False
    try:
        command = _require_initialized_transition_command(command)
        current_record = _require_initialized_work_item_record(current_record)
        standing_lease = _require_initialized_standing_lease(standing_lease)
        admitted_backlog = _require_initialized_finite_backlog(admitted_backlog)
        lease_identity = _require_initialized_lease_identity(lease_identity)
        authorization = _require_initialized_authorization(authorization)
        dependency = _require_initialized_dependency(dependency)
        global_stop = _require_initialized_global_stop(global_stop)

        validate_b3_work_item_authority_binding(standing_lease, admitted_backlog, current_record)
        _require_lease_identity_authority(standing_lease=standing_lease, lease_identity=lease_identity)
        _require_authorization_authority(
            standing_lease=standing_lease,
            lease_identity=lease_identity,
            authorization=authorization,
        )

        if command.work_item_id != current_record.work_item_id:
            return _validation_failed()
        if command.lease_identity_decision_ref != lease_identity.decision_ref:
            return _validation_failed()
        if command.authorization_decision_ref != authorization.decision_ref:
            return _validation_failed()
        if classify_authorization_model_for_b3(authorization) is B3AuthorizationModelHandling.UNSUPPORTED_AUTHORITATIVE_MODEL:
            return _validation_failed()

        dependency_conflict = _bind_dependency(command=command, current_record=current_record, dependency=dependency)
        if dependency_conflict is not None:
            return dependency_conflict
        if command.global_stop_ref != global_stop.stop_ref or command.global_stop_version != global_stop.version:
            return _validation_failed()

        return _BoundTransitionAuthority(
            current_record=current_record,
            standing_lease=standing_lease,
            lease_identity=lease_identity,
            authorization=authorization,
            dependency=dependency,
            global_stop=global_stop,
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        ordinary_failure = True
    if ordinary_failure:
        raise _database_integrity_failure()
    raise _database_integrity_failure()


def _require_initialized_transition_command(value: object) -> TransitionCommand:
    state = _candidate_state_snapshot(value, TransitionCommand)
    def reconstruct() -> TransitionCommand:
        target_state = _field(state, "target_state")
        evidence_refs = _field(state, "evidence_refs")
        dependency_decision_ref = _field(state, "dependency_decision_ref")
        if type(target_state) is not WorkItemState:
            raise ValueError("invalid_target_state")
        if type(evidence_refs) is not tuple:
            raise ValueError("invalid_evidence_refs")
        for evidence_ref in evidence_refs:
            if type(evidence_ref) is not str:
                raise ValueError("invalid_evidence_ref")
        if dependency_decision_ref is not None and type(dependency_decision_ref) is not str:
            raise ValueError("invalid_dependency_ref")
        return TransitionCommand(
            schema_id=_require_exact_str(_field(state, "schema_id")),
            work_item_id=_require_exact_str(_field(state, "work_item_id")),
            idempotency_key=_require_exact_str(_field(state, "idempotency_key")),
            expected_version=_require_exact_int(_field(state, "expected_version")),
            target_state=target_state,
            lease_identity_decision_ref=_require_exact_str(_field(state, "lease_identity_decision_ref")),
            authorization_decision_ref=_require_exact_str(_field(state, "authorization_decision_ref")),
            global_stop_ref=_require_exact_str(_field(state, "global_stop_ref")),
            global_stop_version=_require_exact_int(_field(state, "global_stop_version")),
            dependency_decision_ref=dependency_decision_ref,
            evidence_refs=evidence_refs,
            safe_failure_class=_require_optional_exact_str(_field(state, "safe_failure_class")),
            budget_cost=_require_exact_int(_field(state, "budget_cost")),
            canonical_command_digest=_require_exact_str(_field(state, "canonical_command_digest")),
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_work_item_record(value: object) -> WorkItemRecord:
    state = _candidate_state_snapshot(value, WorkItemRecord)
    def reconstruct() -> WorkItemRecord:
        work_item_state = _field(state, "state")
        if type(work_item_state) is not WorkItemState:
            raise ValueError("invalid_state")
        return WorkItemRecord(
            schema_id=_require_exact_str(_field(state, "schema_id")),
            work_item_id=_require_exact_str(_field(state, "work_item_id")),
            lease_id=_require_exact_str(_field(state, "lease_id")),
            backlog_id=_require_exact_str(_field(state, "backlog_id")),
            state=work_item_state,
            version=_require_exact_int(_field(state, "version")),
            attempt_count=_require_exact_int(_field(state, "attempt_count")),
            repair_count=_require_exact_int(_field(state, "repair_count")),
            budget_consumed=_require_exact_int(_field(state, "budget_consumed")),
            budget_limit=_require_exact_int(_field(state, "budget_limit")),
            max_attempts=_require_exact_int(_field(state, "max_attempts")),
            max_repairs=_require_exact_int(_field(state, "max_repairs")),
            cleanup_required=_require_exact_bool(_field(state, "cleanup_required")),
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_lease_runtime(value: object) -> LeaseRuntimeDecision:
    state = _candidate_state_snapshot(value, LeaseRuntimeDecision)

    def reconstruct() -> LeaseRuntimeDecision:
        status = _field(state, "status")
        if type(status) is not LeaseRuntimeStatus:
            raise ValueError("invalid_runtime_status")
        return LeaseRuntimeDecision(
            schema_id=_require_exact_str(_field(state, "schema_id")),
            lease_ref=_require_exact_str(_field(state, "lease_ref")),
            evaluated_at=_require_exact_str(_field(state, "evaluated_at")),
            status=status,
            reason=_require_exact_str(_field(state, "reason")),
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_transition_event(value: object) -> TransitionEvent:
    state = _candidate_state_snapshot(value, TransitionEvent)
    def reconstruct() -> TransitionEvent:
        source_state = _field(state, "source_state")
        resulting_state = _field(state, "resulting_state")
        outcome = _field(state, "outcome")
        evidence_refs = _field(state, "evidence_refs")
        if type(source_state) is not WorkItemState:
            raise ValueError("invalid_source_state")
        if type(resulting_state) is not WorkItemState:
            raise ValueError("invalid_resulting_state")
        if type(outcome) is not TransitionEventOutcome:
            raise ValueError("invalid_outcome")
        evidence_refs = _require_exact_str_tuple(evidence_refs)
        lease_runtime = _require_initialized_lease_runtime(_field(state, "lease_runtime"))
        return TransitionEvent(
            schema_id=_require_exact_str(_field(state, "schema_id")),
            event_ref=_require_exact_str(_field(state, "event_ref")),
            work_item_id=_require_exact_str(_field(state, "work_item_id")),
            lease_id=_require_exact_str(_field(state, "lease_id")),
            command_digest=_require_exact_str(_field(state, "command_digest")),
            idempotency_key=_require_exact_str(_field(state, "idempotency_key")),
            source_state=source_state,
            source_version=_require_exact_int(_field(state, "source_version")),
            resulting_state=resulting_state,
            resulting_version=_require_exact_int(_field(state, "resulting_version")),
            outcome=outcome,
            reason=_require_exact_str(_field(state, "reason")),
            evidence_refs=evidence_refs,
            budget_cost_delta=_require_exact_int(_field(state, "budget_cost_delta")),
            attempt_count_delta=_require_exact_int(_field(state, "attempt_count_delta")),
            repair_count_delta=_require_exact_int(_field(state, "repair_count_delta")),
            lease_identity_decision_ref=_require_exact_str(_field(state, "lease_identity_decision_ref")),
            authorization_decision_ref=_require_exact_str(_field(state, "authorization_decision_ref")),
            dependency_decision_ref=_require_optional_exact_str(_field(state, "dependency_decision_ref")),
            lease_runtime=lease_runtime,
            global_stop_ref=_require_exact_str(_field(state, "global_stop_ref")),
            global_stop_version=_require_exact_int(_field(state, "global_stop_version")),
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_transition_conflict(value: object) -> TransitionConflict:
    state = _candidate_state_snapshot(value, TransitionConflict)
    def reconstruct() -> TransitionConflict:
        conflict_class = _field(state, "conflict_class")
        if type(conflict_class) is not str:
            raise ValueError("invalid_conflict_class")
        return TransitionConflict(conflict_class)

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_committed_transition(value: object) -> CommittedTransition:
    state = _candidate_state_snapshot(value, CommittedTransition)
    def reconstruct() -> CommittedTransition:
        replayed = _field(state, "replayed")
        if type(replayed) is not bool:
            raise ValueError("invalid_replayed")
        record = _require_initialized_work_item_record(_field(state, "record"))
        event = _require_initialized_transition_event(_field(state, "event"))
        return CommittedTransition(record=record, event=event, replayed=replayed)

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_transition_evaluation(value: object) -> TransitionEvaluation:
    state = _candidate_state_snapshot(value, TransitionEvaluation)
    def reconstruct() -> TransitionEvaluation:
        kind = _field(state, "kind")
        reason = _field(state, "reason")
        raw_event = _field(state, "event")
        if type(kind) is not TransitionEvaluationKind:
            raise ValueError("invalid_evaluation_kind")
        if type(reason) is not str:
            raise ValueError("invalid_evaluation_reason")
        record = _require_initialized_work_item_record(_field(state, "record"))
        if kind is TransitionEvaluationKind.PRE_APPLY_INVALID:
            if raw_event is not None:
                raise ValueError("invalid_pre_apply_event")
            event = None
        else:
            event = _require_initialized_transition_event(raw_event)
        return TransitionEvaluation(kind=kind, reason=reason, record=record, event=event)

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_standing_lease(value: object) -> StandingLease:
    state = _candidate_state_snapshot(value, StandingLease)
    def reconstruct() -> StandingLease:
        revocation_state = _field(state, "revocation_state")
        if type(revocation_state) is not LeaseRevocationState:
            raise ValueError("invalid_revocation_state")
        permissions = (
            _field(state, "local_commit_permission"),
            _field(state, "publication_permission"),
            _field(state, "cross_repo_permission"),
            _field(state, "maintenance_permission"),
        )
        for permission in permissions:
            if type(permission) is not Permission:
                raise ValueError("invalid_permission")
        return StandingLease(
            schema_id=_require_exact_str(_field(state, "schema_id")),
            schema_version=_require_exact_int(_field(state, "schema_version")),
            lease_id=_require_exact_str(_field(state, "lease_id")),
            issuer_label=_require_exact_str(_field(state, "issuer_label")),
            issued_at=_require_exact_str(_field(state, "issued_at")),
            valid_from=_require_exact_str(_field(state, "valid_from")),
            expires_at=_require_exact_str(_field(state, "expires_at")),
            revocation_state=revocation_state,
            revocation_reference=_require_optional_exact_str(_field(state, "revocation_reference")),
            subject=_require_exact_str(_field(state, "subject")),
            repo_identity=_require_exact_mapping_proxy(_field(state, "repo_identity")),
            branch_policy=_require_exact_mapping_proxy(_field(state, "branch_policy")),
            allowed_paths=_require_exact_str_tuple(_field(state, "allowed_paths")),
            forbidden_path_policy_identity=_require_exact_str(_field(state, "forbidden_path_policy_identity")),
            task_classes=_require_exact_str_tuple(_field(state, "task_classes")),
            risk_lanes=_require_exact_str_tuple(_field(state, "risk_lanes")),
            finite_backlog_reference=_require_exact_str(_field(state, "finite_backlog_reference")),
            finite_backlog_digest=_require_exact_str(_field(state, "finite_backlog_digest")),
            max_work_items=_require_exact_int(_field(state, "max_work_items")),
            max_concurrency=_require_exact_int(_field(state, "max_concurrency")),
            max_attempts=_require_exact_int(_field(state, "max_attempts")),
            max_repairs=_require_exact_int(_field(state, "max_repairs")),
            compute_api_budget=_require_exact_mapping_proxy(_field(state, "compute_api_budget")),
            wall_clock_budget_seconds=_require_exact_int(_field(state, "wall_clock_budget_seconds")),
            validation_requirements=_require_exact_str_tuple(_field(state, "validation_requirements")),
            audit_requirements=_require_exact_str_tuple(_field(state, "audit_requirements")),
            local_commit_permission=permissions[0],
            publication_permission=permissions[1],
            cross_repo_permission=permissions[2],
            maintenance_permission=permissions[3],
            cleanup_requirements=_require_exact_str_tuple(_field(state, "cleanup_requirements")),
            reporting_cadence=_require_exact_str(_field(state, "reporting_cadence")),
            retention_policy=_require_exact_str(_field(state, "retention_policy")),
            global_stop_reference=_require_exact_str(_field(state, "global_stop_reference")),
            canonical_digest_metadata=_require_exact_mapping_proxy(_field(state, "canonical_digest_metadata")),
            authorization_mechanism=_require_exact_mapping_proxy(_field(state, "authorization_mechanism")),
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_finite_backlog(value: object) -> FiniteBacklog:
    state = _candidate_state_snapshot(value, FiniteBacklog)
    def reconstruct() -> FiniteBacklog:
        work_items = _field(state, "work_items")
        if type(work_items) is not tuple:
            raise ValueError("invalid_work_items")
        safe_items = tuple(_require_initialized_work_item(item) for item in work_items)
        return FiniteBacklog.from_dict(
            {
                "schema_id": _require_exact_str(_field(state, "schema_id")),
                "schema_version": _require_exact_int(_field(state, "schema_version")),
                "backlog_id": _require_exact_str(_field(state, "backlog_id")),
                "lease_reference": _require_exact_str(_field(state, "lease_reference")),
                "work_items": [WorkItem.to_dict(item) for item in safe_items],
                "content_digest": _require_exact_str(_field(state, "content_digest")),
            }
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_lease_identity(value: object) -> LeaseIdentityValidation:
    state = _candidate_state_snapshot(value, LeaseIdentityValidation)
    def reconstruct() -> LeaseIdentityValidation:
        identity_valid = _field(state, "identity_valid")
        digest = _field(state, "digest")
        issues = _field(state, "issues")
        decision_ref = _field(state, "decision_ref")
        lease_ref = _field(state, "lease_ref")
        if type(identity_valid) is not bool:
            raise ValueError("invalid_identity_valid")
        if digest is not None and type(digest) is not str:
            raise ValueError("invalid_digest")
        if type(issues) is not tuple:
            raise ValueError("invalid_issues")
        safe_issues = []
        for issue in issues:
            safe_issues.append(_require_initialized_validation_issue(issue))
        if type(decision_ref) is not str or type(lease_ref) is not str:
            raise ValueError("invalid_refs")
        return LeaseIdentityValidation(
            identity_valid=identity_valid,
            digest=digest,
            issues=tuple(safe_issues),
            decision_ref=decision_ref,
            lease_ref=lease_ref,
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_validation_issue(value: object) -> ValidationIssue:
    state = _candidate_state_snapshot(value, ValidationIssue)
    def reconstruct() -> ValidationIssue:
        return ValidationIssue(
            field=_require_exact_str(_field(state, "field")),
            reason=_require_exact_str(_field(state, "reason")),
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_authorization(value: object) -> AuthorizationDecision:
    state = _candidate_state_snapshot(value, AuthorizationDecision)
    def reconstruct() -> AuthorizationDecision:
        authorization_model = _field(state, "authorization_model")
        if type(authorization_model) is not AuthorizationModel:
            raise ValueError("invalid_authorization_model")
        return AuthorizationDecision(
            schema_id=_require_exact_str(_field(state, "schema_id")),
            decision_ref=_require_exact_str(_field(state, "decision_ref")),
            lease_ref=_require_exact_str(_field(state, "lease_ref")),
            lease_identity_decision_ref=_require_exact_str(_field(state, "lease_identity_decision_ref")),
            lease_identity_valid=_require_exact_bool(_field(state, "lease_identity_valid")),
            authorization_model=authorization_model,
            authorized=_require_exact_bool(_field(state, "authorized")),
            executable=_require_exact_bool(_field(state, "executable")),
            reason=_require_exact_str(_field(state, "reason")),
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_dependency(value: object) -> DependencyDecision:
    state = _candidate_state_snapshot(value, DependencyDecision)
    def reconstruct() -> DependencyDecision:
        return DependencyDecision(
            schema_id=_require_exact_str(_field(state, "schema_id")),
            decision_ref=_require_exact_str(_field(state, "decision_ref")),
            work_item_id=_require_optional_exact_str(_field(state, "work_item_id")),
            dependencies_satisfied=_require_exact_bool(_field(state, "dependencies_satisfied")),
            reason=_require_exact_str(_field(state, "reason")),
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_global_stop(value: object) -> GlobalStopState:
    state = _candidate_state_snapshot(value, GlobalStopState)
    def reconstruct() -> GlobalStopState:
        reason_class = _field(state, "reason_class")
        if reason_class is not None and type(reason_class) is not GlobalStopReasonClass:
            raise ValueError("invalid_global_stop_reason")
        return GlobalStopState(
            schema_id=_require_exact_str(_field(state, "schema_id")),
            version=_require_exact_int(_field(state, "version")),
            active=_require_exact_bool(_field(state, "active")),
            stop_id=_require_optional_exact_str(_field(state, "stop_id")),
            reason_class=reason_class,
            issuer_ref=_require_optional_exact_str(_field(state, "issuer_ref")),
            issued_at=_require_optional_exact_str(_field(state, "issued_at")),
            operator_decision_ref=_require_optional_exact_str(_field(state, "operator_decision_ref")),
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_work_item(value: object) -> WorkItem:
    state = _candidate_state_snapshot(value, WorkItem)
    def reconstruct() -> WorkItem:
        return WorkItem(
            work_item_id=_require_exact_str(_field(state, "work_item_id")),
            objective_label=_require_exact_str(_field(state, "objective_label")),
            opaque_private_assignment_ref=_require_exact_str(_field(state, "opaque_private_assignment_ref")),
            repo=_require_exact_str(_field(state, "repo")),
            branches=_require_exact_str_tuple(_field(state, "branches")),
            allowed_paths=_require_exact_str_tuple(_field(state, "allowed_paths")),
            task_class=_require_exact_str(_field(state, "task_class")),
            risk_lane=_require_exact_str(_field(state, "risk_lane")),
            required_validation_profile=_require_exact_str(_field(state, "required_validation_profile")),
            budget_allocation=_require_exact_mapping_proxy(_field(state, "budget_allocation")),
            dependencies=_require_exact_str_tuple(_field(state, "dependencies")),
            stop_conditions=_require_exact_str_tuple(_field(state, "stop_conditions")),
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_lease_identity_authority(
    *,
    standing_lease: StandingLease,
    lease_identity: LeaseIdentityValidation,
) -> None:
    expected = StandingLease.validate_identity(standing_lease)
    if lease_identity.lease_ref != standing_lease.lease_id:
        raise _database_integrity_failure()
    if lease_identity.decision_ref != expected.decision_ref:
        raise _database_integrity_failure()
    if lease_identity.lease_ref != expected.lease_ref:
        raise _database_integrity_failure()
    if lease_identity.identity_valid != expected.identity_valid:
        raise _database_integrity_failure()
    if lease_identity.digest != expected.digest:
        raise _database_integrity_failure()
    if lease_identity.issues != expected.issues:
        raise _database_integrity_failure()


def _require_authorization_authority(
    *,
    standing_lease: StandingLease,
    lease_identity: LeaseIdentityValidation,
    authorization: AuthorizationDecision,
) -> None:
    if authorization.lease_ref != standing_lease.lease_id:
        raise _database_integrity_failure()
    if authorization.lease_identity_decision_ref != lease_identity.decision_ref:
        raise _database_integrity_failure()
    if authorization.lease_identity_valid != lease_identity.identity_valid:
        raise _database_integrity_failure()


def _bind_dependency(
    *,
    command: TransitionCommand,
    current_record: WorkItemRecord,
    dependency: DependencyDecision,
) -> TransitionConflict | None:
    if command.target_state is WorkItemState.READY:
        if command.dependency_decision_ref is None:
            return _validation_failed()
        if command.dependency_decision_ref != dependency.decision_ref:
            return _validation_failed()
        if dependency.work_item_id != current_record.work_item_id:
            return _validation_failed()
        return None
    if command.dependency_decision_ref is not None:
        return _validation_failed()
    if dependency != DependencyDecision():
        return _validation_failed()
    return None


def _require_exact_type(value: object, expected: type[object]) -> None:
    if type(value) is not expected:
        raise _database_integrity_failure()


def _candidate_state_snapshot(value: object, expected: type[object]) -> dict[str, object]:
    _require_exact_type(value, expected)
    failed = False
    try:
        raw_state = object.__getattribute__(value, "__dict__")
        expected_fields = fields(expected)
    except Exception:
        failed = True
    if failed:
        raise _database_integrity_failure()
    if type(raw_state) is not dict:
        raise _database_integrity_failure()
    failed = False
    try:
        raw_items = tuple(dict.items(raw_state))
    except Exception:
        failed = True
    if failed:
        raise _database_integrity_failure()
    for key, _field_value in raw_items:
        if type(key) is not str:
            raise _database_integrity_failure()
    trusted_state = {key: field_value for key, field_value in raw_items}
    for model_field in expected_fields:
        if model_field.name not in trusted_state:
            raise _database_integrity_failure()
    return trusted_state


def _field(state: dict[str, object], name: str) -> object:
    return state[name]


def _require_exact_str(value: object) -> str:
    if type(value) is not str:
        raise ValueError("invalid_string")
    return value


def _require_optional_exact_str(value: object) -> str | None:
    if value is None:
        return None
    return _require_exact_str(value)


def _require_exact_bool(value: object) -> bool:
    if type(value) is not bool:
        raise ValueError("invalid_bool")
    return value


def _require_exact_int(value: object) -> int:
    if type(value) is not int:
        raise ValueError("invalid_int")
    return value


def _require_exact_str_tuple(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("invalid_tuple")
    for item in value:
        if type(item) is not str:
            raise ValueError("invalid_tuple_item")
    return value


def _require_exact_mapping_proxy(value: object) -> MappingProxyType:
    if type(value) is not MappingProxyType:
        raise ValueError("invalid_mapping")
    return value


def _validation_failed() -> TransitionConflict:
    return TransitionConflict("validation_failed")


def _collapse_private_contract_failure(callback: Callable[[], _T]) -> _T:
    ordinary_failure = False
    try:
        return callback()
    except SQLiteMutationStoreError:
        raise
    except Exception:
        ordinary_failure = True
    if ordinary_failure:
        raise _database_integrity_failure()
    raise _database_integrity_failure()


def _database_integrity_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)
