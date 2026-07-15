"""A2-P1 NWP Coordinator skeleton.

The package exposes offline parsing, canonicalization, pure state transition,
global-stop, and report projection primitives only. It intentionally provides
no worker runner, background runner, storage backend, network client, or CLI
entrypoint.
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
    TransitionContext,
    TransitionRequest,
    TransitionResult,
    WorkItemRecord,
    WorkItemState,
    transition,
)

__all__ = [
    "AuthorizationDecision",
    "FiniteBacklog",
    "LEASE_SCHEMA_ID",
    "LeaseIdentityValidation",
    "StandingLease",
    "TransitionContext",
    "TransitionRequest",
    "TransitionResult",
    "UnsupportedAuthorizationProvider",
    "WorkItem",
    "WorkItemRecord",
    "WorkItemState",
    "transition",
    "validate_standing_lease",
]
