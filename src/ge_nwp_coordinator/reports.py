"""Safe non-authoritative report projections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ge_nwp_coordinator.global_stop import GlobalStopState
from ge_nwp_coordinator.state_machine import WorkItemRecord

REPORT_SCHEMA_ID = "governed-execution.nwp-coordinator-report.v1"
NON_AUTHORITY_NOTICE = "report projection only; not durable state, authorization, execution, acceptance, commit, or publication authority"
LOCAL_USER_PREFIX = "/" + "Users" + "/"
FORBIDDEN_REPORT_FRAGMENTS = (
    "raw_prompt",
    "raw log",
    "raw_log",
    "secret",
    "credential",
    "private brief",
    "private_assignment_content",
    "worker output",
    LOCAL_USER_PREFIX,
)


@dataclass(frozen=True)
class WorkItemReport:
    work_item_id: str
    lease_ref: str
    backlog_ref: str
    state: str
    version: int
    attempt_count: int
    repair_count: int
    budget_consumed: int
    budget_limit: int
    cleanup_required: bool
    safe_failure_class: str | None
    operator_action_required: bool
    safe_evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "work_item_id": self.work_item_id,
            "lease_ref": self.lease_ref,
            "backlog_ref": self.backlog_ref,
            "state": self.state,
            "version": self.version,
            "attempt_count": self.attempt_count,
            "repair_count": self.repair_count,
            "budget_consumed": self.budget_consumed,
            "budget_limit": self.budget_limit,
            "cleanup_required": self.cleanup_required,
            "safe_failure_class": self.safe_failure_class,
            "operator_action_required": self.operator_action_required,
            "safe_evidence_refs": list(self.safe_evidence_refs),
        }


@dataclass(frozen=True)
class CoordinatorReport:
    schema_id: str
    work_item: WorkItemReport
    global_stop: dict[str, str | bool | None]
    non_authority_notice: str = NON_AUTHORITY_NOTICE

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_id": self.schema_id,
            "work_item": self.work_item.to_dict(),
            "global_stop": dict(self.global_stop),
            "non_authority_notice": self.non_authority_notice,
        }
        assert_safe_report_payload(payload)
        return payload


def project_work_item_report(
    record: WorkItemRecord,
    *,
    lease_ref: str,
    backlog_ref: str,
    global_stop: GlobalStopState,
    safe_failure_class: str | None = None,
    safe_evidence_refs: tuple[str, ...] = (),
) -> CoordinatorReport:
    report = WorkItemReport(
        work_item_id=record.work_item_id,
        lease_ref=lease_ref,
        backlog_ref=backlog_ref,
        state=record.state.value,
        version=record.version,
        attempt_count=record.attempt_count,
        repair_count=record.repair_count,
        budget_consumed=record.budget_consumed,
        budget_limit=record.budget_limit,
        cleanup_required=record.cleanup_required,
        safe_failure_class=safe_failure_class,
        operator_action_required=global_stop.active or record.cleanup_required or record.terminal,
        safe_evidence_refs=safe_evidence_refs,
    )
    return CoordinatorReport(
        schema_id=REPORT_SCHEMA_ID,
        work_item=report,
        global_stop=global_stop.to_report_dict(),
    )


def assert_safe_report_payload(payload: Any) -> None:
    text = repr(payload).lower()
    for fragment in FORBIDDEN_REPORT_FRAGMENTS:
        if fragment.lower() in text:
            raise ValueError(f"unsafe report fragment: {fragment}")
