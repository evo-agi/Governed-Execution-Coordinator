from dataclasses import replace
import inspect

from ge_nwp_coordinator.global_stop import GlobalStopReasonClass, GlobalStopState
from ge_nwp_coordinator.lease import (
    AuthorizationDecision,
    AuthorizationModel,
    LeaseIdentityValidation,
    LeaseRuntimeDecision,
    LeaseRuntimeStatus,
)
from ge_nwp_coordinator.models import ValidationIssue
from ge_nwp_coordinator.state_machine import (
    ALLOWED_PREDECESSORS,
    P1_DISABLED_TARGET_STATES,
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
    """Pure evaluator fixture only; not a persisted reader or provider."""
    if not identity.identity_valid:
        authorized = False
        executable = False
        reason = "lease_identity_invalid"
    else:
        reason = "accepted" if authorized else "lease_not_authorized"
    return AuthorizationDecision(
        decision_ref="authz-lease-a2-p1",
        lease_ref=identity.lease_ref,
        lease_identity_decision_ref=identity.decision_ref,
        lease_identity_valid=identity.identity_valid,
        authorization_model=AuthorizationModel.OPERATOR_POLICY,
        authorized=authorized,
        executable=executable,
        reason=reason,
    )


def _runtime(
    status: LeaseRuntimeStatus = LeaseRuntimeStatus.ACTIVE,
    *,
    evaluated_at: str = "2026-07-14T00:00:02Z",
) -> LeaseRuntimeDecision:
    return LeaseRuntimeDecision(
        lease_ref="lease-a2-p1",
        evaluated_at=evaluated_at,
        status=status,
        reason={
            LeaseRuntimeStatus.ACTIVE: "lease_runtime_active",
            LeaseRuntimeStatus.NOT_YET_VALID: "lease_not_yet_valid",
            LeaseRuntimeStatus.EXPIRED: "lease_expired",
            LeaseRuntimeStatus.REVOKED: "lease_revoked",
            LeaseRuntimeStatus.REVOCATION_UNKNOWN: "lease_revocation_unknown",
        }[status],
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


def _test_only_authorized_operator_policy_context(
    *,
    executable: bool = False,
    stop: bool = False,
    identity_valid: bool = True,
    dependencies_satisfied: bool = True,
    runtime_status: LeaseRuntimeStatus = LeaseRuntimeStatus.ACTIVE,
) -> TransitionContext:
    identity = _identity(valid=identity_valid)
    return TransitionContext(
        lease_identity=identity,
        authorization=_authorization(identity=identity, authorized=True, executable=executable),
        lease_runtime=_runtime(runtime_status),
        global_stop=_stop() if stop else GlobalStopState(),
        dependency_decision=DependencyDecision(
            decision_ref="deps-ready",
            work_item_id="wi-1",
            dependencies_satisfied=dependencies_satisfied,
            reason="accepted" if dependencies_satisfied else "dependencies_not_satisfied",
        ),
    )


def _unsupported_authorization_context(
    *,
    stop: bool = False,
    dependencies_satisfied: bool = True,
    runtime_status: LeaseRuntimeStatus = LeaseRuntimeStatus.ACTIVE,
) -> TransitionContext:
    identity = _identity()
    return replace(
        _test_only_authorized_operator_policy_context(
            executable=False,
            stop=stop,
            dependencies_satisfied=dependencies_satisfied,
            runtime_status=runtime_status,
        ),
        authorization=AuthorizationDecision(
            decision_ref="authz-unsupported-lease-a2-p1",
            lease_ref=identity.lease_ref,
            lease_identity_decision_ref=identity.decision_ref,
            lease_identity_valid=identity.identity_valid,
            authorization_model=AuthorizationModel.UNSUPPORTED,
            authorized=False,
            executable=False,
            reason="unsupported_authorization_model",
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
    context = context or _test_only_authorized_operator_policy_context()
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


def _disabled_stage_cases() -> tuple[tuple[WorkItemRecord, WorkItemState, str, tuple[str, ...]], ...]:
    return (
        (_record(WorkItemState.READY, 1), WorkItemState.CYCLE_STARTING, "cycle", ()),
        (_record(WorkItemState.CYCLE_STARTING, 2), WorkItemState.WORKER_RUNNING, "worker", ()),
        (_record(WorkItemState.WORKER_RUNNING, 3), WorkItemState.VALIDATING, "validate", ("safe-evidence",)),
        (_record(WorkItemState.VALIDATING, 4), WorkItemState.AUDITING, "audit", ("safe-evidence",)),
        (_record(WorkItemState.FAILED, 5), WorkItemState.REPAIR_ADMITTED, "repair-admit", ("safe-evidence",)),
        (_record(WorkItemState.REPAIR_ADMITTED, 6), WorkItemState.REPAIR_RUNNING, "repair-run", ()),
        (_record(WorkItemState.AUDITING, 7), WorkItemState.COMMIT_ELIGIBLE, "commit-eligible", ("safe-evidence",)),
        (
            _record(WorkItemState.COMMIT_ELIGIBLE, 8),
            WorkItemState.LOCAL_COMMIT_COMPLETED,
            "local-commit",
            ("safe-evidence",),
        ),
    )


def test_valid_and_invalid_predecessors_produce_events() -> None:
    context = _test_only_authorized_operator_policy_context()
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
    context = _test_only_authorized_operator_policy_context()
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
    context = _test_only_authorized_operator_policy_context()
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
    context = _test_only_authorized_operator_policy_context()
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
    context = _test_only_authorized_operator_policy_context(executable=True)
    for record, target, key, evidence_refs in _disabled_stage_cases():
        result = transition(
            record,
            _command(target, record=record, context=context, key=key, evidence_refs=evidence_refs),
            context,
        )
        assert not result.accepted
        assert result.reason == "stage_not_enabled"
        assert result.event is not None
        assert result.event.outcome is TransitionEventOutcome.DOMAIN_REJECTED


def test_p1_disabled_target_state_set_is_single_documented_future_set() -> None:
    assert P1_DISABLED_TARGET_STATES == frozenset(
        {
            WorkItemState.CYCLE_STARTING,
            WorkItemState.WORKER_RUNNING,
            WorkItemState.VALIDATING,
            WorkItemState.AUDITING,
            WorkItemState.REPAIR_ADMITTED,
            WorkItemState.REPAIR_RUNNING,
            WorkItemState.COMMIT_ELIGIBLE,
            WorkItemState.LOCAL_COMMIT_COMPLETED,
        }
    )
    assert {target for _, target, _, _ in _disabled_stage_cases()} == P1_DISABLED_TARGET_STATES


def test_p1_disabled_stage_gate_is_invariant_across_lease_runtime_statuses() -> None:
    for record, target, key, evidence_refs in _disabled_stage_cases():
        for status in LeaseRuntimeStatus:
            context = _test_only_authorized_operator_policy_context(executable=True, runtime_status=status)
            result = transition(
                record,
                _command(
                    target,
                    record=record,
                    context=context,
                    key=f"{key}-{status.value.replace('_', '-')}",
                    evidence_refs=evidence_refs,
                ),
                context,
            )
            assert result.kind is TransitionEvaluationKind.DOMAIN_REJECTED
            assert result.reason == "stage_not_enabled"
            assert result.event is not None
            assert result.event.reason == "stage_not_enabled"
            assert result.event.lease_runtime == context.lease_runtime


def test_stage_not_enabled_events_retain_runtime_provenance_in_identity() -> None:
    record = _record(WorkItemState.READY, 1)
    active_context = _test_only_authorized_operator_policy_context(executable=True)
    expired_context = replace(
        active_context,
        lease_runtime=_runtime(
            LeaseRuntimeStatus.EXPIRED,
            evaluated_at="2026-07-15T00:00:00Z",
        ),
    )

    active = transition(
        record,
        _command(WorkItemState.CYCLE_STARTING, record=record, context=active_context, key="cycle-active"),
        active_context,
    )
    expired = transition(
        record,
        _command(WorkItemState.CYCLE_STARTING, record=record, context=expired_context, key="cycle-active"),
        expired_context,
    )

    assert active.reason == expired.reason == "stage_not_enabled"
    assert active.event is not None
    assert expired.event is not None
    assert active.event.lease_runtime == active_context.lease_runtime
    assert expired.event.lease_runtime == expired_context.lease_runtime
    assert active.event.event_ref != expired.event.event_ref
    assert active.event.canonical_digest() != expired.event.canonical_digest()


def test_p1_disabled_stage_gate_precedes_competing_domain_contexts() -> None:
    for record, target, key, evidence_refs in _disabled_stage_cases():
        competing_cases = (
            ("global-stop", _test_only_authorized_operator_policy_context(executable=True, stop=True), record, evidence_refs, 0),
            ("invalid-identity", _test_only_authorized_operator_policy_context(identity_valid=False), record, evidence_refs, 0),
            ("unsupported-auth", _unsupported_authorization_context(), record, evidence_refs, 0),
            ("not-executable", _test_only_authorized_operator_policy_context(executable=False), record, evidence_refs, 0),
            ("unsatisfied-deps", _test_only_authorized_operator_policy_context(executable=True, dependencies_satisfied=False), record, evidence_refs, 0),
            ("missing-evidence", _test_only_authorized_operator_policy_context(executable=True), record, (), 0),
            (
                "budget-exhausted",
                _test_only_authorized_operator_policy_context(executable=True),
                replace(record, budget_consumed=10),
                evidence_refs,
                1,
            ),
            ("invalid-predecessor", _test_only_authorized_operator_policy_context(executable=True), _record(), evidence_refs, 0),
        )
        for label, context, competing_record, competing_evidence_refs, budget_cost in competing_cases:
            result = transition(
                competing_record,
                _command(
                    target,
                    record=competing_record,
                    context=context,
                    key=f"{key}-{label}",
                    evidence_refs=competing_evidence_refs,
                    budget_cost=budget_cost,
                ),
                context,
            )
            assert result.kind is TransitionEvaluationKind.DOMAIN_REJECTED
            assert result.reason == "stage_not_enabled"
            assert result.event is not None
            assert result.event.reason == "stage_not_enabled"

    cycle_record = replace(_record(WorkItemState.READY, 1), attempt_count=2)
    cycle_context = _test_only_authorized_operator_policy_context(executable=True)
    attempts = transition(
        cycle_record,
        _command(WorkItemState.CYCLE_STARTING, record=cycle_record, context=cycle_context, key="attempts"),
        cycle_context,
    )
    assert attempts.reason == "stage_not_enabled"

    repair_record = replace(_record(WorkItemState.FAILED, 1), repair_count=1)
    repair_context = _test_only_authorized_operator_policy_context(executable=True)
    repairs = transition(
        repair_record,
        _command(
            WorkItemState.REPAIR_ADMITTED,
            record=repair_record,
            context=repair_context,
            key="repairs",
            evidence_refs=("safe-evidence",),
        ),
        repair_context,
    )
    assert repairs.reason == "stage_not_enabled"


def test_stage_gate_ordering_contract_is_pinned() -> None:
    context = _test_only_authorized_operator_policy_context(identity_valid=False, stop=True)
    record = _record(WorkItemState.READY, 1)
    pre_apply = transition(
        record,
        _command(WorkItemState.CYCLE_STARTING, record=record, context=context, work_item_id="wi-2"),
        context,
    )
    assert pre_apply.kind is TransitionEvaluationKind.PRE_APPLY_INVALID
    assert pre_apply.event is None

    unsupported = transition(
        record,
        _command(WorkItemState.PROPOSED, record=record, context=context, key="unsupported"),
        context,
    )
    assert unsupported.kind is TransitionEvaluationKind.DOMAIN_REJECTED
    assert unsupported.reason == "unsupported_target_state"
    assert unsupported.event is not None

    source = inspect.getsource(transition.__globals__["_domain_rejection_reason"])
    assert source.index('"unsupported_target_state"') < source.index("_stage_enabled")
    assert source.index("_stage_enabled") < source.index('"lease_identity_invalid"')
    assert source.index("_stage_enabled") < source.index("_global_stop_block")
    assert source.index("_stage_enabled") < source.index("_terminal_blocks")
    assert source.index("_stage_enabled") < source.index("_requires_executable_authority")
    assert source.index("_stage_enabled") < source.index('"dependencies_not_satisfied"')
    assert source.index("_stage_enabled") < source.index('"evidence_required"')
    assert source.index("_stage_enabled") < source.index('"budget_exhausted"')
    assert source.index("_stage_enabled") < source.index('"attempts_exhausted"')
    assert source.index("_stage_enabled") < source.index('"repairs_exhausted"')


def test_explicit_lease_expiry_target_preserves_expired_runtime_semantics() -> None:
    context = _test_only_authorized_operator_policy_context(runtime_status=LeaseRuntimeStatus.EXPIRED)
    record = _record(WorkItemState.READY, 1)

    result = transition(
        record,
        _command(WorkItemState.LEASE_EXPIRED, record=record, context=context, key="lease-expired"),
        context,
    )

    assert result.kind is TransitionEvaluationKind.ACCEPTED
    assert result.event is not None
    assert result.event.reason == "transition_accepted"
    assert result.event.lease_runtime == context.lease_runtime


def test_limits_and_executable_context_do_not_enable_p1_future_stages() -> None:
    context = _test_only_authorized_operator_policy_context(executable=True)
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
            context=_test_only_authorized_operator_policy_context(),
            key="failed",
            safe_failure_class="validation_failed",
        ),
        _test_only_authorized_operator_policy_context(),
    )
    assert missing_evidence.reason == "evidence_required"
    assert missing_evidence.event is not None

    over_budget_record = replace(record, budget_consumed=9)
    over_budget = transition(
        over_budget_record,
        _command(
            WorkItemState.FAILED,
            record=over_budget_record,
            context=_test_only_authorized_operator_policy_context(),
            key="failed2",
            evidence_refs=("safe",),
            safe_failure_class="validation_failed",
            budget_cost=2,
        ),
        _test_only_authorized_operator_policy_context(),
    )
    assert over_budget.reason == "budget_exhausted"
    assert over_budget.event is not None
    assert over_budget.event.budget_cost_delta == 0

    invalid_identity_context = _test_only_authorized_operator_policy_context(identity_valid=False)
    invalid_identity = transition(
        _record(),
        _command(WorkItemState.LEASE_ADMITTED, context=invalid_identity_context),
        invalid_identity_context,
    )
    assert invalid_identity.reason == "lease_identity_invalid"
    assert invalid_identity.event is not None

    deps_context = _test_only_authorized_operator_policy_context(dependencies_satisfied=False)
    admitted = _record(WorkItemState.LEASE_ADMITTED, 1)
    deps = transition(
        admitted,
        _command(WorkItemState.READY, record=admitted, context=deps_context, key="ready"),
        deps_context,
    )
    assert deps.reason == "dependencies_not_satisfied"
    assert deps.event is not None


def test_ready_requires_work_item_bound_dependency_evidence() -> None:
    admitted = _record(WorkItemState.LEASE_ADMITTED, 1)

    unbound_context = replace(
        _test_only_authorized_operator_policy_context(),
        dependency_decision=DependencyDecision(decision_ref="deps-general", work_item_id=None),
    )
    unbound = transition(
        admitted,
        _command(WorkItemState.READY, record=admitted, context=unbound_context, key="ready-unbound"),
        unbound_context,
    )
    assert unbound.kind is TransitionEvaluationKind.PRE_APPLY_INVALID
    assert unbound.reason == "dependency_reference_mismatch"
    assert unbound.event is None

    wrong_item_context = replace(
        _test_only_authorized_operator_policy_context(),
        dependency_decision=DependencyDecision(decision_ref="deps-wrong", work_item_id="wi-2"),
    )
    wrong_item = transition(
        admitted,
        _command(WorkItemState.READY, record=admitted, context=wrong_item_context, key="ready-wrong"),
        wrong_item_context,
    )
    assert wrong_item.kind is TransitionEvaluationKind.PRE_APPLY_INVALID
    assert wrong_item.reason == "dependency_reference_mismatch"
    assert wrong_item.event is None

    rejected_context = _test_only_authorized_operator_policy_context(dependencies_satisfied=False)
    rejected = transition(
        admitted,
        _command(WorkItemState.READY, record=admitted, context=rejected_context, key="ready-rejected"),
        rejected_context,
    )
    assert rejected.kind is TransitionEvaluationKind.DOMAIN_REJECTED
    assert rejected.reason == "dependencies_not_satisfied"
    assert rejected.event is not None

    accepted_context = _test_only_authorized_operator_policy_context(dependencies_satisfied=True)
    accepted = transition(
        admitted,
        _command(WorkItemState.READY, record=admitted, context=accepted_context, key="ready-accepted"),
        accepted_context,
    )
    assert accepted.accepted
    assert accepted.event is not None

    generic_context = replace(
        _test_only_authorized_operator_policy_context(),
        dependency_decision=DependencyDecision(decision_ref="deps-general", work_item_id=None),
    )
    generic_non_authoritative = transition(
        _record(),
        _command(WorkItemState.LEASE_ADMITTED, context=generic_context, key="lease-admitted"),
        generic_context,
    )
    assert generic_non_authoritative.accepted


def test_future_state_vocabulary_has_no_production_enable_policy() -> None:
    assert WorkItemState.WORKER_RUNNING in ALLOWED_PREDECESSORS
    assert WorkItemState.REPAIR_RUNNING in ALLOWED_PREDECESSORS
    assert WorkItemState.LOCAL_COMMIT_COMPLETED in ALLOWED_PREDECESSORS


def test_no_publication_states_exist() -> None:
    assert "publication" not in {state.value for state in WorkItemState}
