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
from typing import Any, TypeVar

from ge_nwp_coordinator.models import require_contract_ref
from ge_nwp_coordinator.persistence_contracts import (
    ADMITTED_BACKLOG_ROW_COLUMNS,
    AdmittedBacklogRecordEnvelope,
    AUTHORIZATION_RECEIPT_ROW_COLUMNS,
    AuthorizationReceiptEnvelope,
    DEPENDENCY_RECEIPT_ROW_COLUMNS,
    DependencyReceiptEnvelope,
    LEASE_IDENTITY_RECORD_ROW_COLUMNS,
    LeaseIdentityRecordEnvelope,
    WORK_ITEM_ROW_COLUMNS,
    WorkItemRecordEnvelope,
    admitted_backlog_record_envelope_from_row,
    authorization_receipt_envelope_from_row,
    dependency_receipt_envelope_from_row,
    lease_identity_record_envelope_from_row,
    work_item_record_envelope_from_row,
)
from ge_nwp_coordinator.sqlite_global_stop_event_contracts import _GLOBAL_STOP_CURRENT_SELECT
from ge_nwp_coordinator.sqlite_global_stop_readers import _read_global_stop_current
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _MutationReadCapability,
    _database_integrity_failure,
    _execute_select_fetch_two,
    _row_tuple_to_private_mapping,
)

_SAFE_SQL_IDENTIFIER_FIRST_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz")
_SAFE_SQL_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_EnvelopeT = TypeVar("_EnvelopeT")


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
_B3B2A_SELECT_QUERY_SPECS = (
    _CURRENT_WORK_ITEM_SELECT,
    _LEASE_IDENTITY_SELECT,
    _AUTHORIZATION_RECEIPT_SELECT,
    _DEPENDENCY_RECEIPT_SELECT,
    _ADMITTED_BACKLOG_SELECT,
    _GLOBAL_STOP_CURRENT_SELECT,
)

def _read_current_work_item(
    capability: _MutationReadCapability,
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
    capability: _MutationReadCapability,
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
    capability: _MutationReadCapability,
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
    capability: _MutationReadCapability,
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
    capability: _MutationReadCapability,
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


def _read_one_select_row(
    *,
    capability: _MutationReadCapability,
    spec: _SelectQuerySpec,
    lookup_value: str | int,
    adapter: Callable[[Mapping[str, Any]], _EnvelopeT],
    missing_row_policy: _MissingRowPolicy,
) -> _EnvelopeT | None:
    rows = _execute_select_fetch_two(
        capability=capability,
        sql=spec.sql,
        parameters=(lookup_value,),
    )
    if len(rows) == 0:
        if missing_row_policy is _MissingRowPolicy.RETURN_NONE:
            return None
        raise _database_integrity_failure()
    if len(rows) != 1:
        raise _database_integrity_failure()

    row = rows[0]
    row_mapping = _row_tuple_to_private_mapping(spec.columns, row)
    del row
    del rows
    return adapter(row_mapping)
