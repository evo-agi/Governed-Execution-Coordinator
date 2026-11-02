"""Private nominal-capability reads for the cross-profile terminal route."""
from __future__ import annotations

from typing import cast

from ._rw0_terminal_anchor_rows import COLUMNS, TABLE, TerminalAnchorRow, checked_anchor_row
from ._rw0_terminal_outcome_contracts import _safe_ref
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .sqlite_transition_select_support import _MutationReadCapability, _execute_select_fetch_bounded

__all__: tuple[str, ...] = ()

_LOOKUPS = frozenset((
    "phase_basis_ref", "family_route", "mutation_ref", "decision_ref",
    "context_ref", "outcome_value_ref", "result_ref", "receipt_ref",
))


def read_terminal_anchor(
    capability: object, column: str, value: object,
) -> TerminalAnchorRow | None:
    """Read one registry route only after the caller's fence and disclosure."""
    if type(column) is not str or column not in _LOOKUPS:
        raise SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)
    try:
        _safe_ref(value)
        rows = _execute_select_fetch_bounded(
            capability=cast(_MutationReadCapability, capability),
            sql=f"SELECT {', '.join(COLUMNS)} FROM {TABLE} WHERE {column}=? LIMIT 2",
            parameters=(value,), limit=2,
        )
        if len(rows) > 1:
            raise ValueError("duplicate terminal anchor")
        return checked_anchor_row(rows[0]) if rows else None
    except SQLiteMutationStoreError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE) from None
