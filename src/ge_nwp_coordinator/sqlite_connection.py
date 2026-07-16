"""SQLite connection posture for B1 bootstrap and migrations."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Any

from ge_nwp_coordinator.sqlite_errors import SQLiteStateError, SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_security import existing_state_database_path, prepare_state_database

DEFAULT_BUSY_TIMEOUT_MS = 5000
MIN_BUSY_TIMEOUT_MS = 1
MAX_BUSY_TIMEOUT_MS = 30000


@dataclass(frozen=True)
class SQLiteConnectionPosture:
    foreign_keys: bool
    journal_mode: str
    synchronous: str
    locking_mode: str
    trusted_schema_supported: bool
    trusted_schema: bool | None
    busy_timeout_ms: int
    extension_loading_disabled: bool
    explicit_transaction_control: bool


def open_sqlite_connection(
    location: CoordinatorStateLocation,
    *,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
) -> sqlite3.Connection:
    database_path = prepare_state_database(location)
    connection = _connect_path(str(database_path), busy_timeout_ms=busy_timeout_ms)
    try:
        apply_connection_posture(connection, busy_timeout_ms=busy_timeout_ms)
    except Exception:
        connection.close()
        raise
    return connection


def open_existing_sqlite_connection(
    location: CoordinatorStateLocation,
    *,
    read_only: bool,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
) -> sqlite3.Connection:
    database_path = existing_state_database_path(location)
    if database_path is None:
        raise SQLiteStateError(SQLiteStateErrorCode.MIGRATION_HISTORY_MISSING)
    mode = "ro" if read_only else "rw"
    connection = _connect_uri(f"{database_path.as_uri()}?mode={mode}", busy_timeout_ms=busy_timeout_ms)
    try:
        apply_observational_connection_posture(connection, busy_timeout_ms=busy_timeout_ms)
    except Exception:
        connection.close()
        raise
    return connection


def apply_connection_posture(
    connection: sqlite3.Connection,
    *,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
) -> SQLiteConnectionPosture:
    _require_bounded_busy_timeout(busy_timeout_ms)
    try:
        _disable_extension_loading(connection)
        connection.execute("PRAGMA foreign_keys = ON")
        journal_mode = _single_pragma_value(connection.execute("PRAGMA journal_mode = DELETE").fetchone())
        connection.execute("PRAGMA synchronous = FULL")
        synchronous = _single_pragma_value(connection.execute("PRAGMA synchronous").fetchone())
        locking_mode = _single_pragma_value(connection.execute("PRAGMA locking_mode = NORMAL").fetchone())
        _set_busy_timeout(connection, busy_timeout_ms)
        trusted_schema_supported, trusted_schema = _disable_trusted_schema(connection)
        posture = SQLiteConnectionPosture(
            foreign_keys=_pragma_bool(connection.execute("PRAGMA foreign_keys").fetchone()),
            journal_mode=str(journal_mode).lower(),
            synchronous=_normalize_synchronous(synchronous),
            locking_mode=str(locking_mode).lower(),
            trusted_schema_supported=trusted_schema_supported,
            trusted_schema=trusted_schema,
            busy_timeout_ms=int(_single_pragma_value(connection.execute("PRAGMA busy_timeout").fetchone())),
            extension_loading_disabled=True,
            explicit_transaction_control=connection.isolation_level is None,
        )
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE) from None
    _verify_posture(posture, busy_timeout_ms)
    return posture


def apply_observational_connection_posture(
    connection: sqlite3.Connection,
    *,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
) -> SQLiteConnectionPosture:
    _require_bounded_busy_timeout(busy_timeout_ms)
    try:
        _disable_extension_loading(connection)
        connection.execute("PRAGMA foreign_keys = ON")
        _set_busy_timeout(connection, busy_timeout_ms)
        trusted_schema_supported, trusted_schema = _disable_trusted_schema(connection)
        posture = SQLiteConnectionPosture(
            foreign_keys=_pragma_bool(connection.execute("PRAGMA foreign_keys").fetchone()),
            journal_mode=str(_single_pragma_value(connection.execute("PRAGMA journal_mode").fetchone())).lower(),
            synchronous=_normalize_synchronous(connection.execute("PRAGMA synchronous").fetchone()[0]),
            locking_mode=str(_single_pragma_value(connection.execute("PRAGMA locking_mode").fetchone())).lower(),
            trusted_schema_supported=trusted_schema_supported,
            trusted_schema=trusted_schema,
            busy_timeout_ms=int(_single_pragma_value(connection.execute("PRAGMA busy_timeout").fetchone())),
            extension_loading_disabled=True,
            explicit_transaction_control=connection.isolation_level is None,
        )
    except (sqlite3.Error, TypeError, ValueError):
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE) from None
    _verify_nonpersistent_posture(posture, busy_timeout_ms)
    return posture


def _connect_path(path: str, *, busy_timeout_ms: int) -> sqlite3.Connection:
    try:
        return sqlite3.connect(
            path,
            timeout=_bounded_busy_timeout_seconds(busy_timeout_ms),
            isolation_level=None,
        )
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE) from None


def _connect_uri(uri: str, *, busy_timeout_ms: int) -> sqlite3.Connection:
    try:
        return sqlite3.connect(
            uri,
            timeout=_bounded_busy_timeout_seconds(busy_timeout_ms),
            isolation_level=None,
            uri=True,
        )
    except sqlite3.Error:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE) from None


def _disable_extension_loading(connection: sqlite3.Connection) -> None:
    enable_load_extension = getattr(connection, "enable_load_extension", None)
    if callable(enable_load_extension):
        try:
            enable_load_extension(False)
        except sqlite3.Error:
            raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE) from None


def _set_busy_timeout(connection: sqlite3.Connection, busy_timeout_ms: int) -> None:
    _require_bounded_busy_timeout(busy_timeout_ms)
    connection.execute(f"PRAGMA busy_timeout = {busy_timeout_ms}")


def _bounded_busy_timeout_seconds(busy_timeout_ms: int) -> float:
    return _require_bounded_busy_timeout(busy_timeout_ms) / 1000


def _require_bounded_busy_timeout(busy_timeout_ms: int) -> int:
    if (
        not isinstance(busy_timeout_ms, int)
        or isinstance(busy_timeout_ms, bool)
        or not MIN_BUSY_TIMEOUT_MS <= busy_timeout_ms <= MAX_BUSY_TIMEOUT_MS
    ):
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    return busy_timeout_ms


def _disable_trusted_schema(connection: sqlite3.Connection) -> tuple[bool, bool | None]:
    try:
        connection.execute("PRAGMA trusted_schema = OFF")
        row = connection.execute("PRAGMA trusted_schema").fetchone()
    except sqlite3.Error:
        return False, None
    if row is None:
        return False, None
    value = _single_pragma_value(row)
    return True, bool(int(value))


def _single_pragma_value(row: tuple[Any, ...] | None) -> Any:
    if row is None or len(row) != 1:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    return row[0]


def _pragma_bool(row: tuple[Any, ...] | None) -> bool:
    return bool(int(_single_pragma_value(row)))


def _normalize_synchronous(value: Any) -> str:
    raw = str(value).lower()
    if raw in {"2", "full"}:
        return "full"
    return raw


def _verify_posture(posture: SQLiteConnectionPosture, expected_busy_timeout_ms: int) -> None:
    if not posture.foreign_keys:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    if posture.journal_mode != "delete":
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    if posture.synchronous != "full":
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    if posture.locking_mode != "normal":
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    if posture.trusted_schema_supported and posture.trusted_schema is not False:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    if posture.busy_timeout_ms != expected_busy_timeout_ms:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    if not posture.extension_loading_disabled or not posture.explicit_transaction_control:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)


def _verify_nonpersistent_posture(posture: SQLiteConnectionPosture, expected_busy_timeout_ms: int) -> None:
    if not posture.foreign_keys:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    if posture.trusted_schema_supported and posture.trusted_schema is not False:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    if posture.busy_timeout_ms != expected_busy_timeout_ms:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    if not posture.extension_loading_disabled or not posture.explicit_transaction_control:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)


def database_path_for_connection(location: CoordinatorStateLocation):
    return prepare_state_database(location)
