"""Private pure Coordinator mutation transaction-resolution contracts."""

from __future__ import annotations

from enum import Enum

__all__: tuple[str, ...] = ()


class _MutationCommitResolutionState(str, Enum):
    NEW = "new"
    TRANSACTION_ACTIVE = "transaction_active"
    FENCED = "fenced"
    CAPABILITY_ACTIVE = "capability_active"
    PLANNED_OUTCOME = "planned_outcome"
    WRITES_PERFORMED = "writes_performed"
    CAPABILITY_INVALIDATED = "capability_invalidated"
    COMMIT_ATTEMPT_STARTED = "commit_attempt_started"
    COMMIT_SUCCEEDED = "commit_succeeded"
    COMMIT_OUTCOME_UNKNOWN = "commit_outcome_unknown"
    ROLLBACK_RESOLVED = "rollback_resolved"
    CLOSED = "closed"


_MUTATION_COMMIT_RESOLUTION_REPLAY_CONFLICT_ROLLBACK_PATH = (
    _MutationCommitResolutionState.TRANSACTION_ACTIVE,
    _MutationCommitResolutionState.FENCED,
    _MutationCommitResolutionState.CAPABILITY_ACTIVE,
    _MutationCommitResolutionState.CAPABILITY_INVALIDATED,
    _MutationCommitResolutionState.ROLLBACK_RESOLVED,
    _MutationCommitResolutionState.CLOSED,
)
_MUTATION_COMMIT_RESOLUTION_PLANNED_OUTCOME_FAILURE_PATH = (
    _MutationCommitResolutionState.TRANSACTION_ACTIVE,
    _MutationCommitResolutionState.FENCED,
    _MutationCommitResolutionState.CAPABILITY_ACTIVE,
    _MutationCommitResolutionState.PLANNED_OUTCOME,
    _MutationCommitResolutionState.CAPABILITY_INVALIDATED,
    _MutationCommitResolutionState.ROLLBACK_RESOLVED,
    _MutationCommitResolutionState.CLOSED,
)
_MUTATION_COMMIT_RESOLUTION_POST_WRITE_PRECOMMIT_FAILURE_PATH = (
    _MutationCommitResolutionState.TRANSACTION_ACTIVE,
    _MutationCommitResolutionState.FENCED,
    _MutationCommitResolutionState.CAPABILITY_ACTIVE,
    _MutationCommitResolutionState.PLANNED_OUTCOME,
    _MutationCommitResolutionState.WRITES_PERFORMED,
    _MutationCommitResolutionState.CAPABILITY_INVALIDATED,
    _MutationCommitResolutionState.ROLLBACK_RESOLVED,
    _MutationCommitResolutionState.CLOSED,
)
_MUTATION_COMMIT_RESOLUTION_FRESH_SUCCESS_PATH = (
    _MutationCommitResolutionState.TRANSACTION_ACTIVE,
    _MutationCommitResolutionState.FENCED,
    _MutationCommitResolutionState.CAPABILITY_ACTIVE,
    _MutationCommitResolutionState.PLANNED_OUTCOME,
    _MutationCommitResolutionState.WRITES_PERFORMED,
    _MutationCommitResolutionState.CAPABILITY_INVALIDATED,
    _MutationCommitResolutionState.COMMIT_ATTEMPT_STARTED,
    _MutationCommitResolutionState.COMMIT_SUCCEEDED,
    _MutationCommitResolutionState.CLOSED,
)
_MUTATION_COMMIT_RESOLUTION_FRESH_UNCERTAIN_PATH = (
    _MutationCommitResolutionState.TRANSACTION_ACTIVE,
    _MutationCommitResolutionState.FENCED,
    _MutationCommitResolutionState.CAPABILITY_ACTIVE,
    _MutationCommitResolutionState.PLANNED_OUTCOME,
    _MutationCommitResolutionState.WRITES_PERFORMED,
    _MutationCommitResolutionState.CAPABILITY_INVALIDATED,
    _MutationCommitResolutionState.COMMIT_ATTEMPT_STARTED,
    _MutationCommitResolutionState.COMMIT_OUTCOME_UNKNOWN,
    _MutationCommitResolutionState.CLOSED,
)
_MUTATION_COMMIT_RESOLUTION_GRAPH_SCOPE = (
    "successful_commit_resolution_milestones_after_graph_covered_mutation_authority",
    "not_complete_operational_cleanup_model",
    "stale_writer_pre_capability_outside_graph",
    "other_pre_capability_failures_outside_graph",
    "pre_capability_exits_cannot_claim_capability_states",
    "capability_invalidation_failure_cannot_claim_capability_invalidated",
    "rollback_failure_cannot_claim_rollback_resolved",
    "close_failure_cannot_force_closed_milestone",
    "successful_capability_invalidation_before_rollback_resolved",
    "successful_capability_invalidation_before_commit_attempt_started",
    "no_direct_rollback_edge_bypasses_capability_invalidation",
    "single_mutation_runtime_enforcement",
)
_MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS = frozenset(
    {
        (_MutationCommitResolutionState.NEW, _MutationCommitResolutionState.TRANSACTION_ACTIVE),
        (_MutationCommitResolutionState.TRANSACTION_ACTIVE, _MutationCommitResolutionState.FENCED),
        (_MutationCommitResolutionState.FENCED, _MutationCommitResolutionState.CAPABILITY_ACTIVE),
        (_MutationCommitResolutionState.CAPABILITY_ACTIVE, _MutationCommitResolutionState.PLANNED_OUTCOME),
        (_MutationCommitResolutionState.CAPABILITY_ACTIVE, _MutationCommitResolutionState.CAPABILITY_INVALIDATED),
        (_MutationCommitResolutionState.PLANNED_OUTCOME, _MutationCommitResolutionState.CAPABILITY_INVALIDATED),
        (_MutationCommitResolutionState.PLANNED_OUTCOME, _MutationCommitResolutionState.WRITES_PERFORMED),
        (_MutationCommitResolutionState.WRITES_PERFORMED, _MutationCommitResolutionState.CAPABILITY_INVALIDATED),
        (_MutationCommitResolutionState.CAPABILITY_INVALIDATED, _MutationCommitResolutionState.ROLLBACK_RESOLVED),
        (_MutationCommitResolutionState.CAPABILITY_INVALIDATED, _MutationCommitResolutionState.COMMIT_ATTEMPT_STARTED),
        (_MutationCommitResolutionState.COMMIT_ATTEMPT_STARTED, _MutationCommitResolutionState.COMMIT_SUCCEEDED),
        (_MutationCommitResolutionState.COMMIT_ATTEMPT_STARTED, _MutationCommitResolutionState.COMMIT_OUTCOME_UNKNOWN),
        (_MutationCommitResolutionState.ROLLBACK_RESOLVED, _MutationCommitResolutionState.CLOSED),
        (_MutationCommitResolutionState.COMMIT_SUCCEEDED, _MutationCommitResolutionState.CLOSED),
        (_MutationCommitResolutionState.COMMIT_OUTCOME_UNKNOWN, _MutationCommitResolutionState.CLOSED),
    }
)
