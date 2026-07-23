from __future__ import annotations

import ast
from pathlib import Path

import pytest

from ge_nwp_coordinator.global_stop import (
    GlobalStopAction,
    GlobalStopCommand,
    GlobalStopEvaluation,
    GlobalStopEvaluationKind,
    GlobalStopEvent,
    GlobalStopEventOutcome,
    GlobalStopOperatorDecision,
    GlobalStopReasonClass,
    GlobalStopState,
    evaluate_global_stop_update,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
import ge_nwp_coordinator.sqlite_global_stop_write_contracts as write_contracts
from ge_nwp_coordinator.sqlite_global_stop_write_contracts import (
    _ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SPEC,
    _GLOBAL_STOP_EVENT_INSERT_SPEC,
    _AcceptedGlobalStopCurrentCasValues,
    _GlobalStopEventInsertValues,
    _GlobalStopWritePlan,
    _accepted_global_stop_current_cas_values,
    _global_stop_event_insert_values,
    _global_stop_write_plan,
)
from ge_nwp_coordinator.state_store import CommittedGlobalStopUpdate


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
TS = "2026-07-22T12:00:04Z"


def _decision(*, authorized: bool = True) -> GlobalStopOperatorDecision:
    return GlobalStopOperatorDecision(
        decision_ref="operator-decision-1",
        authorized=authorized,
        reason="accepted" if authorized else "operator_authorization_required",
    )


def _command() -> GlobalStopCommand:
    return GlobalStopCommand.create(
        action=GlobalStopAction.ACTIVATE,
        idempotency_key="global-stop-key-1",
        expected_version=0,
        stop_id="global-stop-1",
        reason_class=GlobalStopReasonClass.OPERATOR_STOP,
        issuer_ref="operator-policy",
        issued_at="2026-07-22T12:00:00Z",
        operator_decision_ref="operator-decision-1",
    )


def _accepted() -> tuple[GlobalStopState, GlobalStopEvaluation]:
    source = GlobalStopState()
    evaluation = evaluate_global_stop_update(source, _command(), _decision())
    assert evaluation.kind is GlobalStopEvaluationKind.ACCEPTED
    return source, evaluation


def _rejected() -> tuple[GlobalStopState, GlobalStopEvaluation]:
    source = GlobalStopState()
    evaluation = evaluate_global_stop_update(source, _command(), _decision(authorized=False))
    assert evaluation.kind is GlobalStopEvaluationKind.DOMAIN_REJECTED
    return source, evaluation


def _assert_store_error(exc: pytest.ExceptionInfo[SQLiteMutationStoreError]) -> None:
    assert exc.value.error_class == "database_integrity_failure"
    assert exc.value.internal_detail is None


def test_event_insert_and_singleton_cas_specs_are_exact_and_private() -> None:
    assert write_contracts.__all__ == ()
    assert _GLOBAL_STOP_EVENT_INSERT_SPEC.table_name == "global_stop_events"
    assert _GLOBAL_STOP_EVENT_INSERT_SPEC.parameter_count == 18
    assert _GLOBAL_STOP_EVENT_INSERT_SPEC.sql == (
        "INSERT INTO global_stop_events (\n"
        "    event_ref,\n"
        "    event_sequence,\n"
        "    idempotency_key,\n"
        "    command_digest,\n"
        "    action,\n"
        "    source_version,\n"
        "    resulting_version,\n"
        "    outcome,\n"
        "    reason,\n"
        "    operator_decision_ref,\n"
        "    resulting_global_stop_ref,\n"
        "    resulting_status,\n"
        "    schema_id,\n"
        "    event_json,\n"
        "    event_digest,\n"
        "    replay_global_stop_json,\n"
        "    replay_global_stop_digest,\n"
        "    created_at\n"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    assert _ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SPEC.table_name == "global_stop_current"
    assert _ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SPEC.parameter_count == 10
    assert _ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SPEC.sql == (
        "UPDATE global_stop_current\n"
        "SET schema_id = ?,\n"
        "    version = ?,\n"
        "    active = ?,\n"
        "    stop_id = ?,\n"
        "    reason_class = ?,\n"
        "    issuer_ref = ?,\n"
        "    issued_at = ?,\n"
        "    operator_decision_ref = ?,\n"
        "    updated_at = ?\n"
        "WHERE singleton_id = 1\n"
        "  AND version = ?"
    )


def test_accepted_write_plan_contains_one_event_insert_and_one_singleton_cas() -> None:
    source, evaluation = _accepted()
    plan = _global_stop_write_plan(evaluation, source_state=source, event_sequence=5, transaction_timestamp=TS)

    assert type(plan) is _GlobalStopWritePlan
    assert type(plan.planned_update) is CommittedGlobalStopUpdate
    assert plan.planned_update.replayed is False
    assert type(plan.event_insert) is _GlobalStopEventInsertValues
    assert type(plan.accepted_global_stop_current_cas) is _AcceptedGlobalStopCurrentCasValues
    assert plan.event_insert.event_sequence == 5
    assert plan.event_insert.created_at == TS
    assert plan.accepted_global_stop_current_cas.updated_at == TS
    assert plan.event_insert.event == evaluation.event
    assert plan.event_insert.replay_state == evaluation.state
    assert plan.accepted_global_stop_current_cas.source_state == source
    assert plan.accepted_global_stop_current_cas.resulting_state == evaluation.state
    assert plan.event_insert.parameters[0] == evaluation.event.event_ref
    assert plan.event_insert.parameters[1] == 5
    assert plan.event_insert.parameters[-1] == TS
    assert plan.accepted_global_stop_current_cas.parameters == (
        evaluation.state.schema_id,
        evaluation.state.version,
        1,
        evaluation.state.stop_id,
        evaluation.state.reason_class.value,
        evaluation.state.issuer_ref,
        evaluation.state.issued_at,
        evaluation.state.operator_decision_ref,
        TS,
        source.version,
    )


def test_domain_rejected_write_plan_is_event_only_with_unchanged_replay_state() -> None:
    source, evaluation = _rejected()
    plan = _global_stop_write_plan(evaluation, source_state=source, event_sequence=0, transaction_timestamp=TS)

    assert type(plan) is _GlobalStopWritePlan
    assert plan.accepted_global_stop_current_cas is None
    assert plan.planned_update.replayed is False
    assert plan.planned_update.state == source
    assert plan.event_insert.replay_state == source
    assert plan.event_insert.event.outcome is GlobalStopEventOutcome.DOMAIN_REJECTED
    assert plan.event_insert.parameters[1] == 0
    assert plan.event_insert.parameters[-1] == TS


def test_direct_construction_and_hostile_model_inputs_fail_closed() -> None:
    source, evaluation = _accepted()
    values = _global_stop_event_insert_values(evaluation, event_sequence=1, transaction_timestamp=TS)
    with pytest.raises(SQLiteMutationStoreError) as wrong_count:
        _GlobalStopEventInsertValues(
            spec=_GLOBAL_STOP_EVENT_INSERT_SPEC,
            parameters=values.parameters[:-1],
            event=values.event,
            replay_state=values.replay_state,
            event_sequence=1,
            created_at=TS,
        )
    _assert_store_error(wrong_count)

    event = evaluation.event
    assert type(event) is GlobalStopEvent
    wrong_ref = GlobalStopEvent(
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
    forged_evaluation = GlobalStopEvaluation(
        kind=evaluation.kind,
        state=evaluation.state,
        event=wrong_ref,
        reason=evaluation.reason,
    )
    with pytest.raises(SQLiteMutationStoreError) as wrong_event_ref:
        _global_stop_event_insert_values(forged_evaluation, event_sequence=1, transaction_timestamp=TS)
    _assert_store_error(wrong_event_ref)

    pre_apply_invalid = GlobalStopEvaluation(
        kind=GlobalStopEvaluationKind.PRE_APPLY_INVALID,
        state=source,
        event=None,
        reason="decision_reference_mismatch",
    )
    with pytest.raises(SQLiteMutationStoreError) as invalid_evaluation:
        _global_stop_write_plan(pre_apply_invalid, source_state=source, event_sequence=1, transaction_timestamp=TS)
    _assert_store_error(invalid_evaluation)


def test_accepted_cas_values_require_source_and_result_version_relationship() -> None:
    source, evaluation = _accepted()
    cas = _accepted_global_stop_current_cas_values(source, evaluation.state, TS)
    assert cas.parameters[-1] == source.version

    with pytest.raises(SQLiteMutationStoreError) as invalid_source:
        _accepted_global_stop_current_cas_values(evaluation.state, evaluation.state, TS)
    _assert_store_error(invalid_source)


def test_write_contract_module_has_no_runtime_execution_or_receipt_provisioning() -> None:
    source = (PACKAGE_DIR / "sqlite_global_stop_write_contracts.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert "INSERT INTO global_stop_operator_decision_receipts" not in source
    assert "INSERT OR REPLACE" not in source
    assert "ON CONFLICT" not in source
    assert "RETURNING" not in source
    assert "BEGIN" not in source
    assert "COMMIT" not in source
    assert "ROLLBACK" not in source
    assert "sqlite3" not in source
    assert "_run_atomic_global_stop_apply" not in source
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"execute", "executemany", "executescript", "commit", "rollback"}
            elif isinstance(node.func, ast.Name):
                assert node.func.id not in {"execute", "commit", "rollback"}
