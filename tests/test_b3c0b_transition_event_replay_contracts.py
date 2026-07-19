from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import sqlite3
import traceback

import pytest

import ge_nwp_coordinator
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
    TRANSITION_EVENT_ROW_KEYS,
    TransitionEventRecordEnvelope,
    match_transition_event_idempotency,
    next_transition_event_sequence,
    transition_event_record_envelope_from_row,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_transition_event_contracts import (
    _B3C0B_TRANSITION_EVENT_QUERY_SPECS,
    _TRANSITION_EVENT_IDEMPOTENCY_LOOKUP_SELECT,
    _TRANSITION_EVENT_MAX_SEQUENCE_SELECT,
    _TransitionEventIdempotencyQuerySpec,
    _TransitionEventMaxSequenceQuerySpec,
)
from ge_nwp_coordinator.state_machine import (
    WORK_ITEM_STATE_SCHEMA_ID,
    DependencyDecision,
    TransitionCommand,
    TransitionContext,
    TransitionEvent,
    WorkItemRecord,
    WorkItemState,
    transition,
)
from ge_nwp_coordinator.state_store import CommittedTransition, StateStore, TransitionConflict, WriterSession


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
PERSISTENCE_PATH = PACKAGE_DIR / "persistence_contracts.py"
EVENT_CONTRACTS_PATH = PACKAGE_DIR / "sqlite_transition_event_contracts.py"
MIGRATION_PATH = PACKAGE_DIR / "sqlite_migrations/0001_initial.sql"
EXPECTED_MIGRATION_0001_CHECKSUM = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"
CANONICAL_TIMESTAMP = "2026-07-14T00:00:03Z"
PRIVATE_EVENT_SENTINEL = "PRIVATE-EVENT-ROW-MATERIAL-DO-NOT-LEAK-314159"

EXPECTED_TRANSITION_EVENT_ROW_COLUMNS = (
    "event_ref",
    "event_sequence",
    "work_item_id",
    "lease_id",
    "idempotency_key",
    "command_digest",
    "source_state",
    "source_version",
    "resulting_state",
    "resulting_version",
    "outcome",
    "reason",
    "evidence_refs_json",
    "budget_cost_delta",
    "attempt_count_delta",
    "repair_count_delta",
    "lease_identity_decision_ref",
    "authorization_decision_ref",
    "dependency_decision_ref",
    "global_stop_ref",
    "global_stop_version",
    "schema_id",
    "event_json",
    "event_digest",
    "replay_work_item_json",
    "replay_work_item_digest",
    "created_at",
)


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
    if authorized:
        return AuthorizationDecision(
            decision_ref="authz-lease-a2-p1",
            lease_ref=identity.lease_ref,
            lease_identity_decision_ref=identity.decision_ref,
            lease_identity_valid=identity.identity_valid,
            authorization_model=AuthorizationModel.OPERATOR_POLICY,
            authorized=True,
            executable=False,
            reason="accepted",
        )
    return AuthorizationDecision(
        decision_ref="authz-lease-a2-p1",
        lease_ref=identity.lease_ref,
        lease_identity_decision_ref=identity.decision_ref,
        lease_identity_valid=identity.identity_valid,
        authorization_model=AuthorizationModel.UNSUPPORTED,
        authorized=False,
        executable=False,
        reason="unsupported_authorization_model",
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
    evidence_refs: tuple[str, ...] = (),
    budget_cost: int = 0,
) -> TransitionCommand:
    return TransitionCommand.create(
        work_item_id=record.work_item_id,
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


def _accepted_event_and_replay(
    *,
    evidence_refs: tuple[str, ...] = (),
    budget_cost: int = 0,
    budget_limit: int = 0,
) -> tuple[TransitionCommand, TransitionEvent, WorkItemRecord]:
    record = _record(budget_limit=budget_limit)
    context = _context()
    command = _command(record, context, evidence_refs=evidence_refs, budget_cost=budget_cost)
    result = transition(record, command, context)
    assert result.event is not None
    return command, result.event, result.record


def _domain_rejected_event_and_replay() -> tuple[TransitionCommand, TransitionEvent, WorkItemRecord]:
    record = _record()
    context = _context(authorized=False)
    command = _command(record, context)
    result = transition(record, command, context)
    assert result.event is not None
    assert result.event.reason == "lease_not_authorized"
    return command, result.event, result.record


def _row(
    event: TransitionEvent,
    replay_record: WorkItemRecord,
    *,
    event_sequence: int = 0,
    created_at: str | None = None,
) -> dict[str, object]:
    row = {
        "event_ref": event.event_ref,
        "event_sequence": event_sequence,
        "work_item_id": event.work_item_id,
        "lease_id": event.lease_id,
        "idempotency_key": event.idempotency_key,
        "command_digest": event.command_digest,
        "source_state": event.source_state.value,
        "source_version": event.source_version,
        "resulting_state": event.resulting_state.value,
        "resulting_version": event.resulting_version,
        "outcome": event.outcome.value,
        "reason": event.reason,
        "evidence_refs_json": canonical_json_bytes(list(event.evidence_refs)).decode("utf-8"),
        "budget_cost_delta": event.budget_cost_delta,
        "attempt_count_delta": event.attempt_count_delta,
        "repair_count_delta": event.repair_count_delta,
        "lease_identity_decision_ref": event.lease_identity_decision_ref,
        "authorization_decision_ref": event.authorization_decision_ref,
        "dependency_decision_ref": event.dependency_decision_ref,
        "global_stop_ref": event.global_stop_ref,
        "global_stop_version": event.global_stop_version,
        "schema_id": event.schema_id,
        "event_json": event.canonical_json(),
        "event_digest": event.canonical_digest(),
        "replay_work_item_json": replay_record.canonical_json(),
        "replay_work_item_digest": replay_record.canonical_digest(),
        "created_at": event.lease_runtime.evaluated_at if created_at is None else created_at,
    }
    assert tuple(row) == TRANSITION_EVENT_ROW_COLUMNS
    return row


def _row_for_replay(replay_record: WorkItemRecord, event: TransitionEvent) -> dict[str, object]:
    row = _row(event, replay_record)
    row["replay_work_item_json"] = replay_record.canonical_json()
    row["replay_work_item_digest"] = replay_record.canonical_digest()
    return row


def _assert_integrity_failure(call: object) -> SQLiteMutationStoreError:
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        call()  # type: ignore[operator]
    exc = exc_info.value
    assert exc.error_class == "database_integrity_failure"
    assert str(exc) == "database_integrity_failure"
    assert exc.args == ("database_integrity_failure",)
    assert exc.internal_detail is None
    return exc


def _render_exception_graph(exc: BaseException) -> str:
    rendered: list[str] = []
    pending = [exc]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        rendered.extend(
            (
                type(current).__name__,
                str(current),
                repr(current),
                repr(current.args),
                repr(getattr(current, "internal_detail", None)),
                repr(getattr(current, "__notes__", None)),
                "".join(traceback.format_exception(type(current), current, current.__traceback__)),
            )
        )
        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)
    return "\n".join(rendered)


def _columns_from_migration(table_name: str) -> tuple[str, ...]:
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(MIGRATION_PATH.read_text(encoding="utf-8"))
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return tuple(row[1] for row in rows)
    finally:
        connection.close()


def _forged_transition_event_envelope(
    *,
    event: object,
    replay_record: object,
    event_sequence: int = 0,
    created_at: str = CANONICAL_TIMESTAMP,
) -> TransitionEventRecordEnvelope:
    envelope = object.__new__(TransitionEventRecordEnvelope)
    object.__setattr__(envelope, "event_sequence", event_sequence)
    object.__setattr__(envelope, "event", event)
    object.__setattr__(envelope, "replay_record", replay_record)
    object.__setattr__(envelope, "created_at", created_at)
    assert type(envelope) is TransitionEventRecordEnvelope
    return envelope


def test_valid_accepted_transition_event_row_reconstructs_envelope() -> None:
    command, event, replay_record = _accepted_event_and_replay()
    envelope = transition_event_record_envelope_from_row(_row(event, replay_record, event_sequence=4))

    assert isinstance(envelope, TransitionEventRecordEnvelope)
    assert envelope.event_sequence == 4
    assert envelope.event == event
    assert envelope.replay_record == replay_record
    assert envelope.created_at == event.lease_runtime.evaluated_at
    assert command.canonical_command_digest == event.command_digest


def test_valid_domain_rejected_transition_event_row_reconstructs_unchanged_replay() -> None:
    _command_value, event, replay_record = _domain_rejected_event_and_replay()
    envelope = transition_event_record_envelope_from_row(_row(event, replay_record, event_sequence=5))

    assert envelope.event.outcome.value == "domain_rejected"
    assert envelope.event.reason == "lease_not_authorized"
    assert envelope.replay_record.state is WorkItemState.PROPOSED
    assert envelope.replay_record.version == 0


def test_transition_event_row_columns_are_exact_schema_0001_order_and_key_source() -> None:
    assert TRANSITION_EVENT_ROW_COLUMNS == EXPECTED_TRANSITION_EVENT_ROW_COLUMNS
    assert TRANSITION_EVENT_ROW_KEYS == frozenset(TRANSITION_EVENT_ROW_COLUMNS)
    assert len(TRANSITION_EVENT_ROW_COLUMNS) == len(set(TRANSITION_EVENT_ROW_COLUMNS))
    assert _columns_from_migration("transition_events") == TRANSITION_EVENT_ROW_COLUMNS
    assert hashlib.sha256(MIGRATION_PATH.read_bytes()).hexdigest() == EXPECTED_MIGRATION_0001_CHECKSUM


def test_transition_event_row_rejects_unknown_missing_and_invalid_sequence_shape() -> None:
    _command_value, event, replay_record = _accepted_event_and_replay()
    row = _row(event, replay_record)

    _assert_integrity_failure(lambda: transition_event_record_envelope_from_row({key: value for key, value in row.items() if key != "created_at"}))
    _assert_integrity_failure(lambda: transition_event_record_envelope_from_row({**row, "extra": "not-allowed"}))
    _assert_integrity_failure(lambda: transition_event_record_envelope_from_row({**row, "event_sequence": True}))
    _assert_integrity_failure(lambda: transition_event_record_envelope_from_row({**row, "event_sequence": -1}))


@pytest.mark.parametrize(
    "mutate",
    (
        lambda row: {**row, "event_ref": "transition-event-other"},
        lambda row: {**row, "work_item_id": "wi-2"},
        lambda row: {**row, "lease_id": "lease-other"},
        lambda row: {**row, "idempotency_key": "transition-k2"},
        lambda row: {**row, "command_digest": "b" * 64},
        lambda row: {**row, "source_state": "ready"},
        lambda row: {**row, "source_version": 7},
        lambda row: {**row, "resulting_state": "ready"},
        lambda row: {**row, "resulting_version": 8},
        lambda row: {**row, "outcome": "domain_rejected"},
        lambda row: {**row, "reason": "invalid_predecessor"},
        lambda row: {**row, "evidence_refs_json": '["evidence-other"]'},
        lambda row: {**row, "budget_cost_delta": 1},
        lambda row: {**row, "attempt_count_delta": 1},
        lambda row: {**row, "repair_count_delta": 1},
        lambda row: {**row, "lease_identity_decision_ref": "lease-identity-other"},
        lambda row: {**row, "authorization_decision_ref": "authz-other"},
        lambda row: {**row, "dependency_decision_ref": "deps-other"},
        lambda row: {**row, "global_stop_ref": "global-stop-other"},
        lambda row: {**row, "global_stop_version": 1},
        lambda row: {**row, "schema_id": "governed-execution.nwp-transition-event.v2"},
    ),
)
def test_every_indexed_event_column_must_match_reconstructed_event(mutate: object) -> None:
    _command_value, event, replay_record = _accepted_event_and_replay()
    malformed = mutate(_row(event, replay_record))  # type: ignore[operator]

    _assert_integrity_failure(lambda: transition_event_record_envelope_from_row(malformed))


def test_event_json_digest_and_evidence_refs_must_be_exact_canonical_values() -> None:
    _command_value, event, replay_record = _accepted_event_and_replay()
    row = _row(event, replay_record)

    _assert_integrity_failure(lambda: transition_event_record_envelope_from_row({**row, "event_json": "not-json"}))
    _assert_integrity_failure(
        lambda: transition_event_record_envelope_from_row(
            {**row, "event_json": json.dumps(event.to_dict(), indent=2, sort_keys=True)}
        )
    )
    _assert_integrity_failure(lambda: transition_event_record_envelope_from_row({**row, "event_digest": "c" * 64}))
    _assert_integrity_failure(lambda: transition_event_record_envelope_from_row({**row, "evidence_refs_json": "[ ]"}))


@pytest.mark.parametrize(
    "replay_record",
    (
        _record(work_item_id="wi-2", state=WorkItemState.LEASE_ADMITTED, version=1),
        _record(lease_id="lease-other", state=WorkItemState.LEASE_ADMITTED, version=1),
        _record(state=WorkItemState.PROPOSED, version=1),
        _record(state=WorkItemState.LEASE_ADMITTED, version=9),
    ),
)
def test_replay_record_must_match_event_work_item_lease_state_and_version(replay_record: WorkItemRecord) -> None:
    _command_value, event, _valid_replay = _accepted_event_and_replay()

    _assert_integrity_failure(
        lambda: transition_event_record_envelope_from_row(_row_for_replay(replay_record, event))
    )


def test_replay_json_and_digest_must_be_exact_canonical_values() -> None:
    _command_value, event, replay_record = _accepted_event_and_replay()
    row = _row(event, replay_record)

    _assert_integrity_failure(lambda: transition_event_record_envelope_from_row({**row, "replay_work_item_json": "not-json"}))
    _assert_integrity_failure(
        lambda: transition_event_record_envelope_from_row(
            {**row, "replay_work_item_json": json.dumps(replay_record.to_dict(), indent=2, sort_keys=True)}
        )
    )
    _assert_integrity_failure(
        lambda: transition_event_record_envelope_from_row({**row, "replay_work_item_digest": "d" * 64})
    )


def test_created_at_must_equal_event_runtime_timestamp_and_sequence_is_not_identity() -> None:
    _command_value, event, replay_record = _accepted_event_and_replay()
    first = transition_event_record_envelope_from_row(_row(event, replay_record, event_sequence=0))
    second = transition_event_record_envelope_from_row(_row(event, replay_record, event_sequence=22))

    assert second.event_sequence == 22
    assert first.event == second.event
    assert first.event.event_ref == second.event.event_ref
    assert first.event.canonical_digest() == second.event.canonical_digest()
    assert first.replay_record == second.replay_record
    assert first.replay_record.canonical_digest() == second.replay_record.canonical_digest()

    _assert_integrity_failure(
        lambda: transition_event_record_envelope_from_row(
            _row(event, replay_record, created_at="2026-07-14T00:00:04Z")
        )
    )
    _assert_integrity_failure(
        lambda: transition_event_record_envelope_from_row(
            _row(event, replay_record, created_at="2026-07-14T00:00:03+00:00")
        )
    )


def test_bounded_zero_budget_slice_is_enforced_for_event_and_replay() -> None:
    _command_value, event, replay_record = _accepted_event_and_replay()
    consumed = WorkItemRecord.from_dict({**replay_record.to_dict(), "budget_consumed": 1})
    limited = WorkItemRecord.from_dict({**replay_record.to_dict(), "budget_limit": 1})
    _assert_integrity_failure(lambda: transition_event_record_envelope_from_row(_row_for_replay(consumed, event)))
    _assert_integrity_failure(lambda: transition_event_record_envelope_from_row(_row_for_replay(limited, event)))

    _budget_command, budget_event, budget_replay = _accepted_event_and_replay(budget_cost=1, budget_limit=10)
    _assert_integrity_failure(lambda: transition_event_record_envelope_from_row(_row(budget_event, budget_replay)))


def test_envelope_repr_and_exception_graph_do_not_expose_event_replay_or_raw_row_material() -> None:
    _command_value, event, replay_record = _accepted_event_and_replay(evidence_refs=("private-evidence-ref",))
    envelope = transition_event_record_envelope_from_row(_row(event, replay_record))

    rendered = repr(envelope)
    for forbidden in (
        "private-evidence-ref",
        event.event_ref,
        event.command_digest,
        event.canonical_json(),
        replay_record.canonical_json(),
        "replay_record",
    ):
        assert forbidden not in rendered

    exc = _assert_integrity_failure(
        lambda: transition_event_record_envelope_from_row(
            {**_row(event, replay_record), "event_json": PRIVATE_EVENT_SENTINEL}
        )
    )
    assert exc.__cause__ is None
    assert exc.__context__ is None
    assert getattr(exc, "__notes__", None) is None
    rendered_graph = _render_exception_graph(exc)
    for forbidden in (
        PRIVATE_EVENT_SENTINEL,
        "invalid_json",
        "TransitionEvent.from_json",
        event.canonical_json(),
        replay_record.canonical_json(),
    ):
        assert forbidden not in rendered_graph


def test_transition_event_record_envelope_requires_exact_nested_base_types() -> None:
    _command_value, event, replay_record = _accepted_event_and_replay(evidence_refs=("private-evidence-ref",))

    envelope = TransitionEventRecordEnvelope(
        event_sequence=7,
        event=event,
        replay_record=replay_record,
        created_at=event.lease_runtime.evaluated_at,
    )
    assert type(envelope.event) is TransitionEvent
    assert type(envelope.replay_record) is WorkItemRecord
    assert envelope.event is event
    assert envelope.replay_record is replay_record

    class EventSubclass(TransitionEvent):
        pass

    class RecordSubclass(WorkItemRecord):
        pass

    event_subclass = EventSubclass(**event.__dict__)
    record_subclass = RecordSubclass(**replay_record.__dict__)

    event_error = _assert_integrity_failure(
        lambda: TransitionEventRecordEnvelope(
            event_sequence=7,
            event=event_subclass,
            replay_record=replay_record,
            created_at=event.lease_runtime.evaluated_at,
        )
    )
    replay_error = _assert_integrity_failure(
        lambda: TransitionEventRecordEnvelope(
            event_sequence=7,
            event=event,
            replay_record=record_subclass,
            created_at=event.lease_runtime.evaluated_at,
        )
    )

    for exc in (event_error, replay_error):
        rendered_graph = _render_exception_graph(exc)
        for forbidden in (
            "private-evidence-ref",
            event.event_ref,
            event.command_digest,
            event.canonical_json(),
            replay_record.canonical_json(),
            "EventSubclass",
            "RecordSubclass",
        ):
            assert forbidden not in rendered_graph


def test_transition_event_record_envelope_rejects_hostile_nested_subclasses_before_semantic_access() -> None:
    _command_value, event, replay_record = _accepted_event_and_replay(evidence_refs=("private-evidence-ref",))

    class HostileEvent(TransitionEvent):
        def __getattribute__(self, name: str) -> object:
            if name in {"work_item_id", "idempotency_key", "command_digest", "canonical_digest", "canonical_json"}:
                try:
                    armed = object.__getattribute__(self, "_armed")
                except AttributeError:
                    armed = False
                if armed:
                    raise AssertionError(PRIVATE_EVENT_SENTINEL)
            return super().__getattribute__(name)

    class HostileRecord(WorkItemRecord):
        def __getattribute__(self, name: str) -> object:
            if name in {"work_item_id", "lease_id", "state", "version", "canonical_digest", "canonical_json"}:
                try:
                    armed = object.__getattribute__(self, "_armed")
                except AttributeError:
                    armed = False
                if armed:
                    raise AssertionError(PRIVATE_EVENT_SENTINEL)
            return super().__getattribute__(name)

    hostile_event = HostileEvent(**event.__dict__)
    hostile_record = HostileRecord(**replay_record.__dict__)
    object.__setattr__(hostile_event, "_armed", True)
    object.__setattr__(hostile_record, "_armed", True)

    event_error = _assert_integrity_failure(
        lambda: TransitionEventRecordEnvelope(
            event_sequence=7,
            event=hostile_event,
            replay_record=replay_record,
            created_at=event.lease_runtime.evaluated_at,
        )
    )
    replay_error = _assert_integrity_failure(
        lambda: TransitionEventRecordEnvelope(
            event_sequence=7,
            event=event,
            replay_record=hostile_record,
            created_at=event.lease_runtime.evaluated_at,
        )
    )

    for exc in (event_error, replay_error):
        rendered_graph = _render_exception_graph(exc)
        for forbidden in (
            PRIVATE_EVENT_SENTINEL,
            "private-evidence-ref",
            event.event_ref,
            event.command_digest,
            event.canonical_json(),
            replay_record.canonical_json(),
            "HostileEvent",
            "HostileRecord",
        ):
            assert forbidden not in rendered_graph


def test_event_owned_idempotency_match_returns_miss_replay_conflict_or_integrity_failure() -> None:
    command, event, replay_record = _accepted_event_and_replay()
    envelope = transition_event_record_envelope_from_row(_row(event, replay_record))
    assert type(command) is TransitionCommand
    assert type(envelope) is TransitionEventRecordEnvelope

    assert match_transition_event_idempotency(None, command) is None

    replay = match_transition_event_idempotency(envelope, command)
    assert isinstance(replay, CommittedTransition)
    assert replay.replayed is True
    assert replay.event is envelope.event
    assert replay.record is envelope.replay_record

    conflicting = TransitionCommand.create(
        work_item_id=command.work_item_id,
        idempotency_key=command.idempotency_key,
        expected_version=command.expected_version,
        target_state=WorkItemState.BLOCKED,
        lease_identity_decision_ref=command.lease_identity_decision_ref,
        authorization_decision_ref=command.authorization_decision_ref,
        global_stop_ref=command.global_stop_ref,
        global_stop_version=command.global_stop_version,
        safe_failure_class="operator_action_required",
    )
    conflict = match_transition_event_idempotency(envelope, conflicting)
    assert isinstance(conflict, TransitionConflict)
    assert conflict.conflict_class == "idempotency_key_reuse_conflict"

    wrong_work_item = TransitionCommand.create(
        work_item_id="wi-2",
        idempotency_key=command.idempotency_key,
        expected_version=command.expected_version,
        target_state=command.target_state,
        lease_identity_decision_ref=command.lease_identity_decision_ref,
        authorization_decision_ref=command.authorization_decision_ref,
        global_stop_ref=command.global_stop_ref,
        global_stop_version=command.global_stop_version,
    )
    _assert_integrity_failure(lambda: match_transition_event_idempotency(envelope, wrong_work_item))

    wrong_key = TransitionCommand.create(
        work_item_id=command.work_item_id,
        idempotency_key="transition-k2",
        expected_version=command.expected_version,
        target_state=command.target_state,
        lease_identity_decision_ref=command.lease_identity_decision_ref,
        authorization_decision_ref=command.authorization_decision_ref,
        global_stop_ref=command.global_stop_ref,
        global_stop_version=command.global_stop_version,
    )
    _assert_integrity_failure(lambda: match_transition_event_idempotency(envelope, wrong_key))


def test_event_owned_idempotency_match_uses_exact_type_gates_before_semantic_access() -> None:
    source = inspect.getsource(match_transition_event_idempotency)
    envelope_source = inspect.getsource(TransitionEventRecordEnvelope.__post_init__)

    assert "isinstance(existing, TransitionEventRecordEnvelope)" not in source
    assert "isinstance(command, TransitionCommand)" not in source
    assert "isinstance(event, TransitionEvent)" not in source
    assert "isinstance(replay_record, WorkItemRecord)" not in source
    assert "type(existing) is not TransitionEventRecordEnvelope" in source
    assert "type(command) is not TransitionCommand" in source
    assert "type(event) is not TransitionEvent" in source
    assert "type(replay_record) is not WorkItemRecord" in source
    assert "assert " not in source
    assert source.index("type(command) is not TransitionCommand") < source.index("command.work_item_id")
    assert source.index("type(existing) is not TransitionEventRecordEnvelope") < source.index("event = existing.event")
    assert source.index("event = existing.event") < source.index("type(event) is not TransitionEvent")
    assert source.index("replay_record = existing.replay_record") < source.index(
        "type(replay_record) is not WorkItemRecord"
    )
    assert source.index("type(event) is not TransitionEvent") < source.index("event.work_item_id")
    assert source.index("type(replay_record) is not WorkItemRecord") < source.index(
        "CommittedTransition(record=replay_record"
    )

    assert "isinstance(self.event, TransitionEvent)" not in envelope_source
    assert "isinstance(self.replay_record, WorkItemRecord)" not in envelope_source
    assert "type(event) is not TransitionEvent" in envelope_source
    assert "type(replay_record) is not WorkItemRecord" in envelope_source
    assert "assert " not in envelope_source


def test_event_owned_idempotency_match_rejects_subclasses_and_keeps_error_graph_private() -> None:
    command, event, replay_record = _accepted_event_and_replay(evidence_refs=("private-evidence-ref",))
    envelope = transition_event_record_envelope_from_row(_row(event, replay_record))

    class EnvelopeSubclass(TransitionEventRecordEnvelope):
        pass

    class CommandSubclass(TransitionCommand):
        pass

    envelope_subclass = EnvelopeSubclass(
        event_sequence=envelope.event_sequence,
        event=envelope.event,
        replay_record=envelope.replay_record,
        created_at=envelope.created_at,
    )
    command_subclass = CommandSubclass(**command.__dict__)

    invalid_existing = _assert_integrity_failure(
        lambda: match_transition_event_idempotency(object(), command)  # type: ignore[arg-type]
    )
    invalid_command = _assert_integrity_failure(
        lambda: match_transition_event_idempotency(envelope, object())  # type: ignore[arg-type]
    )
    envelope_subclass_error = _assert_integrity_failure(
        lambda: match_transition_event_idempotency(envelope_subclass, command)
    )
    command_subclass_error = _assert_integrity_failure(
        lambda: match_transition_event_idempotency(envelope, command_subclass)
    )

    for exc in (envelope_subclass_error, command_subclass_error):
        assert exc.error_class == invalid_existing.error_class
        assert exc.error_class == invalid_command.error_class
        rendered_graph = _render_exception_graph(exc)
        for forbidden in (
            PRIVATE_EVENT_SENTINEL,
            "private-evidence-ref",
            event.event_ref,
            event.command_digest,
            event.canonical_json(),
            replay_record.canonical_json(),
            "EnvelopeSubclass",
            "CommandSubclass",
        ):
            assert forbidden not in rendered_graph


def test_event_owned_idempotency_match_rejects_hostile_subclasses_before_semantic_attribute_access() -> None:
    command, event, replay_record = _accepted_event_and_replay(evidence_refs=("private-evidence-ref",))
    envelope = transition_event_record_envelope_from_row(_row(event, replay_record))

    class HostileEnvelope(TransitionEventRecordEnvelope):
        def __getattribute__(self, name: str) -> object:
            if name in {"event", "replay_record"}:
                try:
                    armed = object.__getattribute__(self, "_armed")
                except AttributeError:
                    armed = False
                if armed:
                    raise AssertionError(PRIVATE_EVENT_SENTINEL)
            return super().__getattribute__(name)

    class HostileCommand(TransitionCommand):
        def __getattribute__(self, name: str) -> object:
            if name in {"work_item_id", "idempotency_key", "canonical_command_digest"}:
                try:
                    armed = object.__getattribute__(self, "_armed")
                except AttributeError:
                    armed = False
                if armed:
                    raise AssertionError(PRIVATE_EVENT_SENTINEL)
            return super().__getattribute__(name)

    hostile_envelope = HostileEnvelope(
        event_sequence=envelope.event_sequence,
        event=envelope.event,
        replay_record=envelope.replay_record,
        created_at=envelope.created_at,
    )
    hostile_command = HostileCommand(**command.__dict__)
    object.__setattr__(hostile_envelope, "_armed", True)
    object.__setattr__(hostile_command, "_armed", True)

    for exc in (
        _assert_integrity_failure(lambda: match_transition_event_idempotency(hostile_envelope, command)),
        _assert_integrity_failure(lambda: match_transition_event_idempotency(envelope, hostile_command)),
    ):
        rendered_graph = _render_exception_graph(exc)
        for forbidden in (
            PRIVATE_EVENT_SENTINEL,
            "private-evidence-ref",
            event.event_ref,
            event.command_digest,
            event.canonical_json(),
            replay_record.canonical_json(),
            "HostileEnvelope",
            "HostileCommand",
        ):
            assert forbidden not in rendered_graph


def test_event_owned_idempotency_match_defends_against_forged_exact_envelope_nested_values() -> None:
    command, event, replay_record = _accepted_event_and_replay(evidence_refs=("private-evidence-ref",))

    class HostileEvent(TransitionEvent):
        def __getattribute__(self, name: str) -> object:
            if name in {"work_item_id", "idempotency_key", "command_digest", "canonical_digest", "canonical_json"}:
                try:
                    armed = object.__getattribute__(self, "_armed")
                except AttributeError:
                    armed = False
                if armed:
                    raise AssertionError(PRIVATE_EVENT_SENTINEL)
            return super().__getattribute__(name)

    class HostileRecord(WorkItemRecord):
        def __getattribute__(self, name: str) -> object:
            if name in {"work_item_id", "lease_id", "state", "version", "canonical_digest", "canonical_json"}:
                try:
                    armed = object.__getattribute__(self, "_armed")
                except AttributeError:
                    armed = False
                if armed:
                    raise AssertionError(PRIVATE_EVENT_SENTINEL)
            return super().__getattribute__(name)

    hostile_event = HostileEvent(**event.__dict__)
    hostile_record = HostileRecord(**replay_record.__dict__)
    object.__setattr__(hostile_event, "_armed", True)
    object.__setattr__(hostile_record, "_armed", True)

    forged_cases = (
        _forged_transition_event_envelope(event=hostile_event, replay_record=replay_record),
        _forged_transition_event_envelope(event=event, replay_record=hostile_record),
        _forged_transition_event_envelope(event=object(), replay_record=replay_record),
        _forged_transition_event_envelope(event=event, replay_record=object()),
    )

    for forged in forged_cases:
        exc = _assert_integrity_failure(lambda forged=forged: match_transition_event_idempotency(forged, command))
        rendered_graph = _render_exception_graph(exc)
        for forbidden in (
            PRIVATE_EVENT_SENTINEL,
            "private-evidence-ref",
            event.event_ref,
            event.command_digest,
            event.canonical_json(),
            replay_record.canonical_json(),
            "HostileEvent",
            "HostileRecord",
        ):
            assert forbidden not in rendered_graph


def test_transition_event_query_specs_are_private_immutable_data_only_and_prepare_against_schema() -> None:
    assert _B3C0B_TRANSITION_EVENT_QUERY_SPECS == (
        _TRANSITION_EVENT_IDEMPOTENCY_LOOKUP_SELECT,
        _TRANSITION_EVENT_MAX_SEQUENCE_SELECT,
    )
    idempotency = _TRANSITION_EVENT_IDEMPOTENCY_LOOKUP_SELECT
    sequence = _TRANSITION_EVENT_MAX_SEQUENCE_SELECT
    assert isinstance(idempotency, _TransitionEventIdempotencyQuerySpec)
    assert isinstance(sequence, _TransitionEventMaxSequenceQuerySpec)

    assert idempotency.columns == TRANSITION_EVENT_ROW_COLUMNS
    assert idempotency.lookup_columns == ("work_item_id", "idempotency_key")
    assert idempotency.sql == (
        f"SELECT {', '.join(TRANSITION_EVENT_ROW_COLUMNS)}\n"
        "FROM transition_events\n"
        "WHERE work_item_id = ? AND idempotency_key = ?\n"
        "LIMIT 2"
    )
    assert idempotency.sql.count("?") == 2
    assert "SELECT *" not in idempotency.sql
    assert "JOIN" not in idempotency.sql.upper().split()
    assert "(" not in idempotency.sql
    assert ")" not in idempotency.sql
    assert "global_stop_events" not in idempotency.sql
    assert "global_stop_current" not in idempotency.sql

    assert sequence.sql == "SELECT MAX(event_sequence)\nFROM transition_events"
    assert sequence.sql.count("?") == 0
    assert "WHERE" not in sequence.sql
    assert "JOIN" not in sequence.sql.upper().split()

    with pytest.raises(Exception):
        idempotency.table_name = "changed"  # type: ignore[misc]

    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(MIGRATION_PATH.read_text(encoding="utf-8"))
        connection.execute(f"EXPLAIN QUERY PLAN {idempotency.sql}", ("wi-1", "transition-k1")).fetchall()
        connection.execute(f"EXPLAIN QUERY PLAN {sequence.sql}").fetchall()
    finally:
        connection.close()


def test_sequence_allocation_contract_is_pure_and_strict() -> None:
    assert next_transition_event_sequence(None) == 0
    assert next_transition_event_sequence(0) == 1
    assert next_transition_event_sequence(41) == 42
    for value in (False, True, -1, 1.25, "1", object()):
        _assert_integrity_failure(lambda value=value: next_transition_event_sequence(value))  # type: ignore[arg-type]
    with pytest.raises(SQLiteMutationStoreError) as exhausted:
        next_transition_event_sequence(SQLITE_SIGNED_INT_MAX)
    assert exhausted.value.error_class == "event_sequence_exhausted"


def test_b3c0b_sources_add_no_sql_execution_reader_or_mutation_runtime_surface() -> None:
    event_source = EVENT_CONTRACTS_PATH.read_text(encoding="utf-8")
    persistence_source = PERSISTENCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(event_source)
    forbidden_calls = {
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
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
            elif isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls

    for forbidden in (
        "sqlite3",
        "StateStore",
        "WriterSession",
        "TransitionContext",
        "evaluate_transition",
        "INSERT",
        "UPDATE",
        "DELETE",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
        "fixture",
        "seed_",
        "admission",
        "authorization_verifier",
    ):
        assert forbidden not in event_source

    assert "TransitionEventRecordEnvelope" in persistence_source
    assert "transition_event_record_envelope_from_row" in persistence_source
    assert "match_transition_event_idempotency" in persistence_source
    assert "sqlite3" not in persistence_source


def test_b3c0b_adds_no_public_export_or_state_store_writer_session_widening() -> None:
    for name in (
        "TRANSITION_EVENT_ROW_COLUMNS",
        "TransitionEventRecordEnvelope",
        "TransitionEventRecordContract",
        "transition_event_record_envelope_from_row",
        "match_transition_event_idempotency",
        "_TRANSITION_EVENT_IDEMPOTENCY_LOOKUP_SELECT",
        "_TRANSITION_EVENT_MAX_SEQUENCE_SELECT",
    ):
        assert name not in ge_nwp_coordinator.__all__
        assert not hasattr(ge_nwp_coordinator, name)

    assert list(inspect.signature(StateStore.read_current).parameters) == ["self", "work_item_id"]
    assert list(inspect.signature(StateStore.read_global_stop).parameters) == ["self"]
    assert list(inspect.signature(WriterSession.apply_transition).parameters) == ["self", "transition_command"]
    assert list(inspect.signature(WriterSession.apply_global_stop_update).parameters) == [
        "self",
        "global_stop_command",
        "typed_operator_decision",
    ]

    writer_source = (PACKAGE_DIR / "sqlite_writer_session.py").read_text(encoding="utf-8")
    state_store_source = (PACKAGE_DIR / "state_store.py").read_text(encoding="utf-8")
    for forbidden in (
        "transition_event_record_envelope_from_row",
        "match_transition_event_idempotency",
        "sqlite_transition_event_contracts",
    ):
        assert forbidden not in writer_source
        assert forbidden not in state_store_source


def test_b3c0b_boundary_files_and_migrations_remain_frozen() -> None:
    assert sorted(path.name for path in (PACKAGE_DIR / "sqlite_migrations").glob("*.sql")) == ["0001_initial.sql"]
    assert hashlib.sha256(MIGRATION_PATH.read_bytes()).hexdigest() == EXPECTED_MIGRATION_0001_CHECKSUM
    assert not (PACKAGE_DIR / "sqlite_transition_fixtures.py").exists()
    assert not (PACKAGE_DIR / "sqlite_transition_readers.py").exists()
    assert not (PACKAGE_DIR / "sqlite_transition_mutation.py").exists()
