from dataclasses import replace

from ge_nwp_coordinator.global_stop import GlobalStopReasonClass, GlobalStopState
from ge_nwp_coordinator.lease import AuthorizationDecision, AuthorizationModel, LeaseIdentityValidation
from ge_nwp_coordinator.models import ValidationIssue
from ge_nwp_coordinator.state_machine import (
    ALLOWED_PREDECESSORS,
    DependencyDecision,
    TransitionCommand,
    TransitionContext,
    TransitionEvaluationKind,
    TransitionEventOutcome,
    WorkItemRecord,
    WorkItemState,
    transition,
)


def _identity(*, valid: bool = True) -> LeaseIdentityValidation:
    return LeaseIdentityValidation(
        identity_valid=valid,
        digest="a" * 64 if valid else None,
        issues=() if valid else (ValidationIssue(field="lease", reason="digest_mismatch"),),
        decision_ref="lease-identity-lease-a2-p1",
        lease_ref="lease-a2-p1",
    )


def _authorization(
    *,
    identity: LeaseIdentityValidation,
    authorized: bool = True,
    executable: bool = False,
) -> AuthorizationDecision:
    return AuthorizationDecision(
        decision_ref="authz-lease-a2-p1",
        lease_ref=identity.lease_ref,
        lease_identity_valid=identity.identity_valid,
        authorization_model=AuthorizationModel.OPERATOR_POLICY,
        authorized=authorized,
        executable=executable,
        reason="accepted" if authorized else "lease_not_authorized",
    )


def _stop() -> GlobalStopState:
    return GlobalStopState(
        version=1,
        active=True,
        stop_id="stop-1",
        reason_class=GlobalStopReasonClass.OPERATOR_STOP,
        issuer_ref="operator-policy",
        issued_at="2026-07-14T00:00:00Z",
        operator_decision_ref="operator-decision-1",
    )


def _context(
    *,
    executable: bool = False,
    stop: bool = False,
    identity_valid: bool = True,
    dependencies_satisfied: bool = True,
) -> TransitionContext:
    identity = _identity(valid=identity_valid)
    return TransitionContext(
        lease_identity=identity,
        authorization=_authorization(identity=identity, authorized=True, executable=executable),
        global_stop=_stop() if stop else GlobalStopState(),
        dependency_decision=DependencyDecision(
            decision_ref="deps-ready",
            dependencies_satisfied=dependencies_satisfied,
            reason="accepted" if dependencies_satisfied else "dependencies_not_satisfied",
        ),
    )


def _record(state: WorkItemState = WorkItemState.PROPOSED, version: int = 0) -> WorkItemRecord:
    return WorkItemRecord(
        work_item_id="wi-1",
        lease_id="lease-a2-p1",
        backlog_id="backlog-a2-p1",
        state=state,
        version=version,
        max_attempts=2,
        max_repairs=1,
        budget_limit=10,
    )


def _command(
    target: WorkItemState,
    *,
    record: WorkItemRecord | None = None,
    context: TransitionContext | None = None,
    version: int | None = None,
    key: str = "k1",
    work_item_id: str = "wi-1",
    **kwargs: object,
) -> TransitionCommand:
    record = record or _record()
    context = context or _context()
    return TransitionCommand.create(
        work_item_id=work_item_id,
        idempotency_key=key,
        expected_version=record.version if version is None else version,
        target_state=target,
        lease_identity_decision_ref=context.lease_identity.decision_ref,
        authorization_decision_ref=context.authorization.decision_ref,
        global_stop_ref=context.global_stop.stop_ref,
        global_stop_version=context.global_stop.version,
        dependency_decision_ref=(
            context.dependency_decision.decision_ref if target is WorkItemState.READY else None
        ),
        **kwargs,
    )


def test_valid_and_invalid_predecessors_produce_events() -> None:
    context = _context()
    record = _record()
    admitted = transition(record, _command(WorkItemState.LEASE_ADMITTED, record=record, context=context), context)
    assert admitted.kind is TransitionEvaluationKind.ACCEPTED
    assert admitted.event is not None
    assert admitted.event.outcome is TransitionEventOutcome.ACCEPTED
    assert admitted.event.reason == "transition_accepted"

    ready = transition(
        admitted.record,
        _command(WorkItemState.READY, record=admitted.record, context=context, key="k2"),
        context,
    )
    assert ready.accepted
    assert ready.event is not None
    assert ready.event.resulting_state is WorkItemState.READY

    invalid = transition(record, _command(WorkItemState.READY, record=record, context=context), context)
    assert invalid.kind is TransitionEvaluationKind.DOMAIN_REJECTED
    assert invalid.reason == "invalid_predecessor"
    assert invalid.event is not None
    assert invalid.event.outcome is TransitionEventOutcome.DOMAIN_REJECTED
    assert invalid.event.resulting_version == record.version


def test_expected_version_is_not_an_evaluator_rule() -> None:
    context = _context()
    record = _record()
    result = transition(
        record,
        _command(WorkItemState.LEASE_ADMITTED, record=record, context=context, version=99),
        context,
    )
    assert result.accepted
    assert result.event is not None
    assert result.event.reason == "transition_accepted"


def test_pre_apply_invalid_command_has_no_event() -> None:
    context = _context()
    record = _record()
    result = transition(
        record,
        _command(WorkItemState.LEASE_ADMITTED, record=record, context=context, work_item_id="wi-2"),
        context,
    )
    assert result.kind is TransitionEvaluationKind.PRE_APPLY_INVALID
    assert result.reason == "work_item_id_mismatch"
    assert result.event is None


def test_counters_budgets_terminal_and_cleanup() -> None:
    context = _context()
    record = _record(state=WorkItemState.CYCLE_STARTING, version=2)
    failed = transition(
        record,
        _command(
            WorkItemState.FAILED,
            record=record,
            context=context,
            key="failed",
            evidence_refs=("safe-evidence",),
            safe_failure_class="validation_failed",
            budget_cost=3,
        ),
        context,
    )
    assert failed.accepted
    assert failed.record.budget_consumed == 3
    assert failed.record.cleanup_required
    assert failed.event is not None
    assert failed.event.budget_cost_delta == 3

    after_terminal = transition(
        failed.record,
        _command(WorkItemState.READY, record=failed.record, context=context, key="ready"),
        context,
    )
    assert not after_terminal.accepted
    assert after_terminal.reason == "terminal_state"
    assert after_terminal.event is not None

    cleanup = transition(
        failed.record,
        _command(WorkItemState.CLEANUP_PENDING, record=failed.record, context=context, key="cleanup"),
        context,
    )
    assert cleanup.accepted


def test_stage_not_enabled_for_worker_repair_and_commit() -> None:
    cases = (
        (_record(WorkItemState.READY, 1), WorkItemState.CYCLE_STARTING, "cycle", ()),
        (_record(WorkItemState.WORKER_RUNNING, 1), WorkItemState.VALIDATING, "validate", ("safe-evidence",)),
        (_record(WorkItemState.VALIDATING, 1), WorkItemState.AUDITING, "audit", ("safe-evidence",)),
        (_record(WorkItemState.FAILED, 1), WorkItemState.REPAIR_ADMITTED, "repair", ("safe-evidence",)),
        (_record(WorkItemState.AUDITING, 1), WorkItemState.COMMIT_ELIGIBLE, "commit", ("safe-evidence",)),
    )
    context = _context(executable=True)
    for record, target, key, evidence_refs in cases:
        result = transition(
            record,
            _command(target, record=record, context=context, key=key, evidence_refs=evidence_refs),
            context,
        )
        assert not result.accepted
        assert result.reason == "stage_not_enabled"
        assert result.event is not None
        assert result.event.outcome is TransitionEventOutcome.DOMAIN_REJECTED


def test_limits_and_executable_context_do_not_enable_p1_future_stages() -> None:
    context = _context(executable=True)
    cycle_record = replace(_record(WorkItemState.READY, 1), max_attempts=5)
    cycle = transition(
        cycle_record,
        _command(WorkItemState.CYCLE_STARTING, record=cycle_record, context=context, key="cycle"),
        context,
    )
    assert cycle.reason == "stage_not_enabled"

    repair_record = replace(_record(WorkItemState.FAILED, 1), max_repairs=5)
    repair = transition(
        repair_record,
        _command(
            WorkItemState.REPAIR_ADMITTED,
            record=repair_record,
            context=context,
            key="repair",
            evidence_refs=("safe-evidence",),
        ),
        context,
    )
    assert repair.reason == "stage_not_enabled"

    commit_record = _record(WorkItemState.AUDITING, 1)
    commit = transition(
        commit_record,
        _command(
            WorkItemState.COMMIT_ELIGIBLE,
            record=commit_record,
            context=context,
            key="commit",
            evidence_refs=("safe-evidence",),
        ),
        context,
    )
    assert commit.reason == "stage_not_enabled"


def test_evidence_budget_identity_and_dependency_requirements() -> None:
    record = _record(WorkItemState.WORKER_RUNNING, 3)
    missing_evidence = transition(
        record,
        _command(
            WorkItemState.FAILED,
            record=record,
            context=_context(),
            key="failed",
            safe_failure_class="validation_failed",
        ),
        _context(),
    )
    assert missing_evidence.reason == "evidence_required"
    assert missing_evidence.event is not None

    over_budget_record = replace(record, budget_consumed=9)
    over_budget = transition(
        over_budget_record,
        _command(
            WorkItemState.FAILED,
            record=over_budget_record,
            context=_context(),
            key="failed2",
            evidence_refs=("safe",),
            safe_failure_class="validation_failed",
            budget_cost=2,
        ),
        _context(),
    )
    assert over_budget.reason == "budget_exhausted"
    assert over_budget.event is not None
    assert over_budget.event.budget_cost_delta == 0

    invalid_identity_context = _context(identity_valid=False)
    invalid_identity = transition(
        _record(),
        _command(WorkItemState.LEASE_ADMITTED, context=invalid_identity_context),
        invalid_identity_context,
    )
    assert invalid_identity.reason == "lease_identity_invalid"
    assert invalid_identity.event is not None

    deps_context = _context(dependencies_satisfied=False)
    admitted = _record(WorkItemState.LEASE_ADMITTED, 1)
    deps = transition(
        admitted,
        _command(WorkItemState.READY, record=admitted, context=deps_context, key="ready"),
        deps_context,
    )
    assert deps.reason == "dependencies_not_satisfied"
    assert deps.event is not None


def test_future_state_vocabulary_has_no_production_enable_policy() -> None:
    assert WorkItemState.WORKER_RUNNING in ALLOWED_PREDECESSORS
    assert WorkItemState.REPAIR_RUNNING in ALLOWED_PREDECESSORS
    assert WorkItemState.LOCAL_COMMIT_COMPLETED in ALLOWED_PREDECESSORS


def test_no_publication_states_exist() -> None:
    assert "publication" not in {state.value for state in WorkItemState}
