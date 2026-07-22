"""Private pure B3c4a transition write and commit-resolution contracts.

B3c4a freezes write SQL shape, parameter builders, planned transition-write
values, and future commit-resolution vocabulary only. This module deliberately
does not import the SQLite runtime, open database handles, run SQL, allocate sequences
from durable state, integrate with the transaction controller, or change public
writer-session behavior.
"""

from dataclasses import dataclass as _dataclass, field as _field
from enum import Enum as _Enum

from ge_nwp_coordinator.canonicalization import canonical_json_bytes as _canonical_json_bytes
from ge_nwp_coordinator.persistence_contracts import (
    SQLITE_SIGNED_INT_MAX as _SQLITE_SIGNED_INT_MAX,
    TRANSITION_EVENT_ROW_COLUMNS as _TRANSITION_EVENT_ROW_COLUMNS,
    WORK_ITEM_ROW_COLUMNS as _WORK_ITEM_ROW_COLUMNS,
    encode_sqlite_boolean as _encode_sqlite_boolean,
    normalize_transaction_timestamp as _normalize_transaction_timestamp,
    transition_event_record_envelope_from_row as _transition_event_record_envelope_from_row,
    work_item_record_envelope_from_row as _work_item_record_envelope_from_row,
)
from ge_nwp_coordinator.sqlite_transition_dry_run_contracts import (
    _collapse_private_contract_failure,
    _require_initialized_committed_transition,
    _require_initialized_transition_evaluation,
    _require_initialized_transition_event,
    _require_initialized_work_item_record,
)
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError as _SQLiteMutationStoreError,
    SQLiteMutationStoreErrorCode as _SQLiteMutationStoreErrorCode,
)
from ge_nwp_coordinator.state_machine import (
    WORK_ITEM_STATE_SCHEMA_ID as _WORK_ITEM_STATE_SCHEMA_ID,
    TransitionEvaluation as _TransitionEvaluation,
    TransitionEvaluationKind as _TransitionEvaluationKind,
    TransitionEvent as _TransitionEvent,
    TransitionEventOutcome as _TransitionEventOutcome,
    WorkItemRecord as _WorkItemRecord,
)
from ge_nwp_coordinator.state_store import CommittedTransition as _CommittedTransition

__all__: tuple[str, ...] = ()

_TRANSITION_EVENTS_TABLE = "transition_events"
_WORK_ITEMS_TABLE = "work_items"
_ACCEPTED_WORK_ITEM_CAS_SET_COLUMNS = _WORK_ITEM_ROW_COLUMNS[1:]
_ACCEPTED_WORK_ITEM_CAS_WHERE_COLUMNS = ("work_item_id", "version")


@_dataclass(frozen=True, slots=True, repr=False)
class _TransitionEventInsertSpec:
    table_name: str
    columns: tuple[str, ...]
    sql: str
    parameter_count: int

    def __post_init__(self) -> None:
        if self.table_name != _TRANSITION_EVENTS_TABLE:
            raise ValueError("invalid_transition_event_insert_spec")
        if self.columns != _TRANSITION_EVENT_ROW_COLUMNS:
            raise ValueError("invalid_transition_event_insert_spec")
        if self.parameter_count != len(_TRANSITION_EVENT_ROW_COLUMNS) or self.parameter_count != 27:
            raise ValueError("invalid_transition_event_insert_spec")
        if self.sql != _transition_event_insert_sql(_TRANSITION_EVENT_ROW_COLUMNS):
            raise ValueError("invalid_transition_event_insert_spec")

    def __repr__(self) -> str:
        return "<_TransitionEventInsertSpec>"

    def __reduce__(self) -> object:
        raise TypeError("invalid transition write contract")


@_dataclass(frozen=True, slots=True, repr=False)
class _AcceptedWorkItemCasSpec:
    table_name: str
    set_columns: tuple[str, ...]
    where_columns: tuple[str, ...]
    sql: str
    parameter_count: int

    def __post_init__(self) -> None:
        if self.table_name != _WORK_ITEMS_TABLE:
            raise ValueError("invalid_accepted_work_item_cas_spec")
        if self.set_columns != _ACCEPTED_WORK_ITEM_CAS_SET_COLUMNS:
            raise ValueError("invalid_accepted_work_item_cas_spec")
        if self.where_columns != _ACCEPTED_WORK_ITEM_CAS_WHERE_COLUMNS:
            raise ValueError("invalid_accepted_work_item_cas_spec")
        if self.parameter_count != len(self.set_columns) + len(self.where_columns) or self.parameter_count != 15:
            raise ValueError("invalid_accepted_work_item_cas_spec")
        if self.sql != _accepted_work_item_cas_sql(
            set_columns=_ACCEPTED_WORK_ITEM_CAS_SET_COLUMNS,
            where_columns=_ACCEPTED_WORK_ITEM_CAS_WHERE_COLUMNS,
        ):
            raise ValueError("invalid_accepted_work_item_cas_spec")

    def __repr__(self) -> str:
        return "<_AcceptedWorkItemCasSpec>"

    def __reduce__(self) -> object:
        raise TypeError("invalid transition write contract")


@_dataclass(frozen=True, slots=True, repr=False)
class _TransitionEventInsertValues:
    spec: _TransitionEventInsertSpec = _field(repr=False)
    parameters: tuple[object, ...] = _field(repr=False)
    event: _TransitionEvent = _field(repr=False)
    replay_record: _WorkItemRecord = _field(repr=False)
    event_sequence: int
    created_at: str

    def __post_init__(self) -> None:
        def validate() -> None:
            _require_exact_event_insert_spec(self.spec)
            event = _require_initialized_transition_event(self.event)
            replay_record = _require_initialized_work_item_record(self.replay_record)
            sequence = _require_event_sequence(self.event_sequence)
            created_at = _normalize_transaction_timestamp(self.created_at)
            expected = _expected_transition_event_insert_parameters(
                event=event,
                replay_record=replay_record,
                event_sequence=sequence,
                created_at=created_at,
            )
            _require_exact_parameter_tuple(
                self.parameters,
                expected,
                parameter_count=self.spec.parameter_count,
            )
            row = dict(zip(self.spec.columns, expected, strict=True))
            envelope = _transition_event_record_envelope_from_row(row)
            if (
                envelope.event_sequence != sequence
                or envelope.event != event
                or envelope.replay_record != replay_record
                or envelope.created_at != created_at
            ):
                raise ValueError("invalid_event_insert_values")
            object.__setattr__(self, "parameters", expected)
            object.__setattr__(self, "event", event)
            object.__setattr__(self, "replay_record", replay_record)
            object.__setattr__(self, "event_sequence", sequence)
            object.__setattr__(self, "created_at", created_at)

        _collapse_private_contract_failure(validate)

    def __repr__(self) -> str:
        return "<_TransitionEventInsertValues>"

    def __reduce__(self) -> object:
        raise TypeError("invalid transition write contract")


@_dataclass(frozen=True, slots=True, repr=False)
class _AcceptedWorkItemCasValues:
    spec: _AcceptedWorkItemCasSpec = _field(repr=False)
    parameters: tuple[object, ...] = _field(repr=False)
    source_record: _WorkItemRecord = _field(repr=False)
    resulting_record: _WorkItemRecord = _field(repr=False)
    updated_at: str

    def __post_init__(self) -> None:
        def validate() -> None:
            _require_exact_cas_spec(self.spec)
            source = _require_initialized_work_item_record(self.source_record)
            resulting = _require_initialized_work_item_record(self.resulting_record)
            updated_at = _normalize_transaction_timestamp(self.updated_at)
            expected = _expected_accepted_work_item_cas_parameters(
                safe_source_record=source,
                safe_resulting_record=resulting,
                normalized_timestamp=updated_at,
            )
            _require_exact_parameter_tuple(
                self.parameters,
                expected,
                parameter_count=self.spec.parameter_count,
            )
            row = _work_item_row_for_adapter(resulting, updated_at)
            envelope = _work_item_record_envelope_from_row(row)
            if envelope.record != resulting or envelope.updated_at != updated_at:
                raise ValueError("invalid_accepted_work_item_cas_values")
            object.__setattr__(self, "parameters", expected)
            object.__setattr__(self, "source_record", source)
            object.__setattr__(self, "resulting_record", resulting)
            object.__setattr__(self, "updated_at", updated_at)

        _collapse_private_contract_failure(validate)

    def __repr__(self) -> str:
        return "<_AcceptedWorkItemCasValues>"

    def __reduce__(self) -> object:
        raise TypeError("invalid transition write contract")


@_dataclass(frozen=True, slots=True, repr=False)
class _TransitionWritePlan:
    planned_transition: _CommittedTransition = _field(repr=False)
    event_insert: _TransitionEventInsertValues = _field(repr=False)
    accepted_work_item_cas: _AcceptedWorkItemCasValues | None = _field(default=None, repr=False)

    def __post_init__(self) -> None:
        def validate() -> None:
            planned = _require_planned_transition(self.planned_transition)
            event_insert = _require_exact_event_insert_values(self.event_insert)
            if planned.event != event_insert.event or planned.record != event_insert.replay_record:
                raise ValueError("invalid_transition_write_plan")
            if planned.event.outcome is _TransitionEventOutcome.ACCEPTED:
                cas = _require_exact_cas_values(self.accepted_work_item_cas)
                if cas.resulting_record != planned.record or event_insert.created_at != cas.updated_at:
                    raise ValueError("invalid_transition_write_plan")
                _require_source_record_matches_event(cas.source_record, planned.event)
                _require_resulting_record_matches_event(cas.resulting_record, planned.event)
                object.__setattr__(self, "planned_transition", planned)
                object.__setattr__(self, "event_insert", event_insert)
                object.__setattr__(self, "accepted_work_item_cas", cas)
                return
            if planned.event.outcome is _TransitionEventOutcome.DOMAIN_REJECTED:
                if self.accepted_work_item_cas is not None:
                    raise ValueError("invalid_transition_write_plan")
                _require_domain_rejected_event(planned.event)
                object.__setattr__(self, "planned_transition", planned)
                object.__setattr__(self, "event_insert", event_insert)
                object.__setattr__(self, "accepted_work_item_cas", None)
                return
            raise ValueError("invalid_transition_write_plan")

        _collapse_private_contract_failure(validate)

    def __repr__(self) -> str:
        return "<_TransitionWritePlan planned_not_committed>"

    def __reduce__(self) -> object:
        raise TypeError("invalid transition write contract")


class _TransitionCommitResolutionState(str, _Enum):
    NEW = "new"
    TRANSACTION_ACTIVE = "transaction_active"
    FENCED = "fenced"
    CAPABILITY_ACTIVE = "capability_active"
    PLANNED_OUTCOME = "planned_outcome"
    WRITES_PERFORMED = "writes_performed"
    CAPABILITY_INVALIDATED = "capability_invalidated"
    COMMIT_ATTEMPT_STARTED = "commit_attempt_started"
    COMMIT_SUCCEEDED = "commit_succeeded"
    COMMIT_OUTCOME_UNKNOWN = "commit_outcome_unknown"
    ROLLBACK_RESOLVED = "rollback_resolved"
    CLOSED = "closed"


def _transition_event_insert_values(
    evaluation: _TransitionEvaluation,
    event_sequence: int,
    transaction_timestamp: str,
) -> _TransitionEventInsertValues:
    def build() -> _TransitionEventInsertValues:
        checked = _require_write_evaluation(evaluation)
        event = checked.event
        replay_record = checked.record
        if type(event) is not _TransitionEvent:
            raise ValueError("invalid_transition_event")
        sequence = _require_event_sequence(event_sequence)
        created_at = _normalize_transaction_timestamp(transaction_timestamp)
        if created_at != event.lease_runtime.evaluated_at:
            raise ValueError("invalid_transition_timestamp")
        parameters = _expected_transition_event_insert_parameters(
            event=event,
            replay_record=replay_record,
            event_sequence=sequence,
            created_at=created_at,
        )
        return _TransitionEventInsertValues(
            spec=_TRANSITION_EVENT_INSERT_SPEC,
            parameters=parameters,
            event=event,
            replay_record=replay_record,
            event_sequence=sequence,
            created_at=created_at,
        )

    return _collapse_private_contract_failure(build)


def _accepted_work_item_cas_values(
    source_record: _WorkItemRecord,
    resulting_record: _WorkItemRecord,
    transaction_timestamp: str,
) -> _AcceptedWorkItemCasValues:
    def build() -> _AcceptedWorkItemCasValues:
        source = _require_initialized_work_item_record(source_record)
        resulting = _require_initialized_work_item_record(resulting_record)
        updated_at = _normalize_transaction_timestamp(transaction_timestamp)
        parameters = _expected_accepted_work_item_cas_parameters(
            safe_source_record=source,
            safe_resulting_record=resulting,
            normalized_timestamp=updated_at,
        )
        return _AcceptedWorkItemCasValues(
            spec=_ACCEPTED_WORK_ITEM_CAS_SPEC,
            parameters=parameters,
            source_record=source,
            resulting_record=resulting,
            updated_at=updated_at,
        )

    return _collapse_private_contract_failure(build)


def _transition_write_plan(
    evaluation: _TransitionEvaluation,
    *,
    source_record: _WorkItemRecord,
    event_sequence: int,
    transaction_timestamp: str,
) -> _TransitionWritePlan:
    def build() -> _TransitionWritePlan:
        checked = _require_write_evaluation(evaluation)
        source = _require_initialized_work_item_record(source_record)
        event = checked.event
        if type(event) is not _TransitionEvent:
            raise ValueError("invalid_transition_event")
        _require_source_record_matches_event(source, event)
        event_insert = _transition_event_insert_values(
            checked,
            event_sequence,
            transaction_timestamp,
        )
        planned_transition = _CommittedTransition(record=checked.record, event=event, replayed=False)
        if checked.kind is _TransitionEvaluationKind.ACCEPTED:
            cas = _accepted_work_item_cas_values(
                source,
                checked.record,
                transaction_timestamp,
            )
        elif checked.kind is _TransitionEvaluationKind.DOMAIN_REJECTED:
            if checked.record != source:
                raise ValueError("invalid_domain_rejected_record")
            cas = None
        else:
            raise ValueError("invalid_transition_evaluation")
        return _TransitionWritePlan(
            planned_transition=planned_transition,
            event_insert=event_insert,
            accepted_work_item_cas=cas,
        )

    return _collapse_private_contract_failure(build)


def _transition_event_insert_sql(columns: tuple[str, ...]) -> str:
    if columns != _TRANSITION_EVENT_ROW_COLUMNS:
        raise ValueError("invalid_transition_event_insert_columns")
    return (
        "INSERT INTO transition_events (\n"
        "    event_ref,\n"
        "    event_sequence,\n"
        "    work_item_id,\n"
        "    lease_id,\n"
        "    idempotency_key,\n"
        "    command_digest,\n"
        "    source_state,\n"
        "    source_version,\n"
        "    resulting_state,\n"
        "    resulting_version,\n"
        "    outcome,\n"
        "    reason,\n"
        "    evidence_refs_json,\n"
        "    budget_cost_delta,\n"
        "    attempt_count_delta,\n"
        "    repair_count_delta,\n"
        "    lease_identity_decision_ref,\n"
        "    authorization_decision_ref,\n"
        "    dependency_decision_ref,\n"
        "    global_stop_ref,\n"
        "    global_stop_version,\n"
        "    schema_id,\n"
        "    event_json,\n"
        "    event_digest,\n"
        "    replay_work_item_json,\n"
        "    replay_work_item_digest,\n"
        "    created_at\n"
        ") VALUES (\n"
        "    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,\n"
        "    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,\n"
        "    ?, ?, ?, ?, ?, ?, ?\n"
        ")"
    )


def _accepted_work_item_cas_sql(
    *,
    set_columns: tuple[str, ...],
    where_columns: tuple[str, ...],
) -> str:
    if set_columns != _ACCEPTED_WORK_ITEM_CAS_SET_COLUMNS or where_columns != _ACCEPTED_WORK_ITEM_CAS_WHERE_COLUMNS:
        raise ValueError("invalid_accepted_work_item_cas_columns")
    return (
        "UPDATE work_items\n"
        "SET\n"
        "    lease_id = ?,\n"
        "    backlog_id = ?,\n"
        "    schema_id = ?,\n"
        "    state = ?,\n"
        "    version = ?,\n"
        "    attempt_count = ?,\n"
        "    repair_count = ?,\n"
        "    budget_consumed = ?,\n"
        "    budget_limit = ?,\n"
        "    max_attempts = ?,\n"
        "    max_repairs = ?,\n"
        "    cleanup_required = ?,\n"
        "    updated_at = ?\n"
        "WHERE work_item_id = ?\n"
        "  AND version = ?"
    )


def _require_write_evaluation(evaluation: _TransitionEvaluation) -> _TransitionEvaluation:
    def validate() -> _TransitionEvaluation:
        checked = _require_initialized_transition_evaluation(evaluation)
        kind = checked.kind
        if type(kind) is not _TransitionEvaluationKind:
            raise ValueError("invalid_transition_evaluation")
        if kind is _TransitionEvaluationKind.PRE_APPLY_INVALID:
            raise ValueError("invalid_transition_evaluation")
        if kind is not _TransitionEvaluationKind.ACCEPTED and kind is not _TransitionEvaluationKind.DOMAIN_REJECTED:
            raise ValueError("invalid_transition_evaluation")
        record = _require_exact_work_item_record(checked.record)
        event = _require_exact_transition_event(checked.event)
        if kind.value != event.outcome.value or checked.reason != event.reason:
            raise ValueError("invalid_transition_evaluation")
        if record.work_item_id != event.work_item_id:
            raise ValueError("invalid_transition_evaluation")
        if record.state is not event.resulting_state or record.version != event.resulting_version:
            raise ValueError("invalid_transition_evaluation")
        return _TransitionEvaluation(kind=kind, reason=checked.reason, record=record, event=event)

    return _collapse_private_contract_failure(validate)


def _expected_transition_event_insert_parameters(
    *,
    event: _TransitionEvent,
    replay_record: _WorkItemRecord,
    event_sequence: int,
    created_at: str,
) -> tuple[object, ...]:
    return (
        event.event_ref,
        event_sequence,
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
        _canonical_json_bytes(list(event.evidence_refs)).decode("utf-8"),
        event.budget_cost_delta,
        event.attempt_count_delta,
        event.repair_count_delta,
        event.lease_identity_decision_ref,
        event.authorization_decision_ref,
        event.dependency_decision_ref,
        event.global_stop_ref,
        event.global_stop_version,
        event.schema_id,
        _TransitionEvent.canonical_json(event),
        _TransitionEvent.canonical_digest(event),
        _WorkItemRecord.canonical_json(replay_record),
        _WorkItemRecord.canonical_digest(replay_record),
        created_at,
    )


def _expected_accepted_work_item_cas_parameters(
    *,
    safe_source_record: _WorkItemRecord,
    safe_resulting_record: _WorkItemRecord,
    normalized_timestamp: str,
) -> tuple[object, ...]:
    _require_accepted_cas_records(safe_source_record, safe_resulting_record)
    return (
        safe_resulting_record.lease_id,
        safe_resulting_record.backlog_id,
        safe_resulting_record.schema_id,
        safe_resulting_record.state.value,
        safe_resulting_record.version,
        safe_resulting_record.attempt_count,
        safe_resulting_record.repair_count,
        safe_resulting_record.budget_consumed,
        safe_resulting_record.budget_limit,
        safe_resulting_record.max_attempts,
        safe_resulting_record.max_repairs,
        _encode_sqlite_boolean(safe_resulting_record.cleanup_required, "accepted_work_item_cas.cleanup_required"),
        normalized_timestamp,
        safe_source_record.work_item_id,
        safe_source_record.version,
    )


def _require_exact_parameter_tuple(
    value: object,
    expected: tuple[object, ...],
    *,
    parameter_count: int,
) -> tuple[object, ...]:
    if type(value) is not tuple or len(value) != parameter_count or len(expected) != parameter_count:
        raise _database_integrity_failure()
    for actual, expected_value in zip(value, expected, strict=True):
        if type(actual) is not type(expected_value) or actual != expected_value:
            raise _database_integrity_failure()
    return expected


def _require_accepted_cas_records(source: _WorkItemRecord, resulting: _WorkItemRecord) -> None:
    if source.work_item_id != resulting.work_item_id:
        raise _database_integrity_failure()
    if source.lease_id != resulting.lease_id or source.backlog_id != resulting.backlog_id:
        raise _database_integrity_failure()
    if source.schema_id != _WORK_ITEM_STATE_SCHEMA_ID or resulting.schema_id != _WORK_ITEM_STATE_SCHEMA_ID:
        raise _database_integrity_failure()
    if resulting.version != source.version + 1:
        raise _database_integrity_failure()


def _require_source_record_matches_event(source: _WorkItemRecord, event: _TransitionEvent) -> None:
    if source.work_item_id != event.work_item_id:
        raise _database_integrity_failure()
    if source.lease_id != event.lease_id:
        raise _database_integrity_failure()
    if source.state is not event.source_state or source.version != event.source_version:
        raise _database_integrity_failure()


def _require_resulting_record_matches_event(resulting: _WorkItemRecord, event: _TransitionEvent) -> None:
    if resulting.work_item_id != event.work_item_id:
        raise _database_integrity_failure()
    if resulting.lease_id != event.lease_id:
        raise _database_integrity_failure()
    if resulting.schema_id != _WORK_ITEM_STATE_SCHEMA_ID:
        raise _database_integrity_failure()
    if resulting.state is not event.resulting_state or resulting.version != event.resulting_version:
        raise _database_integrity_failure()


def _require_domain_rejected_event(event: _TransitionEvent) -> None:
    if event.source_state is not event.resulting_state or event.source_version != event.resulting_version:
        raise _database_integrity_failure()
    if event.budget_cost_delta != 0 or event.attempt_count_delta != 0 or event.repair_count_delta != 0:
        raise _database_integrity_failure()


def _work_item_row_for_adapter(record: _WorkItemRecord, updated_at: str) -> dict[str, object]:
    return {
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
        "cleanup_required": _encode_sqlite_boolean(record.cleanup_required, "accepted_work_item_cas.cleanup_required"),
        "updated_at": updated_at,
    }


def _require_event_sequence(value: int) -> int:
    if type(value) is not int or value < 0 or value > _SQLITE_SIGNED_INT_MAX:
        raise _database_integrity_failure()
    return value


def _require_exact_event_insert_spec(value: object) -> _TransitionEventInsertSpec:
    if type(value) is not _TransitionEventInsertSpec or value is not _TRANSITION_EVENT_INSERT_SPEC:
        raise _database_integrity_failure()
    return value


def _require_exact_cas_spec(value: object) -> _AcceptedWorkItemCasSpec:
    if type(value) is not _AcceptedWorkItemCasSpec or value is not _ACCEPTED_WORK_ITEM_CAS_SPEC:
        raise _database_integrity_failure()
    return value


def _require_exact_event_insert_values(value: object) -> _TransitionEventInsertValues:
    def reconstruct() -> _TransitionEventInsertValues:
        if type(value) is not _TransitionEventInsertValues:
            raise ValueError("invalid_event_insert_values")
        return _TransitionEventInsertValues(
            spec=value.spec,
            parameters=value.parameters,
            event=value.event,
            replay_record=value.replay_record,
            event_sequence=value.event_sequence,
            created_at=value.created_at,
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_exact_cas_values(value: object) -> _AcceptedWorkItemCasValues:
    def reconstruct() -> _AcceptedWorkItemCasValues:
        if type(value) is not _AcceptedWorkItemCasValues:
            raise ValueError("invalid_accepted_work_item_cas_values")
        return _AcceptedWorkItemCasValues(
            spec=value.spec,
            parameters=value.parameters,
            source_record=value.source_record,
            resulting_record=value.resulting_record,
            updated_at=value.updated_at,
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_exact_transition_event(value: object) -> _TransitionEvent:
    def reconstruct() -> _TransitionEvent:
        if type(value) is not _TransitionEvent:
            raise ValueError("invalid_transition_event")
        return _require_initialized_transition_event(value)

    return _collapse_private_contract_failure(reconstruct)


def _require_exact_work_item_record(value: object) -> _WorkItemRecord:
    def reconstruct() -> _WorkItemRecord:
        if type(value) is not _WorkItemRecord:
            raise ValueError("invalid_work_item_record")
        return _require_initialized_work_item_record(value)

    return _collapse_private_contract_failure(reconstruct)


def _require_planned_transition(value: object) -> _CommittedTransition:
    def reconstruct() -> _CommittedTransition:
        if type(value) is not _CommittedTransition:
            raise ValueError("invalid_planned_transition")
        checked = _require_initialized_committed_transition(value)
        if checked.replayed is not False:
            raise ValueError("invalid_planned_transition")
        return checked

    return _collapse_private_contract_failure(reconstruct)


def _database_integrity_failure() -> _SQLiteMutationStoreError:
    return _SQLiteMutationStoreError(_SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


_TRANSITION_EVENT_INSERT_SPEC = _TransitionEventInsertSpec(
    table_name=_TRANSITION_EVENTS_TABLE,
    columns=_TRANSITION_EVENT_ROW_COLUMNS,
    sql=_transition_event_insert_sql(_TRANSITION_EVENT_ROW_COLUMNS),
    parameter_count=27,
)
_ACCEPTED_WORK_ITEM_CAS_SPEC = _AcceptedWorkItemCasSpec(
    table_name=_WORK_ITEMS_TABLE,
    set_columns=_ACCEPTED_WORK_ITEM_CAS_SET_COLUMNS,
    where_columns=_ACCEPTED_WORK_ITEM_CAS_WHERE_COLUMNS,
    sql=_accepted_work_item_cas_sql(
        set_columns=_ACCEPTED_WORK_ITEM_CAS_SET_COLUMNS,
        where_columns=_ACCEPTED_WORK_ITEM_CAS_WHERE_COLUMNS,
    ),
    parameter_count=15,
)

_TRANSITION_COMMIT_RESOLUTION_REPLAY_CONFLICT_PATH = (
    _TransitionCommitResolutionState.TRANSACTION_ACTIVE,
    _TransitionCommitResolutionState.FENCED,
    _TransitionCommitResolutionState.CAPABILITY_ACTIVE,
    _TransitionCommitResolutionState.CAPABILITY_INVALIDATED,
    _TransitionCommitResolutionState.ROLLBACK_RESOLVED,
    _TransitionCommitResolutionState.CLOSED,
)
_TRANSITION_COMMIT_RESOLUTION_FRESH_SUCCESS_PATH = (
    _TransitionCommitResolutionState.TRANSACTION_ACTIVE,
    _TransitionCommitResolutionState.FENCED,
    _TransitionCommitResolutionState.CAPABILITY_ACTIVE,
    _TransitionCommitResolutionState.PLANNED_OUTCOME,
    _TransitionCommitResolutionState.WRITES_PERFORMED,
    _TransitionCommitResolutionState.CAPABILITY_INVALIDATED,
    _TransitionCommitResolutionState.COMMIT_ATTEMPT_STARTED,
    _TransitionCommitResolutionState.COMMIT_SUCCEEDED,
    _TransitionCommitResolutionState.CLOSED,
)
_TRANSITION_COMMIT_RESOLUTION_FRESH_UNCERTAIN_PATH = (
    _TransitionCommitResolutionState.TRANSACTION_ACTIVE,
    _TransitionCommitResolutionState.FENCED,
    _TransitionCommitResolutionState.CAPABILITY_ACTIVE,
    _TransitionCommitResolutionState.PLANNED_OUTCOME,
    _TransitionCommitResolutionState.WRITES_PERFORMED,
    _TransitionCommitResolutionState.CAPABILITY_INVALIDATED,
    _TransitionCommitResolutionState.COMMIT_ATTEMPT_STARTED,
    _TransitionCommitResolutionState.COMMIT_OUTCOME_UNKNOWN,
    _TransitionCommitResolutionState.CLOSED,
)
_TRANSITION_COMMIT_RESOLUTION_PLANNED_OUTCOME_FAILURE_PATH = (
    _TransitionCommitResolutionState.TRANSACTION_ACTIVE,
    _TransitionCommitResolutionState.FENCED,
    _TransitionCommitResolutionState.CAPABILITY_ACTIVE,
    _TransitionCommitResolutionState.PLANNED_OUTCOME,
    _TransitionCommitResolutionState.CAPABILITY_INVALIDATED,
    _TransitionCommitResolutionState.ROLLBACK_RESOLVED,
    _TransitionCommitResolutionState.CLOSED,
)
_TRANSITION_COMMIT_RESOLUTION_POST_WRITE_PRECOMMIT_FAILURE_PATH = (
    _TransitionCommitResolutionState.TRANSACTION_ACTIVE,
    _TransitionCommitResolutionState.FENCED,
    _TransitionCommitResolutionState.CAPABILITY_ACTIVE,
    _TransitionCommitResolutionState.PLANNED_OUTCOME,
    _TransitionCommitResolutionState.WRITES_PERFORMED,
    _TransitionCommitResolutionState.CAPABILITY_INVALIDATED,
    _TransitionCommitResolutionState.ROLLBACK_RESOLVED,
    _TransitionCommitResolutionState.CLOSED,
)
_B3C4A_COMMIT_RESOLUTION_GRAPH_SCOPE = (
    "successful_commit_resolution_milestones_after_graph_covered_transaction_authority",
    "not_complete_operational_cleanup_model",
    "stale_writer_pre_capability_outside_graph",
    "other_pre_capability_failures_outside_graph",
    "pre_capability_exits_cannot_claim_capability_states",
    "capability_invalidation_failure_cannot_claim_capability_invalidated",
    "rollback_failure_cannot_claim_rollback_resolved",
    "close_failure_cannot_force_closed_milestone",
    "successful_capability_invalidation_before_rollback_resolved",
    "successful_capability_invalidation_before_commit_attempt_started",
    "no_direct_rollback_edge_bypasses_capability_invalidation",
    "b3c4b_runtime_enforcement_future",
)
_TRANSITION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS = frozenset(
    {
        (_TransitionCommitResolutionState.NEW, _TransitionCommitResolutionState.TRANSACTION_ACTIVE),
        (_TransitionCommitResolutionState.TRANSACTION_ACTIVE, _TransitionCommitResolutionState.FENCED),
        (_TransitionCommitResolutionState.FENCED, _TransitionCommitResolutionState.CAPABILITY_ACTIVE),
        (_TransitionCommitResolutionState.CAPABILITY_ACTIVE, _TransitionCommitResolutionState.PLANNED_OUTCOME),
        (_TransitionCommitResolutionState.CAPABILITY_ACTIVE, _TransitionCommitResolutionState.CAPABILITY_INVALIDATED),
        (_TransitionCommitResolutionState.PLANNED_OUTCOME, _TransitionCommitResolutionState.CAPABILITY_INVALIDATED),
        (_TransitionCommitResolutionState.PLANNED_OUTCOME, _TransitionCommitResolutionState.WRITES_PERFORMED),
        (_TransitionCommitResolutionState.WRITES_PERFORMED, _TransitionCommitResolutionState.CAPABILITY_INVALIDATED),
        (_TransitionCommitResolutionState.CAPABILITY_INVALIDATED, _TransitionCommitResolutionState.ROLLBACK_RESOLVED),
        (_TransitionCommitResolutionState.CAPABILITY_INVALIDATED, _TransitionCommitResolutionState.COMMIT_ATTEMPT_STARTED),
        (_TransitionCommitResolutionState.COMMIT_ATTEMPT_STARTED, _TransitionCommitResolutionState.COMMIT_SUCCEEDED),
        (_TransitionCommitResolutionState.COMMIT_ATTEMPT_STARTED, _TransitionCommitResolutionState.COMMIT_OUTCOME_UNKNOWN),
        (_TransitionCommitResolutionState.ROLLBACK_RESOLVED, _TransitionCommitResolutionState.CLOSED),
        (_TransitionCommitResolutionState.COMMIT_SUCCEEDED, _TransitionCommitResolutionState.CLOSED),
        (_TransitionCommitResolutionState.COMMIT_OUTCOME_UNKNOWN, _TransitionCommitResolutionState.CLOSED),
    }
)

_B3C4A_SQLITE_CLASSIFICATION_MATRIX = (
    ("maximum_sequence_read", "schema_query_corruption_cardinality_shape", "database_integrity_failure"),
    ("maximum_sequence_read", "operational_or_unknown", "mutation_failed"),
    ("event_insert", "event_ref_collision_after_miss", "database_integrity_failure"),
    ("event_insert", "event_sequence_collision_after_miss", "database_integrity_failure"),
    ("event_insert", "idempotency_collision_after_miss", "database_integrity_failure"),
    ("event_insert", "schema_constraint_contradiction", "database_integrity_failure"),
    ("event_insert", "operational", "mutation_failed"),
    ("accepted_cas", "rowcount_not_one", "database_integrity_failure"),
    ("accepted_cas", "schema_constraint_contradiction", "database_integrity_failure"),
    ("accepted_cas", "operational", "mutation_failed"),
    ("rollback_before_commit_attempt", "any_rollback_failure", "mutation_failed"),
    ("commit", "any_exception_after_attempt_begins", "commit_outcome_unknown"),
    ("close_before_commit_attempt", "after_successful_rollback", "mutation_failed"),
    ("close_after_commit_success", "close_failure", "committed_success"),
    ("close_after_commit_uncertainty", "close_failure", "commit_outcome_unknown"),
)
_B3C4A_RETRY_AFTER_COMMIT_UNCERTAINTY_CONTRACT = (
    "caller_receives_commit_outcome_unknown",
    "no_hidden_controller_retry",
    "retry_same_work_item",
    "retry_same_idempotency_key",
    "retry_same_canonical_command_digest",
    "same_or_new_valid_writer_session",
    "prior_commit_succeeded_exact_replay",
    "prior_commit_did_not_occur_normal_apply",
    "same_key_different_digest_idempotency_conflict",
    "exact_replay_skips_timestamp_context_evaluator_sequence_and_writes",
)
_B3C4B_REQUIRED_PROOF_MATRIX = (
    "sequence_0",
    "sequence_increment",
    "signed_max_overflow",
    "accepted_write_plan",
    "domain_rejected_write_plan",
    "exact_event_adapter_round_trip",
    "exact_work_item_adapter_round_trip",
    "replay_conflict_no_write_plan",
    "event_ref_collision",
    "sequence_collision",
    "idempotency_collision_after_miss",
    "insert_failure",
    "cas_rowcount_mismatch",
    "cas_sqlite_failure",
    "rollback_failure",
    "commit_uncertainty",
    "commit_succeeded_then_close_failed",
    "uncertainty_then_same_key_replay",
    "uncertainty_then_normal_apply",
    "crash_restart_committed_replay",
    "crash_restart_rolled_back_reapply",
    "no_partial_event_or_current_state_row",
    "process_thread_fork_capability_behavior",
    "public_method_later_delegates_only",
)
_B3C4C_PUBLIC_INTEGRATION_BOUNDARY = (
    "public_apply_enters_existing_operation_guard",
    "public_apply_delegates_to_one_private_atomic_entry",
    "public_apply_contains_no_sql",
    "public_apply_accepts_no_context_timestamp_capability",
    "public_apply_exposes_existing_apply_outcomes_and_errors",
    "apply_global_stop_update_unavailable_until_b4",
    "no_public_database_reader_or_store",
    "no_state_store_widening",
)
_B4_SEPARATION_CONTRACT = (
    "no_global_stop_event_insert",
    "no_global_stop_current_update",
    "no_operator_decision_mutation",
    "b4_remains_future_global_stop_persistence_tranche",
)
