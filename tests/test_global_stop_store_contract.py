from dataclasses import dataclass

from ge_nwp_coordinator.global_stop import (
    GlobalStopAction,
    GlobalStopCommand,
    GlobalStopEvaluationKind,
    GlobalStopOperatorDecision,
    GlobalStopReasonClass,
    GlobalStopState,
    evaluate_global_stop_update,
)
from ge_nwp_coordinator.state_store import (
    CommittedGlobalStopUpdate,
    GlobalStopConflict,
    StateWriterToken,
)


@dataclass(frozen=True)
class _StopIdempotencyEntry:
    command_digest: str
    committed: CommittedGlobalStopUpdate


class _FakeAtomicGlobalStopStore:
    def __init__(self, state: GlobalStopState, writer: StateWriterToken) -> None:
        self.state = state
        self.writer = writer
        self.events = []
        self.idempotency = {}

    def apply_global_stop_update(
        self,
        writer_token: StateWriterToken,
        command: GlobalStopCommand,
        decision: GlobalStopOperatorDecision,
    ) -> CommittedGlobalStopUpdate | GlobalStopConflict:
        if writer_token != self.writer:
            return GlobalStopConflict("stale_writer_token")
        entry = self.idempotency.get(command.idempotency_key)
        if entry is not None:
            if entry.command_digest == command.canonical_command_digest:
                return CommittedGlobalStopUpdate(entry.committed.state, entry.committed.event, replayed=True)
            return GlobalStopConflict("idempotency_key_reuse_conflict")
        if command.expected_version != self.state.version:
            return GlobalStopConflict("expected_version_conflict")
        evaluation = evaluate_global_stop_update(self.state, command, decision)
        if evaluation.kind is GlobalStopEvaluationKind.PRE_APPLY_INVALID:
            return GlobalStopConflict("validation_failed")
        assert evaluation.event is not None
        committed = CommittedGlobalStopUpdate(evaluation.state, evaluation.event, replayed=False)
        self.state = committed.state
        self.events.append(committed.event)
        self.idempotency[command.idempotency_key] = _StopIdempotencyEntry(command.canonical_command_digest, committed)
        return committed


def _writer(generation: int = 1) -> StateWriterToken:
    return StateWriterToken(writer_ref="writer-main", generation=generation, issued_ref=f"writer-issued-{generation}")


def _decision(*, authorized: bool = True, decision_ref: str = "operator-decision-1") -> GlobalStopOperatorDecision:
    return GlobalStopOperatorDecision(
        decision_ref=decision_ref,
        authorized=authorized,
        reason="accepted" if authorized else "operator_authorization_required",
    )


def _activate(
    *,
    key: str = "stop-k1",
    expected_version: int = 0,
    decision_ref: str = "operator-decision-1",
    stop_id: str = "stop-1",
) -> GlobalStopCommand:
    return GlobalStopCommand.create(
        action=GlobalStopAction.ACTIVATE,
        idempotency_key=key,
        expected_version=expected_version,
        stop_id=stop_id,
        reason_class=GlobalStopReasonClass.OPERATOR_STOP,
        issuer_ref="operator-policy",
        issued_at="2026-07-14T00:00:00Z",
        operator_decision_ref=decision_ref,
    )


def test_global_stop_stale_writer_precedes_idempotency() -> None:
    writer = _writer()
    store = _FakeAtomicGlobalStopStore(GlobalStopState(), writer)
    command = _activate()
    first = store.apply_global_stop_update(writer, command, _decision())
    assert isinstance(first, CommittedGlobalStopUpdate)

    stale = store.apply_global_stop_update(_writer(2), command, _decision())
    assert isinstance(stale, GlobalStopConflict)
    assert stale.conflict_class == "stale_writer_token"
    assert len(store.events) == 1


def test_global_stop_expected_version_conflict_has_no_event() -> None:
    store = _FakeAtomicGlobalStopStore(GlobalStopState(version=3, active=False), _writer())
    outcome = store.apply_global_stop_update(_writer(), _activate(expected_version=2), _decision())
    assert isinstance(outcome, GlobalStopConflict)
    assert outcome.conflict_class == "expected_version_conflict"
    assert store.events == []
    assert store.state.version == 3


def test_global_stop_domain_rejection_commits_event_and_unchanged_state() -> None:
    state = GlobalStopState()
    store = _FakeAtomicGlobalStopStore(state, _writer())
    outcome = store.apply_global_stop_update(_writer(), _activate(), _decision(authorized=False))
    assert isinstance(outcome, CommittedGlobalStopUpdate)
    assert outcome.state == state
    assert outcome.event.outcome.value == "domain_rejected"
    assert outcome.event.reason == "operator_authorization_required"
    assert store.events == [outcome.event]


def test_global_stop_exact_replay_preserves_original_event() -> None:
    store = _FakeAtomicGlobalStopStore(GlobalStopState(), _writer())
    command = _activate()
    first = store.apply_global_stop_update(_writer(), command, _decision())
    replay = store.apply_global_stop_update(_writer(), command, _decision())
    assert isinstance(first, CommittedGlobalStopUpdate)
    assert isinstance(replay, CommittedGlobalStopUpdate)
    assert replay.replayed
    assert replay.event == first.event
    assert replay.state == first.state
    assert len(store.events) == 1
    assert not hasattr(first, "result_class")


def test_global_stop_idempotency_conflict_has_no_event() -> None:
    store = _FakeAtomicGlobalStopStore(GlobalStopState(), _writer())
    first = store.apply_global_stop_update(_writer(), _activate(key="same"), _decision())
    assert isinstance(first, CommittedGlobalStopUpdate)
    conflict = store.apply_global_stop_update(
        _writer(),
        _activate(key="same", expected_version=first.state.version, stop_id="stop-2"),
        _decision(),
    )
    assert isinstance(conflict, GlobalStopConflict)
    assert conflict.conflict_class == "idempotency_key_reuse_conflict"
    assert len(store.events) == 1


def test_writer_token_is_excluded_from_global_stop_command_digest() -> None:
    command = _activate()
    assert _writer().writer_ref not in command.canonical_identity_payload()
    assert _writer(2).writer_ref not in command.canonical_identity_payload()
