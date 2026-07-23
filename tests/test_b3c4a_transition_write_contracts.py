from __future__ import annotations

import ast
from dataclasses import fields, replace
import inspect
from pathlib import Path
import re
import traceback

import pytest

import ge_nwp_coordinator
import ge_nwp_coordinator.sqlite_mutation_transaction_contracts as mutation_contracts
import ge_nwp_coordinator.sqlite_writer_session as writer_session_module
import ge_nwp_coordinator.sqlite_transition_write_contracts as write_contracts
from ge_nwp_coordinator.canonicalization import canonical_json_bytes
from ge_nwp_coordinator.global_stop import GlobalStopState
from ge_nwp_coordinator.lease import (
    AuthorizationDecision,
    AuthorizationModel,
    LeaseIdentityValidation,
    LeaseRuntimeDecision,
    LeaseRuntimeStatus,
)
from ge_nwp_coordinator.persistence_contracts import (
    SQLITE_SIGNED_INT_MAX,
    TRANSITION_EVENT_ROW_COLUMNS,
    WORK_ITEM_ROW_COLUMNS,
    encode_sqlite_boolean,
    transition_event_record_envelope_from_row,
    work_item_record_envelope_from_row,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from ge_nwp_coordinator.state_machine import (
    WORK_ITEM_STATE_SCHEMA_ID,
    DependencyDecision,
    TransitionCommand,
    TransitionContext,
    TransitionEvaluation,
    TransitionEvaluationKind,
    TransitionEvent,
    TransitionEventOutcome,
    WorkItemRecord,
    WorkItemState,
    evaluate_transition,
)
from ge_nwp_coordinator.state_store import CommittedTransition, WriterSessionFailureReason


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
WRITE_CONTRACTS_PATH = PACKAGE_DIR / "sqlite_transition_write_contracts.py"
MUTATION_CONTRACTS_PATH = PACKAGE_DIR / "sqlite_mutation_transaction_contracts.py"
TRANSACTION_MODULE_PATH = PACKAGE_DIR / "sqlite_transition_transaction.py"
WRITER_SESSION_PATH = PACKAGE_DIR / "sqlite_writer_session.py"
PACKAGE_EXPORT_PATH = PACKAGE_DIR / "__init__.py"
MIGRATION_DIR = PACKAGE_DIR / "sqlite_migrations"
CANONICAL_TIMESTAMP = "2026-07-14T00:00:03Z"
PRIVATE_SENTINEL = "b3c4a-private-sentinel-do-not-leak"


EXPECTED_EVENT_INSERT_SQL = """INSERT INTO transition_events (
    event_ref,
    event_sequence,
    work_item_id,
    lease_id,
    idempotency_key,
    command_digest,
    source_state,
    source_version,
    resulting_state,
    resulting_version,
    outcome,
    reason,
    evidence_refs_json,
    budget_cost_delta,
    attempt_count_delta,
    repair_count_delta,
    lease_identity_decision_ref,
    authorization_decision_ref,
    dependency_decision_ref,
    global_stop_ref,
    global_stop_version,
    schema_id,
    event_json,
    event_digest,
    replay_work_item_json,
    replay_work_item_digest,
    created_at
) VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?
)"""

EXPECTED_ACCEPTED_CAS_SQL = """UPDATE work_items
SET
    lease_id = ?,
    backlog_id = ?,
    schema_id = ?,
    state = ?,
    version = ?,
    attempt_count = ?,
    repair_count = ?,
    budget_consumed = ?,
    budget_limit = ?,
    max_attempts = ?,
    max_repairs = ?,
    cleanup_required = ?,
    updated_at = ?
WHERE work_item_id = ?
  AND version = ?"""


def _identity() -> LeaseIdentityValidation:
    return LeaseIdentityValidation(
        identity_valid=True,
        digest="a" * 64,
        issues=(),
        decision_ref="lease-identity-lease-a2-p1",
        lease_ref="lease-a2-p1",
    )


def _authorization(*, authorized: bool = True) -> AuthorizationDecision:
    identity = _identity()
    return AuthorizationDecision(
        decision_ref="authz-lease-a2-p1",
        lease_ref=identity.lease_ref,
        lease_identity_decision_ref=identity.decision_ref,
        lease_identity_valid=identity.identity_valid,
        authorization_model=AuthorizationModel.OPERATOR_POLICY if authorized else AuthorizationModel.UNSUPPORTED,
        authorized=authorized,
        executable=False,
        reason="accepted" if authorized else "unsupported_authorization_model",
    )


def _context(
    *,
    authorized: bool = True,
    dependency_decision: DependencyDecision | None = None,
    evaluated_at: str = CANONICAL_TIMESTAMP,
) -> TransitionContext:
    return TransitionContext(
        lease_identity=_identity(),
        authorization=_authorization(authorized=authorized),
        lease_runtime=LeaseRuntimeDecision(
            lease_ref="lease-a2-p1",
            evaluated_at=evaluated_at,
            status=LeaseRuntimeStatus.ACTIVE,
            reason="lease_runtime_active",
        ),
        global_stop=GlobalStopState(),
        dependency_decision=dependency_decision or DependencyDecision(),
    )


def _record(**overrides: object) -> WorkItemRecord:
    fields = {
        "schema_id": WORK_ITEM_STATE_SCHEMA_ID,
        "work_item_id": "wi-1",
        "lease_id": "lease-a2-p1",
        "backlog_id": "backlog-a2-p1",
        "state": WorkItemState.PROPOSED,
        "version": 0,
        "attempt_count": 0,
        "repair_count": 0,
        "budget_consumed": 0,
        "budget_limit": 0,
        "max_attempts": 1,
        "max_repairs": 0,
        "cleanup_required": False,
    }
    fields.update(overrides)
    return WorkItemRecord(**fields)


def _command(
    record: WorkItemRecord,
    context: TransitionContext,
    *,
    target_state: WorkItemState = WorkItemState.LEASE_ADMITTED,
    idempotency_key: str = "transition-k1",
    work_item_id: str | None = None,
    evidence_refs: tuple[str, ...] = (),
    budget_cost: int = 0,
) -> TransitionCommand:
    return TransitionCommand.create(
        work_item_id=work_item_id or record.work_item_id,
        idempotency_key=idempotency_key,
        expected_version=record.version,
        target_state=target_state,
        lease_identity_decision_ref=context.lease_identity.decision_ref,
        authorization_decision_ref=context.authorization.decision_ref,
        global_stop_ref=context.global_stop.stop_ref,
        global_stop_version=context.global_stop.version,
        dependency_decision_ref=context.dependency_decision.decision_ref if target_state is WorkItemState.READY else None,
        evidence_refs=evidence_refs,
        budget_cost=budget_cost,
    )


def _accepted_evaluation() -> tuple[WorkItemRecord, TransitionEvaluation]:
    record = _record(max_attempts=2, max_repairs=1)
    context = _context()
    command = _command(record, context, evidence_refs=("evidence-a",), budget_cost=0)
    evaluation = evaluate_transition(record, command, context)
    assert evaluation.kind is TransitionEvaluationKind.ACCEPTED
    assert evaluation.event is not None
    return record, evaluation


def _domain_rejected_evaluation() -> tuple[WorkItemRecord, TransitionEvaluation]:
    record = _record()
    context = _context(authorized=False)
    command = _command(record, context, idempotency_key="transition-k-domain")
    evaluation = evaluate_transition(record, command, context)
    assert evaluation.kind is TransitionEvaluationKind.DOMAIN_REJECTED
    assert evaluation.event is not None
    return record, evaluation


def _pre_apply_invalid_evaluation() -> tuple[WorkItemRecord, TransitionEvaluation]:
    record = _record()
    context = _context()
    command = _command(
        record,
        context,
        idempotency_key="transition-k-invalid",
        work_item_id="wi-other",
    )
    evaluation = evaluate_transition(record, command, context)
    assert evaluation.kind is TransitionEvaluationKind.PRE_APPLY_INVALID
    assert evaluation.event is None
    return record, evaluation


def _assert_mutation_error(
    exc_info: pytest.ExceptionInfo[SQLiteMutationStoreError],
    code: SQLiteMutationStoreErrorCode,
    capsys: pytest.CaptureFixture[str] | None = None,
) -> None:
    assert exc_info.value.error_class == code.value
    assert str(exc_info.value) == code.value
    assert exc_info.value.internal_detail is None
    assert PRIVATE_SENTINEL not in repr(exc_info.value)
    assert PRIVATE_SENTINEL not in str(exc_info.value)
    assert PRIVATE_SENTINEL not in repr(exc_info.value.args)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None
    assert not getattr(exc_info.value, "__notes__", ())
    formatted = "".join(traceback.format_exception(type(exc_info.value), exc_info.value, exc_info.value.__traceback__))
    assert PRIVATE_SENTINEL not in formatted
    if capsys is not None:
        captured = capsys.readouterr()
        assert PRIVATE_SENTINEL not in captured.out
        assert PRIVATE_SENTINEL not in captured.err


def _event_row(values: object) -> dict[str, object]:
    return dict(zip(write_contracts._TRANSITION_EVENT_INSERT_SPEC.columns, values.parameters, strict=True))


def _expected_event_parameters(event: TransitionEvent, replay_record: WorkItemRecord, sequence: int) -> tuple[object, ...]:
    return (
        event.event_ref,
        sequence,
        event.work_item_id,
        event.lease_id,
        event.idempotency_key,
        event.command_digest,
        event.source_state.value,
        event.source_version,
        event.resulting_state.value,
        event.resulting_version,
        event.outcome.value,
        event.reason,
        canonical_json_bytes(list(event.evidence_refs)).decode("utf-8"),
        event.budget_cost_delta,
        event.attempt_count_delta,
        event.repair_count_delta,
        event.lease_identity_decision_ref,
        event.authorization_decision_ref,
        event.dependency_decision_ref,
        event.global_stop_ref,
        event.global_stop_version,
        event.schema_id,
        event.canonical_json(),
        event.canonical_digest(),
        replay_record.canonical_json(),
        replay_record.canonical_digest(),
        event.lease_runtime.evaluated_at,
    )


def _cas_row(values: object) -> dict[str, object]:
    record = values.resulting_record
    updated_at = values.updated_at
    row = {
        "work_item_id": record.work_item_id,
        "lease_id": record.lease_id,
        "backlog_id": record.backlog_id,
        "schema_id": record.schema_id,
        "state": record.state.value,
        "version": record.version,
        "attempt_count": record.attempt_count,
        "repair_count": record.repair_count,
        "budget_consumed": record.budget_consumed,
        "budget_limit": record.budget_limit,
        "max_attempts": record.max_attempts,
        "max_repairs": record.max_repairs,
        "cleanup_required": encode_sqlite_boolean(record.cleanup_required, "accepted_work_item_cas.cleanup_required"),
        "updated_at": updated_at,
    }
    assert tuple(row) == WORK_ITEM_ROW_COLUMNS
    return row


def _manual_cas_records() -> tuple[WorkItemRecord, WorkItemRecord]:
    source = _record(
        version=3,
        attempt_count=1,
        repair_count=0,
        budget_consumed=2,
        budget_limit=9,
        max_attempts=5,
        max_repairs=4,
    )
    resulting = replace(
        source,
        state=WorkItemState.BLOCKED,
        version=4,
        attempt_count=2,
        repair_count=1,
        budget_consumed=7,
        cleanup_required=True,
    )
    return source, resulting


def _forged_from_model(model: object, **overrides: object) -> object:
    forged = object.__new__(type(model))
    for model_field in fields(type(model)):
        object.__setattr__(forged, model_field.name, getattr(model, model_field.name))
    for name, value in overrides.items():
        object.__setattr__(forged, name, value)
    return forged


def _shadow_callable(
    model: object,
    name: str,
    calls: list[str],
    *,
    hostile: bool = False,
    result: object = PRIVATE_SENTINEL,
) -> None:
    def shadow(*_args: object, **_kwargs: object) -> object:
        calls.append(name)
        if hostile:
            raise ValueError(PRIVATE_SENTINEL)
        return result

    object.__setattr__(model, name, shadow)


def _accepted_value_parts() -> tuple[WorkItemRecord, TransitionEvaluation, object, object, CommittedTransition]:
    source, evaluation = _accepted_evaluation()
    event_insert = write_contracts._transition_event_insert_values(evaluation, 0, CANONICAL_TIMESTAMP)
    cas = write_contracts._accepted_work_item_cas_values(source, evaluation.record, CANONICAL_TIMESTAMP)
    assert evaluation.event is not None
    planned = CommittedTransition(record=evaluation.record, event=evaluation.event, replayed=False)
    return source, evaluation, event_insert, cas, planned


def test_event_insert_spec_is_exact_and_immutable() -> None:
    spec = write_contracts._TRANSITION_EVENT_INSERT_SPEC

    assert spec.table_name == "transition_events"
    assert spec.columns == TRANSITION_EVENT_ROW_COLUMNS
    assert len(spec.columns) == 27
    assert spec.parameter_count == 27
    assert spec.sql == EXPECTED_EVENT_INSERT_SQL
    assert spec.sql.count("?") == 27
    assert "RETURNING" not in spec.sql.upper()
    assert "REPLACE" not in spec.sql.upper()
    assert "*" not in spec.sql
    assert not hasattr(spec, "execute")
    assert repr(spec) == "<_TransitionEventInsertSpec>"


def test_accepted_work_item_cas_spec_is_exact_and_narrow() -> None:
    spec = write_contracts._ACCEPTED_WORK_ITEM_CAS_SPEC

    assert spec.table_name == "work_items"
    assert spec.set_columns == WORK_ITEM_ROW_COLUMNS[1:]
    assert spec.where_columns == ("work_item_id", "version")
    assert spec.parameter_count == 15
    assert spec.sql == EXPECTED_ACCEPTED_CAS_SQL
    assert spec.sql.count("?") == 15
    assert "RETURNING" not in spec.sql.upper()
    assert re.search(r"WHERE work_item_id = \?\n  AND version = \?", spec.sql)
    assert "WHERE" in spec.sql
    assert not hasattr(spec, "execute")
    assert repr(spec) == "<_AcceptedWorkItemCasSpec>"


def test_event_insert_values_for_accepted_evaluation_round_trip_through_adapter() -> None:
    _source_record, evaluation = _accepted_evaluation()
    event = evaluation.event
    assert event is not None

    values = write_contracts._transition_event_insert_values(evaluation, 0, CANONICAL_TIMESTAMP)
    row = _event_row(values)
    envelope = transition_event_record_envelope_from_row(row)

    assert values.event_sequence == 0
    assert values.created_at == event.lease_runtime.evaluated_at
    assert values.parameters == _expected_event_parameters(event, evaluation.record, 0)
    assert tuple(row) == TRANSITION_EVENT_ROW_COLUMNS
    assert envelope.event_sequence == 0
    assert envelope.event == event
    assert envelope.replay_record == evaluation.record
    assert envelope.created_at == CANONICAL_TIMESTAMP
    assert row["event_json"] == event.canonical_json()
    assert row["event_digest"] == event.canonical_digest()
    assert row["replay_work_item_json"] == evaluation.record.canonical_json()
    assert row["replay_work_item_digest"] == evaluation.record.canonical_digest()
    assert repr(values) == "<_TransitionEventInsertValues>"
    assert "wi-1" not in repr(values)


def test_event_insert_values_for_domain_rejection_round_trip_through_adapter() -> None:
    source_record, evaluation = _domain_rejected_evaluation()
    event = evaluation.event
    assert event is not None

    values = write_contracts._transition_event_insert_values(evaluation, 1, CANONICAL_TIMESTAMP)
    row = _event_row(values)
    envelope = transition_event_record_envelope_from_row(row)

    assert event.outcome is TransitionEventOutcome.DOMAIN_REJECTED
    assert evaluation.record == source_record
    assert values.parameters == _expected_event_parameters(event, source_record, 1)
    assert envelope.event == event
    assert envelope.replay_record == source_record
    assert envelope.created_at == CANONICAL_TIMESTAMP
    assert row["budget_cost_delta"] == 0
    assert row["attempt_count_delta"] == 0
    assert row["repair_count_delta"] == 0


def test_event_insert_values_accept_sqlite_signed_max_as_supplied_valid_sequence() -> None:
    _source_record, evaluation = _accepted_evaluation()

    values = write_contracts._transition_event_insert_values(evaluation, SQLITE_SIGNED_INT_MAX, CANONICAL_TIMESTAMP)

    assert values.event_sequence == SQLITE_SIGNED_INT_MAX
    assert values.parameters[1] == SQLITE_SIGNED_INT_MAX
    assert transition_event_record_envelope_from_row(_event_row(values)).event_sequence == SQLITE_SIGNED_INT_MAX


@pytest.mark.parametrize("bad_sequence", [True, -1, SQLITE_SIGNED_INT_MAX + 1, "0", 0.0])
def test_event_insert_values_reject_invalid_sequences(bad_sequence: object) -> None:
    _source_record, evaluation = _accepted_evaluation()

    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        write_contracts._transition_event_insert_values(evaluation, bad_sequence, CANONICAL_TIMESTAMP)  # type: ignore[arg-type]

    _assert_mutation_error(exc_info, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def test_event_insert_values_reject_timestamp_mismatch_and_pre_apply_invalid() -> None:
    _source_record, accepted = _accepted_evaluation()
    _invalid_source, pre_apply_invalid = _pre_apply_invalid_evaluation()

    with pytest.raises(SQLiteMutationStoreError) as mismatch:
        write_contracts._transition_event_insert_values(accepted, 0, "2026-07-14T00:00:04Z")
    _assert_mutation_error(mismatch, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    with pytest.raises(SQLiteMutationStoreError) as invalid:
        write_contracts._transition_event_insert_values(pre_apply_invalid, 0, CANONICAL_TIMESTAMP)
    _assert_mutation_error(invalid, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def test_event_insert_values_do_not_leak_private_inputs_in_errors() -> None:
    _source_record, evaluation = _accepted_evaluation()

    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        write_contracts._transition_event_insert_values(evaluation, PRIVATE_SENTINEL, CANONICAL_TIMESTAMP)  # type: ignore[arg-type]

    _assert_mutation_error(exc_info, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def test_event_insert_values_direct_construction_revalidates_canonical_parameters() -> None:
    _source, evaluation, values, _cas, _planned = _accepted_value_parts()

    direct = write_contracts._TransitionEventInsertValues(
        spec=values.spec,
        parameters=values.parameters,
        event=values.event,
        replay_record=values.replay_record,
        event_sequence=values.event_sequence,
        created_at=values.created_at,
    )

    assert direct == values
    assert direct is not values
    assert direct.event == values.event
    assert direct.event is not values.event
    assert direct.replay_record == values.replay_record
    assert direct.replay_record is not values.replay_record

    bad_parameters = tuple("not-canonical-json" if index == 22 else value for index, value in enumerate(values.parameters))
    with pytest.raises(SQLiteMutationStoreError) as bad_canonical:
        write_contracts._TransitionEventInsertValues(
            spec=values.spec,
            parameters=bad_parameters,
            event=values.event,
            replay_record=values.replay_record,
            event_sequence=values.event_sequence,
            created_at=values.created_at,
        )
    _assert_mutation_error(bad_canonical, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    bad_sequence = tuple(1 if index == 1 else value for index, value in enumerate(values.parameters))
    with pytest.raises(SQLiteMutationStoreError) as sequence:
        write_contracts._TransitionEventInsertValues(
            spec=values.spec,
            parameters=bad_sequence,
            event=values.event,
            replay_record=values.replay_record,
            event_sequence=values.event_sequence,
            created_at=values.created_at,
        )
    _assert_mutation_error(sequence, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    with pytest.raises(SQLiteMutationStoreError) as timestamp:
        write_contracts._TransitionEventInsertValues(
            spec=values.spec,
            parameters=values.parameters,
            event=values.event,
            replay_record=values.replay_record,
            event_sequence=values.event_sequence,
            created_at="2026-07-14T00:00:04Z",
        )
    _assert_mutation_error(timestamp, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    bad_replay = replace(values.replay_record, work_item_id="wi-other")
    bad_replay_parameters = tuple(
        bad_replay.canonical_json() if index == 24 else bad_replay.canonical_digest() if index == 25 else value
        for index, value in enumerate(values.parameters)
    )
    with pytest.raises(SQLiteMutationStoreError) as replay:
        write_contracts._TransitionEventInsertValues(
            spec=values.spec,
            parameters=bad_replay_parameters,
            event=values.event,
            replay_record=bad_replay,
            event_sequence=values.event_sequence,
            created_at=values.created_at,
        )
    _assert_mutation_error(replay, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    assert evaluation.event is not None


def test_event_insert_values_reject_forged_nested_shells_and_redact_exception_graph(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _source, _evaluation, values, _cas, _planned = _accepted_value_parts()
    forged_event = _forged_from_model(values.event, event_ref=PRIVATE_SENTINEL)

    with pytest.raises(SQLiteMutationStoreError) as event_error:
        write_contracts._TransitionEventInsertValues(
            spec=values.spec,
            parameters=values.parameters,
            event=forged_event,  # type: ignore[arg-type]
            replay_record=values.replay_record,
            event_sequence=values.event_sequence,
            created_at=values.created_at,
        )
    _assert_mutation_error(event_error, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE, capsys)

    forged_replay = _forged_from_model(values.replay_record, work_item_id=PRIVATE_SENTINEL)
    with pytest.raises(SQLiteMutationStoreError) as replay_error:
        write_contracts._TransitionEventInsertValues(
            spec=values.spec,
            parameters=values.parameters,
            event=values.event,
            replay_record=forged_replay,  # type: ignore[arg-type]
            event_sequence=values.event_sequence,
            created_at=values.created_at,
        )
    _assert_mutation_error(replay_error, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE, capsys)


def test_accepted_cas_values_map_every_current_field_and_round_trip() -> None:
    source, resulting = _manual_cas_records()

    values = write_contracts._accepted_work_item_cas_values(source, resulting, CANONICAL_TIMESTAMP)
    row = _cas_row(values)
    envelope = work_item_record_envelope_from_row(row)

    assert values.parameters == (
        resulting.lease_id,
        resulting.backlog_id,
        resulting.schema_id,
        resulting.state.value,
        resulting.version,
        resulting.attempt_count,
        resulting.repair_count,
        resulting.budget_consumed,
        resulting.budget_limit,
        resulting.max_attempts,
        resulting.max_repairs,
        1,
        CANONICAL_TIMESTAMP,
        source.work_item_id,
        source.version,
    )
    assert values.parameters[11] == encode_sqlite_boolean(resulting.cleanup_required, "cleanup")
    assert values.parameters[-2:] == (source.work_item_id, source.version)
    assert envelope.record == resulting
    assert envelope.updated_at == CANONICAL_TIMESTAMP
    assert repr(values) == "<_AcceptedWorkItemCasValues>"
    assert "wi-1" not in repr(values)


def test_accepted_cas_values_from_accepted_evaluator_result() -> None:
    source, evaluation = _accepted_evaluation()

    values = write_contracts._accepted_work_item_cas_values(source, evaluation.record, CANONICAL_TIMESTAMP)

    assert values.resulting_record == evaluation.record
    assert values.parameters[-2:] == (source.work_item_id, source.version)
    assert work_item_record_envelope_from_row(_cas_row(values)).record == evaluation.record


def test_accepted_cas_values_reject_wrong_identity_version_and_rejection_shape() -> None:
    source, resulting = _manual_cas_records()

    with pytest.raises(SQLiteMutationStoreError) as wrong_work_item:
        write_contracts._accepted_work_item_cas_values(
            source,
            replace(resulting, work_item_id="wi-other"),
            CANONICAL_TIMESTAMP,
        )
    _assert_mutation_error(wrong_work_item, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    with pytest.raises(SQLiteMutationStoreError) as wrong_version:
        write_contracts._accepted_work_item_cas_values(source, replace(resulting, version=5), CANONICAL_TIMESTAMP)
    _assert_mutation_error(wrong_version, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    with pytest.raises(SQLiteMutationStoreError) as domain_rejected:
        write_contracts._accepted_work_item_cas_values(source, source, CANONICAL_TIMESTAMP)
    _assert_mutation_error(domain_rejected, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def test_accepted_cas_values_reject_timestamp_mismatch_and_non_record_inputs() -> None:
    source, resulting = _manual_cas_records()

    with pytest.raises(SQLiteMutationStoreError) as timestamp:
        write_contracts._accepted_work_item_cas_values(source, resulting, "not-a-timestamp")
    _assert_mutation_error(timestamp, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    with pytest.raises(SQLiteMutationStoreError) as wrong_type:
        write_contracts._accepted_work_item_cas_values(PRIVATE_SENTINEL, resulting, CANONICAL_TIMESTAMP)  # type: ignore[arg-type]
    _assert_mutation_error(wrong_type, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def test_accepted_cas_values_direct_construction_revalidates_every_parameter() -> None:
    source, resulting = _manual_cas_records()
    values = write_contracts._accepted_work_item_cas_values(source, resulting, CANONICAL_TIMESTAMP)

    direct = write_contracts._AcceptedWorkItemCasValues(
        spec=values.spec,
        parameters=values.parameters,
        source_record=source,
        resulting_record=resulting,
        updated_at=CANONICAL_TIMESTAMP,
    )

    assert direct == values
    assert direct.source_record == source
    assert direct.source_record is not source
    assert direct.resulting_record == resulting
    assert direct.resulting_record is not resulting

    mutations = (
        (3, WorkItemState.FAILED.value),
        (-1, source.version + 1),
        (-2, "wi-other"),
        (12, "2026-07-14T00:00:04Z"),
        (11, 0),
        (11, True),
    )
    for index, replacement in mutations:
        bad_parameters = tuple(replacement if parameter_index == index % len(values.parameters) else value for parameter_index, value in enumerate(values.parameters))
        with pytest.raises(SQLiteMutationStoreError) as exc_info:
            write_contracts._AcceptedWorkItemCasValues(
                spec=values.spec,
                parameters=bad_parameters,
                source_record=source,
                resulting_record=resulting,
                updated_at=CANONICAL_TIMESTAMP,
            )
        _assert_mutation_error(exc_info, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def test_accepted_cas_values_reject_forged_records_and_redact_exception_graph(
    capsys: pytest.CaptureFixture[str],
) -> None:
    source, resulting = _manual_cas_records()
    values = write_contracts._accepted_work_item_cas_values(source, resulting, CANONICAL_TIMESTAMP)
    forged_source = _forged_from_model(source, version=True)

    with pytest.raises(SQLiteMutationStoreError) as source_error:
        write_contracts._AcceptedWorkItemCasValues(
            spec=values.spec,
            parameters=values.parameters,
            source_record=forged_source,  # type: ignore[arg-type]
            resulting_record=resulting,
            updated_at=CANONICAL_TIMESTAMP,
        )
    _assert_mutation_error(source_error, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE, capsys)

    forged_result = _forged_from_model(resulting, cleanup_required=PRIVATE_SENTINEL)
    with pytest.raises(SQLiteMutationStoreError) as result_error:
        write_contracts._AcceptedWorkItemCasValues(
            spec=values.spec,
            parameters=values.parameters,
            source_record=source,
            resulting_record=forged_result,  # type: ignore[arg-type]
            updated_at=CANONICAL_TIMESTAMP,
        )
    _assert_mutation_error(result_error, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE, capsys)


def test_write_plan_for_accepted_evaluation_contains_private_planned_result_and_cas() -> None:
    source, evaluation = _accepted_evaluation()

    plan = write_contracts._transition_write_plan(
        evaluation,
        source_record=source,
        event_sequence=0,
        transaction_timestamp=CANONICAL_TIMESTAMP,
    )

    assert type(plan.planned_transition) is CommittedTransition
    assert plan.planned_transition.replayed is False
    assert plan.planned_transition.event == evaluation.event
    assert plan.planned_transition.record == evaluation.record
    assert plan.event_insert.event == evaluation.event
    assert plan.accepted_work_item_cas is not None
    assert plan.accepted_work_item_cas.resulting_record == evaluation.record
    assert repr(plan) == "<_TransitionWritePlan planned_not_committed>"
    assert "wi-1" not in repr(plan)
    assert "transition-event" not in repr(plan)
    assert not hasattr(plan, "to_dict")
    assert not hasattr(plan, "canonical_json")


def test_write_plan_for_domain_rejection_has_no_current_state_cas() -> None:
    source, evaluation = _domain_rejected_evaluation()

    plan = write_contracts._transition_write_plan(
        evaluation,
        source_record=source,
        event_sequence=2,
        transaction_timestamp=CANONICAL_TIMESTAMP,
    )

    assert plan.planned_transition.replayed is False
    assert plan.planned_transition.event == evaluation.event
    assert plan.planned_transition.record == source
    assert plan.event_insert.event == evaluation.event
    assert plan.accepted_work_item_cas is None


def test_write_plan_direct_construction_reconstructs_nested_values() -> None:
    _source, _evaluation, event_insert, cas, planned = _accepted_value_parts()

    plan = write_contracts._TransitionWritePlan(
        planned_transition=planned,
        event_insert=event_insert,
        accepted_work_item_cas=cas,
    )

    assert plan.planned_transition == planned
    assert plan.planned_transition is not planned
    assert plan.event_insert == event_insert
    assert plan.event_insert is not event_insert
    assert plan.accepted_work_item_cas == cas
    assert plan.accepted_work_item_cas is not cas

    rejected_source, rejected_evaluation = _domain_rejected_evaluation()
    rejected_event_insert = write_contracts._transition_event_insert_values(
        rejected_evaluation,
        2,
        CANONICAL_TIMESTAMP,
    )
    assert rejected_evaluation.event is not None
    rejected_planned = CommittedTransition(
        record=rejected_source,
        event=rejected_evaluation.event,
        replayed=False,
    )

    rejected_plan = write_contracts._TransitionWritePlan(
        planned_transition=rejected_planned,
        event_insert=rejected_event_insert,
        accepted_work_item_cas=None,
    )

    assert rejected_plan.planned_transition == rejected_planned
    assert rejected_plan.event_insert == rejected_event_insert
    assert rejected_plan.accepted_work_item_cas is None


def test_write_plan_direct_construction_rejects_accepted_cross_inconsistency() -> None:
    source, evaluation, event_insert, cas, planned = _accepted_value_parts()

    mismatched_timestamp_cas = write_contracts._accepted_work_item_cas_values(
        source,
        evaluation.record,
        "2026-07-14T00:00:04Z",
    )
    with pytest.raises(SQLiteMutationStoreError) as timestamp:
        write_contracts._TransitionWritePlan(
            planned_transition=planned,
            event_insert=event_insert,
            accepted_work_item_cas=mismatched_timestamp_cas,
        )
    _assert_mutation_error(timestamp, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    mismatched_result = replace(evaluation.record, state=WorkItemState.BLOCKED)
    result_cas = write_contracts._accepted_work_item_cas_values(source, mismatched_result, CANONICAL_TIMESTAMP)
    with pytest.raises(SQLiteMutationStoreError) as result:
        write_contracts._TransitionWritePlan(
            planned_transition=planned,
            event_insert=event_insert,
            accepted_work_item_cas=result_cas,
        )
    _assert_mutation_error(result, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    source_version = replace(source, version=source.version + 1)
    source_version_result = replace(evaluation.record, version=evaluation.record.version + 1)
    source_version_cas = write_contracts._accepted_work_item_cas_values(
        source_version,
        source_version_result,
        CANONICAL_TIMESTAMP,
    )
    with pytest.raises(SQLiteMutationStoreError) as source_mismatch:
        write_contracts._TransitionWritePlan(
            planned_transition=planned,
            event_insert=event_insert,
            accepted_work_item_cas=source_version_cas,
        )
    _assert_mutation_error(source_mismatch, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    with pytest.raises(SQLiteMutationStoreError) as missing_cas:
        write_contracts._TransitionWritePlan(
            planned_transition=planned,
            event_insert=event_insert,
            accepted_work_item_cas=None,
        )
    _assert_mutation_error(missing_cas, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def test_write_plan_direct_construction_rejects_rejected_and_planned_mismatches() -> None:
    _source, evaluation, event_insert, cas, planned = _accepted_value_parts()
    rejected_source, rejected_evaluation = _domain_rejected_evaluation()
    rejected_event_insert = write_contracts._transition_event_insert_values(
        rejected_evaluation,
        2,
        CANONICAL_TIMESTAMP,
    )
    assert rejected_evaluation.event is not None
    rejected_planned = CommittedTransition(
        record=rejected_source,
        event=rejected_evaluation.event,
        replayed=False,
    )

    with pytest.raises(SQLiteMutationStoreError) as rejected_with_cas:
        write_contracts._TransitionWritePlan(
            planned_transition=rejected_planned,
            event_insert=rejected_event_insert,
            accepted_work_item_cas=cas,
        )
    _assert_mutation_error(rejected_with_cas, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    with pytest.raises(SQLiteMutationStoreError) as event_mismatch:
        write_contracts._TransitionWritePlan(
            planned_transition=rejected_planned,
            event_insert=event_insert,
            accepted_work_item_cas=None,
        )
    _assert_mutation_error(event_mismatch, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    assert evaluation.event is not None
    replay_mismatch = CommittedTransition(
        record=replace(evaluation.record, backlog_id="backlog-other"),
        event=evaluation.event,
        replayed=False,
    )
    with pytest.raises(SQLiteMutationStoreError) as replay:
        write_contracts._TransitionWritePlan(
            planned_transition=replay_mismatch,
            event_insert=event_insert,
            accepted_work_item_cas=cas,
        )
    _assert_mutation_error(replay, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    replayed = CommittedTransition(record=evaluation.record, event=evaluation.event, replayed=True)
    with pytest.raises(SQLiteMutationStoreError) as replayed_error:
        write_contracts._TransitionWritePlan(
            planned_transition=replayed,
            event_insert=event_insert,
            accepted_work_item_cas=cas,
        )
    _assert_mutation_error(replayed_error, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def test_write_plan_rejects_forged_exact_nested_private_shells(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _source, _evaluation, event_insert, cas, planned = _accepted_value_parts()
    forged_event_insert = object.__new__(write_contracts._TransitionEventInsertValues)

    with pytest.raises(SQLiteMutationStoreError) as event_shell:
        write_contracts._TransitionWritePlan(
            planned_transition=planned,
            event_insert=forged_event_insert,
            accepted_work_item_cas=cas,
        )
    _assert_mutation_error(event_shell, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE, capsys)

    forged_cas = object.__new__(write_contracts._AcceptedWorkItemCasValues)
    with pytest.raises(SQLiteMutationStoreError) as cas_shell:
        write_contracts._TransitionWritePlan(
            planned_transition=planned,
            event_insert=event_insert,
            accepted_work_item_cas=forged_cas,
        )
    _assert_mutation_error(cas_shell, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE, capsys)


def test_write_plan_rejects_pre_apply_invalid_and_replay_conflict_shapes() -> None:
    source, pre_apply_invalid = _pre_apply_invalid_evaluation()

    with pytest.raises(SQLiteMutationStoreError) as invalid:
        write_contracts._transition_write_plan(
            pre_apply_invalid,
            source_record=source,
            event_sequence=0,
            transaction_timestamp=CANONICAL_TIMESTAMP,
        )
    _assert_mutation_error(invalid, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)

    with pytest.raises(SQLiteMutationStoreError) as wrong_shape:
        write_contracts._transition_write_plan(
            object(),  # type: ignore[arg-type]
            source_record=source,
            event_sequence=0,
            transaction_timestamp=CANONICAL_TIMESTAMP,
        )
    _assert_mutation_error(wrong_shape, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def test_write_plan_rejects_source_record_that_does_not_match_event_source() -> None:
    source, evaluation = _accepted_evaluation()

    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        write_contracts._transition_write_plan(
            evaluation,
            source_record=replace(source, version=source.version + 1),
            event_sequence=0,
            transaction_timestamp=CANONICAL_TIMESTAMP,
        )

    _assert_mutation_error(exc_info, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def test_event_builder_ignores_benign_shadowed_serializers_and_digests() -> None:
    _source, evaluation = _accepted_evaluation()
    assert evaluation.event is not None
    assert hasattr(evaluation.event, "__dict__")
    assert hasattr(evaluation.record, "__dict__")
    calls: list[str] = []
    for model in (evaluation.event, evaluation.record):
        for name in ("to_dict", "canonical_json", "canonical_digest", "compute_digest", "compute_event_ref"):
            _shadow_callable(model, name, calls, result=PRIVATE_SENTINEL)

    values = write_contracts._transition_event_insert_values(evaluation, 0, CANONICAL_TIMESTAMP)

    assert calls == []
    assert values.event == evaluation.event
    assert values.event is not evaluation.event
    assert values.replay_record == evaluation.record
    assert values.replay_record is not evaluation.record
    assert values.parameters == _expected_event_parameters(values.event, values.replay_record, 0)


def test_event_builder_ignores_hostile_shadowed_serializers_and_redacts_failures(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _source, evaluation = _accepted_evaluation()
    assert evaluation.event is not None
    calls: list[str] = []
    for model in (evaluation.event, evaluation.record):
        for name in ("to_dict", "canonical_json", "canonical_digest", "compute_digest", "compute_event_ref"):
            _shadow_callable(model, name, calls, hostile=True)

    values = write_contracts._transition_event_insert_values(evaluation, 0, CANONICAL_TIMESTAMP)

    assert calls == []
    assert values.parameters == _expected_event_parameters(values.event, values.replay_record, 0)
    safe_event_json = values.event.canonical_json()
    safe_record_json = values.replay_record.canonical_json()

    bad_event = _forged_from_model(evaluation.event, event_ref=PRIVATE_SENTINEL)
    bad_event_calls: list[str] = []
    for name in ("to_dict", "canonical_json", "canonical_digest", "compute_event_ref"):
        _shadow_callable(bad_event, name, bad_event_calls, result=safe_event_json)
    bad_evaluation = _forged_from_model(evaluation, event=bad_event)
    with pytest.raises(SQLiteMutationStoreError) as event_error:
        write_contracts._transition_event_insert_values(bad_evaluation, 0, CANONICAL_TIMESTAMP)  # type: ignore[arg-type]
    _assert_mutation_error(event_error, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE, capsys)
    assert bad_event_calls == []

    bad_record = _forged_from_model(evaluation.record, work_item_id=PRIVATE_SENTINEL)
    bad_record_calls: list[str] = []
    for name in ("to_dict", "canonical_json", "canonical_digest", "compute_digest"):
        _shadow_callable(bad_record, name, bad_record_calls, result=safe_record_json)
    bad_record_evaluation = _forged_from_model(evaluation, record=bad_record)
    with pytest.raises(SQLiteMutationStoreError) as record_error:
        write_contracts._transition_event_insert_values(bad_record_evaluation, 0, CANONICAL_TIMESTAMP)  # type: ignore[arg-type]
    _assert_mutation_error(record_error, SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE, capsys)
    assert bad_record_calls == []


def test_commit_resolution_state_vocabulary_and_lifecycle_paths_are_closed() -> None:
    state = mutation_contracts._MutationCommitResolutionState

    assert tuple(member.value for member in state) == (
        "new",
        "transaction_active",
        "fenced",
        "capability_active",
        "planned_outcome",
        "writes_performed",
        "capability_invalidated",
        "commit_attempt_started",
        "commit_succeeded",
        "commit_outcome_unknown",
        "rollback_resolved",
        "closed",
    )
    assert mutation_contracts._MUTATION_COMMIT_RESOLUTION_REPLAY_CONFLICT_ROLLBACK_PATH == (
        state.TRANSACTION_ACTIVE,
        state.FENCED,
        state.CAPABILITY_ACTIVE,
        state.CAPABILITY_INVALIDATED,
        state.ROLLBACK_RESOLVED,
        state.CLOSED,
    )
    assert mutation_contracts._MUTATION_COMMIT_RESOLUTION_FRESH_SUCCESS_PATH[-3:] == (
        state.COMMIT_ATTEMPT_STARTED,
        state.COMMIT_SUCCEEDED,
        state.CLOSED,
    )
    assert mutation_contracts._MUTATION_COMMIT_RESOLUTION_FRESH_UNCERTAIN_PATH[-3:] == (
        state.COMMIT_ATTEMPT_STARTED,
        state.COMMIT_OUTCOME_UNKNOWN,
        state.CLOSED,
    )
    assert mutation_contracts._MUTATION_COMMIT_RESOLUTION_PLANNED_OUTCOME_FAILURE_PATH == (
        state.TRANSACTION_ACTIVE,
        state.FENCED,
        state.CAPABILITY_ACTIVE,
        state.PLANNED_OUTCOME,
        state.CAPABILITY_INVALIDATED,
        state.ROLLBACK_RESOLVED,
        state.CLOSED,
    )
    assert mutation_contracts._MUTATION_COMMIT_RESOLUTION_POST_WRITE_PRECOMMIT_FAILURE_PATH == (
        state.TRANSACTION_ACTIVE,
        state.FENCED,
        state.CAPABILITY_ACTIVE,
        state.PLANNED_OUTCOME,
        state.WRITES_PERFORMED,
        state.CAPABILITY_INVALIDATED,
        state.ROLLBACK_RESOLVED,
        state.CLOSED,
    )
    assert not hasattr(mutation_contracts, "_MUTATION_COMMIT_RESOLUTION_PRECOMMIT_FAILURE_PATH")
    assert (state.COMMIT_ATTEMPT_STARTED, state.COMMIT_OUTCOME_UNKNOWN) in (
        mutation_contracts._MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS
    )
    assert (state.COMMIT_SUCCEEDED, state.COMMIT_OUTCOME_UNKNOWN) not in (
        mutation_contracts._MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS
    )
    assert not hasattr(write_contracts, "_MutationCommitResolutionState")
    assert not hasattr(write_contracts, "_MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS")


def test_commit_resolution_paths_are_composed_only_of_allowed_edges() -> None:
    state = mutation_contracts._MutationCommitResolutionState
    allowed = mutation_contracts._MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS
    path_names = tuple(
        sorted(
            name
            for name in vars(mutation_contracts)
            if name.startswith("_MUTATION_COMMIT_RESOLUTION_") and name.endswith("_PATH")
        )
    )

    assert path_names == (
        "_MUTATION_COMMIT_RESOLUTION_FRESH_SUCCESS_PATH",
        "_MUTATION_COMMIT_RESOLUTION_FRESH_UNCERTAIN_PATH",
        "_MUTATION_COMMIT_RESOLUTION_PLANNED_OUTCOME_FAILURE_PATH",
        "_MUTATION_COMMIT_RESOLUTION_POST_WRITE_PRECOMMIT_FAILURE_PATH",
        "_MUTATION_COMMIT_RESOLUTION_REPLAY_CONFLICT_ROLLBACK_PATH",
    )
    for name in path_names:
        path = getattr(mutation_contracts, name)
        for current, next_state in zip(path, path[1:]):
            assert (current, next_state) in allowed, name

    assert (state.PLANNED_OUTCOME, state.CAPABILITY_INVALIDATED) in allowed
    assert (state.CAPABILITY_ACTIVE, state.ROLLBACK_RESOLVED) not in allowed
    assert (state.PLANNED_OUTCOME, state.ROLLBACK_RESOLVED) not in allowed
    assert (state.WRITES_PERFORMED, state.ROLLBACK_RESOLVED) not in allowed
    assert (state.TRANSACTION_ACTIVE, state.CAPABILITY_INVALIDATED) not in allowed
    assert (state.FENCED, state.ROLLBACK_RESOLVED) not in allowed
    for member in state:
        assert (member, member) not in allowed
    assert all(current is not state.CLOSED for current, _next_state in allowed)


def test_commit_resolution_graph_scope_remains_static_and_excludes_cleanup_failures() -> None:
    state = mutation_contracts._MutationCommitResolutionState
    scope = mutation_contracts._MUTATION_COMMIT_RESOLUTION_GRAPH_SCOPE
    source = WRITE_CONTRACTS_PATH.read_text()
    mutation_source = MUTATION_CONTRACTS_PATH.read_text()
    transaction_source = TRANSACTION_MODULE_PATH.read_text()
    doc = (ROOT / ".docs/b3c4a-transition-write-and-commit-contracts.md").read_text()
    normalized_doc = " ".join(doc.split())

    assert "stale_writer_pre_capability_outside_graph" in scope
    assert "other_pre_capability_failures_outside_graph" in scope
    assert "pre_capability_exits_cannot_claim_capability_states" in scope
    assert "capability_invalidation_failure_cannot_claim_capability_invalidated" in scope
    assert "rollback_failure_cannot_claim_rollback_resolved" in scope
    assert "close_failure_cannot_force_closed_milestone" in scope
    assert "no_direct_rollback_edge_bypasses_capability_invalidation" in scope
    assert "single_mutation_runtime_enforcement" in scope
    assert (state.CAPABILITY_ACTIVE, state.ROLLBACK_RESOLVED) not in (
        mutation_contracts._MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS
    )
    assert "Stale writer is the currently proved" in normalized_doc
    assert "pre-capability conflict exit and remains outside the graph" in normalized_doc
    assert "other failures before capability" in normalized_doc
    assert "cannot fabricate `capability_active`" in normalized_doc
    assert "capability invalidation must not claim `capability_invalidated`" in normalized_doc
    assert "rollback must not claim `rollback_resolved`" in normalized_doc
    assert "must not force a later graph milestone" in normalized_doc
    assert "do not retroactively establish missing successful graph milestones" in normalized_doc
    assert "must not fabricate transitions on cleanup failure" in normalized_doc
    assert "class _MutationCommitResolutionState" not in source
    assert "_MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS" not in source
    assert "class _MutationCommitResolutionState" in mutation_source
    assert mutation_source.count("class _MutationCommitResolutionState") == 1
    assert mutation_source.count("_MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS") == 1
    assert mutation_source.count("_MUTATION_COMMIT_RESOLUTION_GRAPH_SCOPE") == 1
    assert "_MutationCommitResolutionState" in transaction_source
    assert "_run_atomic_transition_apply" in transaction_source
    assert "apply_transition" not in transaction_source


def test_error_retry_public_and_b4_contract_matrices_pin_future_b3c4b_and_b3c4c() -> None:
    matrix = write_contracts._B3C4A_SQLITE_CLASSIFICATION_MATRIX
    retry = write_contracts._B3C4A_RETRY_AFTER_COMMIT_UNCERTAINTY_CONTRACT
    proof = write_contracts._B3C4B_REQUIRED_PROOF_MATRIX
    public = write_contracts._B3C4C_PUBLIC_INTEGRATION_BOUNDARY
    b4 = write_contracts._B4_SEPARATION_CONTRACT

    assert ("commit", "any_exception_after_attempt_begins", "commit_outcome_unknown") in matrix
    assert ("event_insert", "event_ref_collision_after_miss", "database_integrity_failure") in matrix
    assert ("event_insert", "event_sequence_collision_after_miss", "database_integrity_failure") in matrix
    assert ("event_insert", "idempotency_collision_after_miss", "database_integrity_failure") in matrix
    assert ("accepted_cas", "rowcount_not_one", "database_integrity_failure") in matrix
    assert ("rollback_before_commit_attempt", "any_rollback_failure", "mutation_failed") in matrix
    assert ("close_after_commit_success", "close_failure", "committed_success") in matrix
    assert "no_hidden_controller_retry" in retry
    assert "same_or_new_valid_writer_session" in retry
    assert "exact_replay_skips_timestamp_context_evaluator_sequence_and_writes" in retry
    assert "sequence_0" in proof
    assert "signed_max_overflow" in proof
    assert "no_partial_event_or_current_state_row" in proof
    assert "process_thread_fork_capability_behavior" in proof
    assert "public_apply_delegates_to_one_private_atomic_entry" in public
    assert "apply_global_stop_update_unavailable_until_b4c" in public
    assert "apply_global_stop_update_unavailable_until_b4" not in public
    assert "no_global_stop_event_insert" in b4
    assert "b4b_private_global_stop_persistence_exists_b4c_public_delegation_future" in b4
    assert "b4_remains_future_global_stop_persistence_tranche" not in b4


def test_new_module_has_no_runtime_io_or_public_exports() -> None:
    source = WRITE_CONTRACTS_PATH.read_text()
    tree = ast.parse(source)

    assert write_contracts.__all__ == ()
    assert sorted(name for name in vars(write_contracts) if not name.startswith("_")) == []
    assert "sqlite3" not in source
    assert "StateStore" not in source
    assert "global_stop_events" not in source
    assert "INSERT INTO global_stop_events" not in source
    assert "UPDATE global_stop_current" not in source
    assert "BEGIN IMMEDIATE" not in source
    assert "INSERT OR REPLACE" not in source
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name != "sqlite3" for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "sqlite3"
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                assert func.attr not in {
                    "execute",
                    "executemany",
                    "executescript",
                    "cursor",
                    "fetchone",
                    "fetchmany",
                    "fetchall",
                    "commit",
                    "rollback",
                }


def test_b3c4a_is_consumed_only_by_private_b3c4b_runtime_and_public_apply_remains_unavailable() -> None:
    source_files = [path for path in PACKAGE_DIR.glob("*.py") if path.name != "sqlite_transition_write_contracts.py"]
    for path in source_files:
        if path.name == "sqlite_transition_transaction.py":
            continue
        assert "sqlite_transition_write_contracts" not in path.read_text(), path

    transaction_source = TRANSACTION_MODULE_PATH.read_text()
    assert "sqlite_transition_write_contracts" in transaction_source
    assert "_read_transition_event_max_sequence" in transaction_source
    assert "next_transition_event_sequence" in transaction_source
    assert 'connection.execute("COMMIT")' in transaction_source
    assert "_run_atomic_transition_apply" in transaction_source
    assert "apply_transition" not in transaction_source

    writer_source = WRITER_SESSION_PATH.read_text()
    apply_transition_source = inspect.getsource(writer_session_module._SQLiteWriterSession.apply_transition)
    assert "sqlite_transition_write_contracts" not in writer_source
    assert writer_source.count("_run_atomic_transition_apply") == 2
    assert WriterSessionFailureReason.WRITER_SESSION_MUTATION_UNAVAILABLE.name in apply_transition_source
    assert "transition_command" in apply_transition_source
    assert "TransitionApplyPreflightError" in apply_transition_source
    assert "_acquire_mutation_lease" not in apply_transition_source

    assert "sqlite_transition_write_contracts" not in PACKAGE_EXPORT_PATH.read_text()
    assert not list(MIGRATION_DIR.glob("0002*"))


def test_docs_pin_b3c4a_boundary_and_follow_on_tranches() -> None:
    doc_paths = (
        ROOT / ".docs/b3c4a-transition-write-and-commit-contracts.md",
        ROOT / "AGENTS.md",
        ROOT / "README.md",
        ROOT / ".docs/architecture.md",
        ROOT / ".docs/b3-transition-persistence-contract.md",
        ROOT / ".docs/b3c0a-transition-authority-and-order.md",
        ROOT / ".docs/b3c0b-transition-event-replay-contracts.md",
        ROOT / ".docs/b3c1-prerequisite-contract.md",
        ROOT / ".docs/b3c1b-rollback-only-writer-fencing.md",
        ROOT / ".docs/b3c2-transition-event-readers.md",
        ROOT / ".docs/b3c3-prerequisite-contract.md",
        ROOT / ".docs/b3c3-rollback-only-transition-dry-run.md",
        ROOT / ".docs/durable-state-model.md",
        ROOT / ".docs/p1-1-transition-event-algebra.md",
        ROOT / ".docs/sqlite-schema-v1.md",
        ROOT / ".docs/sqlite-state-backend-adr.md",
        ROOT / ".docs/sqlite-operations-and-recovery.md",
        ROOT / ".docs/sqlite-threat-model.md",
        ROOT / ".docs/writer-session-authority.md",
    )
    for path in doc_paths:
        assert path.exists(), path
        assert "B3c4a" in path.read_text(), path

    contract_doc = doc_paths[0].read_text()
    for phrase in (
        "pure/static",
        "B3c4b",
        "B3c4c",
        "commit_outcome_unknown",
        "no migration 0002",
        "B4c remains",
        "not admission",
        "not authorization",
    ):
        assert phrase in contract_doc
