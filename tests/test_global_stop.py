from ge_nwp_coordinator.global_stop import (
    GlobalStopAction,
    GlobalStopCommand,
    GlobalStopEvaluationKind,
    GlobalStopEventOutcome,
    GlobalStopOperatorDecision,
    GlobalStopReasonClass,
    GlobalStopState,
    GlobalStopTransitionClass,
    coordinator_clear_global_stop,
    enforce_global_stop,
    evaluate_global_stop_update,
)
from ge_nwp_coordinator.lease import AuthorizationDecision, AuthorizationModel, LeaseIdentityValidation
from ge_nwp_coordinator.reports import project_work_item_report
from ge_nwp_coordinator.state_machine import TransitionCommand, TransitionContext, WorkItemRecord, WorkItemState, transition


def _identity() -> LeaseIdentityValidation:
    return LeaseIdentityValidation(
        identity_valid=True,
        digest="a" * 64,
        issues=(),
        decision_ref="lease-identity-lease-1",
        lease_ref="lease-1",
    )


def _context(global_stop: GlobalStopState) -> TransitionContext:
    identity = _identity()
    return TransitionContext(
        lease_identity=identity,
        authorization=AuthorizationDecision(
            decision_ref="authz-lease-1",
            lease_ref="lease-1",
            lease_identity_valid=True,
            authorization_model=AuthorizationModel.OPERATOR_POLICY,
            authorized=True,
            executable=True,
            reason="accepted",
        ),
        global_stop=global_stop,
    )


def _active_stop(version: int = 1) -> GlobalStopState:
    return GlobalStopState(
        version=version,
        active=True,
        stop_id="stop-1",
        reason_class=GlobalStopReasonClass.OPERATOR_STOP,
        issuer_ref="operator-policy",
        issued_at="2026-07-14T00:00:00Z",
        operator_decision_ref="operator-decision-1",
    )


def _operator_decision(*, authorized: bool = True) -> GlobalStopOperatorDecision:
    return GlobalStopOperatorDecision(
        decision_ref="operator-decision-1",
        authorized=authorized,
        reason="accepted" if authorized else "operator_authorization_required",
    )


def _transition_command(
    target: WorkItemState,
    *,
    record: WorkItemRecord,
    context: TransitionContext,
    key: str = "admit",
) -> TransitionCommand:
    return TransitionCommand.create(
        work_item_id=record.work_item_id,
        idempotency_key=key,
        expected_version=record.version,
        target_state=target,
        lease_identity_decision_ref=context.lease_identity.decision_ref,
        authorization_decision_ref=context.authorization.decision_ref,
        global_stop_ref=context.global_stop.stop_ref,
        global_stop_version=context.global_stop.version,
        dependency_decision_ref=context.dependency_decision.decision_ref if target is WorkItemState.READY else None,
    )


def test_global_stop_blocks_required_transition_classes() -> None:
    stop = _active_stop()
    for transition_class in (
        GlobalStopTransitionClass.LEASE_ADMISSION,
        GlobalStopTransitionClass.READY,
        GlobalStopTransitionClass.CYCLE_START,
        GlobalStopTransitionClass.RETRY,
        GlobalStopTransitionClass.REPAIR,
        GlobalStopTransitionClass.COMMIT_ELIGIBILITY,
    ):
        decision = enforce_global_stop(stop, transition_class)
        assert not decision.accepted
        assert decision.reason == f"global_stop_active:{transition_class.value}"


def test_state_machine_global_stop_blocks_enabled_p1_admission_and_ready() -> None:
    stop = _active_stop()
    context = _context(stop)
    record = WorkItemRecord(work_item_id="wi-1", lease_id="lease-1", backlog_id="backlog-1")
    result = transition(
        record,
        _transition_command(WorkItemState.LEASE_ADMITTED, record=record, context=context),
        context,
    )
    assert not result.accepted
    assert result.reason == "global_stop_active:lease_admission"
    assert result.event is not None
    assert result.event.outcome.value == "domain_rejected"

    admitted = WorkItemRecord(
        work_item_id="wi-1",
        lease_id="lease-1",
        backlog_id="backlog-1",
        state=WorkItemState.LEASE_ADMITTED,
        version=1,
    )
    ready = transition(
        admitted,
        _transition_command(WorkItemState.READY, record=admitted, context=context, key="ready"),
        context,
    )
    assert ready.reason == "global_stop_active:ready"


def test_p1_stage_not_enabled_precedes_global_stop_for_future_stages() -> None:
    stop = _active_stop()
    context = _context(stop)
    cases = (
        (WorkItemState.READY, WorkItemState.CYCLE_STARTING),
        (WorkItemState.CYCLE_STARTING, WorkItemState.WORKER_RUNNING),
        (WorkItemState.WORKER_RUNNING, WorkItemState.VALIDATING),
        (WorkItemState.VALIDATING, WorkItemState.AUDITING),
        (WorkItemState.FAILED, WorkItemState.REPAIR_ADMITTED),
        (WorkItemState.AUDITING, WorkItemState.COMMIT_ELIGIBLE),
    )
    for index, (source, target) in enumerate(cases):
        record = WorkItemRecord(
            work_item_id="wi-1",
            lease_id="lease-1",
            backlog_id="backlog-1",
            state=source,
            version=index,
        )
        result = transition(
            record,
            _transition_command(target, record=record, context=context, key=f"k-{index}"),
            context,
        )
        assert not result.accepted
        assert result.reason == "stage_not_enabled"


def test_global_stop_update_command_event_evaluator_accepts_and_rejects() -> None:
    clear = GlobalStopState()
    command = GlobalStopCommand.create(
        action=GlobalStopAction.ACTIVATE,
        idempotency_key="stop-k1",
        expected_version=0,
        stop_id="stop-1",
        reason_class=GlobalStopReasonClass.OPERATOR_STOP,
        issuer_ref="operator-policy",
        issued_at="2026-07-14T00:00:00Z",
        operator_decision_ref="operator-decision-1",
    )
    accepted = evaluate_global_stop_update(clear, command, _operator_decision())
    assert accepted.kind is GlobalStopEvaluationKind.ACCEPTED
    assert accepted.state.active
    assert accepted.event is not None
    assert accepted.event.outcome is GlobalStopEventOutcome.ACCEPTED
    assert accepted.event.reason == "global_stop_update_accepted"

    rejected = evaluate_global_stop_update(clear, command, _operator_decision(authorized=False))
    assert rejected.kind is GlobalStopEvaluationKind.DOMAIN_REJECTED
    assert rejected.state == clear
    assert rejected.event is not None
    assert rejected.event.outcome is GlobalStopEventOutcome.DOMAIN_REJECTED
    assert rejected.event.resulting_version == clear.version

    mismatched_decision = evaluate_global_stop_update(
        clear,
        command,
        GlobalStopOperatorDecision(
            decision_ref="operator-decision-2",
            authorized=True,
            reason="accepted",
        ),
    )
    assert mismatched_decision.kind is GlobalStopEvaluationKind.PRE_APPLY_INVALID
    assert mismatched_decision.event is None


def test_global_stop_clear_requires_matching_operator_decision_and_source() -> None:
    stop = _active_stop()
    clear_command = GlobalStopCommand.create(
        action=GlobalStopAction.CLEAR,
        idempotency_key="clear-k1",
        expected_version=stop.version,
        source_stop_id=stop.stop_id,
        stop_id=stop.stop_id,
        reason_class=stop.reason_class,
        issuer_ref=stop.issuer_ref,
        issued_at=stop.issued_at,
        operator_decision_ref="operator-decision-1",
    )
    result = evaluate_global_stop_update(stop, clear_command, _operator_decision())
    assert result.accepted
    assert not result.state.active
    assert result.event is not None
    assert result.event.resulting_status.value == "clear"


def test_coordinator_cannot_clear_global_stop() -> None:
    stop = _active_stop()
    decision = coordinator_clear_global_stop(stop)
    assert not decision.accepted
    assert decision.reason == "coordinator_cannot_clear_global_stop"
    assert stop.active

    clear = GlobalStopState(active=False)
    clear_decision = coordinator_clear_global_stop(clear)
    assert not clear_decision.accepted
    assert clear_decision.reason == "coordinator_cannot_replace_global_stop"


def test_global_stop_safe_report_projection() -> None:
    stop = _active_stop()
    record = WorkItemRecord(work_item_id="wi-1", lease_id="lease-1", backlog_id="backlog-1")
    report = project_work_item_report(
        record,
        lease_ref="lease-1",
        backlog_ref="backlog-1",
        global_stop=stop,
    ).to_dict()
    assert report["global_stop"]["active"] is True
    assert report["global_stop"]["status"] == "active"
    assert "reason" not in report["global_stop"]
    assert report["non_authority_notice"].startswith("report projection only")


def test_report_projection_failure_cannot_disable_global_stop() -> None:
    stop = _active_stop()
    record = WorkItemRecord(work_item_id="wi-1", lease_id="lease-1", backlog_id="backlog-1")
    try:
        project_work_item_report(
            record,
            lease_ref="lease-1",
            backlog_ref="backlog-1",
            global_stop=stop,
            safe_evidence_refs=("https://example.invalid/evidence",),
        ).to_dict()
    except ValueError:
        pass
    else:  # pragma: no cover - defensive assertion path
        raise AssertionError("unsafe projection should fail closed")

    context = _context(stop)
    result = transition(
        record,
        _transition_command(WorkItemState.LEASE_ADMITTED, record=record, context=context),
        context,
    )
    assert not result.accepted
    assert result.reason == "global_stop_active:lease_admission"
