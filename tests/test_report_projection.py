import json

import pytest

from ge_nwp_coordinator.global_stop import GlobalStopState
from ge_nwp_coordinator.reports import (
    NON_AUTHORITY_NOTICE,
    project_work_item_report,
    validate_public_projection_payload,
)
from ge_nwp_coordinator.state_machine import TransitionRequest, WorkItemRecord, WorkItemState


def _payload() -> dict[str, object]:
    record = WorkItemRecord(
        work_item_id="wi-1",
        lease_id="lease-1",
        backlog_id="backlog-1",
        state=WorkItemState.BLOCKED,
        version=3,
        cleanup_required=True,
    )
    return project_work_item_report(
        record,
        lease_ref="lease-safe-ref",
        backlog_ref="backlog-safe-ref",
        global_stop=GlobalStopState(active=True, stop_id="stop-1", reason="RAW_REASON_NOT_PUBLIC"),
        safe_failure_class="operator_action_required",
        safe_evidence_refs=("evidence-safe-ref",),
    ).to_dict()


def test_valid_projection_passes_and_does_not_mutate_state() -> None:
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
    validate_public_projection_payload(payload)
    assert record.state is WorkItemState.BLOCKED
    assert payload["work_item"]["state"] == "blocked"
    assert payload["work_item"]["operator_action_required"] is True
    assert payload["non_authority_notice"] == NON_AUTHORITY_NOTICE


def test_unknown_public_projection_fields_fail_closed() -> None:
    payload = _payload()
    payload["extra"] = "not-part-of-v1"
    with pytest.raises(ValueError, match="unknown_field:report.extra"):
        validate_public_projection_payload(payload)

    payload = _payload()
    payload["work_item"]["extra"] = "not-part-of-v1"
    with pytest.raises(ValueError, match="unknown_field:work_item.extra"):
        validate_public_projection_payload(payload)


@pytest.mark.parametrize(
    "unsafe_ref",
    (
        "http://example.invalid",
        "https://example.invalid",
        "service.invalid:443",
        "/etc/passwd",
        "/Users/operator/private",
        "/home/operator/private",
        "C:\\private\\file",
        "C:/private/file",
        "\\\\server\\share",
        "../private",
        "..\\private",
        "file:///tmp/private",
    ),
)
def test_paths_and_endpoints_are_rejected_without_echoing_values(unsafe_ref: str) -> None:
    payload = _payload()
    payload["work_item"]["safe_evidence_refs"] = [unsafe_ref]
    with pytest.raises(ValueError) as exc_info:
        validate_public_projection_payload(payload)
    assert unsafe_ref not in str(exc_info.value)


@pytest.mark.parametrize(
    "unsafe_ref",
    (
        "-----BEGIN-PRIVATE-KEY-----",
        "certificate",
        "trust-root",
        "bearer-token",
        "api-key",
        "credential",
        "connector-id",
        "tunnel-id",
        "workspace-123",
        "org-123",
        "privateBrief",
        "raw-prompt",
        "raw-log",
        "payload",
        "environment",
    ),
)
def test_trust_credentials_platform_ids_and_private_content_are_rejected(unsafe_ref: str) -> None:
    payload = _payload()
    payload["work_item"]["safe_evidence_refs"] = [unsafe_ref]
    with pytest.raises(ValueError) as exc_info:
        validate_public_projection_payload(payload)
    assert unsafe_ref not in str(exc_info.value)


@pytest.mark.parametrize(
    "field_name",
    (
        "private_brief",
        "privateBrief",
        "private-brief",
        "prompt",
        "raw_prompt",
        "instructions",
        "local_path",
        "localPath",
        "worktree_path",
        "endpoint",
        "endpoint_url",
        "url",
        "uri",
        "trust_material",
        "certificate",
        "private_key",
        "token",
        "credential",
        "environment",
        "raw_log",
        "payload",
    ),
)
def test_private_field_spelling_variants_are_rejected_as_unknown_fields(field_name: str) -> None:
    payload = _payload()
    payload["work_item"][field_name] = "not-part-of-v1"
    with pytest.raises(ValueError, match=f"unknown_field:work_item.{field_name}"):
        validate_public_projection_payload(payload)


def test_fixed_non_authority_notice_is_enforced() -> None:
    payload = _payload()
    payload["non_authority_notice"] = "caller-controlled"
    with pytest.raises(ValueError, match="invalid_field_type:non_authority_notice"):
        validate_public_projection_payload(payload)


def test_report_does_not_claim_worker_execution_or_expose_global_stop_reason() -> None:
    payload = _payload()
    text = json.dumps(payload, sort_keys=True).lower()
    assert "worker executed" not in text
    assert "worker_running" not in text
    assert "raw_reason" not in text
    assert "reason" not in payload["global_stop"]


def test_report_cannot_be_used_directly_as_transition_request() -> None:
    payload = _payload()
    with pytest.raises(TypeError):
        TransitionRequest(**payload)
