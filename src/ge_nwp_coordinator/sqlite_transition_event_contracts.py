"""Private B3c0b transition-event SQL contract data."""

from __future__ import annotations

from dataclasses import dataclass

from ge_nwp_coordinator.persistence_contracts import TRANSITION_EVENT_ROW_COLUMNS

_SAFE_SQL_IDENTIFIER_FIRST_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz")
_SAFE_SQL_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")


@dataclass(frozen=True, slots=True)
class _TransitionEventIdempotencyQuerySpec:
    query_id: str
    table_name: str
    columns: tuple[str, ...]
    lookup_columns: tuple[str, str]
    sql: str

    def __post_init__(self) -> None:
        _require_safe_identifier(self.query_id, "query_id")
        _require_safe_identifier(self.table_name, "table_name")
        _require_safe_columns(self.columns)
        if type(self.lookup_columns) is not tuple or len(self.lookup_columns) != 2:
            raise ValueError("invalid_lookup_columns")
        for lookup_column in self.lookup_columns:
            _require_safe_identifier(lookup_column, "lookup_column")
            if lookup_column not in self.columns:
                raise ValueError("lookup_column_not_selected")
        expected_sql = _idempotency_lookup_sql(
            table_name=self.table_name,
            columns=self.columns,
            lookup_columns=self.lookup_columns,
        )
        if self.sql != expected_sql:
            raise ValueError("invalid_transition_event_idempotency_query_spec")


@dataclass(frozen=True, slots=True)
class _TransitionEventMaxSequenceQuerySpec:
    query_id: str
    table_name: str
    sequence_column: str
    sql: str

    def __post_init__(self) -> None:
        _require_safe_identifier(self.query_id, "query_id")
        _require_safe_identifier(self.table_name, "table_name")
        _require_safe_identifier(self.sequence_column, "sequence_column")
        expected_sql = _max_sequence_sql(table_name=self.table_name, sequence_column=self.sequence_column)
        if self.sql != expected_sql:
            raise ValueError("invalid_transition_event_max_sequence_query_spec")


def _idempotency_lookup_sql(
    *,
    table_name: str,
    columns: tuple[str, ...],
    lookup_columns: tuple[str, str],
) -> str:
    _require_safe_identifier(table_name, "table_name")
    _require_safe_columns(columns)
    for lookup_column in lookup_columns:
        _require_safe_identifier(lookup_column, "lookup_column")
    return (
        f"SELECT {', '.join(columns)}\n"
        f"FROM {table_name}\n"
        f"WHERE {lookup_columns[0]} = ? AND {lookup_columns[1]} = ?\n"
        "LIMIT 2"
    )


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


_TRANSITION_EVENT_IDEMPOTENCY_LOOKUP_SELECT = _TransitionEventIdempotencyQuerySpec(
    query_id="transition_event_idempotency_lookup",
    table_name="transition_events",
    columns=TRANSITION_EVENT_ROW_COLUMNS,
    lookup_columns=("work_item_id", "idempotency_key"),
    sql=_idempotency_lookup_sql(
        table_name="transition_events",
        columns=TRANSITION_EVENT_ROW_COLUMNS,
        lookup_columns=("work_item_id", "idempotency_key"),
    ),
)
_TRANSITION_EVENT_MAX_SEQUENCE_SELECT = _TransitionEventMaxSequenceQuerySpec(
    query_id="transition_event_max_sequence",
    table_name="transition_events",
    sequence_column="event_sequence",
    sql=_max_sequence_sql(table_name="transition_events", sequence_column="event_sequence"),
)

_B3C0B_TRANSITION_EVENT_QUERY_SPECS = (
    _TRANSITION_EVENT_IDEMPOTENCY_LOOKUP_SELECT,
    _TRANSITION_EVENT_MAX_SEQUENCE_SELECT,
)
