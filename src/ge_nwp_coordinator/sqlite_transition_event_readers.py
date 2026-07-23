"""Private B3c2 transition-event SELECT readers."""

from __future__ import annotations

from typing import Any

from ge_nwp_coordinator.models import require_contract_ref
from ge_nwp_coordinator.persistence_contracts import (
    SQLITE_SIGNED_INT_MAX,
    TRANSITION_EVENT_ROW_COLUMNS,
    TransitionEventRecordEnvelope,
    transition_event_record_envelope_from_row,
)
from ge_nwp_coordinator.sqlite_transition_event_contracts import (
    _TRANSITION_EVENT_IDEMPOTENCY_LOOKUP_SELECT,
    _TRANSITION_EVENT_MAX_SEQUENCE_SELECT,
)
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _MutationReadCapability,
    _database_integrity_failure,
    _execute_select_fetch_two,
    _row_tuple_to_private_mapping,
)
from ge_nwp_coordinator.state_machine import TransitionEvent


def _read_transition_event_for_idempotency(
    capability: _MutationReadCapability,
    work_item_id: str,
    idempotency_key: str,
) -> TransitionEventRecordEnvelope | None:
    _require_exact_lookup_ref_type(
        work_item_id,
        "transition_event_idempotency.work_item_id",
    )
    _require_exact_lookup_ref_type(
        idempotency_key,
        "transition_event_idempotency.idempotency_key",
    )
    validated_work_item_id = require_contract_ref(
        work_item_id,
        "transition_event_idempotency.work_item_id",
    )
    validated_idempotency_key = require_contract_ref(
        idempotency_key,
        "transition_event_idempotency.idempotency_key",
    )
    rows = _execute_select_fetch_two(
        capability=capability,
        sql=_TRANSITION_EVENT_IDEMPOTENCY_LOOKUP_SELECT.sql,
        parameters=(validated_work_item_id, validated_idempotency_key),
    )
    if len(rows) == 0:
        return None
    if len(rows) != 1:
        raise _database_integrity_failure()

    row = rows[0]
    mapping = _row_tuple_to_private_mapping(TRANSITION_EVENT_ROW_COLUMNS, row)
    del row
    del rows
    envelope = transition_event_record_envelope_from_row(mapping)
    if type(envelope) is not TransitionEventRecordEnvelope:
        raise _database_integrity_failure()
    event = envelope.event
    if type(event) is not TransitionEvent:
        raise _database_integrity_failure()
    if event.work_item_id != validated_work_item_id or event.idempotency_key != validated_idempotency_key:
        raise _database_integrity_failure()
    return envelope


def _read_transition_event_max_sequence(
    capability: _MutationReadCapability,
) -> int | None:
    rows = _execute_select_fetch_two(
        capability=capability,
        sql=_TRANSITION_EVENT_MAX_SEQUENCE_SELECT.sql,
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


def _require_exact_lookup_ref_type(value: object, field_name: str) -> None:
    if type(value) is not str:
        raise ValueError(f"invalid_field_type:{field_name}") from None
