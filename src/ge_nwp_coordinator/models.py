"""Shared Coordinator value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any

from ge_nwp_coordinator.canonicalization import require_bool, require_safe_ref, require_safe_string, require_string


class DecisionStatus(str, Enum):
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    REJECTED = "rejected"


TRANSITION_ACCEPTED_REASONS = frozenset({"transition_accepted"})
TRANSITION_DOMAIN_REJECTED_REASONS = frozenset(
    {
        "lease_identity_invalid",
        "lease_expired",
        "lease_revoked",
        "unsupported_target_state",
        "stage_not_enabled",
        "terminal_state",
        "invalid_predecessor",
        "lease_not_authorized",
        "not_executable",
        "dependencies_not_satisfied",
        "evidence_required",
        "safe_failure_class_required",
        "budget_exhausted",
        "attempts_exhausted",
        "repairs_exhausted",
        "global_stop_active:lease_admission",
        "global_stop_active:ready",
        "global_stop_active:cycle_start",
        "global_stop_active:retry",
        "global_stop_active:repair",
        "global_stop_active:commit_eligibility",
    }
)
GLOBAL_STOP_ACCEPTED_REASONS = frozenset({"global_stop_update_accepted"})
GLOBAL_STOP_DOMAIN_REJECTED_REASONS = frozenset(
    {
        "global_stop_update_blocked",
        "operator_authorization_required",
    }
)
APPLY_CONFLICT_REASONS = frozenset(
    {
        "stale_writer_token",
        "split_brain_writer",
        "writer_token_required",
        "idempotency_key_reuse_conflict",
        "expected_version_conflict",
        "work_item_not_found",
        "validation_failed",
    }
)
PRE_APPLY_REASONS = frozenset(
    {
        "work_item_id_mismatch",
        "lease_reference_mismatch",
        "decision_reference_mismatch",
        "global_stop_reference_mismatch",
        "dependency_reference_mismatch",
        "transition_command_digest_mismatch",
        "global_stop_command_digest_mismatch",
        "invalid_field_type",
        "invalid_field_value",
        "unknown_field",
        "missing_field",
        "duplicate_field",
        "unsupported_schema_id",
        "unsupported_schema_version",
        "digest_mismatch",
        "schema_id_mismatch",
        "schema_version_mismatch",
        "valid_from_before_issued_at",
        "expires_at_not_after_valid_from",
        "max_concurrency_exceeds_max_work_items",
        "max_attempts_malformed",
        "max_repairs_malformed",
        "finite_backlog_binding_malformed",
        "revoked_without_reference",
        "non_revoked_with_reference",
        "digest_algorithm_mismatch",
        "canonicalization_mismatch",
        "content_digest_mismatch",
        "unsupported_authorization_model",
    }
)
SAFE_DECISION_REASONS = (
    frozenset({"accepted", "global_stop_clear", "coordinator_cannot_clear_global_stop", "coordinator_cannot_replace_global_stop"})
    | TRANSITION_ACCEPTED_REASONS
    | TRANSITION_DOMAIN_REJECTED_REASONS
    | GLOBAL_STOP_ACCEPTED_REASONS
    | GLOBAL_STOP_DOMAIN_REJECTED_REASONS
    | APPLY_CONFLICT_REASONS
    | PRE_APPLY_REASONS
)
SAFE_FAILURE_CLASSES = frozenset(
    {
        "budget_exhausted",
        "dependencies_not_satisfied",
        "evidence_required",
        "global_stop_active",
        "lease_identity_invalid",
        "invalid_predecessor",
        "lease_expired",
        "lease_not_authorized",
        "lease_revoked",
        "not_executable",
        "operator_action_required",
        "stage_not_enabled",
        "terminal_state",
        "validation_failed",
    }
)

_SAFE_LABEL_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.:\-\[\]]*")
_SAFE_FIELD_PATH_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.\-\[\]]*")
_SENSITIVE_REF_FRAGMENTS = (
    "secret",
    "password",
    "credential",
    "private-key",
    "private_key",
    "certificate",
    "trust-root",
    "trust_root",
    "bearer",
    "api-key",
    "api_key",
    "raw-prompt",
    "raw_prompt",
    "raw-log",
    "raw_log",
    "private-brief",
    "private_brief",
    "endpoint",
    "url",
    "uri",
)


@dataclass(frozen=True)
class Decision:
    status: DecisionStatus
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", require_decision_status(self.status, "decision.status"))
        object.__setattr__(self, "reason", require_reason_class(self.reason, "decision.reason"))

    @property
    def accepted(self) -> bool:
        return self.status is DecisionStatus.ACCEPTED


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "field", require_safe_field_path(self.field, "validation_issue.field"))
        object.__setattr__(self, "reason", require_issue_reason(self.reason, "validation_issue.reason"))


def blocked(reason: str) -> Decision:
    return Decision(status=DecisionStatus.BLOCKED, reason=reason)


def accepted(reason: str = "accepted") -> Decision:
    return Decision(status=DecisionStatus.ACCEPTED, reason=reason)


def require_decision_status(value: Any, field_name: str) -> DecisionStatus:
    if isinstance(value, DecisionStatus):
        return value
    if isinstance(value, str) and value in {status.value for status in DecisionStatus}:
        return DecisionStatus(value)
    raise ValueError(f"invalid_field_type:{field_name}")


def require_safe_label(value: Any, field_name: str, *, max_length: int = 128) -> str:
    text = require_safe_string(value, field_name, max_length=max_length)
    if not _SAFE_LABEL_RE.fullmatch(text):
        raise ValueError(f"invalid_field_type:{field_name}")
    return text


def require_safe_field_path(value: Any, field_name: str, *, max_length: int = 128) -> str:
    text = require_safe_string(value, field_name, max_length=max_length)
    if not _SAFE_FIELD_PATH_RE.fullmatch(text):
        raise ValueError(f"invalid_field_type:{field_name}")
    return text


def require_contract_ref(value: Any, field_name: str, *, max_length: int = 96) -> str:
    ref = require_safe_ref(value, field_name, max_length=max_length)
    lowered = ref.lower()
    if any(fragment in lowered for fragment in _SENSITIVE_REF_FRAGMENTS):
        raise ValueError(f"invalid_field_type:{field_name}")
    return ref


def require_reason_class(value: Any, field_name: str) -> str:
    reason = require_safe_label(value, field_name, max_length=96)
    if reason not in SAFE_DECISION_REASONS:
        raise ValueError(f"invalid_field_type:{field_name}")
    return reason


def require_issue_reason(value: Any, field_name: str) -> str:
    reason = require_safe_label(value, field_name, max_length=128)
    if reason not in SAFE_DECISION_REASONS:
        raise ValueError(f"invalid_field_type:{field_name}")
    return reason


def require_transition_event_reason(value: Any, field_name: str, *, accepted: bool) -> str:
    reason = require_reason_class(value, field_name)
    allowed = TRANSITION_ACCEPTED_REASONS if accepted else TRANSITION_DOMAIN_REJECTED_REASONS
    if reason not in allowed:
        raise ValueError(f"invalid_field_value:{field_name}")
    return reason


def require_global_stop_event_reason(value: Any, field_name: str, *, accepted: bool) -> str:
    reason = require_reason_class(value, field_name)
    allowed = GLOBAL_STOP_ACCEPTED_REASONS if accepted else GLOBAL_STOP_DOMAIN_REJECTED_REASONS
    if reason not in allowed:
        raise ValueError(f"invalid_field_value:{field_name}")
    return reason


def require_apply_conflict_reason(value: Any, field_name: str) -> str:
    reason = require_reason_class(value, field_name)
    if reason not in APPLY_CONFLICT_REASONS:
        raise ValueError(f"invalid_field_value:{field_name}")
    return reason


def require_safe_failure_class(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    failure_class = require_string(value, field_name)
    if failure_class not in SAFE_FAILURE_CLASSES:
        raise ValueError(f"invalid_field_type:{field_name}")
    return failure_class


def safe_issue_from_exception(exc: Exception) -> ValidationIssue:
    message = str(exc)
    reason = "invalid_field_type"
    field = "value"
    if ":" in message:
        candidate_reason, candidate_field = message.split(":", 1)
        if candidate_reason in SAFE_DECISION_REASONS:
            reason = candidate_reason
            field = candidate_field
    else:
        field = message.split(" ", 1)[0]
        if "greater than zero" in message:
            reason = "invalid_field_value"
        elif "unsupported" in message and "schema_id" in message:
            reason = "unsupported_schema_id"
            field = "schema_id"
        elif "unsupported" in message and "schema_version" in message:
            reason = "unsupported_schema_version"
            field = "schema_version"
    try:
        safe_field = require_safe_field_path(field, "validation_issue.field")
    except ValueError:
        safe_field = "value"
        reason = "invalid_field_type"
    return ValidationIssue(field=safe_field, reason=reason)
