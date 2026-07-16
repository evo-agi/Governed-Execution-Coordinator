"""Atomic state-store and writer-session ports for the P1.1 event contract.

A2-P1.1 intentionally provides no production implementation. B2a corrects the
writer authority surface to an opaque writer-session protocol only. Future
sessions must be created by the backend after successful writer acquisition;
Protocol conformance by itself is not authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import TracebackType
from typing import Protocol, Self

from ge_nwp_coordinator.canonicalization import require_bool, require_positive_int, require_string
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

SAFE_WRITER_METADATA_SCHEMA_ID = "governed-execution.nwp-safe-writer-metadata.v1"
WRITER_ISSUANCE_PROOF_DOMAIN = "governed-execution.nwp-writer-issuance-proof.v1"
MAX_WRITER_GENERATION = 9223372036854775807


class WriterSessionFailureReason(str, Enum):
    WRITER_SESSION_CLOSED = "writer_session_closed"
    WRITER_SESSION_PROCESS_MISMATCH = "writer_session_process_mismatch"


class WriterSessionError(RuntimeError):
    """Safe session-local failure raised before any atomic apply boundary."""

    def __init__(self, reason: WriterSessionFailureReason | str) -> None:
        normalized = WriterSessionFailureReason(reason)
        self.reason = normalized
        super().__init__(normalized.value)


@dataclass(frozen=True)
class SafeWriterMetadata:
    """Safe writer issuance metadata, not live mutation authority."""

    writer_ref: str
    generation: int
    issued_ref: str
    acquired_at: str
    schema_id: str = SAFE_WRITER_METADATA_SCHEMA_ID

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "safe_writer_metadata.schema_id") != SAFE_WRITER_METADATA_SCHEMA_ID:
            raise ValueError("invalid_field_type:safe_writer_metadata.schema_id")
        object.__setattr__(self, "writer_ref", require_contract_ref(self.writer_ref, "safe_writer_metadata.writer_ref"))
        object.__setattr__(
            self,
            "generation",
            require_positive_int(self.generation, "safe_writer_metadata.generation"),
        )
        if self.generation > MAX_WRITER_GENERATION:
            raise ValueError("invalid_field_value:safe_writer_metadata.generation")
        object.__setattr__(self, "issued_ref", require_contract_ref(self.issued_ref, "safe_writer_metadata.issued_ref"))
        acquired_at = require_string(self.acquired_at, "safe_writer_metadata.acquired_at")
        if not 20 <= len(acquired_at) <= 64:
            raise ValueError("invalid_field_value:safe_writer_metadata.acquired_at")
        object.__setattr__(self, "acquired_at", acquired_at)


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


class WriterSession(Protocol):
    """Opaque future mutation capability created only by writer acquisition."""

    @property
    def metadata(self) -> SafeWriterMetadata:
        """Return safe non-authoritative metadata for diagnostics."""
        ...

    @property
    def active(self) -> bool:
        """Return whether this session is active in this process."""
        ...

    def apply_transition(
        self,
        transition_command: TransitionCommand,
        typed_context: TransitionContext,
    ) -> TransitionApplyOutcome:
        """Apply a transition after session-local lifecycle checks."""
        ...

    def apply_global_stop_update(
        self,
        global_stop_command: GlobalStopCommand,
        typed_operator_decision: GlobalStopOperatorDecision,
    ) -> GlobalStopApplyOutcome:
        """Apply a global-stop update after session-local lifecycle checks."""
        ...

    def close(self) -> None:
        """Idempotently invalidate the session and release future resources."""
        ...

    def __enter__(self) -> Self:
        """Return the active writer session as a context manager."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the session when leaving a context manager."""
        ...


class StateStore(Protocol):
    def read_current(self, work_item_id: str) -> WorkItemRecord | None:
        """Read the current record for a work item."""
        ...

    def read_global_stop(self) -> GlobalStopState:
        """Read the authoritative global-stop state."""
        ...
