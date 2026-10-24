"""Internal SQLite connection posture helpers for B1 administration."""

from __future__ import annotations

from dataclasses import dataclass
import os
import sqlite3
from threading import current_thread, get_ident
from typing import Any
import weakref

from ge_nwp_coordinator.sqlite_errors import SQLiteStateError, SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_security import (
    _StateDatabaseAuthorityBinding,
    _StateDatabaseAuthorityBindingMismatch,
    _StateDatabaseAuthorityBindingUnavailable,
    _close_descriptor,
    _open_bound_database_descriptor,
    _open_bound_root_descriptor,
    _validate_state_database_authority_binding,
    existing_state_database_path,
    prepare_state_database,
)

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


class _SQLiteOperationalPostureError(SQLiteStateError):
    """Private marker for operational posture failures without raw details."""


_SQLITE_READONLY_ROLLBACK = 776


def _is_engine_reported_readonly_rollback(error: sqlite3.Error) -> bool:
    """Use only SQLite's exact extended result, never message or primary code."""

    code = getattr(error, "sqlite_errorcode", None)
    return type(code) is int and code == _SQLITE_READONLY_ROLLBACK


def _safe_observational_sqlite_error(error: sqlite3.Error) -> SQLiteStateError:
    if _is_engine_reported_readonly_rollback(error):
        return SQLiteStateError(SQLiteStateErrorCode.RECOVERY_NEEDED)
    return _SQLiteOperationalPostureError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)


_RETAINED_CONNECTION_CONSTRUCTION_KEY = object()
_CLOSE_PROOF_CONSTRUCTION_KEY = object()
_WRITER_SESSION_RESOURCE_IDENTITY_CONSTRUCTION_KEY = object()


class _WriterSessionResourceIdentity:
    """Opaque identity shared only by components of one writer resource."""

    __slots__ = ()
    __hash__ = object.__hash__

    def __init__(self, *, key: object) -> None:
        if key is not _WRITER_SESSION_RESOURCE_IDENTITY_CONSTRUCTION_KEY:
            raise ValueError("invalid writer resource identity")

    def __repr__(self) -> str:
        return "<_WriterSessionResourceIdentity>"

    def __reduce__(self) -> object:
        raise TypeError("invalid writer resource identity")


def _new_writer_session_resource_identity() -> _WriterSessionResourceIdentity:
    return _WriterSessionResourceIdentity(
        key=_WRITER_SESSION_RESOURCE_IDENTITY_CONSTRUCTION_KEY
    )


@dataclass(frozen=True, slots=True, repr=False)
class _SQLiteConnectionCustodyIdentity:
    resource_identity: _WriterSessionResourceIdentity
    connection_identity: int
    owner_pid: int
    owner_thread: int

    def __post_init__(self) -> None:
        if (
            type(self.resource_identity) is not _WriterSessionResourceIdentity
            or type(self.connection_identity) is not int
            or self.connection_identity < 0
            or type(self.owner_pid) is not int
            or self.owner_pid < 0
            or type(self.owner_thread) is not int
            or self.owner_thread < 0
        ):
            raise ValueError("invalid connection custody")

    def __repr__(self) -> str:
        return "<_SQLiteConnectionCustodyIdentity>"


class _RetainedSQLiteConnection:
    """One exact connection-or-proof custody union for a mutation connection."""

    __slots__ = (
        "_custody",
        "_custody_identity",
        "_owner_thread_ref",
    )
    __hash__ = object.__hash__

    def __init__(
        self,
        *,
        key: object,
        connection: sqlite3.Connection,
        resource_identity: _WriterSessionResourceIdentity,
    ) -> None:
        if key is not _RETAINED_CONNECTION_CONSTRUCTION_KEY:
            raise ValueError("invalid connection custody")
        if (
            not isinstance(connection, sqlite3.Connection)
            or type(resource_identity) is not _WriterSessionResourceIdentity
        ):
            raise ValueError("invalid connection custody")
        self._custody_identity = _SQLiteConnectionCustodyIdentity(
            resource_identity,
            id(connection),
            os.getpid(),
            get_ident(),
        )
        self._custody: sqlite3.Connection | _SQLiteConnectionCloseProof = connection
        self._owner_thread_ref = weakref.ref(current_thread())

    def __repr__(self) -> str:
        return "<_RetainedSQLiteConnection>"

    def __reduce__(self) -> object:
        raise TypeError("invalid connection custody")

    @property
    def connection_identity(self) -> int:
        return self._custody_identity.connection_identity

    @property
    def custody_identity(self) -> _SQLiteConnectionCustodyIdentity:
        return self._custody_identity

    @property
    def resource_identity(self) -> _WriterSessionResourceIdentity:
        return self._custody_identity.resource_identity

    def _require_owner_thread(self) -> None:
        identity = self._custody_identity
        if (
            identity.owner_pid != os.getpid()
            or self._owner_thread_ref() is not current_thread()
            or identity.owner_thread != get_ident()
        ):
            raise RuntimeError("connection custody unavailable")

    def _borrow_exact_connection(self) -> sqlite3.Connection:
        """Return one bounded controller borrow while connection custody remains."""

        self._require_owner_thread()
        current = self._custody
        if (
            not isinstance(current, sqlite3.Connection)
            or id(current) != self._custody_identity.connection_identity
        ):
            raise RuntimeError("connection custody unavailable")
        return current

    def _close_with_proof(self) -> "_SQLiteConnectionCloseProof":
        """Publish proof only after the exact base SQLite close returns normally."""

        self._require_owner_thread()
        current = self._custody
        if type(current) is _SQLiteConnectionCloseProof:
            return current
        if (
            not isinstance(current, sqlite3.Connection)
            or id(current) != self._custody_identity.connection_identity
        ):
            raise RuntimeError("connection custody unavailable")
        exact_connection = current
        sqlite3.Connection.close(exact_connection)
        proof = _SQLiteConnectionCloseProof(
            key=_CLOSE_PROOF_CONSTRUCTION_KEY,
            custody_identity=self._custody_identity,
        )
        self._custody = proof
        return proof

    def owns_exact_connection(self, connection: sqlite3.Connection) -> bool:
        current = self._custody
        return (
            self._custody_identity.owner_pid == os.getpid()
            and self._owner_thread_ref() is current_thread()
            and current is connection
            and id(connection) == self._custody_identity.connection_identity
        )

    def matches_exact_connection(self, connection: sqlite3.Connection) -> bool:
        return (
            isinstance(connection, sqlite3.Connection)
            and id(connection) == self._custody_identity.connection_identity
        )

    def matches_scope_identity(
        self,
        connection_identity: int,
        owner_pid: int,
        owner_thread: int,
    ) -> bool:
        return (
            connection_identity == self._custody_identity.connection_identity
            and owner_pid == self._custody_identity.owner_pid
            and owner_thread == self._custody_identity.owner_thread
        )

    def matches_custody_identity(
        self,
        custody_identity: _SQLiteConnectionCustodyIdentity,
    ) -> bool:
        return custody_identity is self._custody_identity


class _SQLiteConnectionCloseProof:
    """Connection-free proof created only after exact close returns normally."""

    __slots__ = (
        "_custody_identity",
    )
    __hash__ = object.__hash__

    def __init__(
        self,
        *,
        key: object,
        custody_identity: _SQLiteConnectionCustodyIdentity,
    ) -> None:
        if key is not _CLOSE_PROOF_CONSTRUCTION_KEY:
            raise ValueError("invalid connection close proof")
        if type(custody_identity) is not _SQLiteConnectionCustodyIdentity:
            raise ValueError("invalid connection close proof")
        self._custody_identity = custody_identity

    @property
    def connection_identity(self) -> int:
        return self._custody_identity.connection_identity

    @property
    def owner_pid(self) -> int:
        return self._custody_identity.owner_pid

    @property
    def owner_thread(self) -> int:
        return self._custody_identity.owner_thread

    @property
    def custody_identity(self) -> _SQLiteConnectionCustodyIdentity:
        return self._custody_identity

    @property
    def resource_identity(self) -> _WriterSessionResourceIdentity:
        return self._custody_identity.resource_identity

    def __repr__(self) -> str:
        return "<_SQLiteConnectionCloseProof>"

    def __reduce__(self) -> object:
        raise TypeError("invalid connection close proof")


def _make_retained_sqlite_connection(
    connection: sqlite3.Connection,
    resource_identity: _WriterSessionResourceIdentity,
) -> _RetainedSQLiteConnection:
    """Prepare exact retained custody without granting a second active user."""

    return _RetainedSQLiteConnection(
        key=_RETAINED_CONNECTION_CONSTRUCTION_KEY,
        connection=connection,
        resource_identity=resource_identity,
    )


def _open_sqlite_connection(
    location: CoordinatorStateLocation,
    *,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
) -> sqlite3.Connection:
    """Create/open the fixed database for explicit initialize only."""

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
    except BaseException:
        connection.close()
        raise
    return connection


def _open_bound_existing_sqlite_connection(
    binding: _StateDatabaseAuthorityBinding,
    *,
    read_only: bool,
    recovery: bool = False,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
) -> sqlite3.Connection:
    if type(binding) is not _StateDatabaseAuthorityBinding:
        raise _StateDatabaseAuthorityBindingMismatch(SQLiteStateErrorCode.UNSAFE_DATABASE_FILE)
    root_descriptor = -1
    database_descriptor = -1
    connection: sqlite3.Connection | None = None
    failure: BaseException | None = None
    try:
        _validate_state_database_authority_binding(binding)
        root_descriptor = _open_bound_root_descriptor(binding)
        database_descriptor = _open_bound_database_descriptor(
            binding,
            root_descriptor=root_descriptor,
        )
        database_path = binding._location_for_private_open().database_path
        mode = "ro" if read_only else "rw"
        connection = _connect_uri(
            f"{database_path.resolve(strict=True).as_uri()}?mode={mode}",
            busy_timeout_ms=busy_timeout_ms,
        )
        if recovery:
            _apply_pre_recovery_connection_controls(connection, busy_timeout_ms)
        _validate_state_database_authority_binding(binding)
        apply_observational_connection_posture(connection, busy_timeout_ms=busy_timeout_ms)
        _validate_state_database_authority_binding(binding)
        opened = connection
        connection = None
        return opened
    except (_StateDatabaseAuthorityBindingMismatch, _StateDatabaseAuthorityBindingUnavailable) as exc:
        if connection is not None:
            _close_rejected_bound_connection(connection)
        failure = exc
    except (OSError, SQLiteStateError, sqlite3.Error):
        if connection is not None:
            _close_rejected_bound_connection(connection)
        failure = _StateDatabaseAuthorityBindingUnavailable(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        if connection is not None:
            _close_rejected_bound_connection(connection)
        raise
    finally:
        _close_descriptor(database_descriptor)
        _close_descriptor(root_descriptor)
    if failure is not None:
        raise failure
    raise _StateDatabaseAuthorityBindingUnavailable(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)


def _close_rejected_bound_connection(connection: sqlite3.Connection) -> None:
    try:
        connection.close()
    except Exception:
        pass


def _apply_pre_recovery_connection_controls(
    connection: sqlite3.Connection, busy_timeout_ms: int
) -> None:
    """Set nonpersistent controls before the first posture/database read.

    Python exposes no pre-connect PRAGMA hook. The checked journal entry is
    therefore established before connect, and this is the first API opportunity.
    """

    _require_bounded_busy_timeout(busy_timeout_ms)
    _disable_extension_loading(connection)
    connection.execute("PRAGMA trusted_schema = OFF")
    connection.execute("PRAGMA synchronous = FULL")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA locking_mode = NORMAL")
    _set_busy_timeout(connection, busy_timeout_ms)


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
    except sqlite3.Error as exc:
        raise _safe_observational_sqlite_error(exc) from None
    except (TypeError, ValueError):
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
    except sqlite3.Error as exc:
        raise _safe_observational_sqlite_error(exc) from None


def _disable_extension_loading(connection: sqlite3.Connection) -> None:
    enable_load_extension = getattr(connection, "enable_load_extension", None)
    if callable(enable_load_extension):
        try:
            enable_load_extension(False)
        except sqlite3.Error as exc:
            raise _safe_observational_sqlite_error(exc) from None


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
    except sqlite3.Error as exc:
        if _is_engine_reported_readonly_rollback(exc):
            raise SQLiteStateError(SQLiteStateErrorCode.RECOVERY_NEEDED) from None
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


def _is_operational_posture_error(error: SQLiteStateError) -> bool:
    return isinstance(error, _SQLiteOperationalPostureError)


def _verify_nonpersistent_posture(posture: SQLiteConnectionPosture, expected_busy_timeout_ms: int) -> None:
    if not posture.foreign_keys:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    if posture.trusted_schema_supported and posture.trusted_schema is not False:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    if posture.busy_timeout_ms != expected_busy_timeout_ms:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
    if not posture.extension_loading_disabled or not posture.explicit_transaction_control:
        raise SQLiteStateError(SQLiteStateErrorCode.SQLITE_POSTURE_UNAVAILABLE)
