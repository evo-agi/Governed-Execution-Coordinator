"""Private pure B4a global-stop write grammar contracts.

B4a freezes SQL shape, parameter builders, and planned global-stop write values
only. It deliberately does not open database handles, execute SQL, allocate
sequences from durable state, begin or commit transactions, provision decision
receipts, or change public writer-session behavior.
"""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field

from ge_nwp_coordinator.global_stop import (
    GLOBAL_STOP_SCHEMA_ID as _GLOBAL_STOP_SCHEMA_ID,
    GlobalStopAction as _GlobalStopAction,
    GlobalStopEvaluation as _GlobalStopEvaluation,
    GlobalStopEvaluationKind as _GlobalStopEvaluationKind,
    GlobalStopEvent as _GlobalStopEvent,
    GlobalStopEventOutcome as _GlobalStopEventOutcome,
    GlobalStopReasonClass as _GlobalStopReasonClass,
    GlobalStopState as _GlobalStopState,
    GlobalStopStatus as _GlobalStopStatus,
)
from ge_nwp_coordinator.persistence_contracts import (
    GLOBAL_STOP_CURRENT_ROW_COLUMNS as _GLOBAL_STOP_CURRENT_ROW_COLUMNS,
    GLOBAL_STOP_EVENT_ROW_COLUMNS as _GLOBAL_STOP_EVENT_ROW_COLUMNS,
    SQLITE_SIGNED_INT_MAX as _SQLITE_SIGNED_INT_MAX,
    encode_sqlite_boolean as _encode_sqlite_boolean,
    global_stop_current_envelope_from_row as _global_stop_current_envelope_from_row,
    global_stop_event_canonical_digest as _global_stop_event_canonical_digest,
    global_stop_event_canonical_json as _global_stop_event_canonical_json,
    global_stop_event_record_envelope_from_row as _global_stop_event_record_envelope_from_row,
    normalize_transaction_timestamp as _normalize_transaction_timestamp,
)
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError as _SQLiteMutationStoreError,
    SQLiteMutationStoreErrorCode as _SQLiteMutationStoreErrorCode,
)
from ge_nwp_coordinator.state_store import CommittedGlobalStopUpdate as _CommittedGlobalStopUpdate

__all__: tuple[str, ...] = ()

_GLOBAL_STOP_EVENTS_TABLE = "global_stop_events"
_GLOBAL_STOP_CURRENT_TABLE = "global_stop_current"
_GLOBAL_STOP_SINGLETON_ID = 1
_ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SET_COLUMNS = _GLOBAL_STOP_CURRENT_ROW_COLUMNS[1:]
_ACCEPTED_GLOBAL_STOP_CURRENT_CAS_WHERE_COLUMNS = ("singleton_id", "version")


@_dataclass(frozen=True, slots=True, repr=False)
class _GlobalStopEventInsertSpec:
    table_name: str
    columns: tuple[str, ...]
    sql: str
    parameter_count: int

    def __post_init__(self) -> None:
        if self.table_name != _GLOBAL_STOP_EVENTS_TABLE:
            raise ValueError("invalid_global_stop_event_insert_spec")
        if self.columns != _GLOBAL_STOP_EVENT_ROW_COLUMNS:
            raise ValueError("invalid_global_stop_event_insert_spec")
        if self.parameter_count != len(_GLOBAL_STOP_EVENT_ROW_COLUMNS) or self.parameter_count != 18:
            raise ValueError("invalid_global_stop_event_insert_spec")
        if self.sql != _global_stop_event_insert_sql(_GLOBAL_STOP_EVENT_ROW_COLUMNS):
            raise ValueError("invalid_global_stop_event_insert_spec")

    def __repr__(self) -> str:
        return "<_GlobalStopEventInsertSpec>"

    def __reduce__(self) -> object:
        raise TypeError("invalid global-stop write contract")


@_dataclass(frozen=True, slots=True, repr=False)
class _AcceptedGlobalStopCurrentCasSpec:
    table_name: str
    set_columns: tuple[str, ...]
    where_columns: tuple[str, ...]
    sql: str
    parameter_count: int

    def __post_init__(self) -> None:
        if self.table_name != _GLOBAL_STOP_CURRENT_TABLE:
            raise ValueError("invalid_accepted_global_stop_current_cas_spec")
        if self.set_columns != _ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SET_COLUMNS:
            raise ValueError("invalid_accepted_global_stop_current_cas_spec")
        if self.where_columns != _ACCEPTED_GLOBAL_STOP_CURRENT_CAS_WHERE_COLUMNS:
            raise ValueError("invalid_accepted_global_stop_current_cas_spec")
        if self.parameter_count != len(self.set_columns) + 1 or self.parameter_count != 10:
            raise ValueError("invalid_accepted_global_stop_current_cas_spec")
        if self.sql != _accepted_global_stop_current_cas_sql(
            set_columns=_ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SET_COLUMNS,
            where_columns=_ACCEPTED_GLOBAL_STOP_CURRENT_CAS_WHERE_COLUMNS,
        ):
            raise ValueError("invalid_accepted_global_stop_current_cas_spec")

    def __repr__(self) -> str:
        return "<_AcceptedGlobalStopCurrentCasSpec>"

    def __reduce__(self) -> object:
        raise TypeError("invalid global-stop write contract")


@_dataclass(frozen=True, slots=True, repr=False)
class _GlobalStopEventInsertValues:
    spec: _GlobalStopEventInsertSpec = _field(repr=False)
    parameters: tuple[object, ...] = _field(repr=False)
    event: _GlobalStopEvent = _field(repr=False)
    replay_state: _GlobalStopState = _field(repr=False)
    event_sequence: int
    created_at: str

    def __post_init__(self) -> None:
        def validate() -> None:
            _require_exact_event_insert_spec(self.spec)
            event = _require_initialized_global_stop_event(self.event)
            replay_state = _require_initialized_global_stop_state(self.replay_state)
            sequence = _require_event_sequence(self.event_sequence)
            created_at = _normalize_transaction_timestamp(self.created_at)
            expected = _expected_global_stop_event_insert_parameters(
                event=event,
                replay_state=replay_state,
                event_sequence=sequence,
                created_at=created_at,
            )
            _require_exact_parameter_tuple(self.parameters, expected, parameter_count=self.spec.parameter_count)
            row = dict(zip(self.spec.columns, expected, strict=True))
            envelope = _global_stop_event_record_envelope_from_row(row)
            if (
                envelope.event_sequence != sequence
                or envelope.event != event
                or envelope.replay_state != replay_state
                or envelope.created_at != created_at
            ):
                raise ValueError("invalid_global_stop_event_insert_values")
            object.__setattr__(self, "parameters", expected)
            object.__setattr__(self, "event", event)
            object.__setattr__(self, "replay_state", replay_state)
            object.__setattr__(self, "event_sequence", sequence)
            object.__setattr__(self, "created_at", created_at)

        _collapse_private_contract_failure(validate)

    def __repr__(self) -> str:
        return "<_GlobalStopEventInsertValues>"

    def __reduce__(self) -> object:
        raise TypeError("invalid global-stop write contract")


@_dataclass(frozen=True, slots=True, repr=False)
class _AcceptedGlobalStopCurrentCasValues:
    spec: _AcceptedGlobalStopCurrentCasSpec = _field(repr=False)
    parameters: tuple[object, ...] = _field(repr=False)
    source_state: _GlobalStopState = _field(repr=False)
    resulting_state: _GlobalStopState = _field(repr=False)
    updated_at: str

    def __post_init__(self) -> None:
        def validate() -> None:
            _require_exact_cas_spec(self.spec)
            source = _require_initialized_global_stop_state(self.source_state)
            resulting = _require_initialized_global_stop_state(self.resulting_state)
            updated_at = _normalize_transaction_timestamp(self.updated_at)
            expected = _expected_accepted_global_stop_current_cas_parameters(
                safe_source_state=source,
                safe_resulting_state=resulting,
                normalized_timestamp=updated_at,
            )
            _require_exact_parameter_tuple(self.parameters, expected, parameter_count=self.spec.parameter_count)
            row = _global_stop_current_row_for_adapter(resulting, updated_at)
            envelope = _global_stop_current_envelope_from_row(row)
            if envelope.state != resulting or envelope.updated_at != updated_at:
                raise ValueError("invalid_accepted_global_stop_current_cas_values")
            object.__setattr__(self, "parameters", expected)
            object.__setattr__(self, "source_state", source)
            object.__setattr__(self, "resulting_state", resulting)
            object.__setattr__(self, "updated_at", updated_at)

        _collapse_private_contract_failure(validate)

    def __repr__(self) -> str:
        return "<_AcceptedGlobalStopCurrentCasValues>"

    def __reduce__(self) -> object:
        raise TypeError("invalid global-stop write contract")


@_dataclass(frozen=True, slots=True, repr=False)
class _GlobalStopWritePlan:
    planned_update: _CommittedGlobalStopUpdate = _field(repr=False)
    event_insert: _GlobalStopEventInsertValues = _field(repr=False)
    accepted_global_stop_current_cas: _AcceptedGlobalStopCurrentCasValues | None = _field(default=None, repr=False)

    def __post_init__(self) -> None:
        def validate() -> None:
            planned = _require_planned_global_stop_update(self.planned_update)
            event_insert = _require_exact_event_insert_values(self.event_insert)
            if planned.event != event_insert.event or planned.state != event_insert.replay_state:
                raise ValueError("invalid_global_stop_write_plan")
            if planned.event.outcome is _GlobalStopEventOutcome.ACCEPTED:
                cas = _require_exact_cas_values(self.accepted_global_stop_current_cas)
                if cas.resulting_state != planned.state or event_insert.created_at != cas.updated_at:
                    raise ValueError("invalid_global_stop_write_plan")
                _require_source_state_matches_event(cas.source_state, planned.event)
                object.__setattr__(self, "planned_update", planned)
                object.__setattr__(self, "event_insert", event_insert)
                object.__setattr__(self, "accepted_global_stop_current_cas", cas)
                return
            if planned.event.outcome is _GlobalStopEventOutcome.DOMAIN_REJECTED:
                if self.accepted_global_stop_current_cas is not None:
                    raise ValueError("invalid_global_stop_write_plan")
                _require_domain_rejected_event(planned.event, planned.state)
                object.__setattr__(self, "planned_update", planned)
                object.__setattr__(self, "event_insert", event_insert)
                object.__setattr__(self, "accepted_global_stop_current_cas", None)
                return
            raise ValueError("invalid_global_stop_write_plan")

        _collapse_private_contract_failure(validate)

    def __repr__(self) -> str:
        return "<_GlobalStopWritePlan planned_not_committed>"

    def __reduce__(self) -> object:
        raise TypeError("invalid global-stop write contract")


def _global_stop_event_insert_values(
    evaluation: _GlobalStopEvaluation,
    event_sequence: int,
    transaction_timestamp: str,
) -> _GlobalStopEventInsertValues:
    def build() -> _GlobalStopEventInsertValues:
        checked = _require_write_evaluation(evaluation)
        event = checked.event
        replay_state = checked.state
        if type(event) is not _GlobalStopEvent:
            raise ValueError("invalid_global_stop_event")
        sequence = _require_event_sequence(event_sequence)
        created_at = _normalize_transaction_timestamp(transaction_timestamp)
        parameters = _expected_global_stop_event_insert_parameters(
            event=event,
            replay_state=replay_state,
            event_sequence=sequence,
            created_at=created_at,
        )
        return _GlobalStopEventInsertValues(
            spec=_GLOBAL_STOP_EVENT_INSERT_SPEC,
            parameters=parameters,
            event=event,
            replay_state=replay_state,
            event_sequence=sequence,
            created_at=created_at,
        )

    return _collapse_private_contract_failure(build)


def _accepted_global_stop_current_cas_values(
    source_state: _GlobalStopState,
    resulting_state: _GlobalStopState,
    transaction_timestamp: str,
) -> _AcceptedGlobalStopCurrentCasValues:
    def build() -> _AcceptedGlobalStopCurrentCasValues:
        source = _require_initialized_global_stop_state(source_state)
        resulting = _require_initialized_global_stop_state(resulting_state)
        updated_at = _normalize_transaction_timestamp(transaction_timestamp)
        parameters = _expected_accepted_global_stop_current_cas_parameters(
            safe_source_state=source,
            safe_resulting_state=resulting,
            normalized_timestamp=updated_at,
        )
        return _AcceptedGlobalStopCurrentCasValues(
            spec=_ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SPEC,
            parameters=parameters,
            source_state=source,
            resulting_state=resulting,
            updated_at=updated_at,
        )

    return _collapse_private_contract_failure(build)


def _global_stop_write_plan(
    evaluation: _GlobalStopEvaluation,
    *,
    source_state: _GlobalStopState,
    event_sequence: int,
    transaction_timestamp: str,
) -> _GlobalStopWritePlan:
    def build() -> _GlobalStopWritePlan:
        checked = _require_write_evaluation(evaluation)
        source = _require_initialized_global_stop_state(source_state)
        event = checked.event
        if type(event) is not _GlobalStopEvent:
            raise ValueError("invalid_global_stop_event")
        _require_source_state_matches_event(source, event)
        event_insert = _global_stop_event_insert_values(checked, event_sequence, transaction_timestamp)
        planned_update = _CommittedGlobalStopUpdate(state=checked.state, event=event, replayed=False)
        if checked.kind is _GlobalStopEvaluationKind.ACCEPTED:
            cas = _accepted_global_stop_current_cas_values(source, checked.state, transaction_timestamp)
        elif checked.kind is _GlobalStopEvaluationKind.DOMAIN_REJECTED:
            if checked.state != source:
                raise ValueError("invalid_domain_rejected_global_stop_state")
            cas = None
        else:
            raise ValueError("invalid_global_stop_evaluation")
        return _GlobalStopWritePlan(
            planned_update=planned_update,
            event_insert=event_insert,
            accepted_global_stop_current_cas=cas,
        )

    return _collapse_private_contract_failure(build)


def _global_stop_event_insert_sql(columns: tuple[str, ...]) -> str:
    if columns != _GLOBAL_STOP_EVENT_ROW_COLUMNS:
        raise ValueError("invalid_global_stop_event_insert_columns")
    return (
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


def _accepted_global_stop_current_cas_sql(
    *,
    set_columns: tuple[str, ...],
    where_columns: tuple[str, ...],
) -> str:
    if (
        set_columns != _ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SET_COLUMNS
        or where_columns != _ACCEPTED_GLOBAL_STOP_CURRENT_CAS_WHERE_COLUMNS
    ):
        raise ValueError("invalid_accepted_global_stop_current_cas_columns")
    return (
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


def _require_write_evaluation(evaluation: _GlobalStopEvaluation) -> _GlobalStopEvaluation:
    def validate() -> _GlobalStopEvaluation:
        checked = _require_initialized_global_stop_evaluation(evaluation)
        kind = checked.kind
        if type(kind) is not _GlobalStopEvaluationKind:
            raise ValueError("invalid_global_stop_evaluation")
        if kind is _GlobalStopEvaluationKind.PRE_APPLY_INVALID:
            raise ValueError("invalid_global_stop_evaluation")
        if kind is not _GlobalStopEvaluationKind.ACCEPTED and kind is not _GlobalStopEvaluationKind.DOMAIN_REJECTED:
            raise ValueError("invalid_global_stop_evaluation")
        state = _require_initialized_global_stop_state(checked.state)
        event = _require_initialized_global_stop_event(checked.event)
        if kind.value != event.outcome.value or checked.reason != event.reason:
            raise ValueError("invalid_global_stop_evaluation")
        if state.version != event.resulting_version:
            raise ValueError("invalid_global_stop_evaluation")
        if state.stop_ref != event.resulting_global_stop_ref or state.status is not event.resulting_status:
            raise ValueError("invalid_global_stop_evaluation")
        return _GlobalStopEvaluation(kind=kind, reason=checked.reason, state=state, event=event)

    return _collapse_private_contract_failure(validate)


def _expected_global_stop_event_insert_parameters(
    *,
    event: _GlobalStopEvent,
    replay_state: _GlobalStopState,
    event_sequence: int,
    created_at: str,
) -> tuple[object, ...]:
    return (
        event.event_ref,
        event_sequence,
        event.idempotency_key,
        event.command_digest,
        event.action.value,
        event.source_version,
        event.resulting_version,
        event.outcome.value,
        event.reason,
        event.operator_decision_ref,
        event.resulting_global_stop_ref,
        event.resulting_status.value,
        event.schema_id,
        _global_stop_event_canonical_json(event),
        _global_stop_event_canonical_digest(event),
        replay_state.canonical_json(),
        replay_state.canonical_digest(),
        created_at,
    )


def _expected_accepted_global_stop_current_cas_parameters(
    *,
    safe_source_state: _GlobalStopState,
    safe_resulting_state: _GlobalStopState,
    normalized_timestamp: str,
) -> tuple[object, ...]:
    _require_accepted_cas_states(safe_source_state, safe_resulting_state)
    return (
        safe_resulting_state.schema_id,
        safe_resulting_state.version,
        _encode_sqlite_boolean(safe_resulting_state.active, "accepted_global_stop_current_cas.active"),
        safe_resulting_state.stop_id,
        safe_resulting_state.reason_class.value if safe_resulting_state.reason_class is not None else None,
        safe_resulting_state.issuer_ref,
        safe_resulting_state.issued_at,
        safe_resulting_state.operator_decision_ref,
        normalized_timestamp,
        safe_source_state.version,
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


def _require_accepted_cas_states(source: _GlobalStopState, resulting: _GlobalStopState) -> None:
    if source.schema_id != _GLOBAL_STOP_SCHEMA_ID or resulting.schema_id != _GLOBAL_STOP_SCHEMA_ID:
        raise _database_integrity_failure()
    if resulting.version != source.version + 1:
        raise _database_integrity_failure()


def _require_source_state_matches_event(source: _GlobalStopState, event: _GlobalStopEvent) -> None:
    if source.version != event.source_version:
        raise _database_integrity_failure()


def _require_domain_rejected_event(event: _GlobalStopEvent, state: _GlobalStopState) -> None:
    if event.resulting_version != event.source_version:
        raise _database_integrity_failure()
    if state.version != event.source_version:
        raise _database_integrity_failure()


def _global_stop_current_row_for_adapter(state: _GlobalStopState, updated_at: str) -> dict[str, object]:
    return {
        "singleton_id": _GLOBAL_STOP_SINGLETON_ID,
        "schema_id": state.schema_id,
        "version": state.version,
        "active": _encode_sqlite_boolean(state.active, "global_stop_current.active"),
        "stop_id": state.stop_id,
        "reason_class": state.reason_class.value if state.reason_class is not None else None,
        "issuer_ref": state.issuer_ref,
        "issued_at": state.issued_at,
        "operator_decision_ref": state.operator_decision_ref,
        "updated_at": updated_at,
    }


def _require_event_sequence(value: int) -> int:
    if type(value) is not int or value < 0 or value > _SQLITE_SIGNED_INT_MAX:
        raise _database_integrity_failure()
    return value


def _require_initialized_global_stop_evaluation(value: object) -> _GlobalStopEvaluation:
    def reconstruct() -> _GlobalStopEvaluation:
        if type(value) is not _GlobalStopEvaluation:
            raise ValueError("invalid_global_stop_evaluation")
        event = object.__getattribute__(value, "event")
        if event is not None:
            event = _require_initialized_global_stop_event(event)
        return _GlobalStopEvaluation(
            kind=object.__getattribute__(value, "kind"),
            state=_require_initialized_global_stop_state(object.__getattribute__(value, "state")),
            event=event,
            reason=object.__getattribute__(value, "reason"),
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_global_stop_event(value: object) -> _GlobalStopEvent:
    def reconstruct() -> _GlobalStopEvent:
        if type(value) is not _GlobalStopEvent:
            raise ValueError("invalid_global_stop_event")
        action = object.__getattribute__(value, "action")
        outcome = object.__getattribute__(value, "outcome")
        status = object.__getattribute__(value, "resulting_status")
        if type(action) is not _GlobalStopAction:
            raise ValueError("invalid_global_stop_event")
        if type(outcome) is not _GlobalStopEventOutcome:
            raise ValueError("invalid_global_stop_event")
        if type(status) is not _GlobalStopStatus:
            raise ValueError("invalid_global_stop_event")
        return _GlobalStopEvent(
            schema_id=object.__getattribute__(value, "schema_id"),
            event_ref=object.__getattribute__(value, "event_ref"),
            command_digest=object.__getattribute__(value, "command_digest"),
            idempotency_key=object.__getattribute__(value, "idempotency_key"),
            action=action,
            source_version=object.__getattribute__(value, "source_version"),
            resulting_version=object.__getattribute__(value, "resulting_version"),
            outcome=outcome,
            reason=object.__getattribute__(value, "reason"),
            operator_decision_ref=object.__getattribute__(value, "operator_decision_ref"),
            resulting_global_stop_ref=object.__getattribute__(value, "resulting_global_stop_ref"),
            resulting_status=status,
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_global_stop_state(value: object) -> _GlobalStopState:
    def reconstruct() -> _GlobalStopState:
        if type(value) is not _GlobalStopState:
            raise ValueError("invalid_global_stop_state")
        reason_class = object.__getattribute__(value, "reason_class")
        if reason_class is not None and type(reason_class) is not _GlobalStopReasonClass:
            raise ValueError("invalid_global_stop_state")
        return _GlobalStopState(
            schema_id=object.__getattribute__(value, "schema_id"),
            version=object.__getattribute__(value, "version"),
            active=object.__getattribute__(value, "active"),
            stop_id=object.__getattribute__(value, "stop_id"),
            reason_class=reason_class,
            issuer_ref=object.__getattribute__(value, "issuer_ref"),
            issued_at=object.__getattribute__(value, "issued_at"),
            operator_decision_ref=object.__getattribute__(value, "operator_decision_ref"),
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_exact_event_insert_spec(value: object) -> _GlobalStopEventInsertSpec:
    if type(value) is not _GlobalStopEventInsertSpec or value is not _GLOBAL_STOP_EVENT_INSERT_SPEC:
        raise _database_integrity_failure()
    return value


def _require_exact_cas_spec(value: object) -> _AcceptedGlobalStopCurrentCasSpec:
    if type(value) is not _AcceptedGlobalStopCurrentCasSpec or value is not _ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SPEC:
        raise _database_integrity_failure()
    return value


def _require_exact_event_insert_values(value: object) -> _GlobalStopEventInsertValues:
    def reconstruct() -> _GlobalStopEventInsertValues:
        if type(value) is not _GlobalStopEventInsertValues:
            raise ValueError("invalid_global_stop_event_insert_values")
        return _GlobalStopEventInsertValues(
            spec=value.spec,
            parameters=value.parameters,
            event=value.event,
            replay_state=value.replay_state,
            event_sequence=value.event_sequence,
            created_at=value.created_at,
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_exact_cas_values(value: object) -> _AcceptedGlobalStopCurrentCasValues:
    def reconstruct() -> _AcceptedGlobalStopCurrentCasValues:
        if type(value) is not _AcceptedGlobalStopCurrentCasValues:
            raise ValueError("invalid_accepted_global_stop_current_cas_values")
        return _AcceptedGlobalStopCurrentCasValues(
            spec=value.spec,
            parameters=value.parameters,
            source_state=value.source_state,
            resulting_state=value.resulting_state,
            updated_at=value.updated_at,
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_planned_global_stop_update(value: object) -> _CommittedGlobalStopUpdate:
    def reconstruct() -> _CommittedGlobalStopUpdate:
        if type(value) is not _CommittedGlobalStopUpdate:
            raise ValueError("invalid_planned_global_stop_update")
        checked = _CommittedGlobalStopUpdate(
            state=_require_initialized_global_stop_state(value.state),
            event=_require_initialized_global_stop_event(value.event),
            replayed=object.__getattribute__(value, "replayed"),
        )
        if checked.replayed is not False:
            raise ValueError("invalid_planned_global_stop_update")
        return checked

    return _collapse_private_contract_failure(reconstruct)


def _collapse_private_contract_failure(callback):
    ordinary_failure = False
    try:
        return callback()
    except _SQLiteMutationStoreError:
        raise
    except Exception:
        ordinary_failure = True
    if ordinary_failure:
        raise _database_integrity_failure()
    raise _database_integrity_failure()


def _database_integrity_failure() -> _SQLiteMutationStoreError:
    return _SQLiteMutationStoreError(_SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


_GLOBAL_STOP_EVENT_INSERT_SPEC = _GlobalStopEventInsertSpec(
    table_name=_GLOBAL_STOP_EVENTS_TABLE,
    columns=_GLOBAL_STOP_EVENT_ROW_COLUMNS,
    sql=_global_stop_event_insert_sql(_GLOBAL_STOP_EVENT_ROW_COLUMNS),
    parameter_count=18,
)
_ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SPEC = _AcceptedGlobalStopCurrentCasSpec(
    table_name=_GLOBAL_STOP_CURRENT_TABLE,
    set_columns=_ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SET_COLUMNS,
    where_columns=_ACCEPTED_GLOBAL_STOP_CURRENT_CAS_WHERE_COLUMNS,
    sql=_accepted_global_stop_current_cas_sql(
        set_columns=_ACCEPTED_GLOBAL_STOP_CURRENT_CAS_SET_COLUMNS,
        where_columns=_ACCEPTED_GLOBAL_STOP_CURRENT_CAS_WHERE_COLUMNS,
    ),
    parameter_count=10,
)

_B4A_GLOBAL_STOP_WRITE_GRAMMAR_NON_CLAIMS = (
    "no_receipt_insert_sql",
    "no_write_execution_method",
    "no_begin_commit_rollback",
    "no_public_global_stop_delegation",
    "table_local_global_stop_event_sequence",
)
