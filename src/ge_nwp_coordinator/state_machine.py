"""Pure A2 work-item transition event algebra."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping

from ge_nwp_coordinator.canonicalization import (
    canonical_json_bytes,
    canonical_sha256,
    decode_json_object,
    require_bool,
    require_exact_keys,
    require_non_negative_int,
    require_string,
)
from ge_nwp_coordinator.global_stop import (
    GLOBAL_STOP_CLEAR_REF,
    GlobalStopState,
    GlobalStopTransitionClass,
    enforce_global_stop,
)
from ge_nwp_coordinator.lease import (
    AuthorizationDecision,
    LeaseIdentityValidation,
    LeaseRuntimeDecision,
    LeaseRuntimeStatus,
    require_digest,
)
from ge_nwp_coordinator.models import (
    ValidationIssue,
    require_contract_ref,
    require_reason_class,
    require_safe_failure_class,
    require_transition_event_reason,
)

WORK_ITEM_STATE_SCHEMA_ID = "governed-execution.nwp-work-item-state.v1"
TRANSITION_COMMAND_SCHEMA_ID = "governed-execution.nwp-transition-command.v1"
TRANSITION_EVENT_SCHEMA_ID = "governed-execution.nwp-transition-event.v1"
DEPENDENCY_DECISION_SCHEMA_ID = "governed-execution.nwp-dependency-decision.v1"
SQLITE_SIGNED_INT_MAX = 9223372036854775807

TRANSITION_COMMAND_KEYS = frozenset(
    {
        "schema_id",
        "work_item_id",
        "idempotency_key",
        "expected_version",
        "target_state",
        "lease_identity_decision_ref",
        "authorization_decision_ref",
        "global_stop_ref",
        "global_stop_version",
        "dependency_decision_ref",
        "evidence_refs",
        "safe_failure_class",
        "budget_cost",
        "canonical_command_digest",
    }
)
DEPENDENCY_DECISION_KEYS = frozenset(
    {
        "schema_id",
        "decision_ref",
        "work_item_id",
        "dependencies_satisfied",
        "reason",
    }
)
TRANSITION_EVENT_KEYS = frozenset(
    {
        "schema_id",
        "event_ref",
        "work_item_id",
        "lease_id",
        "command_digest",
        "idempotency_key",
        "source_state",
        "source_version",
        "resulting_state",
        "resulting_version",
        "outcome",
        "reason",
        "evidence_refs",
        "budget_cost_delta",
        "attempt_count_delta",
        "repair_count_delta",
        "lease_identity_decision_ref",
        "authorization_decision_ref",
        "dependency_decision_ref",
        "lease_runtime",
        "global_stop_ref",
        "global_stop_version",
    }
)
WORK_ITEM_RECORD_KEYS = frozenset(
    {
        "schema_id",
        "work_item_id",
        "lease_id",
        "backlog_id",
        "state",
        "version",
        "attempt_count",
        "repair_count",
        "budget_consumed",
        "budget_limit",
        "max_attempts",
        "max_repairs",
        "cleanup_required",
    }
)


class WorkItemState(str, Enum):
    PROPOSED = "proposed"
    LEASE_ADMITTED = "lease_admitted"
    READY = "ready"
    CYCLE_STARTING = "cycle_starting"
    WORKER_RUNNING = "worker_running"
    VALIDATING = "validating"
    AUDITING = "auditing"
    COMMIT_ELIGIBLE = "commit_eligible"
    LOCAL_COMMIT_COMPLETED = "local_commit_completed"
    REPAIR_ADMITTED = "repair_admitted"
    REPAIR_RUNNING = "repair_running"
    BLOCKED = "blocked"
    FAILED = "failed"
    EXHAUSTED = "exhausted"
    LEASE_EXPIRED = "lease_expired"
    CANCELED_REVOKED = "canceled_revoked"
    CLEANUP_PENDING = "cleanup_pending"
    CLEANUP_COMPLETED = "cleanup_completed"


class TransitionEventOutcome(str, Enum):
    ACCEPTED = "accepted"
    DOMAIN_REJECTED = "domain_rejected"


class TransitionEvaluationKind(str, Enum):
    ACCEPTED = "accepted"
    DOMAIN_REJECTED = "domain_rejected"
    PRE_APPLY_INVALID = "pre_apply_invalid"


TERMINAL_STATES = frozenset(
    {
        WorkItemState.LOCAL_COMMIT_COMPLETED,
        WorkItemState.FAILED,
        WorkItemState.EXHAUSTED,
        WorkItemState.LEASE_EXPIRED,
        WorkItemState.CANCELED_REVOKED,
        WorkItemState.CLEANUP_COMPLETED,
    }
)

P1_DISABLED_TARGET_STATES = frozenset(
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

ALLOWED_PREDECESSORS: dict[WorkItemState, frozenset[WorkItemState]] = {
    WorkItemState.LEASE_ADMITTED: frozenset({WorkItemState.PROPOSED}),
    WorkItemState.READY: frozenset(
        {WorkItemState.LEASE_ADMITTED, WorkItemState.BLOCKED, WorkItemState.CLEANUP_COMPLETED}
    ),
    WorkItemState.CYCLE_STARTING: frozenset({WorkItemState.READY}),
    WorkItemState.WORKER_RUNNING: frozenset({WorkItemState.CYCLE_STARTING}),
    WorkItemState.VALIDATING: frozenset({WorkItemState.WORKER_RUNNING, WorkItemState.REPAIR_RUNNING}),
    WorkItemState.AUDITING: frozenset({WorkItemState.VALIDATING}),
    WorkItemState.COMMIT_ELIGIBLE: frozenset({WorkItemState.AUDITING}),
    WorkItemState.LOCAL_COMMIT_COMPLETED: frozenset({WorkItemState.COMMIT_ELIGIBLE}),
    WorkItemState.REPAIR_ADMITTED: frozenset(
        {WorkItemState.AUDITING, WorkItemState.VALIDATING, WorkItemState.FAILED}
    ),
    WorkItemState.REPAIR_RUNNING: frozenset({WorkItemState.REPAIR_ADMITTED}),
    WorkItemState.BLOCKED: frozenset(set(WorkItemState) - {WorkItemState.CLEANUP_COMPLETED}),
    WorkItemState.FAILED: frozenset(
        {
            WorkItemState.CYCLE_STARTING,
            WorkItemState.WORKER_RUNNING,
            WorkItemState.VALIDATING,
            WorkItemState.AUDITING,
            WorkItemState.REPAIR_RUNNING,
        }
    ),
    WorkItemState.EXHAUSTED: frozenset(
        {WorkItemState.FAILED, WorkItemState.BLOCKED, WorkItemState.REPAIR_ADMITTED}
    ),
    WorkItemState.LEASE_EXPIRED: frozenset(set(WorkItemState) - {WorkItemState.CLEANUP_COMPLETED}),
    WorkItemState.CANCELED_REVOKED: frozenset(set(WorkItemState) - {WorkItemState.CLEANUP_COMPLETED}),
    WorkItemState.CLEANUP_PENDING: frozenset(
        {
            WorkItemState.FAILED,
            WorkItemState.BLOCKED,
            WorkItemState.EXHAUSTED,
            WorkItemState.LEASE_EXPIRED,
            WorkItemState.CANCELED_REVOKED,
            WorkItemState.LOCAL_COMMIT_COMPLETED,
        }
    ),
    WorkItemState.CLEANUP_COMPLETED: frozenset({WorkItemState.CLEANUP_PENDING}),
}

EVIDENCE_REQUIRED_STATES = frozenset(
    {
        WorkItemState.VALIDATING,
        WorkItemState.AUDITING,
        WorkItemState.COMMIT_ELIGIBLE,
        WorkItemState.LOCAL_COMMIT_COMPLETED,
        WorkItemState.FAILED,
        WorkItemState.EXHAUSTED,
        WorkItemState.CANCELED_REVOKED,
        WorkItemState.CLEANUP_COMPLETED,
    }
)


@dataclass(frozen=True)
class DependencyDecision:
    decision_ref: str = "dependencies-clear"
    work_item_id: str | None = None
    dependencies_satisfied: bool = True
    reason: str = "accepted"
    schema_id: str = DEPENDENCY_DECISION_SCHEMA_ID

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "dependency_decision.schema_id") != DEPENDENCY_DECISION_SCHEMA_ID:
            raise ValueError("invalid_field_type:dependency_decision.schema_id")
        object.__setattr__(
            self,
            "decision_ref",
            require_contract_ref(self.decision_ref, "dependency_decision.decision_ref"),
        )
        if self.work_item_id is not None:
            object.__setattr__(
                self,
                "work_item_id",
                require_contract_ref(self.work_item_id, "dependency_decision.work_item_id"),
            )
        object.__setattr__(
            self,
            "dependencies_satisfied",
            require_bool(self.dependencies_satisfied, "dependency_decision.dependencies_satisfied"),
        )
        object.__setattr__(self, "reason", require_reason_class(self.reason, "dependency_decision.reason"))
        if self.dependencies_satisfied and self.reason != "accepted":
            raise ValueError("invalid_field_value:dependency_decision.reason")
        if not self.dependencies_satisfied and self.reason != "dependencies_not_satisfied":
            raise ValueError("invalid_field_value:dependency_decision.reason")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DependencyDecision":
        raw = require_exact_keys(payload, "dependency_decision", DEPENDENCY_DECISION_KEYS)
        return cls(
            schema_id=raw.get("schema_id"),
            decision_ref=raw.get("decision_ref"),
            work_item_id=raw.get("work_item_id"),
            dependencies_satisfied=raw.get("dependencies_satisfied"),
            reason=raw.get("reason"),
        )

    @classmethod
    def from_json(cls, text: str) -> "DependencyDecision":
        return cls.from_dict(decode_json_object(text, "dependency_decision"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "decision_ref": self.decision_ref,
            "work_item_id": self.work_item_id,
            "dependencies_satisfied": self.dependencies_satisfied,
            "reason": self.reason,
        }

    def canonical_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def canonical_json(self) -> str:
        return self.canonical_json_bytes().decode("utf-8")

    def canonical_digest(self) -> str:
        return canonical_sha256(self.to_dict())


@dataclass(frozen=True)
class TransitionContext:
    lease_identity: LeaseIdentityValidation
    authorization: AuthorizationDecision
    lease_runtime: LeaseRuntimeDecision
    global_stop: GlobalStopState = field(default_factory=GlobalStopState)
    dependency_decision: DependencyDecision = field(default_factory=DependencyDecision)

    def __post_init__(self) -> None:
        if not isinstance(self.lease_identity, LeaseIdentityValidation):
            raise ValueError("invalid_field_type:transition_context.lease_identity")
        if not isinstance(self.authorization, AuthorizationDecision):
            raise ValueError("invalid_field_type:transition_context.authorization")
        if not isinstance(self.lease_runtime, LeaseRuntimeDecision):
            raise ValueError("invalid_field_type:transition_context.lease_runtime")
        if not isinstance(self.global_stop, GlobalStopState):
            raise ValueError("invalid_field_type:transition_context.global_stop")
        if not isinstance(self.dependency_decision, DependencyDecision):
            raise ValueError("invalid_field_type:transition_context.dependency_decision")


@dataclass(frozen=True)
class TransitionCommand:
    work_item_id: str
    idempotency_key: str
    expected_version: int
    target_state: WorkItemState
    lease_identity_decision_ref: str
    authorization_decision_ref: str
    global_stop_ref: str
    global_stop_version: int
    dependency_decision_ref: str | None
    evidence_refs: tuple[str, ...]
    budget_cost: int
    canonical_command_digest: str
    safe_failure_class: str | None = None
    schema_id: str = TRANSITION_COMMAND_SCHEMA_ID

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "transition_command.schema_id") != TRANSITION_COMMAND_SCHEMA_ID:
            raise ValueError("invalid_field_type:transition_command.schema_id")
        object.__setattr__(self, "work_item_id", require_contract_ref(self.work_item_id, "transition_command.work_item_id"))
        object.__setattr__(
            self,
            "idempotency_key",
            require_contract_ref(self.idempotency_key, "transition_command.idempotency_key"),
        )
        object.__setattr__(
            self,
            "expected_version",
            require_non_negative_int(self.expected_version, "transition_command.expected_version"),
        )
        object.__setattr__(self, "target_state", require_work_item_state(self.target_state, "transition_command.target_state"))
        object.__setattr__(
            self,
            "lease_identity_decision_ref",
            require_contract_ref(
                self.lease_identity_decision_ref,
                "transition_command.lease_identity_decision_ref",
            ),
        )
        object.__setattr__(
            self,
            "authorization_decision_ref",
            require_contract_ref(self.authorization_decision_ref, "transition_command.authorization_decision_ref"),
        )
        object.__setattr__(
            self,
            "global_stop_ref",
            require_contract_ref(self.global_stop_ref, "transition_command.global_stop_ref"),
        )
        object.__setattr__(
            self,
            "global_stop_version",
            require_non_negative_int(self.global_stop_version, "transition_command.global_stop_version"),
        )
        if self.dependency_decision_ref is not None:
            object.__setattr__(
                self,
                "dependency_decision_ref",
                require_contract_ref(self.dependency_decision_ref, "transition_command.dependency_decision_ref"),
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _require_contract_ref_tuple(self.evidence_refs, "transition_command.evidence_refs"),
        )
        object.__setattr__(
            self,
            "safe_failure_class",
            require_safe_failure_class(self.safe_failure_class, "transition_command.safe_failure_class"),
        )
        object.__setattr__(
            self,
            "budget_cost",
            require_non_negative_int(self.budget_cost, "transition_command.budget_cost"),
        )
        object.__setattr__(
            self,
            "canonical_command_digest",
            require_digest(self.canonical_command_digest, "transition_command.canonical_command_digest"),
        )
        if self.canonical_command_digest != self.compute_digest():
            raise ValueError("transition_command_digest_mismatch")

    @classmethod
    def create(
        cls,
        *,
        work_item_id: str,
        idempotency_key: str,
        expected_version: int,
        target_state: WorkItemState | str,
        lease_identity_decision_ref: str,
        authorization_decision_ref: str,
        global_stop_ref: str = GLOBAL_STOP_CLEAR_REF,
        global_stop_version: int = 0,
        dependency_decision_ref: str | None = None,
        evidence_refs: tuple[str, ...] = (),
        safe_failure_class: str | None = None,
        budget_cost: int = 0,
    ) -> "TransitionCommand":
        payload = {
            "schema_id": TRANSITION_COMMAND_SCHEMA_ID,
            "work_item_id": require_contract_ref(work_item_id, "transition_command.work_item_id"),
            "idempotency_key": require_contract_ref(idempotency_key, "transition_command.idempotency_key"),
            "expected_version": require_non_negative_int(expected_version, "transition_command.expected_version"),
            "target_state": require_work_item_state(target_state, "transition_command.target_state").value,
            "lease_identity_decision_ref": require_contract_ref(
                lease_identity_decision_ref,
                "transition_command.lease_identity_decision_ref",
            ),
            "authorization_decision_ref": require_contract_ref(
                authorization_decision_ref,
                "transition_command.authorization_decision_ref",
            ),
            "global_stop_ref": require_contract_ref(global_stop_ref, "transition_command.global_stop_ref"),
            "global_stop_version": require_non_negative_int(
                global_stop_version,
                "transition_command.global_stop_version",
            ),
            "dependency_decision_ref": (
                require_contract_ref(dependency_decision_ref, "transition_command.dependency_decision_ref")
                if dependency_decision_ref is not None
                else None
            ),
            "evidence_refs": _require_contract_ref_tuple(evidence_refs, "transition_command.evidence_refs"),
            "safe_failure_class": require_safe_failure_class(
                safe_failure_class,
                "transition_command.safe_failure_class",
            ),
            "budget_cost": require_non_negative_int(budget_cost, "transition_command.budget_cost"),
        }
        return cls(
            work_item_id=payload["work_item_id"],
            idempotency_key=payload["idempotency_key"],
            expected_version=payload["expected_version"],
            target_state=WorkItemState(payload["target_state"]),
            lease_identity_decision_ref=payload["lease_identity_decision_ref"],
            authorization_decision_ref=payload["authorization_decision_ref"],
            global_stop_ref=payload["global_stop_ref"],
            global_stop_version=payload["global_stop_version"],
            dependency_decision_ref=payload["dependency_decision_ref"],
            evidence_refs=payload["evidence_refs"],
            safe_failure_class=payload["safe_failure_class"],
            budget_cost=payload["budget_cost"],
            canonical_command_digest=canonical_sha256(payload),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TransitionCommand":
        raw = require_exact_keys(payload, "transition_command", TRANSITION_COMMAND_KEYS)
        evidence_refs = _require_external_contract_ref_list(
            raw.get("evidence_refs"),
            "transition_command.evidence_refs",
        )
        return cls(
            schema_id=raw.get("schema_id"),
            work_item_id=raw.get("work_item_id"),
            idempotency_key=raw.get("idempotency_key"),
            expected_version=raw.get("expected_version"),
            target_state=raw.get("target_state"),
            lease_identity_decision_ref=raw.get("lease_identity_decision_ref"),
            authorization_decision_ref=raw.get("authorization_decision_ref"),
            global_stop_ref=raw.get("global_stop_ref"),
            global_stop_version=raw.get("global_stop_version"),
            dependency_decision_ref=raw.get("dependency_decision_ref"),
            evidence_refs=evidence_refs,
            safe_failure_class=raw.get("safe_failure_class"),
            budget_cost=raw.get("budget_cost"),
            canonical_command_digest=raw.get("canonical_command_digest"),
        )

    @classmethod
    def from_json(cls, text: str) -> "TransitionCommand":
        return cls.from_dict(decode_json_object(text, "transition_command"))

    def canonical_identity_payload(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "work_item_id": self.work_item_id,
            "idempotency_key": self.idempotency_key,
            "expected_version": self.expected_version,
            "target_state": self.target_state.value,
            "lease_identity_decision_ref": self.lease_identity_decision_ref,
            "authorization_decision_ref": self.authorization_decision_ref,
            "global_stop_ref": self.global_stop_ref,
            "global_stop_version": self.global_stop_version,
            "dependency_decision_ref": self.dependency_decision_ref,
            "evidence_refs": self.evidence_refs,
            "safe_failure_class": self.safe_failure_class,
            "budget_cost": self.budget_cost,
        }

    def compute_digest(self) -> str:
        return canonical_sha256(self.canonical_identity_payload())


@dataclass(frozen=True)
class TransitionEvent:
    event_ref: str
    work_item_id: str
    lease_id: str
    command_digest: str
    idempotency_key: str
    source_state: WorkItemState
    source_version: int
    resulting_state: WorkItemState
    resulting_version: int
    outcome: TransitionEventOutcome
    reason: str
    evidence_refs: tuple[str, ...]
    budget_cost_delta: int
    attempt_count_delta: int
    repair_count_delta: int
    lease_identity_decision_ref: str
    authorization_decision_ref: str
    dependency_decision_ref: str | None
    lease_runtime: LeaseRuntimeDecision
    global_stop_ref: str
    global_stop_version: int
    schema_id: str = TRANSITION_EVENT_SCHEMA_ID

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "transition_event.schema_id") != TRANSITION_EVENT_SCHEMA_ID:
            raise ValueError("invalid_field_type:transition_event.schema_id")
        object.__setattr__(self, "event_ref", require_contract_ref(self.event_ref, "transition_event.event_ref"))
        object.__setattr__(self, "work_item_id", require_contract_ref(self.work_item_id, "transition_event.work_item_id"))
        object.__setattr__(self, "lease_id", require_contract_ref(self.lease_id, "transition_event.lease_id"))
        object.__setattr__(
            self,
            "command_digest",
            require_digest(self.command_digest, "transition_event.command_digest"),
        )
        object.__setattr__(
            self,
            "idempotency_key",
            require_contract_ref(self.idempotency_key, "transition_event.idempotency_key"),
        )
        object.__setattr__(self, "source_state", require_work_item_state(self.source_state, "transition_event.source_state"))
        object.__setattr__(
            self,
            "source_version",
            require_non_negative_int(self.source_version, "transition_event.source_version"),
        )
        object.__setattr__(
            self,
            "resulting_state",
            require_work_item_state(self.resulting_state, "transition_event.resulting_state"),
        )
        object.__setattr__(
            self,
            "resulting_version",
            require_non_negative_int(self.resulting_version, "transition_event.resulting_version"),
        )
        object.__setattr__(self, "outcome", _require_event_outcome(self.outcome, "transition_event.outcome"))
        accepted = self.outcome is TransitionEventOutcome.ACCEPTED
        object.__setattr__(
            self,
            "reason",
            require_transition_event_reason(self.reason, "transition_event.reason", accepted=accepted),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _require_contract_ref_tuple(self.evidence_refs, "transition_event.evidence_refs"),
        )
        object.__setattr__(
            self,
            "budget_cost_delta",
            require_non_negative_int(self.budget_cost_delta, "transition_event.budget_cost_delta"),
        )
        object.__setattr__(
            self,
            "attempt_count_delta",
            require_non_negative_int(self.attempt_count_delta, "transition_event.attempt_count_delta"),
        )
        object.__setattr__(
            self,
            "repair_count_delta",
            require_non_negative_int(self.repair_count_delta, "transition_event.repair_count_delta"),
        )
        object.__setattr__(
            self,
            "lease_identity_decision_ref",
            require_contract_ref(
                self.lease_identity_decision_ref,
                "transition_event.lease_identity_decision_ref",
            ),
        )
        object.__setattr__(
            self,
            "authorization_decision_ref",
            require_contract_ref(self.authorization_decision_ref, "transition_event.authorization_decision_ref"),
        )
        if self.dependency_decision_ref is not None:
            object.__setattr__(
                self,
                "dependency_decision_ref",
                require_contract_ref(self.dependency_decision_ref, "transition_event.dependency_decision_ref"),
            )
        if type(self.lease_runtime) is not LeaseRuntimeDecision:
            raise ValueError("invalid_field_type:transition_event.lease_runtime")
        if self.lease_runtime.lease_ref != self.lease_id:
            raise ValueError("invalid_field_value:transition_event.lease_runtime")
        object.__setattr__(
            self,
            "global_stop_ref",
            require_contract_ref(self.global_stop_ref, "transition_event.global_stop_ref"),
        )
        object.__setattr__(
            self,
            "global_stop_version",
            require_non_negative_int(self.global_stop_version, "transition_event.global_stop_version"),
        )
        if accepted and self.resulting_version != self.source_version + 1:
            raise ValueError("invalid_field_value:transition_event.resulting_version")
        if not accepted:
            if self.resulting_state is not self.source_state or self.resulting_version != self.source_version:
                raise ValueError("invalid_field_value:transition_event.result")
            if self.budget_cost_delta or self.attempt_count_delta or self.repair_count_delta:
                raise ValueError("invalid_field_value:transition_event.deltas")
        if self.event_ref != self.compute_event_ref():
            raise ValueError("invalid_field_value:transition_event.event_ref")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TransitionEvent":
        raw = require_exact_keys(payload, "transition_event", TRANSITION_EVENT_KEYS)
        evidence_refs = _require_external_contract_ref_list(raw.get("evidence_refs"), "transition_event.evidence_refs")
        return cls(
            schema_id=raw.get("schema_id"),
            event_ref=raw.get("event_ref"),
            work_item_id=raw.get("work_item_id"),
            lease_id=raw.get("lease_id"),
            command_digest=raw.get("command_digest"),
            idempotency_key=raw.get("idempotency_key"),
            source_state=raw.get("source_state"),
            source_version=raw.get("source_version"),
            resulting_state=raw.get("resulting_state"),
            resulting_version=raw.get("resulting_version"),
            outcome=raw.get("outcome"),
            reason=raw.get("reason"),
            evidence_refs=evidence_refs,
            budget_cost_delta=raw.get("budget_cost_delta"),
            attempt_count_delta=raw.get("attempt_count_delta"),
            repair_count_delta=raw.get("repair_count_delta"),
            lease_identity_decision_ref=raw.get("lease_identity_decision_ref"),
            authorization_decision_ref=raw.get("authorization_decision_ref"),
            dependency_decision_ref=raw.get("dependency_decision_ref"),
            lease_runtime=LeaseRuntimeDecision.from_dict(raw.get("lease_runtime")),
            global_stop_ref=raw.get("global_stop_ref"),
            global_stop_version=raw.get("global_stop_version"),
        )

    @classmethod
    def from_json(cls, text: str) -> "TransitionEvent":
        return cls.from_dict(decode_json_object(text, "transition_event"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "event_ref": self.event_ref,
            "work_item_id": self.work_item_id,
            "lease_id": self.lease_id,
            "command_digest": self.command_digest,
            "idempotency_key": self.idempotency_key,
            "source_state": self.source_state.value,
            "source_version": self.source_version,
            "resulting_state": self.resulting_state.value,
            "resulting_version": self.resulting_version,
            "outcome": self.outcome.value,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
            "budget_cost_delta": self.budget_cost_delta,
            "attempt_count_delta": self.attempt_count_delta,
            "repair_count_delta": self.repair_count_delta,
            "lease_identity_decision_ref": self.lease_identity_decision_ref,
            "authorization_decision_ref": self.authorization_decision_ref,
            "dependency_decision_ref": self.dependency_decision_ref,
            "lease_runtime": self.lease_runtime.to_dict(),
            "global_stop_ref": self.global_stop_ref,
            "global_stop_version": self.global_stop_version,
        }

    def canonical_event_ref_payload(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("event_ref")
        return payload

    def compute_event_ref(self) -> str:
        return f"transition-event-{canonical_sha256(self.canonical_event_ref_payload())[:24]}"

    def canonical_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def canonical_json(self) -> str:
        return self.canonical_json_bytes().decode("utf-8")

    def canonical_digest(self) -> str:
        return canonical_sha256(self.to_dict())


@dataclass(frozen=True)
class WorkItemRecord:
    work_item_id: str
    lease_id: str
    backlog_id: str
    state: WorkItemState = WorkItemState.PROPOSED
    version: int = 0
    attempt_count: int = 0
    repair_count: int = 0
    budget_consumed: int = 0
    budget_limit: int = 0
    max_attempts: int = 1
    max_repairs: int = 0
    cleanup_required: bool = False
    schema_id: str = WORK_ITEM_STATE_SCHEMA_ID

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "work_item.schema_id") != WORK_ITEM_STATE_SCHEMA_ID:
            raise ValueError("invalid_field_type:work_item.schema_id")
        object.__setattr__(self, "work_item_id", require_contract_ref(self.work_item_id, "work_item.work_item_id"))
        object.__setattr__(self, "lease_id", require_contract_ref(self.lease_id, "work_item.lease_id"))
        object.__setattr__(self, "backlog_id", require_contract_ref(self.backlog_id, "work_item.backlog_id"))
        object.__setattr__(self, "state", require_work_item_state(self.state, "work_item.state"))
        object.__setattr__(self, "version", require_non_negative_int(self.version, "work_item.version"))
        object.__setattr__(self, "attempt_count", require_non_negative_int(self.attempt_count, "work_item.attempt_count"))
        object.__setattr__(self, "repair_count", require_non_negative_int(self.repair_count, "work_item.repair_count"))
        object.__setattr__(
            self,
            "budget_consumed",
            require_non_negative_int(self.budget_consumed, "work_item.budget_consumed"),
        )
        object.__setattr__(self, "budget_limit", require_non_negative_int(self.budget_limit, "work_item.budget_limit"))
        object.__setattr__(self, "max_attempts", require_non_negative_int(self.max_attempts, "work_item.max_attempts"))
        object.__setattr__(self, "max_repairs", require_non_negative_int(self.max_repairs, "work_item.max_repairs"))
        object.__setattr__(self, "cleanup_required", require_bool(self.cleanup_required, "work_item.cleanup_required"))

    @property
    def terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WorkItemRecord":
        raw = require_exact_keys(payload, "work_item", WORK_ITEM_RECORD_KEYS)
        return cls(
            schema_id=raw.get("schema_id"),
            work_item_id=raw.get("work_item_id"),
            lease_id=raw.get("lease_id"),
            backlog_id=raw.get("backlog_id"),
            state=raw.get("state"),
            version=raw.get("version"),
            attempt_count=raw.get("attempt_count"),
            repair_count=raw.get("repair_count"),
            budget_consumed=raw.get("budget_consumed"),
            budget_limit=raw.get("budget_limit"),
            max_attempts=raw.get("max_attempts"),
            max_repairs=raw.get("max_repairs"),
            cleanup_required=raw.get("cleanup_required"),
        )

    @classmethod
    def from_json(cls, text: str) -> "WorkItemRecord":
        return cls.from_dict(decode_json_object(text, "work_item"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "work_item_id": self.work_item_id,
            "lease_id": self.lease_id,
            "backlog_id": self.backlog_id,
            "state": self.state.value,
            "version": self.version,
            "attempt_count": self.attempt_count,
            "repair_count": self.repair_count,
            "budget_consumed": self.budget_consumed,
            "budget_limit": self.budget_limit,
            "max_attempts": self.max_attempts,
            "max_repairs": self.max_repairs,
            "cleanup_required": self.cleanup_required,
        }

    def canonical_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def canonical_json(self) -> str:
        return self.canonical_json_bytes().decode("utf-8")

    def canonical_digest(self) -> str:
        return canonical_sha256(self.to_dict())


@dataclass(frozen=True)
class TransitionEvaluation:
    kind: TransitionEvaluationKind
    reason: str
    record: WorkItemRecord
    event: TransitionEvent | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _require_evaluation_kind(self.kind, "transition_evaluation.kind"))
        object.__setattr__(self, "reason", require_reason_class(self.reason, "transition_evaluation.reason"))
        if not isinstance(self.record, WorkItemRecord):
            raise ValueError("invalid_field_type:transition_evaluation.record")
        if self.kind is TransitionEvaluationKind.PRE_APPLY_INVALID:
            if self.event is not None:
                raise ValueError("invalid_field_value:transition_evaluation.event")
            return
        if not isinstance(self.event, TransitionEvent):
            raise ValueError("invalid_field_type:transition_evaluation.event")
        if self.kind.value != self.event.outcome.value or self.reason != self.event.reason:
            raise ValueError("invalid_field_value:transition_evaluation.event")
        if self.record.work_item_id != self.event.work_item_id:
            raise ValueError("invalid_field_value:transition_evaluation.work_item_id")
        if self.record.state is not self.event.resulting_state or self.record.version != self.event.resulting_version:
            raise ValueError("invalid_field_value:transition_evaluation.record")

    @property
    def accepted(self) -> bool:
        return self.kind is TransitionEvaluationKind.ACCEPTED


def evaluate_transition(
    record: WorkItemRecord,
    command: TransitionCommand,
    context: TransitionContext,
) -> TransitionEvaluation:
    if not isinstance(record, WorkItemRecord):
        raise ValueError("invalid_field_type:transition.record")
    if not isinstance(command, TransitionCommand):
        raise ValueError("invalid_field_type:transition.command")
    if not isinstance(context, TransitionContext):
        raise ValueError("invalid_field_type:transition.context")

    pre_apply_reason = _pre_apply_invalid_reason(record, command, context)
    if pre_apply_reason is not None:
        return TransitionEvaluation(
            kind=TransitionEvaluationKind.PRE_APPLY_INVALID,
            reason=pre_apply_reason,
            record=record,
            event=None,
        )

    domain_reason = _domain_rejection_reason(record, command, context)
    if domain_reason is not None:
        return _domain_rejected(record, command, context, domain_reason)

    next_record = _advance(record, command)
    event = _transition_event(
        source=record,
        command=command,
        context=context,
        resulting_record=next_record,
        outcome=TransitionEventOutcome.ACCEPTED,
        reason="transition_accepted",
    )
    return TransitionEvaluation(
        kind=TransitionEvaluationKind.ACCEPTED,
        reason=event.reason,
        record=next_record,
        event=event,
    )


def transition(
    record: WorkItemRecord,
    command: TransitionCommand,
    context: TransitionContext,
) -> TransitionEvaluation:
    return evaluate_transition(record, command, context)


def require_work_item_state(value: Any, field_name: str) -> WorkItemState:
    if isinstance(value, WorkItemState):
        return value
    raw = require_string(value, field_name)
    if raw not in {state.value for state in WorkItemState}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return WorkItemState(raw)


def global_stop_transition_class(target: WorkItemState) -> GlobalStopTransitionClass | None:
    return {
        WorkItemState.LEASE_ADMITTED: GlobalStopTransitionClass.LEASE_ADMISSION,
        WorkItemState.READY: GlobalStopTransitionClass.READY,
        WorkItemState.CYCLE_STARTING: GlobalStopTransitionClass.CYCLE_START,
        WorkItemState.WORKER_RUNNING: GlobalStopTransitionClass.CYCLE_START,
        WorkItemState.VALIDATING: GlobalStopTransitionClass.CYCLE_START,
        WorkItemState.AUDITING: GlobalStopTransitionClass.CYCLE_START,
        WorkItemState.REPAIR_ADMITTED: GlobalStopTransitionClass.REPAIR,
        WorkItemState.REPAIR_RUNNING: GlobalStopTransitionClass.REPAIR,
        WorkItemState.COMMIT_ELIGIBLE: GlobalStopTransitionClass.COMMIT_ELIGIBILITY,
        WorkItemState.LOCAL_COMMIT_COMPLETED: GlobalStopTransitionClass.COMMIT_ELIGIBILITY,
    }.get(target)


def _pre_apply_invalid_reason(
    record: WorkItemRecord,
    command: TransitionCommand,
    context: TransitionContext,
) -> str | None:
    if command.work_item_id != record.work_item_id:
        return "work_item_id_mismatch"
    if record.lease_id != context.lease_identity.lease_ref or record.lease_id != context.authorization.lease_ref:
        return "lease_reference_mismatch"
    if record.lease_id != context.lease_runtime.lease_ref:
        return "lease_reference_mismatch"
    if context.authorization.lease_identity_valid != context.lease_identity.identity_valid:
        return "decision_reference_mismatch"
    if context.authorization.lease_identity_decision_ref != context.lease_identity.decision_ref:
        return "decision_reference_mismatch"
    if command.lease_identity_decision_ref != context.lease_identity.decision_ref:
        return "decision_reference_mismatch"
    if command.authorization_decision_ref != context.authorization.decision_ref:
        return "decision_reference_mismatch"
    if command.global_stop_ref != context.global_stop.stop_ref or command.global_stop_version != context.global_stop.version:
        return "global_stop_reference_mismatch"
    if command.target_state is WorkItemState.READY:
        if command.dependency_decision_ref != context.dependency_decision.decision_ref:
            return "dependency_reference_mismatch"
        if context.dependency_decision.work_item_id is None:
            return "dependency_reference_mismatch"
        if context.dependency_decision.work_item_id != record.work_item_id:
            return "dependency_reference_mismatch"
    if (
        command.target_state is not WorkItemState.READY
        and command.dependency_decision_ref is not None
        and command.dependency_decision_ref != context.dependency_decision.decision_ref
    ):
        return "dependency_reference_mismatch"
    if context.dependency_decision.work_item_id is not None and context.dependency_decision.work_item_id != record.work_item_id:
        return "dependency_reference_mismatch"
    return None


def _domain_rejection_reason(
    record: WorkItemRecord,
    command: TransitionCommand,
    context: TransitionContext,
) -> str | None:
    if command.target_state not in ALLOWED_PREDECESSORS:
        return "unsupported_target_state"
    stage_reason = _stage_enabled(command.target_state)
    if stage_reason is not None:
        return stage_reason
    if not context.lease_identity.identity_valid:
        return "lease_identity_invalid"
    if context.lease_runtime.status is LeaseRuntimeStatus.NOT_YET_VALID:
        return "lease_not_yet_valid"
    if context.lease_runtime.status is LeaseRuntimeStatus.EXPIRED and command.target_state is not WorkItemState.LEASE_EXPIRED:
        return "lease_expired"
    if context.lease_runtime.status is LeaseRuntimeStatus.REVOKED and command.target_state is not WorkItemState.CANCELED_REVOKED:
        return "lease_revoked"
    if context.lease_runtime.status is LeaseRuntimeStatus.REVOCATION_UNKNOWN:
        return "lease_revocation_unknown"
    global_stop_reason = _global_stop_block(command.target_state, context.global_stop)
    if global_stop_reason is not None:
        return global_stop_reason
    if _terminal_blocks(record, command.target_state):
        return "terminal_state"
    if record.state not in ALLOWED_PREDECESSORS[command.target_state]:
        return "invalid_predecessor"
    if command.target_state is WorkItemState.LEASE_ADMITTED and not context.authorization.authorized:
        return "lease_not_authorized"
    if _requires_executable_authority(command.target_state) and not context.authorization.executable:
        return "not_executable"
    if command.target_state is WorkItemState.READY and not context.dependency_decision.dependencies_satisfied:
        return "dependencies_not_satisfied"
    if command.target_state in EVIDENCE_REQUIRED_STATES and not command.evidence_refs:
        return "evidence_required"
    if command.target_state in {WorkItemState.BLOCKED, WorkItemState.FAILED} and not command.safe_failure_class:
        return "safe_failure_class_required"
    if record.budget_limit and record.budget_consumed + command.budget_cost > record.budget_limit:
        return "budget_exhausted"
    if command.target_state is WorkItemState.CYCLE_STARTING and record.attempt_count >= record.max_attempts:
        return "attempts_exhausted"
    if command.target_state is WorkItemState.REPAIR_ADMITTED and record.repair_count >= record.max_repairs:
        return "repairs_exhausted"
    return None


def _advance(record: WorkItemRecord, command: TransitionCommand) -> WorkItemRecord:
    attempt_count = record.attempt_count + _attempt_delta(command)
    repair_count = record.repair_count + _repair_delta(command)
    cleanup_required = record.cleanup_required
    if command.target_state in {
        WorkItemState.FAILED,
        WorkItemState.BLOCKED,
        WorkItemState.EXHAUSTED,
        WorkItemState.LEASE_EXPIRED,
        WorkItemState.CANCELED_REVOKED,
        WorkItemState.LOCAL_COMMIT_COMPLETED,
    }:
        cleanup_required = True
    if command.target_state is WorkItemState.CLEANUP_COMPLETED:
        cleanup_required = False
    return replace(
        record,
        state=command.target_state,
        version=record.version + 1,
        attempt_count=attempt_count,
        repair_count=repair_count,
        budget_consumed=record.budget_consumed + command.budget_cost,
        cleanup_required=cleanup_required,
    )


def _domain_rejected(
    record: WorkItemRecord,
    command: TransitionCommand,
    context: TransitionContext,
    reason: str,
) -> TransitionEvaluation:
    event = _transition_event(
        source=record,
        command=command,
        context=context,
        resulting_record=record,
        outcome=TransitionEventOutcome.DOMAIN_REJECTED,
        reason=reason,
    )
    return TransitionEvaluation(
        kind=TransitionEvaluationKind.DOMAIN_REJECTED,
        reason=event.reason,
        record=record,
        event=event,
    )


def _transition_event(
    source: WorkItemRecord,
    command: TransitionCommand,
    context: TransitionContext,
    resulting_record: WorkItemRecord,
    outcome: TransitionEventOutcome,
    reason: str,
) -> TransitionEvent:
    accepted = outcome is TransitionEventOutcome.ACCEPTED
    payload = {
        "schema_id": TRANSITION_EVENT_SCHEMA_ID,
        "work_item_id": source.work_item_id,
        "lease_id": source.lease_id,
        "command_digest": command.canonical_command_digest,
        "idempotency_key": command.idempotency_key,
        "source_state": source.state.value,
        "source_version": source.version,
        "resulting_state": resulting_record.state.value,
        "resulting_version": resulting_record.version,
        "outcome": outcome.value,
        "reason": reason,
        "evidence_refs": command.evidence_refs,
        "budget_cost_delta": command.budget_cost if accepted else 0,
        "attempt_count_delta": _attempt_delta(command) if accepted else 0,
        "repair_count_delta": _repair_delta(command) if accepted else 0,
        "lease_identity_decision_ref": context.lease_identity.decision_ref,
        "authorization_decision_ref": context.authorization.decision_ref,
        "dependency_decision_ref": command.dependency_decision_ref,
        "lease_runtime": context.lease_runtime.to_dict(),
        "global_stop_ref": context.global_stop.stop_ref,
        "global_stop_version": context.global_stop.version,
    }
    return TransitionEvent(
        event_ref=f"transition-event-{canonical_sha256(payload)[:24]}",
        work_item_id=payload["work_item_id"],
        lease_id=payload["lease_id"],
        command_digest=payload["command_digest"],
        idempotency_key=payload["idempotency_key"],
        source_state=WorkItemState(payload["source_state"]),
        source_version=payload["source_version"],
        resulting_state=WorkItemState(payload["resulting_state"]),
        resulting_version=payload["resulting_version"],
        outcome=outcome,
        reason=payload["reason"],
        evidence_refs=payload["evidence_refs"],
        budget_cost_delta=payload["budget_cost_delta"],
        attempt_count_delta=payload["attempt_count_delta"],
        repair_count_delta=payload["repair_count_delta"],
        lease_identity_decision_ref=payload["lease_identity_decision_ref"],
        authorization_decision_ref=payload["authorization_decision_ref"],
        dependency_decision_ref=payload["dependency_decision_ref"],
        lease_runtime=context.lease_runtime,
        global_stop_ref=payload["global_stop_ref"],
        global_stop_version=payload["global_stop_version"],
    )


def _attempt_delta(command: TransitionCommand) -> int:
    return 1 if command.target_state is WorkItemState.CYCLE_STARTING else 0


def _repair_delta(command: TransitionCommand) -> int:
    return 1 if command.target_state is WorkItemState.REPAIR_ADMITTED else 0


def _terminal_blocks(record: WorkItemRecord, target_state: WorkItemState) -> bool:
    if record.state is WorkItemState.CLEANUP_COMPLETED:
        return True
    if record.terminal and target_state is WorkItemState.CLEANUP_PENDING:
        return False
    if record.terminal:
        return target_state not in {
            WorkItemState.CLEANUP_PENDING,
            WorkItemState.LEASE_EXPIRED,
            WorkItemState.CANCELED_REVOKED,
        }
    return False


def _global_stop_block(target: WorkItemState, global_stop: GlobalStopState) -> str | None:
    transition_class = global_stop_transition_class(target)
    if transition_class is None:
        return None
    decision = enforce_global_stop(global_stop, transition_class)
    if decision.accepted:
        return None
    return decision.reason


def _stage_enabled(target: WorkItemState) -> str | None:
    if target in P1_DISABLED_TARGET_STATES:
        return "stage_not_enabled"
    return None


def _requires_executable_authority(target: WorkItemState) -> bool:
    return target in P1_DISABLED_TARGET_STATES


def _require_event_outcome(value: Any, field_name: str) -> TransitionEventOutcome:
    if isinstance(value, TransitionEventOutcome):
        return value
    raw = require_string(value, field_name)
    if raw not in {outcome.value for outcome in TransitionEventOutcome}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return TransitionEventOutcome(raw)


def _require_evaluation_kind(value: Any, field_name: str) -> TransitionEvaluationKind:
    if isinstance(value, TransitionEvaluationKind):
        return value
    raw = require_string(value, field_name)
    if raw not in {kind.value for kind in TransitionEvaluationKind}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return TransitionEvaluationKind(raw)


def _require_contract_ref_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"invalid_field_type:{field_name}")
    return _validate_contract_refs(value, field_name)


def _require_external_contract_ref_list(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"invalid_field_type:{field_name}")
    return _validate_contract_refs(tuple(value), field_name)


def _validate_contract_refs(value: tuple[Any, ...], field_name: str) -> tuple[str, ...]:
    refs: list[str] = []
    seen: set[str] = set()
    for item in value:
        ref = require_contract_ref(item, f"{field_name}[]")
        if ref in seen:
            raise ValueError(f"duplicate_field:{field_name}")
        refs.append(ref)
        seen.add(ref)
    return tuple(refs)
