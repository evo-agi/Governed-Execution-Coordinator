"""Private immutable B4a global-stop SELECT query specifications."""

from __future__ import annotations

from dataclasses import dataclass

from ge_nwp_coordinator.persistence_contracts import (
    GLOBAL_STOP_CURRENT_ROW_COLUMNS,
    GLOBAL_STOP_EVENT_ROW_COLUMNS,
    GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS,
)

_SAFE_SQL_IDENTIFIER_FIRST_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz")
_SAFE_SQL_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_GLOBAL_STOP_SINGLETON_ID = 1


@dataclass(frozen=True, slots=True)
class _GlobalStopSelectQuerySpec:
    query_id: str
    table_name: str
    columns: tuple[str, ...]
    lookup_column: str
    sql: str

    def __post_init__(self) -> None:
        _require_safe_identifier(self.query_id, "query_id")
        _require_safe_identifier(self.table_name, "table_name")
        _require_safe_identifier(self.lookup_column, "lookup_column")
        _require_safe_columns(self.columns)
        if self.lookup_column not in self.columns:
            raise ValueError("lookup_column_not_selected")
        expected_sql = _select_one_sql(
            table_name=self.table_name,
            columns=self.columns,
            lookup_column=self.lookup_column,
        )
        if self.sql != expected_sql:
            raise ValueError("invalid_global_stop_select_query_spec")


@dataclass(frozen=True, slots=True)
class _GlobalStopMaxSequenceQuerySpec:
    query_id: str
    table_name: str
    sequence_column: str
    sql: str

    def __post_init__(self) -> None:
        _require_safe_identifier(self.query_id, "query_id")
        _require_safe_identifier(self.table_name, "table_name")
        _require_safe_identifier(self.sequence_column, "sequence_column")
        if self.sql != _max_sequence_sql(table_name=self.table_name, sequence_column=self.sequence_column):
            raise ValueError("invalid_global_stop_max_sequence_query_spec")


def _select_one_sql(*, table_name: str, columns: tuple[str, ...], lookup_column: str) -> str:
    _require_safe_identifier(table_name, "table_name")
    _require_safe_identifier(lookup_column, "lookup_column")
    _require_safe_columns(columns)
    return f"SELECT {', '.join(columns)}\nFROM {table_name}\nWHERE {lookup_column} = ?\nLIMIT 2"


def _max_sequence_sql(*, table_name: str, sequence_column: str) -> str:
    _require_safe_identifier(table_name, "table_name")
    _require_safe_identifier(sequence_column, "sequence_column")
    return f"SELECT MAX({sequence_column})\nFROM {table_name}"


def _require_safe_columns(columns: tuple[str, ...]) -> None:
    if type(columns) is not tuple or not columns:
        raise ValueError("invalid_columns")
    seen: set[str] = set()
    for column in columns:
        _require_safe_identifier(column, "column")
        if column in seen:
            raise ValueError("duplicate_column")
        seen.add(column)


def _require_safe_identifier(value: str, field_name: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"invalid_identifier:{field_name}")
    if value[0] not in _SAFE_SQL_IDENTIFIER_FIRST_CHARS:
        raise ValueError(f"invalid_identifier:{field_name}")
    if any(character not in _SAFE_SQL_IDENTIFIER_CHARS for character in value):
        raise ValueError(f"invalid_identifier:{field_name}")


_GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_SELECT = _GlobalStopSelectQuerySpec(
    query_id="global_stop_operator_decision_receipt",
    table_name="global_stop_operator_decision_receipts",
    columns=GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS,
    lookup_column="decision_ref",
    sql=_select_one_sql(
        table_name="global_stop_operator_decision_receipts",
        columns=GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS,
        lookup_column="decision_ref",
    ),
)
_GLOBAL_STOP_EVENT_IDEMPOTENCY_LOOKUP_SELECT = _GlobalStopSelectQuerySpec(
    query_id="global_stop_event_idempotency_lookup",
    table_name="global_stop_events",
    columns=GLOBAL_STOP_EVENT_ROW_COLUMNS,
    lookup_column="idempotency_key",
    sql=_select_one_sql(
        table_name="global_stop_events",
        columns=GLOBAL_STOP_EVENT_ROW_COLUMNS,
        lookup_column="idempotency_key",
    ),
)
_GLOBAL_STOP_EVENT_MAX_SEQUENCE_SELECT = _GlobalStopMaxSequenceQuerySpec(
    query_id="global_stop_event_max_sequence",
    table_name="global_stop_events",
    sequence_column="event_sequence",
    sql=_max_sequence_sql(table_name="global_stop_events", sequence_column="event_sequence"),
)
_GLOBAL_STOP_CURRENT_SELECT = _GlobalStopSelectQuerySpec(
    query_id="global_stop_current",
    table_name="global_stop_current",
    columns=GLOBAL_STOP_CURRENT_ROW_COLUMNS,
    lookup_column="singleton_id",
    sql=_select_one_sql(
        table_name="global_stop_current",
        columns=GLOBAL_STOP_CURRENT_ROW_COLUMNS,
        lookup_column="singleton_id",
    ),
)

_B4A_GLOBAL_STOP_QUERY_SPECS = (
    _GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_SELECT,
    _GLOBAL_STOP_EVENT_IDEMPOTENCY_LOOKUP_SELECT,
    _GLOBAL_STOP_EVENT_MAX_SEQUENCE_SELECT,
    _GLOBAL_STOP_CURRENT_SELECT,
)
