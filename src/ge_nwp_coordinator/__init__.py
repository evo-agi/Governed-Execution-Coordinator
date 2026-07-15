"""A2-P1 NWP Coordinator skeleton.

The package exposes offline parsing, canonicalization, pure state transition,
atomic store-port contracts, global-stop, and report projection primitives only.
It intentionally provides no worker runner, background runner, storage backend,
network client, or CLI entrypoint.
"""

from ge_nwp_coordinator.backlog import FiniteBacklog, WorkItem
from ge_nwp_coordinator.lease import (
    LEASE_SCHEMA_ID,
    AuthorizationDecision,
    LeaseIdentityValidation,
    StandingLease,
    UnsupportedAuthorizationProvider,
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
    GlobalStopConflict,
    StateStore,
    StateWriterToken,
    TransitionConflict,
)

__all__ = [
    "AuthorizationDecision",
    "CommittedGlobalStopUpdate",
    "CommittedTransition",
    "DependencyDecision",
    "FiniteBacklog",
    "GlobalStopConflict",
    "LEASE_SCHEMA_ID",
    "LeaseIdentityValidation",
    "StateStore",
    "StateWriterToken",
    "StandingLease",
    "TransitionCommand",
    "TransitionContext",
    "TransitionConflict",
    "TransitionEvaluation",
    "TransitionEvent",
    "TransitionEventOutcome",
    "UnsupportedAuthorizationProvider",
    "WorkItem",
    "WorkItemRecord",
    "WorkItemState",
    "evaluate_transition",
    "transition",
    "validate_standing_lease",
]
