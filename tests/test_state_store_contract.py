from dataclasses import dataclass

import pytest

from ge_nwp_coordinator.lease import AuthorizationDecision, AuthorizationModel, LeaseIdentityValidation
from ge_nwp_coordinator.models import ValidationIssue
from ge_nwp_coordinator.state_machine import (
    DependencyDecision,
    TransitionCommand,
    TransitionContext,
    TransitionEvaluationKind,
    WorkItemRecord,
    WorkItemState,
    evaluate_transition,
)
from ge_nwp_coordinator.state_store import (
    CommittedTransition,
    StateWriterToken,
    TransitionConflict,
)


@dataclass(frozen=True)
class _IdempotencyEntry:
    command_digest: str
    committed: CommittedTransition


class _FakeAtomicTransitionStore:
    def __init__(self, record: WorkItemRecord, writer: StateWriterToken) -> None:
        self.current = {record.work_item_id: record}
        self.writer = writer
        self.events = []
        self.idempotency = {}
        self.crash_before_commit = False

    def apply_transition(
        self,
        writer_token: StateWriterToken,
        command: TransitionCommand,
        context: TransitionContext,
    ) -> CommittedTransition | TransitionConflict:
        if writer_token != self.writer:
            return TransitionConflict("stale_writer_token")

        entry = self.idempotency.get(command.idempotency_key)
        if entry is not None:
            if entry.command_digest == command.canonical_command_digest:
                return CommittedTransition(entry.committed.record, entry.committed.event, replayed=True)
            return TransitionConflict("idempotency_key_reuse_conflict")

        record = self.current.get(command.work_item_id)
        if record is None:
            return TransitionConflict("work_item_not_found")
        if command.expected_version != record.version:
            return TransitionConflict("expected_version_conflict")

        evaluation = evaluate_transition(record, command, context)
        if evaluation.kind is TransitionEvaluationKind.PRE_APPLY_INVALID:
            return TransitionConflict("validation_failed")
        if self.crash_before_commit:
            raise RuntimeError("simulated-crash-before-commit")

        assert evaluation.event is not None
        committed = CommittedTransition(evaluation.record, evaluation.event, replayed=False)
        self.current[command.work_item_id] = committed.record
        self.events.append(committed.event)
        self.idempotency[command.idempotency_key] = _IdempotencyEntry(command.canonical_command_digest, committed)
        return committed


def _writer(generation: int = 1) -> StateWriterToken:
    return StateWriterToken(writer_ref="writer-main", generation=generation, issued_ref=f"writer-issued-{generation}")


def _identity(*, valid: bool = True) -> LeaseIdentityValidation:
    return LeaseIdentityValidation(
        identity_valid=valid,
        digest="a" * 64 if valid else None,
        issues=() if valid else (ValidationIssue(field="lease", reason="digest_mismatch"),),
        decision_ref="lease-identity-lease-1",
        lease_ref="lease-1",
    )


def _context(*, identity_valid: bool = True, dependencies_satisfied: bool = True) -> TransitionContext:
    identity = _identity(valid=identity_valid)
    return TransitionContext(
        lease_identity=identity,
        authorization=AuthorizationDecision(
            decision_ref="authz-lease-1",
            lease_ref="lease-1",
            lease_identity_valid=identity.identity_valid,
            authorization_model=AuthorizationModel.OPERATOR_POLICY,
            authorized=True,
            executable=False,
            reason="accepted",
        ),
        dependency_decision=DependencyDecision(
            decision_ref="deps-ready",
            dependencies_satisfied=dependencies_satisfied,
            reason="accepted" if dependencies_satisfied else "dependencies_not_satisfied",
        ),
    )


def _record(state: WorkItemState = WorkItemState.PROPOSED, version: int = 0) -> WorkItemRecord:
    return WorkItemRecord(
        work_item_id="wi-1",
        lease_id="lease-1",
        backlog_id="backlog-1",
        state=state,
        version=version,
        budget_limit=10,
    )


def _command(
    target: WorkItemState,
    *,
    record: WorkItemRecord,
    context: TransitionContext,
    key: str = "k1",
    expected_version: int | None = None,
    work_item_id: str | None = None,
    budget_cost: int = 0,
) -> TransitionCommand:
    return TransitionCommand.create(
        work_item_id=work_item_id or record.work_item_id,
        idempotency_key=key,
        expected_version=record.version if expected_version is None else expected_version,
        target_state=target,
        lease_identity_decision_ref=context.lease_identity.decision_ref,
        authorization_decision_ref=context.authorization.decision_ref,
        global_stop_ref=context.global_stop.stop_ref,
        global_stop_version=context.global_stop.version,
        dependency_decision_ref=context.dependency_decision.decision_ref if target is WorkItemState.READY else None,
        budget_cost=budget_cost,
    )


def test_stale_writer_precedes_idempotency_and_discloses_nothing() -> None:
    writer = _writer()
    record = _record()
    context = _context()
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context, key="same")
    store = _FakeAtomicTransitionStore(record, writer)

    first = store.apply_transition(writer, command, context)
    assert isinstance(first, CommittedTransition)

    stale = store.apply_transition(_writer(generation=2), command, context)
    assert isinstance(stale, TransitionConflict)
    assert stale.conflict_class == "stale_writer_token"
    assert len(store.events) == 1


def test_expected_version_conflict_has_no_event_or_evaluation_side_effect() -> None:
    record = _record(version=3)
    context = _context()
    store = _FakeAtomicTransitionStore(record, _writer())
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context, expected_version=2)

    outcome = store.apply_transition(_writer(), command, context)
    assert isinstance(outcome, TransitionConflict)
    assert outcome.conflict_class == "expected_version_conflict"
    assert store.current[record.work_item_id] == record
    assert store.events == []


def test_idempotency_conflict_has_no_event() -> None:
    writer = _writer()
    record = _record()
    context = _context()
    store = _FakeAtomicTransitionStore(record, writer)
    first_command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context, key="same")
    first = store.apply_transition(writer, first_command, context)
    assert isinstance(first, CommittedTransition)

    conflicting = _command(
        WorkItemState.BLOCKED,
        record=first.record,
        context=context,
        key="same",
        expected_version=first.record.version,
    )
    outcome = store.apply_transition(writer, conflicting, context)
    assert isinstance(outcome, TransitionConflict)
    assert outcome.conflict_class == "idempotency_key_reuse_conflict"
    assert len(store.events) == 1


def test_domain_rejection_commits_one_event_and_unchanged_state() -> None:
    writer = _writer()
    record = _record()
    context = _context()
    store = _FakeAtomicTransitionStore(record, writer)
    command = _command(WorkItemState.READY, record=record, context=context)

    outcome = store.apply_transition(writer, command, context)
    assert isinstance(outcome, CommittedTransition)
    assert not outcome.replayed
    assert outcome.record == record
    assert outcome.event.reason == "invalid_predecessor"
    assert outcome.event.outcome.value == "domain_rejected"
    assert store.events == [outcome.event]


def test_accepted_transition_exact_replay_preserves_event_without_duplicate() -> None:
    writer = _writer()
    record = _record()
    context = _context()
    store = _FakeAtomicTransitionStore(record, writer)
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context)

    first = store.apply_transition(writer, command, context)
    replay = store.apply_transition(writer, command, context)
    assert isinstance(first, CommittedTransition)
    assert isinstance(replay, CommittedTransition)
    assert first.event == replay.event
    assert first.record == replay.record
    assert replay.replayed
    assert len(store.events) == 1
    assert not hasattr(first, "result_class")


def test_crash_before_commit_leaves_neither_state_nor_event() -> None:
    writer = _writer()
    record = _record()
    context = _context()
    store = _FakeAtomicTransitionStore(record, writer)
    store.crash_before_commit = True
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context)

    with pytest.raises(RuntimeError, match="simulated-crash-before-commit"):
        store.apply_transition(writer, command, context)
    assert store.current[record.work_item_id] == record
    assert store.events == []
    assert store.idempotency == {}


def test_malformed_address_is_pre_apply_invalid_and_no_event() -> None:
    writer = _writer()
    record = _record()
    context = _context()
    store = _FakeAtomicTransitionStore(record, writer)
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context, work_item_id="wi-2")

    outcome = store.apply_transition(writer, command, context)
    assert isinstance(outcome, TransitionConflict)
    assert outcome.conflict_class == "work_item_not_found"
    assert store.events == []
