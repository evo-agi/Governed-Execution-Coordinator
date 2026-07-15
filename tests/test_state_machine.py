from dataclasses import replace

from ge_nwp_coordinator.global_stop import GlobalStopState
from ge_nwp_coordinator.state_machine import (
    ALLOWED_PREDECESSORS,
    TransitionContext,
    TransitionRequest,
    WorkItemRecord,
    WorkItemState,
    transition,
)


def _context(*, executable: bool = False, stop: bool = False) -> TransitionContext:
    return TransitionContext(
        lease_identity_valid=True,
        authorized=True,
        executable=executable,
        global_stop=GlobalStopState(active=stop, stop_id="stop-1" if stop else None),
    )


def _record(state: WorkItemState = WorkItemState.PROPOSED, version: int = 0) -> WorkItemRecord:
    return WorkItemRecord(
        work_item_id="wi-1",
        lease_id="lease-a2-p1",
        backlog_id="backlog-a2-p1",
        state=state,
        version=version,
        max_attempts=2,
        max_repairs=1,
        budget_limit=10,
    )


def _request(target: WorkItemState, version: int = 0, key: str = "k1", **kwargs: object) -> TransitionRequest:
    return TransitionRequest(target_state=target, expected_version=version, idempotency_key=key, **kwargs)


def test_valid_and_invalid_predecessors() -> None:
    admitted = transition(_record(), _request(WorkItemState.LEASE_ADMITTED), _context())
    assert admitted.accepted
    ready = transition(admitted.record, _request(WorkItemState.READY, 1, "k2"), _context())
    assert ready.accepted

    invalid = transition(_record(), _request(WorkItemState.READY), _context())
    assert not invalid.accepted
    assert invalid.reason == "invalid_predecessor"


def test_expected_version_mismatch_and_idempotency() -> None:
    record = _record()
    mismatch = transition(record, _request(WorkItemState.LEASE_ADMITTED, version=1), _context())
    assert not mismatch.accepted
    assert mismatch.reason == "expected_version_mismatch"

    first = transition(record, _request(WorkItemState.LEASE_ADMITTED, key="same"), _context())
    second = transition(first.record, _request(WorkItemState.LEASE_ADMITTED, version=1, key="same"), _context())
    assert second.accepted
    assert second.record == first.record
    assert second.receipt == first.receipt


def test_counters_budgets_terminal_and_cleanup() -> None:
    record = _record(state=WorkItemState.CYCLE_STARTING, version=2)
    failed = transition(
        record,
        _request(
            WorkItemState.FAILED,
            2,
            "failed",
            evidence_refs=("safe-evidence",),
            safe_failure_class="validation_failed",
            budget_cost=3,
        ),
        _context(),
    )
    assert failed.accepted
    assert failed.record.attempt_count == 0
    assert failed.record.budget_consumed == 3
    assert failed.record.cleanup_required

    after_terminal = transition(failed.record, _request(WorkItemState.READY, 3, "ready"), _context())
    assert not after_terminal.accepted
    assert after_terminal.reason == "terminal_state"

    cleanup = transition(
        failed.record,
        _request(WorkItemState.CLEANUP_PENDING, 3, "cleanup"),
        _context(),
    )
    assert cleanup.accepted


def test_stage_not_enabled_for_worker_repair_and_commit() -> None:
    worker = transition(_record(WorkItemState.READY, 1), _request(WorkItemState.CYCLE_STARTING, 1), _context())
    assert not worker.accepted
    assert worker.reason == "stage_not_enabled"

    validating = transition(
        _record(WorkItemState.WORKER_RUNNING, 1),
        _request(WorkItemState.VALIDATING, 1, "validate", evidence_refs=("safe-evidence",)),
        _context(executable=True),
    )
    assert not validating.accepted
    assert validating.reason == "stage_not_enabled"

    auditing = transition(
        _record(WorkItemState.VALIDATING, 1),
        _request(WorkItemState.AUDITING, 1, "audit", evidence_refs=("safe-evidence",)),
        _context(executable=True),
    )
    assert not auditing.accepted
    assert auditing.reason == "stage_not_enabled"

    repair = transition(
        _record(WorkItemState.FAILED, 1),
        _request(WorkItemState.REPAIR_ADMITTED, 1, "repair", evidence_refs=("safe-evidence",)),
        _context(),
    )
    assert not repair.accepted
    assert repair.reason == "stage_not_enabled"

    commit = transition(
        _record(WorkItemState.AUDITING, 1),
        _request(WorkItemState.COMMIT_ELIGIBLE, 1, "commit", evidence_refs=("safe-evidence",)),
        _context(),
    )
    assert not commit.accepted
    assert commit.reason == "stage_not_enabled"


def test_limits_and_executable_context_do_not_enable_p1_future_stages() -> None:
    cycle = transition(
        replace(_record(WorkItemState.READY, 1), max_attempts=5),
        _request(WorkItemState.CYCLE_STARTING, 1, "cycle"),
        _context(executable=True),
    )
    assert not cycle.accepted
    assert cycle.reason == "stage_not_enabled"

    repair = transition(
        replace(_record(WorkItemState.FAILED, 1), max_repairs=5),
        _request(WorkItemState.REPAIR_ADMITTED, 1, "repair", evidence_refs=("safe-evidence",)),
        _context(executable=True),
    )
    assert not repair.accepted
    assert repair.reason == "stage_not_enabled"

    commit = transition(
        _record(WorkItemState.AUDITING, 1),
        _request(WorkItemState.COMMIT_ELIGIBLE, 1, "commit", evidence_refs=("safe-evidence",)),
        _context(executable=True),
    )
    assert not commit.accepted
    assert commit.reason == "stage_not_enabled"


def test_evidence_and_budget_requirements() -> None:
    record = _record(WorkItemState.WORKER_RUNNING, 3)
    missing_evidence = transition(
        record,
        _request(WorkItemState.FAILED, 3, "failed", safe_failure_class="validation_failed"),
        _context(),
    )
    assert not missing_evidence.accepted
    assert missing_evidence.reason == "evidence_required"

    over_budget = transition(
        replace(record, budget_consumed=9),
        _request(
            WorkItemState.FAILED,
            3,
            "failed2",
            evidence_refs=("safe",),
            safe_failure_class="validation_failed",
            budget_cost=2,
        ),
        _context(),
    )
    assert not over_budget.accepted
    assert over_budget.reason == "budget_exhausted"


def test_future_state_vocabulary_has_no_production_enable_policy() -> None:
    assert WorkItemState.WORKER_RUNNING in ALLOWED_PREDECESSORS
    assert WorkItemState.REPAIR_RUNNING in ALLOWED_PREDECESSORS
    assert WorkItemState.LOCAL_COMMIT_COMPLETED in ALLOWED_PREDECESSORS


def test_no_publication_states_exist() -> None:
    assert "publication" not in {state.value for state in WorkItemState}
