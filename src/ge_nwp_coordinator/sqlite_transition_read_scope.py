"""Private B3b2a transition-read capability and immutable SELECT contracts.

B3b2a defines data-only query specifications and a private protocol for a
future B3c-managed transaction capability. It does not implement concrete
transaction authority, execute SQL, create cursors, fetch rows, map rows, invoke
row adapters, or own connection lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import sqlite3
from typing import Protocol

from ge_nwp_coordinator.persistence_contracts import (
    ADMITTED_BACKLOG_ROW_COLUMNS,
    AUTHORIZATION_RECEIPT_ROW_COLUMNS,
    DEPENDENCY_RECEIPT_ROW_COLUMNS,
    GLOBAL_STOP_CURRENT_ROW_COLUMNS,
    LEASE_IDENTITY_RECORD_ROW_COLUMNS,
    WORK_ITEM_ROW_COLUMNS,
)

_SAFE_SQL_IDENTIFIER_FIRST_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz")
_SAFE_SQL_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")


class _TransitionReadCapabilityFailureReason(str, Enum):
    CAPABILITY_UNAVAILABLE = "transition_read_capability_unavailable"
    CAPABILITY_EXPIRED = "transition_read_capability_expired"
    PROCESS_MISMATCH = "process_mismatch"
    THREAD_MISMATCH = "thread_mismatch"


class _TransitionReadCapabilityError(RuntimeError):
    """Safe private B3b2a capability failure with no connection details."""

    def __init__(self, reason: _TransitionReadCapabilityFailureReason | str) -> None:
        normalized = _TransitionReadCapabilityFailureReason(reason)
        self.reason = normalized
        super().__init__(normalized.value)


@dataclass(frozen=True, slots=True)
class _SelectQuerySpec:
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
        expected_sql = _select_sql(
            table_name=self.table_name,
            columns=self.columns,
            lookup_column=self.lookup_column,
        )
        if self.sql != expected_sql:
            raise ValueError("invalid_select_query_spec")


class _TransitionReadCapability(Protocol):
    """Private future-B3c transaction capability protocol.

    This protocol is not public authority and has no concrete B3b2a
    implementation. Future B3c must create any implementation only after the B2
    operation guard is active, after `BEGIN IMMEDIATE`, and after writer fencing
    required by final apply ordering. A concrete implementation must bind one
    opaque transaction epoch, invalidate before commit or rollback, never change
    or disclose that epoch, reject use after transaction end or restart on the
    same connection, reject process/thread mismatch, expose no connection
    property, and open, close, commit, or roll back nothing through this reader
    interface. `connection.in_transaction` is not transaction identity.
    """

    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        """Return the B3c-owned transaction connection for future B3b2b SELECTs."""
        ...


@dataclass(frozen=True, slots=True)
class _FutureReaderSignatureSpec:
    reader_name: str
    capability_type: str
    lookup_parameter: str
    return_type: str


_FUTURE_B3B2B_READER_SIGNATURES = (
    _FutureReaderSignatureSpec(
        reader_name="_read_current_work_item",
        capability_type="_TransitionReadCapability",
        lookup_parameter="work_item_id",
        return_type="WorkItemRecordEnvelope | None",
    ),
    _FutureReaderSignatureSpec(
        reader_name="_read_lease_identity_record",
        capability_type="_TransitionReadCapability",
        lookup_parameter="decision_ref",
        return_type="LeaseIdentityRecordEnvelope | None",
    ),
    _FutureReaderSignatureSpec(
        reader_name="_read_authorization_receipt",
        capability_type="_TransitionReadCapability",
        lookup_parameter="decision_ref",
        return_type="AuthorizationReceiptEnvelope | None",
    ),
    _FutureReaderSignatureSpec(
        reader_name="_read_dependency_receipt",
        capability_type="_TransitionReadCapability",
        lookup_parameter="decision_ref",
        return_type="DependencyReceiptEnvelope | None",
    ),
    _FutureReaderSignatureSpec(
        reader_name="_read_admitted_backlog",
        capability_type="_TransitionReadCapability",
        lookup_parameter="backlog_id",
        return_type="AdmittedBacklogRecordEnvelope | None",
    ),
    _FutureReaderSignatureSpec(
        reader_name="_read_global_stop_current",
        capability_type="_TransitionReadCapability",
        lookup_parameter="singleton_id",
        return_type="GlobalStopCurrentRecordEnvelope | None",
    ),
)


def _make_select_query_spec(
    *,
    query_id: str,
    table_name: str,
    columns: tuple[str, ...],
    lookup_column: str,
) -> _SelectQuerySpec:
    return _SelectQuerySpec(
        query_id=query_id,
        table_name=table_name,
        columns=columns,
        lookup_column=lookup_column,
        sql=_select_sql(table_name=table_name, columns=columns, lookup_column=lookup_column),
    )


def _select_sql(*, table_name: str, columns: tuple[str, ...], lookup_column: str) -> str:
    _require_safe_identifier(table_name, "table_name")
    _require_safe_identifier(lookup_column, "lookup_column")
    _require_safe_columns(columns)
    return f"SELECT {', '.join(columns)}\nFROM {table_name}\nWHERE {lookup_column} = ?\nLIMIT 2"


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


_CURRENT_WORK_ITEM_SELECT = _make_select_query_spec(
    query_id="current_work_item",
    table_name="work_items",
    columns=WORK_ITEM_ROW_COLUMNS,
    lookup_column="work_item_id",
)
_LEASE_IDENTITY_SELECT = _make_select_query_spec(
    query_id="lease_identity",
    table_name="lease_identity_records",
    columns=LEASE_IDENTITY_RECORD_ROW_COLUMNS,
    lookup_column="decision_ref",
)
_AUTHORIZATION_RECEIPT_SELECT = _make_select_query_spec(
    query_id="authorization_receipt",
    table_name="authorization_decision_receipts",
    columns=AUTHORIZATION_RECEIPT_ROW_COLUMNS,
    lookup_column="decision_ref",
)
_DEPENDENCY_RECEIPT_SELECT = _make_select_query_spec(
    query_id="dependency_receipt",
    table_name="dependency_decision_receipts",
    columns=DEPENDENCY_RECEIPT_ROW_COLUMNS,
    lookup_column="decision_ref",
)
_ADMITTED_BACKLOG_SELECT = _make_select_query_spec(
    query_id="admitted_backlog",
    table_name="admitted_backlogs",
    columns=ADMITTED_BACKLOG_ROW_COLUMNS,
    lookup_column="backlog_id",
)
_GLOBAL_STOP_CURRENT_SELECT = _make_select_query_spec(
    query_id="global_stop_current",
    table_name="global_stop_current",
    columns=GLOBAL_STOP_CURRENT_ROW_COLUMNS,
    lookup_column="singleton_id",
)

_B3B2A_SELECT_QUERY_SPECS = (
    _CURRENT_WORK_ITEM_SELECT,
    _LEASE_IDENTITY_SELECT,
    _AUTHORIZATION_RECEIPT_SELECT,
    _DEPENDENCY_RECEIPT_SELECT,
    _ADMITTED_BACKLOG_SELECT,
    _GLOBAL_STOP_CURRENT_SELECT,
)
