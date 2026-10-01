"""Private transaction SELECT support for Coordinator mutation readers."""

from __future__ import annotations

from enum import Enum
import sqlite3
from typing import Any, NoReturn, Protocol

from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode


class _MutationReadCapabilityFailureReason(str, Enum):
    CAPABILITY_UNAVAILABLE = "mutation_read_capability_unavailable"
    CAPABILITY_EXPIRED = "mutation_read_capability_expired"
    PROCESS_MISMATCH = "process_mismatch"
    THREAD_MISMATCH = "thread_mismatch"


class _MutationReadCapabilityError(RuntimeError):
    """Safe private transaction-read capability failure with no connection details."""

    def __init__(self, reason: _MutationReadCapabilityFailureReason | str) -> None:
        normalized = _MutationReadCapabilityFailureReason(reason)
        self.reason = normalized
        super().__init__(normalized.value)


class _MutationReadCapability(Protocol):
    """Private Coordinator mutation transaction capability protocol.

    Protocol conformance is not authority. Concrete capability authority is
    owned by the Coordinator mutation transaction controller after
    operation-lease validation, managed transaction start, managed validation,
    writer fencing, and opaque epoch creation.
    """

    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        """Return the B3c-owned transaction connection for private SELECTs."""
        ...


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


def _execute_select_fetch_two(
    *,
    capability: _MutationReadCapability,
    sql: str,
    parameters: tuple[object, ...],
) -> list[object]:
    outcome = _perform_select_fetch_bounded(
        capability=capability,
        sql=sql,
        parameters=parameters,
        limit=2,
    )
    del capability, sql, parameters
    return _complete_select_fetch(outcome)


def _execute_select_fetch_bounded(
    *,
    capability: _MutationReadCapability,
    sql: str,
    parameters: tuple[object, ...],
    limit: int,
) -> list[object]:
    outcome = _perform_select_fetch_bounded(
        capability=capability,
        sql=sql,
        parameters=parameters,
        limit=limit,
    )
    del capability, sql, parameters, limit
    return _complete_select_fetch(outcome)


def _perform_select_fetch_bounded(
    *,
    capability: _MutationReadCapability,
    sql: str,
    parameters: tuple[object, ...],
    limit: int,
) -> list[object] | SQLiteMutationStoreErrorCode | _MutationReadCapabilityFailureReason:
    # RW0-C1 adds exact two-relation and fourteen-operand overflow bounds.
    # The registry remains finite; callers cannot select arbitrary limits.
    if type(limit) is not int or limit not in (2, 3, 15, 16, 257, 258):
        return SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
    borrowed = _borrow_connection_or_failure(capability)
    if type(borrowed) is _MutationReadCapabilityFailureReason:
        return borrowed
    connection = borrowed
    cursor: Any | None = None
    failure: SQLiteMutationStoreErrorCode | None = None
    rows: Any | None = None
    try:
        cursor = connection.execute(sql, parameters)
        rows = cursor.fetchmany(limit)
    except sqlite3.Error as raw_sqlite_error:
        failure = _classify_sqlite_select_error(raw_sqlite_error)
    except Exception:
        failure = SQLiteMutationStoreErrorCode.MUTATION_FAILED
    finally:
        if cursor is not None:
            close_failure = _close_cursor_safely(cursor)
            if failure is None and close_failure is not None:
                failure = close_failure
    if failure is not None:
        return failure
    if type(rows) is not list:
        return SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
    return rows


def _complete_select_fetch(
    outcome: list[object] | SQLiteMutationStoreErrorCode | _MutationReadCapabilityFailureReason,
) -> list[object]:
    if type(outcome) is list:
        return outcome
    if type(outcome) is SQLiteMutationStoreErrorCode:
        failure = outcome
        outcome = []
        _raise_select_failure(failure)
    if type(outcome) is _MutationReadCapabilityFailureReason:
        capability_failure = outcome
        outcome = []
        _raise_select_failure(capability_failure)
    outcome = []
    _raise_select_failure(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def _raise_select_failure(
    failure: SQLiteMutationStoreErrorCode | _MutationReadCapabilityFailureReason,
) -> NoReturn:
    if type(failure) is _MutationReadCapabilityFailureReason:
        raise _MutationReadCapabilityError(failure) from None
    raise SQLiteMutationStoreError(failure) from None


def _row_tuple_to_private_mapping(columns: tuple[str, ...], row: object) -> dict[str, object]:
    if type(row) is not tuple:
        raise _database_integrity_failure()
    if len(row) != len(columns):
        raise _database_integrity_failure()
    return dict(zip(columns, row, strict=True))


def _borrow_connection_or_failure(
    capability: _MutationReadCapability,
) -> sqlite3.Connection | _MutationReadCapabilityFailureReason:
    try:
        borrowed = capability._borrow_connection_for_select()
    except _MutationReadCapabilityError as error:
        return error.reason
    except Exception:
        return _MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE
    if not isinstance(borrowed, sqlite3.Connection):
        return _MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE
    return borrowed


def _close_cursor_safely(cursor: Any) -> SQLiteMutationStoreErrorCode | None:
    try:
        cursor.close()
    except sqlite3.Error:
        return SQLiteMutationStoreErrorCode.MUTATION_FAILED
    except Exception:
        return SQLiteMutationStoreErrorCode.MUTATION_FAILED
    return None


def _classify_sqlite_select_error(error: sqlite3.Error) -> SQLiteMutationStoreErrorCode:
    primary_code = _sqlite_primary_result_code(error)
    if primary_code in _SQLITE_INTEGRITY_PRIMARY_RESULT_CODES:
        return SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
    return SQLiteMutationStoreErrorCode.MUTATION_FAILED


def _sqlite_primary_result_code(error: sqlite3.Error) -> int | None:
    code = getattr(error, "sqlite_errorcode", None)
    if type(code) is not int:
        return None
    return code & 0xFF


def _database_integrity_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def _mutation_failed() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)


def _cursor_close_failed() -> SQLiteMutationStoreError:
    return _mutation_failed()
