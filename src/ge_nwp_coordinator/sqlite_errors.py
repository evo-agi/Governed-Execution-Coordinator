"""Safe SQLite bootstrap and migration error vocabulary."""

from __future__ import annotations

from enum import Enum
from typing import Any


class SQLiteStateErrorCode(str, Enum):
    UNSAFE_STATE_ROOT = "unsafe_state_root"
    UNSAFE_DATABASE_FILE = "unsafe_database_file"
    UNSUPPORTED_FILESYSTEM = "unsupported_filesystem"
    DATABASE_NOT_EMPTY_UNMANAGED = "database_not_empty_unmanaged"
    MIGRATION_HISTORY_MISSING = "migration_history_missing"
    MIGRATION_HISTORY_INVALID = "migration_history_invalid"
    MIGRATION_CHECKSUM_MISMATCH = "migration_checksum_mismatch"
    MIGRATION_GAP = "migration_gap"
    DATABASE_SCHEMA_TOO_NEW = "database_schema_too_new"
    DATABASE_SCHEMA_INCOMPATIBLE = "database_schema_incompatible"
    MIGRATION_FAILED = "migration_failed"
    SCHEMA_VERIFICATION_FAILED = "schema_verification_failed"
    SCHEMA_FINGERPRINT_MISMATCH = "schema_fingerprint_mismatch"
    SQLITE_POSTURE_UNAVAILABLE = "sqlite_posture_unavailable"


class SQLiteStateError(Exception):
    """Closed public error whose string form is only the safe error class."""

    def __init__(self, error_class: SQLiteStateErrorCode | str, *, internal_detail: Any | None = None) -> None:
        code = SQLiteStateErrorCode(error_class)
        self.error_class = code.value
        self._internal_detail = internal_detail
        super().__init__(code.value)

    @property
    def internal_detail(self) -> Any | None:
        """Internal diagnostic detail for tests; not a public payload field."""

        return self._internal_detail

    def __str__(self) -> str:
        return self.error_class
