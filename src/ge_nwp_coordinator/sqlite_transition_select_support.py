"""Private transaction SELECT support for Coordinator mutation readers."""

from __future__ import annotations

from enum import Enum
import sqlite3
from typing import Any, Protocol

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
    connection = _borrow_sqlite_connection_for_select(capability)
    cursor: Any | None = None
    sqlite_failure: SQLiteMutationStoreError | None = None
    rows: Any | None = None
    try:
        cursor = connection.execute(sql, parameters)
        rows = cursor.fetchmany(2)
    except sqlite3.Error as raw_sqlite_error:
        sqlite_failure = _classify_sqlite_select_error(raw_sqlite_error)
    except Exception:
        sqlite_failure = _mutation_failed()
    finally:
        if cursor is not None:
            close_failure = _close_cursor_safely(cursor)
            if sqlite_failure is None and close_failure is not None:
                sqlite_failure = close_failure
    if sqlite_failure is not None:
        raise sqlite_failure
    if type(rows) is not list:
        raise _database_integrity_failure()
    return rows


def _row_tuple_to_private_mapping(columns: tuple[str, ...], row: object) -> dict[str, object]:
    if type(row) is not tuple:
        raise _database_integrity_failure()
    if len(row) != len(columns):
        raise _database_integrity_failure()
    return dict(zip(columns, row, strict=True))


def _borrow_sqlite_connection_for_select(capability: _MutationReadCapability) -> sqlite3.Connection:
    borrowed = _borrow_connection_or_capability_error(capability)
    if isinstance(borrowed, _MutationReadCapabilityError):
        raise borrowed
    connection = borrowed
    if not isinstance(connection, sqlite3.Connection):
        raise _MutationReadCapabilityError(_MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE)
    return connection


def _borrow_connection_or_capability_error(
    capability: _MutationReadCapability,
) -> sqlite3.Connection | _MutationReadCapabilityError:
    try:
        return capability._borrow_connection_for_select()
    except _MutationReadCapabilityError:
        raise
    except Exception:
        return _MutationReadCapabilityError(_MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE)


def _close_cursor_safely(cursor: Any) -> SQLiteMutationStoreError | None:
    try:
        cursor.close()
    except sqlite3.Error:
        return _cursor_close_failed()
    except Exception:
        return _cursor_close_failed()
    return None


def _classify_sqlite_select_error(error: sqlite3.Error) -> SQLiteMutationStoreError:
    primary_code = _sqlite_primary_result_code(error)
    if primary_code in _SQLITE_INTEGRITY_PRIMARY_RESULT_CODES:
        return _database_integrity_failure()
    return _mutation_failed()


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
