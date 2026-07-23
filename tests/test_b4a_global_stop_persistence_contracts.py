from __future__ import annotations

from pathlib import Path

import pytest

from ge_nwp_coordinator.global_stop import (
    GlobalStopAction,
    GlobalStopCommand,
    GlobalStopEvaluationKind,
    GlobalStopEvent,
    GlobalStopEventOutcome,
    GlobalStopOperatorDecision,
    GlobalStopReasonClass,
    GlobalStopState,
    evaluate_global_stop_update,
)
from ge_nwp_coordinator.persistence_contracts import (
    B4_GLOBAL_STOP_APPLY_CONFLICT_CLASSES,
    FIRST_GLOBAL_STOP_EVENT_SEQUENCE,
    GLOBAL_STOP_EVENT_ROW_COLUMNS,
    GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS,
    GlobalStopEventRecordEnvelope,
    GlobalStopOperatorDecisionReceiptEnvelope,
    global_stop_event_canonical_digest,
    global_stop_event_canonical_json,
    global_stop_event_record_envelope_from_row,
    global_stop_operator_decision_canonical_digest,
    global_stop_operator_decision_canonical_json,
    global_stop_operator_decision_receipt_envelope_from_row,
    match_global_stop_event_idempotency,
    next_global_stop_event_sequence,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.state_store import CommittedGlobalStopUpdate, GlobalStopConflict


ROOT = Path(__file__).resolve().parents[1]
TS = "2026-07-22T12:00:02Z"


def _decision(*, ref: str = "operator-decision-1", authorized: bool = True) -> GlobalStopOperatorDecision:
    return GlobalStopOperatorDecision(
        decision_ref=ref,
        authorized=authorized,
        reason="accepted" if authorized else "operator_authorization_required",
    )


def _command(
    *,
    key: str = "global-stop-key-1",
    decision_ref: str = "operator-decision-1",
    stop_id: str = "global-stop-1",
) -> GlobalStopCommand:
    return GlobalStopCommand.create(
        action=GlobalStopAction.ACTIVATE,
        idempotency_key=key,
        expected_version=0,
        stop_id=stop_id,
        reason_class=GlobalStopReasonClass.OPERATOR_STOP,
        issuer_ref="operator-policy",
        issued_at="2026-07-22T12:00:00Z",
        operator_decision_ref=decision_ref,
    )


def _receipt_row(decision: GlobalStopOperatorDecision, *, created_at: str = TS) -> dict[str, object]:
    return {
        "decision_ref": decision.decision_ref,
        "authorized": 1 if decision.authorized else 0,
        "reason": decision.reason,
        "schema_id": decision.schema_id,
        "canonical_json": global_stop_operator_decision_canonical_json(decision),
        "canonical_digest": global_stop_operator_decision_canonical_digest(decision),
        "created_at": created_at,
    }


def _accepted() -> tuple[GlobalStopState, GlobalStopCommand, GlobalStopOperatorDecision, object]:
    state = GlobalStopState()
    command = _command()
    decision = _decision()
    evaluation = evaluate_global_stop_update(state, command, decision)
    assert evaluation.kind is GlobalStopEvaluationKind.ACCEPTED
    return state, command, decision, evaluation


def _rejected() -> tuple[GlobalStopState, GlobalStopCommand, GlobalStopOperatorDecision, object]:
    state = GlobalStopState()
    command = _command()
    decision = _decision(authorized=False)
    evaluation = evaluate_global_stop_update(state, command, decision)
    assert evaluation.kind is GlobalStopEvaluationKind.DOMAIN_REJECTED
    return state, command, decision, evaluation


def _event_row(event: GlobalStopEvent, replay_state: GlobalStopState, *, sequence: int = 0) -> dict[str, object]:
    return {
        "event_ref": event.event_ref,
        "event_sequence": sequence,
        "idempotency_key": event.idempotency_key,
        "command_digest": event.command_digest,
        "action": event.action.value,
        "source_version": event.source_version,
        "resulting_version": event.resulting_version,
        "outcome": event.outcome.value,
        "reason": event.reason,
        "operator_decision_ref": event.operator_decision_ref,
        "resulting_global_stop_ref": event.resulting_global_stop_ref,
        "resulting_status": event.resulting_status.value,
        "schema_id": event.schema_id,
        "event_json": global_stop_event_canonical_json(event),
        "event_digest": global_stop_event_canonical_digest(event),
        "replay_global_stop_json": replay_state.canonical_json(),
        "replay_global_stop_digest": replay_state.canonical_digest(),
        "created_at": TS,
    }


def _assert_store_error(exc: pytest.ExceptionInfo[SQLiteMutationStoreError]) -> None:
    assert exc.value.error_class == "database_integrity_failure"
    assert str(exc.value) == "database_integrity_failure"
    assert exc.value.internal_detail is None


def test_receipt_row_contract_round_trips_authorized_and_unauthorized_decisions() -> None:
    assert GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS == (
        "decision_ref",
        "authorized",
        "reason",
        "schema_id",
        "canonical_json",
        "canonical_digest",
        "created_at",
    )
    for decision in (_decision(), _decision(ref="operator-decision-2", authorized=False)):
        envelope = global_stop_operator_decision_receipt_envelope_from_row(_receipt_row(decision))
        assert type(envelope) is GlobalStopOperatorDecisionReceiptEnvelope
        assert envelope.decision == decision
        assert envelope.created_at == TS
        assert "canonical" not in repr(envelope)
        assert "operator-decision" not in repr(envelope)


def test_receipt_row_contract_rejects_canonical_digest_index_and_timestamp_drift() -> None:
    decision = _decision()
    base = _receipt_row(decision)
    for mutation in (
        {"authorized": True},
        {"authorized": 0},
        {"canonical_digest": "0" * 64},
        {"canonical_json": base["canonical_json"][:-1] + " "},
        {"created_at": "2026-07-22T12:00:02+00:00"},
        {"private_field": "not-allowed"},
    ):
        row = {**base, **mutation}
        with pytest.raises(SQLiteMutationStoreError) as exc_info:
            global_stop_operator_decision_receipt_envelope_from_row(row)
        _assert_store_error(exc_info)


def test_event_replay_row_contract_round_trips_accepted_and_domain_rejected_events() -> None:
    assert GLOBAL_STOP_EVENT_ROW_COLUMNS == (
        "event_ref",
        "event_sequence",
        "idempotency_key",
        "command_digest",
        "action",
        "source_version",
        "resulting_version",
        "outcome",
        "reason",
        "operator_decision_ref",
        "resulting_global_stop_ref",
        "resulting_status",
        "schema_id",
        "event_json",
        "event_digest",
        "replay_global_stop_json",
        "replay_global_stop_digest",
        "created_at",
    )
    for _source, _command_value, _decision_value, evaluation in (_accepted(), _rejected()):
        event = evaluation.event
        assert type(event) is GlobalStopEvent
        row = _event_row(event, evaluation.state, sequence=7)
        envelope = global_stop_event_record_envelope_from_row(row)
        assert type(envelope) is GlobalStopEventRecordEnvelope
        assert envelope.event == event
        assert envelope.replay_state == evaluation.state
        assert envelope.event_sequence == 7
        assert envelope.created_at == TS
        assert "global-stop-event" not in repr(envelope)
        assert "digest" not in repr(envelope)


def test_event_replay_row_contract_rejects_event_ref_index_replay_and_created_at_drift() -> None:
    _source, _command_value, _decision_value, evaluation = _accepted()
    event = evaluation.event
    assert type(event) is GlobalStopEvent
    base = _event_row(event, evaluation.state)
    wrong_event = GlobalStopEvent(
        event_ref="global-stop-event-000000000000000000000000",
        command_digest=event.command_digest,
        idempotency_key=event.idempotency_key,
        action=event.action,
        source_version=event.source_version,
        resulting_version=event.resulting_version,
        outcome=event.outcome,
        reason=event.reason,
        operator_decision_ref=event.operator_decision_ref,
        resulting_global_stop_ref=event.resulting_global_stop_ref,
        resulting_status=event.resulting_status,
    )
    for mutation in (
        {"event_ref": "other-event-ref"},
        {"event_json": global_stop_event_canonical_json(wrong_event)},
        {"event_digest": "0" * 64},
        {"replay_global_stop_json": GlobalStopState().canonical_json()},
        {"created_at": "2026-07-22T12:00:02+00:00"},
        {"event_sequence": True},
        {"private_field": "not-allowed"},
    ):
        row = {**base, **mutation}
        if "event_json" in mutation:
            row["event_digest"] = global_stop_event_canonical_digest(wrong_event)
        with pytest.raises(SQLiteMutationStoreError) as exc_info:
            global_stop_event_record_envelope_from_row(row)
        _assert_store_error(exc_info)


def test_global_stop_idempotency_match_returns_replay_conflict_or_none() -> None:
    _source, command, _decision_value, evaluation = _accepted()
    event = evaluation.event
    assert type(event) is GlobalStopEvent
    envelope = global_stop_event_record_envelope_from_row(_event_row(event, evaluation.state))

    assert match_global_stop_event_idempotency(None, command) is None
    replay = match_global_stop_event_idempotency(envelope, command)
    assert type(replay) is CommittedGlobalStopUpdate
    assert replay.replayed is True
    assert replay.event == event
    assert replay.state == evaluation.state

    changed = _command(key=command.idempotency_key, stop_id="global-stop-2")
    conflict = match_global_stop_event_idempotency(envelope, changed)
    assert type(conflict) is GlobalStopConflict
    assert conflict.conflict_class == "idempotency_key_reuse_conflict"

    wrong_key = _command(key="other-key")
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        match_global_stop_event_idempotency(envelope, wrong_key)
    _assert_store_error(exc_info)


def test_global_stop_sequence_contract_is_table_local_and_strict() -> None:
    assert FIRST_GLOBAL_STOP_EVENT_SEQUENCE == 0
    assert next_global_stop_event_sequence(None) == 0
    assert next_global_stop_event_sequence(0) == 1
    assert next_global_stop_event_sequence(9) == 10
    assert B4_GLOBAL_STOP_APPLY_CONFLICT_CLASSES == frozenset(
        {
            "stale_writer_token",
            "idempotency_key_reuse_conflict",
            "expected_version_conflict",
            "validation_failed",
        }
    )

    with pytest.raises(SQLiteMutationStoreError) as exhausted:
        next_global_stop_event_sequence(9223372036854775807)
    assert exhausted.value.error_class == "event_sequence_exhausted"
    for malformed in (True, -1, 1.5, "1", object()):
        with pytest.raises(SQLiteMutationStoreError) as exc_info:
            next_global_stop_event_sequence(malformed)  # type: ignore[arg-type]
        _assert_store_error(exc_info)


def test_persistence_contracts_add_no_sqlite_or_receipt_insert_grammar() -> None:
    source = (ROOT / "src/ge_nwp_coordinator/persistence_contracts.py").read_text(encoding="utf-8")
    assert "sqlite3" not in source
    assert "INSERT INTO global_stop_operator_decision_receipts" not in source
    assert "INSERT INTO global_stop_events" not in source
    assert "UPDATE global_stop_current" not in source
