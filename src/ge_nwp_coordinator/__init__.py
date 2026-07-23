"""A2-P1 NWP Coordinator skeleton.

The package exposes offline parsing, canonicalization, pure state transition,
atomic store-port contracts, global-stop, report projection primitives, and B1
SQLite bootstrap/migration infrastructure only. It intentionally provides no
worker runner, background runner, StateStore mutation backend, network client,
or CLI entrypoint.
"""

from ge_nwp_coordinator.backlog import FiniteBacklog, WorkItem
from ge_nwp_coordinator.lease import (
    LEASE_SCHEMA_ID,
    AuthorizationDecision,
    LeaseIdentityValidation,
    LeaseRuntimeDecision,
    LeaseRuntimeStatus,
    StandingLease,
    UnsupportedAuthorizationProvider,
    derive_lease_runtime_decision,
    validate_standing_lease,
)
from ge_nwp_coordinator.state_machine import (
    DependencyDecision,
    TransitionCommand,
    TransitionContext,
    TransitionEvaluation,
    TransitionEvent,
    TransitionEventOutcome,
    WorkItemRecord,
    WorkItemState,
    evaluate_transition,
    transition,
)
from ge_nwp_coordinator.state_store import (
    CommittedGlobalStopUpdate,
    CommittedTransition,
    GlobalStopApplyPreflightError,
    GlobalStopApplyPreflightFailureReason,
    GlobalStopConflict,
    SafeWriterMetadata,
    StateStore,
    TransitionApplyPreflightError,
    TransitionApplyPreflightFailureReason,
    TransitionConflict,
    WriterSessionError,
    WriterSessionFailureReason,
    WriterSession,
)

__all__ = [
    "AuthorizationDecision",
    "CommittedGlobalStopUpdate",
    "CommittedTransition",
    "DependencyDecision",
    "FiniteBacklog",
    "GlobalStopApplyPreflightError",
    "GlobalStopApplyPreflightFailureReason",
    "GlobalStopConflict",
    "LEASE_SCHEMA_ID",
    "LeaseIdentityValidation",
    "LeaseRuntimeDecision",
    "LeaseRuntimeStatus",
    "SafeWriterMetadata",
    "StateStore",
    "StandingLease",
    "TransitionApplyPreflightError",
    "TransitionApplyPreflightFailureReason",
    "TransitionCommand",
    "TransitionContext",
    "TransitionConflict",
    "TransitionEvaluation",
    "TransitionEvent",
    "TransitionEventOutcome",
    "UnsupportedAuthorizationProvider",
    "WriterSessionError",
    "WriterSessionFailureReason",
    "WriterSession",
    "WorkItem",
    "WorkItemRecord",
    "WorkItemState",
    "derive_lease_runtime_decision",
    "evaluate_transition",
    "transition",
    "validate_standing_lease",
]
