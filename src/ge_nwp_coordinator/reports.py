"""Closed, typed, non-authoritative public report projections."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import re
from typing import Any, Mapping

from ge_nwp_coordinator.canonicalization import (
    require_bool,
    require_exact_keys,
    require_non_negative_int,
    require_safe_ref,
    require_string,
)
from ge_nwp_coordinator.global_stop import GLOBAL_STOP_SCHEMA_ID, GlobalStopState
from ge_nwp_coordinator.state_machine import WorkItemRecord, WorkItemState

REPORT_SCHEMA_ID = "governed-execution.nwp-coordinator-report.v1"
NON_AUTHORITY_NOTICE = "report projection only; not durable state, authorization, execution, acceptance, commit, or publication authority"

REPORT_KEYS = frozenset({"schema_id", "work_item", "global_stop", "non_authority_notice"})
WORK_ITEM_REPORT_KEYS = frozenset(
    {
        "work_item_id",
        "lease_ref",
        "backlog_ref",
        "state",
        "version",
        "attempt_count",
        "repair_count",
        "budget_consumed",
        "budget_limit",
        "cleanup_required",
        "safe_failure_class",
        "operator_action_required",
        "safe_evidence_refs",
    }
)
GLOBAL_STOP_REPORT_KEYS = frozenset({"schema_id", "active", "stop_id", "status"})


class SafeFailureClass(str, Enum):
    BUDGET_EXHAUSTED = "budget_exhausted"
    DEPENDENCIES_NOT_SATISFIED = "dependencies_not_satisfied"
    EVIDENCE_REQUIRED = "evidence_required"
    GLOBAL_STOP_ACTIVE = "global_stop_active"
    IDENTITY_INVALID = "lease_identity_invalid"
    INVALID_PREDECESSOR = "invalid_predecessor"
    LEASE_EXPIRED = "lease_expired"
    LEASE_NOT_YET_VALID = "lease_not_yet_valid"
    LEASE_NOT_AUTHORIZED = "lease_not_authorized"
    LEASE_REVOKED = "lease_revoked"
    LEASE_REVOCATION_UNKNOWN = "lease_revocation_unknown"
    NOT_EXECUTABLE = "not_executable"
    OPERATOR_ACTION_REQUIRED = "operator_action_required"
    STAGE_NOT_ENABLED = "stage_not_enabled"
    TERMINAL_STATE = "terminal_state"
    VALIDATION_FAILED = "validation_failed"


class GlobalStopReportStatus(str, Enum):
    ACTIVE = "active"
    CLEAR = "clear"


_FORBIDDEN_SERIALIZED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "path",
        re.compile(
            r"(?:file://|~/|[A-Za-z]:[\\/]|\\\\|(?:^|[\"'\s])/(?:Users|home|root|private|tmp|var|Volumes|[A-Za-z0-9._-]+)(?:/|[\"'\s])|(?:^|[/\\])\.\.(?:/|\\))",
            re.IGNORECASE,
        ),
    ),
    (
        "endpoint",
        re.compile(r"(?:https?://|ssh://|wss?://|grpc://|[A-Za-z0-9.-]+:\d{2,5}|endpoint|url|uri)", re.IGNORECASE),
    ),
    (
        "trust_material",
        re.compile(r"(?:-----begin|private[-_\s]?key|certificate|trust[-_\s]?root|signature|custody)", re.IGNORECASE),
    ),
    (
        "auth_material",
        re.compile(r"(?:bearer\s+[A-Za-z0-9._-]+|api[-_\s]?key|token|credential|password|secret)", re.IGNORECASE),
    ),
    (
        "platform_identifier",
        re.compile(r"(?:connector[-_\s]?id|tunnel[-_\s]?id|workspace[-_\s]?id|org(?:anization)?[-_\s]?id)", re.IGNORECASE),
    ),
    (
        "private_content",
        re.compile(r"(?:private[-_\s]?brief|raw[-_\s]?prompt|prompt|instructions|raw[-_\s]?log|payload|environment|objective)", re.IGNORECASE),
    ),
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

    def __post_init__(self) -> None:
        object.__setattr__(self, "work_item_id", require_safe_ref(self.work_item_id, "work_item.work_item_id"))
        object.__setattr__(self, "lease_ref", require_safe_ref(self.lease_ref, "work_item.lease_ref"))
        object.__setattr__(self, "backlog_ref", require_safe_ref(self.backlog_ref, "work_item.backlog_ref"))
        object.__setattr__(self, "state", _require_work_item_state(self.state, "work_item.state"))
        object.__setattr__(self, "version", require_non_negative_int(self.version, "work_item.version"))
        object.__setattr__(
            self,
            "attempt_count",
            require_non_negative_int(self.attempt_count, "work_item.attempt_count"),
        )
        object.__setattr__(
            self,
            "repair_count",
            require_non_negative_int(self.repair_count, "work_item.repair_count"),
        )
        object.__setattr__(
            self,
            "budget_consumed",
            require_non_negative_int(self.budget_consumed, "work_item.budget_consumed"),
        )
        object.__setattr__(
            self,
            "budget_limit",
            require_non_negative_int(self.budget_limit, "work_item.budget_limit"),
        )
        object.__setattr__(
            self,
            "cleanup_required",
            require_bool(self.cleanup_required, "work_item.cleanup_required"),
        )
        object.__setattr__(
            self,
            "safe_failure_class",
            _require_safe_failure_class(self.safe_failure_class, "work_item.safe_failure_class"),
        )
        object.__setattr__(
            self,
            "operator_action_required",
            require_bool(self.operator_action_required, "work_item.operator_action_required"),
        )
        object.__setattr__(
            self,
            "safe_evidence_refs",
            tuple(require_safe_ref(ref, "work_item.safe_evidence_refs[]") for ref in self.safe_evidence_refs),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WorkItemReport":
        raw = require_exact_keys(payload, "work_item", WORK_ITEM_REPORT_KEYS)
        evidence_refs = raw.get("safe_evidence_refs")
        if not isinstance(evidence_refs, list):
            raise ValueError("invalid_field_type:work_item.safe_evidence_refs")
        return cls(
            work_item_id=raw.get("work_item_id"),
            lease_ref=raw.get("lease_ref"),
            backlog_ref=raw.get("backlog_ref"),
            state=raw.get("state"),
            version=raw.get("version"),
            attempt_count=raw.get("attempt_count"),
            repair_count=raw.get("repair_count"),
            budget_consumed=raw.get("budget_consumed"),
            budget_limit=raw.get("budget_limit"),
            cleanup_required=raw.get("cleanup_required"),
            safe_failure_class=raw.get("safe_failure_class"),
            operator_action_required=raw.get("operator_action_required"),
            safe_evidence_refs=tuple(evidence_refs),
        )

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
class GlobalStopReport:
    schema_id: str
    active: bool
    stop_id: str | None
    status: str

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "global_stop.schema_id") != GLOBAL_STOP_SCHEMA_ID:
            raise ValueError("invalid_field_type:global_stop.schema_id")
        object.__setattr__(self, "active", require_bool(self.active, "global_stop.active"))
        if self.stop_id is not None:
            object.__setattr__(self, "stop_id", require_safe_ref(self.stop_id, "global_stop.stop_id"))
        object.__setattr__(self, "status", _require_global_stop_status(self.status, "global_stop.status"))

    @classmethod
    def from_state(cls, state: GlobalStopState) -> "GlobalStopReport":
        return cls(
            schema_id=GLOBAL_STOP_SCHEMA_ID,
            active=state.active,
            stop_id=state.stop_id,
            status=GlobalStopReportStatus.ACTIVE.value if state.active else GlobalStopReportStatus.CLEAR.value,
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GlobalStopReport":
        raw = require_exact_keys(payload, "global_stop", GLOBAL_STOP_REPORT_KEYS)
        return cls(
            schema_id=raw.get("schema_id"),
            active=raw.get("active"),
            stop_id=raw.get("stop_id"),
            status=raw.get("status"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "active": self.active,
            "stop_id": self.stop_id,
            "status": self.status,
        }


@dataclass(frozen=True)
class CoordinatorReport:
    schema_id: str
    work_item: WorkItemReport
    global_stop: GlobalStopReport
    non_authority_notice: str = NON_AUTHORITY_NOTICE

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "schema_id") != REPORT_SCHEMA_ID:
            raise ValueError("invalid_field_type:schema_id")
        if not isinstance(self.work_item, WorkItemReport):
            raise ValueError("invalid_field_type:work_item")
        if not isinstance(self.global_stop, GlobalStopReport):
            raise ValueError("invalid_field_type:global_stop")
        if self.non_authority_notice != NON_AUTHORITY_NOTICE:
            raise ValueError("invalid_field_type:non_authority_notice")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CoordinatorReport":
        raw = require_exact_keys(payload, "report", REPORT_KEYS)
        return cls(
            schema_id=raw.get("schema_id"),
            work_item=WorkItemReport.from_dict(raw.get("work_item")),
            global_stop=GlobalStopReport.from_dict(raw.get("global_stop")),
            non_authority_notice=raw.get("non_authority_notice"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_id": self.schema_id,
            "work_item": self.work_item.to_dict(),
            "global_stop": self.global_stop.to_dict(),
            "non_authority_notice": self.non_authority_notice,
        }
        _assert_closed_projection_payload(payload)
        _assert_safe_serialized_projection(payload)
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
        global_stop=GlobalStopReport.from_state(global_stop),
    )


def validate_public_projection_payload(payload: Mapping[str, Any]) -> None:
    _assert_closed_projection_payload(payload)
    _assert_safe_serialized_projection(payload)


def _assert_closed_projection_payload(payload: Mapping[str, Any]) -> None:
    CoordinatorReport.from_dict(payload)


def _assert_safe_serialized_projection(payload: Mapping[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    for category, pattern in _FORBIDDEN_SERIALIZED_PATTERNS:
        if pattern.search(serialized):
            raise ValueError(f"unsafe_public_projection:{category}")


def _require_work_item_state(value: Any, field_name: str) -> str:
    raw = require_string(value, field_name)
    if raw not in {state.value for state in WorkItemState}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return raw


def _require_safe_failure_class(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    raw = require_string(value, field_name)
    if raw not in {failure.value for failure in SafeFailureClass}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return raw


def _require_global_stop_status(value: Any, field_name: str) -> str:
    raw = require_string(value, field_name)
    if raw not in {status.value for status in GlobalStopReportStatus}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return raw
