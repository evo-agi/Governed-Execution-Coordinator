from dataclasses import replace

from ge_nwp_coordinator.global_stop import GlobalStopState
from ge_nwp_coordinator.state_machine import (
    P1Policy,
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
    policy = P1Policy(worker_execution_enabled=True, repair_enabled=True, local_commit_enabled=True)
    record = _record(state=WorkItemState.READY, version=2)
    started = transition(
        record,
        _request(WorkItemState.CYCLE_STARTING, 2, "start", budget_cost=3),
        _context(executable=True),
        policy,
    )
    assert started.accepted
    assert started.record.attempt_count == 1
    assert started.record.budget_consumed == 3

    running = transition(
        started.record,
        _request(WorkItemState.WORKER_RUNNING, 3, "worker"),
        _context(executable=True),
        policy,
    )
    failed = transition(
        running.record,
        _request(
            WorkItemState.FAILED,
            4,
            "failed",
            evidence_refs=("safe-evidence",),
            safe_failure_class="validation_failed",
        ),
        _context(executable=True),
        policy,
    )
    assert failed.accepted
    assert failed.record.cleanup_required

    after_terminal = transition(failed.record, _request(WorkItemState.READY, 5, "ready"), _context())
    assert not after_terminal.accepted
    assert after_terminal.reason == "terminal_state"

    cleanup = transition(
        failed.record,
        _request(WorkItemState.CLEANUP_PENDING, 5, "cleanup"),
        _context(),
        policy,
    )
    assert cleanup.accepted


def test_stage_not_enabled_for_worker_repair_and_commit() -> None:
    worker = transition(_record(WorkItemState.READY, 1), _request(WorkItemState.CYCLE_STARTING, 1), _context())
    assert not worker.accepted
    assert worker.reason == "stage_not_enabled"

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


def test_evidence_and_budget_requirements() -> None:
    policy = P1Policy(worker_execution_enabled=True)
    record = _record(WorkItemState.WORKER_RUNNING, 3)
    missing_evidence = transition(
        record,
        _request(WorkItemState.VALIDATING, 3, "validate"),
        _context(executable=True),
        policy,
    )
    assert not missing_evidence.accepted
    assert missing_evidence.reason == "evidence_required"

    over_budget = transition(
        replace(record, budget_consumed=9),
        _request(WorkItemState.VALIDATING, 3, "validate2", evidence_refs=("safe",), budget_cost=2),
        _context(executable=True),
        policy,
    )
    assert not over_budget.accepted
    assert over_budget.reason == "budget_exhausted"


def test_no_publication_states_exist() -> None:
    assert "publication" not in {state.value for state in WorkItemState}
