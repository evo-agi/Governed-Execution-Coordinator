from __future__ import annotations

from enum import Enum
import hashlib
import inspect
from pathlib import Path
from typing import get_args

import pytest

import ge_nwp_coordinator
import ge_nwp_coordinator.sqlite_writer_session as writer_session_module
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import initialize_database
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.state_store import (
    CommittedTransition,
    StateStore,
    TransitionApplyOutcome,
    TransitionApplyPreflightError,
    TransitionApplyPreflightFailureReason,
    TransitionConflict,
    WriterSession,
    WriterSessionError,
    WriterSessionFailureReason,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src" / "ge_nwp_coordinator"
MIGRATION_DIR = PACKAGE_DIR / "sqlite_migrations"

EXPECTED_FROZEN_SOURCE_SHA256 = {
    "src/ge_nwp_coordinator/sqlite_transition_dry_run_contracts.py": (
        "f0ccae80ef3c805802425b1b7716890e8a17eae1194540573470d8356bb892b8"
    ),
    "src/ge_nwp_coordinator/sqlite_transition_transaction.py": (
        "a8f0f6fbea713575b4ab7fc5f9cdf68740fbee016c30c32f30a0238e32e63f15"
    ),
    "src/ge_nwp_coordinator/sqlite_transition_write_contracts.py": (
        "8b5a6a0ffc54833e33707efb10d7a9fe8ff35489f220d46ac235e1cde0addfbb"
    ),
}


class _OtherReason(str, Enum):
    INVALID_COMMAND = "transition_apply_invalid_command"


class _HostileInput:
    def __str__(self) -> str:
        return "hostile-command-value"

    def __repr__(self) -> str:
        return "hostile-digest-and-path"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_public_preflight_reason_enum_values_are_exact() -> None:
    assert [reason.name for reason in TransitionApplyPreflightFailureReason] == [
        "INVALID_COMMAND",
        "UNSUPPORTED_COMMAND",
    ]
    assert TransitionApplyPreflightFailureReason.INVALID_COMMAND.value == "transition_apply_invalid_command"
    assert TransitionApplyPreflightFailureReason.UNSUPPORTED_COMMAND.value == "transition_apply_unsupported_command"


def test_public_preflight_error_is_safe_runtime_error() -> None:
    error = TransitionApplyPreflightError(TransitionApplyPreflightFailureReason.INVALID_COMMAND)

    assert isinstance(error, RuntimeError)
    assert type(error) is TransitionApplyPreflightError
    assert error.reason is TransitionApplyPreflightFailureReason.INVALID_COMMAND
    assert str(error) == "transition_apply_invalid_command"
    assert error.args == ("transition_apply_invalid_command",)
    assert repr(error) == "<TransitionApplyPreflightError>"
    assert error.__cause__ is None
    assert error.__context__ is None
    assert not hasattr(error, "__notes__")
    for forbidden in ("hostile", "digest", "path", "command-value"):
        assert forbidden not in str(error)
        assert forbidden not in repr(error)


def test_public_preflight_error_constructor_accepts_only_exact_enum_type() -> None:
    for invalid in (
        "transition_apply_invalid_command",
        _OtherReason.INVALID_COMMAND,
        _HostileInput(),
        object(),
        None,
    ):
        with pytest.raises(ValueError) as exc_info:
            TransitionApplyPreflightError(invalid)  # type: ignore[arg-type]
        assert exc_info.value.args == ("invalid_field_type:transition_apply_preflight.reason",)
        rendered = f"{exc_info.value!r} {exc_info.value}"
        assert "hostile-command-value" not in rendered
        assert "hostile-digest-and-path" not in rendered


def test_package_root_exports_only_public_preflight_vocabulary() -> None:
    package_exports = set(ge_nwp_coordinator.__all__)

    assert "TransitionApplyPreflightError" in package_exports
    assert "TransitionApplyPreflightFailureReason" in package_exports
    assert ge_nwp_coordinator.TransitionApplyPreflightError is TransitionApplyPreflightError
    assert ge_nwp_coordinator.TransitionApplyPreflightFailureReason is TransitionApplyPreflightFailureReason

    for private_name in (
        "_TransitionDryRunPreflightError",
        "_TransitionDryRunPreflightFailureReason",
        "_run_atomic_transition_apply",
        "_TransitionTransactionController",
        "_SQLiteTransitionReadCapability",
        "_TransitionWritePlan",
    ):
        assert private_name not in package_exports
        assert not hasattr(ge_nwp_coordinator, private_name)
        assert private_name not in _read("src/ge_nwp_coordinator/__init__.py")


def test_state_store_and_writer_session_public_shapes_are_unchanged() -> None:
    assert get_args(TransitionApplyOutcome) == (CommittedTransition, TransitionConflict)
    assert TransitionApplyPreflightError not in get_args(TransitionApplyOutcome)
    assert not hasattr(StateStore, "apply_transition")
    assert not hasattr(StateStore, "apply_global_stop_update")
    assert list(inspect.signature(StateStore.read_current).parameters) == ["self", "work_item_id"]
    assert list(inspect.signature(StateStore.read_global_stop).parameters) == ["self"]
    assert list(inspect.signature(WriterSession.apply_transition).parameters) == ["self", "transition_command"]
    assert list(inspect.signature(WriterSession.apply_global_stop_update).parameters) == [
        "self",
        "global_stop_command",
        "typed_operator_decision",
    ]


def test_public_sqlite_transition_preflight_and_global_stop_unavailable_do_not_open_sqlite(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "state")
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    sqlite_open_calls = 0

    def fail_if_sqlite_opens(*args: object, **kwargs: object) -> object:
        nonlocal sqlite_open_calls
        sqlite_open_calls += 1
        raise AssertionError("public mutation method opened SQLite")

    monkeypatch.setattr(writer_session_module, "open_existing_sqlite_connection", fail_if_sqlite_opens)

    try:
        with pytest.raises(TransitionApplyPreflightError) as transition_error:
            session.apply_transition(None)  # type: ignore[arg-type]
        assert transition_error.value.reason is TransitionApplyPreflightFailureReason.INVALID_COMMAND
        assert transition_error.value.__cause__ is None
        assert transition_error.value.__context__ is None

        with pytest.raises(WriterSessionError) as global_stop_error:
            session.apply_global_stop_update(None, None)  # type: ignore[arg-type]
        assert global_stop_error.value.reason is WriterSessionFailureReason.WRITER_SESSION_MUTATION_UNAVAILABLE
    finally:
        session.close()

    assert sqlite_open_calls == 0


def test_private_runtime_sources_remain_frozen_and_public_wrapper_imports_are_bounded() -> None:
    for path, expected in EXPECTED_FROZEN_SOURCE_SHA256.items():
        assert _sha256(path) == expected

    writer_source = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")
    assert writer_source.count("_run_atomic_transition_apply") == 2
    assert writer_source.count("sqlite_transition_dry_run_contracts") == 1
    assert "from ge_nwp_coordinator.sqlite_transition_transaction import _run_atomic_transition_apply" in writer_source
    assert "sqlite_transition_write_contracts" not in writer_source


def test_docs_pin_exact_private_to_public_preflight_mapping() -> None:
    doc = _read(".docs/b3c4c-prerequisite-contract.md")
    normalized = " ".join(doc.split())

    for phrase in (
        '| `transition_dry_run_invalid_command` | `TransitionApplyPreflightFailureReason.INVALID_COMMAND` |',
        '| `transition_dry_run_unsupported_command` | `TransitionApplyPreflightFailureReason.UNSUPPORTED_COMMAND` |',
        "catch only the exact private preflight error type",
        "exact-gate the private reason",
        "raise the public error outside the active `except` block",
        "no private `__context__` survives",
        "internal private-contract integrity contradiction",
        "`validation_failed` remains reserved",
    ):
        assert phrase in normalized


def test_docs_pin_malformed_private_preflight_database_integrity_classification() -> None:
    prerequisite = _read(".docs/b3c4c-prerequisite-contract.md")
    implementation = _read(".docs/b3c4c-public-transition-delegation.md")
    writer_source = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")
    normalized_prerequisite = " ".join(prerequisite.split())
    normalized_implementation = " ".join(implementation.split())

    for normalized in (normalized_prerequisite, normalized_implementation):
        for phrase in (
            "malformed private preflight object or reason",
            "SQLiteMutationStoreError(database_integrity_failure)",
            "internal private-contract integrity contradiction",
            "must not become a third public preflight reason",
            "must not fall back to `TransitionApplyPreflightFailureReason.INVALID_COMMAND`",
            "`TransitionApplyPreflightFailureReason.UNSUPPORTED_COMMAND`",
            "no cause, context, notes",
            "distinct from import/load failure",
            "which remains `SQLiteMutationStoreError(mutation_failed)`",
            "`commit_outcome_unknown`",
            "passes through unchanged",
        ):
            assert phrase in normalized

    assert SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value == "database_integrity_failure"
    assert SQLiteMutationStoreErrorCode.MUTATION_FAILED.value == "mutation_failed"
    assert "SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE" in writer_source
    assert "SQLiteMutationStoreErrorCode.MUTATION_FAILED" in writer_source
    assert "TransitionApplyPreflightFailureReason.INVALID_COMMAND" in writer_source
    assert "TransitionApplyPreflightFailureReason.UNSUPPORTED_COMMAND" in writer_source
    assert "except Exception" in writer_source
    assert "except BaseException" not in inspect.getsource(writer_session_module._SQLiteWriterSession.apply_transition)


def test_docs_pin_operation_guard_precedence_and_function_local_import_contract() -> None:
    doc = _read(".docs/b3c4c-prerequisite-contract.md")
    normalized = " ".join(doc.split())

    for phrase in (
        "acquire the existing WriterSession operation guard",
        "inside that active guard, perform one bounded function-local import",
        "`_run_atomic_transition_apply`",
        "exact private preflight error and reason types",
        "call the delegate exactly once with the exact operation lease and the exact caller command",
        "top-level reverse import",
        "mutable delegate registry",
        "injection callback",
        "package-root indirection",
        "second controller",
        "second atomic wrapper",
        "second capability path",
        "No command preflight or delegate import occurs if operation-guard acquisition fails.",
    ):
        assert phrase in normalized


def test_docs_pin_import_failure_delegate_catchall_and_commit_uncertainty() -> None:
    doc = _read(".docs/b3c4c-prerequisite-contract.md")
    normalized = " ".join(doc.split())

    for phrase in (
        "Import or delegate-load failure before delegate invocation is classified as:",
        "SQLiteMutationStoreError(mutation_failed)",
        "No delegate or COMMIT has begun on that path",
        "No Generic Delegate Catch-All",
        "The private atomic delegate remains the sole owner",
        "must not wrap delegate execution in a broad",
        "`except Exception -> mutation_failed`",
        "`commit_outcome_unknown` passes through unchanged.",
        "unexpected non-contract exception escaping the private atomic delegate is contract drift",
    ):
        assert phrase in normalized


def test_docs_pin_public_result_error_matrix_and_no_b4_schema_behavior() -> None:
    doc = _read(".docs/b3c4c-prerequisite-contract.md")
    normalized = " ".join(doc.split())

    for phrase in (
        "| fresh accepted transition | `CommittedTransition(replayed=False)` |",
        "| fresh domain rejection | `CommittedTransition(replayed=False)` |",
        "| exact replay | `CommittedTransition(replayed=True)` |",
        "| invalid local command | `TransitionApplyPreflightError` |",
        "| unsupported local command | `TransitionApplyPreflightError` |",
        "| session lifecycle or slot failure | `WriterSessionError` |",
        "| store, sequence, or commit failure | `SQLiteMutationStoreError` |",
        "`_SQLiteWriterSession.apply_transition()` now enters",
        "`_run_atomic_transition_apply`",
        "`_SQLiteWriterSession.apply_global_stop_update()` still enters",
        "`writer_session_mutation_unavailable`",
        "B4 remains future for global-stop persistence",
        "schema-ID bump",
        "migration 0002",
    ):
        assert phrase in normalized

    assert not list(MIGRATION_DIR.glob("0002*"))
