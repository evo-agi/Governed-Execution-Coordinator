from ge_nwp_coordinator.global_stop import (
    GlobalStopState,
    GlobalStopTransitionClass,
    coordinator_clear_global_stop,
    enforce_global_stop,
)
from ge_nwp_coordinator.reports import project_work_item_report
from ge_nwp_coordinator.state_machine import TransitionContext, TransitionRequest, WorkItemRecord, WorkItemState, transition


def test_global_stop_blocks_required_transition_classes() -> None:
    stop = GlobalStopState(active=True, stop_id="stop-1", reason="operator-stop")
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
        assert decision.reason.startswith("global_stop_active")


def test_state_machine_global_stop_blocks_admission_and_ready() -> None:
    stop = GlobalStopState(active=True, stop_id="stop-1")
    context = TransitionContext(lease_identity_valid=True, authorized=True, executable=False, global_stop=stop)
    record = WorkItemRecord(work_item_id="wi-1", lease_id="lease-1", backlog_id="backlog-1")
    result = transition(
        record,
        TransitionRequest(WorkItemState.LEASE_ADMITTED, 0, "admit"),
        context,
    )
    assert not result.accepted
    assert result.reason == "global_stop_active:lease_admission"


def test_coordinator_cannot_clear_global_stop() -> None:
    stop = GlobalStopState(active=True, stop_id="stop-1")
    decision = coordinator_clear_global_stop(stop)
    assert not decision.accepted
    assert decision.reason == "coordinator_cannot_clear_global_stop"
    assert stop.active


def test_global_stop_safe_report_projection() -> None:
    stop = GlobalStopState(active=True, stop_id="stop-1", reason="operator-stop")
    record = WorkItemRecord(work_item_id="wi-1", lease_id="lease-1", backlog_id="backlog-1")
    report = project_work_item_report(
        record,
        lease_ref="lease-1",
        backlog_ref="backlog-1",
        global_stop=stop,
    ).to_dict()
    assert report["global_stop"]["active"] is True
    assert report["non_authority_notice"].startswith("report projection only")
