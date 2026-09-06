from __future__ import annotations

import ast
from enum import Enum
import hashlib
import inspect
from pathlib import Path
from typing import get_args

import pytest

import ge_nwp_coordinator
import ge_nwp_coordinator.sqlite_connection as connection_module
import ge_nwp_coordinator.sqlite_writer_session as writer_session_module
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import initialize_database
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.state_store import (
    CommittedTransition,
    GlobalStopApplyPreflightError,
    GlobalStopApplyPreflightFailureReason,
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
        "c01350dc15f753f0c9ecae1e9c253f217a425317e19a60105f053f6295864a3c"
    ),
    "src/ge_nwp_coordinator/sqlite_transition_write_contracts.py": (
        "5512294de5030b94936dc43caec659a16c5617633dcafac28cbffed6dc878760"
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
        "_CoordinatorMutationTransactionController",
        "_SQLiteMutationReadCapability",
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


def test_public_sqlite_transition_and_global_stop_preflight_do_not_open_sqlite(
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

        with pytest.raises(GlobalStopApplyPreflightError) as global_stop_error:
            session.apply_global_stop_update(None, None)  # type: ignore[arg-type]
        assert global_stop_error.value.reason is GlobalStopApplyPreflightFailureReason.INVALID_COMMAND
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


def test_vs1a_resource_identity_has_one_resource_allocation_site_and_no_public_registry() -> None:
    writer_source = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")
    connection_source = _read("src/ge_nwp_coordinator/sqlite_connection.py")
    resource_init = inspect.getsource(writer_session_module._WriterSessionResource.__init__)
    assert resource_init.count("_new_writer_session_resource_identity()") == 1
    assert writer_source.count("_new_writer_session_resource_identity()") == 1
    assert connection_source.count("def _new_writer_session_resource_identity(") == 1
    assert "_WRITER_SESSION_RESOURCE_IDENTITIES" not in connection_source
    assert "_WRITER_SESSION_RESOURCE_IDENTITIES" not in writer_source
    assert "_WriterSessionResourceIdentity" not in ge_nwp_coordinator.__all__
    assert "_new_writer_session_resource_identity" not in ge_nwp_coordinator.__all__
    assert "_WriterSessionResourceIdentity" not in writer_session_module.__all__


def test_vs1a_every_live_lifecycle_family_carries_exact_resource_identity() -> None:
    assert "resource_identity" in writer_session_module._WriterSessionAuthority.__dataclass_fields__
    assert "resource_identity" in writer_session_module._OperationCompletionHandle.__slots__
    assert hasattr(writer_session_module._WriterSessionMutationSlot, "resource_identity")
    assert hasattr(writer_session_module._ControllerScopeToken, "resource_identity")
    assert "resource_identity" in connection_module._SQLiteConnectionCustodyIdentity.__dataclass_fields__
    assert hasattr(connection_module._RetainedSQLiteConnection, "resource_identity")
    assert hasattr(connection_module._SQLiteConnectionCloseProof, "resource_identity")
    for cursor_type in writer_session_module._CLEANUP_CURSOR_TYPES:
        assert hasattr(cursor_type, "resource_identity")
    assert "resource_identity" in writer_session_module._WriterSessionCleanupClaim.__dataclass_fields__

    for state_type in (
        writer_session_module._WriterSessionAbortCloseUnproved,
        writer_session_module._WriterSessionCommitUncertainUnproved,
        writer_session_module._WriterSessionCommitKnownUnproved,
        writer_session_module._WriterSessionAbortPendingCleanup,
        writer_session_module._WriterSessionCommitUncertainPendingCleanup,
        writer_session_module._WriterSessionCommitKnownPendingCleanup,
    ):
        source = inspect.getsource(state_type)
        assert "__post_init__" in source


def test_vs1a_resource_identity_comparisons_are_identity_only() -> None:
    total = 0
    for path in (
        "src/ge_nwp_coordinator/sqlite_connection.py",
        "src/ge_nwp_coordinator/sqlite_writer_session.py",
    ):
        source = _read(path)
        tree = ast.parse(source)
        comparisons = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Compare)
            and "resource_identity" in (ast.get_source_segment(source, node) or "")
        ]
        assert comparisons
        total += len(comparisons)
        assert all(
            all(isinstance(operator, (ast.Is, ast.IsNot)) for operator in node.ops)
            for node in comparisons
        )
    assert total >= 20
    transaction_source = _read(
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py"
    )
    assert "operation_lease._completion_handle.resource_identity" in transaction_source


def test_vs1a_completion_fence_is_monotonic_and_precedes_fallible_completion() -> None:
    handle_source = inspect.getsource(writer_session_module._OperationCompletionHandle)
    record_source = inspect.getsource(writer_session_module._WriterSessionOperationRecord)
    operation_exit = inspect.getsource(writer_session_module._WriterSessionOperationLease.__exit__)
    operation_close = inspect.getsource(writer_session_module._WriterSessionOperationLease._close)
    mutation_close = inspect.getsource(writer_session_module._WriterSessionMutationLease._close)
    operation_finalizer = inspect.getsource(
        writer_session_module._finalize_writer_session_operation
    )
    mark_source = inspect.getsource(
        writer_session_module._WriterSessionResource._mark_operation_cleanup_required
    )
    release_source = inspect.getsource(
        writer_session_module._WriterSessionResource._release_mutation_slot
    )
    prepare_source = inspect.getsource(
        writer_session_module._WriterSessionResource._prepare_operation_retirement
    )
    local_retirement_source = inspect.getsource(
        writer_session_module._WriterSessionResource._retire_operation_lease_locally
    )
    publish_source = inspect.getsource(
        writer_session_module._WriterSessionResource._publish_prepared_operation_retirement
    )
    successor_source = inspect.getsource(
        writer_session_module._WriterSessionResource._state_after_operation_completion
    )

    assert 'object.__setattr__(self, "_cleanup_required", True)' in handle_source
    assert 'object.__setattr__(self, "_cleanup_required", False)' not in handle_source
    assert "exception" not in tuple(writer_session_module._OperationCompletionHandle.__slots__)
    assert "with self._condition:" in mark_source
    assert "successor_record = replace(record, cleanup_required=True)" in mark_source
    assert "_state_with_replaced_operation_record_locked(" in mark_source
    assert "with self._condition:" in release_source
    assert "mutation_release_acknowledgment=release_acknowledgment" in release_source
    assert "with self._condition:" in prepare_source
    assert "retirement_preparation_acknowledgment=acknowledgment" in prepare_source
    assert "_operation_has_exact_mutation_release_acknowledgment(" in prepare_source
    assert "with self._condition:" in local_retirement_source
    assert "admitted_lease = record.lease_reference()" in local_retirement_source
    assert "finalizer = record.finalizer" in local_retirement_source
    assert local_retirement_source.index("operation_lease._closed = True") < (
        local_retirement_source.index("finalizer.detach()")
    )
    assert local_retirement_source.index("finalizer.detach()") < (
        local_retirement_source.index("_is_successful_exact_operation_finalizer_detach(")
    )
    assert ".alive" not in local_retirement_source
    assert "phase=_OperationRetirementPhase.EXPLICIT_RETIRED" in local_retirement_source
    assert operation_exit.index("_mark_operation_cleanup_required(") < operation_exit.index(
        "self._close()"
    )
    assert mutation_close.index("_mark_operation_cleanup_required(") > mutation_close.index(
        "_release_mutation_slot("
    )
    finalizer_try = next(
        statement
        for statement in ast.parse(operation_finalizer).body[0].body
        if isinstance(statement, ast.Try)
    )
    ordinary_finalizer_source = "\n".join(
        ast.unparse(statement) for statement in finalizer_try.body
    )
    process_control_handler_source = "\n".join(
        ast.unparse(statement)
        for handler in finalizer_try.handlers
        for statement in handler.body
    )
    assert "_mark_operation_orphaned" in ordinary_finalizer_source
    assert "_publish_prepared_operation_retirement" not in ordinary_finalizer_source
    assert "active_for_owner" not in ordinary_finalizer_source
    assert "_continue_cleanup(blocking=False, finalizer=True)" in ordinary_finalizer_source
    assert "_mark_operation_orphaned" in process_control_handler_source
    assert operation_close.index("_prepare_operation_retirement(") < operation_close.index(
        "_retire_operation_lease_locally("
    )
    assert operation_close.index("_retire_operation_lease_locally(") < operation_close.index(
        "_publish_prepared_operation_retirement("
    )
    assignment = "self._lifecycle_state = final_successor"
    assert publish_source.count(assignment) == 1
    assert publish_source.index(assignment) < publish_source.index(
        "self._notify_operation_retirement_waiters_locked()"
    )
    assert "completion_acknowledged" not in handle_source
    assert "completion_acknowledged" not in publish_source
    assert "record.retirement_preparation_acknowledgment" in publish_source
    assert "record.phase is not _OperationRetirementPhase.EXPLICIT_RETIRED" in publish_source
    assert "or record.cleanup_required" in publish_source
    assert "_operation_has_exact_local_retirement_locked" not in publish_source
    assert "record is None" in publish_source
    assert "raise WriterSessionError(" in publish_source
    assert "_OperationLocalRetirementAcknowledgment" not in handle_source
    assert "_OperationLocalRetirementAcknowledgment" not in inspect.getsource(
        writer_session_module
    )
    assert tuple(writer_session_module._WriterSessionOperationRecord.__dataclass_fields__) == (
        "handle",
        "resource_identity",
        "operation_id",
        "owner_pid",
        "owner_thread",
        "lifecycle_epoch",
        "lease_reference",
        "finalizer",
        "phase",
        "cleanup_required",
        "mutation_release_acknowledgment",
        "retirement_preparation_acknowledgment",
    )
    assert "frozen=True" in record_source
    assert successor_source.count("if record.cleanup_required:") >= 3
    released_branch = successor_source.split(
        "if type(state) is _WriterSessionControllerCloseProvedReleased:", 1
    )[1]
    assert released_branch.index("if record.cleanup_required:") < released_branch.index(
        "return _WriterSessionActive(activity)"
    )
    normal_try = next(
        statement
        for statement in ast.parse(operation_close.lstrip()).body[0].body
        if isinstance(statement, ast.Try)
    )
    assert isinstance(normal_try.body[-1], ast.Expr)
    assert "_publish_prepared_operation_retirement" in ast.unparse(
        normal_try.body[-1]
    )


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
        "delegates once to the B4b private atomic global-stop entry",
        "B4c adds guarded public global-stop delegation",
        "schema-ID bump",
        "migration 0002",
    ):
        assert phrase in normalized

    assert sorted(path.name for path in MIGRATION_DIR.glob("0002*")) == [
        "0002_development_program_and_effect_state.sql"
    ]
