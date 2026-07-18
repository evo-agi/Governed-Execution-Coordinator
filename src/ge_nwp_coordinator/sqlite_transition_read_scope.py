"""Private B3b2 transition-read capability, SELECT contracts, and readers.

B3b2a defines data-only query specifications and a private protocol for a
future B3c-managed transaction capability. B3b2b adds private SELECT readers
that consume only that protocol when tests invoke them. This module still does
not implement concrete transaction authority, production read integration,
transaction ownership, mutation, idempotency, replay, or context assembly.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
import sqlite3
from typing import Any, Protocol, TypeVar

from ge_nwp_coordinator.models import require_contract_ref
from ge_nwp_coordinator.persistence_contracts import (
    ADMITTED_BACKLOG_ROW_COLUMNS,
    AdmittedBacklogRecordEnvelope,
    AUTHORIZATION_RECEIPT_ROW_COLUMNS,
    AuthorizationReceiptEnvelope,
    DEPENDENCY_RECEIPT_ROW_COLUMNS,
    DependencyReceiptEnvelope,
    GLOBAL_STOP_CURRENT_ROW_COLUMNS,
    GlobalStopCurrentRecordEnvelope,
    LEASE_IDENTITY_RECORD_ROW_COLUMNS,
    LeaseIdentityRecordEnvelope,
    WORK_ITEM_ROW_COLUMNS,
    WorkItemRecordEnvelope,
    admitted_backlog_record_envelope_from_row,
    authorization_receipt_envelope_from_row,
    dependency_receipt_envelope_from_row,
    global_stop_current_envelope_from_row,
    lease_identity_record_envelope_from_row,
    work_item_record_envelope_from_row,
)
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError,
    SQLiteMutationStoreErrorCode,
)

_SAFE_SQL_IDENTIFIER_FIRST_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz")
_SAFE_SQL_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_GLOBAL_STOP_SINGLETON_ID = 1
_EnvelopeT = TypeVar("_EnvelopeT")


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


class _MissingRowPolicy(str, Enum):
    RETURN_NONE = "return_none"
    INTEGRITY_FAILURE = "integrity_failure"


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

_SQLITE_INTEGRITY_PRIMARY_RESULT_CODES = frozenset(
    code
    for code in (
        getattr(sqlite3, "SQLITE_ERROR", None),
        getattr(sqlite3, "SQLITE_SCHEMA", None),
        getattr(sqlite3, "SQLITE_CORRUPT", None),
        getattr(sqlite3, "SQLITE_NOTADB", None),
        getattr(sqlite3, "SQLITE_MISMATCH", None),
        getattr(sqlite3, "SQLITE_CONSTRAINT", None),
    )
    if type(code) is int
)


def _read_current_work_item(
    capability: _TransitionReadCapability,
    work_item_id: str,
) -> WorkItemRecordEnvelope | None:
    validated_ref = require_contract_ref(work_item_id, "transition_read.work_item_id")
    return _read_one_select_row(
        capability=capability,
        spec=_CURRENT_WORK_ITEM_SELECT,
        lookup_value=validated_ref,
        adapter=work_item_record_envelope_from_row,
        missing_row_policy=_MissingRowPolicy.RETURN_NONE,
    )


def _read_lease_identity_record(
    capability: _TransitionReadCapability,
    decision_ref: str,
) -> LeaseIdentityRecordEnvelope | None:
    validated_ref = require_contract_ref(decision_ref, "transition_read.decision_ref")
    return _read_one_select_row(
        capability=capability,
        spec=_LEASE_IDENTITY_SELECT,
        lookup_value=validated_ref,
        adapter=lease_identity_record_envelope_from_row,
        missing_row_policy=_MissingRowPolicy.RETURN_NONE,
    )


def _read_authorization_receipt(
    capability: _TransitionReadCapability,
    decision_ref: str,
) -> AuthorizationReceiptEnvelope | None:
    validated_ref = require_contract_ref(decision_ref, "transition_read.decision_ref")
    return _read_one_select_row(
        capability=capability,
        spec=_AUTHORIZATION_RECEIPT_SELECT,
        lookup_value=validated_ref,
        adapter=authorization_receipt_envelope_from_row,
        missing_row_policy=_MissingRowPolicy.RETURN_NONE,
    )


def _read_dependency_receipt(
    capability: _TransitionReadCapability,
    decision_ref: str,
) -> DependencyReceiptEnvelope | None:
    validated_ref = require_contract_ref(decision_ref, "transition_read.decision_ref")
    return _read_one_select_row(
        capability=capability,
        spec=_DEPENDENCY_RECEIPT_SELECT,
        lookup_value=validated_ref,
        adapter=dependency_receipt_envelope_from_row,
        missing_row_policy=_MissingRowPolicy.RETURN_NONE,
    )


def _read_admitted_backlog(
    capability: _TransitionReadCapability,
    backlog_id: str,
) -> AdmittedBacklogRecordEnvelope | None:
    validated_ref = require_contract_ref(backlog_id, "transition_read.backlog_id")
    return _read_one_select_row(
        capability=capability,
        spec=_ADMITTED_BACKLOG_SELECT,
        lookup_value=validated_ref,
        adapter=admitted_backlog_record_envelope_from_row,
        missing_row_policy=_MissingRowPolicy.RETURN_NONE,
    )


def _read_global_stop_current(
    capability: _TransitionReadCapability,
) -> GlobalStopCurrentRecordEnvelope:
    envelope = _read_one_select_row(
        capability=capability,
        spec=_GLOBAL_STOP_CURRENT_SELECT,
        lookup_value=_GLOBAL_STOP_SINGLETON_ID,
        adapter=global_stop_current_envelope_from_row,
        missing_row_policy=_MissingRowPolicy.INTEGRITY_FAILURE,
    )
    if envelope is None:
        raise _database_integrity_failure()
    return envelope


def _borrow_sqlite_connection_for_select(capability: _TransitionReadCapability) -> sqlite3.Connection:
    try:
        connection = capability._borrow_connection_for_select()
    except _TransitionReadCapabilityError:
        raise
    if not isinstance(connection, sqlite3.Connection):
        raise _TransitionReadCapabilityError(_TransitionReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE)
    return connection


def _read_one_select_row(
    *,
    capability: _TransitionReadCapability,
    spec: _SelectQuerySpec,
    lookup_value: str | int,
    adapter: Callable[[Mapping[str, Any]], _EnvelopeT],
    missing_row_policy: _MissingRowPolicy,
) -> _EnvelopeT | None:
    connection = _borrow_sqlite_connection_for_select(capability)
    cursor: Any | None = None
    sqlite_failure: SQLiteMutationStoreError | None = None
    rows: Any | None = None
    try:
        cursor = connection.execute(spec.sql, (lookup_value,))
        rows = cursor.fetchmany(2)
    except sqlite3.Error as raw_sqlite_error:
        sqlite_failure = _classify_sqlite_select_error(raw_sqlite_error)
    finally:
        if cursor is not None:
            close_failure = _close_cursor_safely(cursor)
            if sqlite_failure is None and close_failure is not None:
                sqlite_failure = close_failure
    if sqlite_failure is not None:
        raise sqlite_failure

    if type(rows) is not list:
        raise _database_integrity_failure()
    if len(rows) == 0:
        if missing_row_policy is _MissingRowPolicy.RETURN_NONE:
            return None
        raise _database_integrity_failure()
    if len(rows) != 1:
        raise _database_integrity_failure()

    row = rows[0]
    row_mapping = _row_tuple_to_private_mapping(spec, row)
    del row
    del rows
    return adapter(row_mapping)


def _row_tuple_to_private_mapping(spec: _SelectQuerySpec, row: Any) -> dict[str, Any]:
    if type(row) is not tuple:
        raise _database_integrity_failure()
    if len(row) != len(spec.columns):
        raise _database_integrity_failure()
    return dict(zip(spec.columns, row, strict=True))


def _close_cursor_safely(cursor: Any) -> SQLiteMutationStoreError | None:
    try:
        cursor.close()
    except sqlite3.Error as raw_sqlite_error:
        return _classify_sqlite_select_error(raw_sqlite_error)
    return None


def _classify_sqlite_select_error(error: sqlite3.Error) -> SQLiteMutationStoreError:
    primary_code = _sqlite_primary_result_code(error)
    if primary_code in _SQLITE_INTEGRITY_PRIMARY_RESULT_CODES:
        return _database_integrity_failure()
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)


def _sqlite_primary_result_code(error: sqlite3.Error) -> int | None:
    code = getattr(error, "sqlite_errorcode", None)
    if type(code) is not int:
        return None
    return code & 0xFF


def _database_integrity_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)
