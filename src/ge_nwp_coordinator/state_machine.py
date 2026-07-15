"""Pure A2 work-item transition engine."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from ge_nwp_coordinator.global_stop import (
    GlobalStopState,
    GlobalStopTransitionClass,
    enforce_global_stop,
)

WORK_ITEM_STATE_SCHEMA_ID = "governed-execution.nwp-work-item-state.v1"


class WorkItemState(str, Enum):
    PROPOSED = "proposed"
    LEASE_ADMITTED = "lease_admitted"
    READY = "ready"
    CYCLE_STARTING = "cycle_starting"
    WORKER_RUNNING = "worker_running"
    VALIDATING = "validating"
    AUDITING = "auditing"
    COMMIT_ELIGIBLE = "commit_eligible"
    LOCAL_COMMIT_COMPLETED = "local_commit_completed"
    REPAIR_ADMITTED = "repair_admitted"
    REPAIR_RUNNING = "repair_running"
    BLOCKED = "blocked"
    FAILED = "failed"
    EXHAUSTED = "exhausted"
    LEASE_EXPIRED = "lease_expired"
    CANCELED_REVOKED = "canceled_revoked"
    CLEANUP_PENDING = "cleanup_pending"
    CLEANUP_COMPLETED = "cleanup_completed"


TERMINAL_STATES = frozenset(
    {
        WorkItemState.LOCAL_COMMIT_COMPLETED,
        WorkItemState.FAILED,
        WorkItemState.EXHAUSTED,
        WorkItemState.LEASE_EXPIRED,
        WorkItemState.CANCELED_REVOKED,
        WorkItemState.CLEANUP_COMPLETED,
    }
)

ALLOWED_PREDECESSORS: dict[WorkItemState, frozenset[WorkItemState]] = {
    WorkItemState.LEASE_ADMITTED: frozenset({WorkItemState.PROPOSED}),
    WorkItemState.READY: frozenset(
        {WorkItemState.LEASE_ADMITTED, WorkItemState.BLOCKED, WorkItemState.CLEANUP_COMPLETED}
    ),
    WorkItemState.CYCLE_STARTING: frozenset({WorkItemState.READY}),
    WorkItemState.WORKER_RUNNING: frozenset({WorkItemState.CYCLE_STARTING}),
    WorkItemState.VALIDATING: frozenset({WorkItemState.WORKER_RUNNING, WorkItemState.REPAIR_RUNNING}),
    WorkItemState.AUDITING: frozenset({WorkItemState.VALIDATING}),
    WorkItemState.COMMIT_ELIGIBLE: frozenset({WorkItemState.AUDITING}),
    WorkItemState.LOCAL_COMMIT_COMPLETED: frozenset({WorkItemState.COMMIT_ELIGIBLE}),
    WorkItemState.REPAIR_ADMITTED: frozenset(
        {WorkItemState.AUDITING, WorkItemState.VALIDATING, WorkItemState.FAILED}
    ),
    WorkItemState.REPAIR_RUNNING: frozenset({WorkItemState.REPAIR_ADMITTED}),
    WorkItemState.BLOCKED: frozenset(set(WorkItemState) - {WorkItemState.CLEANUP_COMPLETED}),
    WorkItemState.FAILED: frozenset(
        {
            WorkItemState.CYCLE_STARTING,
            WorkItemState.WORKER_RUNNING,
            WorkItemState.VALIDATING,
            WorkItemState.AUDITING,
            WorkItemState.REPAIR_RUNNING,
        }
    ),
    WorkItemState.EXHAUSTED: frozenset(
        {WorkItemState.FAILED, WorkItemState.BLOCKED, WorkItemState.REPAIR_ADMITTED}
    ),
    WorkItemState.LEASE_EXPIRED: frozenset(set(WorkItemState) - {WorkItemState.CLEANUP_COMPLETED}),
    WorkItemState.CANCELED_REVOKED: frozenset(set(WorkItemState) - {WorkItemState.CLEANUP_COMPLETED}),
    WorkItemState.CLEANUP_PENDING: frozenset(
        {
            WorkItemState.FAILED,
            WorkItemState.BLOCKED,
            WorkItemState.EXHAUSTED,
            WorkItemState.LEASE_EXPIRED,
            WorkItemState.CANCELED_REVOKED,
            WorkItemState.LOCAL_COMMIT_COMPLETED,
        }
    ),
    WorkItemState.CLEANUP_COMPLETED: frozenset({WorkItemState.CLEANUP_PENDING}),
}

EVIDENCE_REQUIRED_STATES = frozenset(
    {
        WorkItemState.VALIDATING,
        WorkItemState.AUDITING,
        WorkItemState.COMMIT_ELIGIBLE,
        WorkItemState.LOCAL_COMMIT_COMPLETED,
        WorkItemState.FAILED,
        WorkItemState.EXHAUSTED,
        WorkItemState.CANCELED_REVOKED,
        WorkItemState.CLEANUP_COMPLETED,
    }
)


@dataclass(frozen=True)
class TransitionContext:
    lease_identity_valid: bool
    authorized: bool
    executable: bool
    global_stop: GlobalStopState = GlobalStopState()
    lease_expired: bool = False
    lease_revoked: bool = False
    dependencies_satisfied: bool = True


@dataclass(frozen=True)
class TransitionRequest:
    target_state: WorkItemState
    expected_version: int
    idempotency_key: str
    evidence_refs: tuple[str, ...] = ()
    safe_failure_class: str | None = None
    budget_cost: int = 0


@dataclass(frozen=True)
class TransitionReceipt:
    idempotency_key: str
    source_state: WorkItemState
    target_state: WorkItemState
    previous_version: int
    new_version: int
    accepted: bool
    reason: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkItemRecord:
    work_item_id: str
    lease_id: str
    backlog_id: str
    state: WorkItemState = WorkItemState.PROPOSED
    version: int = 0
    attempt_count: int = 0
    repair_count: int = 0
    budget_consumed: int = 0
    budget_limit: int = 0
    max_attempts: int = 1
    max_repairs: int = 0
    cleanup_required: bool = False
    receipts: tuple[TransitionReceipt, ...] = ()
    schema_id: str = WORK_ITEM_STATE_SCHEMA_ID

    @property
    def terminal(self) -> bool:
        return self.state in TERMINAL_STATES


@dataclass(frozen=True)
class TransitionResult:
    accepted: bool
    reason: str
    record: WorkItemRecord
    receipt: TransitionReceipt


def transition(
    record: WorkItemRecord,
    request: TransitionRequest,
    context: TransitionContext,
) -> TransitionResult:
    duplicate = _receipt_for_key(record, request.idempotency_key)
    if duplicate is not None:
        if duplicate.target_state is not request.target_state:
            return _blocked(record, request, "idempotency_key_reuse_conflict")
        return TransitionResult(
            accepted=duplicate.accepted,
            reason=duplicate.reason,
            record=record,
            receipt=duplicate,
        )
    if request.expected_version != record.version:
        return _blocked(record, request, "expected_version_mismatch")
    if request.budget_cost < 0:
        return _blocked(record, request, "budget_cost_malformed")
    if not context.lease_identity_valid:
        return _blocked(record, request, "lease_identity_invalid")
    if context.lease_expired and request.target_state is not WorkItemState.LEASE_EXPIRED:
        return _blocked(record, request, "lease_expired")
    if context.lease_revoked and request.target_state is not WorkItemState.CANCELED_REVOKED:
        return _blocked(record, request, "lease_revoked")
    if request.target_state not in ALLOWED_PREDECESSORS:
        return _blocked(record, request, "unsupported_target_state")
    global_stop_reason = _global_stop_block(request.target_state, context.global_stop)
    if global_stop_reason is not None:
        return _blocked(record, request, global_stop_reason)
    stage_reason = _stage_enabled(request.target_state)
    if stage_reason is not None:
        return _blocked(record, request, stage_reason)
    if _terminal_blocks(record, request.target_state):
        return _blocked(record, request, "terminal_state")
    if record.state not in ALLOWED_PREDECESSORS[request.target_state]:
        return _blocked(record, request, "invalid_predecessor")
    if request.target_state is WorkItemState.LEASE_ADMITTED and not context.authorized:
        return _blocked(record, request, "lease_not_authorized")
    if _requires_executable_authority(request.target_state) and not context.executable:
        return _blocked(record, request, "not_executable")
    if request.target_state is WorkItemState.READY and not context.dependencies_satisfied:
        return _blocked(record, request, "dependencies_not_satisfied")
    if request.target_state in EVIDENCE_REQUIRED_STATES and not request.evidence_refs:
        return _blocked(record, request, "evidence_required")
    if request.target_state in {WorkItemState.BLOCKED, WorkItemState.FAILED} and not request.safe_failure_class:
        return _blocked(record, request, "safe_failure_class_required")
    if record.budget_limit and record.budget_consumed + request.budget_cost > record.budget_limit:
        return _blocked(record, request, "budget_exhausted")
    if request.target_state is WorkItemState.CYCLE_STARTING and record.attempt_count >= record.max_attempts:
        return _blocked(record, request, "attempts_exhausted")
    if request.target_state is WorkItemState.REPAIR_ADMITTED and record.repair_count >= record.max_repairs:
        return _blocked(record, request, "repairs_exhausted")

    new_record = _advance(record, request)
    receipt = TransitionReceipt(
        idempotency_key=request.idempotency_key,
        source_state=record.state,
        target_state=request.target_state,
        previous_version=record.version,
        new_version=new_record.version,
        accepted=True,
        reason="transition_accepted",
        evidence_refs=request.evidence_refs,
    )
    new_record = replace(new_record, receipts=new_record.receipts + (receipt,))
    return TransitionResult(accepted=True, reason=receipt.reason, record=new_record, receipt=receipt)


def _advance(record: WorkItemRecord, request: TransitionRequest) -> WorkItemRecord:
    attempt_count = record.attempt_count
    repair_count = record.repair_count
    cleanup_required = record.cleanup_required
    if request.target_state is WorkItemState.CYCLE_STARTING:
        attempt_count += 1
    if request.target_state is WorkItemState.REPAIR_ADMITTED:
        repair_count += 1
    if request.target_state in {
        WorkItemState.FAILED,
        WorkItemState.BLOCKED,
        WorkItemState.EXHAUSTED,
        WorkItemState.LEASE_EXPIRED,
        WorkItemState.CANCELED_REVOKED,
        WorkItemState.LOCAL_COMMIT_COMPLETED,
    }:
        cleanup_required = True
    if request.target_state is WorkItemState.CLEANUP_COMPLETED:
        cleanup_required = False
    return replace(
        record,
        state=request.target_state,
        version=record.version + 1,
        attempt_count=attempt_count,
        repair_count=repair_count,
        budget_consumed=record.budget_consumed + request.budget_cost,
        cleanup_required=cleanup_required,
    )


def _blocked(record: WorkItemRecord, request: TransitionRequest, reason: str) -> TransitionResult:
    receipt = TransitionReceipt(
        idempotency_key=request.idempotency_key,
        source_state=record.state,
        target_state=request.target_state,
        previous_version=record.version,
        new_version=record.version,
        accepted=False,
        reason=reason,
        evidence_refs=request.evidence_refs,
    )
    return TransitionResult(accepted=False, reason=reason, record=record, receipt=receipt)


def _receipt_for_key(record: WorkItemRecord, key: str) -> TransitionReceipt | None:
    for receipt in record.receipts:
        if receipt.idempotency_key == key:
            return receipt
    return None


def _terminal_blocks(record: WorkItemRecord, target_state: WorkItemState) -> bool:
    if record.state is WorkItemState.CLEANUP_COMPLETED:
        return True
    if record.terminal and target_state is WorkItemState.CLEANUP_PENDING:
        return False
    if record.terminal:
        return target_state not in {
            WorkItemState.CLEANUP_PENDING,
            WorkItemState.LEASE_EXPIRED,
            WorkItemState.CANCELED_REVOKED,
        }
    return False


def _global_stop_block(target: WorkItemState, global_stop: GlobalStopState) -> str | None:
    classes = {
        WorkItemState.LEASE_ADMITTED: GlobalStopTransitionClass.LEASE_ADMISSION,
        WorkItemState.READY: GlobalStopTransitionClass.READY,
        WorkItemState.CYCLE_STARTING: GlobalStopTransitionClass.CYCLE_START,
        WorkItemState.WORKER_RUNNING: GlobalStopTransitionClass.CYCLE_START,
        WorkItemState.VALIDATING: GlobalStopTransitionClass.CYCLE_START,
        WorkItemState.AUDITING: GlobalStopTransitionClass.CYCLE_START,
        WorkItemState.REPAIR_ADMITTED: GlobalStopTransitionClass.REPAIR,
        WorkItemState.REPAIR_RUNNING: GlobalStopTransitionClass.REPAIR,
        WorkItemState.COMMIT_ELIGIBLE: GlobalStopTransitionClass.COMMIT_ELIGIBILITY,
        WorkItemState.LOCAL_COMMIT_COMPLETED: GlobalStopTransitionClass.COMMIT_ELIGIBILITY,
    }
    transition_class = classes.get(target)
    if transition_class is None:
        return None
    decision = enforce_global_stop(global_stop, transition_class)
    if decision.accepted:
        return None
    return decision.reason


def _stage_enabled(target: WorkItemState) -> str | None:
    if target in {
        WorkItemState.CYCLE_STARTING,
        WorkItemState.WORKER_RUNNING,
        WorkItemState.VALIDATING,
        WorkItemState.AUDITING,
    }:
        return "stage_not_enabled"
    if target in {WorkItemState.REPAIR_ADMITTED, WorkItemState.REPAIR_RUNNING}:
        return "stage_not_enabled"
    if target in {WorkItemState.COMMIT_ELIGIBLE, WorkItemState.LOCAL_COMMIT_COMPLETED}:
        return "stage_not_enabled"
    return None


def _requires_executable_authority(target: WorkItemState) -> bool:
    return target in {
        WorkItemState.CYCLE_STARTING,
        WorkItemState.WORKER_RUNNING,
        WorkItemState.VALIDATING,
        WorkItemState.AUDITING,
        WorkItemState.REPAIR_ADMITTED,
        WorkItemState.REPAIR_RUNNING,
        WorkItemState.COMMIT_ELIGIBLE,
        WorkItemState.LOCAL_COMMIT_COMPLETED,
    }
