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
    SafeWriterMetadata,
    WriterSessionError,
    WriterSessionFailureReason,
)


@dataclass(frozen=True)
class _StopIdempotencyEntry:
    command_digest: str
    committed: CommittedGlobalStopUpdate


class _FakeAtomicGlobalStopSession:
    def __init__(self, state: GlobalStopState, metadata: SafeWriterMetadata) -> None:
        self.state = state
        self._metadata = metadata
        self._active = True
        self._process_mismatch = False
        self._stale = False
        self.events = []
        self.idempotency = {}
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

    def apply_global_stop_update(
        self,
        command: GlobalStopCommand,
        decision: GlobalStopOperatorDecision,
    ) -> CommittedGlobalStopUpdate | GlobalStopConflict:
        if self._process_mismatch:
            raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH)
        if not self._active:
            raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_CLOSED)
        return self._apply_store_boundary(command, decision)

    def _apply_store_boundary(
        self,
        command: GlobalStopCommand,
        decision: GlobalStopOperatorDecision,
    ) -> CommittedGlobalStopUpdate | GlobalStopConflict:
        self.store_calls += 1
        if self._stale:
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


def _metadata(generation: int = 1) -> SafeWriterMetadata:
    return SafeWriterMetadata(
        writer_ref="writer-main",
        generation=generation,
        issued_ref=f"writer-issued-{generation}",
        acquired_at="2026-07-16T00:00:00Z",
    )


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
    session = _FakeAtomicGlobalStopSession(GlobalStopState(), _metadata())
    command = _activate()
    first = session.apply_global_stop_update(command, _decision())
    assert isinstance(first, CommittedGlobalStopUpdate)
    session.invalidate_writer()

    stale = session.apply_global_stop_update(command, _decision())
    assert isinstance(stale, GlobalStopConflict)
    assert stale.conflict_class == "stale_writer_token"
    assert len(session.events) == 1
    assert session.store_calls == 2


def test_global_stop_expected_version_conflict_has_no_event() -> None:
    session = _FakeAtomicGlobalStopSession(GlobalStopState(version=3, active=False), _metadata())
    outcome = session.apply_global_stop_update(_activate(expected_version=2), _decision())
    assert isinstance(outcome, GlobalStopConflict)
    assert outcome.conflict_class == "expected_version_conflict"
    assert session.events == []
    assert session.state.version == 3


def test_global_stop_domain_rejection_commits_event_and_unchanged_state() -> None:
    state = GlobalStopState()
    session = _FakeAtomicGlobalStopSession(state, _metadata())
    outcome = session.apply_global_stop_update(_activate(), _decision(authorized=False))
    assert isinstance(outcome, CommittedGlobalStopUpdate)
    assert outcome.state == state
    assert outcome.event.outcome.value == "domain_rejected"
    assert outcome.event.reason == "operator_authorization_required"
    assert session.events == [outcome.event]


def test_global_stop_exact_replay_preserves_original_event() -> None:
    session = _FakeAtomicGlobalStopSession(GlobalStopState(), _metadata())
    command = _activate()
    first = session.apply_global_stop_update(command, _decision())
    replay = session.apply_global_stop_update(command, _decision())
    assert isinstance(first, CommittedGlobalStopUpdate)
    assert isinstance(replay, CommittedGlobalStopUpdate)
    assert replay.replayed
    assert replay.event == first.event
    assert replay.state == first.state
    assert len(session.events) == 1
    assert not hasattr(first, "result_class")


def test_global_stop_idempotency_conflict_has_no_event() -> None:
    session = _FakeAtomicGlobalStopSession(GlobalStopState(), _metadata())
    first = session.apply_global_stop_update(_activate(key="same"), _decision())
    assert isinstance(first, CommittedGlobalStopUpdate)
    conflict = session.apply_global_stop_update(
        _activate(key="same", expected_version=first.state.version, stop_id="stop-2"),
        _decision(),
    )
    assert isinstance(conflict, GlobalStopConflict)
    assert conflict.conflict_class == "idempotency_key_reuse_conflict"
    assert len(session.events) == 1


def test_safe_writer_metadata_is_excluded_from_global_stop_command_digest() -> None:
    command = _activate()
    assert _metadata().writer_ref not in command.canonical_identity_payload()
    assert _metadata(2).writer_ref not in command.canonical_identity_payload()


def test_closed_writer_session_fails_with_session_closed_for_global_stop_update() -> None:
    session = _FakeAtomicGlobalStopSession(GlobalStopState(), _metadata())
    command = _activate()

    with session as active:
        assert active.active
    assert not session.active

    try:
        session.apply_global_stop_update(command, _decision())
    except WriterSessionError as exc:
        assert exc.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED
    else:  # pragma: no cover - defensive assertion for the contract test
        raise AssertionError("closed writer session did not fail locally")
    assert session.events == []


def test_closed_writer_session_does_not_return_stale_writer_conflict_for_global_stop_update() -> None:
    session = _FakeAtomicGlobalStopSession(GlobalStopState(), _metadata())
    command = _activate()
    session.close()

    try:
        session.apply_global_stop_update(command, _decision())
    except WriterSessionError as exc:
        assert exc.reason.value == "writer_session_closed"
        assert exc.reason.value != "stale_writer_token"
    else:  # pragma: no cover - defensive assertion for the contract test
        raise AssertionError("closed writer session did not fail locally")


def test_closed_writer_session_never_calls_global_stop_store() -> None:
    session = _FakeAtomicGlobalStopSession(GlobalStopState(), _metadata())
    command = _activate()
    session.close()

    try:
        session.apply_global_stop_update(command, _decision())
    except WriterSessionError:
        pass
    else:  # pragma: no cover - defensive assertion for the contract test
        raise AssertionError("closed writer session did not fail locally")
    assert session.store_calls == 0
    assert session.events == []
    assert session.idempotency == {}


def test_process_mismatch_is_session_failure_before_global_stop_apply() -> None:
    session = _FakeAtomicGlobalStopSession(GlobalStopState(), _metadata())
    command = _activate()
    session.simulate_process_mismatch()

    try:
        session.apply_global_stop_update(command, _decision())
    except WriterSessionError as exc:
        assert exc.reason is WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH
    else:  # pragma: no cover - defensive assertion for the contract test
        raise AssertionError("process mismatch did not fail locally")
    assert session.store_calls == 0
    assert session.events == []


def test_active_session_stale_fencing_remains_global_stop_apply_conflict() -> None:
    session = _FakeAtomicGlobalStopSession(GlobalStopState(), _metadata())
    command = _activate()
    session.invalidate_writer()

    outcome = session.apply_global_stop_update(command, _decision())
    assert isinstance(outcome, GlobalStopConflict)
    assert outcome.conflict_class == "stale_writer_token"
    assert session.store_calls == 1
    assert session.events == []
