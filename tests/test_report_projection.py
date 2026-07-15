import pytest

from ge_nwp_coordinator.global_stop import GlobalStopState
from ge_nwp_coordinator.reports import assert_safe_report_payload, project_work_item_report
from ge_nwp_coordinator.state_machine import WorkItemRecord, WorkItemState


def test_reports_are_projections_only_and_do_not_mutate_state() -> None:
    record = WorkItemRecord(
        work_item_id="wi-1",
        lease_id="lease-1",
        backlog_id="backlog-1",
        state=WorkItemState.BLOCKED,
        version=3,
        cleanup_required=True,
    )
    report = project_work_item_report(
        record,
        lease_ref="lease-safe-ref",
        backlog_ref="backlog-safe-ref",
        global_stop=GlobalStopState(),
        safe_failure_class="operator_action_required",
        safe_evidence_refs=("evidence-safe-ref",),
    )
    payload = report.to_dict()
    assert record.state is WorkItemState.BLOCKED
    assert payload["work_item"]["state"] == "blocked"
    assert payload["work_item"]["operator_action_required"] is True
    assert "not durable state" in payload["non_authority_notice"]


def test_reports_reject_private_raw_material_and_local_paths() -> None:
    with pytest.raises(ValueError, match="unsafe report fragment"):
        assert_safe_report_payload({"raw_prompt": "do work"})
    with pytest.raises(ValueError, match="unsafe report fragment"):
        assert_safe_report_payload({"evidence": "secret token"})
    unsafe_path = "/" + "Users" + "/" + "operator" + "/" + "private"
    with pytest.raises(ValueError, match="unsafe report fragment"):
        assert_safe_report_payload({"path": unsafe_path})


def test_report_does_not_claim_worker_execution() -> None:
    record = WorkItemRecord(work_item_id="wi-1", lease_id="lease-1", backlog_id="backlog-1")
    payload = project_work_item_report(
        record,
        lease_ref="lease-1",
        backlog_ref="backlog-1",
        global_stop=GlobalStopState(),
    ).to_dict()
    text = repr(payload).lower()
    assert "worker executed" not in text
    assert "worker_running" not in text
