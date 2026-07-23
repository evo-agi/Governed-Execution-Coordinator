"""Private B4a global-stop transaction-internal SELECT readers."""

from __future__ import annotations

from typing import Any, Callable, Mapping, TypeVar

from ge_nwp_coordinator.models import require_contract_ref
from ge_nwp_coordinator.persistence_contracts import (
    GLOBAL_STOP_CURRENT_ROW_COLUMNS,
    GLOBAL_STOP_EVENT_ROW_COLUMNS,
    GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS,
    SQLITE_SIGNED_INT_MAX,
    GlobalStopCurrentRecordEnvelope,
    GlobalStopEventRecordEnvelope,
    GlobalStopOperatorDecisionReceiptEnvelope,
    global_stop_current_envelope_from_row,
    global_stop_event_record_envelope_from_row,
    global_stop_operator_decision_receipt_envelope_from_row,
)
from ge_nwp_coordinator.sqlite_global_stop_event_contracts import (
    _GLOBAL_STOP_CURRENT_SELECT,
    _GLOBAL_STOP_EVENT_IDEMPOTENCY_LOOKUP_SELECT,
    _GLOBAL_STOP_EVENT_MAX_SEQUENCE_SELECT,
    _GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_SELECT,
    _GLOBAL_STOP_SINGLETON_ID,
)
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _TransitionReadCapability,
    _database_integrity_failure,
    _execute_select_fetch_two,
    _row_tuple_to_private_mapping,
)

_EnvelopeT = TypeVar("_EnvelopeT")


def _read_global_stop_operator_decision_receipt(
    capability: _TransitionReadCapability,
    decision_ref: str,
) -> GlobalStopOperatorDecisionReceiptEnvelope | None:
    _require_exact_lookup_ref_type(decision_ref, "global_stop_receipt.decision_ref")
    validated_ref = require_contract_ref(decision_ref, "global_stop_receipt.decision_ref")
    envelope = _read_optional_global_stop_row(
        capability=capability,
        sql=_GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_SELECT.sql,
        parameters=(validated_ref,),
        columns=GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS,
        adapter=global_stop_operator_decision_receipt_envelope_from_row,
    )
    if envelope is None:
        return None
    if type(envelope) is not GlobalStopOperatorDecisionReceiptEnvelope:
        raise _database_integrity_failure()
    if envelope.decision.decision_ref != validated_ref:
        raise _database_integrity_failure()
    return envelope


def _read_global_stop_event_for_idempotency(
    capability: _TransitionReadCapability,
    idempotency_key: str,
) -> GlobalStopEventRecordEnvelope | None:
    _require_exact_lookup_ref_type(idempotency_key, "global_stop_event_idempotency.idempotency_key")
    validated_key = require_contract_ref(idempotency_key, "global_stop_event_idempotency.idempotency_key")
    envelope = _read_optional_global_stop_row(
        capability=capability,
        sql=_GLOBAL_STOP_EVENT_IDEMPOTENCY_LOOKUP_SELECT.sql,
        parameters=(validated_key,),
        columns=GLOBAL_STOP_EVENT_ROW_COLUMNS,
        adapter=global_stop_event_record_envelope_from_row,
    )
    if envelope is None:
        return None
    if type(envelope) is not GlobalStopEventRecordEnvelope:
        raise _database_integrity_failure()
    if envelope.event.idempotency_key != validated_key:
        raise _database_integrity_failure()
    return envelope


def _read_global_stop_event_max_sequence(capability: _TransitionReadCapability) -> int | None:
    rows = _execute_select_fetch_two(
        capability=capability,
        sql=_GLOBAL_STOP_EVENT_MAX_SEQUENCE_SELECT.sql,
        parameters=(),
    )
    if len(rows) != 1:
        raise _database_integrity_failure()
    row = rows[0]
    if type(row) is not tuple or len(row) != 1:
        raise _database_integrity_failure()
    value: Any = row[0]
    if value is None:
        return None
    if type(value) is not int:
        raise _database_integrity_failure()
    if value < 0 or value > SQLITE_SIGNED_INT_MAX:
        raise _database_integrity_failure()
    return value


def _read_global_stop_current(capability: _TransitionReadCapability) -> GlobalStopCurrentRecordEnvelope:
    envelope = _read_optional_global_stop_row(
        capability=capability,
        sql=_GLOBAL_STOP_CURRENT_SELECT.sql,
        parameters=(_GLOBAL_STOP_SINGLETON_ID,),
        columns=GLOBAL_STOP_CURRENT_ROW_COLUMNS,
        adapter=global_stop_current_envelope_from_row,
    )
    if type(envelope) is not GlobalStopCurrentRecordEnvelope:
        raise _database_integrity_failure()
    return envelope


def _read_optional_global_stop_row(
    *,
    capability: _TransitionReadCapability,
    sql: str,
    parameters: tuple[object, ...],
    columns: tuple[str, ...],
    adapter: Callable[[Mapping[str, Any]], _EnvelopeT],
) -> _EnvelopeT | None:
    rows = _execute_select_fetch_two(capability=capability, sql=sql, parameters=parameters)
    if len(rows) == 0:
        return None
    if len(rows) != 1:
        raise _database_integrity_failure()
    row = rows[0]
    row_mapping = _row_tuple_to_private_mapping(columns, row)
    del row
    del rows
    return adapter(row_mapping)


def _require_exact_lookup_ref_type(value: object, field_name: str) -> None:
    if type(value) is not str:
        raise ValueError(f"invalid_field_type:{field_name}") from None
