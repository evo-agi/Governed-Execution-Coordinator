"""Operator-owned global-stop models and pure update evaluator."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from ge_nwp_coordinator.canonicalization import (
    canonical_json_bytes,
    canonical_sha256,
    decode_json_object,
    require_bool,
    require_exact_keys,
    require_non_negative_int,
    require_safe_string,
    require_string,
)
from ge_nwp_coordinator.lease import require_digest
from ge_nwp_coordinator.models import (
    Decision,
    DecisionStatus,
    require_contract_ref,
    require_global_stop_event_reason,
    require_reason_class,
)

GLOBAL_STOP_SCHEMA_ID = "governed-execution.nwp-global-stop.v1"
GLOBAL_STOP_COMMAND_SCHEMA_ID = "governed-execution.nwp-global-stop-command.v1"
GLOBAL_STOP_EVENT_SCHEMA_ID = "governed-execution.nwp-global-stop-event.v1"
GLOBAL_STOP_OPERATOR_DECISION_SCHEMA_ID = "governed-execution.nwp-global-stop-operator-decision.v1"
GLOBAL_STOP_CLEAR_REF = "global-stop-clear"

GLOBAL_STOP_COMMAND_KEYS = frozenset(
    {
        "schema_id",
        "action",
        "idempotency_key",
        "expected_version",
        "source_stop_id",
        "stop_id",
        "reason_class",
        "issuer_ref",
        "issued_at",
        "operator_decision_ref",
        "canonical_command_digest",
    }
)
GLOBAL_STOP_STATE_KEYS = frozenset(
    {
        "schema_id",
        "version",
        "active",
        "stop_id",
        "reason_class",
        "issuer_ref",
        "issued_at",
        "operator_decision_ref",
    }
)


class GlobalStopTransitionClass(str, Enum):
    LEASE_ADMISSION = "lease_admission"
    READY = "ready"
    CYCLE_START = "cycle_start"
    RETRY = "retry"
    REPAIR = "repair"
    COMMIT_ELIGIBILITY = "commit_eligibility"


class GlobalStopReasonClass(str, Enum):
    OPERATOR_STOP = "operator_stop"
    POLICY_STOP = "policy_stop"
    SAFETY_STOP = "safety_stop"


class GlobalStopAction(str, Enum):
    ACTIVATE = "activate"
    REPLACE = "replace"
    CLEAR = "clear"


class GlobalStopStatus(str, Enum):
    ACTIVE = "active"
    CLEAR = "clear"


class GlobalStopEventOutcome(str, Enum):
    ACCEPTED = "accepted"
    DOMAIN_REJECTED = "domain_rejected"


class GlobalStopEvaluationKind(str, Enum):
    ACCEPTED = "accepted"
    DOMAIN_REJECTED = "domain_rejected"
    PRE_APPLY_INVALID = "pre_apply_invalid"


@dataclass(frozen=True)
class GlobalStopState:
    schema_id: str = GLOBAL_STOP_SCHEMA_ID
    version: int = 0
    active: bool = False
    stop_id: str | None = None
    reason_class: GlobalStopReasonClass | None = None
    issuer_ref: str | None = None
    issued_at: str | None = None
    operator_decision_ref: str | None = None

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "global_stop.schema_id") != GLOBAL_STOP_SCHEMA_ID:
            raise ValueError("invalid_field_type:global_stop.schema_id")
        object.__setattr__(self, "version", require_non_negative_int(self.version, "global_stop.version"))
        object.__setattr__(self, "active", require_bool(self.active, "global_stop.active"))
        if self.active:
            if self.stop_id is None:
                raise ValueError("missing_field:global_stop.stop_id")
            if self.reason_class is None:
                raise ValueError("missing_field:global_stop.reason_class")
            if self.issuer_ref is None:
                raise ValueError("missing_field:global_stop.issuer_ref")
            if self.issued_at is None:
                raise ValueError("missing_field:global_stop.issued_at")
            if self.operator_decision_ref is None:
                raise ValueError("missing_field:global_stop.operator_decision_ref")
            object.__setattr__(self, "stop_id", require_contract_ref(self.stop_id, "global_stop.stop_id"))
            object.__setattr__(
                self,
                "reason_class",
                _require_global_stop_reason(self.reason_class, "global_stop.reason_class"),
            )
            object.__setattr__(self, "issuer_ref", require_contract_ref(self.issuer_ref, "global_stop.issuer_ref"))
            object.__setattr__(self, "issued_at", _require_timestamp(self.issued_at, "global_stop.issued_at"))
            object.__setattr__(
                self,
                "operator_decision_ref",
                require_contract_ref(self.operator_decision_ref, "global_stop.operator_decision_ref"),
            )
        elif any(
            value is not None
            for value in (
                self.stop_id,
                self.reason_class,
                self.issuer_ref,
                self.issued_at,
                self.operator_decision_ref,
            )
        ):
            raise ValueError("invalid_field_value:global_stop.clear_state")

    @property
    def stop_ref(self) -> str:
        return self.stop_id if self.active and self.stop_id is not None else GLOBAL_STOP_CLEAR_REF

    @property
    def status(self) -> GlobalStopStatus:
        return GlobalStopStatus.ACTIVE if self.active else GlobalStopStatus.CLEAR

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GlobalStopState":
        raw = require_exact_keys(payload, "global_stop", GLOBAL_STOP_STATE_KEYS)
        return cls(
            schema_id=raw.get("schema_id"),
            version=raw.get("version"),
            active=raw.get("active"),
            stop_id=raw.get("stop_id"),
            reason_class=raw.get("reason_class"),
            issuer_ref=raw.get("issuer_ref"),
            issued_at=raw.get("issued_at"),
            operator_decision_ref=raw.get("operator_decision_ref"),
        )

    @classmethod
    def from_json(cls, text: str) -> "GlobalStopState":
        return cls.from_dict(decode_json_object(text, "global_stop"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "version": self.version,
            "active": self.active,
            "stop_id": self.stop_id,
            "reason_class": self.reason_class.value if self.reason_class is not None else None,
            "issuer_ref": self.issuer_ref,
            "issued_at": self.issued_at,
            "operator_decision_ref": self.operator_decision_ref,
        }

    def canonical_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def canonical_json(self) -> str:
        return self.canonical_json_bytes().decode("utf-8")

    def canonical_digest(self) -> str:
        return canonical_sha256(self.to_dict())


@dataclass(frozen=True)
class GlobalStopOperatorDecision:
    decision_ref: str
    authorized: bool
    reason: str
    schema_id: str = GLOBAL_STOP_OPERATOR_DECISION_SCHEMA_ID

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "global_stop_operator_decision.schema_id") != GLOBAL_STOP_OPERATOR_DECISION_SCHEMA_ID:
            raise ValueError("invalid_field_type:global_stop_operator_decision.schema_id")
        object.__setattr__(
            self,
            "decision_ref",
            require_contract_ref(self.decision_ref, "global_stop_operator_decision.decision_ref"),
        )
        object.__setattr__(
            self,
            "authorized",
            require_bool(self.authorized, "global_stop_operator_decision.authorized"),
        )
        object.__setattr__(self, "reason", require_reason_class(self.reason, "global_stop_operator_decision.reason"))
        if self.authorized and self.reason != "accepted":
            raise ValueError("invalid_field_value:global_stop_operator_decision.reason")
        if not self.authorized and self.reason != "operator_authorization_required":
            raise ValueError("invalid_field_value:global_stop_operator_decision.reason")


@dataclass(frozen=True)
class GlobalStopCommand:
    action: GlobalStopAction
    idempotency_key: str
    expected_version: int
    source_stop_id: str | None
    stop_id: str
    reason_class: GlobalStopReasonClass
    issuer_ref: str
    issued_at: str
    operator_decision_ref: str
    canonical_command_digest: str
    schema_id: str = GLOBAL_STOP_COMMAND_SCHEMA_ID

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "global_stop_command.schema_id") != GLOBAL_STOP_COMMAND_SCHEMA_ID:
            raise ValueError("invalid_field_type:global_stop_command.schema_id")
        object.__setattr__(self, "action", _require_action(self.action, "global_stop_command.action"))
        object.__setattr__(
            self,
            "idempotency_key",
            require_contract_ref(self.idempotency_key, "global_stop_command.idempotency_key"),
        )
        object.__setattr__(
            self,
            "expected_version",
            require_non_negative_int(self.expected_version, "global_stop_command.expected_version"),
        )
        if self.source_stop_id is not None:
            object.__setattr__(
                self,
                "source_stop_id",
                require_contract_ref(self.source_stop_id, "global_stop_command.source_stop_id"),
            )
        object.__setattr__(self, "stop_id", require_contract_ref(self.stop_id, "global_stop_command.stop_id"))
        object.__setattr__(
            self,
            "reason_class",
            _require_global_stop_reason(self.reason_class, "global_stop_command.reason_class"),
        )
        object.__setattr__(self, "issuer_ref", require_contract_ref(self.issuer_ref, "global_stop_command.issuer_ref"))
        object.__setattr__(self, "issued_at", _require_timestamp(self.issued_at, "global_stop_command.issued_at"))
        object.__setattr__(
            self,
            "operator_decision_ref",
            require_contract_ref(self.operator_decision_ref, "global_stop_command.operator_decision_ref"),
        )
        object.__setattr__(
            self,
            "canonical_command_digest",
            require_digest(self.canonical_command_digest, "global_stop_command.canonical_command_digest"),
        )
        if self.action is GlobalStopAction.ACTIVATE and self.source_stop_id is not None:
            raise ValueError("invalid_field_value:global_stop_command.source_stop_id")
        if self.action in {GlobalStopAction.REPLACE, GlobalStopAction.CLEAR} and self.source_stop_id is None:
            raise ValueError("missing_field:global_stop_command.source_stop_id")
        if self.canonical_command_digest != self.compute_digest():
            raise ValueError("global_stop_command_digest_mismatch")

    @classmethod
    def create(
        cls,
        *,
        action: GlobalStopAction | str,
        idempotency_key: str,
        expected_version: int,
        stop_id: str,
        reason_class: GlobalStopReasonClass | str,
        issuer_ref: str,
        issued_at: str,
        operator_decision_ref: str,
        source_stop_id: str | None = None,
    ) -> "GlobalStopCommand":
        payload = {
            "schema_id": GLOBAL_STOP_COMMAND_SCHEMA_ID,
            "action": _require_action(action, "global_stop_command.action").value,
            "idempotency_key": require_contract_ref(idempotency_key, "global_stop_command.idempotency_key"),
            "expected_version": require_non_negative_int(expected_version, "global_stop_command.expected_version"),
            "source_stop_id": (
                require_contract_ref(source_stop_id, "global_stop_command.source_stop_id")
                if source_stop_id is not None
                else None
            ),
            "stop_id": require_contract_ref(stop_id, "global_stop_command.stop_id"),
            "reason_class": _require_global_stop_reason(reason_class, "global_stop_command.reason_class").value,
            "issuer_ref": require_contract_ref(issuer_ref, "global_stop_command.issuer_ref"),
            "issued_at": _require_timestamp(issued_at, "global_stop_command.issued_at"),
            "operator_decision_ref": require_contract_ref(
                operator_decision_ref,
                "global_stop_command.operator_decision_ref",
            ),
        }
        return cls(
            action=GlobalStopAction(payload["action"]),
            idempotency_key=payload["idempotency_key"],
            expected_version=payload["expected_version"],
            source_stop_id=payload["source_stop_id"],
            stop_id=payload["stop_id"],
            reason_class=GlobalStopReasonClass(payload["reason_class"]),
            issuer_ref=payload["issuer_ref"],
            issued_at=payload["issued_at"],
            operator_decision_ref=payload["operator_decision_ref"],
            canonical_command_digest=canonical_sha256(payload),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GlobalStopCommand":
        raw = require_exact_keys(payload, "global_stop_command", GLOBAL_STOP_COMMAND_KEYS)
        return cls(
            schema_id=raw.get("schema_id"),
            action=raw.get("action"),
            idempotency_key=raw.get("idempotency_key"),
            expected_version=raw.get("expected_version"),
            source_stop_id=raw.get("source_stop_id"),
            stop_id=raw.get("stop_id"),
            reason_class=raw.get("reason_class"),
            issuer_ref=raw.get("issuer_ref"),
            issued_at=raw.get("issued_at"),
            operator_decision_ref=raw.get("operator_decision_ref"),
            canonical_command_digest=raw.get("canonical_command_digest"),
        )

    @classmethod
    def from_json(cls, text: str) -> "GlobalStopCommand":
        return cls.from_dict(decode_json_object(text, "global_stop_command"))

    def canonical_identity_payload(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "action": self.action.value,
            "idempotency_key": self.idempotency_key,
            "expected_version": self.expected_version,
            "source_stop_id": self.source_stop_id,
            "stop_id": self.stop_id,
            "reason_class": self.reason_class.value,
            "issuer_ref": self.issuer_ref,
            "issued_at": self.issued_at,
            "operator_decision_ref": self.operator_decision_ref,
        }

    def compute_digest(self) -> str:
        return canonical_sha256(self.canonical_identity_payload())


@dataclass(frozen=True)
class GlobalStopEvent:
    event_ref: str
    command_digest: str
    idempotency_key: str
    action: GlobalStopAction
    source_version: int
    resulting_version: int
    outcome: GlobalStopEventOutcome
    reason: str
    operator_decision_ref: str
    resulting_global_stop_ref: str
    resulting_status: GlobalStopStatus
    schema_id: str = GLOBAL_STOP_EVENT_SCHEMA_ID

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "global_stop_event.schema_id") != GLOBAL_STOP_EVENT_SCHEMA_ID:
            raise ValueError("invalid_field_type:global_stop_event.schema_id")
        object.__setattr__(self, "event_ref", require_contract_ref(self.event_ref, "global_stop_event.event_ref"))
        object.__setattr__(self, "command_digest", require_digest(self.command_digest, "global_stop_event.command_digest"))
        object.__setattr__(
            self,
            "idempotency_key",
            require_contract_ref(self.idempotency_key, "global_stop_event.idempotency_key"),
        )
        object.__setattr__(self, "action", _require_action(self.action, "global_stop_event.action"))
        object.__setattr__(
            self,
            "source_version",
            require_non_negative_int(self.source_version, "global_stop_event.source_version"),
        )
        object.__setattr__(
            self,
            "resulting_version",
            require_non_negative_int(self.resulting_version, "global_stop_event.resulting_version"),
        )
        object.__setattr__(self, "outcome", _require_event_outcome(self.outcome, "global_stop_event.outcome"))
        accepted = self.outcome is GlobalStopEventOutcome.ACCEPTED
        object.__setattr__(
            self,
            "reason",
            require_global_stop_event_reason(self.reason, "global_stop_event.reason", accepted=accepted),
        )
        object.__setattr__(
            self,
            "operator_decision_ref",
            require_contract_ref(self.operator_decision_ref, "global_stop_event.operator_decision_ref"),
        )
        object.__setattr__(
            self,
            "resulting_global_stop_ref",
            require_contract_ref(self.resulting_global_stop_ref, "global_stop_event.resulting_global_stop_ref"),
        )
        object.__setattr__(
            self,
            "resulting_status",
            _require_global_stop_status(self.resulting_status, "global_stop_event.resulting_status"),
        )
        if accepted and self.resulting_version != self.source_version + 1:
            raise ValueError("invalid_field_value:global_stop_event.resulting_version")
        if not accepted and self.resulting_version != self.source_version:
            raise ValueError("invalid_field_value:global_stop_event.resulting_version")


@dataclass(frozen=True)
class GlobalStopEvaluation:
    kind: GlobalStopEvaluationKind
    state: GlobalStopState
    event: GlobalStopEvent | None
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _require_evaluation_kind(self.kind, "global_stop_evaluation.kind"))
        if not isinstance(self.state, GlobalStopState):
            raise ValueError("invalid_field_type:global_stop_evaluation.state")
        object.__setattr__(self, "reason", require_reason_class(self.reason, "global_stop_evaluation.reason"))
        if self.kind is GlobalStopEvaluationKind.PRE_APPLY_INVALID:
            if self.event is not None:
                raise ValueError("invalid_field_value:global_stop_evaluation.event")
            return
        if not isinstance(self.event, GlobalStopEvent):
            raise ValueError("invalid_field_type:global_stop_evaluation.event")
        if self.kind.value != self.event.outcome.value or self.reason != self.event.reason:
            raise ValueError("invalid_field_value:global_stop_evaluation.event")

    @property
    def accepted(self) -> bool:
        return self.kind is GlobalStopEvaluationKind.ACCEPTED


def enforce_global_stop(state: GlobalStopState, transition_class: GlobalStopTransitionClass) -> Decision:
    transition_class = _require_transition_class(transition_class, "global_stop.transition_class")
    if state.active:
        return Decision(
            status=DecisionStatus.BLOCKED,
            reason=f"global_stop_active:{transition_class.value}",
        )
    return Decision(status=DecisionStatus.ACCEPTED, reason="global_stop_clear")


def coordinator_clear_global_stop(state: GlobalStopState) -> Decision:
    if state.active:
        return Decision(status=DecisionStatus.BLOCKED, reason="coordinator_cannot_clear_global_stop")
    return Decision(status=DecisionStatus.BLOCKED, reason="coordinator_cannot_replace_global_stop")


def evaluate_global_stop_update(
    state: GlobalStopState,
    command: GlobalStopCommand,
    operator_decision: GlobalStopOperatorDecision,
) -> GlobalStopEvaluation:
    if not isinstance(state, GlobalStopState):
        raise ValueError("invalid_field_type:global_stop_evaluation.state")
    if not isinstance(command, GlobalStopCommand):
        raise ValueError("invalid_field_type:global_stop_evaluation.command")
    if not isinstance(operator_decision, GlobalStopOperatorDecision):
        raise ValueError("invalid_field_type:global_stop_evaluation.operator_decision")
    if command.operator_decision_ref != operator_decision.decision_ref:
        return GlobalStopEvaluation(
            kind=GlobalStopEvaluationKind.PRE_APPLY_INVALID,
            state=state,
            event=None,
            reason="decision_reference_mismatch",
        )
    if not operator_decision.authorized:
        return _global_stop_rejected(state, command, "operator_authorization_required")
    accepted_state = _apply_global_stop_command(state, command)
    if accepted_state is None:
        return _global_stop_rejected(state, command, "global_stop_update_blocked")
    event = _global_stop_event(state, command, accepted_state, GlobalStopEventOutcome.ACCEPTED, "global_stop_update_accepted")
    return GlobalStopEvaluation(
        kind=GlobalStopEvaluationKind.ACCEPTED,
        state=accepted_state,
        event=event,
        reason=event.reason,
    )


def _apply_global_stop_command(state: GlobalStopState, command: GlobalStopCommand) -> GlobalStopState | None:
    if command.action is GlobalStopAction.ACTIVATE:
        if state.active or command.source_stop_id is not None:
            return None
        return GlobalStopState(
            version=state.version + 1,
            active=True,
            stop_id=command.stop_id,
            reason_class=command.reason_class,
            issuer_ref=command.issuer_ref,
            issued_at=command.issued_at,
            operator_decision_ref=command.operator_decision_ref,
        )
    if command.action is GlobalStopAction.REPLACE:
        if not state.active or command.source_stop_id != state.stop_id:
            return None
        return GlobalStopState(
            version=state.version + 1,
            active=True,
            stop_id=command.stop_id,
            reason_class=command.reason_class,
            issuer_ref=command.issuer_ref,
            issued_at=command.issued_at,
            operator_decision_ref=command.operator_decision_ref,
        )
    if command.action is GlobalStopAction.CLEAR:
        if (
            not state.active
            or command.source_stop_id != state.stop_id
            or command.stop_id != state.stop_id
            or command.reason_class is not state.reason_class
            or command.issuer_ref != state.issuer_ref
            or command.issued_at != state.issued_at
        ):
            return None
        return GlobalStopState(version=state.version + 1, active=False)
    raise ValueError("invalid_field_value:global_stop_command.action")


def _global_stop_rejected(state: GlobalStopState, command: GlobalStopCommand, reason: str) -> GlobalStopEvaluation:
    event = _global_stop_event(state, command, state, GlobalStopEventOutcome.DOMAIN_REJECTED, reason)
    return GlobalStopEvaluation(
        kind=GlobalStopEvaluationKind.DOMAIN_REJECTED,
        state=state,
        event=event,
        reason=event.reason,
    )


def _global_stop_event(
    source: GlobalStopState,
    command: GlobalStopCommand,
    resulting_state: GlobalStopState,
    outcome: GlobalStopEventOutcome,
    reason: str,
) -> GlobalStopEvent:
    payload = {
        "schema_id": GLOBAL_STOP_EVENT_SCHEMA_ID,
        "command_digest": command.canonical_command_digest,
        "idempotency_key": command.idempotency_key,
        "action": command.action.value,
        "source_version": source.version,
        "resulting_version": resulting_state.version,
        "outcome": outcome.value,
        "reason": reason,
        "operator_decision_ref": command.operator_decision_ref,
        "resulting_global_stop_ref": resulting_state.stop_ref,
        "resulting_status": resulting_state.status.value,
    }
    return GlobalStopEvent(
        event_ref=f"global-stop-event-{canonical_sha256(payload)[:24]}",
        command_digest=payload["command_digest"],
        idempotency_key=payload["idempotency_key"],
        action=GlobalStopAction(payload["action"]),
        source_version=payload["source_version"],
        resulting_version=payload["resulting_version"],
        outcome=outcome,
        reason=payload["reason"],
        operator_decision_ref=payload["operator_decision_ref"],
        resulting_global_stop_ref=payload["resulting_global_stop_ref"],
        resulting_status=GlobalStopStatus(payload["resulting_status"]),
    )


def _require_transition_class(value: Any, field_name: str) -> GlobalStopTransitionClass:
    if isinstance(value, GlobalStopTransitionClass):
        return value
    raw = require_string(value, field_name)
    if raw not in {transition_class.value for transition_class in GlobalStopTransitionClass}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return GlobalStopTransitionClass(raw)


def _require_global_stop_reason(value: Any, field_name: str) -> GlobalStopReasonClass:
    if isinstance(value, GlobalStopReasonClass):
        return value
    raw = require_string(value, field_name)
    if raw not in {reason.value for reason in GlobalStopReasonClass}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return GlobalStopReasonClass(raw)


def _require_action(value: Any, field_name: str) -> GlobalStopAction:
    if isinstance(value, GlobalStopAction):
        return value
    raw = require_string(value, field_name)
    if raw not in {action.value for action in GlobalStopAction}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return GlobalStopAction(raw)


def _require_global_stop_status(value: Any, field_name: str) -> GlobalStopStatus:
    if isinstance(value, GlobalStopStatus):
        return value
    raw = require_string(value, field_name)
    if raw not in {status.value for status in GlobalStopStatus}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return GlobalStopStatus(raw)


def _require_event_outcome(value: Any, field_name: str) -> GlobalStopEventOutcome:
    if isinstance(value, GlobalStopEventOutcome):
        return value
    raw = require_string(value, field_name)
    if raw not in {outcome.value for outcome in GlobalStopEventOutcome}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return GlobalStopEventOutcome(raw)


def _require_evaluation_kind(value: Any, field_name: str) -> GlobalStopEvaluationKind:
    if isinstance(value, GlobalStopEvaluationKind):
        return value
    raw = require_string(value, field_name)
    if raw not in {kind.value for kind in GlobalStopEvaluationKind}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return GlobalStopEvaluationKind(raw)


def _require_timestamp(value: Any, field_name: str) -> str:
    text = require_safe_string(value, field_name, max_length=64)
    raw = text
    if raw.endswith("Z"):
        raw = f"{raw[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"invalid_field_type:{field_name}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"invalid_field_type:{field_name}")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
