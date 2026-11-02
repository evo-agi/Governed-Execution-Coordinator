"""Administrative read-only proof of the migration-0009 normal backfill."""
from __future__ import annotations

from typing import Protocol

from ._rw0_terminal_anchor_rows import COLUMNS as ANCHOR_COLUMNS, TABLE as ANCHOR, checked_anchor_row, expected_normal_anchor
from ._rw0_terminal_outcome_rows import (
    COLUMNS, CONTEXT, OUTCOME, RECEIPT, RESULT, TerminalRow, checked_row,
)

__all__: tuple[str, ...] = ()

_PAGE = 257


class _ReadOnlyCursor(Protocol):
    def fetchone(self) -> tuple[object, ...] | None: ...
    def fetchmany(self, size: int) -> list[tuple[object, ...]]: ...
    def close(self) -> None: ...


class _ReadOnlyAdminConnection(Protocol):
    def execute(self, sql: str, parameters: tuple[object, ...] = ()) -> _ReadOnlyCursor: ...


def _one(connection: _ReadOnlyAdminConnection, table: str, key: str, value: object) -> TerminalRow:
    if table not in (CONTEXT, OUTCOME, RESULT, RECEIPT) or key not in COLUMNS[table]:
        raise ValueError("invalid terminal backfill lookup")
    rows = connection.execute(
        f"SELECT {', '.join(COLUMNS[table])} FROM {table} WHERE {key}=? LIMIT 2",
        (value,),
    ).fetchmany(2)
    if type(rows) is not list or len(rows) != 1:
        raise ValueError("incomplete terminal backfill family")
    return checked_row(table, rows[0])


def verify_terminal_anchor_backfill(connection: _ReadOnlyAdminConnection) -> None:
    """Prove a one-to-one complete persisted family/anchor relation.

    This administrative verifier never changes rows and never claims the
    caller-dependent P1/Section 41/C1 historical semantic reconstruction.
    """
    tables = (CONTEXT, OUTCOME, RESULT, RECEIPT, ANCHOR)
    counts = []
    for table in tables:
        row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        if type(row) is not tuple or len(row) != 1 or type(row[0]) is not int or row[0] < 0:
            raise ValueError("invalid terminal backfill count")
        counts.append(row[0])
    if len(set(counts)) != 1:
        raise ValueError("incomplete terminal backfill")
    seen = 0
    cursor = connection.execute("SELECT receipt_ref FROM rw0_terminal_receipts ORDER BY receipt_ref")
    try:
        page = cursor.fetchmany(_PAGE)
        while page:
            if type(page) is not list or len(page) > _PAGE:
                raise ValueError("invalid terminal backfill page")
            for locator in page:
                if type(locator) is not tuple or len(locator) != 1 or type(locator[0]) is not str:
                    raise ValueError("invalid terminal backfill locator")
                receipt = _one(connection, RECEIPT, "receipt_ref", locator[0])
                r = receipt.mapping
                context = _one(connection, CONTEXT, "context_ref", r["context_ref"])
                outcome = _one(connection, OUTCOME, "outcome_value_ref", r["outcome_value_ref"])
                result = _one(connection, RESULT, "result_ref", r["result_ref"])
                expected = expected_normal_anchor(context, outcome, result, receipt)
                rows = connection.execute(
                    f"SELECT {', '.join(ANCHOR_COLUMNS)} FROM {ANCHOR} WHERE phase_basis_ref=? LIMIT 2",
                    (r["phase_basis_ref"],),
                ).fetchmany(2)
                if type(rows) is not list or len(rows) != 1:
                    raise ValueError("incomplete terminal backfill anchor")
                if checked_anchor_row(rows[0]) != expected:
                    raise ValueError("contradictory terminal backfill anchor")
                seen += 1
            page = cursor.fetchmany(_PAGE)
        if type(page) is not list:
            raise ValueError("invalid terminal backfill page")
    finally:
        cursor.close()
    if seen != counts[0]:
        raise ValueError("incomplete terminal backfill relation")
