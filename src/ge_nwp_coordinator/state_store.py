"""Atomic state-store port for the P1.1 command/event contract.

A2-P1.1 intentionally provides no production implementation. Future stores must
fence every mutation, resolve idempotency internally, load authoritative state,
compare expected versions, invoke the pure evaluator, and atomically persist the
state plus one immutable event.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ge_nwp_coordinator.canonicalization import require_bool, require_non_negative_int, require_string
from ge_nwp_coordinator.global_stop import (
    GlobalStopCommand,
    GlobalStopEvent,
    GlobalStopOperatorDecision,
    GlobalStopState,
)
from ge_nwp_coordinator.models import require_apply_conflict_reason, require_contract_ref
from ge_nwp_coordinator.state_machine import (
    TransitionCommand,
    TransitionContext,
    TransitionEvent,
    WorkItemRecord,
)

STATE_WRITER_TOKEN_SCHEMA_ID = "governed-execution.nwp-state-writer-token.v1"


@dataclass(frozen=True)
class StateWriterToken:
    writer_ref: str
    generation: int
    issued_ref: str
    schema_id: str = STATE_WRITER_TOKEN_SCHEMA_ID

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "state_writer_token.schema_id") != STATE_WRITER_TOKEN_SCHEMA_ID:
            raise ValueError("invalid_field_type:state_writer_token.schema_id")
        object.__setattr__(self, "writer_ref", require_contract_ref(self.writer_ref, "state_writer_token.writer_ref"))
        object.__setattr__(
            self,
            "generation",
            require_non_negative_int(self.generation, "state_writer_token.generation"),
        )
        object.__setattr__(self, "issued_ref", require_contract_ref(self.issued_ref, "state_writer_token.issued_ref"))


@dataclass(frozen=True)
class TransitionConflict:
    conflict_class: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "conflict_class", require_apply_conflict_reason(self.conflict_class, "conflict_class"))


@dataclass(frozen=True)
class CommittedTransition:
    record: WorkItemRecord
    event: TransitionEvent
    replayed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.record, WorkItemRecord):
            raise ValueError("invalid_field_type:committed_transition.record")
        if not isinstance(self.event, TransitionEvent):
            raise ValueError("invalid_field_type:committed_transition.event")
        object.__setattr__(self, "replayed", require_bool(self.replayed, "committed_transition.replayed"))
        if self.record.work_item_id != self.event.work_item_id:
            raise ValueError("invalid_field_value:committed_transition.work_item_id")
        if self.record.state is not self.event.resulting_state or self.record.version != self.event.resulting_version:
            raise ValueError("invalid_field_value:committed_transition.record")


@dataclass(frozen=True)
class GlobalStopConflict:
    conflict_class: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "conflict_class", require_apply_conflict_reason(self.conflict_class, "conflict_class"))


@dataclass(frozen=True)
class CommittedGlobalStopUpdate:
    state: GlobalStopState
    event: GlobalStopEvent
    replayed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.state, GlobalStopState):
            raise ValueError("invalid_field_type:committed_global_stop.state")
        if not isinstance(self.event, GlobalStopEvent):
            raise ValueError("invalid_field_type:committed_global_stop.event")
        object.__setattr__(self, "replayed", require_bool(self.replayed, "committed_global_stop.replayed"))
        if self.state.version != self.event.resulting_version:
            raise ValueError("invalid_field_value:committed_global_stop.version")
        if self.state.stop_ref != self.event.resulting_global_stop_ref:
            raise ValueError("invalid_field_value:committed_global_stop.ref")
        if self.state.status is not self.event.resulting_status:
            raise ValueError("invalid_field_value:committed_global_stop.status")


TransitionApplyOutcome = CommittedTransition | TransitionConflict
GlobalStopApplyOutcome = CommittedGlobalStopUpdate | GlobalStopConflict


class WriterOwnershipStore(Protocol):
    def current_writer(self) -> StateWriterToken | None:
        """Return the current authoritative writer token, if one exists."""


class StateStore(Protocol):
    def read_current(self, work_item_id: str) -> WorkItemRecord | None:
        """Read the current record for a work item."""

    def apply_transition(
        self,
        writer_token: StateWriterToken,
        transition_command: TransitionCommand,
        typed_context: TransitionContext,
    ) -> TransitionApplyOutcome:
        """Atomically apply a transition command or return an apply conflict."""

    def read_global_stop(self) -> GlobalStopState:
        """Read the authoritative global-stop state."""

    def apply_global_stop_update(
        self,
        writer_token: StateWriterToken,
        global_stop_command: GlobalStopCommand,
        typed_operator_decision: GlobalStopOperatorDecision,
    ) -> GlobalStopApplyOutcome:
        """Atomically apply a global-stop command or return an apply conflict."""
