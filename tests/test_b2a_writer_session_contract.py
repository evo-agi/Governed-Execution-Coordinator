from __future__ import annotations

import ast
from dataclasses import fields
import hashlib
import inspect
from pathlib import Path

import pytest

from ge_nwp_coordinator import SafeWriterMetadata, StateStore, WriterSession, WriterSessionFailureReason
from ge_nwp_coordinator.models import APPLY_CONFLICT_REASONS
from ge_nwp_coordinator.state_store import (
    MAX_WRITER_GENERATION,
    WRITER_ISSUANCE_PROOF_DOMAIN,
    TransitionConflict,
    WriterSessionError,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MIGRATION_0001_CHECKSUM = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"


def _contains_requests_client_usage(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name == "requests" or alias.name.startswith("requests.")
            for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and (
            node.module == "requests"
            or (node.module or "").startswith("requests.")
        ):
            return True
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "requests"
        ):
            return True
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        if node.args[0].value != "requests":
            continue
        if isinstance(function, ast.Name) and function.id == "__import__":
            return True
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "importlib"
            and function.attr == "import_module"
        ):
            return True
    return False


def _assert_no_requests_client_usage(paths: tuple[Path, ...]) -> None:
    accepted = (
        "class Example:\n    max_pull_requests = 1\n"
        "payload = {'max_pull_requests': 1}\n"
        "def max_pull_requests() -> int:\n    return 1\n"
    )
    rejected = (
        "import requests\n",
        "import requests as rq\nrq.get(...)\n",
        "from requests import get\nget(...)\n",
        "from requests import get as http_get\nhttp_get(...)\n",
        "requests.get(...)\n",
        "__import__('requests')\n",
        "importlib.import_module('requests')\n",
    )
    assert not _contains_requests_client_usage(accepted)
    assert all(_contains_requests_client_usage(source) for source in rejected)
    assert not any(
        _contains_requests_client_usage(path.read_text(encoding="utf-8"))
        for path in paths
    )


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src").rglob("*.py"))


def _source_without_lock() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src").rglob("*.py")
        if path.name != "state_authority_lock.py"
    )


def _sqlite_sources() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src" / "ge_nwp_coordinator").glob("sqlite_*.py")
    )


def _markdown_section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.index(marker)
    tail = text[start + len(marker) :]
    next_heading = tail.find("\n## ")
    if next_heading == -1:
        return tail
    return tail[:next_heading]


def test_state_writer_token_is_removed_from_public_contract() -> None:
    source = _source()
    package_init = _read("src/ge_nwp_coordinator/__init__.py")
    state_store = _read("src/ge_nwp_coordinator/state_store.py")

    assert "StateWriterToken" not in source
    assert "STATE_WRITER_TOKEN" not in source
    assert "StateWriterToken" not in package_init
    assert "WriterOwnershipStore" not in state_store
    assert "current_writer" not in state_store


def test_state_store_has_no_mutation_methods_and_writer_session_owns_them() -> None:
    assert not hasattr(StateStore, "apply_transition")
    assert not hasattr(StateStore, "apply_global_stop_update")
    assert hasattr(WriterSession, "apply_transition")
    assert hasattr(WriterSession, "apply_global_stop_update")

    transition_signature = inspect.signature(WriterSession.apply_transition)
    assert tuple(transition_signature.parameters) == ("self", "transition_command")

    global_stop_signature = inspect.signature(WriterSession.apply_global_stop_update)
    assert tuple(global_stop_signature.parameters) == (
        "self",
        "global_stop_command",
        "typed_operator_decision",
    )


def test_writer_session_failure_reason_contract_is_safe_and_exported() -> None:
    assert WriterSessionFailureReason.WRITER_SESSION_CLOSED.value == "writer_session_closed"
    assert WriterSessionFailureReason.WRITER_SESSION_PROCESS_MISMATCH.value == "writer_session_process_mismatch"
    assert WriterSessionFailureReason.WRITER_SESSION_CLOSE_DURING_OPERATION.value == "writer_session_close_during_operation"
    assert WriterSessionFailureReason.WRITER_SESSION_MUTATION_IN_PROGRESS.value == "writer_session_mutation_in_progress"
    assert WriterSessionFailureReason.WRITER_SESSION_MUTATION_UNAVAILABLE.value == "writer_session_mutation_unavailable"

    error = WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_CLOSED)
    assert error.reason is WriterSessionFailureReason.WRITER_SESSION_CLOSED
    assert str(error) == "writer_session_closed"

    package_init = _read("src/ge_nwp_coordinator/__init__.py")
    assert "WriterSessionError" in package_init
    assert "WriterSessionFailureReason" in package_init
    assert "StateWriterToken" not in package_init


def test_writer_session_failure_reasons_are_not_apply_conflict_reasons() -> None:
    assert "writer_session_closed" not in APPLY_CONFLICT_REASONS
    assert "writer_session_process_mismatch" not in APPLY_CONFLICT_REASONS
    assert "writer_session_close_during_operation" not in APPLY_CONFLICT_REASONS
    assert "writer_session_required" not in APPLY_CONFLICT_REASONS
    assert "writer_session_mutation_in_progress" not in APPLY_CONFLICT_REASONS
    assert "writer_session_mutation_unavailable" not in APPLY_CONFLICT_REASONS
    assert "stale_writer_token" in APPLY_CONFLICT_REASONS


def test_apply_conflict_reasons_exclude_writer_session_closed() -> None:
    with pytest.raises(ValueError, match="invalid_field_type:conflict_class"):
        TransitionConflict("writer_session_closed")
    with pytest.raises(ValueError, match="invalid_field_type:conflict_class"):
        TransitionConflict("writer_session_process_mismatch")
    with pytest.raises(ValueError, match="invalid_field_type:conflict_class"):
        TransitionConflict("writer_session_close_during_operation")
    with pytest.raises(ValueError, match="invalid_field_type:conflict_class"):
        TransitionConflict("writer_session_mutation_in_progress")


def test_safe_writer_metadata_is_non_authoritative_and_non_secret() -> None:
    metadata = SafeWriterMetadata(
        writer_ref="writer-main",
        generation=1,
        issued_ref="writer-issued-1",
        acquired_at="2026-07-16T00:00:00Z",
    )

    assert metadata.writer_ref == "writer-main"
    assert metadata.generation == 1
    assert metadata.issued_ref == "writer-issued-1"
    assert metadata.acquired_at == "2026-07-16T00:00:00Z"
    field_names = {field.name for field in fields(SafeWriterMetadata)}
    forbidden_fragments = ("proof", "digest", "pid", "lock", "active", "live", "liveness")
    for fragment in forbidden_fragments:
        assert all(fragment not in name for name in field_names)
    assert not hasattr(metadata, "apply_transition")
    assert not hasattr(metadata, "apply_global_stop_update")
    assert not hasattr(metadata, "close")

    with pytest.raises(ValueError, match="safe_writer_metadata.generation must be greater than zero"):
        SafeWriterMetadata(
            writer_ref="writer-main",
            generation=0,
            issued_ref="writer-issued-0",
            acquired_at="2026-07-16T00:00:00Z",
        )


def test_no_latest_writer_read_surface_is_added_in_b2a() -> None:
    source = _source()
    assert "def current_writer" not in source
    assert "def read_latest_writer_issuance" not in source


def test_durable_issuance_is_not_live_session_truth() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    section = _markdown_section(writer_doc, "Durable Row And Liveness Truth")

    for phrase in (
        "records the latest durable fencing issuance",
        "not current-process truth",
        "not lock ownership truth",
        "not an active-session registry",
        "Absence or presence of a row does not prove whether a lock is held.",
        "Safe metadata cannot reconstruct authority",
        "no B2a observer API claims liveness",
    ):
        assert phrase in section


def test_docs_pin_session_apply_domain_failure_layers() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    section = _markdown_section(writer_doc, "Failure Layer Taxonomy")

    for phrase in (
        "WriterSession lifecycle failure",
        "writer_session_closed",
        "writer_session_process_mismatch",
        "writer_session_close_during_operation",
        "Before any `StateStore` or atomic apply call",
        "No event, no apply conflict, no SQLite access, no idempotency disclosure",
        "Atomic apply conflict",
        "Requires a session that passed local lifecycle checks",
        "stale_writer_token",
        "Domain result",
        "accepted or domain-rejected event",
    ):
        assert phrase in section


def test_docs_pin_session_failure_precedence_before_apply_boundary() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    section = _markdown_section(writer_doc, "Failure Precedence")
    normalized = " ".join(section.split())

    for phrase in (
        "Acquire `_WriterSessionOperationLease`.",
        "Acquisition performs owner-process and active-session validation",
        "returns a lease only after the retained authority lock is confirmed active",
        "Any provisional operation registration is synchronously unwound",
        "If acquisition fails, no operation lease is exposed",
        "no mutation slot is attempted",
        "no SQLite connection opens",
        "writer_session_process_mismatch",
        "No store call.",
        "writer_session_closed",
        "writer_session_close_during_operation",
        "private operation guard is entered and exited",
        "perform mutation-specific local command-shape checks",
        "acquire the shared per-session mutation slot",
        "Open one existing managed read/write connection",
        "stale proof or generation returns `stale_writer_token`",
        "A closed session must not be reclassified as stale",
    ):
        assert phrase in normalized


def test_common_lock_topology_is_documented_once() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    bootstrap_doc = _read(".docs/sqlite-bootstrap-and-migrations.md")
    location_source = _read("src/ge_nwp_coordinator/sqlite_location.py")

    assert "one common state-authority advisory lock" in writer_doc
    assert "There are not separate migration and writer lock domains." in writer_doc
    assert "state-authority lock path" in bootstrap_doc
    assert "coordinator-state.migration.lock" in location_source
    assert "COORDINATOR_STATE_AUTHORITY_LOCK_FILENAME" in location_source
    assert "not durable schema identity" in writer_doc


def test_no_ttl_heartbeat_failover_or_takeover_contract() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    threat_doc = _read(".docs/sqlite-threat-model.md")

    for phrase in (
        "There is no TTL, heartbeat, automatic takeover, or automatic failover.",
        "no heartbeat or automatic failover exists",
        "operator action is required to recover",
        "A live hung process holding the lock requires explicit operator action.",
    ):
        assert phrase in (writer_doc + "\n" + threat_doc)


def test_writer_session_close_contract_is_idempotent_and_non_durable() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    section = _markdown_section(writer_doc, "Graceful Close And Process Crash")
    state_store = _read("src/ge_nwp_coordinator/state_store.py")

    assert "| Deliberate close |" in section
    for phrase in (
        "exactly one cleanup owner enters cleaning",
        "Successful explicit close returns only after closed means proof cleanup",
        "advisory-lock close, and registry cleanup are complete",
        "Later operations fail with `writer_session_closed`",
        "close is idempotent after closed",
        "private-proof references are dropped",
        "No SQLite `writer_ownership` `UPDATE`, `DELETE`, or release-marker write occurs",
    ):
        assert phrase in section

    assert "def close(self) -> None:" in state_store
    assert "def __enter__(self) -> Self:" in state_store
    assert "def __exit__(" in state_store
    sqlite_writer_session = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")
    assert sqlite_writer_session.count("def close(") == 1
    assert _read("src/ge_nwp_coordinator/state_authority_lock.py").count("def close(") == 1


def test_writer_session_close_leaves_latest_issuance_evidence() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    section = _markdown_section(writer_doc, "Graceful Close And Process Crash")

    for phrase in (
        "the latest durable issuance row remains unchanged",
        "database row remains latest issuance evidence after close",
        "the row remains latest issuance evidence only",
    ):
        assert phrase in (section + "\n" + writer_doc)


def test_writer_session_close_does_not_clear_generation() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    close_section = _markdown_section(writer_doc, "Graceful Close And Process Crash")
    generation_section = _markdown_section(writer_doc, "Generation And Proof Specification")

    assert "Graceful close does not decrement, clear, reset, release, or reuse the durable generation." in close_section
    assert "graceful close does not decrement, clear, or release the durable generation" in generation_section
    for phrase in (
        "close clears the writer row",
        "close resets generation",
        "crash rolls back an already committed generation",
        "next acquisition may reuse a skipped generation",
    ):
        assert phrase in generation_section


def test_writer_session_close_does_not_claim_memory_zeroization() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    section = _markdown_section(writer_doc, "Graceful Close And Process Crash")

    assert "best-effort overwrite" in section
    assert "no guaranteed Python/CPython memory zeroization is claimed" in section
    assert "No guaranteed memory zeroization is claimed." in writer_doc


def test_writer_session_crash_releases_future_os_lock_by_process_teardown() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    section = _markdown_section(writer_doc, "Graceful Close And Process Crash")

    for phrase in (
        "| Process crash after lock acquisition but before SQLite transaction |",
        "OS lock releases on process death through process/descriptor teardown.",
        "| Process crash while active |",
        "OS lock releases through process/descriptor teardown.",
        "B2b implements and tests the lock primitive itself",
        "B2c implements and tests an internal concrete `WriterSession`",
    ):
        assert phrase in section


def test_uncommitted_writer_acquisition_rolls_back_on_crash() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    section = _markdown_section(writer_doc, "Graceful Close And Process Crash")

    for phrase in (
        "| Process crash during uncommitted issuance transaction |",
        "SQLite rolls back the uncommitted issuance transaction.",
        "No committed writer row change survives.",
        "No committed generation exists to reuse.",
    ):
        assert phrase in section


def test_committed_generation_may_be_skipped_but_never_reused() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    close_section = _markdown_section(writer_doc, "Graceful Close And Process Crash")
    generation_section = _markdown_section(writer_doc, "Generation And Proof Specification")

    for phrase in (
        "| Process crash after issuance commit but before session return |",
        "The committed durable generation remains latest issuance evidence only.",
        "The committed generation may be skipped but is never reused.",
        "No session is reconstructed from the durable row",
    ):
        assert phrase in close_section
    for phrase in (
        "committed generations are never reused",
        "gaps are allowed",
        "a committed issuance that never becomes a usable returned session still",
    ):
        assert phrase in generation_section


def test_next_acquisition_increments_from_latest_durable_generation() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    close_section = _markdown_section(writer_doc, "Graceful Close And Process Crash")
    generation_section = _markdown_section(writer_doc, "Generation And Proof Specification")

    for phrase in (
        "Next acquisition reads the committed durable generation and increments it.",
        "Subsequent acquisition increments from the durable generation.",
        "Future acquisition increments from the durable generation.",
    ):
        assert phrase in close_section
    assert "next acquisition reads the durable latest generation and increments it" in generation_section


def test_generation_and_proof_specification_is_implemented_in_internal_b2c_module() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    source = _source()
    sqlite_writer_session = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")

    assert MAX_WRITER_GENERATION == 9223372036854775807
    assert WRITER_ISSUANCE_PROOF_DOMAIN == "governed-execution.nwp-writer-issuance-proof.v1"
    assert "first generation is `1`" in writer_doc
    assert "secrets.token_bytes(32)" in writer_doc
    assert "hmac.compare_digest" in writer_doc
    assert "guaranteed memory zeroization" in writer_doc
    assert "secrets.token_bytes" in sqlite_writer_session
    assert "hmac.compare_digest" in sqlite_writer_session
    source_without_b2c = source.replace(sqlite_writer_session, "")
    assert "secrets.token_bytes" not in source_without_b2c
    assert "hmac.compare_digest" not in source_without_b2c


def test_no_sqlite_release_marker_or_writer_row_clear_contract() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")
    section = _markdown_section(writer_doc, "Graceful Close And Process Crash")
    sqlite_sources = _sqlite_sources()
    source = _source()

    for phrase in (
        "No SQLite `writer_ownership` `UPDATE`, `DELETE`, or release-marker write occurs",
        "No SQLite release-marker transaction is required.",
        "The durable issuance row remains unchanged.",
    ):
        assert phrase in section

    for fragment in (
        "release_marker",
        "released_at",
        "release_timestamp",
        "writer_released",
        "active_writer",
        "writer_liveness",
    ):
        assert fragment not in source

    sqlite_writer_session = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")
    assert "UPDATE writer_ownership" in sqlite_writer_session
    assert "INSERT INTO writer_ownership" in sqlite_writer_session
    assert "DELETE FROM writer_ownership" not in sqlite_sources


def test_b2c_contains_no_writer_release_takeover_or_reconstruction_runtime() -> None:
    source = _source()
    source_without_lock = _source_without_lock()
    state_store = _read("src/ge_nwp_coordinator/state_store.py")
    sqlite_writer_session = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")

    assert "class WriterSession(Protocol)" in state_store
    for fragment in (
        "class SQLiteWriterSession",
        "class SqliteWriterSession",
        "acquire_writer",
        "release_writer",
        "ttl",
        "heartbeat",
        "expiry",
        "takeover",
        "failover",
        "from_metadata",
        "from_durable",
        "reconstruct_writer_session",
    ):
        assert fragment not in source
    assert "secrets.token_bytes" in sqlite_writer_session
    assert "hmac.compare_digest" in sqlite_writer_session
    for fragment in ("fcntl.", "flock", "LOCK_EX", "LOCK_NB"):
        assert fragment not in source_without_lock
        assert fragment in _read("src/ge_nwp_coordinator/state_authority_lock.py")


def test_fork_exec_and_thread_requirements_are_documented_without_overclaim() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")

    for phrase in (
        "reject use in a forked child",
        "mark the lock descriptor non-inheritable across exec",
        "os.register_at_fork",
        "process-local lifecycle synchronization",
        "private operation-identity registry",
        "reject duplicate active sessions",
        "`FD_CLOEXEC` alone does not solve fork inheritance.",
    ):
        assert phrase in writer_doc


def test_schema_fit_preserves_0001_and_allows_later_migrations() -> None:
    migrations = sorted(path.name for path in (ROOT / "src/ge_nwp_coordinator/sqlite_migrations").glob("*.sql"))
    assert migrations == [
        "0001_initial.sql",
        "0002_development_program_and_effect_state.sql",
        "0003_cognitive_proposal_and_selection_state.sql",
        "0004_rw0_c1_durable_evidence.sql",
    ]
    migration_bytes = (ROOT / "src/ge_nwp_coordinator/sqlite_migrations/0001_initial.sql").read_bytes()
    assert hashlib.sha256(migration_bytes).hexdigest() == EXPECTED_MIGRATION_0001_CHECKSUM

    writer_doc = _read(".docs/writer-session-authority.md")
    assert "Migration `0001_initial` is sufficient" in writer_doc
    assert "requires no migration 0002" in writer_doc
    for forbidden_field in ("release timestamp", "process id", "lock inode", "heartbeat", "expiry", "liveness flag"):
        assert forbidden_field in writer_doc


def test_b2c_implements_only_internal_writer_acquisition_not_state_store_mutations() -> None:
    _assert_no_requests_client_usage(tuple((ROOT / "src").rglob("*.py")))
    source = _source()
    source_without_lock = _source_without_lock()
    sqlite_sources = _sqlite_sources()
    sqlite_writer_session = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")

    forbidden_source_fragments = (
        "acquire_writer",
        "class SQLiteStateStore",
        "class SqliteStateStore",
        "class SQLiteWriterSession",
        "class SqliteWriterSession",
        "subprocess",
        "socket",
        "urllib",
        "CoordinatorService",
        "Scheduler",
        "QueueConsumer",
        "while True",
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in source
    for fragment in ("import fcntl", "fcntl.", "flock", "LOCK_EX", "LOCK_NB"):
        assert fragment not in source_without_lock
    lock_source = _read("src/ge_nwp_coordinator/state_authority_lock.py")
    for fragment in ("import fcntl", "flock", "LOCK_EX", "LOCK_NB"):
        assert fragment in lock_source

    assert "INSERT INTO writer_ownership" in sqlite_writer_session
    assert "UPDATE writer_ownership" in sqlite_writer_session
    assert "DELETE FROM writer_ownership" not in sqlite_sources
    assert "def apply_transition(" in sqlite_writer_session
    assert "def apply_global_stop_update(" in sqlite_writer_session


def test_docs_pin_private_proof_and_b2c_behavior() -> None:
    writer_doc = _read(".docs/writer-session-authority.md")

    for phrase in (
        "never persisted",
        "never serialized publicly",
        "never logged",
        "never projected",
        "never returned by safe read APIs",
        "B2c implements proof generation and verification",
        "B2c updates `writer_ownership` only during writer acquisition",
        "B2c implements an internal concrete `WriterSession`",
        "B3/B4 remain future",
    ):
        assert phrase in writer_doc
