from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path

import ge_nwp_coordinator
from ge_nwp_coordinator.sqlite_transition_select_support import _TransitionReadCapabilityFailureReason
from ge_nwp_coordinator.sqlite_writer_session import _SQLiteWriterSession
from ge_nwp_coordinator.state_store import WriterSessionFailureReason


ROOT = Path(__file__).resolve().parents[1]
B3C1_DOC = ROOT / ".docs/b3c1-prerequisite-contract.md"
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
EXPECTED_MIGRATION_0001_CHECKSUM = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"
EXPECTED_WRITER_ROW_QUERY = """SELECT
    singleton_id,
    writer_ref,
    generation,
    issued_ref,
    issuance_nonce_digest,
    acquired_at
FROM writer_ownership
ORDER BY singleton_id
LIMIT 2"""


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.index(marker)
    tail = text[start + len(marker) :]
    next_heading = tail.find("\n## ")
    return tail if next_heading == -1 else tail[:next_heading]


def _numbered_items(section: str) -> tuple[str, ...]:
    items: list[str] = []
    for raw_line in section.splitlines():
        line = raw_line.strip()
        number, dot, rest = line.partition(". ")
        if number.isdecimal() and dot:
            items.append(rest)
    return tuple(items)


def _table(section: str) -> dict[str, tuple[str, ...]]:
    rows: dict[str, tuple[str, ...]] = {}
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line.startswith("| ") or line.startswith("| ---") or line.startswith("| Case") or line.startswith(
            "| Situation"
        ):
            continue
        columns = tuple(part.strip() for part in line.strip("|").split("|"))
        rows[columns[0]] = columns[1:]
    return rows


def _source_files() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in PACKAGE_DIR.glob("*.py")
    }


def test_b3c1_prerequisite_document_status_boundary_and_split_are_static_only() -> None:
    doc = B3C1_DOC.read_text(encoding="utf-8")
    normalized = _normalized(doc)
    for phrase in (
        "Status: implemented B3c1a private WriterSession authority plumbing and B3c1b private rollback-only writer-fencing/capability mechanics",
        "no B3b2 reader integration, production caller, state mutation, or durable transaction apply",
        "B3c1 is production-unintegrated and test-executed only",
        "B3c1a implements only `_WriterSessionResource` mutation-slot ownership",
        "B3c1a implements:",
        "B3c1b implements only:",
        "Each slice requires an implementation-only prompt",
        "No fresh source snapshot is required between accepted B3c1a and B3c1b commits unless evidence conflicts.",
    ):
        assert phrase in normalized

    boundary_items = _numbered_items(_section(doc, "B3c1 Boundary"))
    assert boundary_items[:9] == (
        "the real shared per-`WriterSession` mutation slot;",
        "the smallest safe operation-lease active-authority interface;",
        "the smallest safe operation-lease durable-issuance verification interface;",
        "resource-owned state-database filesystem-authority binding through the operation lease;",
        "one private nominal rollback-only transaction controller;",
        "one private nominal transaction-read capability;",
        "one fresh existing managed read/write SQLite connection;",
        "`BEGIN IMMEDIATE`;",
        "managed schema and connection-posture validation;",
    )
    assert "B3c1 still excludes event, idempotency, and sequence readers" in normalized


def test_production_unintegrated_posture_reconciles_single_controller_path() -> None:
    b3c1 = _normalized(B3C1_DOC.read_text(encoding="utf-8"))
    b3c0a = _normalized(_read(".docs/b3c0a-transition-authority-and-order.md"))
    writer_authority = _normalized(_read(".docs/writer-session-authority.md"))
    for document in (b3c1, b3c0a, writer_authority):
        for phrase in (
            "created only by one private rollback-only transaction controller",
            "There is one controller construction path",
            "Future production invocation may occur only from `_SQLiteWriterSession.apply_transition()`",
            "During B3c1b, the controller has no production caller",
            "coherent tests may invoke the same private controller directly through private imports",
            "without adding a separate source-level `for_test` factory",
        ):
            assert phrase in document

    assert "created only inside `_SQLiteWriterSession.apply_transition()`" not in b3c0a
    assert "created only inside `_SQLiteWriterSession.apply_transition()`" not in writer_authority
    assert "`_SQLiteWriterSession.apply_global_stop_update()` remain `writer_session_mutation_unavailable`" in b3c1
    assert "contact no SQLite database" in b3c1

    production_source = "\n".join(_source_files().values())
    for forbidden in (
        "transition_transaction_for_test",
        "controller_for_test",
        "capability_for_test",
        "b3c1_for_test",
        "writer_fencing_for_test",
    ):
        assert forbidden not in production_source
    assert "make_coherent_transition_fixture_for_test" not in production_source


def test_resource_owned_mutation_slot_and_lease_identity_are_private_b3c1a_runtime() -> None:
    section = _section(B3C1_DOC.read_text(encoding="utf-8"), "B3c1a Mutation Slot")
    normalized = _normalized(section)
    for phrase in (
        "owned by `_WriterSessionResource`",
        "dedicated private `_WriterSessionMutationLease`",
        "shared by transition mutation and future global-stop mutation",
        "distinct from `_active_operations`",
        "acquired only through an active `_WriterSessionOperationLease`",
        "prompt local `writer_session_mutation_in_progress`",
        "the owning operation",
        "the resource lifecycle epoch",
        "the owner process",
        "the owner thread",
        "an opaque slot token",
        "resource operation finish defensively clears a slot owned by the operation being finished",
        "Mutation-slot publication and `_WriterSessionMutationLease` construction are externally atomic.",
        "no mutation-lease finalizer is primary lifecycle authority",
        "every exit path releases exactly once",
    ):
        assert phrase in normalized

    writer_source = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")
    assert "_active_operations" in writer_source
    for required in (
        "class _WriterSessionMutationLease",
        "class _WriterSessionMutationSlot",
        "self._mutation_slot",
        "def _acquire_mutation_lease",
        "WRITER_SESSION_MUTATION_IN_PROGRESS",
        "def _release_mutation_slot",
        "def _clear_mutation_slot_owned_by_operation_locked",
        "_MUTATION_LEASE_FACTORY",
    ):
        assert required in writer_source


def test_operation_lease_interface_and_issuance_match_are_private_b3c1a_runtime() -> None:
    section = _section(B3C1_DOC.read_text(encoding="utf-8"), "Operation-Lease Interface")
    normalized = _normalized(section)
    for phrase in (
        "_acquire_mutation_lease() -> _WriterSessionMutationLease",
        "_require_active_mutation_authority() -> None",
        "_bound_state_database_for_mutation() -> _StateDatabaseAuthorityBinding",
        "_verify_durable_writer_issuance(",
        "issuance: _DurableWriterIssuance",
        "-> _WriterIssuanceMatch",
        "`_WriterIssuanceMatch` is a closed private result",
        "`MATCH`",
        "`STALE_WRITER`",
        "exact `_DurableWriterIssuance` type",
        "structural lookalikes are not accepted",
        "retained lock",
        "writer ref, generation, issued ref, and the private proof",
        "`acquired_at` is not credential identity",
        "Every well-formed mismatch returns only `STALE_WRITER`",
        "returns the exact private filesystem-authority binding retained by the owning `_WriterSessionResource`",
        "state-root identity, the common authority-lock-file identity, and the active database-file identity",
        "The active database file must have exactly one hard link.",
        "accepts no location argument",
    ):
        assert phrase in normalized

    for forbidden in (
        "private credential object",
        "raw proof",
        "proof digest",
        "authority lock",
        "lock descriptor",
        "operation id",
        "lifecycle epoch",
        "writer metadata as authority",
        "process id",
        "thread id",
        "resource",
        "transaction epoch",
        "raw SQLite row",
        "state-root path",
        "database path",
        "filesystem identity",
        "link count",
        "connection",
    ):
        assert f"must not expose the {forbidden}" in normalized or forbidden in normalized

    writer_source = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")
    assert "_DurableWriterIssuance" in _read("src/ge_nwp_coordinator/sqlite_writer_state.py")
    for required in (
        "class _WriterIssuanceMatch",
        "_require_active_mutation_authority",
        "_verify_durable_writer_issuance",
        "credential.verify_digest",
        "type(issuance) is not _DurableWriterIssuance",
    ):
        assert required in writer_source


def test_rollback_only_controller_result_is_exact_private_enum_contract() -> None:
    doc = B3C1_DOC.read_text(encoding="utf-8")
    section = _section(doc, "Rollback-only controller result")
    normalized = _normalized(section)
    for phrase in (
        "returns exactly `_WriterIssuanceMatch`",
        "exactly two return values: `MATCH` and `STALE_WRITER`",
        "returns `_WriterIssuanceMatch.MATCH` only after all of the following have succeeded",
        "returns `_WriterIssuanceMatch.STALE_WRITER` only after all of the following",
        "returns neither enum value before rollback and close complete",
        "produce `database_integrity_failure` and no enum",
        "produce `mutation_failed` and no enum",
        "Operational open, `BEGIN`, managed-validation, `SELECT`, cursor-close, controller",
        "No rollback-only B3c1 path returns `commit_outcome_unknown`",
        "`_WriterIssuanceMatch.STALE_WRITER` is an internal private result",
        "B3c3 dry-run integration owns the first private conversion",
        "returned only after rollback and close succeed and before any idempotency disclosure",
        "B3c1b itself still does not perform that conversion",
        "must not directly return `TransitionConflict`",
        "`CommittedTransition`",
        "`TransitionApplyOutcome`",
        "Do not add a second enum, dataclass, union, or result model for fenced versus stale outcomes",
        "`_WriterIssuanceMatch` remains private and unexported",
        "B3c3 contracts add a separate private dry-run result algebra",
        "That algebra is not a B3c1 fencing result model",
    ):
        assert phrase in normalized

    result_items = _numbered_items(section)
    assert result_items[:7] == (
        "durable issuance verification returned `MATCH`;",
        "nominal capability was created;",
        "nominal capability was permanently invalidated;",
        "rollback succeeded;",
        "connection-close attempt succeeded;",
        "no B3b2 reader was called;",
        "no durable state was changed.",
    )
    assert result_items[7] == "the durable row was well formed;"
    assert result_items[9:] == (
        "no nominal capability was created;",
        "rollback succeeded;",
        "connection-close attempt succeeded.",
    )
    assert "writer ref, generation, issued ref, or proof verification produced the closed `STALE_WRITER` result" in normalized

    for non_claim in (
        "does not mean transition accepted",
        "apply completed",
        "event persisted",
        "replay persisted",
        "state changed",
        "transaction committed",
    ):
        assert non_claim in normalized

    ambiguous = _normalized(doc).lower()
    for forbidden in (
        "planned " "fenced result",
        "planned " "stale result",
        "planned " "fenced or " "stale result",
        "successful " "fencing result",
        "return the " "planned " "fenced or " "stale result",
    ):
        assert forbidden not in ambiguous

    writer_source = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")
    production_source = "\n".join(_source_files().values())
    assert "class _WriterIssuanceMatch(str, Enum):" in writer_source
    assert "_WriterIssuanceMatch" not in ge_nwp_coordinator.__all__
    assert not hasattr(ge_nwp_coordinator, "_WriterIssuanceMatch")
    transaction_source = _read("src/ge_nwp_coordinator/sqlite_transition_transaction.py")
    assert "def _run_rollback_only_writer_fencing(" in transaction_source
    assert "class _RollbackOnlyTransitionTransactionController" in transaction_source
    assert "_run_rollback_only_writer_fencing" not in ge_nwp_coordinator.__all__
    assert "_RollbackOnlyTransitionTransactionController" not in ge_nwp_coordinator.__all__
    assert "sqlite_transition_transaction" not in ge_nwp_coordinator.__all__
    assert "sqlite_transition_transaction" not in _read("src/ge_nwp_coordinator/__init__.py")
    assert "class _SQLiteTransitionTransactionController" not in production_source


def test_writer_row_query_parser_ownership_and_fencing_matrix_are_pinned() -> None:
    doc = B3C1_DOC.read_text(encoding="utf-8")
    query_section = _section(doc, "Writer-Row Query")
    assert EXPECTED_WRITER_ROW_QUERY in query_section
    normalized_query = _normalized(query_section)
    for phrase in (
        "reads `writer_ownership` only",
        "explicit columns",
        "no `SELECT *`",
        "no idempotency table",
        "no event table",
        "no current-state table",
        "bounded cardinality",
        "exact built-in tuple rows",
        "reuse `_parse_writer_ownership_rows`",
        "must not create a second writer-row grammar",
        "must not reuse the acquisition reader's outward error taxonomy as-is",
        "B3c1b adds no other production SQL.",
        "closes the writer-row cursor before validating row type/length",
        "original fetch classification remains primary",
        "fetch succeeded but cursor close fails",
    ):
        assert phrase in normalized_query

    matrix = _table(_section(doc, "Writer Fencing"))
    assert matrix == {
        "closed session": ("local `WriterSessionError` before SQLite",),
        "process-mismatched session": ("local `WriterSessionError` before SQLite",),
        "mutation slot occupied": ("local `writer_session_mutation_in_progress` before SQLite",),
        "absent writer row while an active session exists": ("`database_integrity_failure`",),
        "multiple writer rows": ("`database_integrity_failure`",),
        "malformed writer row": ("`database_integrity_failure`",),
        "managed-schema contradiction": ("`database_integrity_failure`",),
        "writer-query contradiction": ("`database_integrity_failure`",),
        "retained root/lock/database identity mismatch": ("`database_integrity_failure`",),
        "active database hard-link alias": ("`database_integrity_failure`",),
        "operational open failure": ("`mutation_failed`",),
        "operational BEGIN failure": ("`mutation_failed`",),
        "operational managed-validation failure": ("`mutation_failed`",),
        "operational SELECT failure": ("`mutation_failed`",),
        "successful fetch plus cursor-close failure": ("`mutation_failed`",),
        "well-formed writer ref mismatch": ("`stale_writer_token`",),
        "well-formed generation mismatch": ("`stale_writer_token`",),
        "well-formed issued-ref mismatch": ("`stale_writer_token`",),
        "proof mismatch": ("`stale_writer_token`",),
    }
    normalized_fencing = _normalized(_section(doc, "Writer Fencing"))
    assert "Fencing occurs before all idempotency, current-state, event, replay, and context reads." in normalized_fencing
    assert "Stale writer results carry no event or replay and disclose no key existence." in normalized_fencing
    assert "controller database open binding == WriterSession resource-owned state-database binding" in normalized_fencing
    assert "matching `writer_ownership` row in an independent or cloned database is insufficient authority" in normalized_fencing
    assert "hard-link alias to the active database file fails closed" in normalized_fencing
    assert "There is no automatic reacquisition, takeover, TTL, heartbeat, or failover." in normalized_fencing


def test_nominal_capability_epoch_contract_uses_existing_closed_reasons() -> None:
    section = _section(B3C1_DOC.read_text(encoding="utf-8"), "Nominal Capability And Epoch")
    normalized = _normalized(section)
    for phrase in (
        "`src/ge_nwp_coordinator/sqlite_transition_transaction.py`",
        "This module owns one private nominal rollback-only transaction controller",
        "private nominal rollback-only transaction controller",
        "private nominal transaction-read capability",
        "no public constructor",
        "no package-root export",
        "no finalizer",
        "no independent close",
        "no public connection property",
        "created only by the controller after successful writer fencing",
        "Structural `_TransitionReadCapability` conformance is not authority.",
        "one opaque epoch",
        "private, identity-only",
        "same-process and same-thread only",
        "transition_read_capability_expired",
        "transition_read_capability_unavailable",
        "process_mismatch",
        "thread_mismatch",
        "Transaction A's capability cannot revive during transaction B",
    ):
        assert phrase in normalized

    assert _TransitionReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE.value == "transition_read_capability_unavailable"
    assert _TransitionReadCapabilityFailureReason.CAPABILITY_EXPIRED.value == "transition_read_capability_expired"
    assert _TransitionReadCapabilityFailureReason.PROCESS_MISMATCH.value == "process_mismatch"
    assert _TransitionReadCapabilityFailureReason.THREAD_MISMATCH.value == "thread_mismatch"
    assert (PACKAGE_DIR / "sqlite_transition_transaction.py").exists()

    class_names: set[str] = set()
    for source in _source_files().values():
        class_names.update(
            node.name for node in ast.walk(ast.parse(source)) if isinstance(node, ast.ClassDef)
        )
    assert "_WriterSessionMutationLease" in class_names
    assert "_RollbackOnlyTransitionTransactionController" in class_names
    assert "_SQLiteTransitionTransactionController" not in class_names
    assert "_SQLiteTransitionReadCapability" in class_names


def test_rollback_only_lifecycle_and_cleanup_precedence_are_exact() -> None:
    doc = B3C1_DOC.read_text(encoding="utf-8")
    lifecycle_items = _numbered_items(_section(doc, "Rollback-Only Controller Lifecycle"))
    assert lifecycle_items == (
        "enter with an active operation lease;",
        "acquire the mutation lease;",
        "derive the resource-owned state-database binding from the operation lease;",
        "open one fresh existing managed read/write connection through the bound private open helper;",
        "execute `BEGIN IMMEDIATE`;",
        "revalidate the retained root/lock/database binding after `BEGIN`;",
        "validate managed schema and connection posture;",
        "query and parse the writer row;",
        "verify durable issuance;",
        "on `MATCH`, create the nominal capability;",
        "call no B3b2 reader;",
        "invalidate the capability;",
        "roll back;",
        "close the connection;",
        "release the mutation lease;",
        "exit the operation lease.",
    )
    lifecycle = _normalized(_section(doc, "Rollback-Only Controller Lifecycle"))
    for state in ("NEW", "TRANSACTION_ACTIVE", "FENCED", "CAPABILITY_ACTIVE", "RESOLVING", "CLOSED"):
        assert f"`{state}`" in lifecycle
    assert "B3c1 never commits." in lifecycle
    assert "`COMMIT` and `commit_outcome_unknown` remain outside the rollback-only B3c1 tranche." in lifecycle

    precedence = _table(_section(doc, "Cleanup And Error Precedence"))
    assert precedence == {
        "Fencing matched; invalidation, rollback, and close succeed": ("`_WriterIssuanceMatch.MATCH`",),
        "Well-formed stale mismatch; rollback and close succeed": ("`_WriterIssuanceMatch.STALE_WRITER`",),
        "Missing/multiple/malformed row": ("`database_integrity_failure`",),
        "Schema/query contradiction": ("`database_integrity_failure`",),
        "Operational failure": ("`mutation_failed`",),
        "Cursor close after successful fetch": ("`mutation_failed`",),
        "Rollback failure": ("`mutation_failed`; no enum",),
        "Close failure": ("`mutation_failed`; no enum",),
        "Failed bound-open admission plus rejected-connection close failure": (
            "primary structural/operational open failure preserved; no connection returned",
        ),
        "Any rollback-only path": ("never `commit_outcome_unknown`",),
    }
    normalized_precedence = _normalized(_section(doc, "Cleanup And Error Precedence"))
    assert "Session or slot failure before SQLite remains an existing local `WriterSessionError`" in normalized_precedence
    assert "Capability invalidation precedes rollback." in normalized_precedence
    assert "`_WriterIssuanceMatch.STALE_WRITER` is returned only after rollback and close both succeed." in normalized_precedence
    assert "The controller returns no enum before cleanup completes." in normalized_precedence
    assert "The mutation slot remains held through the connection-close attempt." in normalized_precedence
    assert "Failed bound-open admission plus rejected-connection close failure" in normalized_precedence
    assert "No finalizer is the primary cleanup path." in normalized_precedence


def test_public_mutation_methods_remain_unavailable_and_contact_no_sqlite() -> None:
    apply_source = inspect.getsource(_SQLiteWriterSession.apply_transition)
    global_stop_source = inspect.getsource(_SQLiteWriterSession.apply_global_stop_update)
    for source in (apply_source, global_stop_source):
        assert "operation_guard" in source
        assert "WRITER_SESSION_MUTATION_UNAVAILABLE" in source
        for forbidden in (
            "open_existing_sqlite_connection",
            "BEGIN IMMEDIATE",
            "_read_current_work_item",
            "_borrow_connection_for_select",
            "transition_events",
            "global_stop_events",
            "INSERT",
            "UPDATE",
            "COMMIT",
            "ROLLBACK",
        ):
            assert forbidden not in source

    assert WriterSessionFailureReason.WRITER_SESSION_MUTATION_UNAVAILABLE.value == "writer_session_mutation_unavailable"
    assert WriterSessionFailureReason.WRITER_SESSION_MUTATION_IN_PROGRESS.value == "writer_session_mutation_in_progress"


def test_docs_cross_reference_b3c1a_b3c1b_and_no_mutation_or_migration_exists() -> None:
    for path in (
        "AGENTS.md",
        "README.md",
        ".docs/architecture.md",
        ".docs/durable-state-model.md",
        ".docs/writer-session-authority.md",
        ".docs/b3c1a-writer-session-authority.md",
        ".docs/b3-transition-persistence-contract.md",
        ".docs/b3c0a-transition-authority-and-order.md",
        ".docs/sqlite-state-backend-adr.md",
    ):
        normalized = _normalized(_read(path))
        assert "B3c1" in normalized
        assert (
            ".docs/b3c1-prerequisite-contract.md" in normalized
            or ".docs/b3c1a-writer-session-authority.md" in normalized
            or path in {"AGENTS.md", "README.md"}
        )

    source = "\n".join(_source_files().values())
    for forbidden in (
        "class _SQLiteTransitionTransactionController",
        "def assemble_transition_context",
        "def verify_writer_fencing",
        "INSERT INTO transition_events",
        "UPDATE work_items",
        "UPDATE global_stop_current",
    ):
        assert forbidden not in source
    assert "def _run_rollback_only_writer_fencing(" in source
    assert "class _SQLiteTransitionReadCapability" in source

    migrations = sorted(path.name for path in (PACKAGE_DIR / "sqlite_migrations").glob("*.sql"))
    assert migrations == ["0001_initial.sql"]
    migration_bytes = (PACKAGE_DIR / "sqlite_migrations/0001_initial.sql").read_bytes()
    assert hashlib.sha256(migration_bytes).hexdigest() == EXPECTED_MIGRATION_0001_CHECKSUM
