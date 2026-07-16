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
    SafeWriterMetadata,
    TransitionConflict,
    WriterSessionError,
    WriterSessionFailureReason,
)


@dataclass(frozen=True)
class _IdempotencyEntry:
    command_digest: str
    committed: CommittedTransition


class _FakeAtomicTransitionSession:
    def __init__(self, record: WorkItemRecord, metadata: SafeWriterMetadata) -> None:
        self.current = {record.work_item_id: record}
        self._metadata = metadata
        self._active = True
        self._process_mismatch = False
        self._stale = False
        self.events = []
        self.idempotency = {}
        self.crash_before_commit = False
        self.store_calls = 0

    @property
    def metadata(self) -> SafeWriterMetadata:
        return self._metadata

    @property
    def active(self) -> bool:
        return self._active

    def invalidate_writer(self) -> None:
        self._stale = True

    def simulate_process_mismatch(self) -> None:
        self._process_mismatch = True

    def close(self) -> None:
        self._active = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def apply_transition(
        self,
        command: TransitionCommand,
        context: TransitionContext,
    ) -> CommittedTransition | TransitionConflict:
        if self._process_mismatch:
            raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH)
        if not self._active:
            raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_CLOSED)
        return self._apply_store_boundary(command, context)

    def _apply_store_boundary(
        self,
        command: TransitionCommand,
        context: TransitionContext,
    ) -> CommittedTransition | TransitionConflict:
        self.store_calls += 1
        if self._stale:
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


def _metadata(generation: int = 1) -> SafeWriterMetadata:
    return SafeWriterMetadata(
        writer_ref="writer-main",
        generation=generation,
        issued_ref=f"writer-issued-{generation}",
        acquired_at="2026-07-16T00:00:00Z",
    )


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
    metadata = _metadata()
    record = _record()
    context = _context()
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context, key="same")
    session = _FakeAtomicTransitionSession(record, metadata)

    first = session.apply_transition(command, context)
    assert isinstance(first, CommittedTransition)
    session.invalidate_writer()

    stale = session.apply_transition(command, context)
    assert isinstance(stale, TransitionConflict)
    assert stale.conflict_class == "stale_writer_token"
    assert len(session.events) == 1
    assert session.store_calls == 2


def test_expected_version_conflict_has_no_event_or_evaluation_side_effect() -> None:
    record = _record(version=3)
    context = _context()
    session = _FakeAtomicTransitionSession(record, _metadata())
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context, expected_version=2)

    outcome = session.apply_transition(command, context)
    assert isinstance(outcome, TransitionConflict)
    assert outcome.conflict_class == "expected_version_conflict"
    assert session.current[record.work_item_id] == record
    assert session.events == []


def test_idempotency_conflict_has_no_event() -> None:
    metadata = _metadata()
    record = _record()
    context = _context()
    session = _FakeAtomicTransitionSession(record, metadata)
    first_command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context, key="same")
    first = session.apply_transition(first_command, context)
    assert isinstance(first, CommittedTransition)

    conflicting = _command(
        WorkItemState.BLOCKED,
        record=first.record,
        context=context,
        key="same",
        expected_version=first.record.version,
    )
    outcome = session.apply_transition(conflicting, context)
    assert isinstance(outcome, TransitionConflict)
    assert outcome.conflict_class == "idempotency_key_reuse_conflict"
    assert len(session.events) == 1


def test_domain_rejection_commits_one_event_and_unchanged_state() -> None:
    metadata = _metadata()
    record = _record()
    context = _context()
    session = _FakeAtomicTransitionSession(record, metadata)
    command = _command(WorkItemState.READY, record=record, context=context)

    outcome = session.apply_transition(command, context)
    assert isinstance(outcome, CommittedTransition)
    assert not outcome.replayed
    assert outcome.record == record
    assert outcome.event.reason == "invalid_predecessor"
    assert outcome.event.outcome.value == "domain_rejected"
    assert session.events == [outcome.event]


def test_accepted_transition_exact_replay_preserves_event_without_duplicate() -> None:
    metadata = _metadata()
    record = _record()
    context = _context()
    session = _FakeAtomicTransitionSession(record, metadata)
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context)

    first = session.apply_transition(command, context)
    replay = session.apply_transition(command, context)
    assert isinstance(first, CommittedTransition)
    assert isinstance(replay, CommittedTransition)
    assert first.event == replay.event
    assert first.record == replay.record
    assert replay.replayed
    assert len(session.events) == 1
    assert not hasattr(first, "result_class")


def test_crash_before_commit_leaves_neither_state_nor_event() -> None:
    metadata = _metadata()
    record = _record()
    context = _context()
    session = _FakeAtomicTransitionSession(record, metadata)
    session.crash_before_commit = True
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context)

    with pytest.raises(RuntimeError, match="simulated-crash-before-commit"):
        session.apply_transition(command, context)
    assert session.current[record.work_item_id] == record
    assert session.events == []
    assert session.idempotency == {}


def test_malformed_address_is_pre_apply_invalid_and_no_event() -> None:
    metadata = _metadata()
    record = _record()
    context = _context()
    session = _FakeAtomicTransitionSession(record, metadata)
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context, work_item_id="wi-2")

    outcome = session.apply_transition(command, context)
    assert isinstance(outcome, TransitionConflict)
    assert outcome.conflict_class == "work_item_not_found"
    assert session.events == []


def test_closed_writer_session_fails_with_session_closed() -> None:
    record = _record()
    context = _context()
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context)
    session = _FakeAtomicTransitionSession(record, _metadata())

    with session as active:
        assert active.active
    assert not session.active

    with pytest.raises(WriterSessionError) as exc_info:
        session.apply_transition(command, context)
    assert exc_info.value.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED
    assert session.events == []
    assert session.idempotency == {}


def test_closed_writer_session_does_not_return_stale_writer_conflict() -> None:
    record = _record()
    context = _context()
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context)
    session = _FakeAtomicTransitionSession(record, _metadata())
    session.close()

    with pytest.raises(WriterSessionError) as exc_info:
        session.apply_transition(command, context)
    assert exc_info.value.reason.value == "writer_session_closed"
    assert exc_info.value.reason.value != "stale_writer_token"


def test_closed_writer_session_never_calls_transition_store() -> None:
    record = _record()
    context = _context()
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context)
    session = _FakeAtomicTransitionSession(record, _metadata())
    session.close()

    with pytest.raises(WriterSessionError):
        session.apply_transition(command, context)
    assert session.store_calls == 0
    assert session.current[record.work_item_id] == record
    assert session.events == []


def test_closed_writer_session_produces_no_event() -> None:
    record = _record()
    context = _context()
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context)
    session = _FakeAtomicTransitionSession(record, _metadata())
    session.close()

    with pytest.raises(WriterSessionError):
        session.apply_transition(command, context)
    assert session.events == []


def test_process_mismatch_is_session_failure_before_apply() -> None:
    record = _record()
    context = _context()
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context)
    session = _FakeAtomicTransitionSession(record, _metadata())
    session.simulate_process_mismatch()

    with pytest.raises(WriterSessionError) as exc_info:
        session.apply_transition(command, context)
    assert exc_info.value.reason is WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH
    assert session.store_calls == 0
    assert session.events == []


def test_active_session_stale_fencing_remains_apply_conflict() -> None:
    record = _record()
    context = _context()
    command = _command(WorkItemState.LEASE_ADMITTED, record=record, context=context)
    session = _FakeAtomicTransitionSession(record, _metadata())
    session.invalidate_writer()

    outcome = session.apply_transition(command, context)
    assert isinstance(outcome, TransitionConflict)
    assert outcome.conflict_class == "stale_writer_token"
    assert session.store_calls == 1
    assert session.events == []
