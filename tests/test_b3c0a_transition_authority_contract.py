from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path
import textwrap

from ge_nwp_coordinator.sqlite_writer_session import _SQLiteWriterSession, _WriterSessionResource
from ge_nwp_coordinator.state_store import WriterSessionFailureReason


ROOT = Path(__file__).resolve().parents[1]
B3C0A_DOC = ROOT / ".docs/b3c0a-transition-authority-and-order.md"
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
EXPECTED_MIGRATION_0001_CHECKSUM = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"

EXPECTED_APPLY_ORDER = (
    "acquire `_WriterSessionOperationLease`, including externally atomic owner-process, active-session, and retained-lock validation;",
    "validate exact TransitionCommand type and already-established canonical digest;",
    "enforce non-READY dependency ref is null and budget_cost is zero;",
    "acquire the shared per-session mutation slot;",
    "derive the resource-owned root/lock/database binding from the active operation lease;",
    "open one existing managed read/write connection through that binding;",
    "BEGIN IMMEDIATE;",
    "revalidate the retained binding and validate current managed schema and posture inside the transaction;",
    "load and parse writer_ownership;",
    "verify writer fencing;",
    "create the nominal capability;",
    "inspect event-owned idempotency;",
    "on exact replay, skip all changed context;",
    "on idempotency-key digest mismatch, return conflict;",
    "read current work item;",
    "if absent, work_item_not_found;",
    "compare expected version;",
    "if mismatch, expected_version_conflict;",
    "read lease identity;",
    "read admitted backlog;",
    "read authorization;",
    "read READY dependency only when required;",
    "read global-stop singleton;",
    "apply all cross-record binding and authorization-support checks;",
    "capture one whole-second UTC transaction timestamp;",
    "derive LeaseRuntimeDecision;",
    "construct TransitionContext;",
    "invoke evaluator exactly once;",
    "allocate event sequence;",
    "insert event and replay snapshot;",
    "on acceptance, CAS-update current work item;",
    "invalidate capability;",
    "commit or roll back;",
    "close connection;",
    "return only after transaction resolution.",
)

EXPECTED_GLOBAL_STOP_ORDER_PREFIX = (
    "acquire the operation lease; acquisition performs owner-process and active-session validation and returns only after the retained authority lock is confirmed active;",
    "perform existing future global-stop typed command/operator-decision local checks;",
    "acquire the shared per-session mutation slot;",
    "derive the resource-owned root/lock/database binding from the active operation lease;",
    "open one existing managed read/write connection through that binding;",
    "execute `BEGIN IMMEDIATE`;",
    "revalidate the retained binding and validate managed schema/posture inside the transaction;",
    "load and parse `writer_ownership`;",
    "verify writer fencing;",
    "look up `global_stop_events` by idempotency key;",
)

EXPECTED_MUTATION_SLOT_LIFETIME = (
    "the same future private session-owned mutation slot is shared by transition mutation and global-stop mutation;",
    "the slot is acquired after mutation-specific local command checks and before opening any database connection;",
    "the slot is retained through database open, `BEGIN IMMEDIATE`, managed validation, writer fencing, idempotency, all reads, cross-record binding, timestamp/runtime/context construction, evaluation, writes, capability invalidation, commit or rollback attempt, transaction-resolution error classification, and connection-close attempt;",
    "the slot is not released merely because commit or rollback was attempted and remains held while connection cleanup is still running;",
    "the slot is released only after the connection-close attempt completes and before the outer `_WriterSessionOperationLease` exits;",
    "the slot is released on every path, including local transaction setup failure, reader failure, evaluator failure, write failure, rollback failure, commit uncertainty, and committed-success close failure;",
    "a second transition/global-stop mutation cannot begin while the first is committing, rolling back, classifying transaction outcome, or closing the connection;",
    "that second attempt fails promptly with future-only `writer_session_mutation_in_progress`, and this session-level rule never degrades into SQLite busy/locked behavior;",
    "the slot remains future and unimplemented in B3c0a.",
)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.index(marker)
    tail = text[start + len(marker) :]
    next_heading = tail.find("\n## ")
    return tail if next_heading == -1 else tail[:next_heading]


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _numbered_items(section: str) -> tuple[str, ...]:
    items: list[str] = []
    for raw_line in section.splitlines():
        line = raw_line.strip()
        number, dot, rest = line.partition(". ")
        if number.isdecimal() and dot:
            items.append(rest)
    return tuple(items)


def _numbered_block_after(text: str, marker: str) -> tuple[str, ...]:
    start = text.index(marker) + len(marker)
    tail = text[start:]
    next_heading = tail.find("\n## ")
    if next_heading != -1:
        tail = tail[:next_heading]
    return _numbered_items(tail)


def _table(section: str) -> dict[str, tuple[str, ...]]:
    rows: dict[str, tuple[str, ...]] = {}
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line.startswith("| ") or line.startswith("| ---") or "Case" in line:
            continue
        columns = tuple(part.strip() for part in line.strip("|").split("|"))
        rows[columns[0]] = columns[1:]
    return rows


def test_b3c0a_document_status_scope_and_future_staging_are_static_only() -> None:
    doc = B3C0A_DOC.read_text(encoding="utf-8")
    normalized = _normalized(doc)
    assert "Status: implemented contract/static prerequisite; no transaction capability or mutation implementation." in normalized
    for phrase in (
        "does not implement a concrete transaction capability",
        "does not implement a concrete transaction capability, transaction controller, writer-fencing `SELECT`",
        "B3c0b has since implemented pure/static transition-event row, replay, idempotency, and sequence contracts",
        "B3c1 has since frozen the prerequisite contract",
        "B3 tests-only coherent fixtures are implemented under `tests/` only",
        "B3c1a implements the runtime mutation slot",
        "B3c1b has since implemented private rollback-only writer fencing and nominal capability mechanics",
            "B3c2 has since implemented private transaction-internal event/replay idempotency and observed maximum-sequence readers",
            "B3c3 contracts are now pinned",
            "implemented private rollback-only dry-run runtime",
            "B3c4a now freezes only the pure/static write specifications",
            "Each future stage requires a separate implementation patch and standalone audit.",
        ):
            assert phrase in normalized

    for path in (
        "AGENTS.md",
        "README.md",
        ".docs/architecture.md",
        ".docs/durable-state-model.md",
        ".docs/p1-1-transition-event-algebra.md",
        ".docs/b3-transition-persistence-contract.md",
        ".docs/b3b2a-read-scope-and-query-contracts.md",
        ".docs/b3b2b-select-readers.md",
        ".docs/sqlite-state-backend-adr.md",
        ".docs/writer-session-authority.md",
    ):
        assert "B3c0a" in _read(path)


def test_exact_transition_apply_order_is_pinned_once_in_b3c0a() -> None:
    section = _section(B3C0A_DOC.read_text(encoding="utf-8"), "Transition Apply Order")
    items = _numbered_items(section)
    assert items == EXPECTED_APPLY_ORDER
    assert items[0] == EXPECTED_APPLY_ORDER[0]
    assert not any("reject closed or process-mismatched session" in item for item in items[1:])


def test_current_expected_context_timestamp_and_evaluator_relative_order() -> None:
    order = list(EXPECTED_APPLY_ORDER)
    assert order.index(EXPECTED_APPLY_ORDER[0]) < order.index(
        "validate exact TransitionCommand type and already-established canonical digest;"
    )
    assert order.index("enforce non-READY dependency ref is null and budget_cost is zero;") < order.index(
        "acquire the shared per-session mutation slot;"
    )
    assert order.index("acquire the shared per-session mutation slot;") < order.index(
        "derive the resource-owned root/lock/database binding from the active operation lease;"
    )
    assert order.index("derive the resource-owned root/lock/database binding from the active operation lease;") < order.index(
        "open one existing managed read/write connection through that binding;"
    )
    assert order.index("open one existing managed read/write connection through that binding;") < order.index("BEGIN IMMEDIATE;")
    assert order.index("BEGIN IMMEDIATE;") < order.index(
        "revalidate the retained binding and validate current managed schema and posture inside the transaction;"
    )
    assert order.index(
        "revalidate the retained binding and validate current managed schema and posture inside the transaction;"
    ) < order.index(
        "verify writer fencing;"
    )
    assert order.index("verify writer fencing;") < order.index("create the nominal capability;")
    assert order.index("create the nominal capability;") < order.index("inspect event-owned idempotency;")
    assert order.index("inspect event-owned idempotency;") < order.index("read current work item;")
    assert order.index("read current work item;") < order.index("compare expected version;")
    assert order.index("compare expected version;") < order.index("read lease identity;")
    assert order.index("read lease identity;") < order.index("read admitted backlog;")
    assert order.index("read admitted backlog;") < order.index("read authorization;")
    assert order.index("read authorization;") < order.index("read READY dependency only when required;")
    assert order.index("read READY dependency only when required;") < order.index("read global-stop singleton;")
    assert order.index("apply all cross-record binding and authorization-support checks;") < order.index(
        "capture one whole-second UTC transaction timestamp;"
    )
    assert order.index("capture one whole-second UTC transaction timestamp;") < order.index(
        "derive LeaseRuntimeDecision;"
    )
    assert order.index("derive LeaseRuntimeDecision;") < order.index("construct TransitionContext;")
    assert order.index("construct TransitionContext;") < order.index("invoke evaluator exactly once;")


def test_operation_lease_acquisition_source_contract_is_static_only() -> None:
    """This is structural/source-order evidence only.

    Runtime unwind and cleanup are proven by the separate inactive-lock
    behavioral regression through the concrete WriterSession mutation methods.
    """
    source = textwrap.dedent(inspect.getsource(_WriterSessionResource._begin_operation))
    tree = ast.parse(source)
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)

    operation_registration = "self._active_operations[operation_id] = owner_thread"
    lease_construction = "lease = _WriterSessionOperationLease("
    active_lock_check = "if not authority_lock.active:"

    assert source.index("self._require_owner_process()") < source.index(operation_registration)
    for pre_registration_check in (
        "self._state != _ACTIVE",
        "self._credential is None",
        "self._authority_lock is None",
    ):
        assert source.index(pre_registration_check) < source.index(operation_registration)
    assert source.index("credential = self._credential") < source.index(operation_registration)
    assert source.index("authority_lock = self._authority_lock") < source.index(operation_registration)
    assert source.index(operation_registration) < source.index(lease_construction)
    assert source.index(lease_construction) < source.index(active_lock_check)
    assert source.index(active_lock_check) < source.index("return lease")

    active_lock_branch = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.UnaryOp)
        and isinstance(node.test.op, ast.Not)
        and isinstance(node.test.operand, ast.Attribute)
        and node.test.operand.attr == "active"
        and isinstance(node.test.operand.value, ast.Name)
        and node.test.operand.value.id == "authority_lock"
    )
    branch_source = "\n".join(
        ast.get_source_segment(source, statement) or "" for statement in active_lock_branch.body
    )
    assert branch_source.index("lease._close()") < branch_source.index("self.close_from_owner()")
    assert branch_source.index("self.close_from_owner()") < branch_source.index(
        "raise WriterSessionError(WriterSessionFailureReason.WRITER_SESSION_CLOSED)"
    )
    assert not any(isinstance(node, ast.Return) for node in ast.walk(active_lock_branch))
    return_nodes = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
    assert len(return_nodes) == 1
    assert return_nodes[0].lineno > active_lock_branch.end_lineno


def test_global_stop_adr_uses_shared_pre_sqlite_mutation_prefix() -> None:
    adr = _read(".docs/sqlite-state-backend-adr.md")
    items = _numbered_block_after(adr, "Global-stop mutation transaction remains future and unimplemented.")
    assert items[: len(EXPECTED_GLOBAL_STOP_ORDER_PREFIX)] == EXPECTED_GLOBAL_STOP_ORDER_PREFIX
    assert "BEGIN IMMEDIATE" not in items[0]
    assert items.index(
        EXPECTED_GLOBAL_STOP_ORDER_PREFIX[0]
    ) < items.index("perform existing future global-stop typed command/operator-decision local checks;")
    assert items.index("perform existing future global-stop typed command/operator-decision local checks;") < items.index(
        "acquire the shared per-session mutation slot;"
    )
    assert items.index("acquire the shared per-session mutation slot;") < items.index(
        "derive the resource-owned root/lock/database binding from the active operation lease;"
    )
    assert items.index("derive the resource-owned root/lock/database binding from the active operation lease;") < items.index(
        "open one existing managed read/write connection through that binding;"
    )
    assert items.index("open one existing managed read/write connection through that binding;") < items.index(
        "execute `BEGIN IMMEDIATE`;"
    )
    assert items.index("revalidate the retained binding and validate managed schema/posture inside the transaction;") < items.index(
        "verify writer fencing;"
    )
    assert items.index("verify writer fencing;") < items.index(
        "look up `global_stop_events` by idempotency key;"
    )


def test_nominal_capability_owner_contract_has_no_concrete_runtime() -> None:
    doc = B3C0A_DOC.read_text(encoding="utf-8")
    section = _section(doc, "Nominal Capability Ownership")
    normalized = _normalized(section)
    for phrase in (
        "one private nominal transaction controller",
        "one private nominal transaction-read capability",
        "not trusted through structural Protocol conformance",
        "created only by one private transition transaction controller",
        "There is one controller construction path",
        "Future production invocation may occur only from `_SQLiteWriterSession.apply_transition()`",
        "During B3c4b, the controller still has no public production caller",
        "coherent tests may invoke the same private controller directly through private imports",
        "without adding a separate source-level `for_test` factory",
        "while one valid `_WriterSessionOperationLease` is active",
        "after successful fencing",
        "module-private construction path or sentinel",
        "No raw-connection factory",
        "not escape the controller lifecycle",
        "`_SQLiteWriterSession.apply_transition()` and `_SQLiteWriterSession.apply_global_stop_update()` remain",
    ):
        assert phrase in normalized

    support_source = _read("src/ge_nwp_coordinator/sqlite_transition_select_support.py")
    support_tree = ast.parse(support_source)
    class_names = {node.name for node in ast.walk(support_tree) if isinstance(node, ast.ClassDef)}
    assert "_TransitionReadCapability" in class_names
    assert not any(name.endswith("Capability") and name != "_TransitionReadCapability" for name in class_names)
    assert "runtime_checkable" not in support_source


def test_operation_lease_interface_and_one_mutation_policy_are_contract_only() -> None:
    doc = B3C0A_DOC.read_text(encoding="utf-8")
    lease_section = _section(doc, "Operation Guard And Private Credential Boundary")
    mutation_section = _section(doc, "One Mutation Per Session")
    combined = _normalized(lease_section + mutation_section)
    for phrase in (
        "pre-registration validation",
        "provisional acquisition",
        "final retained-lock validation",
        "inactive-lock failure",
        "successful acquisition",
        "Callers never receive an operation lease backed by an inactive authority lock",
        "An inactive-lock acquisition leaves no registered operation",
        "attempts no mutation slot",
        "opens no SQLite connection",
        "a safe active-authority check",
        "verification of one already-parsed durable writer issuance",
        "must not expose the private credential object",
        "reader capability receives none of those values",
        "at most one mutation transaction may be active per `WriterSession`",
        "transition mutation and future global-stop mutation",
        "shared future transition/global-stop mutation prefix",
        "acquire the shared per-session mutation slot",
        "`writer_session_mutation_in_progress`",
        "B2c still raises `writer_session_mutation_unavailable`",
    ):
        assert phrase in combined

    assert (
        WriterSessionFailureReason.WRITER_SESSION_MUTATION_IN_PROGRESS.value
        == "writer_session_mutation_in_progress"
    )
    apply_source = inspect.getsource(_SQLiteWriterSession.apply_transition)
    global_stop_source = inspect.getsource(_SQLiteWriterSession.apply_global_stop_update)
    assert "WRITER_SESSION_MUTATION_UNAVAILABLE" in apply_source
    assert "WRITER_SESSION_MUTATION_IN_PROGRESS" not in apply_source
    assert "WRITER_SESSION_MUTATION_UNAVAILABLE" in global_stop_source
    assert "WRITER_SESSION_MUTATION_IN_PROGRESS" not in global_stop_source


def test_mutation_slot_lifetime_contract_is_bounded_to_b3c0a_section() -> None:
    section = _section(B3C0A_DOC.read_text(encoding="utf-8"), "Mutation-Slot Lifetime")
    items = _numbered_items(section)
    assert items == EXPECTED_MUTATION_SLOT_LIFETIME
    assert items.index(
        "the slot is acquired after mutation-specific local command checks and before opening any database connection;"
    ) < items.index(
        "the slot is retained through database open, `BEGIN IMMEDIATE`, managed validation, writer fencing, idempotency, all reads, cross-record binding, timestamp/runtime/context construction, evaluation, writes, capability invalidation, commit or rollback attempt, transaction-resolution error classification, and connection-close attempt;"
    )
    assert "capability invalidation" in items[2]
    assert "commit or rollback attempt" in items[2]
    assert "connection-close attempt" in items[2]
    assert "not released merely because commit or rollback was attempted" in items[3]
    assert "released only after the connection-close attempt completes" in items[4]
    assert "before the outer `_WriterSessionOperationLease` exits" in items[4]
    assert "released on every path" in items[5]
    assert "transition mutation and global-stop mutation" in items[0]
    assert "committing, rolling back, classifying transaction outcome, or closing the connection" in items[6]
    assert "`writer_session_mutation_in_progress`" in items[7]
    assert "never degrades into SQLite busy/locked behavior" in items[7]
    assert "future and unimplemented" in items[8]

    writer_source = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")
    read_scope_source = _read("src/ge_nwp_coordinator/sqlite_transition_read_scope.py")
    assert "_shared_mutation_slot" not in writer_source
    assert "_shared_mutation_slot" not in read_scope_source


def test_writer_fencing_classification_matrix_and_idempotency_order() -> None:
    section = _section(B3C0A_DOC.read_text(encoding="utf-8"), "Writer Fencing")
    matrix = _table(section)
    expected = {
        "no writer row while an active issued session exists": ("`database_integrity_failure`",),
        "malformed writer row": ("`database_integrity_failure`",),
        "well-formed row with different writer ref": ("`stale_writer_token`",),
        "well-formed row with different generation": ("`stale_writer_token`",),
        "well-formed row with different issued ref": ("`stale_writer_token`",),
        "proof mismatch": ("`stale_writer_token`",),
        "closed session": ("`WriterSessionError` before SQLite",),
        "process-mismatched session": ("`WriterSessionError` before SQLite",),
        "schema/query contradiction while reading writer state": ("`database_integrity_failure`",),
        "operational SQLite failure": ("`mutation_failed`",),
    }
    assert matrix == expected
    normalized = _normalized(section)
    assert "Stale writer precedes idempotency disclosure." in normalized
    assert "returns only `stale_writer_token`" in normalized
    assert "no key-existence, replay, digest mismatch, proof mismatch, or conflict detail" in normalized


def test_conflict_integrity_matrix_and_reader_ownership_are_pinned() -> None:
    section = _section(B3C0A_DOC.read_text(encoding="utf-8"), "Context And Error Ownership")
    matrix = _table(section)
    expected = {
        "current work item absent": ("B3c apply boundary", "`work_item_not_found`"),
        "expected-version mismatch": ("B3c apply boundary", "`expected_version_conflict`"),
        "exact replay": ("B3c apply boundary", "`CommittedTransition(replayed=True)`"),
        "same key with different command digest": ("B3c apply boundary", "`idempotency_key_reuse_conflict`"),
        "missing lease identity": ("B3c apply boundary", "`validation_failed`"),
        "missing authorization": ("B3c apply boundary", "`validation_failed`"),
        "missing READY dependency": ("B3c apply boundary", "`validation_failed`"),
        "missing admitted backlog after current-state binding": ("B3c apply boundary", "`database_integrity_failure`"),
        "missing global-stop singleton": ("reader or B3c apply boundary", "`database_integrity_failure`"),
        "command refs inconsistent with valid authoritative rows": ("B3c apply boundary", "`validation_failed`"),
        "contradiction among authoritative persisted rows": ("B3c apply boundary", "`database_integrity_failure`"),
        "evaluator PRE_APPLY_INVALID after successful B3c binding": (
            "B3c apply boundary",
            "`database_integrity_failure`",
        ),
        "domain rejection": ("B3c apply boundary", "one durable event and unchanged replay/current record"),
        "acceptance": ("B3c apply boundary", "one durable event and one CAS current-state update"),
    }
    assert matrix == expected
    normalized = _normalized(section)
    assert "Current work item and expected version are resolved before prerequisite context rows." in normalized
    assert "No reader constructs `TransitionConflict`, `TransitionEvent`, `TransitionContext`, reports, replay, or mutation output." in normalized
    assert "`operator_policy` remains schema vocabulary only" in normalized


def test_timestamp_invalidation_resolution_and_collision_posture_are_pinned() -> None:
    doc = B3C0A_DOC.read_text(encoding="utf-8")
    timestamp = _normalized(_section(doc, "Timestamp Capture"))
    invalidation = _normalized(_section(doc, "Capability Invalidation"))
    precedence = _normalized(_section(doc, "Resolution Precedence"))
    collision = _normalized(_section(doc, "Identity And Sequence Collision Posture"))

    for phrase in (
        "No transaction timestamp is generated on exact replay",
        "after all prerequisite rows have been loaded and cross-bound successfully",
        "`LeaseRuntimeDecision.evaluated_at`",
        "`transition_events.created_at`",
        "accepted `work_items.updated_at`",
        "Timestamp-generation failure is `mutation_failed` with no event",
    ):
        assert phrase in timestamp
    assert "invalidated before every commit or rollback attempt" in invalidation
    assert "must not become valid after another transaction starts on the same connection" in invalidation
    for phrase in (
        "Rollback failure:",
        "`mutation_failed` supersedes a planned replay",
        "Commit attempt fails:",
        "return `commit_outcome_unknown`",
        "Commit succeeds and connection close fails:",
        "committed outcome remains committed",
        "Event-ref or event-sequence uniqueness collision after idempotency miss:",
        "never regenerate event identity or sequence outside the transaction",
    ):
        assert phrase in precedence
    assert "event_sequence` is ordering metadata, not event identity" in collision
    assert "Signed SQLite maximum overflow remains `event_sequence_exhausted`." in collision


def test_static_runtime_boundary_still_has_no_b3c_transition_apply_implementation() -> None:
    writer_source = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")
    read_scope_source = _read("src/ge_nwp_coordinator/sqlite_transition_read_scope.py")
    persistence_source = _read("src/ge_nwp_coordinator/persistence_contracts.py")
    sqlite_runtime_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in PACKAGE_DIR.glob("sqlite_*.py")
        if path.name not in {"sqlite_transition_event_contracts.py", "sqlite_transition_write_contracts.py"}
    )
    transition_event_contract_source = _read("src/ge_nwp_coordinator/sqlite_transition_event_contracts.py")

    apply_source = inspect.getsource(_SQLiteWriterSession.apply_transition)
    global_stop_source = inspect.getsource(_SQLiteWriterSession.apply_global_stop_update)
    for forbidden in (
        "open_existing_sqlite_connection",
        "BEGIN IMMEDIATE",
        "_read_durable_writer_issuance",
        "_read_current_work_item",
        "evaluate_transition",
        "transition_events",
        "UPDATE work_items",
        "COMMIT",
        "ROLLBACK",
    ):
        assert forbidden not in apply_source
    assert "WRITER_SESSION_MUTATION_UNAVAILABLE" in apply_source

    for forbidden in (
        "open_existing_sqlite_connection",
        "BEGIN IMMEDIATE",
        "global_stop_events",
        "UPDATE global_stop_current",
        "COMMIT",
        "ROLLBACK",
    ):
        assert forbidden not in global_stop_source
    assert "WRITER_SESSION_MUTATION_UNAVAILABLE" in global_stop_source

    for forbidden in (
        "class _TransitionTransactionController",
        "class _B3cTransitionReadCapability",
        "_shared_mutation_slot",
        "_create_for_b3c_managed_transition_transaction",
        "transition_events",
        "replay_work_item",
        "idempotency_key",
        "event_sequence",
        "expected_version",
        "writer_ownership",
        "TransitionContext",
        "TransitionConflict",
        "validate_b3_work_item_authority_binding",
    ):
        assert forbidden not in read_scope_source
    assert "sqlite3.connect" not in read_scope_source
    assert "TransitionEventRecordEnvelope" in persistence_source
    assert "transition_event_record_envelope_from_row" in persistence_source
    assert "ReplayWorkItemRecord" not in persistence_source
    assert "_TRANSITION_EVENT_MAX_SEQUENCE_SELECT" in transition_event_contract_source
    assert "MAX({sequence_column})" in transition_event_contract_source
    assert "MAX(event_sequence" not in sqlite_runtime_sources
    assert "evaluate_transition" in sqlite_runtime_sources
    assert "INSERT INTO transition_events" not in sqlite_runtime_sources
    assert "UPDATE work_items" not in sqlite_runtime_sources

    assert "sqlite_transition_fixtures" not in writer_source
    assert not (PACKAGE_DIR / "sqlite_transition_fixtures.py").exists()


def test_migration_0001_is_unchanged_and_no_0002_exists() -> None:
    migrations = sorted(path.name for path in (PACKAGE_DIR / "sqlite_migrations").glob("*.sql"))
    assert migrations == ["0001_initial.sql"]
    migration_bytes = (PACKAGE_DIR / "sqlite_migrations/0001_initial.sql").read_bytes()
    assert hashlib.sha256(migration_bytes).hexdigest() == EXPECTED_MIGRATION_0001_CHECKSUM
