import ast
import builtins
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys
import tomllib

import pytest


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = ROOT / ".docs" / "c2b-durable-development-state.md"
C2B3A_PLANNING_PATH = ROOT / ".docs" / "c2b3-program-initialization.md"
C2B3A_ORACLE_PATH = ROOT / "tests" / "test_c2b3_program_initialization_contract.py"
SQLITE_MIGRATION_PATH = ROOT / "src/ge_nwp_coordinator/sqlite_migration.py"

C2B3A_PLANNING_PROJECTION_APPROVED_TEXT = (
    "# C2B3 Program Initialization\n"
    "\n"
    "<!-- C2B3A_PLANNING_PROJECTION_BEGIN -->\n"
    "\n"
    "<!-- C2B3A_PLANNING_NON_AUTHORITY_BEGIN -->\n"
    "## Non-authority declaration\n"
    "\n"
    "This file is a planning and implementation-status projection only. It is not\n"
    "semantic authority. Section 35 of `.docs/c2b-durable-development-state.md` is\n"
    "the sole C2B3A semantic owner. Planning cannot create, override, widen, narrow,\n"
    "resolve, or change a structured owner value, and wording here cannot supply\n"
    "operative semantics when a structured owner value exists.\n"
    "<!-- C2B3A_PLANNING_NON_AUTHORITY_END -->\n"
    "\n"
    "<!-- C2B3A_PLANNING_CURRENT_STATUS_BEGIN -->\n"
    "## Current status\n"
    "\n"
    "C2B3A remains a target-contract freeze. The unstaged C2B Pre-I/O VS1A\n"
    "candidate selects controller-exclusive connection custody and an exact scope-\n"
    "token activation acknowledgment before COMMIT. After close, the controller\n"
    "supplies immutable facts only; under the writer-resource lock, the resource\n"
    "observes current disposal posture, selects the actual successor, and publishes\n"
    "it through one lifecycle assignment. Exact publication acknowledgment precedes\n"
    "scope-alias clearing, and scope use is already invalid after assignment. Normal\n"
    "return from the retained-custody owner's direct exact-object `close()` is the\n"
    "sole closure proof; a repeated close is permitted only while proof is absent.\n"
    "Pre-close resumption policy is distinct from field-free post-proof\n"
    "`ResumeActive`. Disposal and governing process control strengthen or convert\n"
    "resumption to cleanup, so later completion cannot restore Active. Operation\n"
    "admission publishes an immutable resource-owned record containing copied\n"
    "resource/operation/PID/thread/epoch facts and the exact admitted lease weak\n"
    "reference and finalizer identity. Handle-side binding fields are compatibility\n"
    "observations only and cannot replace that authority. Retirement first records\n"
    "an exact condition-owned non-admitting preparation. Normal retirement is then\n"
    "owned only by the still-live admitted lease: under that same condition, the\n"
    "resource records local terminality, calls `detach()` on the exact bound\n"
    "finalizer, and records `EXPLICIT_RETIRED` only from that call's exact successful\n"
    "return. A dead finalizer, `alive == False`, weak-reference clearing, GC, object\n"
    "loss, or a caller-built acknowledgment is never retirement proof.\n"
    "Plain mutation-active/closing retirement defensively records exact slot release;\n"
    "controller close-proved release ownership is unchanged. If the operation is the\n"
    "sole cleanup blocker, Phase 1 uses the existing cleanup claim and retains the\n"
    "record while credential/lock cleanup runs before publication. Finalizer\n"
    "execution, direct invocation, GC, and lease or wrapper loss before\n"
    "`EXPLICIT_RETIRED` classify only orphan cleanup, keep admission frozen, and can\n"
    "reach X without restoring Active. Lease loss after `EXPLICIT_RETIRED` adds no\n"
    "authority; it can only finish publication already authorized by the stored\n"
    "resource phase or follow current cleanup posture.\n"
    "One final resource lifecycle assignment under that same condition removes the\n"
    "exact record and is the operation-completion linearization point. Python method\n"
    "return is caller observation only. The two vulnerable retained-lease public\n"
    "callers, transition apply and global-stop apply, now place one caller-side\n"
    "process-control envelope around pre-admission correlation creation and the\n"
    "nested operation-guard helper. One private immutable exact-object token exists\n"
    "before that helper can admit. Admission validates the token's exact resource,\n"
    "PID, and epoch and binds it through the exact handle retained by the immutable\n"
    "resource record in the same condition-protected lifecycle assignment. The\n"
    "envelope never derives correlation from a returned lease or post-return handle.\n"
    "It receives compiler-cleanup, `__exit__`, and `_close()` escapes, including\n"
    "their first traceable opcodes; neither internal method claims to protect its own\n"
    "first opcode. Before poison, the stabilizer checks only the token's exact type,\n"
    "directly stored resource identity, and the resource's direct fork-invalid\n"
    "owner-PID sentinel, acquires the condition, directly inspects the current exact\n"
    "lifecycle-state type and exact immutable record\n"
    "tuple, and recognizes the current record through direct frozen/slotted fields\n"
    "and token-object identity. It reads no lifecycle property and calls no project\n"
    "or policy helper. One exact match is followed immediately by direct poison\n"
    "assignment under the condition. Only afterward may `_state_authority` derive\n"
    "authority and validate PID, epoch, resource, correlation, record, and handle\n"
    "consistency; failure leaves poison set. Absence proves neither no admission nor\n"
    "prior final assignment and does not poison. Post-poison classification\n"
    "distinguishes represented incomplete from represented cleanup-owned. Detailed\n"
    "record replacement, successor construction, and notification follow poison and\n"
    "cannot reset it; controller resolution with\n"
    "`_CleanupRequiredAfterResolution` is represented cleanup-owned. The one-way\n"
    "poison blocks operation and mutation admission and every admitting successor\n"
    "while bounded cleanup continues toward X.\n"
    "\n"
    "After stabilization, a bounded cycle-aware sanitizer clears traceback fields\n"
    "in the supported graph: `BaseException` base traceback, cause, context, args,\n"
    "and base instance dictionary; `BaseExceptionGroup` base children; and\n"
    "`BaseException` values recursively reached through exact built-in `tuple`,\n"
    "`list`, `dict`, `set`, and `frozenset` containers. Bound base-class descriptors\n"
    "and exact built-in operations prevent exception-field dispatch. Subclass\n"
    "dynamic descriptors, arbitrary subclass slots, arbitrary user-object\n"
    "attributes, and custom container iteration are excluded. Each base traceback\n"
    "is cleared before the exception's other base fields are read. Exact identity,\n"
    "type, args, `SystemExit.code`, suppression, notes, instance-dictionary content,\n"
    "group-child identity, and cause/context links remain unchanged before bare\n"
    "reraise. One ordinary primary-traversal or call-boundary failure is contained\n"
    "and followed by one independently bound non-dispatching fallback, so it cannot\n"
    "replace the outward exception. Repeated asynchronous interruption,\n"
    "catastrophic allocation failure, and unsupported private mutation of bound\n"
    "defaults or C-level descriptors are outside the guarantee. The same outer\n"
    "privacy boundary handles an exact content-free safe store error through each\n"
    "genuine bound public operation guard, without process-control poisoning or\n"
    "reconstruction.\n"
    "The separate `require_usable_for_mutation` use remains an already fail-closed\n"
    "ephemeral/unbound-lease path: its reproduced compiler boundary loses the last\n"
    "lease reference and reaches X through existing finalizer cleanup without the\n"
    "caller envelope or poison, while reachable exit boundaries are prepared as\n"
    "non-admitting. Wrong-PID and fork-child non-authority remain unchanged. Later\n"
    "pre-assignment process control retains the record and strengthens cleanup;\n"
    "post-assignment process control preserves the assigned state and uses existing\n"
    "explicit fresh/replay/conflict semantics. An absent or never-published handle\n"
    "cannot prove prior completion; internal retirement retry stops at exact handle\n"
    "absence, with no completion receipt or registry. Each writer resource also allocates one opaque\n"
    "identity shared by its authority, operations, slot/frame, controller token,\n"
    "connection custody/proof, cleanup cursors, and claim, with authority comparisons\n"
    "only by `is`. Exact closed variants and single-owned structural cursors replace\n"
    "the rejected broad snapshot and completed-step model. Cleanup claims bind the\n"
    "exact `threading.Thread` object with explicit dead-owner takeover. Sensitive\n"
    "mutation frames return one private safe\n"
    "disposition; after their bindings clear, the outer public boundary catches,\n"
    "sanitizes, and bare-reraises the same exact content-free store-error object by\n"
    "identity. A normal transaction-\n"
    "connection close with no pending disposal restores the same transition/global-\n"
    "stop wrapper for a later explicit fresh apply or exact replay; QU/QK and\n"
    "disposal-pending postures remain non-reusable. The B3c1a contract-projection\n"
    "test keeps its existing node ID and replaces only its obsolete post-GC Active\n"
    "expectation: loss before `EXPLICIT_RETIRED` is `ORPHANED`, non-admitting,\n"
    "cleanup-owned, and eventually X. The B3c1b change is connection-\n"
    "lifetime hygiene only. The B3c3 change is a private rollback-only regression\n"
    "adaptation to the selected close-proof owner with no result, durability, public,\n"
    "or authority widening. The unchanged B2b issue is pre-existing HEAD-exact test-\n"
    "resource hygiene, strict warning-promotion debt, not repaired by VS1A, and not\n"
    "VS1A authority or semantic behavior. The candidate has exactly twenty-two dirty\n"
    "paths: twenty-one tracked modifications, the sole untracked shared-foundation\n"
    "test, and zero staged paths, including the intentional B3c1a contract\n"
    "replacement in `tests/test_b3c1a_writer_session_authority.py`. A fresh\n"
    "independent audit remains pending. The accepted B4b one-byte zero-Coordinator-\n"
    "frame privacy contract replacement in\n"
    "`tests/test_b4b_private_atomic_global_stop_persistence.py` remains unchanged.\n"
    "These bytes have not been staged, committed, pushed, or published. These scope\n"
    "counts are report-only observations bound to the exact candidate provenance,\n"
    "not architectural invariants.\n"
    "\n"
    "The repaired candidate keeps runtime causal cases, compiled complete-module\n"
    "source mutants, and secondary AST/source guards as distinct evidence classes.\n"
    "The shared-foundation test is the owning surface, and its focused inventory is\n"
    "one literal tuple of selected node IDs. Exact commands, changing node totals,\n"
    "warning totals, overlaps, and validation-group file inventories are report\n"
    "evidence rather than governing architecture. Source mutants use external\n"
    "copies and leave the live repository unchanged. Direct-finalizer\n"
    "counterfactuals still assert reachability at their actual orphan-mark or\n"
    "cleanup-successor seam. This is candidate validation evidence only; it is not\n"
    "an independent-audit acceptance claim.\n"
    "\n"
    "The implemented database remains application generation 2 at terminal\n"
    "migration `0002_development_program_and_effect_state`. VS1A adds no program-\n"
    "initialization command, durable development row, reader, replay, recovery, or\n"
    "author-effect source; it performs no worker, model, Git, Execution Substrate,\n"
    "Bridge, network, or other external effect; and it changes no schema or\n"
    "migration. Section-35 C2B3 initialization recovery/replay remains target-only\n"
    "and affected-resource X-gated. Existing transition and global-stop idempotency/\n"
    "replay remain same-wrapper capable after proved normal close and are not subject\n"
    "to that future initialization gate. C2B3B/VS1B remains absent and unauthorized.\n"
    "\n"
    "The structured owner value\n"
    "`commit_close_outcome_addendum.normative_surface_and_precedence` makes\n"
    "`commit_close_outcome_addendum` the sole operative authority for COMMIT/close\n"
    "outcomes, process-control relationships, cleanup states and order, finalizer\n"
    "and liveness rules, recovery and replay gates, and future C2B3B path scope.\n"
    "The bounded prose in Section 35 and this projection have no independent\n"
    "semantic authority.\n"
    "<!-- C2B3A_PLANNING_CURRENT_STATUS_END -->\n"
    "\n"
    "<!-- C2B3A_PLANNING_LEGACY_LEDGER_BEGIN -->\n"
    "## Legacy-ledger projection\n"
    "\n"
    "Section 35 classifies\n"
    "`commit_uncertainty_cleanup_gate.close_not_proved.process_control_exception_graph_ledger`\n"
    "as `historical_runtime_observation`, with `normative=false`,\n"
    "`operative_for_c2b3b=false`, `portable_contract=false`, and\n"
    "`preserved_for_original_c2b3a_evidence=true`. Its target semantics are\n"
    "superseded by `process_control_relational_policy`. No implementation, test\n"
    "oracle, planning projection, or future prompt may use its observed graph or\n"
    "traceback values as target requirements.\n"
    "\n"
    "The operative process-control rule is deliberate-action-only. C2B3 does not\n"
    "deliberately assign, clear, restore, scrub, sanitize, or manufacture graph or\n"
    "traceback state; it deliberately creates no primary-to-secondary relation and\n"
    "does not serialize, persist, log, render, report, or copy raw process control.\n"
    "Interpreter-managed graph and traceback effects remain permitted, and no exact\n"
    "resulting graph or traceback shape is promised.\n"
    "<!-- C2B3A_PLANNING_LEGACY_LEDGER_END -->\n"
    "\n"
    "<!-- C2B3A_PLANNING_ACTIVE_SCOPE_BEGIN -->\n"
    "## Active future-scope projection\n"
    "\n"
    "The preserved 23-expected, 24-maximum, and twenty-fifth-path-stop material is\n"
    "historical and non-operative. `consumers_may_use` remains false. The only\n"
    "operative future scope is the structured owner value\n"
    "`commit_close_outcome_addendum.future_c2b3b_path_scope_status` for\n"
    "`C2B3B_PRIVATE_ATOMIC_INITIALIZATION`.\n"
    "\n"
    "Production is exactly six paths:\n"
    "\n"
    "- `src/ge_nwp_coordinator/_development_program_initialization_contracts.py`\n"
    "- `src/ge_nwp_coordinator/_sqlite_development_program_initialization.py`\n"
    "- `src/ge_nwp_coordinator/sqlite_transition_transaction.py`\n"
    "- `src/ge_nwp_coordinator/sqlite_writer_session.py`\n"
    "- `src/ge_nwp_coordinator/sqlite_connection.py`\n"
    "- `src/ge_nwp_coordinator/state_authority_lock.py`\n"
    "\n"
    "Documentation/status is exactly ten paths:\n"
    "\n"
    "- `.docs/c2b-durable-development-state.md`\n"
    "- `.docs/c2b3-program-initialization.md`\n"
    "- `.docs/c2b2-private-readers.md`\n"
    "- `.docs/architecture.md`\n"
    "- `.docs/durable-state-model.md`\n"
    "- `.docs/sqlite-operations-and-recovery.md`\n"
    "- `.docs/sqlite-threat-model.md`\n"
    "- `.docs/writer-session-authority.md`\n"
    "- `README.md`\n"
    "- `AGENTS.md`\n"
    "\n"
    "Required changed tests are exactly eleven paths:\n"
    "\n"
    "- `tests/test_c2b3_program_initialization_contract.py`\n"
    "- `tests/test_c2b3_private_atomic_program_initialization.py`\n"
    "- `tests/test_c2b3_program_initialization_recovery.py`\n"
    "- `tests/test_c2b3_private_program_initialization_delegation.py`\n"
    "- `tests/test_c2b2_field_level_contract.py`\n"
    "- `tests/test_c2b2_development_reader_contracts.py`\n"
    "- `tests/test_sqlite_b2c_writer_session.py`\n"
    "- `tests/test_state_authority_lock.py`\n"
    "- `tests/test_runtime_non_authority.py`\n"
    "- `tests/test_architecture_contracts.py`\n"
    "- `tests/test_c2b0_durable_state_contract.py`\n"
    "\n"
    "The one contingency path is\n"
    "`tests/test_c2b2_private_development_readers.py`. The exact expected count is\n"
    "`6 + 10 + 11 = 27`; the exact maximum is 28; a twenty-ninth path is a hard\n"
    "stop and scope-reassessment condition.\n"
    "\n"
    "The four newly required paths relative to the historical manifest are\n"
    "`src/ge_nwp_coordinator/state_authority_lock.py`,\n"
    "`.docs/writer-session-authority.md`,\n"
    "`tests/test_state_authority_lock.py`, and\n"
    "`tests/test_sqlite_b2c_writer_session.py`. This projection authorizes no C2B3B\n"
    "source or implementation.\n"
    "<!-- C2B3A_PLANNING_ACTIVE_SCOPE_END -->\n"
    "\n"
    "<!-- C2B3A_PLANNING_VALIDATION_ACCEPTANCE_BEGIN -->\n"
    "## Validation, source acceptance, and sequencing\n"
    "\n"
    "These are process and acceptance gates projected from the project lifecycle;\n"
    "they do not make this planning file semantic authority.\n"
    "\n"
    "Future C2B3B tests use private temporary databases only. They never open\n"
    "operator state, migrate operator state, or inspect operator-state contents.\n"
    "Project-protocol existence or absence checks remain allowed, but no operator\n"
    "database open or migration is permitted.\n"
    "\n"
    "Before C2B3B source is accepted, all of the following separate evidence is\n"
    "required:\n"
    "\n"
    "- an accepted fresh independent read-only source-acceptance audit;\n"
    "- the exact committed C2B3A contract baseline;\n"
    "- a distinct committed Coordinator repository baseline;\n"
    "- a refreshed exact Coordinator snapshot, or an explicitly equivalent exact\n"
    "  strategic baseline, produced after and bound to that committed baseline;\n"
    "- the committed direct independent oracle;\n"
    "- the then-current generation-2 schema and accepted C2B2 row and reader\n"
    "  identities;\n"
    "- the exact finite 27-expected / 28-maximum / path-29-stop source proposal and\n"
    "  protected complement;\n"
    "- no WorkSpec custody, lookup, retrieval, leakage, logging, report transport,\n"
    "  or traceback retention;\n"
    "- one-database, one-writer, one-mutation-slot, and one-controller reuse;\n"
    "- exact replay and recovery proof requirements; and\n"
    "- zero public, schema, migration, package, authority, route, external-I/O, or\n"
    "  cross-repository widening.\n"
    "\n"
    "The committed Coordinator repository baseline and the refreshed exact\n"
    "Coordinator snapshot or explicitly equivalent exact strategic baseline are\n"
    "separate evidence items. Neither substitutes for the other, and the fresh\n"
    "source-acceptance audit does not itself establish that the snapshot was\n"
    "refreshed.\n"
    "\n"
    "Acceptance of this planning projection is not acceptance of future source.\n"
    "\n"
    "Before source mutation begins, C2B3B source implementation requires all of the\n"
    "following separate evidence:\n"
    "\n"
    "- an accepted independent audit of the committed C2B3A contract baseline;\n"
    "- a committed clean Coordinator baseline;\n"
    "- a refreshed exact Coordinator snapshot or explicitly equivalent exact\n"
    "  strategic baseline bound to that clean committed baseline;\n"
    "- an exact C2B3B source implementation prompt;\n"
    "- fresh opening repository and patch provenance;\n"
    "- the accepted 27-expected / 28-maximum future path scope and a hard stop if a\n"
    "  twenty-ninth path is required; and\n"
    "- the private-test database and operator-state non-access boundaries above.\n"
    "\n"
    "A dirty four-file working tree is not a source baseline.\n"
    "\n"
    "C2B3C is the author-effect contract freeze. C2B3D cannot begin before the\n"
    "C2B3C owner questions are closed. Pending authority evidence remains inert and\n"
    "is not verification, permission, route eligibility, ES admission, or worker\n"
    "authorization. C2B4, C2B5, and C2B6 remain separate later tranches. Migration\n"
    "0003 remains reserved and unimplemented.\n"
    "<!-- C2B3A_PLANNING_VALIDATION_ACCEPTANCE_END -->\n"
    "\n"
    "<!-- C2B3A_PLANNING_PRODUCTION_NONIMPLEMENTATION_BEGIN -->\n"
    "## Production nonimplementation\n"
    "\n"
    "C2B3A implements or authorizes no production mutation, receipt, private\n"
    "delegation, recovery resolver, author effect, worker, scheduler, queue,\n"
    "service, model client, direct-local execution, Execution Substrate invocation,\n"
    "Bridge integration, schema, migration, package export, public model,\n"
    "`StateStore` method, or `WriterSession` public-protocol change. C2B3B remains\n"
    "absent and requires a separately authorized implementation tranche and a fresh\n"
    "independent read-only audit.\n"
    "<!-- C2B3A_PLANNING_PRODUCTION_NONIMPLEMENTATION_END -->\n"
    "\n"
    "<!-- C2B3_NARROWED_PLANNING_BEGIN -->\n"
    "## Governing vertical-slice narrowing projection\n"
    "\n"
    "Section 36 of `.docs/c2b-durable-development-state.md` is the sole semantic\n"
    "owner for this narrowing. This planning projection selects no new value,\n"
    "digest, relation, migration inventory, or physical schema.\n"
    "\n"
    "The preserved initialization and later author-effect adapter selections are\n"
    "non-operative for the first vertical slice. Initialization has no adapter,\n"
    "host, transport, endpoint, delivery, or external request. The first route is\n"
    "selected at author-effect delivery and uses `direct_local_bootstrap`, meaning a\n"
    "bounded direct/non-ES path to one qualified remote Linux host—not the user's\n"
    "Mac, the Coordinator host, or physical colocation. No third adapter exists.\n"
    "\n"
    "The old horizontal sequence, route-specific latch shape, path-count manifests,\n"
    "and migration/initialization target shapes are reopened rather than replaced.\n"
    "The policy still permits at most one productive bootstrap acceptance and,\n"
    "after semantic acceptance, one separate isolated local feature-branch commit.\n"
    "Push, remote-ref mutation, PR, merge, deployment, and publication remain zero;\n"
    "an ambiguous Git outcome never permits a blind second commit.\n"
    "\n"
    "Required dependency order is pre-I/O progression, remote contact through\n"
    "semantic decision, separate local Git and stop, then ES migration before\n"
    "another productive bootstrap slice. The exact initialization graph, custody,\n"
    "verification, invocation, capsule, evidence, Git protocol, reconciliation,\n"
    "replay/recovery, latch representation, migration relations, reliable submit,\n"
    "and conformance details remain just-in-time design questions.\n"
    "\n"
    "All non-superseded committed C2B3A one-writer, transaction, COMMIT/close,\n"
    "cleanup, replay, recovery, privacy, process-control, and no-external-I/O\n"
    "semantics remain operative. C2B3 source remains unauthorized.\n"
    "<!-- C2B3_NARROWED_PLANNING_END -->\n"
    "\n"
    "<!-- C2B3A_PLANNING_PROJECTION_END -->\n"
)
C2B3A_SOURCE_ACCEPTANCE_EVIDENCE_LEDGER = (
    "an accepted fresh independent read-only source-acceptance audit;",
    "the exact committed C2B3A contract baseline;",
    "a distinct committed Coordinator repository baseline;",
    "a refreshed exact Coordinator snapshot, or an explicitly equivalent exact "
    "strategic baseline, produced after and bound to that committed baseline;",
    "the committed direct independent oracle;",
    "the then-current generation-2 schema and accepted C2B2 row and reader "
    "identities;",
    "the exact finite 27-expected / 28-maximum / path-29-stop source proposal and "
    "protected complement;",
    "no WorkSpec custody, lookup, retrieval, leakage, logging, report transport, "
    "or traceback retention;",
    "one-database, one-writer, one-mutation-slot, and one-controller reuse;",
    "exact replay and recovery proof requirements; and",
    "zero public, schema, migration, package, authority, route, external-I/O, or "
    "cross-repository widening.",
)
C2B3A_SOURCE_START_EVIDENCE_LEDGER = (
    "an accepted independent audit of the committed C2B3A contract baseline;",
    "a committed clean Coordinator baseline;",
    "a refreshed exact Coordinator snapshot or explicitly equivalent exact "
    "strategic baseline bound to that clean committed baseline;",
    "an exact C2B3B source implementation prompt;",
    "fresh opening repository and patch provenance;",
    "the accepted 27-expected / 28-maximum future path scope and a hard stop if a "
    "twenty-ninth path is required; and",
    "the private-test database and operator-state non-access boundaries above.",
)

C2B3A_OWNER_PRE_ADDENDUM_SECTION_35_PREFIX = (
    "## 35. C2B3A Program-Initialization Contract Freeze\n"
    "\n"
    "Classification: `ACCEPTED TARGET CONTRACT` for the program-initialization\n"
    "family only. The single-work-item genesis shape is a bounded first vertical\n"
    "slice, not a permanent program-cardinality architecture. `CURRENT\n"
    "IMPLEMENTED CONTRACT` remains generation 2 at terminal migration\n"
    "`0002_development_program_and_effect_state`, with the existing C2B2 pure\n"
    "values and production-unintegrated readers. Program-initialization source,\n"
    "private delegation, product mutation, receipt persistence, replay/recovery\n"
    "runtime, public API, author-effect source, and migration 0003 are absent.\n"
    "\n"
    "This section is the sole semantic owner for C2B3A. The planning record\n"
    "`.docs/c2b3-program-initialization.md` references this section and does not\n"
    "restate or redefine its ledgers. The direct test oracle independently owns its\n"
    "expected literal and treats the following owner literal as candidate input.\n"
    "\n"
    "<!-- C2B3_PROGRAM_INITIALIZATION_CONTRACT_PYTHON_BEGIN -->\n"
    "\n"
    "```python\n"
    "{\n"
    "    \"contract_identity\": {\n"
    "        \"workstream\": \"COORDINATOR_C2B3A_PROGRAM_INITIALIZATION_CONTRACT_FREEZE\",\n"
    "        \"repository_tranche\": \"C2B3 — Program Initialization And Author-Effect Establishment\",\n"
    "        \"this_freeze\": \"C2B3A program-initialization contract only\",\n"
    "        \"semantic_owner\": \".docs/c2b-durable-development-state.md#35-c2b3a-program-initialization-contract-freeze\",\n"
    "        \"status_record\": \".docs/c2b3-program-initialization.md\",\n"
    "        \"status_record_authority\": \"planning only; not semantic authority\",\n"
    "        \"implementation_status\": \"contract frozen; production source absent\",\n"
    "    },\n"
    "    \"tranche_boundary\": {\n"
    "        \"C2B3A\": \"program-initialization contract only\",\n"
    "        \"C2B3B\": \"later private atomic initialization implementation\",\n"
    "        \"C2B3C\": \"later author-effect contract freeze\",\n"
    "        \"C2B3D\": \"later private atomic author-effect implementation\",\n"
    "        \"combined_family_implementation\": False,\n"
    "    },\n"
    "    \"five_path_scope\": {\n"
    "        \"tracked_modifications\": (\n"
    "            \".docs/c2b-durable-development-state.md\",\n"
    "            \"tests/test_c2b0_durable_state_contract.py\",\n"
    "            \"AGENTS.md\",\n"
    "        ),\n"
    "        \"untracked_additions\": (\n"
    "            \".docs/c2b3-program-initialization.md\",\n"
    "            \"tests/test_c2b3_program_initialization_contract.py\",\n"
    "        ),\n"
    "        \"total_paths\": 5,\n"
    "        \"production_source_paths\": (),\n"
    "        \"migration_paths\": (),\n"
    "        \"schema_paths\": (),\n"
    "        \"public_api_paths\": (),\n"
    "    },\n"
    "    \"owner_decisions\": {\n"
    "        \"initial_work_item_count\": 1,\n"
    "        \"initial_work_spec_count\": 1,\n"
    "        \"membership_ordinal\": 0,\n"
    "        \"first_author_attempt_number\": 1,\n"
    "        \"initial_author_basis\": (\"initialize\", \"program_genesis\"),\n"
    "        \"planned_adapter_kind\": \"execution_substrate\",\n"
    "        \"route_effect\": \"absent\",\n"
    "        \"work_spec_ingress\": \"same-call transient only\",\n"
    "        \"work_spec_custody\": \"absent\",\n"
    "        \"recovery_lifecycle\": \"close-complete-gated later call under a newly acquired concrete session and fresh operation lease\",\n"
    "        \"automatic_semantic_retry\": False,\n"
    "        \"family_graph_membership\": \"family-created rows only\",\n"
    "        \"duplicate_program_classification\": \"semantic_identity_conflict\",\n"
    "    },\n"
    "    \"initialization_golden_vector\": {\n"
    "        \"owner_literal_marker\": \"C2B3_PROGRAM_INITIALIZATION_GOLDEN_VECTOR_PYTHON\",\n"
    "        \"oracle_literal_name\": \"EXPECTED_INITIALIZATION_GOLDEN_VECTOR\",\n"
    "        \"vector_id\": \"c2b3a-initialization-single-work-v1\",\n"
    "        \"vector_version\": 1,\n"
    "        \"family\": \"initialize_development_program\",\n"
    "        \"single_work\": True,\n"
    "        \"direct_owner_literal\": True,\n"
    "        \"direct_independent_oracle_literal\": True,\n"
    "        \"oracle_runtime_derivation\": False,\n"
    "        \"proves_implementation\": False,\n"
    "        \"required_components\": (\n"
    "            \"all safe command input values\",\n"
    "            \"exact WorkSpec safe-projection mapping\",\n"
    "            \"exact accepted-intent canonical mapping and UTF-8 byte-hex\",\n"
    "            \"accepted-intent safe-projection digest\",\n"
    "            \"exact safe-command canonical mapping and UTF-8 byte-hex\",\n"
    "            \"command digest\",\n"
    "            \"one transaction timestamp\",\n"
    "            \"all nine complete persisted row mappings and applicable self-digests\",\n"
    "            \"program-head and work-item-head historical postimages\",\n"
    "            \"all eight ordered graph entries with rank, role, ordinal, ref, and digest\",\n"
    "            \"exact result projection and digest\",\n"
    "            \"mutation-graph digest\",\n"
    "            \"complete mutation-receipt scalar envelope\",\n"
    "            \"private committed result\",\n"
    "            \"private exact-replay result\",\n"
    "        ),\n"
    "    },\n"
    "    \"semantic_ref_ownership\": {\n"
    "        \"owner\": \"semantic caller\",\n"
    "        \"preassigned_refs\": (\n"
    "            \"mutation_ref\",\n"
    "            \"program_ref\",\n"
    "            \"program_version_ref\",\n"
    "            \"accepted_intent_revision_ref\",\n"
    "            \"decision_ref\",\n"
    "            \"work_item_ref\",\n"
    "            \"work_item_revision_ref\",\n"
    "            \"work_spec_ref\",\n"
    "            \"preassigned_semantic_attempt_ref\",\n"
    "            \"preassigned_candidate_ref\",\n"
    "        ),\n"
    "        \"initializer_generated_semantic_refs\": (),\n"
    "        \"forbidden_ref_derivations\": (\n"
    "            \"random\",\n"
    "            \"UUID\",\n"
    "            \"clock-derived\",\n"
    "            \"rowid-derived\",\n"
    "            \"implicit\",\n"
    "        ),\n"
    "        \"coordinator_derived_values\": (\n"
    "            \"fixed genesis numbers and states\",\n"
    "            \"dense ordinal 0\",\n"
    "            \"one transaction timestamp\",\n"
    "            \"safe projections\",\n"
    "            \"canonical identities\",\n"
    "            \"row digests\",\n"
    "            \"result projection digest\",\n"
    "            \"mutation graph digest\",\n"
    "            \"complete locator material\",\n"
    "        ),\n"
    "    },\n"
    "    \"existing_work_spec_safe_projection\": {\n"
    "        \"semantic_name\": \"DevelopmentWorkSpecSafeProjection\",\n"
    "        \"schema_id\": \"governed-execution.nwp-development-work-spec-safe-projection.v1\",\n"
    "        \"digest_domain\": \"governed-execution.nwp-development-work-spec-safe-projection.v1.identity\",\n"
    "        \"ordered_fields\": (\n"
    "            \"schema_id\",\n"
    "            \"work_spec_ref\",\n"
    "            \"program_ref\",\n"
    "            \"program_version_ref\",\n"
    "            \"accepted_intent_revision_ref\",\n"
    "            \"work_item_ref\",\n"
    "            \"work_item_revision_ref\",\n"
    "            \"repository_ref\",\n"
    "            \"base_git_object_format\",\n"
    "            \"base_git_oid\",\n"
    "            \"authorized_paths\",\n"
    "            \"validation_requirement_ref\",\n"
    "            \"review_requirement_ref\",\n"
    "            \"privacy_classification\",\n"
    "            \"work_spec_digest\",\n"
    "            \"safe_projection_digest\",\n"
    "        ),\n"
    "        \"replacement_invented\": False,\n"
    "        \"source_or_identity_modified\": False,\n"
    "    },\n"
    "    \"accepted_intent_safe_projection\": {\n"
    "        \"semantic_name\": \"DevelopmentAcceptedIntentSafeProjectionV1\",\n"
    "        \"schema_id\": \"governed-execution.nwp-development-accepted-intent-safe-projection.v1\",\n"
    "        \"digest_domain\": \"governed-execution.nwp-development-accepted-intent-safe-projection.v1.identity\",\n"
    "        \"ordered_fields\": (\n"
    "            \"schema_id\",\n"
    "            \"source_intent_ref\",\n"
    "            \"source_intent_digest\",\n"
    "            \"initial_work_spec_safe_projection\",\n"
    "            \"safe_projection_digest\",\n"
    "        ),\n"
    "        \"identity_excludes\": (\"safe_projection_digest\",),\n"
    "        \"nested_projection_exact_type\": \"DevelopmentWorkSpecSafeProjection\",\n"
    "        \"derived_from\": (\n"
    "            \"caller-supplied source_intent_ref\",\n"
    "            \"caller-supplied source_intent_digest\",\n"
    "            \"exact transient WorkSpecV1\",\n"
    "            \"existing WorkSpec safe-projection builder\",\n"
    "        ),\n"
    "        \"caller_forbidden\": (\n"
    "            \"completed accepted-intent projection\",\n"
    "            \"safe_projection_digest\",\n"
    "            \"generic mapping\",\n"
    "            \"substitute WorkSpec safe projection\",\n"
    "            \"subclass or structural stand-in\",\n"
    "        ),\n"
    "        \"private_fields_absent\": (\n"
    "            \"objective\",\n"
    "            \"requirements text\",\n"
    "            \"exclusions text\",\n"
    "            \"prompt\",\n"
    "            \"response\",\n"
    "            \"transcript\",\n"
    "            \"credential\",\n"
    "            \"endpoint\",\n"
    "            \"retrieval material\",\n"
    "            \"capsule content\",\n"
    "            \"workspace path\",\n"
    "        ),\n"
    "        \"persisted_row_fields\": (\n"
    "            \"source_intent_ref\",\n"
    "            \"source_intent_digest\",\n"
    "            \"safe_projection_digest\",\n"
    "        ),\n"
    "    },\n"
    "    \"sensitive_ingress\": {\n"
    "        \"work_spec_type\": \"exact built-in WorkSpecV1\",\n"
    "        \"work_spec_count\": 1,\n"
    "        \"container_ingress\": False,\n"
    "        \"additional_inputs\": (\n"
    "            \"all preassigned safe semantic refs\",\n"
    "            \"caller-supplied source_intent_ref\",\n"
    "            \"caller-supplied source_intent_digest\",\n"
    "            \"expected coding_global_stop_ref\",\n"
    "            \"expected coding_global_stop_version\",\n"
    "        ),\n"
    "        \"caller\": \"future Coordinator-internal semantic/progression caller already holding the exact value\",\n"
    "        \"possession_meaning\": \"input provenance only; not executable authority\",\n"
    "        \"closed_outcomes\": (\n"
    "            \"one complete safe initialization command\",\n"
    "            \"one closed privacy-safe failure discriminant\",\n"
    "        ),\n"
    "        \"retrieval_by_ref\": False,\n"
    "        \"restart_safe_retrieval\": False,\n"
    "        \"private_custody_store\": False,\n"
    "    },\n"
    "    \"safe_command\": {\n"
    "        \"semantic_name\": \"DevelopmentProgramInitializationCommandV1\",\n"
    "        \"schema_id\": \"governed-execution.nwp-initialize-development-program-command.v1\",\n"
    "        \"digest_domain\": \"governed-execution.nwp-initialize-development-program-command.v1.identity\",\n"
    "        \"ordered_fields\": (\n"
    "            \"schema_id\",\n"
    "            \"mutation_ref\",\n"
    "            \"program_ref\",\n"
    "            \"program_version_ref\",\n"
    "            \"accepted_intent_revision_ref\",\n"
    "            \"decision_ref\",\n"
    "            \"preassigned_semantic_attempt_ref\",\n"
    "            \"preassigned_candidate_ref\",\n"
    "            \"coding_global_stop_ref\",\n"
    "            \"coding_global_stop_version\",\n"
    "            \"reason_code\",\n"
    "            \"work_spec_safe_projection\",\n"
    "            \"accepted_intent_safe_projection\",\n"
    "            \"command_digest\",\n"
    "        ),\n"
    "        \"exact_field_types\": (\n"
    "            (\"schema_id\", \"str\"),\n"
    "            (\"mutation_ref\", \"str\"),\n"
    "            (\"program_ref\", \"str\"),\n"
    "            (\"program_version_ref\", \"str\"),\n"
    "            (\"accepted_intent_revision_ref\", \"str\"),\n"
    "            (\"decision_ref\", \"str\"),\n"
    "            (\"preassigned_semantic_attempt_ref\", \"str\"),\n"
    "            (\"preassigned_candidate_ref\", \"str\"),\n"
    "            (\"coding_global_stop_ref\", \"str\"),\n"
    "            (\"coding_global_stop_version\", \"int excluding bool\"),\n"
    "            (\"reason_code\", \"str\"),\n"
    "            (\"work_spec_safe_projection\", \"exact DevelopmentWorkSpecSafeProjection\"),\n"
    "            (\"accepted_intent_safe_projection\", \"exact DevelopmentAcceptedIntentSafeProjectionV1\"),\n"
    "            (\"command_digest\", \"str\"),\n"
    "        ),\n"
    "        \"reason_code\": \"program_genesis\",\n"
    "        \"identity_excludes\": (\"command_digest\",),\n"
    "        \"digest_owner\": \"Coordinator sensitive reducer\",\n"
    "        \"cross_relations\": (\n"
    "            \"work_spec_safe_projection.program_ref == command.program_ref\",\n"
    "            \"work_spec_safe_projection.program_version_ref == command.program_version_ref\",\n"
    "            \"work_spec_safe_projection.accepted_intent_revision_ref == command.accepted_intent_revision_ref\",\n"
    "            \"accepted_intent_safe_projection.initial_work_spec_safe_projection == command.work_spec_safe_projection\",\n"
    "            \"accepted_intent_safe_projection.source_intent_ref == persisted accepted-intent source_intent_ref\",\n"
    "            \"accepted_intent_safe_projection.source_intent_digest == persisted accepted-intent source_intent_digest\",\n"
    "            \"preassigned_attempt_candidate_binding.work_item_ref == safe command work_spec_safe_projection.work_item_ref == sole program-version membership work_item_ref == sole WorkSpec binding work_item_ref\",\n"
    "            \"preassigned_attempt_candidate_binding.work_item_revision_ref == safe command work_spec_safe_projection.work_item_revision_ref == sole program-version membership work_item_revision_ref == sole WorkSpec binding work_item_revision_ref\",\n"
    "            \"preassigned_attempt_candidate_binding.preassigned_semantic_attempt_ref == safe command preassigned_semantic_attempt_ref == initialize decision preassigned_semantic_attempt_ref\",\n"
    "            \"preassigned_attempt_candidate_binding.preassigned_candidate_ref == safe command preassigned_candidate_ref == initialize decision preassigned_candidate_ref\",\n"
    "        ),\n"
    "        \"rejects\": (\n"
    "            \"Boolean as integer\",\n"
    "            \"subclasses\",\n"
    "            \"coercion\",\n"
    "            \"generic mappings\",\n"
    "            \"extension fields\",\n"
    "            \"optional metadata\",\n"
    "            \"caller-supplied digests\",\n"
    "            \"implicit refs\",\n"
    "            \"zero WorkSpecs\",\n"
    "            \"multiple WorkSpecs\",\n"
    "            \"caller-supplied membership ordinal\",\n"
    "            \"implicit sorting\",\n"
    "        ),\n"
    "        \"contains_complete_work_spec\": False,\n"
    "    },\n"
    "    \"genesis_cardinality\": {\n"
    "        \"program_versions\": 1,\n"
    "        \"accepted_intent_revisions\": 1,\n"
    "        \"work_item_heads\": 1,\n"
    "        \"work_item_revisions\": 1,\n"
    "        \"program_version_memberships\": 1,\n"
    "        \"work_spec_safe_bindings\": 1,\n"
    "        \"preassigned_attempt_candidate_binding\": {\n"
    "            \"ordered_fields\": (\n"
    "                \"work_item_ref\",\n"
    "                \"work_item_revision_ref\",\n"
    "                \"preassigned_semantic_attempt_ref\",\n"
    "                \"preassigned_candidate_ref\",\n"
    "            ),\n"
    "            \"relations\": (\n"
    "                \"preassigned_attempt_candidate_binding.work_item_ref == safe command work_spec_safe_projection.work_item_ref == sole program-version membership work_item_ref == sole WorkSpec binding work_item_ref\",\n"
    "                \"preassigned_attempt_candidate_binding.work_item_revision_ref == safe command work_spec_safe_projection.work_item_revision_ref == sole program-version membership work_item_revision_ref == sole WorkSpec binding work_item_revision_ref\",\n"
    "                \"preassigned_attempt_candidate_binding.preassigned_semantic_attempt_ref == safe command preassigned_semantic_attempt_ref == initialize decision preassigned_semantic_attempt_ref\",\n"
    "                \"preassigned_attempt_candidate_binding.preassigned_candidate_ref == safe command preassigned_candidate_ref == initialize decision preassigned_candidate_ref\",\n"
    "            ),\n"
    "            \"future_lineage_only\": True,\n"
    "            \"creates_selects_authorizes_or_executes_attempt_or_candidate\": False,\n"
    "        },\n"
    "        \"hidden_selection_rule\": False,\n"
    "        \"permanent_one_work_item_architecture\": False,\n"
    "        \"later_additional_work_owner\": \"C2B6 replan mechanics\",\n"
    "    },\n"
    "    \"row_and_head_ledger\": {\n"
    "        \"inserted_row_count\": 9,\n"
    "        \"inserted_rows\": (\n"
    "            \"program_head\",\n"
    "            \"program_version\",\n"
    "            \"accepted_intent_revision\",\n"
    "            \"work_item_head\",\n"
    "            \"work_item_revision\",\n"
    "            \"program_version_work_item\",\n"
    "            \"work_spec_binding\",\n"
    "            \"initialize_decision\",\n"
    "            \"mutation_receipt\",\n"
    "        ),\n"
    "        \"postimages\": {\n"
    "            \"program_head\": (\n"
    "                (\"current_program_version_number\", 1),\n"
    "                (\"current_program_version_ref\", \"exact program_version_ref\"),\n"
    "                (\"head_revision\", 0),\n"
    "                (\"program_state\", \"active\"),\n"
    "            ),\n"
    "            \"program_version\": (\n"
    "                (\"program_version_number\", 1),\n"
    "                (\"program_version_kind\", \"initial\"),\n"
    "                (\"creating_decision_ref\", \"exact decision_ref\"),\n"
    "            ),\n"
    "            \"accepted_intent_revision\": (\n"
    "                (\"accepted_intent_revision_number\", 1),\n"
    "                (\"prior_accepted_intent_revision_ref\", None),\n"
    "                (\"safe_projection_digest\", \"derived accepted-intent safe_projection_digest\"),\n"
    "            ),\n"
    "            \"work_item_head\": (\n"
    "                (\"current_work_item_revision_number\", 1),\n"
    "                (\"current_work_item_revision_ref\", \"exact work_item_revision_ref\"),\n"
    "                (\"head_revision\", 0),\n"
    "                (\"work_state\", \"planned\"),\n"
    "            ),\n"
    "            \"work_item_revision\": (\n"
    "                (\"work_item_revision_number\", 1),\n"
    "                (\"work_item_revision_kind\", \"initial\"),\n"
    "                (\"prior_work_item_revision_ref\", None),\n"
    "            ),\n"
    "            \"program_version_work_item\": (\n"
    "                (\"membership_ordinal\", 0),\n"
    "                (\"work_item_ref\", \"exact work_item_ref\"),\n"
    "                (\"work_item_revision_ref\", \"exact work_item_revision_ref\"),\n"
    "            ),\n"
    "            \"work_spec_binding\": (\n"
    "                (\"safe_projection\", \"exact existing DevelopmentWorkSpecSafeProjection\"),\n"
    "                (\"recorded_at\", \"one transaction timestamp\"),\n"
    "            ),\n"
    "            \"initialize_decision\": (\n"
    "                (\"decision_kind\", \"initialize\"),\n"
    "                (\"decision_variant\", \"program_genesis\"),\n"
    "                (\"basis_decision_ref\", None),\n"
    "                (\"basis_program_version_ref\", None),\n"
    "                (\"basis_semantic_attempt_ref\", None),\n"
    "                (\"basis_effect_intent_ref\", None),\n"
    "                (\"expected_program_head_revision\", 0),\n"
    "                (\"resulting_program_version_number\", 1),\n"
    "                (\"resulting_program_version_ref\", \"exact program_version_ref\"),\n"
    "                (\"selected_semantic_attempt_ref\", None),\n"
    "                (\"selected_candidate_ref\", None),\n"
    "                (\"preassigned_semantic_attempt_ref\", \"exact preassigned_semantic_attempt_ref\"),\n"
    "                (\"preassigned_candidate_ref\", \"exact preassigned_candidate_ref\"),\n"
    "                (\"reason_code\", \"program_genesis\"),\n"
    "            ),\n"
    "            \"mutation_receipt\": (\n"
    "                (\"mutation_family\", \"initialize_development_program\"),\n"
    "                (\"outcome\", \"committed\"),\n"
    "            ),\n"
    "        },\n"
    "        \"single_transaction_timestamp\": True,\n"
    "        \"absent_rows_and_effects\": (\n"
    "            \"revision_edge\",\n"
    "            \"semantic_attempt\",\n"
    "            \"effect\",\n"
    "            \"command row\",\n"
    "            \"delivery\",\n"
    "            \"observation\",\n"
    "            \"capsule\",\n"
    "            \"Git row\",\n"
    "            \"external request\",\n"
    "        ),\n"
    "    },\n"
    "    \"write_order\": {\n"
    "        \"foreign_keys_continuously_enabled\": True,\n"
    "        \"ordered_rows\": (\n"
    "            \"program_head\",\n"
    "            \"accepted_intent_revision\",\n"
    "            \"work_item_head\",\n"
    "            \"work_item_revision\",\n"
    "            \"initialize_decision\",\n"
    "            \"program_version\",\n"
    "            \"program_version_work_item\",\n"
    "            \"work_spec_binding\",\n"
    "            \"mutation_receipt\",\n"
    "        ),\n"
    "    },\n"
    "    \"initialize_graph\": {\n"
    "        \"entry_count\": 8,\n"
    "        \"receipt_is_envelope\": True,\n"
    "        \"receipt_is_entry\": False,\n"
    "        \"entries\": (\n"
    "            (0, \"program_head_postimage\", 0, \"program_ref\"),\n"
    "            (1, \"accepted_intent_revision\", 0, \"accepted_intent_revision_ref\"),\n"
    "            (2, \"initialize_decision\", 0, \"decision_ref\"),\n"
    "            (3, \"program_version\", 0, \"program_version_ref\"),\n"
    "            (4, \"work_item_head_postimage\", 0, \"work_item_ref\"),\n"
    "            (5, \"work_item_revision\", 0, \"work_item_revision_ref\"),\n"
    "            (6, \"program_version_work_item\", 0, \"work_item_ref\"),\n"
    "            (7, \"work_spec_binding\", 0, \"work_spec_ref\"),\n"
    "        ),\n"
    "        \"ordering\": (\"rank ASC\", \"ordinal ASC\"),\n"
    "        \"mutable_preimages\": \"exact absence; not graph entries\",\n"
    "        \"basis_and_global_stop_rows\": \"verified dependencies; not graph entries\",\n"
    "        \"same_ref_distinct_roles_allowed\": \"work_item_ref\",\n"
    "        \"digest_primitive\": \"existing common supplied-entry mutation-graph digest primitive\",\n"
    "    },\n"
    "    \"complete_graph_locator\": {\n"
    "        \"starts_from\": (\"exact safe command\", \"mutation receipt\"),\n"
    "        \"lookups\": (\n"
    "            \"receipt by mutation_ref\",\n"
    "            \"initialize decision and resulting version by program_ref + decision_ref\",\n"
    "            \"accepted-intent revision by program_ref + accepted_intent_revision_ref\",\n"
    "            \"program head by program_ref\",\n"
    "            \"sole complete membership by program_ref + program_version_ref\",\n"
    "            \"work-item head and exact revision by program_ref + work_item_ref + work_item_revision_ref\",\n"
    "            \"WorkSpec binding by exact program/version/work/revision identity, then exact work_spec_ref equality\",\n"
    "        ),\n"
    "        \"completeness\": (\n"
    "            \"exactly one membership\",\n"
    "            \"membership ordinal 0\",\n"
    "            \"exactly one matching WorkSpec binding\",\n"
    "            \"returned binding work_spec_ref equals safe-command work_spec_ref and graph-entry expected work_spec_ref\",\n"
    "            \"all row self-digests valid\",\n"
    "            \"all cross-row relations valid\",\n"
    "            \"historical program-head postimage valid\",\n"
    "            \"historical work-head postimage valid\",\n"
    "            \"persisted result projection valid\",\n"
    "            \"mutation graph digest valid\",\n"
    "        ),\n"
    "        \"physical_lookup_key\": (\n"
    "            \"program_ref\",\n"
    "            \"program_version_ref\",\n"
    "            \"work_item_ref\",\n"
    "            \"work_item_revision_ref\",\n"
    "        ),\n"
    "        \"returned_work_spec_ref_mismatch\": \"database_integrity_failure\",\n"
    "        \"forbidden_selection\": (\"absence\", \"latest row\", \"timestamp\", \"rowid\", \"scan\", \"different WorkSpec\"),\n"
    "        \"generic_graph_engine\": False,\n"
    "        \"future_reads\": \"bounded family-specific absence/collision reads only\",\n"
    "    },\n"
    "    \"persisted_result_projection\": {\n"
    "        \"schema_id\": \"governed-execution.nwp-initialize-development-program-result.v1\",\n"
    "        \"digest_domain\": \"governed-execution.nwp-initialize-development-program-result.v1.identity\",\n"
    "        \"ordered_fields\": (\n"
    "            \"schema_id\",\n"
    "            \"program_ref\",\n"
    "            \"decision_ref\",\n"
    "            \"result_program_version_ref\",\n"
    "            \"result_decision_ref\",\n"
    "        ),\n"
    "        \"result_program_version_ref\": \"exactly program_version_ref\",\n"
    "        \"result_decision_ref\": \"exactly decision_ref\",\n"
    "    },\n"
    "    \"private_apply_result\": {\n"
    "        \"semantic_name\": \"DevelopmentProgramInitializationResultV1\",\n"
    "        \"ordered_fields\": (\n"
    "            \"disposition\",\n"
    "            \"mutation_ref\",\n"
    "            \"command_digest\",\n"
    "            \"program_ref\",\n"
    "            \"program_version_ref\",\n"
    "            \"accepted_intent_revision_ref\",\n"
    "            \"decision_ref\",\n"
    "            \"work_item_ref\",\n"
    "            \"work_item_revision_ref\",\n"
    "            \"work_spec_ref\",\n"
    "            \"preassigned_semantic_attempt_ref\",\n"
    "            \"preassigned_candidate_ref\",\n"
    "            \"transaction_timestamp\",\n"
    "        ),\n"
    "        \"dispositions\": (\"committed\", \"exact_replay\"),\n"
    "    },\n"
    "    \"private_outcome_ownership\": {\n"
    "        \"future_module\": \"src/ge_nwp_coordinator/_development_program_initialization_contracts.py\",\n"
    "        \"module_present_this_turn\": False,\n"
    "        \"package_root_export\": False,\n"
    "        \"conflict_reason\": {\n"
    "            \"semantic_name\": \"DevelopmentProgramInitializationConflictReasonV1\",\n"
    "            \"values\": (\n"
    "                \"mutation_ref_reuse_conflict\",\n"
    "                \"global_stop_version_conflict\",\n"
    "                \"coding_global_stop_active\",\n"
    "                \"semantic_identity_conflict\",\n"
    "            ),\n"
    "        },\n"
    "        \"conflict_result\": {\n"
    "            \"semantic_name\": \"DevelopmentProgramInitializationConflictV1\",\n"
    "            \"ordered_fields\": (\"reason\", \"mutation_ref\", \"command_digest\", \"program_ref\"),\n"
    "            \"reason_type\": \"exact DevelopmentProgramInitializationConflictReasonV1\",\n"
    "            \"posture\": (\n"
    "                \"not persisted\",\n"
    "                \"not canonical durable identity\",\n"
    "                \"not a SQLite safe error\",\n"
    "                \"not a public apply-conflict value\",\n"
    "                \"not package-exported\",\n"
    "                \"not authority\",\n"
    "            ),\n"
    "        },\n"
    "        \"recovery_disposition\": {\n"
    "            \"semantic_name\": \"DevelopmentProgramInitializationRecoveryDispositionV1\",\n"
    "            \"values\": (\"committed_exact\", \"definitely_not_committed\", \"unresolved\"),\n"
    "        },\n"
    "        \"existing_sqlite_store_error_reasons\": (\n"
    "            \"database_integrity_failure\",\n"
    "            \"mutation_failed\",\n"
    "            \"commit_outcome_unknown\",\n"
    "        ),\n"
    "        \"public_surfaces_unchanged\": (\n"
    "            \"models.APPLY_CONFLICT_REASONS\",\n"
    "            \"sqlite_errors\",\n"
    "            \"package root\",\n"
    "            \"StateStore\",\n"
    "            \"public WriterSession protocol\",\n"
    "        ),\n"
    "    },\n"
    "    \"mutation_receipt\": {\n"
    "        \"family\": \"initialize_development_program\",\n"
    "        \"command_schema_id\": \"governed-execution.nwp-initialize-development-program-command.v1\",\n"
    "        \"result_class\": \"development_program_initialized\",\n"
    "        \"result_attempt_ref\": None,\n"
    "        \"result_effect_ref\": None,\n"
    "        \"result_fence_ref\": None,\n"
    "        \"result_delivery_ref\": None,\n"
    "        \"result_observation_ref\": None,\n"
    "        \"outcome\": \"committed\",\n"
    "        \"self_digest\": None,\n"
    "        \"graph_entry_count\": 8,\n"
    "        \"failed_fresh_receipt\": False,\n"
    "    },\n"
    "    \"exact_replay\": {\n"
    "        \"after_writer_fencing\": True,\n"
    "        \"ordered_steps\": (\n"
    "            \"read receipt by mutation_ref\",\n"
    "            \"absent receipt selects fresh path\",\n"
    "            \"present receipt with different command digest is mutation_ref_reuse_conflict\",\n"
    "            \"validate receipt family, schema, and scalar algebra\",\n"
    "            \"locate all eight graph entries\",\n"
    "            \"validate every row self-digest\",\n"
    "            \"validate all program/version/decision/intent/work/membership/WorkSpec relations\",\n"
    "            \"reconstruct historical program and work head postimages\",\n"
    "            \"recompute accepted-intent projection, persisted result projection, and graph digest\",\n"
    "            \"return original private result with disposition exact_replay\",\n"
    "        ),\n"
    "        \"incomplete_or_malformed_graph\": \"database_integrity_failure\",\n"
    "        \"contradictory_same_revision_head\": \"database_integrity_failure\",\n"
    "        \"later_valid_head_advancement\": \"allowed; historical replay remains exact\",\n"
    "        \"later_C2B6_lineage_proven\": False,\n"
    "    },\n"
    "    \"commit_uncertainty_cleanup_gate\": {\n"
    "        \"commit_attempt_exception\": \"controller records commit_outcome_unknown\",\n"
    "        \"raw_connection_owner_before_close\": \"transaction controller retains exclusive custody\",\n"
    "        \"close_attempt_precedes\": (\n"
    "            \"clearing controller connection custody\",\n"
    "            \"making the mutation slot available\",\n"
    "            \"returning commit_outcome_unknown to the caller\",\n"
    "        ),\n"
    "        \"close_complete\": {\n"
    "            \"controller_connection_custody\": \"cleared\",\n"
    "            \"mutation_slot_available\": True,\n"
    "            \"session_quarantined\": False,\n"
    "            \"outward_store_error\": \"commit_outcome_unknown\",\n"
    "            \"original_apply_error\": {\n"
    "                \"type\": \"SQLiteMutationStoreError\",\n"
    "                \"reason\": \"commit_outcome_unknown\",\n"
    "                \"internal_detail\": None,\n"
    "                \"cause\": None,\n"
    "                \"context\": None,\n"
    "                \"notes\": None,\n"
    "                \"raised_from\": None,\n"
    "            },\n"
    "            \"slot_release_gate\": \"only after close proof\",\n"
    "            \"fresh_resolver\": \"permitted later under a new operation lease and reacquired same shared slot\",\n"
    "        },\n"
    "        \"close_not_proved\": {\n"
    "            \"ordered_steps\": (\n"
    "                \"commit attempt raises\",\n"
    "                \"controller retains connection custody and mutation slot\",\n"
    "                \"close is attempted\",\n"
    "                \"close not proved\",\n"
    "                \"connection custody transfers to private _WriterSessionResource\",\n"
    "                \"session quarantine is recorded\",\n"
    "                \"writer-authority lock remains retained\",\n"
    "                \"mutation slot remains unavailable\",\n"
    "                \"fresh content-free commit_outcome_unknown is raised from None\",\n"
    "            ),\n"
    "            \"raw_connection_custody\": \"transferred to and retained by private _WriterSessionResource\",\n"
    "            \"session_state\": \"commit-uncertain quarantined\",\n"
    "            \"writer_authority_lock\": \"retained by that concrete session\",\n"
    "            \"mutation_slot_available\": False,\n"
    "            \"original_apply_error\": {\n"
    "                \"type\": \"SQLiteMutationStoreError\",\n"
    "                \"reason\": \"commit_outcome_unknown\",\n"
    "                \"internal_detail\": None,\n"
    "                \"cause\": None,\n"
    "                \"context\": None,\n"
    "                \"notes\": None,\n"
    "                \"raised_from\": None,\n"
    "            },\n"
    "            \"close_failure_role\": \"secondary\",\n"
    "            \"close_failure_replaces_primary_error\": False,\n"
    "            \"close_failure_decorates_primary_error\": False,\n"
    "            \"close_failure_leaks_outward\": False,\n"
    "            \"close_exception_in_outward_error_graph\": False,\n"
    "            \"same_session_mutation\": False,\n"
    "            \"same_session_database_backed_resolver\": False,\n"
    "            \"same_session_resolver_disposition\": \"unresolved before operation-lease acquisition, database open, BEGIN, or SQL\",\n"
    "            \"permitted_work\": \"explicit close/finalization of the retained connection only\",\n"
    "            \"new_session_resolver_before_proved_close\": False,\n"
    "            \"definitely_not_committed\": False,\n"
    "            \"automatic_semantic_retry\": False,\n"
    "            \"process_control_close_interruption_ordered_steps\": (\n"
    "                \"observe the exact process-control exception object from connection close\",\n"
    "                \"retain the mutation slot\",\n"
    "                \"retain the writer-authority lock\",\n"
    "                \"transfer the uncertain raw connection into the private _WriterSessionResource\",\n"
    "                \"publish the concrete session as commit-uncertain quarantined\",\n"
    "                \"confirm same-session mutation and database-backed recovery remain forbidden\",\n"
    "                \"confirm no operation lease, database open, BEGIN, or SQL can occur\",\n"
    "                \"re-raise the identical process-control exception object\",\n"
    "            ),\n"
    "            \"process_control_exceptions\": {\n"
    "                \"KeyboardInterrupt\": {\n"
    "                    \"exception_identity_preserved\": True,\n"
    "                    \"connection_custody_transferred_before_propagation\": True,\n"
    "                    \"quarantine_published_before_propagation\": True,\n"
    "                    \"writer_lock_retained_before_propagation\": True,\n"
    "                    \"mutation_slot_retained_before_propagation\": True,\n"
    "                    \"same_session_database_recovery_allowed\": False,\n"
    "                    \"operation_lease_allowed_before_close_proof\": False,\n"
    "                    \"database_open_allowed_before_close_proof\": False,\n"
    "                    \"begin_allowed_before_close_proof\": False,\n"
    "                    \"sql_allowed_before_close_proof\": False,\n"
    "                    \"ordinary_store_error_conversion\": False,\n"
    "                    \"automatic_semantic_retry\": False,\n"
    "                },\n"
    "                \"SystemExit\": {\n"
    "                    \"exception_identity_preserved\": True,\n"
    "                    \"connection_custody_transferred_before_propagation\": True,\n"
    "                    \"quarantine_published_before_propagation\": True,\n"
    "                    \"writer_lock_retained_before_propagation\": True,\n"
    "                    \"mutation_slot_retained_before_propagation\": True,\n"
    "                    \"same_session_database_recovery_allowed\": False,\n"
    "                    \"operation_lease_allowed_before_close_proof\": False,\n"
    "                    \"database_open_allowed_before_close_proof\": False,\n"
    "                    \"begin_allowed_before_close_proof\": False,\n"
    "                    \"sql_allowed_before_close_proof\": False,\n"
    "                    \"ordinary_store_error_conversion\": False,\n"
    "                    \"automatic_semantic_retry\": False,\n"
    "                },\n"
    "                \"GeneratorExit\": {\n"
    "                    \"exception_identity_preserved\": True,\n"
    "                    \"connection_custody_transferred_before_propagation\": True,\n"
    "                    \"quarantine_published_before_propagation\": True,\n"
    "                    \"writer_lock_retained_before_propagation\": True,\n"
    "                    \"mutation_slot_retained_before_propagation\": True,\n"
    "                    \"same_session_database_recovery_allowed\": False,\n"
    "                    \"operation_lease_allowed_before_close_proof\": False,\n"
    "                    \"database_open_allowed_before_close_proof\": False,\n"
    "                    \"begin_allowed_before_close_proof\": False,\n"
    "                    \"sql_allowed_before_close_proof\": False,\n"
    "                    \"ordinary_store_error_conversion\": False,\n"
    "                    \"automatic_semantic_retry\": False,\n"
    "                },\n"
    "            },\n"
    "            \"process_control_exception_graph_ledger\": (\n"
    "                {\n"
    "                    \"branch_name\": \"KeyboardInterrupt\",\n"
    "                    \"propagation_form\": \"bare_reraise\",\n"
    "                    \"same_exception_object\": True,\n"
    "                    \"exact_type_preserved\": True,\n"
    "                    \"args_preserved\": True,\n"
    "                    \"system_exit_code_preserved_or_not_applicable\": \"not_applicable\",\n"
    "                    \"caught_traceback_tail_identity_preserved\": True,\n"
    "                    \"repair_owned_traceback_frame_delta\": 0,\n"
    "                    \"cause_before\": None,\n"
    "                    \"cause_after\": None,\n"
    "                    \"context_before\": None,\n"
    "                    \"context_after\": None,\n"
    "                    \"suppress_context_before\": False,\n"
    "                    \"suppress_context_after\": False,\n"
    "                    \"notes_before\": \"absent\",\n"
    "                    \"notes_after\": \"absent\",\n"
    "                    \"private_material_in_exception_graph\": False,\n"
    "                    \"automatic_semantic_retry\": False,\n"
    "                },\n"
    "                {\n"
    "                    \"branch_name\": \"SystemExit\",\n"
    "                    \"propagation_form\": \"bare_reraise\",\n"
    "                    \"same_exception_object\": True,\n"
    "                    \"exact_type_preserved\": True,\n"
    "                    \"args_preserved\": True,\n"
    "                    \"system_exit_code_preserved_or_not_applicable\": \"preserved\",\n"
    "                    \"caught_traceback_tail_identity_preserved\": True,\n"
    "                    \"repair_owned_traceback_frame_delta\": 0,\n"
    "                    \"cause_before\": None,\n"
    "                    \"cause_after\": None,\n"
    "                    \"context_before\": None,\n"
    "                    \"context_after\": None,\n"
    "                    \"suppress_context_before\": False,\n"
    "                    \"suppress_context_after\": False,\n"
    "                    \"notes_before\": \"absent\",\n"
    "                    \"notes_after\": \"absent\",\n"
    "                    \"private_material_in_exception_graph\": False,\n"
    "                    \"automatic_semantic_retry\": False,\n"
    "                },\n"
    "                {\n"
    "                    \"branch_name\": \"GeneratorExit\",\n"
    "                    \"propagation_form\": \"bare_reraise\",\n"
    "                    \"same_exception_object\": True,\n"
    "                    \"exact_type_preserved\": True,\n"
    "                    \"args_preserved\": True,\n"
    "                    \"system_exit_code_preserved_or_not_applicable\": \"not_applicable\",\n"
    "                    \"caught_traceback_tail_identity_preserved\": True,\n"
    "                    \"repair_owned_traceback_frame_delta\": 0,\n"
    "                    \"cause_before\": None,\n"
    "                    \"cause_after\": None,\n"
    "                    \"context_before\": None,\n"
    "                    \"context_after\": None,\n"
    "                    \"suppress_context_before\": False,\n"
    "                    \"suppress_context_after\": False,\n"
    "                    \"notes_before\": \"absent\",\n"
    "                    \"notes_after\": \"absent\",\n"
    "                    \"private_material_in_exception_graph\": False,\n"
    "                    \"automatic_semantic_retry\": False,\n"
    "                },\n"
    "            ),\n"
    "        },\n"
    "        \"quarantine_clearance\": (\n"
    "            \"proven retained-connection closure\",\n"
    "            \"proven writer-authority-lock release\",\n"
    "            \"newly acquired concrete writer session\",\n"
    "            \"exact safe command\",\n"
    "        ),\n"
    "        \"caller_authored_clearance\": False,\n"
    "        \"forbidden_clearance_evidence\": (\n"
    "            \"cleanup token\",\n"
    "            \"Boolean assertion\",\n"
    "            \"path marker\",\n"
    "            \"report\",\n"
    "            \"timeout\",\n"
    "        ),\n"
    "        \"forbidden_outward_material\": (\n"
    "            \"raw connection\",\n"
    "            \"cursor\",\n"
    "            \"transaction controller\",\n"
    "            \"mutation-slot object\",\n"
    "            \"writer-lock object\",\n"
    "            \"quarantine object\",\n"
    "            \"ordinary commit exception\",\n"
    "            \"close implementation details\",\n"
    "            \"SQLite path\",\n"
    "            \"SQL or parameters\",\n"
    "            \"WorkSpec material\",\n"
    "        ),\n"
    "        \"forbidden_outward_destinations\": (\n"
    "            \"safe command\",\n"
    "            \"receipt\",\n"
    "            \"apply result\",\n"
    "            \"resolver result\",\n"
    "            \"public value\",\n"
    "            \"exception payload\",\n"
    "            \"log\",\n"
    "            \"report\",\n"
    "            \"future C2B3-owned outward traceback locals\",\n"
    "        ),\n"
    "        \"process_control_exception_graph_privacy\": {\n"
    "            \"forbidden_material\": (\n"
    "                \"ordinary commit exception\",\n"
    "                \"ordinary close exception\",\n"
    "                \"raw SQLite exception\",\n"
    "                \"connection\",\n"
    "                \"cursor\",\n"
    "                \"controller\",\n"
    "                \"mutation-slot object\",\n"
    "                \"writer-lock object\",\n"
    "                \"quarantine object\",\n"
    "                \"database path\",\n"
    "                \"SQL\",\n"
    "                \"parameters\",\n"
    "                \"WorkSpec content\",\n"
    "                \"private test sentinel\",\n"
    "            ),\n"
    "            \"forbidden_surfaces\": (\n"
    "                \"exception args\",\n"
    "                \"str or repr\",\n"
    "                \"__cause__ graph\",\n"
    "                \"__context__ graph\",\n"
    "                \"__notes__\",\n"
    "                \"formatted traceback\",\n"
    "                \"C2B3-owned traceback-frame locals\",\n"
    "                \"returned or persisted values\",\n"
    "                \"logs or reports\",\n"
    "            ),\n"
    "            \"sole_permitted_outward_exception\": \"the identical process-control exception object\",\n"
    "        },\n"
    "    },\n"
    "    \"commit_outcome_recovery\": {\n"
    "        \"semantic_name\": \"DevelopmentProgramInitializationRecoveryResultV1\",\n"
    "        \"disposition_owner\": \"DevelopmentProgramInitializationRecoveryDispositionV1\",\n"
    "        \"dispositions\": (\n"
    "            \"committed_exact\",\n"
    "            \"definitely_not_committed\",\n"
    "            \"unresolved\",\n"
    "        ),\n"
    "        \"inputs\": (\n"
    "            \"currently valid concrete _SQLiteWriterSession\",\n"
    "            \"exact safe initialization command\",\n"
    "        ),\n"
    "        \"accepts_work_spec\": False,\n"
    "        \"lifecycle\": (\n"
    "            \"prior uncertain connection closure and prior writer-lock release are proven\",\n"
    "            \"newly acquired concrete writer session\",\n"
    "            \"new operation guard and fresh operation lease\",\n"
    "            \"reacquire existing shared mutation slot\",\n"
    "            \"same transaction-controller class\",\n"
    "            \"fresh readback-only BEGIN IMMEDIATE\",\n"
    "            \"managed schema and resource revalidation\",\n"
    "            \"writer fencing\",\n"
    "            \"same nominal read capability\",\n"
    "            \"readback only\",\n"
    "            \"rollback and close\",\n"
    "        ),\n"
    "        \"same_session_resolver_while_quarantined\": False,\n"
    "        \"mutation_slot_available_before_close_completion\": False,\n"
    "        \"close_not_proved_disposition\": \"unresolved\",\n"
    "        \"committed_exact_requires\": (\n"
    "            \"exact receipt\",\n"
    "            \"exact command digest\",\n"
    "            \"exact persisted result\",\n"
    "            \"all eight graph entries\",\n"
    "            \"all row self-digests\",\n"
    "            \"all cross-row relations\",\n"
    "            \"both historical head postimages\",\n"
    "            \"exact result-projection digest\",\n"
    "            \"exact mutation-graph digest\",\n"
    "        ),\n"
    "        \"definitely_not_committed_requires_all_absent\": (\n"
    "            \"receipt for mutation_ref\",\n"
    "            \"program head for program_ref\",\n"
    "            \"program version for program_version_ref\",\n"
    "            \"accepted-intent revision for accepted_intent_revision_ref\",\n"
    "            \"decision for decision_ref\",\n"
    "            \"work-item head for work_item_ref\",\n"
    "            \"work-item revision for work_item_revision_ref\",\n"
    "            \"membership for command identities\",\n"
    "            \"WorkSpec binding for work_spec_ref\",\n"
    "        ),\n"
    "        \"unresolved_evidence\": (\n"
    "            \"receipt-only\",\n"
    "            \"graph-without-receipt\",\n"
    "            \"partial graph\",\n"
    "            \"mixed evidence\",\n"
    "            \"malformed evidence\",\n"
    "            \"contradictory postimage\",\n"
    "            \"unlocatable evidence\",\n"
    "            \"any state other than exact committed or exact all-absent\",\n"
    "        ),\n"
    "        \"basis_or_global_stop_presence_proves_family_commit\": False,\n"
    "        \"automatic_semantic_retry\": False,\n"
    "        \"fresh_retry_after_definitely_not_committed\": \"caller must supply the exact complete WorkSpecV1 again\",\n"
    "    },\n"
    "    \"conflict_precedence\": {\n"
    "        \"after_writer_fencing\": (\n"
    "            (1, \"exact receipt replay\"),\n"
    "            (2, \"mutation_ref_reuse_conflict\"),\n"
    "            (3, \"global_stop_version_conflict\"),\n"
    "            (4, \"coding_global_stop_active\"),\n"
    "            (5, \"semantic_identity_conflict\"),\n"
    "            (6, \"database_integrity_failure\"),\n"
    "            (7, \"mutation_failed\"),\n"
    "            (8, \"commit_outcome_unknown\"),\n"
    "        ),\n"
    "        \"classification_conditions\": (\n"
    "            (\"exact receipt replay\", \"same mutation_ref and same command digest with an exact complete persisted family\"),\n"
    "            (\"mutation_ref_reuse_conflict\", \"same mutation_ref and different command digest\"),\n"
    "            (\"global_stop_version_conflict\", \"coding-global-stop ref or version mismatch\"),\n"
    "            (\"coding_global_stop_active\", \"active exact coding global stop\"),\n"
    "            (\"semantic_identity_conflict\", \"pre-existing program or colliding genesis semantic identity\"),\n"
    "            (\"database_integrity_failure\", \"malformed or contradictory persisted state\"),\n"
    "            (\"mutation_failed\", \"operational SQLite or capability failure\"),\n"
    "            (\"commit_outcome_unknown\", \"commit-attempt exception\"),\n"
    "        ),\n"
    "        \"semantic_identity_conflict_visibility\": \"private\",\n"
    "        \"program_head_conflict\": \"reserved for later non-genesis CAS-bearing families\",\n"
    "        \"failed_fresh_operation_creates_receipt\": False,\n"
    "    },\n"
    "    \"privacy_and_traceback\": {\n"
    "        \"ordered_failure_boundary\": (\n"
    "            \"sensitive WorkSpec reducer\",\n"
    "            \"safe closed outcome\",\n"
    "            \"raw reducer returns normally\",\n"
    "            \"outer wrapper clears WorkSpec and caught-exception references\",\n"
    "            \"fresh bounded outward failure from None\",\n"
    "        ),\n"
    "        \"complete_work_spec_forbidden_destinations\": (\n"
    "            \"SQLite\",\n"
    "            \"safe command\",\n"
    "            \"receipt\",\n"
    "            \"result\",\n"
    "            \"resolver input\",\n"
    "            \"exception payload\",\n"
    "            \"log\",\n"
    "            \"report\",\n"
    "            \"traceback locals owned by future C2B3 source\",\n"
    "        ),\n"
    "        \"forbidden_custody_sources\": (\n"
    "            \"chat\",\n"
    "            \"model memory\",\n"
    "            \"Bridge\",\n"
    "            \"reports\",\n"
    "            \"connectors\",\n"
    "            \"logs\",\n"
    "            \"transcripts\",\n"
    "        ),\n"
    "        \"transaction_controller_receives_work_spec\": False,\n"
    "        \"contract_freeze_persists_or_executes_work_spec\": False,\n"
    "    },\n"
    "    \"later_author_effect_owner_decisions\": {\n"
    "        \"complete_contract_frozen\": False,\n"
    "        \"source_implemented\": False,\n"
    "        \"initial_basis\": (\"initialize\", \"program_genesis\"),\n"
    "        \"attempt_number\": 1,\n"
    "        \"planned_adapter_kind\": \"execution_substrate\",\n"
    "        \"route_effect\": \"absent\",\n"
    "        \"planned_adapter_value_authority\": \"safe planned-row value only; no ES compatibility, dispatch permission, route eligibility, reliable submit, or current API binding\",\n"
    "        \"adapter_safe_correlation_ref\": \"preassigned, safe, non-authoritative\",\n"
    "        \"work_spec_ingress\": \"same-call transient only\",\n"
    "        \"authority_evaluation\": {\n"
    "            \"authorship\": \"Coordinator-authored pending evidence\",\n"
    "            \"evaluation_scope\": \"effect\",\n"
    "            \"evaluation_subject_ref\": \"exact effect_intent_ref\",\n"
    "            \"semantic_attempt_ref\": None,\n"
    "            \"effect_intent_ref\": \"exact effect_intent_ref\",\n"
    "            \"authority_ref\": \"exact externally authored effect_authorization_ref\",\n"
    "            \"authority_digest\": \"exact externally authored effect_authorization_digest\",\n"
    "            \"authority_state\": \"pending\",\n"
    "            \"reason_code\": \"external_verification_pending\",\n"
    "            \"expires_at\": None,\n"
    "            \"evaluated_at\": \"one transaction timestamp\",\n"
    "            \"authority_evaluation_ref\": \"preassigned and command-bound\",\n"
    "            \"dispatch_eligibility\": False,\n"
    "        },\n"
    "        \"coordinator_does_not_author\": (\n"
    "            \"verified\",\n"
    "            \"blocked\",\n"
    "            \"stale\",\n"
    "            \"revoked\",\n"
    "            \"expired\",\n"
    "            \"executable permission\",\n"
    "            \"ES admission\",\n"
    "            \"worker authorization\",\n"
    "        ),\n"
    "        \"requirement_provenance\": {\n"
    "            \"refs\": \"exact validation_requirement_ref and review_requirement_ref from WorkSpec\",\n"
    "            \"digests\": \"exact typed safe requirement evidence supplied in the same future private call\",\n"
    "            \"raw_digest_only_input\": False,\n"
    "            \"digest_inference_from_refs\": False,\n"
    "            \"digest_inference_from_text_reports_or_runtime\": False,\n"
    "        },\n"
    "        \"recovery\": \"explicit fresh-lease readback\",\n"
    "        \"graph_membership\": \"family-created rows only\",\n"
    "        \"C2B3C_must_freeze_before_source\": (\n"
    "            \"exact typed requirement evidence\",\n"
    "            \"exact author command\",\n"
    "            \"AttemptFence ingress\",\n"
    "            \"all author refs\",\n"
    "            \"effect and delivery postimages\",\n"
    "            \"nine graph entries\",\n"
    "            \"golden vector\",\n"
    "            \"replay matrix\",\n"
    "            \"recovery matrix\",\n"
    "            \"privacy matrix\",\n"
    "        ),\n"
    "        \"direct_local_bootstrap_selected\": False,\n"
    "        \"direct_local_posture\": \"separate later proof/contract; never a silently selected runtime alternative\",\n"
    "        \"ES_invocation_or_compatibility_claim\": False,\n"
    "    },\n"
    "    \"future_c2b3b_maximum_path_scope\": {\n"
    "        \"tranche\": \"C2B3B_PRIVATE_ATOMIC_INITIALIZATION\",\n"
    "        \"maximum_paths\": 24,\n"
    "        \"production\": (\n"
    "            \"src/ge_nwp_coordinator/_development_program_initialization_contracts.py\",\n"
    "            \"src/ge_nwp_coordinator/_sqlite_development_program_initialization.py\",\n"
    "            \"src/ge_nwp_coordinator/sqlite_transition_transaction.py\",\n"
    "            \"src/ge_nwp_coordinator/sqlite_writer_session.py\",\n"
    "            \"src/ge_nwp_coordinator/sqlite_connection.py\",\n"
    "        ),\n"
    "        \"documentation_status\": (\n"
    "            \".docs/c2b-durable-development-state.md\",\n"
    "            \".docs/c2b3-program-initialization.md\",\n"
    "            \".docs/c2b2-private-readers.md\",\n"
    "            \".docs/architecture.md\",\n"
    "            \".docs/durable-state-model.md\",\n"
    "            \".docs/sqlite-operations-and-recovery.md\",\n"
    "            \".docs/sqlite-threat-model.md\",\n"
    "            \"README.md\",\n"
    "            \"AGENTS.md\",\n"
    "        ),\n"
    "        \"tests\": (\n"
    "            \"tests/test_c2b3_program_initialization_contract.py\",\n"
    "            \"tests/test_c2b3_private_atomic_program_initialization.py\",\n"
    "            \"tests/test_c2b3_program_initialization_recovery.py\",\n"
    "            \"tests/test_c2b3_private_program_initialization_delegation.py\",\n"
    "            \"tests/test_c2b2_field_level_contract.py\",\n"
    "            \"tests/test_c2b2_private_development_readers.py\",\n"
    "            \"tests/test_c2b2_development_reader_contracts.py\",\n"
    "            \"tests/test_runtime_non_authority.py\",\n"
    "            \"tests/test_architecture_contracts.py\",\n"
    "            \"tests/test_c2b0_durable_state_contract.py\",\n"
    "        ),\n"
    "        \"counts\": {\n"
    "            \"production\": 5,\n"
    "            \"documentation_status\": 9,\n"
    "            \"tests\": 10,\n"
    "            \"total\": 24,\n"
    "        },\n"
    "        \"production_responsibilities\": {\n"
    "            \"src/ge_nwp_coordinator/_development_program_initialization_contracts.py\": (\n"
    "                \"private pure command, projection, result, conflict, recovery, graph, and quarantine-admission values\",\n"
    "                \"no process-control result or enum\",\n"
    "                \"no ordinary-value representation of KeyboardInterrupt, SystemExit, or GeneratorExit\",\n"
    "                \"no SQLite\",\n"
    "                \"no I/O\",\n"
    "                \"no package export\",\n"
    "            ),\n"
    "            \"src/ge_nwp_coordinator/_sqlite_development_program_initialization.py\": (\n"
    "                \"sensitive same-call reducer\",\n"
    "                \"safe initialization command construction\",\n"
    "                \"exact replay\",\n"
    "                \"fresh apply\",\n"
    "                \"family-specific graph location and verification\",\n"
    "                \"explicit recovery resolver\",\n"
    "                \"does not catch, translate, wrap, or retry KeyboardInterrupt, SystemExit, or GeneratorExit after transaction cleanup returns them for propagation\",\n"
    "                \"no public API\",\n"
    "                \"no external I/O\",\n"
    "            ),\n"
    "            \"src/ge_nwp_coordinator/sqlite_transition_transaction.py\": (\n"
    "                \"preserve one-commit-attempt ownership\",\n"
    "                \"retain uncertain connection and mutation slot after commit exception\",\n"
    "                \"attempt close before custody clear\",\n"
    "                \"transfer retained connection into session resource when close is unproved\",\n"
    "                \"reduce and detach the ordinary commit failure before close-time process-control handling\",\n"
    "                \"own the narrow close-interruption catch point\",\n"
    "                \"recognize exactly KeyboardInterrupt, SystemExit, and GeneratorExit\",\n"
    "                \"catch exactly KeyboardInterrupt, SystemExit, and GeneratorExit from close\",\n"
    "                \"retain connection and mutation-slot custody for a named process-control close interruption\",\n"
    "                \"retain connection, slot, and writer-lock custody\",\n"
    "                \"request session-resource quarantine publication and wait for publication completion\",\n"
    "                \"re-raise the identical process-control exception only after publication completion\",\n"
    "                \"perform a bare re-raise in the same catch suite\",\n"
    "                \"add no traceback frame beyond bare-reraise semantics\",\n"
    "                \"add no cause, context, note, or exception-graph material\",\n"
    "                \"do not execute unconditional slot release in a named process-control branch\",\n"
    "                \"never unconditionally release the slot after commit uncertainty\",\n"
    "                \"preserve fresh content-free commit_outcome_unknown\",\n"
    "                \"admit no semantic retry\",\n"
    "            ),\n"
    "            \"src/ge_nwp_coordinator/sqlite_writer_session.py\": (\n"
    "                \"private program-initialization delegation only\",\n"
    "                \"_WriterSessionResource retained-connection custody\",\n"
    "                \"commit-uncertain quarantine state\",\n"
    "                \"writer-lock and mutation-slot retention\",\n"
    "                \"reject new operations while quarantined\",\n"
    "                \"acknowledge quarantine publication before the transaction layer re-raises a named process-control exception\",\n"
    "                \"publication acknowledgement must not raise or attach an ordinary exception to the process-control exception\",\n"
    "                \"publication helpers receive no authority to propagate or replace the caught process-control exception\",\n"
    "                \"admit close/finalization only while quarantined\",\n"
    "                \"release quarantine only after proved closure and session disposal\",\n"
    "                \"no public WriterSession protocol change\",\n"
    "            ),\n"
    "            \"src/ge_nwp_coordinator/sqlite_connection.py\": (\n"
    "                \"one private C2B3B-only connection posture or equivalent explicit mechanism permitting proved closure from session-resource finalization\",\n"
    "                \"cross-thread close from session-resource finalization is permitted only for proved closure\",\n"
    "                \"may surface the exact close-time KeyboardInterrupt, SystemExit, or GeneratorExit\",\n"
    "                \"no cross-thread SQL\",\n"
    "                \"no public raw connection\",\n"
    "                \"no public signature widening\",\n"
    "                \"no second connection authority\",\n"
    "                \"existing ordinary connection behavior preserved\",\n"
    "            ),\n"
    "        },\n"
    "        \"twenty_fifth_path\": \"future implementation stop condition\",\n"
    "        \"forbidden\": (\n"
    "            \"pyproject.toml\",\n"
    "            \"package __init__.py\",\n"
    "            \"state_store.py\",\n"
    "            \"sqlite_errors.py\",\n"
    "            \"models.py public values\",\n"
    "            \"sqlite_mutation_transaction_contracts.py\",\n"
    "            \"migration SQL or catalog\",\n"
    "            \"schemas\",\n"
    "            \"C2B4-C2B6 implementation\",\n"
    "            \"another repository\",\n"
    "        ),\n"
    "        \"authorized_by_this_freeze\": False,\n"
    "    },\n"
    "    \"nonimplementation\": {\n"
    "        \"program_initialization_source\": False,\n"
    "        \"private_writer_session_methods\": False,\n"
    "        \"sqlite_insert_or_update_execution\": False,\n"
    "        \"mutation_receipt_persistence\": False,\n"
    "        \"production_reader_integration\": False,\n"
    "        \"exact_replay_runtime\": False,\n"
    "        \"commit_outcome_recovery_runtime\": False,\n"
    "        \"author_effect_source\": False,\n"
    "        \"complete_author_effect_contract\": False,\n"
    "        \"public_C2B_API\": False,\n"
    "        \"StateStore_widening\": False,\n"
    "        \"WriterSession_public_surface_widening\": False,\n"
    "        \"package_root_export\": False,\n"
    "        \"dependency_or_entry_surface\": False,\n"
    "        \"WorkSpec_custody_or_retrieval\": False,\n"
    "        \"authority_verification\": False,\n"
    "        \"worker_or_model_execution\": False,\n"
    "        \"direct_local_execution\": False,\n"
    "        \"Execution_Substrate_invocation\": False,\n"
    "        \"Bridge_integration\": False,\n"
    "        \"schema_change\": False,\n"
    "        \"migration_0001_change\": False,\n"
    "        \"migration_0002_change\": False,\n"
    "        \"migration_0003_creation\": False,\n"
    "        \"C2B4_C2B5_C2B6_behavior\": False,\n"
    "        \"external_IO\": False,\n"
    "    },\n"
)

C2B3A_OWNER_STRUCTURED_TO_VECTOR_BRIDGE = (
    "    # C2B3A_OWNER_ADDENDUM_STRUCTURED_END\n"
    "}\n"
    "```\n"
    "\n"
    "<!-- C2B3_PROGRAM_INITIALIZATION_CONTRACT_PYTHON_END -->\n"
    "\n"
    "The complete initialization-family vector below is one synthetic,\n"
    "privacy-safe contract fixture. It is not runtime-generated identity, operator\n"
    "data, implementation evidence, or authorization.\n"
    "\n"
    "<!-- C2B3_PROGRAM_INITIALIZATION_GOLDEN_VECTOR_PYTHON_BEGIN -->\n"
)

C2B3A_OWNER_VECTOR_TO_EXPLANATORY_BRIDGE = (
    "<!-- C2B3_PROGRAM_INITIALIZATION_GOLDEN_VECTOR_PYTHON_END -->\n"
    "\n"
    "For `initialize` / `program_genesis`, the selected attempt/candidate tuple is\n"
    "wholly absent and the caller-preassigned attempt/candidate tuple is wholly\n"
    "present. Those preassigned refs are future lineage inputs only: initialization\n"
    "does not create, select, authorize, or make executable a semantic attempt or\n"
    "candidate.\n"
    "\n"
    "The `preassigned_attempt_candidate_binding` is ordered as `work_item_ref`,\n"
    "`work_item_revision_ref`, `preassigned_semantic_attempt_ref`, and\n"
    "`preassigned_candidate_ref`. The work-item pair is identical across the safe\n"
    "command WorkSpec projection, the sole program-version membership, and the sole\n"
    "WorkSpec binding. The preassigned attempt/candidate pair is identical across\n"
    "the safe command and initialize decision. No semantic-attempt, candidate, or\n"
    "AttemptFence row is created by initialization.\n"
    "\n"
    "The WorkSpec binding reader remains physically bounded by the exact\n"
    "program/version/work/revision tuple. After decoding its unique result, the\n"
    "future family locator must compare the returned `work_spec_ref` with both the\n"
    "safe command and the rank-7 graph entry. Any mismatch is\n"
    "`database_integrity_failure`; absence, latest-row selection, rowid/timestamp\n"
    "selection, scanning, or choosing another WorkSpec is forbidden.\n"
    "\n"
    "After a commit-attempt exception, connection close is part of the admission\n"
    "gate, not best-effort cleanup after slot release. Until close completes, the\n"
    "controller retains exclusive custody and the slot remains unavailable. If\n"
    "close cannot be proved, custody transfers to the private\n"
    "`_WriterSessionResource`; that concrete session retains its writer lock and is\n"
    "quarantined. Its only permitted work is disposing of the retained connection,\n"
    "and its resolver result is `unresolved` before operation-lease acquisition,\n"
    "database open, `BEGIN`, or SQL. Only proven closure and writer-lock release\n"
    "permit a newly acquired concrete session to run readback. Caller-authored\n"
    "cleanup evidence and automatic semantic retry never clear quarantine.\n"
    "\n"
    "In both the close-complete and close-not-proved branches, the original apply\n"
    "call raises a fresh ordinary `SQLiteMutationStoreError` with reason\n"
    "`commit_outcome_unknown`, null internal detail, cause, context, and notes, and\n"
    "explicit `raise ... from None` behavior. An ordinary close failure is\n"
    "secondary: its text and object cannot replace, decorate, enter the error graph,\n"
    "or leak through that content-free primary error.\n"
    "\n"
    "`KeyboardInterrupt`, `SystemExit`, and `GeneratorExit` are the exact closed\n"
    "process-control close-interruption inventory. After commit uncertainty has\n"
    "begun, if connection close raises one of those exact branches, the transaction\n"
    "layer observes that exact exception object, retains the mutation slot and\n"
    "writer-authority lock, transfers the uncertain raw connection into the private\n"
    "`_WriterSessionResource`, publishes the concrete session as commit-uncertain\n"
    "quarantined, confirms that same-session mutation and database-backed recovery\n"
    "are forbidden before operation-lease acquisition, database open, `BEGIN`, or\n"
    "SQL, and only then re-raises the identical exception object. Exact type and\n"
    "arguments, including `SystemExit.code`, are preserved. The branch does not\n"
    "wrap, replace, translate, retry, or convert the exception into an ordinary\n"
    "store error, `commit_outcome_unknown`, `mutation_failed`, or a private\n"
    "`unresolved` result. Custody, quarantine, the writer lock, and the mutation\n"
    "slot remain retained when propagation occurs.\n"
    "\n"
)

C2B3A_OWNER_EXPLANATORY_SUFFIX = (
    "<!-- C2B3A_OWNER_ADDENDUM_EXPLANATORY_BEGIN -->\n"
    "\n"
    "### C2B3A COMMIT/close outcome addendum projection\n"
    "\n"
    "<!-- C2B3A_OWNER_AUTHORITY_PROSE_BEGIN -->\n"
    "The structured `commit_close_outcome_addendum` value is the sole operative\n"
    "semantic authority for this addendum. The exact bounded explanatory blocks\n"
    "below are non-authoritative projections: they cannot create, override, widen,\n"
    "or narrow a structured owner value, and free-form prose cannot supply operative\n"
    "semantics where a structured owner value exists. Planning cannot resolve or\n"
    "change owner truth.\n"
    "<!-- C2B3A_OWNER_AUTHORITY_PROSE_END -->\n"
    "\n"
    "<!-- C2B3A_OWNER_PROCESS_CONTROL_PROSE_BEGIN -->\n"
    "Propagation is exactly a bare `raise` in the same `except` suite that caught\n"
    "the close-time process-control exception. A named raise, `raise ... from None`,\n"
    "`raise ... from another_exception`, reconstructed exception, explicit\n"
    "`with_traceback(...)`, helper-owned propagation, or later named raise is\n"
    "forbidden merely to manufacture a cosmetic traceback shape. The selected\n"
    "outward object remains the same object with its exact type, arguments, and\n"
    "`SystemExit.code`. C2B3 does not deliberately attach, clear, restore, scrub,\n"
    "sanitize, or rewrite graph or traceback fields and does not deliberately\n"
    "introduce a primary-to-secondary relation. Nested raising and catching may\n"
    "produce interpreter-managed graph and traceback effects; those effects are not\n"
    "C2B3-owned, and no exact resulting graph, reachability, cycle, cause, context,\n"
    "suppression, or traceback-tail shape is guaranteed.\n"
    "\n"
    "The ordinary commit failure must still be reduced and detached before\n"
    "close-time process-control handling; C2B3 creates no new cause, context, note,\n"
    "or private-material edge from the selected raw primary. The earlier exact\n"
    "eighteen-field `process_control_exception_graph_ledger` remains byte-for-byte\n"
    "unchanged as historical C2B3A evidence. It is a historical runtime observation:\n"
    "its exact traceback, cause, context, suppression, cycle, and reachability values\n"
    "describe only the original bounded reference branch. It is non-normative,\n"
    "non-operative for C2B3B, and not a portable contract. No implementation, test\n"
    "oracle, planning projection, or future prompt may use those observed values as\n"
    "target requirements. It is not a universal sanitizer for an arbitrary\n"
    "caller/runtime-authored raw exception. The additive\n"
    "`process_control_relational_policy` supersedes the ledger for target semantics\n"
    "and governs distinct graph-disjoint, distinct pre-linked, and same-instance\n"
    "relations.\n"
    "\n"
    "The additive `commit_close_outcome_addendum` closes the complete ordered\n"
    "six-by-six space without changing that earlier ordinary-commit-exception\n"
    "freeze. Its thirty-six direct rows distinguish normal active `A`, fully\n"
    "disposed `X`, commit-uncertain quarantine `QU`, and known-committed\n"
    "close-unproved quarantine `QK`, while the separate cleanup continuation adds\n"
    "commit-uncertain `PU` and known-committed `PK` after connection closure is\n"
    "proved but residual cleanup remains pending. Every row fixes commit truth,\n"
    "outward identity, raw-connection custody, initial controller/session\n"
    "disposition, recovery or replay, retry, and post-COMMIT rollback. The separate\n"
    "direct relational and cleanup literals close the non-Cartesian identity/graph\n"
    "and residual-cleanup continuations. Neither owner nor independent oracle\n"
    "semantics is generated from the other literal or from a Cartesian product.\n"
    "\n"
    "When COMMIT returns normally, commit truth stays known committed. An ordinary\n"
    "close failure publishes `QK` and retains the connection, resource-owned slot,\n"
    "and writer lock before the identical planned committed result returns. A\n"
    "close-time process-control exception also publishes `QK` before its identical\n"
    "bare-reraise, but the planned result was not delivered; after proved disposal,\n"
    "the identical safe command uses ordinary receipt-first exact replay in a new\n"
    "session. A later normal retained-connection close moves `QK` irreversibly to\n"
    "`PK`; replay remains blocked until residual cleanup reaches `X`. No `QK` or\n"
    "`PK` branch has a commit-outcome resolver.\n"
    "\n"
    "When COMMIT itself raises `KeyboardInterrupt`, `SystemExit`, or\n"
    "`GeneratorExit`, that original exception has absolute outward precedence. If\n"
    "close proves closure, connection custody clears permanently and `PU` is\n"
    "published before residual cleanup. If cleanup completes, state reaches `X`\n"
    "before the original exception propagates. If cleanup is interrupted or\n"
    "incomplete, actual monotonic progress remains in `PU` and the original\n"
    "exception still propagates. If close is not proved, `QU` custody is published\n"
    "before that same original exception propagates. A distinct graph-disjoint\n"
    "secondary is not deliberately attached to the outward primary; a pre-existing\n"
    "link is not deliberately scrubbed or restored, and a same-instance second\n"
    "raise has no distinct secondary. Interpreter-managed relations remain\n"
    "permitted, so no exact secondary reachability or absence result is promised.\n"
    "In every relation C2B3 deliberately adds no new primary-to-secondary\n"
    "relationship. Recovery remains blocked until explicit disposal reaches `X`\n"
    "and releases the writer lock.\n"
    "<!-- C2B3A_OWNER_PROCESS_CONTROL_PROSE_END -->\n"
    "\n"
    "<!-- C2B3A_OWNER_CLEANUP_PROSE_BEGIN -->\n"
    "Explicit disposal of `QU` or `QK` may repeat\n"
    "`retained_connection.close()` until normal return proves closure, then moves\n"
    "irreversibly to `PU` or `PK`. In `PU` or `PK` it never closes the connection\n"
    "again; it resumes only incomplete monotonic, idempotent residual cleanup and\n"
    "reaches `X` only after every release is proved. The one-shot future finalizer\n"
    "catches `BaseException` and never claims retry. A pre-proof failure preserves\n"
    "`QU` or `QK`; a post-proof failure preserves `PU` or `PK` plus truthful\n"
    "progress. Only an explicit reachable handle can resume cleanup. Garbage\n"
    "collection proves neither closure nor cleanup completion. The transient safe\n"
    "command is never reconstructed from an exception, and no complete\n"
    "`WorkSpecV1` enters recovery or session-resource custody.\n"
    "\n"
    "C1 retained-connection close and C2 closure-proof acknowledgment remain named,\n"
    "ordered responsibilities, but a normal C1 return is not an outwardly observable\n"
    "stable boundary until C2 records closure proof, clears raw connection custody,\n"
    "and publishes `QU -> PU` or `QK -> PK`. No model result or modeled exception may\n"
    "be returned between those effects. C1-after and C2-before are therefore not\n"
    "independent stable fault outcomes: once close returns normally, the complete C2\n"
    "acknowledgment is published before residual cleanup or propagation. No output\n"
    "may combine closure proof with `QU`/`QK` or retained connection custody, and no\n"
    "`PU`/`PK` output may retain connection custody. Direct C4-C6/K1 close proof and\n"
    "`PU` publication use the same acknowledgment-complete boundary.\n"
    "\n"
    "Finalizer entry makes the wrapper unreachable, freezes effective operation\n"
    "admission, records `finalizer_attempted=true`, and records\n"
    "`retry_reachable=false` before any later cleanup fault can be exposed. P0 is\n"
    "the mandatory finalizer-entry admission and cleanup-ownership publication; a\n"
    "finalizer P0-before result with effective admission open is not a legal model\n"
    "output. A reachable explicit-close wrapper may retain retryable monotonic P0\n"
    "progress. Neither posture creates registry lookup, hidden disposal, or another\n"
    "in-process retry route after wrapper loss.\n"
    "\n"
    "The Coordinator-generated `commit_outcome_unknown` error remains content-free\n"
    "and may contain none of the raw connection, controller, mutation slot, writer\n"
    "lock, SQL, path, WorkSpec, safe command, or source-exception graph. Raw\n"
    "`KeyboardInterrupt`, `SystemExit`, and `GeneratorExit` are control flow, not\n"
    "privacy-safe report or serialization values. C2B3 never serializes, persists,\n"
    "logs, formats, renders, reports, or copies their payloads or graphs, and never\n"
    "adds C2B3-owned private material or a new edge to a distinct secondary. An\n"
    "arbitrary pre-existing caller/runtime-owned value in args, `SystemExit.code`,\n"
    "notes, cause, context, or traceback is not sanitized while exact raw-object\n"
    "identity is retained.\n"
    "<!-- C2B3A_OWNER_CLEANUP_PROSE_END -->\n"
    "\n"
    "<!-- C2B3A_OWNER_FUTURE_SCOPE_PROSE_BEGIN -->\n"
    "The preserved `future_c2b3b_maximum_path_scope` literal remains byte-for-byte\n"
    "only as historical evidence of the accepted earlier C2B3A freeze. Its five\n"
    "production, nine documentation/status, ten test, twenty-three-expected,\n"
    "twenty-four-maximum, and twenty-fifth-path-stop values are non-operative for\n"
    "C2B3B after this addendum. No consumer, implementation prompt, test, or\n"
    "planning projection may use those historical values as active authority. The\n"
    "only operative future `C2B3B_PRIVATE_ATOMIC_INITIALIZATION` scope is owned by\n"
    "`commit_close_outcome_addendum.future_c2b3b_path_scope_status`: six production\n"
    "paths, ten documentation/status paths, eleven required changed tests, twenty-\n"
    "seven expected actual paths, one contingency path, twenty-eight maximum paths,\n"
    "and a twenty-ninth-path hard stop and scope reassessment. This freeze records\n"
    "future responsibilities but authorizes no C2B3B source or implementation in\n"
    "C2B3A.\n"
    "<!-- C2B3A_OWNER_FUTURE_SCOPE_PROSE_END -->\n"
    "\n"
    "<!-- C2B3A_OWNER_RETAINED_TAIL_BEGIN -->\n"
    "The future private module named by `private_outcome_ownership` is the sole\n"
    "representation owner for the four initialization conflict reasons, their\n"
    "four-field conflict result, and the three recovery dispositions. It remains\n"
    "absent here. None is public, package-exported, durable identity, SQLite error,\n"
    "or authority; the existing three SQLite mutation-store reasons remain\n"
    "unchanged.\n"
    "\n"
    "The literal is closed-world. Exact built-in values, field order, one-item\n"
    "cardinality, row postimages, write order, graph order, family locator,\n"
    "persisted result, receipt, replay, recovery, precedence, privacy, and\n"
    "nonimplementation are all part of the identity of this freeze. Missing,\n"
    "additional, reordered, coerced, or contradictory material is not compatible.\n"
    "The same `work_item_ref` in the two distinct graph roles is intentional.\n"
    "\n"
    "The future C2B3B initializer may enter only through the current concrete SQLite\n"
    "writer session, operation guard, shared mutation slot, existing transaction\n"
    "controller, writer fence, and nominal capability. It must perform no external\n"
    "I/O. Its complete transient `WorkSpecV1` must be reduced before the transaction\n"
    "controller is entered and must not survive into outward traceback frames.\n"
    "Receipt lookup remains before fresh stop or collision disclosure. One immutable\n"
    "family plan, one transaction timestamp, and at most one commit attempt remain\n"
    "mandatory.\n"
    "\n"
    "The author-effect family is deliberately not complete here. In particular,\n"
    "the pending authority-evaluation decision is evidence that external\n"
    "verification has not happened; it is neither authorization nor route\n"
    "eligibility. C2B3C must freeze the exact typed requirement evidence, author\n"
    "command, fence ingress, row postimages, nine-entry graph, golden vector,\n"
    "replay/recovery, and privacy matrix before any C2B3D source may begin.\n"
    "<!-- C2B3A_OWNER_RETAINED_TAIL_END -->\n"
    "\n"
    "<!-- C2B3A_OWNER_ADDENDUM_END -->\n"
)
C2B3A_ORACLE_ALLOWED_IMPORTS = ("ast", "copy", "pathlib", "pytest")
C2B3A_ORACLE_ALLOWED_RELATIVE_READS = (
    ".docs/c2b-durable-development-state.md",
    ".docs/c2b3-program-initialization.md",
    "tests/test_c2b3_program_initialization_contract.py",
)
C2B3A_ORACLE_ALLOWED_DIRECT_CALLS = (
    "GeneratorExit",
    "KeyboardInterrupt",
    "Path",
    "RuntimeError",
    "SystemExit",
    "_ContractViolation",
    "_assert_future_c2b3b_scope",
    "_assert_oracle_architecture",
    "_assert_original_apply_outcome",
    "_assert_preassigned_binding",
    "_assigned_names",
    "_bare_reraise_reference",
    "_candidate",
    "_cleanup_reference",
    "_cleanup_reference_result",
    "_direct_allowed_import_inventory",
    "_direct_literal_assignment",
    "_enclosing_function_name",
    "_exception_graph_snapshot",
    "_exception_graph_identity_walk",
    "_expect_golden_violation",
    "_expect_violation",
    "_golden_candidate",
    "_named_reraise_reference",
    "_owner_contract",
    "_owner_golden_vector",
    "_planning_fence_candidate",
    "_planning_markdown_prefix_stripped",
    "_planning_mutant_at_position",
    "_planning_nonfenced_normalized_lines",
    "_planning_normalized_line",
    "_process_control_exception_graph_contains_private_material",
    "_relational_process_control_reference",
    "_read_allowed_text",
    "_require",
    "_traceback_signature",
    "_validate_contract",
    "_validate_golden_vector",
    "_validate_planning_status",
    "all",
    "any",
    "bool",
    "deepcopy",
    "enumerate",
    "id",
    "isinstance",
    "len",
    "list",
    "next",
    "repr",
    "set",
    "sorted",
    "str",
    "tuple",
    "type",
)
C2B3A_ORACLE_ALLOWED_ATTRIBUTE_CALLS = (
    "ORACLE_SOURCE_PARENT.resolve",
    "after.startswith",
    "ascii_spaced.split",
    "ast.get_source_segment",
    "ast.iter_child_nodes",
    "ast.literal_eval",
    "ast.parse",
    "ast.walk",
    "before.endswith",
    "binding_rendered.lower",
    "candidate.startswith",
    "cardinality.pop",
    "complete.get",
    "digit.isdigit",
    "expected_path.is_symlink",
    "expected_path.resolve",
    "expected_repr.encode",
    "event_ledger.append",
    "item.startswith",
    "lookup.replace",
    "lowered.replace",
    "moved.append",
    "name.lower",
    "names.extend",
    "newline.join",
    "node.name.lower",
    "normalized.endswith",
    "observed_imports.append",
    "observed_repr.encode",
    "owner_source.split",
    "parameter_names.add",
    "parents.get",
    "path.relative_to",
    "payload.strip",
    "planning_document_candidate.count",
    "planning_document_candidate.endswith",
    "planning_document_candidate.replace",
    "prose.append",
    "pytest.mark.parametrize",
    "pytest.raises",
    "quarantined.get",
    "relative.as_posix",
    "remainder.split",
    "remaining.lstrip",
    "resolved.read_text",
    "separator.join",
    "source.count",
    "source.replace",
    "source.split",
    "stripped.lower",
    "stripped_payload.splitlines",
    "swapped.replace",
    "text.index",
    "text.replace",
    "text.rstrip",
    "text.splitlines",
    "vector_remainder.split",
    "vector_tail.replace",
)

C2B3A_PROCESS_CONTROL_ORDERED_STEPS = (
    "observe the exact process-control exception object from connection close",
    "retain the mutation slot",
    "retain the writer-authority lock",
    "transfer the uncertain raw connection into the private _WriterSessionResource",
    "publish the concrete session as commit-uncertain quarantined",
    "confirm same-session mutation and database-backed recovery remain forbidden",
    "confirm no operation lease, database open, BEGIN, or SQL can occur",
    "re-raise the identical process-control exception object",
)
C2B3A_PROCESS_CONTROL_BRANCH_FACTS = {
    "KeyboardInterrupt": {
        "exception_identity_preserved": True,
        "connection_custody_transferred_before_propagation": True,
        "quarantine_published_before_propagation": True,
        "writer_lock_retained_before_propagation": True,
        "mutation_slot_retained_before_propagation": True,
        "same_session_database_recovery_allowed": False,
        "operation_lease_allowed_before_close_proof": False,
        "database_open_allowed_before_close_proof": False,
        "begin_allowed_before_close_proof": False,
        "sql_allowed_before_close_proof": False,
        "ordinary_store_error_conversion": False,
        "automatic_semantic_retry": False,
    },
    "SystemExit": {
        "exception_identity_preserved": True,
        "connection_custody_transferred_before_propagation": True,
        "quarantine_published_before_propagation": True,
        "writer_lock_retained_before_propagation": True,
        "mutation_slot_retained_before_propagation": True,
        "same_session_database_recovery_allowed": False,
        "operation_lease_allowed_before_close_proof": False,
        "database_open_allowed_before_close_proof": False,
        "begin_allowed_before_close_proof": False,
        "sql_allowed_before_close_proof": False,
        "ordinary_store_error_conversion": False,
        "automatic_semantic_retry": False,
    },
    "GeneratorExit": {
        "exception_identity_preserved": True,
        "connection_custody_transferred_before_propagation": True,
        "quarantine_published_before_propagation": True,
        "writer_lock_retained_before_propagation": True,
        "mutation_slot_retained_before_propagation": True,
        "same_session_database_recovery_allowed": False,
        "operation_lease_allowed_before_close_proof": False,
        "database_open_allowed_before_close_proof": False,
        "begin_allowed_before_close_proof": False,
        "sql_allowed_before_close_proof": False,
        "ordinary_store_error_conversion": False,
        "automatic_semantic_retry": False,
    },
}
C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_LEDGER = (
    {
        "branch_name": "KeyboardInterrupt",
        "propagation_form": "bare_reraise",
        "same_exception_object": True,
        "exact_type_preserved": True,
        "args_preserved": True,
        "system_exit_code_preserved_or_not_applicable": "not_applicable",
        "caught_traceback_tail_identity_preserved": True,
        "repair_owned_traceback_frame_delta": 0,
        "cause_before": None,
        "cause_after": None,
        "context_before": None,
        "context_after": None,
        "suppress_context_before": False,
        "suppress_context_after": False,
        "notes_before": "absent",
        "notes_after": "absent",
        "private_material_in_exception_graph": False,
        "automatic_semantic_retry": False,
    },
    {
        "branch_name": "SystemExit",
        "propagation_form": "bare_reraise",
        "same_exception_object": True,
        "exact_type_preserved": True,
        "args_preserved": True,
        "system_exit_code_preserved_or_not_applicable": "preserved",
        "caught_traceback_tail_identity_preserved": True,
        "repair_owned_traceback_frame_delta": 0,
        "cause_before": None,
        "cause_after": None,
        "context_before": None,
        "context_after": None,
        "suppress_context_before": False,
        "suppress_context_after": False,
        "notes_before": "absent",
        "notes_after": "absent",
        "private_material_in_exception_graph": False,
        "automatic_semantic_retry": False,
    },
    {
        "branch_name": "GeneratorExit",
        "propagation_form": "bare_reraise",
        "same_exception_object": True,
        "exact_type_preserved": True,
        "args_preserved": True,
        "system_exit_code_preserved_or_not_applicable": "not_applicable",
        "caught_traceback_tail_identity_preserved": True,
        "repair_owned_traceback_frame_delta": 0,
        "cause_before": None,
        "cause_after": None,
        "context_before": None,
        "context_after": None,
        "suppress_context_before": False,
        "suppress_context_after": False,
        "notes_before": "absent",
        "notes_after": "absent",
        "private_material_in_exception_graph": False,
        "automatic_semantic_retry": False,
    },
)
C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_FIELDS = (
    "branch_name",
    "propagation_form",
    "same_exception_object",
    "exact_type_preserved",
    "args_preserved",
    "system_exit_code_preserved_or_not_applicable",
    "caught_traceback_tail_identity_preserved",
    "repair_owned_traceback_frame_delta",
    "cause_before",
    "cause_after",
    "context_before",
    "context_after",
    "suppress_context_before",
    "suppress_context_after",
    "notes_before",
    "notes_after",
    "private_material_in_exception_graph",
    "automatic_semantic_retry",
)
C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_PRIVACY = {
    "forbidden_material": (
        "ordinary commit exception",
        "ordinary close exception",
        "raw SQLite exception",
        "connection",
        "cursor",
        "controller",
        "mutation-slot object",
        "writer-lock object",
        "quarantine object",
        "database path",
        "SQL",
        "parameters",
        "WorkSpec content",
        "private test sentinel",
    ),
    "forbidden_surfaces": (
        "exception args",
        "str or repr",
        "__cause__ graph",
        "__context__ graph",
        "__notes__",
        "formatted traceback",
        "C2B3-owned traceback-frame locals",
        "returned or persisted values",
        "logs or reports",
    ),
    "sole_permitted_outward_exception": "the identical process-control exception object",
}
C2B3A_PROCESS_CONTROL_POSITIVE_MODELS = (
    (
        "KeyboardInterrupt",
        "test_keyboard_interrupt_close_fault_publishes_before_identical_propagation",
        "repair4-keyboard",
    ),
    (
        "SystemExit",
        "test_system_exit_close_fault_publishes_before_identical_propagation",
        41,
    ),
    (
        "GeneratorExit",
        "test_generator_exit_close_fault_publishes_before_identical_propagation",
        "repair4-generator",
    ),
)
C2B3A_PROCESS_CONTROL_EXPECTED_CASE_IDS = (
    "cross-k-s",
    "cross-k-g",
    "cross-s-k",
    "cross-s-g",
    "cross-g-k",
    "cross-g-s",
    "distinct-k",
    "distinct-s",
    "distinct-g",
    "same-k",
    "same-s",
    "same-g",
    "prelinked-cause",
    "prelinked-context",
    "linked-cycle",
    "private-payload",
)
C2B3A_CLEANUP_EXPECTED_CASE_IDS = (
    "normal-a", "normal-qu", "normal-qk", "normal-pu", "normal-pk",
    "p0-before", "p0-after", "c1-before", "c1-after", "c2-before",
    "c2-after", "r1-before", "r1-after", "r2-before", "r2-after",
    "r3-before", "r3-after", "l1-before", "l1-after", "h1-before",
    "h1-after", "h2-before", "h2-between", "h2-after", "t1-before",
    "t1-after", "h3-before", "h3-after", "primary-pu-k",
    "primary-pu-s", "primary-pu-g", "primary-pk-k", "primary-pk-s",
    "primary-pk-g", "precedence-pu-k-s", "precedence-pu-s-g",
    "precedence-pu-g-k", "precedence-pk-k-g", "precedence-pk-s-k",
    "precedence-pk-g-s", "finalizer-cleanup-k", "finalizer-cleanup-s",
    "finalizer-cleanup-g", "finalizer-primary-k", "finalizer-primary-s",
    "finalizer-primary-g", "close-qu-ordinary", "close-qu-k",
    "close-qk-s", "close-qk-g", "close-qu-g-primary-k",
    "close-qk-k-primary-s", "unlock-unproved", "unlock-retry-normal",
    "descriptor-unknown",
)
C2B3A_ORACLE_PROTECTED_EXPECTED_VALUE_NAMES = (
    "EXPECTED_PLANNING_PROJECTION",
    "EXPECTED_INITIALIZATION_CONTRACT",
    "EXPECTED_INITIALIZATION_GOLDEN_VECTOR",
    "EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM",
    "EXPECTED_PROCESS_CONTROL_REFERENCE_CASES",
    "CLEANUP_SAFE_PROJECTION_FIELDS",
    "CLEANUP_REFERENCE_INPUT_CASES",
    "EXPECTED_CLEANUP_REFERENCE_CASES",
)
C2B3A_ORACLE_PROTECTED_CANDIDATE_VALUE_NAMES = (
    "owner_contract_candidate",
    "owner_golden_vector_candidate",
    "planning_document_candidate",
)
C2B3A_ORACLE_PROTECTED_READER_PARSER_NAMES = (
    "_owner_contract",
    "_owner_golden_vector",
    "_read_allowed_text",
)
C2B3A_ORACLE_PROTECTED_VALIDATION_HELPER_NAMES = (
    "_assert_future_c2b3b_scope",
    "_assert_oracle_architecture",
    "_assert_original_apply_outcome",
    "_assert_preassigned_binding",
    "_validate_contract",
    "_validate_golden_vector",
    "_validate_planning_status",
    "_expect_violation",
    "_expect_golden_violation",
)
C2B3A_ORACLE_PROTECTED_CALLABLE_NAMES = (
    "_assert_future_c2b3b_scope",
    "_assert_oracle_architecture",
    "_assert_original_apply_outcome",
    "_assert_preassigned_binding",
    "_bare_reraise_reference",
    "_candidate",
    "_cleanup_reference",
    "_cleanup_reference_result",
    "_exception_graph_identity_walk",
    "_expect_golden_violation",
    "_expect_violation",
    "_golden_candidate",
    "_named_reraise_reference",
    "_owner_contract",
    "_owner_golden_vector",
    "_read_allowed_text",
    "_relational_process_control_reference",
    "_validate_contract",
    "_validate_golden_vector",
    "_validate_planning_status",
)
C2B3A_LINEAR_MUTANT_FUNCTIONS = (
    ("M16", "test_commit_close_mutant_m16_missing_matrix_row_is_rejected"),
    ("M17", "test_commit_close_mutant_m17_duplicate_matrix_row_is_rejected"),
    ("M18", "test_commit_close_mutant_m18_reordered_matrix_rows_is_rejected"),
    ("M19", "test_commit_close_mutant_m19_c1k2_state_is_rejected"),
    ("M20", "test_commit_close_mutant_m20_c4k1_state_is_rejected"),
    ("M21", "test_commit_close_mutant_m21_cleanup_primary_precedence_is_rejected"),
    ("M22", "test_commit_close_mutant_m22_named_raise_is_rejected"),
    ("M23", "test_commit_close_mutant_m23_reconstructed_system_exit_is_rejected"),
    ("M24", "test_commit_close_mutant_m24_post_commit_rollback_is_rejected"),
    ("M25", "test_commit_close_mutant_m25_slot_release_before_quarantine_is_rejected"),
    ("M26", "test_commit_close_mutant_m26_pending_cleanup_sql_is_rejected"),
    ("M27", "test_commit_close_mutant_m27_finalizer_retry_is_rejected"),
    ("M28", "test_commit_close_mutant_m28_work_spec_recovery_custody_is_rejected"),
    ("M29", "test_commit_close_mutant_m29_production_behavior_is_rejected"),
    ("M30", "test_commit_close_mutant_m30_scope_maximum_is_rejected"),
    ("M31", "test_commit_close_mutant_m31_same_class_implies_same_object_is_rejected"),
    ("M32", "test_commit_close_mutant_m32_distinct_same_class_routing_is_rejected"),
    ("M33", "test_commit_close_mutant_m33_same_instance_routing_is_rejected"),
    ("M34", "test_commit_close_mutant_m34_prelinked_cause_promise_is_rejected"),
    ("M35", "test_commit_close_mutant_m35_prelinked_context_promise_is_rejected"),
    ("M36", "test_commit_close_mutant_m36_fixed_graph_shape_is_rejected"),
    ("M37", "test_commit_close_mutant_m37_graph_scrub_is_rejected"),
    ("M38", "test_commit_close_mutant_m38_universal_sanitization_is_rejected"),
    ("M39", "test_commit_close_mutant_m39_raw_payload_copy_is_rejected"),
    ("M40", "test_commit_close_mutant_m40_raw_payload_report_is_rejected"),
    ("M41", "test_commit_close_mutant_m41_descriptor_close_release_proof_is_rejected"),
    ("M42", "test_commit_close_mutant_m42_x_before_release_proof_is_rejected"),
    ("M43", "test_commit_close_mutant_m43_authority_registry_before_release_is_rejected"),
    ("M44", "test_commit_close_mutant_m44_acquisition_on_unproved_release_is_rejected"),
    ("M45", "test_commit_close_mutant_m45_recovery_on_unproved_release_is_rejected"),
    ("M46", "test_commit_close_mutant_m46_replay_on_unproved_release_is_rejected"),
    ("M47", "test_commit_close_mutant_m47_descriptor_close_retry_is_rejected"),
    ("M48", "test_commit_close_mutant_m48_session_registry_before_x_is_rejected"),
    ("M49", "test_commit_close_mutant_m49_descriptor_reclamation_x_gate_is_rejected"),
    ("M50", "test_commit_close_mutant_m50_retry_after_wrapper_loss_is_rejected"),
    ("M51", "test_commit_close_mutant_m51_hidden_registry_cleanup_is_rejected"),
    ("M52", "test_commit_close_mutant_m52_c2k1_pending_state_is_rejected"),
    ("M53", "test_commit_close_mutant_m53_c3k1_pending_state_is_rejected"),
    ("M54", "test_commit_close_mutant_m54_a_to_x_lock_bypass_is_rejected"),
    ("M55", "test_commit_close_mutant_m55_finalizer_automatic_retry_is_rejected"),
    ("M56", "test_commit_close_mutant_m56_finalizer_clears_progress_is_rejected"),
    ("M57", "test_commit_close_mutant_m57_missing_lock_source_path_is_rejected"),
    ("M58", "test_commit_close_mutant_m58_missing_writer_authority_doc_is_rejected"),
    ("M59", "test_commit_close_mutant_m59_missing_lock_test_is_rejected"),
    ("M60", "test_commit_close_mutant_m60_missing_writer_session_test_is_rejected"),
    ("M61", "test_commit_close_mutant_m61_historical_scope_reactivation_is_rejected"),
    ("M62", "test_commit_close_mutant_m62_dynamic_oracle_derivation_is_rejected"),
    ("M63", "test_commit_close_mutant_m63_implementation_claim_is_rejected"),
    ("M64", "test_commit_close_mutant_m64_h2_order_is_rejected"),
    ("M65", "test_commit_close_mutant_m65_new_operation_in_pending_state_is_rejected"),
)
C2B3A_EFFICACY_GUARD_ASSURANCE_BOUNDARY = {
    "classification": "bounded exact-byte self-test assurance",
    "in_scope_guarantees": (
        "the exact checked-in efficacy function header and body match the independently authored bounded AST/dataflow grammar",
        "the exact checked-in function has no local or lexical binding of exec",
        "the exact checked-in module has no ordinary lexical module binding of exec that changes the efficacy function resolution",
        "the exact checked-in source contains no directly recognized source-local module-dictionary replacement of exec",
        "the exact checked-in source contains no wildcard import capable of supplying exec",
        "the efficacy function in-function namespace, immediate validator capture, baseline validation, terminal validation, one-mutant invocation, restoration, and aggregate behavior retain their existing exact protections",
        "runtime instrumentation on the exact audited bytes observes builtins.exec as the callable used by the checked execution path",
        "runtime instrumentation observes 100 calls to the exec-produced validator and zero calls to an alternate validator",
    ),
    "explicit_non_claims": (
        "resistance to malicious coordinated editing of both the efficacy checker and its higher-order guard",
        "resistance to mutation of builtins.exec or the builtins object",
        "resistance to mutation through __builtins__",
        "resistance to a pre-poisoned or malicious sys.modules environment",
        "resistance to mutation of imported module objects",
        "resistance to custom import hooks or loaders",
        "resistance to tracing, profiling, debugger, coverage, or interpreter instrumentation that changes execution",
        "resistance to hostile monkeypatching performed outside the bounded source-local forms",
        "resistance to arbitrary Python metaprogramming",
        "resistance to process or interpreter compromise",
    ),
    "external_assurance_chain": (
        "exact patch provenance",
        "fresh independent read-only audit",
        "staged-blob equality",
        "committed-blob equality",
        "Git object and ref truth",
    ),
    "external_assurance_role": (
        "provenance and audit are external assurance mechanisms, not semantics "
        "owned by this test"
    ),
}
C2B3A_MUTANT_EFFICACY_CHECKER_CONTRACT = {
    "function_name": "_assert_c2b3a_mutant_dataflow_semantics",
    "assurance_boundary_name": "C2B3A_EFFICACY_GUARD_ASSURANCE_BOUNDARY",
    "outer_function_header": (
        ("node_type", "FunctionDef"),
        ("name", "_assert_c2b3a_mutant_dataflow_semantics"),
        ("decorators", ()),
        ("return_annotation", ("Constant", None, None)),
        ("type_comment", None),
        ("type_params", ()),
        ("posonlyargs", ()),
        (
            "args",
            (
                (
                    "tree",
                    (
                        "Attribute",
                        ("Name", "ast", "Load"),
                        "Module",
                        "Load",
                    ),
                    None,
                ),
            ),
        ),
        ("defaults", ()),
        ("vararg", None),
        ("kwonlyargs", ()),
        ("kw_defaults", ()),
        ("kwarg", None),
    ),
    "module_lexical_exec_binding_inventory": (),
    "module_lexical_ast_binding_inventory": (("import_alias", 1),),
    "module_wildcard_import_inventory": (),
    "direct_source_local_module_dictionary_operation_inventory": (),
    "mapping_source_name": "C2B3A_LINEAR_MUTANT_FUNCTIONS",
    "ordered_mutant_ids": (
        "M16", "M17", "M18", "M19", "M20", "M21", "M22", "M23", "M24",
        "M25", "M26", "M27", "M28", "M29", "M30", "M31", "M32", "M33",
        "M34", "M35", "M36", "M37", "M38", "M39", "M40", "M41", "M42",
        "M43", "M44", "M45", "M46", "M47", "M48", "M49", "M50", "M51",
        "M52", "M53", "M54", "M55", "M56", "M57", "M58", "M59", "M60",
        "M61", "M62", "M63", "M64", "M65",
    ),
    "candidate_factory_name": "_candidate",
    "validator_name": "_validate_contract",
    "contract_exception_name": "_ContractViolation",
    "terminal_helper_name": "_expect_violation",
    "execution_namespace_name": "namespace",
    "captured_validator_name": "original_validate",
    "validator_namespace_key": "_validate_contract",
    "namespace_construction_source": (
        "namespace: dict[str, object] = {'__file__': str(C2B3A_ORACLE_PATH), "
        "'__name__': 'c2b3a_mutant_efficacy_probe'}"
    ),
    "exec_capture_try_source": (
        "try:\n"
        "    exec(compile(tree, filename=str(C2B3A_ORACLE_PATH), mode='exec'), "
        "namespace)\n"
        "    original_validate = namespace['_validate_contract']\n"
        "except BaseException:\n"
        "    raise AssertionError(diagnostic) from None"
    ),
    "pre_mapping_loop_statement_sources": (
        "diagnostic = 'C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID'",
        "expected_m16_m65_ids = ('M16', 'M17', 'M18', 'M19', 'M20', 'M21', "
        "'M22', 'M23', 'M24', 'M25', 'M26', 'M27', 'M28', 'M29', 'M30', "
        "'M31', 'M32', 'M33', 'M34', 'M35', 'M36', 'M37', 'M38', 'M39', "
        "'M40', 'M41', 'M42', 'M43', 'M44', 'M45', 'M46', 'M47', 'M48', "
        "'M49', 'M50', 'M51', 'M52', 'M53', 'M54', 'M55', 'M56', 'M57', "
        "'M58', 'M59', 'M60', 'M61', 'M62', 'M63', 'M64', 'M65')",
        "if tuple((mutant_id for mutant_id, _name in "
        "C2B3A_LINEAR_MUTANT_FUNCTIONS)) != expected_m16_m65_ids or "
        "tuple(C2B3A_M16_M65_EXPECTED_MUTATION_SOURCE) != "
        "expected_m16_m65_ids:\n    raise AssertionError(diagnostic)",
        "expected_names = tuple((name for _mutant_id, name in "
        "C2B3A_LINEAR_MUTANT_FUNCTIONS))",
        "observed_named_functions = tuple((node.name for node in tree.body if "
        "isinstance(node, ast.FunctionDef) and "
        "node.name.startswith('test_commit_close_mutant_m')))",
        "if observed_named_functions != expected_names:\n"
        "    raise AssertionError(diagnostic)",
        "expected_name_set = set(expected_names)",
        "for node in tree.body:\n"
        "    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n"
        "        continue\n"
        "    parameter_names = {argument.arg for argument in "
        "tuple(node.args.posonlyargs) + tuple(node.args.args) + "
        "tuple(node.args.kwonlyargs)}\n"
        "    if 'mutant_id' in parameter_names:\n"
        "        raise AssertionError(diagnostic)\n"
        "    if node.name.startswith('test_commit_close_') and 'mutant' in "
        "node.name and (node.name not in expected_name_set):\n"
        "        raise AssertionError(diagnostic)",
        "def is_exact_candidate_factory(statement: ast.stmt) -> bool:\n"
        "    return isinstance(statement, ast.Assign) and "
        "len(statement.targets) == 1 and isinstance(statement.targets[0], "
        "ast.Name) and (statement.targets[0].id == 'candidate') and "
        "isinstance(statement.targets[0].ctx, ast.Store) and "
        "isinstance(statement.value, ast.Call) and "
        "isinstance(statement.value.func, ast.Name) and "
        "(statement.value.func.id == '_candidate') and "
        "(not statement.value.args) and (not statement.value.keywords)",
        "def is_exact_terminal_validation(statement: ast.stmt) -> bool:\n"
        "    if not isinstance(statement, ast.Expr):\n"
        "        return False\n"
        "    call = statement.value\n"
        "    return isinstance(call, ast.Call) and "
        "isinstance(call.func, ast.Name) and "
        "(call.func.id == '_expect_violation') and (len(call.args) == 2) and "
        "isinstance(call.args[0], ast.Name) and "
        "(call.args[0].id == 'candidate') and "
        "isinstance(call.args[0].ctx, ast.Load) and "
        "isinstance(call.args[1], ast.Constant) and "
        "(call.args[1].value == 'C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID') and "
        "(not call.keywords)",
        "signatures: dict[str, tuple[str, ...]] = {}",
        "namespace: dict[str, object] = {'__file__': "
        "str(C2B3A_ORACLE_PATH), '__name__': "
        "'c2b3a_mutant_efficacy_probe'}",
        "try:\n"
        "    exec(compile(tree, filename=str(C2B3A_ORACLE_PATH), mode='exec'), "
        "namespace)\n"
        "    original_validate = namespace['_validate_contract']\n"
        "except BaseException:\n"
        "    raise AssertionError(diagnostic) from None",
        "original_candidate = namespace.get('_candidate')",
        "original_expect_violation = namespace.get('_expect_violation')",
        "direct_deepcopy = namespace.get('deepcopy')",
        "contract_violation = namespace.get('_ContractViolation')",
        "if not (callable(original_candidate) and callable(original_validate) "
        "and callable(original_expect_violation) and callable(direct_deepcopy) "
        "and isinstance(contract_violation, type) and "
        "issubclass(contract_violation, Exception)):\n"
        "    raise AssertionError(diagnostic)",
        "execution_totals: dict[str, int] = {'mapping_entries': 0, "
        "'valid_baselines': 0, 'mutant_invocations': 0, "
        "'changed_candidates': 0, 'identical_candidate_terminals': 0, "
        "'single_terminal_reaches': 0, 'exact_supplied_diagnostics': 0, "
        "'exact_validator_diagnostics': 0}",
    ),
    "protected_binding_names": (
        "namespace",
        "original_validate",
        "original_candidate",
        "original_expect_violation",
        "controlled_candidate",
        "instrumented_candidate",
        "instrumented_expect_violation",
        "candidate",
        "supplied_diagnostic",
        "exec",
    ),
    "protected_binding_inventory": (
        ("candidate", "argument"),
        ("controlled_candidate", "name_store"),
        ("instrumented_candidate", "function_definition"),
        ("instrumented_expect_violation", "function_definition"),
        ("namespace", "name_store"),
        ("original_candidate", "name_store"),
        ("original_expect_violation", "name_store"),
        ("original_validate", "name_store"),
        ("supplied_diagnostic", "argument"),
    ),
    "namespace_subscript_inventory": (
        (
            "_assert_c2b3a_mutant_dataflow_semantics",
            "if namespace['_validate_contract'] is not original_validate:\n"
            "    raise AssertionError(diagnostic)",
            "namespace['_validate_contract']",
            "Load",
        ),
        (
            "_assert_c2b3a_mutant_dataflow_semantics",
            "namespace['_candidate'] = instrumented_candidate",
            "namespace['_candidate']",
            "Store",
        ),
        (
            "_assert_c2b3a_mutant_dataflow_semantics",
            "namespace['_candidate'] = original_candidate",
            "namespace['_candidate']",
            "Store",
        ),
        (
            "_assert_c2b3a_mutant_dataflow_semantics",
            "namespace['_expect_violation'] = instrumented_expect_violation",
            "namespace['_expect_violation']",
            "Store",
        ),
        (
            "_assert_c2b3a_mutant_dataflow_semantics",
            "namespace['_expect_violation'] = original_expect_violation",
            "namespace['_expect_violation']",
            "Store",
        ),
        (
            "_assert_c2b3a_mutant_dataflow_semantics",
            "original_validate = namespace['_validate_contract']",
            "namespace['_validate_contract']",
            "Load",
        ),
        (
            "instrumented_expect_violation",
            "if namespace['_validate_contract'] is not original_validate:\n"
            "    raise AssertionError(diagnostic)",
            "namespace['_validate_contract']",
            "Load",
        ),
    ),
    "namespace_get_inventory": (
        (
            "_assert_c2b3a_mutant_dataflow_semantics",
            "contract_violation = namespace.get('_ContractViolation')",
            "namespace.get('_ContractViolation')",
        ),
        (
            "_assert_c2b3a_mutant_dataflow_semantics",
            "direct_deepcopy = namespace.get('deepcopy')",
            "namespace.get('deepcopy')",
        ),
        (
            "_assert_c2b3a_mutant_dataflow_semantics",
            "if namespace.get('_candidate') is not original_candidate or "
            "namespace.get('_expect_violation') is not "
            "original_expect_violation:\n    raise AssertionError(diagnostic)",
            "namespace.get('_candidate')",
        ),
        (
            "_assert_c2b3a_mutant_dataflow_semantics",
            "if namespace.get('_candidate') is not original_candidate or "
            "namespace.get('_expect_violation') is not "
            "original_expect_violation:\n    raise AssertionError(diagnostic)",
            "namespace.get('_expect_violation')",
        ),
        (
            "_assert_c2b3a_mutant_dataflow_semantics",
            "mutant_function = namespace.get(function_name)",
            "namespace.get(function_name)",
        ),
        (
            "_assert_c2b3a_mutant_dataflow_semantics",
            "original_candidate = namespace.get('_candidate')",
            "namespace.get('_candidate')",
        ),
        (
            "_assert_c2b3a_mutant_dataflow_semantics",
            "original_expect_violation = namespace.get('_expect_violation')",
            "namespace.get('_expect_violation')",
        ),
    ),
    "loop_target_names": ("mutant_id", "function_name"),
    "execution_record_fields": (
        "candidate_factory_calls",
        "mutant_calls",
        "terminal_calls",
        "identical_candidate",
        "supplied_diagnostic",
        "validator_diagnostic",
    ),
    "aggregate_record_fields": (
        "mapping_entries",
        "valid_baselines",
        "mutant_invocations",
        "changed_candidates",
        "identical_candidate_terminals",
        "single_terminal_reaches",
        "exact_supplied_diagnostics",
        "exact_validator_diagnostics",
    ),
    "function_top_level_statement_kinds": (
        "Assign", "Assign", "If", "Assign", "Assign", "If", "Assign", "For",
        "FunctionDef", "FunctionDef", "AnnAssign", "AnnAssign", "Try", "Assign",
        "Assign", "Assign", "Assign", "If", "AnnAssign", "For", "If", "If",
        "If", "If",
    ),
    "mapping_loop_statement_kinds": (
        "Assign", "If", "Assign", "Assign", "Assign", "If", "Try",
        "AugAssign", "AugAssign", "AnnAssign", "FunctionDef", "FunctionDef",
        "Assign", "Assign", "Try", "If", "If", "If", "AugAssign", "AugAssign",
        "AugAssign", "AugAssign", "AugAssign", "AugAssign", "Assign", "Assign",
        "If", "Assign", "Assign", "If", "For", "Assign", "Assign", "If",
        "Assign",
    ),
    "mapping_loop_statement_sources": (
        "mutant_function = namespace.get(function_name)",
        "if not callable(mutant_function):\n    raise AssertionError(diagnostic)",
        "expected_diagnostic = 'C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID'",
        "controlled_candidate = original_candidate()",
        "valid_baseline = direct_deepcopy(controlled_candidate)",
        "if namespace['_validate_contract'] is not original_validate:\n"
        "    raise AssertionError(diagnostic)",
        "try:\n    original_validate(controlled_candidate)\nexcept BaseException:\n"
        "    raise AssertionError(diagnostic) from None",
        "execution_totals['mapping_entries'] += 1",
        "execution_totals['valid_baselines'] += 1",
        "execution: dict[str, object] = {'candidate_factory_calls': 0, "
        "'mutant_calls': 0, 'terminal_calls': 0, 'identical_candidate': False, "
        "'supplied_diagnostic': None, 'validator_diagnostic': None}",
        "def instrumented_candidate() -> object:\n"
        "    execution['candidate_factory_calls'] = "
        "int(execution['candidate_factory_calls']) + 1\n"
        "    if execution['candidate_factory_calls'] != 1:\n"
        "        raise AssertionError(diagnostic)\n"
        "    return controlled_candidate",
        "def instrumented_expect_violation(candidate: object, "
        "supplied_diagnostic: object) -> None:\n"
        "    execution['terminal_calls'] = int(execution['terminal_calls']) + 1\n"
        "    if execution['terminal_calls'] != 1:\n"
        "        raise AssertionError(diagnostic)\n"
        "    execution['identical_candidate'] = candidate is controlled_candidate\n"
        "    execution['supplied_diagnostic'] = supplied_diagnostic\n"
        "    if candidate is not controlled_candidate:\n"
        "        raise AssertionError(diagnostic)\n"
        "    if supplied_diagnostic != expected_diagnostic:\n"
        "        raise AssertionError(diagnostic)\n"
        "    if namespace['_validate_contract'] is not original_validate:\n"
        "        raise AssertionError(diagnostic)\n"
        "    with pytest.raises(contract_violation) as exc_info:\n"
        "        original_validate(candidate)\n"
        "    execution['validator_diagnostic'] = str(exc_info.value)\n"
        "    if execution['validator_diagnostic'] != expected_diagnostic:\n"
        "        raise AssertionError(diagnostic)",
        "namespace['_candidate'] = instrumented_candidate",
        "namespace['_expect_violation'] = instrumented_expect_violation",
        "try:\n"
        "    execution['mutant_calls'] = int(execution['mutant_calls']) + 1\n"
        "    mutant_function()\n"
        "except BaseException:\n"
        "    raise AssertionError(diagnostic) from None\n"
        "finally:\n"
        "    namespace['_candidate'] = original_candidate\n"
        "    namespace['_expect_violation'] = original_expect_violation",
        "if namespace.get('_candidate') is not original_candidate or "
        "namespace.get('_expect_violation') is not original_expect_violation:\n"
        "    raise AssertionError(diagnostic)",
        "if controlled_candidate == valid_baseline:\n"
        "    raise AssertionError(diagnostic)",
        "if execution['candidate_factory_calls'] != 1 or "
        "execution['mutant_calls'] != 1 or execution['terminal_calls'] != 1 or "
        "(execution['identical_candidate'] is not True) or "
        "(execution['supplied_diagnostic'] != expected_diagnostic) or "
        "(execution['validator_diagnostic'] != expected_diagnostic):\n"
        "    raise AssertionError(diagnostic)",
        "execution_totals['mutant_invocations'] += 1",
        "execution_totals['changed_candidates'] += 1",
        "execution_totals['identical_candidate_terminals'] += 1",
        "execution_totals['single_terminal_reaches'] += 1",
        "execution_totals['exact_supplied_diagnostics'] += 1",
        "execution_totals['exact_validator_diagnostics'] += 1",
        "function = _c2b3a_oracle_top_level_function(tree, function_name)",
        "expected_mutations = C2B3A_M16_M65_EXPECTED_MUTATION_SOURCE[mutant_id]",
        "if _c2b3a_oracle_function_parameters(function) or function.decorator_list "
        "or len(function.body) != len(expected_mutations) + 2 or "
        "(not is_exact_candidate_factory(function.body[0])) or "
        "(not is_exact_terminal_validation(function.body[-1])):\n"
        "    raise AssertionError(diagnostic)",
        "mutations = function.body[1:-1]",
        "mutation_source = tuple((ast.unparse(statement) for statement in mutations))",
        "if mutation_source != expected_mutations:\n"
        "    raise AssertionError(diagnostic)",
        "for statement in mutations:\n"
        "    if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:\n"
        "        raise AssertionError(diagnostic)\n"
        "    names = tuple((node for node in ast.walk(statement) if "
        "isinstance(node, ast.Name)))\n"
        "    if not names or any((node.id != 'candidate' for node in names)):\n"
        "        raise AssertionError(diagnostic)",
        "calls = tuple((node for node in ast.walk(function) if "
        "isinstance(node, ast.Call)))",
        "candidate_stores = tuple((node for node in ast.walk(function) if "
        "isinstance(node, ast.Name) and node.id == 'candidate' and "
        "isinstance(node.ctx, ast.Store)))",
        "if len(calls) != 2 or len(candidate_stores) != 1 or "
        "calls[0] is not function.body[0].value or "
        "(calls[1] is not function.body[-1].value):\n"
        "    raise AssertionError(diagnostic)",
        "signatures[mutant_id] = mutation_source",
    ),
    "post_loop_statement_sources": (
        "if tuple(signatures) != expected_m16_m65_ids:\n"
        "    raise AssertionError(diagnostic)",
        "if signatures != C2B3A_M16_M65_EXPECTED_MUTATION_SOURCE:\n"
        "    raise AssertionError(diagnostic)",
        "if len(set(signatures.values())) != len(expected_m16_m65_ids):\n"
        "    raise AssertionError(diagnostic)",
        "if execution_totals != {'mapping_entries': 50, 'valid_baselines': 50, "
        "'mutant_invocations': 50, 'changed_candidates': 50, "
        "'identical_candidate_terminals': 50, 'single_terminal_reaches': 50, "
        "'exact_supplied_diagnostics': 50, 'exact_validator_diagnostics': 50}:\n"
        "    raise AssertionError(diagnostic)",
    ),
}
C2B3A_M16_M65_EXPECTED_MUTATION_SOURCE = {
    "M16": ("candidate['commit_close_outcome_addendum']['outcome_matrix'] = candidate['commit_close_outcome_addendum']['outcome_matrix'][:-1]",),
    "M17": ("candidate['commit_close_outcome_addendum']['outcome_matrix'] = candidate['commit_close_outcome_addendum']['outcome_matrix'][:-1] + (candidate['commit_close_outcome_addendum']['outcome_matrix'][0],)",),
    "M18": ("candidate['commit_close_outcome_addendum']['outcome_matrix'] = (candidate['commit_close_outcome_addendum']['outcome_matrix'][1], candidate['commit_close_outcome_addendum']['outcome_matrix'][0]) + candidate['commit_close_outcome_addendum']['outcome_matrix'][2:]",),
    "M19": ("candidate['commit_close_outcome_addendum']['outcome_matrix'] = candidate['commit_close_outcome_addendum']['outcome_matrix'][:1] + (candidate['commit_close_outcome_addendum']['outcome_matrix'][1][:12] + ('QU',) + candidate['commit_close_outcome_addendum']['outcome_matrix'][1][13:],) + candidate['commit_close_outcome_addendum']['outcome_matrix'][2:]",),
    "M20": ("candidate['commit_close_outcome_addendum']['outcome_matrix'] = candidate['commit_close_outcome_addendum']['outcome_matrix'][:18] + (candidate['commit_close_outcome_addendum']['outcome_matrix'][18][:12] + ('A',) + candidate['commit_close_outcome_addendum']['outcome_matrix'][18][13:],) + candidate['commit_close_outcome_addendum']['outcome_matrix'][19:]",),
    "M21": ("candidate['commit_close_outcome_addendum']['outcome_matrix'] = candidate['commit_close_outcome_addendum']['outcome_matrix'][:21] + (candidate['commit_close_outcome_addendum']['outcome_matrix'][21][:4] + ('propagate close-time KeyboardInterrupt',) + candidate['commit_close_outcome_addendum']['outcome_matrix'][21][5:],) + candidate['commit_close_outcome_addendum']['outcome_matrix'][22:]",),
    "M22": ("candidate['commit_close_outcome_addendum']['outcome_matrix'] = candidate['commit_close_outcome_addendum']['outcome_matrix'][:3] + (candidate['commit_close_outcome_addendum']['outcome_matrix'][3][:6] + ('raise caught_exception',) + candidate['commit_close_outcome_addendum']['outcome_matrix'][3][7:],) + candidate['commit_close_outcome_addendum']['outcome_matrix'][4:]",),
    "M23": ("candidate['commit_close_outcome_addendum']['outcome_matrix'] = candidate['commit_close_outcome_addendum']['outcome_matrix'][:4] + (candidate['commit_close_outcome_addendum']['outcome_matrix'][4][:5] + ('reconstructed SystemExit with normalized code',) + candidate['commit_close_outcome_addendum']['outcome_matrix'][4][6:],) + candidate['commit_close_outcome_addendum']['outcome_matrix'][5:]",),
    "M24": ("candidate['commit_close_outcome_addendum']['outcome_matrix'] = candidate['commit_close_outcome_addendum']['outcome_matrix'][:6] + (candidate['commit_close_outcome_addendum']['outcome_matrix'][6][:20] + (True,) + candidate['commit_close_outcome_addendum']['outcome_matrix'][6][21:],) + candidate['commit_close_outcome_addendum']['outcome_matrix'][7:]",),
    "M25": ("candidate['commit_close_outcome_addendum']['outcome_matrix'] = candidate['commit_close_outcome_addendum']['outcome_matrix'][:7] + (candidate['commit_close_outcome_addendum']['outcome_matrix'][7][:13] + ('released before quarantine publication',) + candidate['commit_close_outcome_addendum']['outcome_matrix'][7][14:],) + candidate['commit_close_outcome_addendum']['outcome_matrix'][8:]",),
    "M26": ("candidate['commit_close_outcome_addendum']['explicit_disposal']['while_PU_or_PK'] = 'recreate connection and run SQL'",),
    "M27": ("candidate['commit_close_outcome_addendum']['finalizer']['weakref_finalize_invocation'] = 'repeatable'",),
    "M28": ("candidate['commit_close_outcome_addendum']['recovery_and_safe_command_custody']['complete_work_spec_reaches_recovery'] = True",),
    "M29": ("candidate['commit_close_outcome_addendum']['nonimplementation']['worker_scheduler_queue_service_model_or_reconciler'] = True",),
    "M30": ("candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['maximum_paths'] = 29",),
    "M31": ("candidate['commit_close_outcome_addendum']['matrix_identity_overlay']['same_exact_class_implies_same_object'] = True",),
    "M32": ("candidate['commit_close_outcome_addendum']['matrix_identity_overlay']['diagonal_discriminator'] = 'same exact class always selects same_instance'",),
    "M33": ("candidate['commit_close_outcome_addendum']['process_control_relational_policy']['same_instance']['selection'] = 'always distinct_instance'",),
    "M34": ("candidate['commit_close_outcome_addendum']['process_control_relational_policy']['distinct_prelinked']['exact_link_preservation_promised'] = True",),
    "M35": ("candidate['commit_close_outcome_addendum']['process_control_relational_policy']['exact_interpreter_preservation_guaranteed'] = True",),
    "M36": ("candidate['commit_close_outcome_addendum']['process_control_relational_policy']['exact_before_after_graph_reachability_cycle_or_traceback_promise'] = True",),
    "M37": ("candidate['commit_close_outcome_addendum']['process_control_relational_policy']['preexisting_relation_deliberately_removed'] = True",),
    "M38": ("candidate['commit_close_outcome_addendum']['process_control_relational_policy']['preexisting_private_payload']['universal_sanitization_claim'] = True",),
    "M39": ("candidate['commit_close_outcome_addendum']['process_control_relational_policy']['preexisting_private_payload']['copied_or_added_by_C2B3'] = True",),
    "M40": ("candidate['commit_close_outcome_addendum']['process_control_relational_policy']['raw_process_control']['serialize_persist_log_format_render_or_report'] = True",),
    "M41": ("candidate['commit_close_outcome_addendum']['post_close_cleanup_contract']['step_contracts']['L1']['proof'] = 'normal descriptor close return'",),
    "M42": ("candidate['commit_close_outcome_addendum']['post_close_cleanup_contract']['step_contracts']['T1']['preconditions'] = ('applicable C2', 'R1', 'R2', 'R3')",),
    "M43": ("candidate['commit_close_outcome_addendum']['post_close_cleanup_contract']['step_contracts']['H2']['preconditions'] = ('one H1 attempt',)",),
    "M44": ("candidate['commit_close_outcome_addendum']['post_close_cleanup_contract']['step_contracts']['H2']['same_process_acquisition'] = 'permitted while release_unproved'",),
    "M45": ("candidate['commit_close_outcome_addendum']['post_close_cleanup_contract']['recovery_replay_gate']['blocked_lock_facet'] = None",),
    "M46": ("candidate['commit_close_outcome_addendum']['post_close_cleanup_contract']['step_contracts']['L1']['release_unproved_forbids'] = ('descriptor close', 'X publication', 'new same-process writer')",),
    "M47": ("candidate['commit_close_outcome_addendum']['post_close_cleanup_contract']['step_contracts']['H1']['retry_numeric_fd'] = True",),
    "M48": ("candidate['commit_close_outcome_addendum']['post_close_cleanup_contract']['step_contracts']['H3']['precondition'] = 'PU or PK'",),
    "M49": ("candidate['commit_close_outcome_addendum']['orthogonal_cleanup_facets']['X_requires_descriptor_reclaimed'] = True",),
    "M50": ("candidate['commit_close_outcome_addendum']['finalizer']['failure_before_X_after_wrapper_loss']['retry_reachable'] = True",),
    "M51": ("candidate['commit_close_outcome_addendum']['finalizer']['hidden_cleanup_service_or_registry_scan'] = True",),
    "M52": ("candidate['commit_close_outcome_addendum']['outcome_matrix'] = candidate['commit_close_outcome_addendum']['outcome_matrix'][:6] + (candidate['commit_close_outcome_addendum']['outcome_matrix'][6][:12] + ('PU',) + candidate['commit_close_outcome_addendum']['outcome_matrix'][6][13:],) + candidate['commit_close_outcome_addendum']['outcome_matrix'][7:]",),
    "M53": ("candidate['commit_close_outcome_addendum']['outcome_matrix'] = candidate['commit_close_outcome_addendum']['outcome_matrix'][:12] + (candidate['commit_close_outcome_addendum']['outcome_matrix'][12][:12] + ('PK',) + candidate['commit_close_outcome_addendum']['outcome_matrix'][12][13:],) + candidate['commit_close_outcome_addendum']['outcome_matrix'][13:]",),
    "M54": ("candidate['commit_close_outcome_addendum']['post_close_cleanup_contract']['ordinary_A_to_X']['shared_lock_release_primitive'] = False",),
    "M55": ("candidate['commit_close_outcome_addendum']['finalizer']['automatic_retry'] = True",),
    "M56": ("candidate['commit_close_outcome_addendum']['finalizer']['failure_after_close_proof'] = 'clear every incomplete responsibility'",),
    "M57": ("candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['required_production_paths'] = candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['required_production_paths'][:5]",),
    "M58": ("candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['required_documentation_status_paths'] = candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['required_documentation_status_paths'][:7] + candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['required_documentation_status_paths'][8:]",),
    "M59": ("candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['required_changed_test_paths'] = candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['required_changed_test_paths'][:7] + candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['required_changed_test_paths'][8:]",),
    "M60": ("candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['required_changed_test_paths'] = candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['required_changed_test_paths'][:6] + candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['required_changed_test_paths'][7:]",),
    "M61": (
        "candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['expected_actual_write_paths'] = 23",
        "candidate['commit_close_outcome_addendum']['future_c2b3b_path_scope_status']['maximum_paths'] = 24",
    ),
    "M62": ("candidate['commit_close_outcome_addendum']['matrix_identity_overlay']['dynamic_generation'] = True",),
    "M63": ("candidate['commit_close_outcome_addendum']['nonimplementation']['production_behavior'] = True",),
    "M64": ("candidate['commit_close_outcome_addendum']['post_close_cleanup_contract']['step_contracts']['H2']['under_lifecycle_fork_gate_order'] = ('identity-check and remove exact _ACTIVE_LOCK_RESOURCES entry', 'publish release-proved terminal facts and descriptor outcome')",),
    "M65": ("candidate['commit_close_outcome_addendum']['post_close_cleanup_contract']['step_contracts']['P0']['new_operation_admission_in_PU_or_PK'] = True",),
}
C2B3A_ORACLE_LEGAL_LOAD_SITE_FIELDS = (
    "protected_name",
    "enclosing_top_level_function",
    "enclosing_nested_function",
    "load_role",
    "ancestor_kind_chain",
    "ordinal",
)
C2B3A_ORACLE_LEGAL_PROTECTED_LOAD_SITES: tuple[tuple[object, ...], ...] = (('_read_allowed_text', '_owner_contract', None, 'direct_call_func', ('Name', 'Call', 'IfExp', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_read_allowed_text', '_owner_golden_vector', None, 'direct_call_func', ('Name', 'Call', 'IfExp', 'Assign', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_INITIALIZATION_GOLDEN_VECTOR', '_validate_golden_vector', None, 'direct_comparison_operand', ('Name', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_PLANNING_PROJECTION', '_validate_planning_status', None, 'direct_comparison_operand', ('Name', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_candidate_argument', ('Name', 'Call', 'BinOp', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 6),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 7),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 8),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 9),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 10),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 11),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 12),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 13),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 14),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 15),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 16),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 17),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 18),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 19),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 20),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 21),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 22),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 23),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 24),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 25),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 26),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Subscript', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 27),
 ('EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM', '_validate_contract', None, 'direct_comparison_operand', ('Name', 'Compare', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_candidate', None, 'direct_candidate_argument', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM', '_candidate', None, 'direct_candidate_argument', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_INITIALIZATION_GOLDEN_VECTOR', '_golden_candidate', None, 'direct_candidate_argument', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_exception_graph_identity_walk', '_relational_process_control_reference', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_exception_graph_identity_walk', '_relational_process_control_reference', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_exception_graph_identity_walk', '_relational_process_control_reference', None, 'direct_call_func',
  ('Name', 'Call', 'Dict', 'Return', 'ExceptHandler', 'Try', 'FunctionDef', 'Module'), 2),
 ('_cleanup_reference_result', '_cleanup_reference', None, 'direct_call_func', ('Name', 'Call', 'Subscript', 'Return', 'FunctionDef', 'Module'), 0),
 ('_validate_contract', '_expect_violation', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 0),
 ('_validate_golden_vector', '_expect_golden_violation', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_PLANNING_PROJECTION', '_assert_oracle_architecture', None, 'direct_candidate_argument', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_INITIALIZATION_CONTRACT', '_assert_oracle_architecture', None, 'direct_candidate_argument', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_INITIALIZATION_GOLDEN_VECTOR', '_assert_oracle_architecture', None, 'direct_candidate_argument', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM', '_assert_oracle_architecture', None, 'direct_candidate_argument', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_PROCESS_CONTROL_REFERENCE_CASES', '_assert_oracle_architecture', None, 'direct_candidate_argument', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('CLEANUP_SAFE_PROJECTION_FIELDS', '_assert_oracle_architecture', None, 'direct_candidate_argument', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('CLEANUP_REFERENCE_INPUT_CASES', '_assert_oracle_architecture', None, 'direct_candidate_argument', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_CLEANUP_REFERENCE_CASES', '_assert_oracle_architecture', None, 'direct_candidate_argument', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_owner_contract', 'test_owner_literal_equals_independent_expected_contract', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('owner_contract_candidate', 'test_owner_literal_equals_independent_expected_contract', None, 'direct_comparison_operand', ('Name', 'Compare', 'Assert', 'FunctionDef', 'Module'),
  0),
 ('_candidate', 'test_owner_literal_equals_independent_expected_contract', None, 'direct_call_func', ('Name', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 0),
 ('owner_contract_candidate', 'test_owner_literal_equals_independent_expected_contract', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_owner_literal_equals_independent_expected_contract', None, 'direct_call_func', ('Name', 'Call', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 1),
 ('owner_contract_candidate', 'test_owner_literal_equals_independent_expected_contract', None, 'direct_comparison_operand',
  ('Name', 'Subscript', 'Compare', 'Assert', 'FunctionDef', 'Module'), 2),
 ('EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM', 'test_owner_literal_equals_independent_expected_contract', None, 'direct_comparison_operand',
  ('Name', 'Compare', 'Assert', 'FunctionDef', 'Module'), 0),
 ('_validate_contract', 'test_owner_literal_equals_independent_expected_contract', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('owner_contract_candidate', 'test_owner_literal_equals_independent_expected_contract', None, 'direct_candidate_argument', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_owner_golden_vector', 'test_owner_golden_vector_equals_independent_direct_literal', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('owner_golden_vector_candidate', 'test_owner_golden_vector_equals_independent_direct_literal', None, 'direct_comparison_operand',
  ('Name', 'Compare', 'Assert', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_INITIALIZATION_GOLDEN_VECTOR', 'test_owner_golden_vector_equals_independent_direct_literal', None, 'direct_comparison_operand',
  ('Name', 'Compare', 'Assert', 'FunctionDef', 'Module'), 0),
 ('owner_golden_vector_candidate', 'test_owner_golden_vector_equals_independent_direct_literal', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 1),
 ('EXPECTED_INITIALIZATION_GOLDEN_VECTOR', 'test_owner_golden_vector_equals_independent_direct_literal', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 1),
 ('owner_golden_vector_candidate', 'test_owner_golden_vector_equals_independent_direct_literal', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('EXPECTED_INITIALIZATION_GOLDEN_VECTOR', 'test_owner_golden_vector_equals_independent_direct_literal', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_read_allowed_text', 'test_owner_golden_vector_equals_independent_direct_literal', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_read_allowed_text', 'test_owner_golden_vector_equals_independent_direct_literal', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_validate_golden_vector', 'test_owner_golden_vector_equals_independent_direct_literal', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('owner_golden_vector_candidate', 'test_owner_golden_vector_equals_independent_direct_literal', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('EXPECTED_INITIALIZATION_GOLDEN_VECTOR', 'test_golden_vector_is_complete_privacy_safe_single_work_ledger', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_golden_candidate', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'),
  0),
 ('_expect_golden_violation', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_golden_candidate', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'),
  1),
 ('_expect_golden_violation', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_golden_candidate', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'),
  2),
 ('_expect_golden_violation', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_golden_candidate', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'),
  3),
 ('_expect_golden_violation', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_golden_candidate', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'),
  4),
 ('_expect_golden_violation', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_golden_candidate', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'),
  5),
 ('_expect_golden_violation', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('_golden_candidate', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'),
  6),
 ('_expect_golden_violation', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 6),
 ('_golden_candidate', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'),
  7),
 ('_expect_golden_violation', 'test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 7),
 ('_read_allowed_text', 'test_golden_vector_parser_rejects_marker_fence_and_literal_bypasses', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_owner_golden_vector', 'test_golden_vector_parser_rejects_marker_fence_and_literal_bypasses', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 0),
 ('_owner_golden_vector', 'test_golden_vector_parser_rejects_marker_fence_and_literal_bypasses', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 1),
 ('_owner_golden_vector', 'test_golden_vector_parser_rejects_marker_fence_and_literal_bypasses', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 2),
 ('_owner_golden_vector', 'test_golden_vector_parser_rejects_marker_fence_and_literal_bypasses', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 3),
 ('_read_allowed_text', 'test_expected_contract_is_one_direct_literal_with_bounded_oracle_inputs', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'),
  0),
 ('_assert_oracle_architecture', 'test_expected_contract_is_one_direct_literal_with_bounded_oracle_inputs', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_read_allowed_text', 'test_oracle_architecture_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_assert_oracle_architecture', 'test_oracle_architecture_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 0),
 ('_assert_oracle_architecture', 'test_oracle_architecture_counterfactuals_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'For', 'FunctionDef', 'Module'), 1),
 ('_assert_oracle_architecture', 'test_oracle_architecture_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 2),
 ('_assert_oracle_architecture', 'test_oracle_architecture_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 3),
 ('_assert_oracle_architecture', 'test_oracle_architecture_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 4),
 ('_assert_oracle_architecture', 'test_oracle_architecture_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 5),
 ('_read_allowed_text', 'test_owner_literal_parser_rejects_marker_fence_and_literal_bypasses', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_owner_contract', 'test_owner_literal_parser_rejects_marker_fence_and_literal_bypasses', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 0),
 ('_owner_contract', 'test_owner_literal_parser_rejects_marker_fence_and_literal_bypasses', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 1),
 ('_owner_contract', 'test_owner_literal_parser_rejects_marker_fence_and_literal_bypasses', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 2),
 ('_owner_contract', 'test_owner_literal_parser_rejects_marker_fence_and_literal_bypasses', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 3),
 ('_read_allowed_text', 'test_planning_status_baseline_is_exact_closed_projection', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('planning_document_candidate', 'test_planning_status_baseline_is_exact_closed_projection', None, 'direct_comparison_operand',
  ('Name', 'Compare', 'Assert', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_PLANNING_PROJECTION', 'test_planning_status_baseline_is_exact_closed_projection', None, 'direct_comparison_operand',
  ('Name', 'Compare', 'Assert', 'FunctionDef', 'Module'), 0),
 ('planning_document_candidate', 'test_planning_status_baseline_is_exact_closed_projection', None, None,
  ('Name', 'Attribute', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 1),
 ('planning_document_candidate', 'test_planning_status_baseline_is_exact_closed_projection', None, None,
  ('Name', 'Attribute', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 2),
 ('planning_document_candidate', 'test_planning_status_baseline_is_exact_closed_projection', None, None, ('Name', 'Attribute', 'Call', 'Assert', 'FunctionDef', 'Module'), 3),
 ('_validate_planning_status', 'test_planning_status_baseline_is_exact_closed_projection', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('planning_document_candidate', 'test_planning_status_baseline_is_exact_closed_projection', None, 'direct_candidate_argument', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'),
  4),
 ('_read_allowed_text', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None,
  ('Name', 'Attribute', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None, ('Name', 'BinOp', 'Tuple', 'For', 'FunctionDef', 'Module'), 1),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None, ('Name', 'BinOp', 'Tuple', 'For', 'FunctionDef', 'Module'), 2),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None,
  ('Name', 'Attribute', 'Call', 'Tuple', 'For', 'FunctionDef', 'Module'), 3),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None,
  ('Name', 'Attribute', 'Call', 'Tuple', 'For', 'FunctionDef', 'Module'), 4),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None,
  ('Name', 'Attribute', 'Call', 'Tuple', 'For', 'FunctionDef', 'Module'), 5),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None,
  ('Name', 'Attribute', 'Call', 'Tuple', 'For', 'FunctionDef', 'Module'), 6),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None,
  ('Name', 'Attribute', 'Call', 'Tuple', 'For', 'FunctionDef', 'Module'), 7),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None,
  ('Name', 'Attribute', 'Call', 'Tuple', 'For', 'FunctionDef', 'Module'), 8),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None, ('Name', 'BinOp', 'Tuple', 'For', 'FunctionDef', 'Module'), 9),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None, ('Name', 'BinOp', 'Tuple', 'For', 'FunctionDef', 'Module'),
  10),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None, ('Name', 'BinOp', 'Tuple', 'For', 'FunctionDef', 'Module'),
  11),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None, ('Name', 'BinOp', 'Tuple', 'For', 'FunctionDef', 'Module'),
  12),
 ('_validate_planning_status', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'For', 'FunctionDef', 'Module'), 0),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, None,
  ('Name', 'Attribute', 'Call', 'Assign', 'For', 'FunctionDef', 'Module'), 13),
 ('planning_document_candidate', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, 'direct_comparison_operand',
  ('Name', 'Compare', 'Assert', 'For', 'FunctionDef', 'Module'), 14),
 ('_validate_planning_status', 'test_planning_projection_closed_grammar_counterfactuals_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'For', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_owner_and_five_path_scope_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_owner_and_five_path_scope_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_owner_and_five_path_scope_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_owner_and_five_path_scope_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_owner_and_five_path_scope_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_owner_and_five_path_scope_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_owner_and_five_path_scope_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_expect_violation', 'test_owner_and_five_path_scope_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_owner_and_five_path_scope_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_expect_violation', 'test_owner_and_five_path_scope_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_owner_and_five_path_scope_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_expect_violation', 'test_owner_and_five_path_scope_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_expect_violation', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_expect_violation', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_expect_violation', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 6),
 ('_expect_violation', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 6),
 ('_candidate', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 7),
 ('_expect_violation', 'test_genesis_cardinality_and_selection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 7),
 ('_candidate', 'test_genesis_decision_selected_and_preassigned_algebra_is_closed', None, 'direct_call_func',
  ('Name', 'Call', 'Subscript', 'Subscript', 'Subscript', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_genesis_decision_selected_and_preassigned_algebra_is_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'For', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_genesis_decision_selected_and_preassigned_algebra_is_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'For', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_genesis_decision_selected_and_preassigned_algebra_is_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_genesis_decision_selected_and_preassigned_algebra_is_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_expect_violation', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_expect_violation', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_expect_violation', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 6),
 ('_expect_violation', 'test_accepted_intent_projection_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 6),
 ('_candidate', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_expect_violation', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_expect_violation', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_expect_violation', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 6),
 ('_expect_violation', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 6),
 ('_candidate', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 7),
 ('_expect_violation', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 7),
 ('_candidate', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 8),
 ('_expect_violation', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 8),
 ('_candidate', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 9),
 ('_expect_violation', 'test_safe_command_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 9),
 ('_candidate', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_expect_violation', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_expect_violation', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_expect_violation', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 6),
 ('_expect_violation', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 6),
 ('_candidate', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 7),
 ('_expect_violation', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 7),
 ('_candidate', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 8),
 ('_expect_violation', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 8),
 ('_candidate', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 9),
 ('_expect_violation', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 9),
 ('_candidate', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 10),
 ('_expect_violation', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 10),
 ('_candidate', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 11),
 ('_expect_violation', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 11),
 ('_candidate', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 12),
 ('_expect_violation', 'test_row_write_and_graph_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 12),
 ('_candidate', 'test_locator_result_receipt_and_existing_projection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_locator_result_receipt_and_existing_projection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_locator_result_receipt_and_existing_projection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_locator_result_receipt_and_existing_projection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_locator_result_receipt_and_existing_projection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_locator_result_receipt_and_existing_projection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_locator_result_receipt_and_existing_projection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_expect_violation', 'test_locator_result_receipt_and_existing_projection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_locator_result_receipt_and_existing_projection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_expect_violation', 'test_locator_result_receipt_and_existing_projection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_locator_result_receipt_and_existing_projection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_expect_violation', 'test_locator_result_receipt_and_existing_projection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_work_spec_locator_exact_ref_relation_and_selection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_work_spec_locator_exact_ref_relation_and_selection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_work_spec_locator_exact_ref_relation_and_selection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_work_spec_locator_exact_ref_relation_and_selection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_work_spec_locator_exact_ref_relation_and_selection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_work_spec_locator_exact_ref_relation_and_selection_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_replay_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_replay_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_replay_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_replay_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_replay_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_replay_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_replay_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_expect_violation', 'test_replay_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_replay_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_expect_violation', 'test_replay_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_expect_violation', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_expect_violation', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_expect_violation', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 6),
 ('_expect_violation', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 6),
 ('_candidate', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 7),
 ('_expect_violation', 'test_commit_recovery_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 7),
 ('_assert_preassigned_binding', 'test_preassigned_attempt_candidate_binding_is_exact_and_cross_related', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_INITIALIZATION_CONTRACT', 'test_preassigned_attempt_candidate_binding_is_exact_and_cross_related', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_INITIALIZATION_GOLDEN_VECTOR', 'test_preassigned_attempt_candidate_binding_is_exact_and_cross_related', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_owner_contract', 'test_preassigned_attempt_candidate_binding_is_exact_and_cross_related', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_assert_preassigned_binding', 'test_preassigned_attempt_candidate_binding_is_exact_and_cross_related', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('owner_contract_candidate', 'test_preassigned_attempt_candidate_binding_is_exact_and_cross_related', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_INITIALIZATION_GOLDEN_VECTOR', 'test_preassigned_attempt_candidate_binding_is_exact_and_cross_related', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_assert_preassigned_binding', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 0),
 ('_golden_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'),
  0),
 ('_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_assert_preassigned_binding', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 1),
 ('_golden_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'),
  1),
 ('_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_assert_preassigned_binding', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 2),
 ('_golden_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'),
  2),
 ('_golden_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_assert_preassigned_binding', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 3),
 ('_golden_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_assert_preassigned_binding', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 4),
 ('_golden_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_assert_preassigned_binding', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 5),
 ('_golden_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 6),
 ('_assert_preassigned_binding', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 6),
 ('_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 6),
 ('_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 7),
 ('_assert_preassigned_binding', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 7),
 ('_golden_candidate', 'test_preassigned_binding_mutants_b01_through_b08_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'),
  7),
 ('_assert_original_apply_outcome', 'test_original_apply_outcome_and_quarantine_branch_are_exact', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_INITIALIZATION_CONTRACT', 'test_original_apply_outcome_and_quarantine_branch_are_exact', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_assert_original_apply_outcome', 'test_original_apply_outcome_and_quarantine_branch_are_exact', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_owner_contract', 'test_original_apply_outcome_and_quarantine_branch_are_exact', None, 'direct_call_func', ('Name', 'Call', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_original_apply_outcome_mutants_u09_through_u14_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_assert_original_apply_outcome', 'test_original_apply_outcome_mutants_u09_through_u14_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_original_apply_outcome_mutants_u09_through_u14_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_assert_original_apply_outcome', 'test_original_apply_outcome_mutants_u09_through_u14_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_original_apply_outcome_mutants_u09_through_u14_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_assert_original_apply_outcome', 'test_original_apply_outcome_mutants_u09_through_u14_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_original_apply_outcome_mutants_u09_through_u14_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_assert_original_apply_outcome', 'test_original_apply_outcome_mutants_u09_through_u14_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_original_apply_outcome_mutants_u09_through_u14_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_assert_original_apply_outcome', 'test_original_apply_outcome_mutants_u09_through_u14_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_original_apply_outcome_mutants_u09_through_u14_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_assert_original_apply_outcome', 'test_original_apply_outcome_mutants_u09_through_u14_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_process_control_close_interruption_contract_is_exact', None, 'direct_call_func',
  ('Name', 'Call', 'Subscript', 'Subscript', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_process_control_exception_graph_ledger_is_exact', None, 'direct_call_func', ('Name', 'Call', 'Subscript', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_bare_reraise_reference', 'test_bare_reraise_reference_model_distinguishes_named_reraise', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_named_reraise_reference', 'test_bare_reraise_reference_model_distinguishes_named_reraise', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_bare_reraise_reference', 'test_keyboard_interrupt_close_fault_publishes_before_identical_propagation', None, 'direct_call_func',
  ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_bare_reraise_reference', 'test_system_exit_close_fault_publishes_before_identical_propagation', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'),
  0),
 ('_bare_reraise_reference', 'test_generator_exit_close_fault_publishes_before_identical_propagation', None, 'direct_call_func',
  ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_assert_future_c2b3b_scope', 'test_future_c2b3b_twenty_four_path_scope_is_exact', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_INITIALIZATION_CONTRACT', 'test_future_c2b3b_twenty_four_path_scope_is_exact', None, 'direct_candidate_argument', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_assert_future_c2b3b_scope', 'test_future_c2b3b_twenty_four_path_scope_is_exact', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_owner_contract', 'test_future_c2b3b_twenty_four_path_scope_is_exact', None, 'direct_call_func', ('Name', 'Call', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_future_c2b3b_scope_mutants_s01_through_s07_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'For', 'FunctionDef', 'Module'), 0),
 ('_assert_future_c2b3b_scope', 'test_future_c2b3b_scope_mutants_s01_through_s07_are_rejected', None, 'direct_call_func',
  ('Name', 'Call', 'Expr', 'With', 'For', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_future_c2b3b_scope_mutants_s01_through_s07_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_assert_future_c2b3b_scope', 'test_future_c2b3b_scope_mutants_s01_through_s07_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'),
  1),
 ('_candidate', 'test_future_c2b3b_scope_mutants_s01_through_s07_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_assert_future_c2b3b_scope', 'test_future_c2b3b_scope_mutants_s01_through_s07_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'),
  2),
 ('_candidate', 'test_future_c2b3b_scope_mutants_s01_through_s07_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_assert_future_c2b3b_scope', 'test_future_c2b3b_scope_mutants_s01_through_s07_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'),
  3),
 ('_candidate', 'test_future_c2b3b_scope_mutants_s01_through_s07_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_assert_future_c2b3b_scope', 'test_future_c2b3b_scope_mutants_s01_through_s07_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'With', 'FunctionDef', 'Module'),
  4),
 ('_candidate', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_expect_violation', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_expect_violation', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_expect_violation', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 6),
 ('_expect_violation', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 6),
 ('_candidate', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 7),
 ('_expect_violation', 'test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 7),
 ('_candidate', 'test_stop_conflict_and_receipt_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_stop_conflict_and_receipt_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_stop_conflict_and_receipt_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_stop_conflict_and_receipt_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_stop_conflict_and_receipt_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_stop_conflict_and_receipt_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_stop_conflict_and_receipt_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_expect_violation', 'test_stop_conflict_and_receipt_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_stop_conflict_and_receipt_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_expect_violation', 'test_stop_conflict_and_receipt_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_stop_conflict_and_receipt_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_expect_violation', 'test_stop_conflict_and_receipt_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_expect_violation', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_expect_violation', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_expect_violation', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 6),
 ('_expect_violation', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 6),
 ('_candidate', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 7),
 ('_expect_violation', 'test_private_conflict_and_recovery_outcome_owners_are_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 7),
 ('_candidate', 'test_privacy_and_custody_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_privacy_and_custody_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_privacy_and_custody_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_privacy_and_custody_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_privacy_and_custody_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'For', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_privacy_and_custody_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'For', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_privacy_and_custody_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'For', 'FunctionDef', 'Module'), 3),
 ('_expect_violation', 'test_privacy_and_custody_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'For', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_privacy_and_custody_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_expect_violation', 'test_privacy_and_custody_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_privacy_and_custody_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_expect_violation', 'test_privacy_and_custody_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_later_author_effect_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_later_author_effect_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 0),
 ('_candidate', 'test_later_author_effect_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 1),
 ('_expect_violation', 'test_later_author_effect_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 1),
 ('_candidate', 'test_later_author_effect_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 2),
 ('_expect_violation', 'test_later_author_effect_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 2),
 ('_candidate', 'test_later_author_effect_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 3),
 ('_expect_violation', 'test_later_author_effect_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 3),
 ('_candidate', 'test_later_author_effect_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 4),
 ('_expect_violation', 'test_later_author_effect_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 4),
 ('_candidate', 'test_later_author_effect_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 5),
 ('_expect_violation', 'test_later_author_effect_counterfactuals_are_rejected', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'FunctionDef', 'Module'), 5),
 ('_candidate', 'test_nonimplementation_surface_is_closed', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'For', 'FunctionDef', 'Module'), 0),
 ('_expect_violation', 'test_nonimplementation_surface_is_closed', None, 'direct_call_func', ('Name', 'Call', 'Expr', 'For', 'FunctionDef', 'Module'), 0),
 ('_owner_contract', 'test_commit_close_addendum_direct_oracle_matrix_is_closed', None, 'direct_call_func', ('Name', 'Call', 'Subscript', 'Assign', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM', 'test_commit_close_addendum_direct_oracle_matrix_is_closed', None, 'direct_comparison_operand',
  ('Name', 'Compare', 'Assert', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM', 'test_commit_close_addendum_custody_recovery_and_scope_are_exact', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_PROCESS_CONTROL_REFERENCE_CASES', 'test_process_control_reference_case_fixture_is_closed_and_privacy_safe', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 0),
 ('_exception_graph_identity_walk', 'test_process_control_reference_case_fixture_is_closed_and_privacy_safe', None, 'direct_call_func',
  ('Name', 'Call', 'Assign', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_PROCESS_CONTROL_REFERENCE_CASES', 'test_commit_close_relational_process_control_reference_cases_are_exact', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 0),
 ('_relational_process_control_reference', 'test_commit_close_relational_process_control_reference_cases_are_exact', None, 'direct_call_func',
  ('Name', 'Call', 'Assign', 'For', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_PROCESS_CONTROL_REFERENCE_CASES', 'test_commit_close_relational_process_control_reference_cases_are_exact', None, None,
  ('Name', 'Subscript', 'Assign', 'For', 'FunctionDef', 'Module'), 1),
 ('CLEANUP_REFERENCE_INPUT_CASES', 'test_cleanup_reference_vector_shape_is_exact', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_CLEANUP_REFERENCE_CASES', 'test_cleanup_reference_vector_shape_is_exact', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 0),
 ('CLEANUP_REFERENCE_INPUT_CASES', 'test_cleanup_reference_vector_shape_is_exact', None, None,
  ('Name', 'comprehension', 'GeneratorExp', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 1),
 ('EXPECTED_CLEANUP_REFERENCE_CASES', 'test_cleanup_reference_vector_shape_is_exact', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 1),
 ('EXPECTED_CLEANUP_REFERENCE_CASES', 'test_cleanup_reference_vector_shape_is_exact', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 2),
 ('CLEANUP_SAFE_PROJECTION_FIELDS', 'test_cleanup_reference_vector_shape_is_exact', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 0),
 ('CLEANUP_REFERENCE_INPUT_CASES', 'test_post_close_cleanup_reference_model_covers_every_release_point', None, None, ('Name', 'Assign', 'FunctionDef', 'Module'), 0),
 ('EXPECTED_CLEANUP_REFERENCE_CASES', 'test_post_close_cleanup_reference_model_covers_every_release_point', None, 'direct_candidate_argument',
  ('Name', 'Call', 'Compare', 'Assert', 'FunctionDef', 'Module'), 0),
 ('_cleanup_reference', 'test_post_close_cleanup_reference_model_covers_every_release_point', None, 'direct_call_func', ('Name', 'Call', 'Assign', 'For', 'FunctionDef', 'Module'),
  0),
 ('EXPECTED_CLEANUP_REFERENCE_CASES', 'test_post_close_cleanup_reference_model_covers_every_release_point', None, None,
  ('Name', 'Subscript', 'Assign', 'For', 'FunctionDef', 'Module'), 1))
C2B3A_ORACLE_EXPECTED_TEST_NODE_NAMES: tuple[str, ...] = (
    "test_owner_literal_equals_independent_expected_contract",
    "test_owner_golden_vector_equals_independent_direct_literal",
    "test_golden_vector_is_complete_privacy_safe_single_work_ledger",
    "test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected",
    "test_golden_vector_parser_rejects_marker_fence_and_literal_bypasses",
    "test_expected_contract_is_one_direct_literal_with_bounded_oracle_inputs",
    "test_oracle_architecture_counterfactuals_are_rejected",
    "test_owner_literal_parser_rejects_marker_fence_and_literal_bypasses",
    "test_planning_status_baseline_is_exact_closed_projection",
    "test_planning_projection_closed_grammar_counterfactuals_are_rejected",
    "test_owner_and_five_path_scope_counterfactuals_are_rejected",
    "test_genesis_cardinality_and_selection_counterfactuals_are_rejected",
    "test_genesis_decision_selected_and_preassigned_algebra_is_closed",
    "test_accepted_intent_projection_counterfactuals_are_rejected",
    "test_safe_command_counterfactuals_are_rejected",
    "test_row_write_and_graph_counterfactuals_are_rejected",
    "test_locator_result_receipt_and_existing_projection_are_closed",
    "test_work_spec_locator_exact_ref_relation_and_selection_are_closed",
    "test_replay_counterfactuals_are_rejected",
    "test_commit_recovery_counterfactuals_are_rejected",
    "test_preassigned_attempt_candidate_binding_is_exact_and_cross_related",
    "test_preassigned_binding_mutants_b01_through_b08_are_rejected",
    "test_original_apply_outcome_and_quarantine_branch_are_exact",
    "test_original_apply_outcome_mutants_u09_through_u14_are_rejected",
    "test_process_control_close_interruption_contract_is_exact",
    "test_process_control_exception_graph_ledger_is_exact",
    "test_bare_reraise_reference_model_distinguishes_named_reraise",
    "test_keyboard_interrupt_close_fault_publishes_before_identical_propagation",
    "test_system_exit_close_fault_publishes_before_identical_propagation",
    "test_generator_exit_close_fault_publishes_before_identical_propagation",
    "test_future_c2b3b_twenty_four_path_scope_is_exact",
    "test_future_c2b3b_scope_mutants_s01_through_s07_are_rejected",
    "test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected",
    "test_stop_conflict_and_receipt_counterfactuals_are_rejected",
    "test_private_conflict_and_recovery_outcome_owners_are_closed",
    "test_privacy_and_custody_counterfactuals_are_rejected",
    "test_later_author_effect_counterfactuals_are_rejected",
    "test_nonimplementation_surface_is_closed",
    "test_commit_close_addendum_direct_oracle_matrix_is_closed",
    "test_commit_close_addendum_custody_recovery_and_scope_are_exact",
    "test_process_control_reference_case_fixture_is_closed_and_privacy_safe",
    "test_commit_close_relational_process_control_reference_cases_are_exact",
    "test_cleanup_reference_vector_shape_is_exact",
    "test_post_close_cleanup_reference_model_covers_every_release_point",
    "test_commit_close_mutant_m16_missing_matrix_row_is_rejected",
    "test_commit_close_mutant_m17_duplicate_matrix_row_is_rejected",
    "test_commit_close_mutant_m18_reordered_matrix_rows_is_rejected",
    "test_commit_close_mutant_m19_c1k2_state_is_rejected",
    "test_commit_close_mutant_m20_c4k1_state_is_rejected",
    "test_commit_close_mutant_m21_cleanup_primary_precedence_is_rejected",
    "test_commit_close_mutant_m22_named_raise_is_rejected",
    "test_commit_close_mutant_m23_reconstructed_system_exit_is_rejected",
    "test_commit_close_mutant_m24_post_commit_rollback_is_rejected",
    "test_commit_close_mutant_m25_slot_release_before_quarantine_is_rejected",
    "test_commit_close_mutant_m26_pending_cleanup_sql_is_rejected",
    "test_commit_close_mutant_m27_finalizer_retry_is_rejected",
    "test_commit_close_mutant_m28_work_spec_recovery_custody_is_rejected",
    "test_commit_close_mutant_m29_production_behavior_is_rejected",
    "test_commit_close_mutant_m30_scope_maximum_is_rejected",
    "test_commit_close_mutant_m31_same_class_implies_same_object_is_rejected",
    "test_commit_close_mutant_m32_distinct_same_class_routing_is_rejected",
    "test_commit_close_mutant_m33_same_instance_routing_is_rejected",
    "test_commit_close_mutant_m34_prelinked_cause_promise_is_rejected",
    "test_commit_close_mutant_m35_prelinked_context_promise_is_rejected",
    "test_commit_close_mutant_m36_fixed_graph_shape_is_rejected",
    "test_commit_close_mutant_m37_graph_scrub_is_rejected",
    "test_commit_close_mutant_m38_universal_sanitization_is_rejected",
    "test_commit_close_mutant_m39_raw_payload_copy_is_rejected",
    "test_commit_close_mutant_m40_raw_payload_report_is_rejected",
    "test_commit_close_mutant_m41_descriptor_close_release_proof_is_rejected",
    "test_commit_close_mutant_m42_x_before_release_proof_is_rejected",
    "test_commit_close_mutant_m43_authority_registry_before_release_is_rejected",
    "test_commit_close_mutant_m44_acquisition_on_unproved_release_is_rejected",
    "test_commit_close_mutant_m45_recovery_on_unproved_release_is_rejected",
    "test_commit_close_mutant_m46_replay_on_unproved_release_is_rejected",
    "test_commit_close_mutant_m47_descriptor_close_retry_is_rejected",
    "test_commit_close_mutant_m48_session_registry_before_x_is_rejected",
    "test_commit_close_mutant_m49_descriptor_reclamation_x_gate_is_rejected",
    "test_commit_close_mutant_m50_retry_after_wrapper_loss_is_rejected",
    "test_commit_close_mutant_m51_hidden_registry_cleanup_is_rejected",
    "test_commit_close_mutant_m52_c2k1_pending_state_is_rejected",
    "test_commit_close_mutant_m53_c3k1_pending_state_is_rejected",
    "test_commit_close_mutant_m54_a_to_x_lock_bypass_is_rejected",
    "test_commit_close_mutant_m55_finalizer_automatic_retry_is_rejected",
    "test_commit_close_mutant_m56_finalizer_clears_progress_is_rejected",
    "test_commit_close_mutant_m57_missing_lock_source_path_is_rejected",
    "test_commit_close_mutant_m58_missing_writer_authority_doc_is_rejected",
    "test_commit_close_mutant_m59_missing_lock_test_is_rejected",
    "test_commit_close_mutant_m60_missing_writer_session_test_is_rejected",
    "test_commit_close_mutant_m61_historical_scope_reactivation_is_rejected",
    "test_commit_close_mutant_m62_dynamic_oracle_derivation_is_rejected",
    "test_commit_close_mutant_m63_implementation_claim_is_rejected",
    "test_commit_close_mutant_m64_h2_order_is_rejected",
    "test_commit_close_mutant_m65_new_operation_in_pending_state_is_rejected",
)
SECTION_HEADINGS = (
    "1. Status, Classification, And Layering",
    "2. One Database, One Writer, And Fact Ownership",
    "3. Identity Non-Collapse",
    "4. Hybrid Durable Representation",
    "5. Program Genesis",
    "6. Exact Decision-Kind Inventory",
    "7. Distinct Cancel Decision",
    "8. Decision-To-Effect Basis",
    "9. Originating Author-Command Cardinality",
    "10. Author-Effect Establishment",
    "11. Bound-Effect Establishment",
    "12. Complete Target Mutation Families",
    "13. Source Invocation, Observation, And Ingest",
    "14. Unknown Outcome And Redelivery",
    "15. Coding Global-Stop Matrix",
    "16. Private WorkSpec Custody",
    "17. C2A Value Persistence Matrix",
    "18. Authority Evaluation",
    "19. First-Slice One-Shot Latch",
    "20. Migration-Framework Strategy",
    "21. Migration 0002",
    "22. Migration 0003",
    "23. Exact Schema Totals",
    "24. Exact Explicit Indexes",
    "25. Transaction And Replay Algebra",
    "26. Exact Target Tranche Sequence",
    "27. Explicit Nonimplementation",
    "28. C2B2 Field-Level Freeze Classification",
    "29. C2B2 Field-Level Structured Contract Ledger",
    "30. Receipt Scalar Result And Persisted Graph Coherence",
    "31. Common Mutation-Graph Digest Primitive",
    "32. C2B2 Private Reader Boundary",
    "33. Family Replay Deferral And Tranche Ownership",
    "34. C2B2 Remaining Nonimplementation",
    "35. C2B3A Program-Initialization Contract Freeze",
    "36. C2B3 Vertical-Slice Governing Narrowing Addendum",
    "37. C2B Pre-I/O VS1A Shared Cleanup Foundation",
)

DECISION_KINDS = (
    "initialize",
    "accept",
    "repair",
    "replan",
    "terminal_reject",
    "block",
    "redeliver",
    "cancel",
)

DECISION_VERSION_EFFECTS = (
    "initialize: creates version 1",
    "accept: appends an accepted program version",
    "repair: appends a program version and preassigns a successor attempt/candidate",
    "replan: appends accepted-intent/work revision and program-version state",
    "terminal_reject: appends a terminal-rejected version",
    "block: appends a blocked version",
    "redeliver: no program-version advance",
    "cancel: no program-version advance",
)

MUTABLE_HEADS = (
    "development_program_heads",
    "development_work_item_heads",
    "development_effect_heads",
    "development_delivery_heads",
    "development_observation_ref_heads",
    "development_first_slice_latch",
)

TABLES_0002 = (
    "development_program_heads",
    "development_program_versions",
    "development_accepted_intent_revisions",
    "development_work_item_heads",
    "development_work_item_revisions",
    "development_program_version_work_items",
    "development_revision_edges",
    "development_work_spec_bindings",
    "development_semantic_attempts",
    "development_attempt_fences",
    "development_authority_evaluations",
    "development_effect_intents",
    "development_effect_fences",
    "development_author_commands",
    "development_effect_heads",
    "development_delivery_attempts",
    "development_delivery_heads",
    "development_decisions",
    "development_mutation_receipts",
)

_C2B_MIGRATION_LITERAL_ALLOWLIST = frozenset(
    (
        "EXPECTED_TABLES",
        "Constant",
        table_name,
        "schema introspection and verification",
    )
    for table_name in TABLES_0002
) | frozenset(
    (
        "_EMPTY_AFTER_C2B2_MIGRATION_TABLES",
        "Constant",
        table_name,
        "sequence-scoped migration-completion zero-seed checks",
    )
    for table_name in TABLES_0002
) | frozenset(
    {
        (
            "_C2B2_MIGRATION_ID",
            "Constant",
            "0002_development_program_and_effect_state",
            "literal migration catalog/resource metadata",
        ),
        (
            "_PACKAGED_MIGRATION_SPECS",
            "Constant",
            "0002_development_program_and_effect_state.sql",
            "literal migration catalog/resource metadata",
        ),
    }
)

_C2B_MIGRATION_NAME_REFERENCE_ALLOWLIST = frozenset(
    {
        (
            "_PACKAGED_MIGRATION_SPECS",
            "Name",
            "_C2B2_MIGRATION_ID",
            "literal migration catalog/resource metadata",
        ),
        (
            "_require_sqlite_runtime_for_selected_migrations",
            "Name",
            "_C2B2_MIGRATION_ID",
            "the SQLite runtime-floor gate",
        ),
        (
            "_verify_applied_migration_zero_seed_invariants",
            "Name",
            "_C2B2_MIGRATION_ID",
            "sequence-scoped migration-completion zero-seed checks",
        ),
        (
            "_verify_empty_c2b2_migration_tables",
            "Name",
            "_EMPTY_AFTER_C2B2_MIGRATION_TABLES",
            "sequence-scoped migration-completion zero-seed checks",
        ),
    }
)

_C2B_MIGRATION_MODULE_CONSTANTS = frozenset(
    {"_C2B2_MIGRATION_ID", "_EMPTY_AFTER_C2B2_MIGRATION_TABLES"}
)
_C2B_MIGRATION_NAMED_CALLABLES = frozenset(
    {"_verify_empty_c2b2_migration_tables"}
)
_C2B_MIGRATION_REFERENCING_CALLABLES = frozenset(
    {
        "_require_sqlite_runtime_for_selected_migrations",
        "_verify_applied_migration_zero_seed_invariants",
        "_verify_empty_c2b2_migration_tables",
    }
)

TABLES_0003 = (
    "development_source_invocations",
    "development_candidate_capsule_bindings",
    "development_source_observation_claims",
    "development_observation_ref_heads",
    "development_observation_ingests",
    "development_observation_quarantines",
    "development_decision_evidence_bindings",
    "development_publication_eligibility",
    "development_first_slice_latch",
)

EXPLICIT_INDEXES = (
    "uq_development_effect_intents_author_command",
    "idx_development_source_observation_claims_digest",
)

CANCELLATION_EVIDENCE_ROLES = (
    "cancel_target_effect",
    "cancel_target_effect_fence",
    "cancel_target_capsule",
    "cancel_source_directive",
    "cancel_source_evidence",
)

DISPOSITIONS = (
    "duplicate_exact",
    "conflict_quarantined",
    "ambiguous_quarantined",
    "stale_retained",
    "late_retained",
    "recorded",
)

OBSERVATION_INGEST_STEPS = (
    "1. C2A1 record-local validation",
    "2. actual durable graph validation",
    "3. preserve source-authored claim",
    "4. compare prior observation identity/digest",
    "5. classify source-owner relation",
    "6. append Coordinator ingest disposition",
    "7. evaluate semantic progression separately",
)

MUTATION_FAMILIES = (
    "_initialize_development_program",
    "_establish_development_author_effect_intent",
    "_establish_development_bound_effect_intent",
    "_ingest_development_source_observation",
    "_record_development_progression_decision",
)

RECOVERY_FAMILIES = (
    "_resolve_development_program_initialization_commit_outcome",
    "_resolve_development_author_effect_establishment_commit_outcome",
    "_resolve_development_bound_effect_establishment_commit_outcome",
    "_resolve_development_source_observation_ingest_commit_outcome",
    "_resolve_development_progression_decision_commit_outcome",
)

TRANCHES = ("C2B0", "C2B1", "C2B2", "C2B3", "C2B4", "C2B5", "C2B6")

TRIGGER_ARITHMETIC = (
    "0002: 15 immutable tables * no-update/no-delete = 30",
    "0003: 7 immutable tables * no-update/no-delete = 14",
    "0003: latch no-delete = 1",
    "0003: latch one-way update guard = 1",
)

MIGRATION_PATHS = (
    "C2B2 fresh installation: 0001 -> 0002",
    "C2B4-or-later fresh installation: 0001 -> 0002 -> 0003",
    "C2B2 upgrade from exact 0001: apply only 0002",
    "C2B4-or-later upgrade from exact 0001: apply 0002 then 0003",
    "C2B4-or-later upgrade from exact 0002: apply only 0003",
)

ORDINARY_OPEN_RULES = (
    "exact complete catalog history",
    "exact current terminal sequence and migration ID",
    "terminal migration compatibility containing the current application generation",
    "complete final-schema verification",
)

MIGRATION_TRANSACTION_PATHS = (
    "C2B2 fresh installation transaction: [0001, 0002]",
    "C2B4-or-later fresh installation transaction: [0001, 0002, 0003]",
    "C2B2 upgrade from exact 0001 transaction: [0002]",
    "C2B4-or-later upgrade from exact 0001 transaction: [0002, 0003]",
    "C2B4-or-later upgrade from exact 0002 transaction: [0003]",
)

MIGRATION_TRANSACTION_COMPONENTS = (
    "DDL",
    "managed invariant changes",
    "matching migration-history insertion",
)

MIGRATION_RECOVERY_STEPS = (
    "close the uncertain connection",
    "reopen through the migration recovery path",
    "reread the complete exact migration history",
    "reread the complete live-schema invariants",
    "compare both the exact prior supported prefix and exact intended completed suffix tip",
)

MIGRATION_COMMITTED_EXACT = (
    "COMMITTED_EXACT",
    "history equals the prior prefix plus the complete intended suffix",
    "every suffix row's persisted projection resolves exactly to one packaged non-destructive definition",
    "live schema equals the complete intended terminal-tip schema",
    "the prior prefix remains unchanged",
    "no partial, extra, unknown, or divergent object exists",
)

MIGRATION_DEFINITELY_NOT_COMMITTED = (
    "DEFINITELY_NOT_COMMITTED",
    "history equals the exact prior supported prefix",
    "live schema equals the exact prior supported-prefix schema",
    "no intended suffix history row exists",
    "no intended suffix schema object or invariant exists",
    "no partial or unexpected object exists",
)

MIGRATION_UNRESOLVED = (
    "UNRESOLVED",
    "history and schema disagree",
    "only part of the intended suffix is present",
    "history-only suffix evidence exists",
    "schema-only suffix evidence exists",
    "an unknown or divergent history row exists",
    "an unexpected schema object exists",
    "either exact verification cannot be completed",
)

SQLITE_MIGRATION_DEFINITIONS = (
    "0002_development_program_and_effect_state: [2,2], non-destructive, 19 tables, 30 triggers, 1 explicit index, no seed rows",
    "0003_development_observation_and_progression_state: [2,2], non-destructive, 9 tables, 16 triggers, 1 explicit index, one available latch seed",
)

SQLITE_MIGRATION_SCHEMA_TOTALS = (
    "0001: 11 user tables, 0 explicit indexes, 16 triggers",
    "0002: 30 user tables, 1 explicit index, 46 triggers",
    "0003: 39 user tables, 2 explicit indexes, 62 triggers",
)

MIGRATION_FORBIDDEN_CLAIMS = (
    "c2b2 remains generation 1.",
    "c2b2 becomes generation 3.",
    "c2b3 prematurely installs 0003.",
    "c2b4 becomes generation 3.",
    "c2b4 drops to generation 1.",
    "c2b4 omits 0003.",
    "fresh installation applies only the terminal migration.",
    "fresh installation skips 0001.",
    "fresh installation skips 0002.",
    "ordinary open accepts 0001 before explicit migration.",
    "ordinary tip-0003 open accepts 0002.",
    "explicit migration accepts a gap.",
    "explicit migration accepts an unknown row.",
    "explicit migration accepts a checksum mismatch.",
    "explicit migration accepts divergent bounds.",
    "explicit migration accepts partial history or schema.",
    "c2b4 upgrade from exact 0001 commits 0002 before starting 0003.",
    "matching migration history alone is committed_exact even when the live schema differs.",
    "matching live schema alone is committed_exact even when migration history differs.",
    "after an unresolved migration commit, the suffix is automatically rerun.",
    "history and live-schema disagreement is committed_exact.",
    "a partial intended suffix is committed_exact.",
    "an unknown or divergent migration-history row is committed_exact.",
    "an unexpected live-schema object is committed_exact.",
    "incomplete exact history or live-schema verification is committed_exact.",
    "after an unresolved migration commit, the missing migration-suffix remainder is automatically appended.",
)

C2B1_REPAIR1_FORBIDDEN_CLAIMS = (
    "c2b1 is target-only.",
    "application generation 2 is current.",
    "migration 0002 is current.",
    "migration 0003 is current.",
    "ordinary open migrates a supported prefix.",
    "every historical row must include the running application generation.",
    "destructive is a schema_migrations column.",
    "non-filesystem migration resources are currently supported.",
    "symlinked migration resources are accepted.",
    "all migration failures use ordinary rollback.",
    "migration history alone is final-schema authority.",
    "an unresolved migration is automatically retried.",
    "the complete migration suffix is automatically rerun.",
    "the missing migration-suffix remainder is automatically appended.",
    "durable c2b records and runtime are current.",
)

LATCH_CONTRACT = (
    "latch_ref: direct_local_first_productive_acceptance",
    "scope: global Coordinator bootstrap",
    "initial state: available",
    "initial version: 0",
    "final state: consumed",
    "final version: 1",
    "reset: forbidden",
    "delete: forbidden",
    "reuse: forbidden",
)

LATCH_SEED_CONTRACT = (
    "latch_ref: direct_local_first_productive_acceptance",
    "state: available",
    "version: 0",
    "consumed bindings: null",
)

LATCH_DECLARATION_INVENTORY = (
    "latch_ref: direct_local_first_productive_acceptance",
    "reuse: forbidden",
    "latch_ref: direct_local_first_productive_acceptance",
)

SCHEMA_TOTALS = (
    "schema 0001: 11 user tables, 0 explicit application indexes, 16 triggers",
    "schema tip 0002: 30 user tables, 1 explicit application index, 46 triggers",
    "schema tip 0003: 39 user tables, 2 explicit application indexes, 62 triggers",
)

MIGRATION_ADDITION_TOTALS = (
    "0002: 19 tables, 30 triggers, 1 explicit index",
    "0003: 9 tables, 16 triggers, 1 explicit index",
)

TRIGGER_SCHEMA_ROLE_CLAIMS = (
    "schema 0001: 11 user tables, 0 explicit application indexes, 16 triggers",
    "schema tip 0002: 30 user tables, 1 explicit application index, 46 triggers",
    "schema tip 0003: 39 user tables, 2 explicit application indexes, 62 triggers",
)

TRIGGER_MIGRATION_ADDITION_ROLE_CLAIMS = (
    "0002: 19 tables, 30 triggers, 1 explicit index",
    "0003: 9 tables, 16 triggers, 1 explicit index",
)

TRIGGER_AGGREGATE_ROLE_CLAIMS = (
    "C2B adds exactly twenty-eight tables, forty-six triggers, and two explicit indexes.",
)

TRANCHE_LINES = (
    "C2B0: historical documentation and direct documentation-contract tests only",
    "C2B1: historical application generation 1 / terminal tip 0001 migration-framework reset; no SQL or schema change; no durable development state",
    "C2B2: application generation advances to 2; terminal tip 0002; migration 0002; core records, base decision envelope, initialize-decision representation, pure private row/value source, and twelve production-unintegrated private reader roles; no mutation API",
    "C2B3: application generation 2; terminal tip 0002; program initialization, author-effect establishment, private delegation and recovery; no external I/O",
    "C2B4: application generation 2; terminal tip 0003; migration 0003; observation/evidence/non-initialize-decision/eligibility/latch contracts and readers; initialize representation remains C2B2-owned; no new mutation API",
    "C2B5: application generation 2; terminal tip 0003; source-observation ingest, cancel and redeliver decisions, bound validation/review/cancellation effects, knowledge and recovery; no external I/O",
    "C2B6: application generation 2; terminal tip 0003; accept, repair, replan, terminal_reject, block, publication eligibility, latch, version/head recovery; no external I/O",
)


def _c2b_enclosing_symbol(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> str:
    current = node
    while current in parents:
        parent = parents[current]
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return parent.name
        if isinstance(parent, ast.Assign) and isinstance(parents.get(parent), ast.Module):
            targets = tuple(
                target.id for target in parent.targets if isinstance(target, ast.Name)
            )
            assert len(targets) == 1
            return targets[0]
        current = parent
    return "<module>"


def _assert_sqlite_migration_c2b_structure(
    source: str,
) -> tuple[tuple[str, str, str, str], ...]:
    tree = ast.parse(source)
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    literal_purposes = {
        (enclosing, category, token): purpose
        for enclosing, category, token, purpose in _C2B_MIGRATION_LITERAL_ALLOWLIST
    }
    name_purposes = {
        (enclosing, category, token): purpose
        for enclosing, category, token, purpose in _C2B_MIGRATION_NAME_REFERENCE_ALLOWLIST
    }
    observed_literals: list[tuple[str, str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or type(node.value) is not str:
            continue
        value = node.value
        if value in {
            "0002_development_program_and_effect_state",
            "0002_development_program_and_effect_state.sql",
        }:
            observed_literals.append(
                (_c2b_enclosing_symbol(node, parents), "Constant", value)
            )
        for table_name in TABLES_0002:
            if re.search(
                rf"(?<![0-9A-Za-z_]){re.escape(table_name)}(?![0-9A-Za-z_])",
                value,
            ):
                observed_literals.append(
                    (_c2b_enclosing_symbol(node, parents), "Constant", table_name)
                )

    observed_names = [
        (
            _c2b_enclosing_symbol(node, parents),
            "Name",
            node.id,
        )
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node.id in _C2B_MIGRATION_MODULE_CONSTANTS
    ]
    assert len(observed_literals) == len(literal_purposes)
    assert frozenset(observed_literals) == frozenset(literal_purposes)
    assert len(observed_names) == len(name_purposes)
    assert frozenset(observed_names) == frozenset(name_purposes)

    module_constants = frozenset(
        target.id
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        for target in statement.targets
        if isinstance(target, ast.Name)
        and re.search(r"c2b|development", target.id, flags=re.IGNORECASE)
    )
    named_callables = frozenset(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and re.search(r"c2b|development", node.name, flags=re.IGNORECASE)
    )
    referencing_callables = frozenset(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and (
            re.search(r"c2b|development", node.name, flags=re.IGNORECASE)
            or any(
                isinstance(descendant, ast.Name)
                and re.search(
                    r"c2b|development",
                    descendant.id,
                    flags=re.IGNORECASE,
                )
                for descendant in ast.walk(node)
            )
            or any(
                isinstance(descendant, ast.Constant)
                and type(descendant.value) is str
                and (
                    descendant.value
                    in {
                        "0002_development_program_and_effect_state",
                        "0002_development_program_and_effect_state.sql",
                    }
                    or any(
                        re.search(
                            rf"(?<![0-9A-Za-z_]){re.escape(table_name)}(?![0-9A-Za-z_])",
                            descendant.value,
                        )
                        for table_name in TABLES_0002
                    )
                )
                for descendant in ast.walk(node)
            )
        )
    )
    assert module_constants == _C2B_MIGRATION_MODULE_CONSTANTS
    assert named_callables == _C2B_MIGRATION_NAMED_CALLABLES
    assert referencing_callables == _C2B_MIGRATION_REFERENCING_CALLABLES

    return tuple(
        sorted(
            (
                enclosing,
                category,
                token,
                literal_purposes[(enclosing, category, token)],
            )
            for enclosing, category, token in observed_literals
        )
        + sorted(
            (
                enclosing,
                category,
                token,
                name_purposes[(enclosing, category, token)],
            )
            for enclosing, category, token in observed_names
        )
    )


def _text(path: Path | str) -> str:
    selected = path if isinstance(path, Path) else ROOT / path
    return selected.read_text(encoding="utf-8")


def _owner() -> str:
    return _text(OWNER_PATH)


def _compact(text: str) -> str:
    return " ".join(text.split())


def _require(condition: bool, diagnostic: str) -> None:
    if not condition:
        raise AssertionError(diagnostic)


def _markdown_fence_candidate(content: str) -> tuple[str, int, str] | None:
    stripped = content.lstrip(" ")
    indent = len(content) - len(stripped)
    if indent > 3 or not stripped or stripped[0] not in "`~":
        return None
    marker = stripped[0]
    run_length = len(stripped) - len(stripped.lstrip(marker))
    if run_length < 3:
        return None
    remainder = stripped[run_length:]
    if marker == "`" and "`" in remainder:
        return None
    return marker, run_length, remainder


def _markdown_closer_suffix_is_ascii_space_tab(suffix: str) -> bool:
    return all(character in {" ", "\t"} for character in suffix)


def _markdown_fence_closes(
    candidate: tuple[str, int, str] | None,
    *,
    marker: str,
    opener_length: int,
) -> bool:
    return (
        candidate is not None
        and candidate[0] == marker
        and candidate[1] >= opener_length
        and _markdown_closer_suffix_is_ascii_space_tab(candidate[2])
    )


@dataclass(frozen=True)
class _TopLevelFencedBlock:
    marker: str
    opener_length: int
    info: str
    opening_line: str
    closing_line: str
    opening_line_number: int
    closing_line_number: int
    start_offset: int
    end_offset: int
    content_start_offset: int
    content_end_offset: int
    content: str


def _markdown_scan(
    text: str,
    *,
    role: str,
) -> tuple[tuple[tuple[int, str, int, int], ...], str]:
    """Return real ATX headings and unfenced Markdown with bounded diagnostics."""
    headings: list[tuple[int, str, int, int]] = []
    unfenced: list[str] = []
    fence: tuple[str, int] | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        stripped = content.lstrip(" ")
        indent = len(content) - len(stripped)
        fence_candidate = _markdown_fence_candidate(content)

        if fence is not None:
            if _markdown_fence_closes(
                fence_candidate,
                marker=fence[0],
                opener_length=fence[1],
            ):
                fence = None
            offset += len(line)
            continue

        if fence_candidate is not None:
            fence = (fence_candidate[0], fence_candidate[1])
            offset += len(line)
            continue

        unfenced.append(line)
        if indent <= 3:
            match = re.fullmatch(r"(#{1,6})[ \t]+(.+?)[ \t]*", stripped)
            if match is not None:
                title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2)).strip()
                _require(bool(title), f"{role}|heading=<atx>|failure=empty")
                headings.append((len(match.group(1)), title, offset, offset + len(line)))
        offset += len(line)

    _require(fence is None, f"{role}|heading=<none>|failure=unbalanced_fence")
    return tuple(headings), "".join(unfenced)


def _top_level_fenced_blocks(
    text: str,
    *,
    role: str,
) -> tuple[_TopLevelFencedBlock, ...]:
    """Read the finite top-level fenced-block surface used by C2B0 inventories."""
    blocks: list[_TopLevelFencedBlock] = []
    fence: tuple[str, int, str, str, int, int, int] | None = None
    offset = 0
    for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
        content = line.rstrip("\r\n")
        candidate = _markdown_fence_candidate(content)
        if fence is None:
            if candidate is not None:
                marker, opener_length, info = candidate
                fence = (
                    marker,
                    opener_length,
                    info,
                    line,
                    line_number,
                    offset,
                    offset + len(line),
                )
            offset += len(line)
            continue

        marker, opener_length, info, opening_line, opening_line_number, start, content_start = fence
        if _markdown_fence_closes(
            candidate,
            marker=marker,
            opener_length=opener_length,
        ):
            blocks.append(
                _TopLevelFencedBlock(
                    marker=marker,
                    opener_length=opener_length,
                    info=info,
                    opening_line=opening_line,
                    closing_line=line,
                    opening_line_number=opening_line_number,
                    closing_line_number=line_number,
                    start_offset=start,
                    end_offset=offset + len(line),
                    content_start_offset=content_start,
                    content_end_offset=offset,
                    content=text[content_start:offset],
                )
            )
            fence = None
        offset += len(line)

    _require(
        fence is None,
        f"{role}|block=<none>|failure=unbalanced_fence",
    )
    return tuple(blocks)


def _unfenced_markdown(text: str, *, role: str) -> str:
    return _markdown_scan(text, role=role)[1]


def _c2b3a_planning_evidence_ledger(
    text: str,
    *,
    begin: str,
    end: str,
    diagnostic: str,
) -> tuple[str, ...]:
    if text.count(begin) != 1 or text.count(end) != 1:
        raise AssertionError(diagnostic)
    payload = text.split(begin, 1)[1].split(end, 1)[0]
    entries: list[str] = []
    for line in payload.splitlines():
        if line.startswith("- "):
            entries.append(line[2:])
        elif line.startswith("  ") and entries:
            entries[-1] += " " + line.strip()
        else:
            raise AssertionError(diagnostic)
    return tuple(entries)


def _assert_c2b3a_planning_status(text: str) -> None:
    diagnostic = "C2B3A_PLANNING_PROJECTION_INVALID"
    markers = (
        "<!-- C2B3A_PLANNING_PROJECTION_BEGIN -->",
        "<!-- C2B3A_PLANNING_NON_AUTHORITY_BEGIN -->",
        "<!-- C2B3A_PLANNING_NON_AUTHORITY_END -->",
        "<!-- C2B3A_PLANNING_CURRENT_STATUS_BEGIN -->",
        "<!-- C2B3A_PLANNING_CURRENT_STATUS_END -->",
        "<!-- C2B3A_PLANNING_LEGACY_LEDGER_BEGIN -->",
        "<!-- C2B3A_PLANNING_LEGACY_LEDGER_END -->",
        "<!-- C2B3A_PLANNING_ACTIVE_SCOPE_BEGIN -->",
        "<!-- C2B3A_PLANNING_ACTIVE_SCOPE_END -->",
        "<!-- C2B3A_PLANNING_VALIDATION_ACCEPTANCE_BEGIN -->",
        "<!-- C2B3A_PLANNING_VALIDATION_ACCEPTANCE_END -->",
        "<!-- C2B3A_PLANNING_PRODUCTION_NONIMPLEMENTATION_BEGIN -->",
        "<!-- C2B3A_PLANNING_PRODUCTION_NONIMPLEMENTATION_END -->",
        "<!-- C2B3A_PLANNING_PROJECTION_END -->",
    )
    if type(text) is not str:
        raise AssertionError(diagnostic)
    if any(text.count(marker) != 1 for marker in markers):
        raise AssertionError(diagnostic)
    positions = tuple(text.index(marker) for marker in markers)
    if positions != tuple(sorted(positions)):
        raise AssertionError(diagnostic)
    if not text.startswith(
        "# C2B3 Program Initialization\n\n" + markers[0] + "\n"
    ):
        raise AssertionError(diagnostic)
    if not text.endswith(markers[-1] + "\n"):
        raise AssertionError(diagnostic)
    source_acceptance_evidence = _c2b3a_planning_evidence_ledger(
        text,
        begin=(
            "Before C2B3B source is accepted, all of the following separate "
            "evidence is\nrequired:\n\n"
        ),
        end=(
            "\n\nThe committed Coordinator repository baseline and the refreshed "
            "exact\n"
        ),
        diagnostic=diagnostic,
    )
    source_start_evidence = _c2b3a_planning_evidence_ledger(
        text,
        begin=(
            "Before source mutation begins, C2B3B source implementation requires "
            "all of the\nfollowing separate evidence:\n\n"
        ),
        end="\n\nA dirty four-file working tree is not a source baseline.",
        diagnostic=diagnostic,
    )
    if (
        source_acceptance_evidence != C2B3A_SOURCE_ACCEPTANCE_EVIDENCE_LEDGER
        or source_start_evidence != C2B3A_SOURCE_START_EVIDENCE_LEDGER
    ):
        raise AssertionError(diagnostic)
    if text != C2B3A_PLANNING_PROJECTION_APPROVED_TEXT:
        raise AssertionError(diagnostic)


def _c2b3a_oracle_attribute_chain(node: ast.AST) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    return ".".join(reversed(parts))


def _c2b3a_oracle_closed_literal(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.Tuple, ast.List)):
        return all(_c2b3a_oracle_closed_literal(element) for element in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            key is not None
            and _c2b3a_oracle_closed_literal(key)
            and _c2b3a_oracle_closed_literal(value)
            for key, value in zip(node.keys, node.values, strict=True)
        )
    return (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and type(node.operand.value) in {int, float, complex}
    )


def _c2b3a_oracle_assigned_names(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, (ast.Tuple, ast.List)):
        names: list[str] = []
        for element in node.elts:
            names.extend(_c2b3a_oracle_assigned_names(element))
        return tuple(names)
    if isinstance(node, ast.Starred):
        return _c2b3a_oracle_assigned_names(node.value)
    if isinstance(node, ast.MatchAs):
        nested = (
            _c2b3a_oracle_assigned_names(node.pattern)
            if node.pattern is not None
            else ()
        )
        return nested + ((node.name,) if node.name is not None else ())
    if isinstance(node, ast.MatchStar):
        return (node.name,) if node.name is not None else ()
    if isinstance(node, ast.MatchMapping):
        names = tuple(
            name
            for pattern in node.patterns
            for name in _c2b3a_oracle_assigned_names(pattern)
        )
        return names + ((node.rest,) if node.rest is not None else ())
    if isinstance(node, (ast.MatchSequence, ast.MatchOr)):
        return tuple(
            name
            for pattern in node.patterns
            for name in _c2b3a_oracle_assigned_names(pattern)
        )
    if isinstance(node, ast.MatchClass):
        return tuple(
            name
            for pattern in (*node.patterns, *node.kwd_patterns)
            for name in _c2b3a_oracle_assigned_names(pattern)
        )
    return ()


def _c2b3a_oracle_enclosing_function(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
        current = parents.get(current)
    return None


def _c2b3a_oracle_function_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[str, ...]:
    header = _c2b3a_oracle_function_header(node)
    parameters = tuple(
        argument.arg
        for argument in (
            *header["posonlyargs"],
            *header["args"],
            *header["kwonlyargs"],
        )
    )
    vararg = header["vararg"]
    kwarg = header["kwarg"]
    if vararg is not None:
        parameters += (vararg.arg,)
    if kwarg is not None:
        parameters += (kwarg.arg,)
    return parameters


def _c2b3a_oracle_function_header(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, object]:
    return {
        "node_type": type(node),
        "name": node.name,
        "decorators": tuple(node.decorator_list),
        "return_annotation": node.returns,
        "type_comment": node.type_comment,
        "type_params": tuple(getattr(node, "type_params", ())),
        "posonlyargs": tuple(node.args.posonlyargs),
        "args": tuple(node.args.args),
        "defaults": tuple(node.args.defaults),
        "vararg": node.args.vararg,
        "kwonlyargs": tuple(node.args.kwonlyargs),
        "kw_defaults": tuple(node.args.kw_defaults),
        "kwarg": node.args.kwarg,
    }


def _c2b3a_oracle_module_name_bindings(
    tree: ast.Module,
    name: str,
) -> tuple[tuple[str, int], ...]:
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }

    def enclosing_binding_scope(node: ast.AST) -> ast.AST | None:
        current = node
        while current in parents:
            parent = parents[current]
            if isinstance(parent, ast.Lambda):
                return parent
            if isinstance(
                parent,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ) and any(current is statement for statement in parent.body):
                return parent
            current = parent
        return None

    def is_comprehension_target(node: ast.AST) -> bool:
        current = node
        while current in parents:
            parent = parents[current]
            if isinstance(parent, ast.comprehension):
                return current is parent.target
            if isinstance(
                parent,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Lambda,
                ),
            ):
                return False
            current = parent
        return False

    bindings: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        bound_name: str | None = None
        binding_kind: str | None = None
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, (ast.Store, ast.Del))
            and not is_comprehension_target(node)
        ):
            bound_name = node.id
            binding_kind = (
                "name_store" if isinstance(node.ctx, ast.Store) else "name_delete"
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            bound_name = node.name
            binding_kind = "function_definition"
        elif isinstance(node, ast.ClassDef):
            bound_name = node.name
            binding_kind = "class_definition"
        elif isinstance(node, ast.alias):
            bound_name = node.asname or node.name.split(".", 1)[0]
            binding_kind = "import_alias"
        elif isinstance(node, ast.ExceptHandler) and node.name is not None:
            bound_name = node.name
            binding_kind = "exception_handler"
        elif isinstance(node, (ast.Global, ast.Nonlocal)) and name in node.names:
            bound_name = name
            binding_kind = type(node).__name__.lower()
        elif isinstance(node, ast.MatchAs) and node.name is not None:
            bound_name = node.name
            binding_kind = "match_as"
        elif isinstance(node, ast.MatchStar) and node.name is not None:
            bound_name = node.name
            binding_kind = "match_star"
        elif isinstance(node, ast.MatchMapping) and node.rest is not None:
            bound_name = node.rest
            binding_kind = "match_mapping_rest"
        if (
            bound_name == name
            and binding_kind is not None
            and (
                binding_kind in {"global", "nonlocal"}
                or enclosing_binding_scope(node) is None
            )
        ):
            bindings.append((binding_kind, node.lineno))
    return tuple(sorted(bindings))


def _c2b3a_oracle_module_wildcard_imports(
    tree: ast.Module,
) -> tuple[tuple[str | None, int, int], ...]:
    return tuple(
        sorted(
            (
                node.module,
                node.level,
                node.lineno,
            )
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and any(alias.name == "*" for alias in node.names)
        )
    )


def _c2b3a_oracle_direct_module_dictionary_operations(
    tree: ast.Module,
) -> tuple[tuple[str, str, int], ...]:
    protected_names = {"ast", "exec"}

    def is_loaded_name(node: ast.AST, name: str) -> bool:
        return (
            isinstance(node, ast.Name)
            and node.id == name
            and isinstance(node.ctx, ast.Load)
        )

    def is_module_object(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Subscript)
            and isinstance(node.ctx, ast.Load)
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "modules"
            and isinstance(node.value.ctx, ast.Load)
            and is_loaded_name(node.value.value, "sys")
            and isinstance(node.slice, ast.Name)
            and node.slice.id == "__name__"
            and isinstance(node.slice.ctx, ast.Load)
        )

    def is_globals_dictionary(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and is_loaded_name(node.func, "globals")
            and node.args == []
            and node.keywords == []
        )

    def is_vars_module_dictionary(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and is_loaded_name(node.func, "vars")
            and len(node.args) == 1
            and is_module_object(node.args[0])
            and node.keywords == []
        )

    operations: list[tuple[str, str, int]] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.ctx, (ast.Store, ast.Del))
            and isinstance(node.slice, ast.Constant)
            and type(node.slice.value) is str
            and node.slice.value in protected_names
        ):
            operation = (
                "write" if isinstance(node.ctx, ast.Store) else "delete"
            )
            if is_globals_dictionary(node.value):
                operations.append(
                    (node.slice.value, f"globals_subscript_{operation}", node.lineno)
                )
            elif is_vars_module_dictionary(node.value):
                operations.append(
                    (
                        node.slice.value,
                        f"vars_sys_modules_subscript_{operation}",
                        node.lineno,
                    )
                )
        elif (
            isinstance(node, ast.Call)
            and is_loaded_name(node.func, "setattr")
            and len(node.args) == 3
            and is_module_object(node.args[0])
            and isinstance(node.args[1], ast.Constant)
            and type(node.args[1].value) is str
            and node.args[1].value in protected_names
            and node.keywords == []
        ):
            operations.append(
                (node.args[1].value, "setattr_sys_modules_write", node.lineno)
            )
        elif (
            isinstance(node, ast.Call)
            and is_loaded_name(node.func, "delattr")
            and len(node.args) == 2
            and is_module_object(node.args[0])
            and isinstance(node.args[1], ast.Constant)
            and type(node.args[1].value) is str
            and node.args[1].value in protected_names
            and node.keywords == []
        ):
            operations.append(
                (node.args[1].value, "delattr_sys_modules_delete", node.lineno)
            )
    return tuple(sorted(operations))


def _c2b3a_oracle_direct_hostile_environment_operations(
    tree: ast.Module,
) -> tuple[tuple[str, int], ...]:
    imported_module_names = {
        alias.asname or alias.name.split(".", 1)[0]
        for statement in tree.body
        if isinstance(statement, ast.Import)
        for alias in statement.names
    }

    def loaded_name(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            return node.id
        return None

    def attribute_root(node: ast.Attribute) -> str | None:
        value = node.value
        while isinstance(value, ast.Attribute):
            value = value.value
        return loaded_name(value)

    def is_vars_of_imported_module(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and loaded_name(node.func) == "vars"
            and len(node.args) == 1
            and loaded_name(node.args[0]) in imported_module_names
            and node.keywords == []
        )

    def is_sys_modules(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Attribute)
            and node.attr == "modules"
            and isinstance(node.ctx, ast.Load)
            and loaded_name(node.value) == "sys"
        )

    def direct_environment_object(node: ast.AST) -> bool:
        return (
            loaded_name(node) in imported_module_names | {"__builtins__"}
            or (
                isinstance(node, ast.Subscript)
                and isinstance(node.ctx, ast.Load)
                and is_sys_modules(node.value)
            )
        )

    operations: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and node.id == "__builtins__"
            and isinstance(node.ctx, (ast.Store, ast.Del))
        ):
            operations.append(("direct___builtins___binding_mutation", node.lineno))
        elif (
            isinstance(node, ast.Attribute)
            and isinstance(node.ctx, (ast.Store, ast.Del))
            and attribute_root(node) in imported_module_names | {"__builtins__"}
        ):
            operations.append(("direct_imported_object_attribute_mutation", node.lineno))
        elif isinstance(node, ast.Subscript) and isinstance(
            node.ctx,
            (ast.Store, ast.Del),
        ):
            if is_sys_modules(node.value):
                operations.append(("direct_sys_modules_mutation", node.lineno))
            elif is_vars_of_imported_module(node.value):
                operations.append(("direct_imported_object_vars_mutation", node.lineno))
            elif loaded_name(node.value) == "__builtins__":
                operations.append(("direct___builtins___mapping_mutation", node.lineno))
        elif (
            isinstance(node, ast.Call)
            and loaded_name(node.func) in {"setattr", "delattr"}
            and len(node.args) >= 2
            and direct_environment_object(node.args[0])
        ):
            operations.append(("direct_environment_setattr_or_delattr", node.lineno))
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"setattr", "delattr"}
            and len(node.args) >= 2
            and direct_environment_object(node.args[0])
        ):
            operations.append(
                ("direct_monkeypatch_environment_setattr_or_delattr", node.lineno)
            )
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"setitem", "delitem"}
            and len(node.args) >= 2
            and (
                is_sys_modules(node.args[0])
                or is_vars_of_imported_module(node.args[0])
                or loaded_name(node.args[0]) == "__builtins__"
            )
        ):
            operations.append(
                ("direct_monkeypatch_environment_setitem_or_delitem", node.lineno)
            )
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"append", "clear", "extend", "insert", "pop"}
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr in {"meta_path", "path_hooks"}
            and loaded_name(node.func.value.value) == "sys"
        ):
            operations.append(("direct_import_hook_collection_mutation", node.lineno))
    return tuple(sorted(operations))


def _c2b3a_oracle_literal_assignment(
    tree: ast.Module,
    name: str,
) -> ast.Assign:
    assignments = tuple(
        statement
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == name
    )
    if len(assignments) != 1:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_ARCHITECTURE_INVALID")
    assignment = assignments[0]
    expected_node_type: type[ast.AST] = {
        "EXPECTED_PLANNING_PROJECTION": ast.Constant,
        "EXPECTED_INITIALIZATION_CONTRACT": ast.Dict,
        "EXPECTED_INITIALIZATION_GOLDEN_VECTOR": ast.Dict,
        "EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM": ast.Dict,
        "EXPECTED_PROCESS_CONTROL_REFERENCE_CASES": ast.Dict,
        "CLEANUP_SAFE_PROJECTION_FIELDS": ast.Tuple,
        "CLEANUP_REFERENCE_INPUT_CASES": ast.Tuple,
        "EXPECTED_CLEANUP_REFERENCE_CASES": ast.Dict,
    }.get(name, ast.Dict)
    if not isinstance(assignment.value, expected_node_type):
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_ARCHITECTURE_INVALID")
    if not _c2b3a_oracle_closed_literal(assignment.value):
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_ARCHITECTURE_INVALID")
    return assignment


def _c2b3a_oracle_protected_load_role(
    node: ast.Name,
    parents: dict[ast.AST, ast.AST],
) -> str | None:
    parent = parents.get(node)
    if isinstance(parent, ast.Call) and parent.func is node:
        return "direct_call_func"

    expression: ast.AST = node
    while isinstance(parent, ast.Subscript) and parent.value is expression:
        expression = parent
        parent = parents.get(expression)

    if isinstance(parent, ast.Compare) and (
        parent.left is expression or expression in parent.comparators
    ):
        return "direct_comparison_operand"
    if isinstance(parent, ast.Assert) and parent.test is expression:
        return "direct_assert_operand"
    if isinstance(parent, ast.Call) and (
        expression in parent.args
        or any(keyword.value is expression for keyword in parent.keywords)
    ):
        return "direct_candidate_argument"
    return None


def _c2b3a_oracle_protected_load_sites(
    tree: ast.Module,
    parents: dict[ast.AST, ast.AST],
) -> tuple[tuple[object, ...], ...]:
    protected_names = (
        C2B3A_ORACLE_PROTECTED_EXPECTED_VALUE_NAMES
        + C2B3A_ORACLE_PROTECTED_CANDIDATE_VALUE_NAMES
        + C2B3A_ORACLE_PROTECTED_CALLABLE_NAMES
    )
    if len(set(protected_names)) != len(protected_names):
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_ARCHITECTURE_INVALID")
    protected_name_set = set(protected_names)
    loads = sorted(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in protected_name_set
        ),
        key=lambda node: (
            node.lineno,
            node.col_offset,
            node.end_lineno if node.end_lineno is not None else -1,
            node.end_col_offset if node.end_col_offset is not None else -1,
        ),
    )
    ordinals: dict[tuple[str, str | None, str | None], int] = {}
    records: list[tuple[object, ...]] = []
    for node in loads:
        functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        current = parents.get(node)
        ancestor_kinds = [type(node).__name__]
        while current is not None:
            ancestor_kinds.append(type(current).__name__)
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(current)
            current = parents.get(current)
        top_level_function = functions[-1].name if functions else None
        nested_function = functions[0].name if len(functions) > 1 else None
        ordinal_key = (node.id, top_level_function, nested_function)
        ordinal = ordinals.get(ordinal_key, 0)
        ordinals[ordinal_key] = ordinal + 1
        records.append(
            (
                node.id,
                top_level_function,
                nested_function,
                _c2b3a_oracle_protected_load_role(node, parents),
                tuple(ancestor_kinds),
                ordinal,
            )
        )
    return tuple(records)


def _c2b3a_oracle_expected_protected_load_sites() -> tuple[tuple[object, ...], ...]:
    mutant_records: list[tuple[object, ...]] = []
    for _mutant_id, function_name in C2B3A_LINEAR_MUTANT_FUNCTIONS:
        mutant_records.extend(
            (
                (
                    "_candidate",
                    function_name,
                    None,
                    "direct_call_func",
                    ("Name", "Call", "Assign", "FunctionDef", "Module"),
                    0,
                ),
                (
                    "_expect_violation",
                    function_name,
                    None,
                    "direct_call_func",
                    ("Name", "Call", "Expr", "FunctionDef", "Module"),
                    0,
                ),
            )
        )
    return C2B3A_ORACLE_LEGAL_PROTECTED_LOAD_SITES + tuple(mutant_records)


def _assert_c2b3a_oracle_collection_architecture(
    tree: ast.Module,
    parents: dict[ast.AST, ast.AST],
) -> None:
    diagnostic = "C2B3A_INDEPENDENT_ORACLE_ARCHITECTURE_INVALID"
    forbidden_module_bindings = {
        "__all__",
        "__test__",
        "pytest_plugins",
        "pytestmark",
    }
    test_function_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("pytest_"):
                raise AssertionError(diagnostic)
            if node.name.startswith("test_"):
                if parents.get(node) is not tree or node.name in test_function_names:
                    raise AssertionError(diagnostic)
                test_function_names.add(node.name)
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            for target in targets:
                root = target
                while isinstance(root, (ast.Attribute, ast.Subscript)):
                    root = root.value
                if not isinstance(root, ast.Name):
                    continue
                if root.id in forbidden_module_bindings:
                    raise AssertionError(diagnostic)
                if root.id.startswith("test_"):
                    raise AssertionError(diagnostic)
        if isinstance(node, ast.Delete):
            for target in node.targets:
                root = target
                while isinstance(root, (ast.Attribute, ast.Subscript)):
                    root = root.value
                if isinstance(root, ast.Name) and root.id.startswith("test_"):
                    raise AssertionError(diagnostic)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            chain = _c2b3a_oracle_attribute_chain(node.func)
            if chain in {"pytest.exit", "pytest.skip"}:
                raise AssertionError(diagnostic)


def _c2b3a_oracle_top_level_function(
    tree: ast.Module,
    name: str,
) -> ast.FunctionDef:
    diagnostic = "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
    matches = tuple(
        statement
        for statement in tree.body
        if isinstance(statement, ast.FunctionDef) and statement.name == name
    )
    if len(matches) != 1:
        raise AssertionError(diagnostic)
    return matches[0]


def _c2b3a_oracle_store_root(node: ast.AST) -> str | None:
    current = node
    while isinstance(current, (ast.Attribute, ast.Subscript)):
        current = current.value
    return current.id if isinstance(current, ast.Name) else None


def _c2b3a_oracle_literal_value(tree: ast.Module, name: str) -> dict[str, object]:
    diagnostic = "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
    try:
        assignment = _c2b3a_oracle_literal_assignment(tree, name)
        value = ast.literal_eval(assignment.value)
    except (AssertionError, SyntaxError, ValueError):
        raise AssertionError(diagnostic) from None
    if type(value) is not dict:
        raise AssertionError(diagnostic)
    return value


def _assert_c2b3a_addendum_literal_semantics(tree: ast.Module) -> None:
    diagnostic = "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
    addendum = _c2b3a_oracle_literal_value(
        tree,
        "EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM",
    )
    if addendum.get("normative_surface_and_precedence") != {
        "structured_owner": "commit_close_outcome_addendum",
        "sole_operative_semantic_authority_for": (
            "COMMIT and close outcomes",
            "process-control relationships",
            "cleanup states and order",
            "finalizer and liveness rules",
            "recovery and replay gates",
            "future C2B3B path scope",
        ),
        "pre_addendum_section_35_treatment": "historical evidence and original C2B3A contract truth",
        "explicit_supersession_rule": "where an additive structured owner value explicitly supersedes a historical target value, the additive structured value is operative for C2B3B",
        "explanatory_prose_has_independent_authority": False,
        "explanatory_prose_may_create_override_widen_or_narrow": False,
        "planning_is_semantic_authority": False,
        "planning_may_resolve_or_change_owner_truth": False,
        "free_form_prose_may_supply_operational_semantics_when_structured_value_exists": False,
    }:
        raise AssertionError(diagnostic)
    cleanup = addendum.get("post_close_cleanup_contract")
    if type(cleanup) is not dict or cleanup.get("ordered_steps") != (
        "P0",
        "C1",
        "C2",
        "R1",
        "R2",
        "R3",
        "L1",
        "H1",
        "H2",
        "T1",
        "H3",
    ):
        raise AssertionError(diagnostic)
    acknowledgement = cleanup.get("acknowledgement_complete_boundary")
    if acknowledgement != {
        "C1_and_C2_remain_ordered_responsibilities": True,
        "successful_C1_is_stable_or_outwardly_observable_before_C2": False,
        "C1_after_fault_is_independently_observable": False,
        "C2_before_fault_is_independently_observable": False,
        "normal_close_requires_before_result_or_propagation": (
            "record connection_closed_proved",
            "clear raw connection custody",
            "publish QU -> PU or QK -> PK",
        ),
        "closure_proved_QU_or_QK_with_connection_custody": False,
        "PU_or_PK_with_connection_custody": False,
        "extra_stable_session_state": False,
    }:
        raise AssertionError(diagnostic)
    if addendum.get("legacy_exception_probe_ledger_classification") != {
        "ledger_path": "commit_uncertainty_cleanup_gate.close_not_proved.process_control_exception_graph_ledger",
        "classification": "historical_runtime_observation",
        "normative": False,
        "operative_for_c2b3b": False,
        "portable_contract": False,
        "preserved_for_original_c2b3a_evidence": True,
        "superseded_for_target_semantics_by": "process_control_relational_policy",
        "observed_values_scope": "exact traceback, cause, context, suppression, cycle, and reachability values are observations of the original bounded reference branch only",
        "consumer_rule": "no implementation, test oracle, planning projection, or future prompt may use those observed values as target requirements",
    }:
        raise AssertionError(diagnostic)
    scope = addendum.get("future_c2b3b_path_scope_status")
    if type(scope) is not dict:
        raise AssertionError(diagnostic)
    if scope.get("required_production_paths") != (
        "src/ge_nwp_coordinator/_development_program_initialization_contracts.py",
        "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py",
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "src/ge_nwp_coordinator/sqlite_writer_session.py",
        "src/ge_nwp_coordinator/sqlite_connection.py",
        "src/ge_nwp_coordinator/state_authority_lock.py",
    ):
        raise AssertionError(diagnostic)
    if scope.get("required_documentation_status_paths") != (
        ".docs/c2b-durable-development-state.md",
        ".docs/c2b3-program-initialization.md",
        ".docs/c2b2-private-readers.md",
        ".docs/architecture.md",
        ".docs/durable-state-model.md",
        ".docs/sqlite-operations-and-recovery.md",
        ".docs/sqlite-threat-model.md",
        ".docs/writer-session-authority.md",
        "README.md",
        "AGENTS.md",
    ):
        raise AssertionError(diagnostic)
    if scope.get("required_changed_test_paths") != (
        "tests/test_c2b3_program_initialization_contract.py",
        "tests/test_c2b3_private_atomic_program_initialization.py",
        "tests/test_c2b3_program_initialization_recovery.py",
        "tests/test_c2b3_private_program_initialization_delegation.py",
        "tests/test_c2b2_field_level_contract.py",
        "tests/test_c2b2_development_reader_contracts.py",
        "tests/test_sqlite_b2c_writer_session.py",
        "tests/test_state_authority_lock.py",
        "tests/test_runtime_non_authority.py",
        "tests/test_architecture_contracts.py",
        "tests/test_c2b0_durable_state_contract.py",
    ):
        raise AssertionError(diagnostic)
    if (
        scope.get("required_path_counts") != (6, 10, 11)
        or scope.get("expected_actual_write_paths") != 27
        or scope.get("contingency_path")
        != "tests/test_c2b2_private_development_readers.py"
        or scope.get("maximum_paths") != 28
        or scope.get("twenty_ninth_path")
        != "hard stop and scope reassessment condition"
    ):
        raise AssertionError(diagnostic)
    if scope.get("future_implementation_scope_supersession") != {
        "historical_scope_id": "future_c2b3b_maximum_path_scope",
        "operative": False,
        "consumers_may_use": False,
        "active_replacement_scope_id": "C2B3B_PRIVATE_ATOMIC_INITIALIZATION",
        "active_replacement_owner": "commit_close_outcome_addendum.future_c2b3b_path_scope_status",
        "active_expected_actual_write_paths": 27,
        "active_maximum_paths": 28,
        "active_stop_path_ordinal": 29,
        "newly_required_paths": (
            "src/ge_nwp_coordinator/state_authority_lock.py",
            ".docs/writer-session-authority.md",
            "tests/test_state_authority_lock.py",
            "tests/test_sqlite_b2c_writer_session.py",
        ),
        "preserved_literal": "future_c2b3b_maximum_path_scope",
        "preserved_values": {
            "production_paths": 5,
            "documentation_status_paths": 9,
            "test_paths": 10,
            "expected_actual_write_paths": 23,
            "maximum_paths": 24,
            "stop_path_ordinal": 25,
        },
        "classification": "historical and non-operative for C2B3B after this addendum",
        "preservation_reason": "preserve the accepted earlier C2B3A freeze byte-for-byte",
        "operative_scope_owner": "commit_close_outcome_addendum.future_c2b3b_path_scope_status",
        "old_values_may_be_used_as_active_authority": False,
        "operative_values": {
            "production_paths": 6,
            "documentation_status_paths": 10,
            "required_changed_tests": 11,
            "expected_actual_write_paths": 27,
            "contingency_paths": 1,
            "maximum_paths": 28,
            "stop_path_ordinal": 29,
        },
    }:
        raise AssertionError(diagnostic)
    semantic = addendum.get("direct_oracle_requirements")
    if type(semantic) is not dict:
        raise AssertionError(diagnostic)
    protection = semantic.get("semantic_execution_protection")
    if type(protection) is not dict or protection != {
        "diagnostic": "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID",
        "expect_violation_exact_validator_and_diagnostic": True,
        "mutant_dataflow": "each protected mutant has exactly one candidate = _candidate(), one or more direct candidate-rooted assignments, and the identical candidate reaches one final _expect_violation with the exact diagnostic",
        "mutant_control_flow": "each protected mutant is one branch-free linear function with no unrelated local assignment, call, or possible pre-validation termination",
        "positive_body_and_reference_helper_execution_protected": True,
        "positive_result_dataflow": "each helper result is a single immutable reaching definition consumed directly by discriminating field assertions; overwrite, deletion, mutation, alias, shadow target, and unused results are rejected",
        "bounded_isolated_physical_counterfactuals": True,
        "whole_file_source_hash_authority": False,
        "generic_semantic_dispatcher": False,
    }:
        raise AssertionError(diagnostic)


def _assert_c2b3a_expect_violation_semantics(tree: ast.Module) -> None:
    diagnostic = "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
    function = _c2b3a_oracle_top_level_function(tree, "_expect_violation")
    if _c2b3a_oracle_function_parameters(function) != ("candidate", "code"):
        raise AssertionError(diagnostic)
    if function.decorator_list or len(function.body) != 2:
        raise AssertionError(diagnostic)
    context_statement, diagnostic_statement = function.body
    if (
        not isinstance(context_statement, ast.With)
        or len(context_statement.items) != 1
        or len(context_statement.body) != 1
    ):
        raise AssertionError(diagnostic)
    item = context_statement.items[0]
    context_call = item.context_expr
    if (
        not isinstance(context_call, ast.Call)
        or _c2b3a_oracle_attribute_chain(context_call.func) != "pytest.raises"
        or len(context_call.args) != 1
        or not isinstance(context_call.args[0], ast.Name)
        or context_call.args[0].id != "_ContractViolation"
        or context_call.keywords
        or not isinstance(item.optional_vars, ast.Name)
        or item.optional_vars.id != "exc_info"
    ):
        raise AssertionError(diagnostic)
    validation_statement = context_statement.body[0]
    if (
        not isinstance(validation_statement, ast.Expr)
        or not isinstance(validation_statement.value, ast.Call)
        or not isinstance(validation_statement.value.func, ast.Name)
        or validation_statement.value.func.id != "_validate_contract"
        or len(validation_statement.value.args) != 1
        or not isinstance(validation_statement.value.args[0], ast.Name)
        or validation_statement.value.args[0].id != "candidate"
        or validation_statement.value.keywords
    ):
        raise AssertionError(diagnostic)
    if not isinstance(diagnostic_statement, ast.Assert):
        raise AssertionError(diagnostic)
    comparison = diagnostic_statement.test
    if (
        not isinstance(comparison, ast.Compare)
        or len(comparison.ops) != 1
        or not isinstance(comparison.ops[0], ast.Eq)
        or len(comparison.comparators) != 1
        or not isinstance(comparison.comparators[0], ast.Name)
        or comparison.comparators[0].id != "code"
        or not isinstance(comparison.left, ast.Call)
        or not isinstance(comparison.left.func, ast.Name)
        or comparison.left.func.id != "str"
        or len(comparison.left.args) != 1
        or not isinstance(comparison.left.args[0], ast.Attribute)
        or comparison.left.args[0].attr != "value"
        or not isinstance(comparison.left.args[0].value, ast.Name)
        or comparison.left.args[0].value.id != "exc_info"
        or comparison.left.keywords
    ):
        raise AssertionError(diagnostic)


def _assert_c2b3a_reference_helper_semantics(tree: ast.Module) -> None:
    diagnostic = "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
    bare = _c2b3a_oracle_top_level_function(tree, "_bare_reraise_reference")
    if _c2b3a_oracle_function_parameters(bare) != ("injected_exception",):
        raise AssertionError(diagnostic)
    bare_raises = tuple(node for node in ast.walk(bare) if isinstance(node, ast.Raise))
    if (
        len(tuple(node for node in ast.walk(bare) if isinstance(node, ast.Try))) < 2
        or len(tuple(node for node in bare_raises if node.exc is None)) != 1
        or any(node.cause is not None for node in bare_raises)
    ):
        raise AssertionError(diagnostic)

    relational = _c2b3a_oracle_top_level_function(
        tree,
        "_relational_process_control_reference",
    )
    if _c2b3a_oracle_function_parameters(relational) != ("primary", "secondary"):
        raise AssertionError(diagnostic)
    relational_raises = tuple(
        node for node in ast.walk(relational) if isinstance(node, ast.Raise)
    )
    named_raise_inputs = tuple(
        node.exc.id
        for node in relational_raises
        if isinstance(node.exc, ast.Name)
    )
    if (
        len(tuple(node for node in ast.walk(relational) if isinstance(node, ast.Try))) < 2
        or named_raise_inputs != ("primary", "secondary")
        or len(tuple(node for node in relational_raises if node.exc is None)) != 1
        or any(node.cause is not None for node in relational_raises)
    ):
        raise AssertionError(diagnostic)
    forbidden_graph_stores = {
        "__cause__",
        "__context__",
        "__suppress_context__",
        "__traceback__",
        "__notes__",
    }
    for node in ast.walk(relational):
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            if node.attr in forbidden_graph_stores:
                raise AssertionError(diagnostic)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"with_traceback", "add_note"}:
                raise AssertionError(diagnostic)
    returns = tuple(node for node in ast.walk(relational) if isinstance(node, ast.Return))
    if len(returns) != 1 or not isinstance(returns[0].value, ast.Dict):
        raise AssertionError(diagnostic)
    returned_source = ast.unparse(returns[0].value)
    for required in (
        "'provided_primary': primary",
        "'provided_secondary': secondary",
        "'outward_primary': outward_primary",
        "'entered': entered",
        "'completed': completed",
        "'exact_interpreter_graph_promise': False",
    ):
        if required not in returned_source:
            raise AssertionError(diagnostic)

    graph_walk = _c2b3a_oracle_top_level_function(
        tree,
        "_exception_graph_identity_walk",
    )
    if (
        _c2b3a_oracle_function_parameters(graph_walk) != ("exception",)
        or not any(isinstance(node, ast.While) for node in ast.walk(graph_walk))
        or not any(isinstance(node, ast.Continue) for node in ast.walk(graph_walk))
    ):
        raise AssertionError(diagnostic)
    graph_returns = tuple(
        node for node in ast.walk(graph_walk) if isinstance(node, ast.Return)
    )
    if (
        len(graph_returns) != 1
        or not isinstance(graph_returns[0].value, ast.Name)
        or graph_returns[0].value.id != "seen"
    ):
        raise AssertionError(diagnostic)

    cleanup = _c2b3a_oracle_top_level_function(tree, "_cleanup_reference")
    if _c2b3a_oracle_function_parameters(cleanup) != (
        "initial_state",
        "fault_step",
        "fault_position",
        "connection_outcome",
        "unlock_outcome",
        "descriptor_close_outcome",
        "finalizer",
        "cleanup_outcome",
        "earlier_primary",
    ):
        raise AssertionError(diagnostic)
    cleanup_source = ast.unparse(cleanup)
    ordered_steps = (
        "P0",
        "C1",
        "C2",
        "R1",
        "R2",
        "R3",
        "L1",
        "H1",
        "H2",
        "T1",
        "H3",
    )
    entered_positions: list[int] = []
    completed_positions: list[int] = []
    for step in ordered_steps:
        if (
            f"entered += ('{step}',)" not in cleanup_source
            or f"completed += ('{step}',)" not in cleanup_source
        ):
            raise AssertionError(diagnostic)
        entered_positions.append(cleanup_source.index(f"entered += ('{step}',)"))
        completed_positions.append(cleanup_source.index(f"completed += ('{step}',)"))
    if entered_positions != sorted(entered_positions):
        raise AssertionError(diagnostic)
    if completed_positions != sorted(completed_positions):
        raise AssertionError(diagnostic)
    if any(
        entered_position >= completed_position
        for entered_position, completed_position in zip(
            entered_positions,
            completed_positions,
            strict=True,
        )
    ):
        raise AssertionError(diagnostic)

    def exact_assignments(name: str, value: object) -> tuple[ast.Assign, ...]:
        return tuple(
            node
            for node in ast.walk(cleanup)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == name
            and isinstance(node.value, ast.Constant)
            and node.value.value == value
        )

    admission_closed = exact_assignments("admission_open", False)
    connection_proved = exact_assignments("connection_closed_proved", True)
    connection_custody_cleared = exact_assignments("connection_owned", False)
    credential_revoked = exact_assignments("credential_authority", False)
    mutation_slot_cleared = exact_assignments("mutation_slot_owned", False)
    database_binding_cleared = exact_assignments("database_binding_owned", False)
    release_proved = exact_assignments("writer_lock_release", "release_proved")
    descriptor_custody_cleared = exact_assignments("descriptor_owned", False)
    authority_terminal = exact_assignments("authority_lock_terminal", True)
    authority_registry_removed = exact_assignments(
        "authority_lock_registry_present",
        False,
    )
    X_published = exact_assignments("state", "X")
    session_registry_removed = exact_assignments(
        "writer_session_registry_present",
        False,
    )
    if not (
        len(admission_closed) == 1
        and len(connection_proved) == 1
        and len(connection_custody_cleared) == 1
        and len(credential_revoked) == 1
        and len(mutation_slot_cleared) == 1
        and len(database_binding_cleared) == 1
        and len(release_proved) == 1
        and len(descriptor_custody_cleared) == 1
        and len(authority_terminal) == 1
        and len(authority_registry_removed) == 1
        and len(X_published) == 1
        and len(session_registry_removed) == 1
        and admission_closed[0].lineno < connection_proved[0].lineno
        and connection_proved[0].lineno < credential_revoked[0].lineno
        and credential_revoked[0].lineno < mutation_slot_cleared[0].lineno
        and mutation_slot_cleared[0].lineno < database_binding_cleared[0].lineno
        and database_binding_cleared[0].lineno < release_proved[0].lineno
        and release_proved[0].lineno < descriptor_custody_cleared[0].lineno
        and descriptor_custody_cleared[0].lineno < authority_terminal[0].lineno
        and authority_terminal[0].lineno < authority_registry_removed[0].lineno
        and authority_registry_removed[0].lineno < X_published[0].lineno
        and X_published[0].lineno < session_registry_removed[0].lineno
    ):
        raise AssertionError(diagnostic)
    for required in (
        "admission_open = initial_state == 'A'",
        "wrapper_reachable = not finalizer",
        "retry_reachable = not finalizer",
        "if fault_step == 'P0' and fault_position == 'before' and (not finalizer):",
        "else:\n        admission_open = False\n        if state == 'A':\n            state = 'A-closing'",
        "if not halted and initial_state in ('QU', 'QK'):\n        entered += ('C1',)",
        "if connection_outcome == 'normal':\n                completed += ('C1',)\n                entered += ('C2',)\n                connection_closed_proved = True\n                connection_owned = False\n                state = 'PU' if initial_state == 'QU' else 'PK'\n                completed += ('C2',)",
        "assert connection_outcome in ('normal', 'ordinary', 'KeyboardInterrupt', 'SystemExit', 'GeneratorExit')",
        "assert cleanup_outcome in ('normal', 'ordinary', 'KeyboardInterrupt', 'SystemExit', 'GeneratorExit')",
        "assert earlier_primary in ('none', 'KeyboardInterrupt', 'SystemExit', 'GeneratorExit')",
        "if earlier_primary != 'none':\n            selected_outward = 'commit_' + earlier_primary",
        "selected_outward = 'cleanup_' + effective_cleanup_outcome",
        "cleanup_failure_suppressed = halted and (finalizer or earlier_primary != 'none' or effective_cleanup_outcome == 'ordinary')",
        "assert not (connection_closed_proved and (state in ('QU', 'QK') or connection_owned))",
        "assert not (state in ('PU', 'PK') and connection_owned)",
        "assert not (finalizer and (not wrapper_reachable) and admission_open)",
    ):
        if required not in cleanup_source:
            raise AssertionError(diagnostic)

    selection_indexes = tuple(
        index
        for index, statement in enumerate(cleanup.body)
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "selected_outward"
        and isinstance(statement.value, ast.Constant)
        and statement.value.value == "none"
    )
    if len(selection_indexes) != 1:
        raise AssertionError(diagnostic)
    selection_index = selection_indexes[0]
    if selection_index + 1 >= len(cleanup.body):
        raise AssertionError(diagnostic)
    finalizer_gate = cleanup.body[selection_index + 1]
    if (
        not isinstance(finalizer_gate, ast.If)
        or not isinstance(finalizer_gate.test, ast.UnaryOp)
        or not isinstance(finalizer_gate.test.op, ast.Not)
        or not isinstance(finalizer_gate.test.operand, ast.Name)
        or finalizer_gate.test.operand.id != "finalizer"
        or finalizer_gate.orelse
        or len(finalizer_gate.body) != 1
        or not isinstance(finalizer_gate.body[0], ast.If)
    ):
        raise AssertionError(diagnostic)
    primary_gate = finalizer_gate.body[0]
    if (
        not isinstance(primary_gate.test, ast.Compare)
        or not isinstance(primary_gate.test.left, ast.Name)
        or primary_gate.test.left.id != "earlier_primary"
        or len(primary_gate.test.ops) != 1
        or not isinstance(primary_gate.test.ops[0], ast.NotEq)
        or len(primary_gate.test.comparators) != 1
        or not isinstance(primary_gate.test.comparators[0], ast.Constant)
        or primary_gate.test.comparators[0].value != "none"
        or len(primary_gate.body) != 1
        or len(primary_gate.orelse) != 1
        or not isinstance(primary_gate.orelse[0], ast.If)
    ):
        raise AssertionError(diagnostic)
    cleanup_gate = primary_gate.orelse[0]
    expected_primary_assignment = "selected_outward = 'commit_' + earlier_primary"
    expected_cleanup_test = "halted and effective_cleanup_outcome in ('KeyboardInterrupt', 'SystemExit', 'GeneratorExit')"
    expected_cleanup_assignment = "selected_outward = 'cleanup_' + effective_cleanup_outcome"
    if (
        ast.unparse(primary_gate.body[0]) != expected_primary_assignment
        or ast.unparse(cleanup_gate.test) != expected_cleanup_test
        or len(cleanup_gate.body) != 1
        or cleanup_gate.orelse
        or ast.unparse(cleanup_gate.body[0]) != expected_cleanup_assignment
    ):
        raise AssertionError(diagnostic)
    cleanup_result = _c2b3a_oracle_top_level_function(
        tree,
        "_cleanup_reference_result",
    )
    cleanup_result_source = ast.unparse(cleanup_result)
    for required in (
        "'X': state == 'X'",
        "'recovery_admitted': state == 'X'",
        "'replay_admitted': state == 'X'",
        "'new_operation_admitted': state == 'X'",
        "'admission_open': admission_open",
        "'wrapper_reachable': wrapper_reachable",
        "'ordinary_closing': ordinary_closing",
        "'connection_owned': connection_owned",
        "'connection_closed_proved': connection_closed_proved",
        "'credential_authority': credential_authority",
        "'mutation_slot_owned': mutation_slot_owned",
        "'database_binding_owned': database_binding_owned",
        "'finalizer_attempted': finalizer_attempted",
        "'retry_reachable': retry_reachable",
        "'effective_cleanup_outcome': effective_cleanup_outcome",
        "'selected_outward': selected_outward",
        "'cleanup_failure_suppressed': cleanup_failure_suppressed",
    ):
        if required not in cleanup_result_source:
            raise AssertionError(diagnostic)
        cleanup_returns = tuple(
            node for node in ast.walk(cleanup) if isinstance(node, ast.Return)
        )
        cleanup_return_value = (
            cleanup_returns[0].value if len(cleanup_returns) == 1 else None
        )
        if (
            len(cleanup_returns) != 1
            or not isinstance(cleanup_return_value, ast.Subscript)
            or not isinstance(cleanup_return_value.ctx, ast.Load)
            or not isinstance(cleanup_return_value.slice, ast.Constant)
            or cleanup_return_value.slice.value != "safe_projection"
            or not isinstance(cleanup_return_value.value, ast.Call)
            or not isinstance(cleanup_return_value.value.func, ast.Name)
            or cleanup_return_value.value.func.id != "_cleanup_reference_result"
        ):
            raise AssertionError(diagnostic)
    returned_keywords = {
        keyword.arg for keyword in cleanup_return_value.value.keywords
    }
    if not {
        "state",
        "entered",
        "completed",
        "admission_open",
        "wrapper_reachable",
        "ordinary_closing",
        "connection_owned",
        "connection_closed_proved",
        "credential_authority",
        "mutation_slot_owned",
        "database_binding_owned",
        "writer_lock_release",
        "descriptor_outcome",
        "descriptor_owned",
        "retry_reachable",
        "effective_cleanup_outcome",
        "selected_outward",
        "cleanup_failure_suppressed",
        "authority_lock_registry_present",
        "writer_session_registry_present",
    }.issubset(returned_keywords):
        raise AssertionError(diagnostic)


def _assert_c2b3a_mutant_dataflow_semantics(tree: ast.Module) -> None:
    diagnostic = "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
    expected_m16_m65_ids = (
        "M16", "M17", "M18", "M19", "M20", "M21", "M22", "M23", "M24",
        "M25", "M26", "M27", "M28", "M29", "M30",
        "M31", "M32", "M33", "M34", "M35", "M36", "M37", "M38", "M39",
        "M40", "M41", "M42", "M43", "M44", "M45", "M46", "M47", "M48",
        "M49", "M50", "M51", "M52", "M53", "M54", "M55", "M56", "M57",
        "M58", "M59", "M60", "M61", "M62", "M63", "M64", "M65",
    )
    if (
        tuple(mutant_id for mutant_id, _name in C2B3A_LINEAR_MUTANT_FUNCTIONS)
        != expected_m16_m65_ids
        or tuple(C2B3A_M16_M65_EXPECTED_MUTATION_SOURCE)
        != expected_m16_m65_ids
    ):
        raise AssertionError(diagnostic)

    expected_names = tuple(name for _mutant_id, name in C2B3A_LINEAR_MUTANT_FUNCTIONS)
    observed_named_functions = tuple(
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("test_commit_close_mutant_m")
    )
    if observed_named_functions != expected_names:
        raise AssertionError(diagnostic)
    expected_name_set = set(expected_names)
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        parameter_names = {
            argument.arg
            for argument in (
                tuple(node.args.posonlyargs)
                + tuple(node.args.args)
                + tuple(node.args.kwonlyargs)
            )
        }
        if "mutant_id" in parameter_names:
            raise AssertionError(diagnostic)
        if (
            node.name.startswith("test_commit_close_")
            and "mutant" in node.name
            and node.name not in expected_name_set
        ):
            raise AssertionError(diagnostic)

    def is_exact_candidate_factory(statement: ast.stmt) -> bool:
        return (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == "candidate"
            and isinstance(statement.targets[0].ctx, ast.Store)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id == "_candidate"
            and not statement.value.args
            and not statement.value.keywords
        )

    def is_exact_terminal_validation(statement: ast.stmt) -> bool:
        if not isinstance(statement, ast.Expr):
            return False
        call = statement.value
        return (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "_expect_violation"
            and len(call.args) == 2
            and isinstance(call.args[0], ast.Name)
            and call.args[0].id == "candidate"
            and isinstance(call.args[0].ctx, ast.Load)
            and isinstance(call.args[1], ast.Constant)
            and call.args[1].value == "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID"
            and not call.keywords
        )

    signatures: dict[str, tuple[str, ...]] = {}
    namespace: dict[str, object] = {
        "__file__": str(C2B3A_ORACLE_PATH),
        "__name__": "c2b3a_mutant_efficacy_probe",
    }
    try:
        exec(
            compile(tree, filename=str(C2B3A_ORACLE_PATH), mode="exec"),
            namespace,
        )
        original_validate = namespace["_validate_contract"]
    except BaseException:
        raise AssertionError(diagnostic) from None
    original_candidate = namespace.get("_candidate")
    original_expect_violation = namespace.get("_expect_violation")
    direct_deepcopy = namespace.get("deepcopy")
    contract_violation = namespace.get("_ContractViolation")
    if not (
        callable(original_candidate)
        and callable(original_validate)
        and callable(original_expect_violation)
        and callable(direct_deepcopy)
        and isinstance(contract_violation, type)
        and issubclass(contract_violation, Exception)
    ):
        raise AssertionError(diagnostic)

    execution_totals: dict[str, int] = {
        "mapping_entries": 0,
        "valid_baselines": 0,
        "mutant_invocations": 0,
        "changed_candidates": 0,
        "identical_candidate_terminals": 0,
        "single_terminal_reaches": 0,
        "exact_supplied_diagnostics": 0,
        "exact_validator_diagnostics": 0,
    }

    for mutant_id, function_name in C2B3A_LINEAR_MUTANT_FUNCTIONS:
        mutant_function = namespace.get(function_name)
        if not callable(mutant_function):
            raise AssertionError(diagnostic)
        expected_diagnostic = "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID"
        controlled_candidate = original_candidate()
        valid_baseline = direct_deepcopy(controlled_candidate)
        if namespace["_validate_contract"] is not original_validate:
            raise AssertionError(diagnostic)
        try:
            original_validate(controlled_candidate)
        except BaseException:
            raise AssertionError(diagnostic) from None
        execution_totals["mapping_entries"] += 1
        execution_totals["valid_baselines"] += 1
        execution: dict[str, object] = {
            "candidate_factory_calls": 0,
            "mutant_calls": 0,
            "terminal_calls": 0,
            "identical_candidate": False,
            "supplied_diagnostic": None,
            "validator_diagnostic": None,
        }

        def instrumented_candidate() -> object:
            execution["candidate_factory_calls"] = (
                int(execution["candidate_factory_calls"]) + 1
            )
            if execution["candidate_factory_calls"] != 1:
                raise AssertionError(diagnostic)
            return controlled_candidate

        def instrumented_expect_violation(
            candidate: object,
            supplied_diagnostic: object,
        ) -> None:
            execution["terminal_calls"] = int(execution["terminal_calls"]) + 1
            if execution["terminal_calls"] != 1:
                raise AssertionError(diagnostic)
            execution["identical_candidate"] = candidate is controlled_candidate
            execution["supplied_diagnostic"] = supplied_diagnostic
            if candidate is not controlled_candidate:
                raise AssertionError(diagnostic)
            if supplied_diagnostic != expected_diagnostic:
                raise AssertionError(diagnostic)
            if namespace["_validate_contract"] is not original_validate:
                raise AssertionError(diagnostic)
            with pytest.raises(contract_violation) as exc_info:
                original_validate(candidate)
            execution["validator_diagnostic"] = str(exc_info.value)
            if execution["validator_diagnostic"] != expected_diagnostic:
                raise AssertionError(diagnostic)

        namespace["_candidate"] = instrumented_candidate
        namespace["_expect_violation"] = instrumented_expect_violation
        try:
            execution["mutant_calls"] = int(execution["mutant_calls"]) + 1
            mutant_function()
        except BaseException:
            raise AssertionError(diagnostic) from None
        finally:
            namespace["_candidate"] = original_candidate
            namespace["_expect_violation"] = original_expect_violation

        if (
            namespace.get("_candidate") is not original_candidate
            or namespace.get("_expect_violation") is not original_expect_violation
        ):
            raise AssertionError(diagnostic)
        if controlled_candidate == valid_baseline:
            raise AssertionError(diagnostic)
        if (
            execution["candidate_factory_calls"] != 1
            or execution["mutant_calls"] != 1
            or execution["terminal_calls"] != 1
            or execution["identical_candidate"] is not True
            or execution["supplied_diagnostic"] != expected_diagnostic
            or execution["validator_diagnostic"] != expected_diagnostic
        ):
            raise AssertionError(diagnostic)

        execution_totals["mutant_invocations"] += 1
        execution_totals["changed_candidates"] += 1
        execution_totals["identical_candidate_terminals"] += 1
        execution_totals["single_terminal_reaches"] += 1
        execution_totals["exact_supplied_diagnostics"] += 1
        execution_totals["exact_validator_diagnostics"] += 1

        function = _c2b3a_oracle_top_level_function(tree, function_name)
        expected_mutations = C2B3A_M16_M65_EXPECTED_MUTATION_SOURCE[mutant_id]
        if (
            _c2b3a_oracle_function_parameters(function)
            or function.decorator_list
            or len(function.body) != len(expected_mutations) + 2
            or not is_exact_candidate_factory(function.body[0])
            or not is_exact_terminal_validation(function.body[-1])
        ):
            raise AssertionError(diagnostic)
        mutations = function.body[1:-1]
        mutation_source = tuple(ast.unparse(statement) for statement in mutations)
        if mutation_source != expected_mutations:
            raise AssertionError(diagnostic)
        for statement in mutations:
            if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
                raise AssertionError(diagnostic)
            names = tuple(node for node in ast.walk(statement) if isinstance(node, ast.Name))
            if not names or any(node.id != "candidate" for node in names):
                raise AssertionError(diagnostic)
        calls = tuple(node for node in ast.walk(function) if isinstance(node, ast.Call))
        candidate_stores = tuple(
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Name)
            and node.id == "candidate"
            and isinstance(node.ctx, ast.Store)
        )
        if (
            len(calls) != 2
            or len(candidate_stores) != 1
            or calls[0] is not function.body[0].value
            or calls[1] is not function.body[-1].value
        ):
            raise AssertionError(diagnostic)
        signatures[mutant_id] = mutation_source

    if tuple(signatures) != expected_m16_m65_ids:
        raise AssertionError(diagnostic)
    if signatures != C2B3A_M16_M65_EXPECTED_MUTATION_SOURCE:
        raise AssertionError(diagnostic)
    if len(set(signatures.values())) != len(expected_m16_m65_ids):
        raise AssertionError(diagnostic)
    if execution_totals != {
        "mapping_entries": 50,
        "valid_baselines": 50,
        "mutant_invocations": 50,
        "changed_candidates": 50,
        "identical_candidate_terminals": 50,
        "single_terminal_reaches": 50,
        "exact_supplied_diagnostics": 50,
        "exact_validator_diagnostics": 50,
    }:
        raise AssertionError(diagnostic)


def _assert_c2b3a_mutant_efficacy_checker_structure(source: str) -> None:
    diagnostic = "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
    try:
        tree = ast.parse(
            source,
            filename=Path(__file__).name,
            type_comments=True,
        )
    except SyntaxError:
        raise AssertionError(diagnostic) from None
    contract = C2B3A_MUTANT_EFFICACY_CHECKER_CONTRACT
    expected_outer_header = (
        ("node_type", "FunctionDef"),
        ("name", "_assert_c2b3a_mutant_dataflow_semantics"),
        ("decorators", ()),
        ("return_annotation", ("Constant", None, None)),
        ("type_comment", None),
        ("type_params", ()),
        ("posonlyargs", ()),
        (
            "args",
            (
                (
                    "tree",
                    (
                        "Attribute",
                        ("Name", "ast", "Load"),
                        "Module",
                        "Load",
                    ),
                    None,
                ),
            ),
        ),
        ("defaults", ()),
        ("vararg", None),
        ("kwonlyargs", ()),
        ("kw_defaults", ()),
        ("kwarg", None),
    )
    expected_assurance_boundary = {
        "classification": "bounded exact-byte self-test assurance",
        "in_scope_guarantees": (
            "the exact checked-in efficacy function header and body match the independently authored bounded AST/dataflow grammar",
            "the exact checked-in function has no local or lexical binding of exec",
            "the exact checked-in module has no ordinary lexical module binding of exec that changes the efficacy function resolution",
            "the exact checked-in source contains no directly recognized source-local module-dictionary replacement of exec",
            "the exact checked-in source contains no wildcard import capable of supplying exec",
            "the efficacy function in-function namespace, immediate validator capture, baseline validation, terminal validation, one-mutant invocation, restoration, and aggregate behavior retain their existing exact protections",
            "runtime instrumentation on the exact audited bytes observes builtins.exec as the callable used by the checked execution path",
            "runtime instrumentation observes 100 calls to the exec-produced validator and zero calls to an alternate validator",
        ),
        "explicit_non_claims": (
            "resistance to malicious coordinated editing of both the efficacy checker and its higher-order guard",
            "resistance to mutation of builtins.exec or the builtins object",
            "resistance to mutation through __builtins__",
            "resistance to a pre-poisoned or malicious sys.modules environment",
            "resistance to mutation of imported module objects",
            "resistance to custom import hooks or loaders",
            "resistance to tracing, profiling, debugger, coverage, or interpreter instrumentation that changes execution",
            "resistance to hostile monkeypatching performed outside the bounded source-local forms",
            "resistance to arbitrary Python metaprogramming",
            "resistance to process or interpreter compromise",
        ),
        "external_assurance_chain": (
            "exact patch provenance",
            "fresh independent read-only audit",
            "staged-blob equality",
            "committed-blob equality",
            "Git object and ref truth",
        ),
        "external_assurance_role": (
            "provenance and audit are external assurance mechanisms, not semantics "
            "owned by this test"
        ),
    }
    if (
        type(contract) is not dict
        or tuple(contract) != (
            "function_name",
            "assurance_boundary_name",
            "outer_function_header",
            "module_lexical_exec_binding_inventory",
            "module_lexical_ast_binding_inventory",
            "module_wildcard_import_inventory",
            "direct_source_local_module_dictionary_operation_inventory",
            "mapping_source_name",
            "ordered_mutant_ids",
            "candidate_factory_name",
            "validator_name",
            "contract_exception_name",
            "terminal_helper_name",
            "execution_namespace_name",
            "captured_validator_name",
            "validator_namespace_key",
            "namespace_construction_source",
            "exec_capture_try_source",
            "pre_mapping_loop_statement_sources",
            "protected_binding_names",
            "protected_binding_inventory",
            "namespace_subscript_inventory",
            "namespace_get_inventory",
            "loop_target_names",
            "execution_record_fields",
            "aggregate_record_fields",
            "function_top_level_statement_kinds",
            "mapping_loop_statement_kinds",
            "mapping_loop_statement_sources",
            "post_loop_statement_sources",
        )
        or contract["function_name"]
        != "_assert_c2b3a_mutant_dataflow_semantics"
        or contract["assurance_boundary_name"]
        != "C2B3A_EFFICACY_GUARD_ASSURANCE_BOUNDARY"
        or contract["outer_function_header"] != expected_outer_header
        or contract["module_lexical_exec_binding_inventory"] != ()
        or contract["module_lexical_ast_binding_inventory"]
        != (("import_alias", 1),)
        or contract["module_wildcard_import_inventory"] != ()
        or contract[
            "direct_source_local_module_dictionary_operation_inventory"
        ]
        != ()
        or contract["mapping_source_name"] != "C2B3A_LINEAR_MUTANT_FUNCTIONS"
        or contract["candidate_factory_name"] != "_candidate"
        or contract["validator_name"] != "_validate_contract"
        or contract["contract_exception_name"] != "_ContractViolation"
        or contract["terminal_helper_name"] != "_expect_violation"
        or contract["execution_namespace_name"] != "namespace"
        or contract["captured_validator_name"] != "original_validate"
        or contract["validator_namespace_key"] != "_validate_contract"
        or len(contract["ordered_mutant_ids"]) != 50
        or tuple(mutant_id for mutant_id, _name in C2B3A_LINEAR_MUTANT_FUNCTIONS)
        != contract["ordered_mutant_ids"]
    ):
        raise AssertionError(diagnostic)
    boundary_assignments = tuple(
        statement
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == contract["assurance_boundary_name"]
    )
    if len(boundary_assignments) != 1:
        raise AssertionError(diagnostic)
    boundary_assignment = boundary_assignments[0]
    if (
        not isinstance(boundary_assignment.value, ast.Dict)
        or not _c2b3a_oracle_closed_literal(boundary_assignment.value)
    ):
        raise AssertionError(diagnostic)
    try:
        observed_assurance_boundary = ast.literal_eval(boundary_assignment.value)
    except (TypeError, ValueError):
        raise AssertionError(diagnostic) from None
    if (
        type(C2B3A_EFFICACY_GUARD_ASSURANCE_BOUNDARY) is not dict
        or tuple(C2B3A_EFFICACY_GUARD_ASSURANCE_BOUNDARY)
        != tuple(expected_assurance_boundary)
        or C2B3A_EFFICACY_GUARD_ASSURANCE_BOUNDARY
        != expected_assurance_boundary
        or type(observed_assurance_boundary) is not dict
        or tuple(observed_assurance_boundary) != tuple(expected_assurance_boundary)
        or observed_assurance_boundary != expected_assurance_boundary
    ):
        raise AssertionError(diagnostic)
    matches = tuple(
        statement
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        and statement.name == contract["function_name"]
    )
    if len(matches) != 1:
        raise AssertionError(diagnostic)
    function = matches[0]
    header = _c2b3a_oracle_function_header(function)
    ordinary_arguments = header["args"]
    if (
        tuple(header)
        != (
            "node_type",
            "name",
            "decorators",
            "return_annotation",
            "type_comment",
            "type_params",
            "posonlyargs",
            "args",
            "defaults",
            "vararg",
            "kwonlyargs",
            "kw_defaults",
            "kwarg",
        )
        or header["node_type"] is not ast.FunctionDef
        or header["name"] != "_assert_c2b3a_mutant_dataflow_semantics"
        or header["decorators"] != ()
        or header["type_comment"] is not None
        or header["type_params"] != ()
        or header["posonlyargs"] != ()
        or type(ordinary_arguments) is not tuple
        or len(ordinary_arguments) != 1
        or header["defaults"] != ()
        or header["vararg"] is not None
        or header["kwonlyargs"] != ()
        or header["kw_defaults"] != ()
        or header["kwarg"] is not None
        or type(function.args) is not ast.arguments
    ):
        raise AssertionError(diagnostic)
    tree_argument = ordinary_arguments[0]
    tree_annotation = tree_argument.annotation
    return_annotation = header["return_annotation"]
    if (
        type(tree_argument) is not ast.arg
        or tree_argument.arg != "tree"
        or tree_argument.type_comment is not None
        or type(tree_annotation) is not ast.Attribute
        or tree_annotation.attr != "Module"
        or type(tree_annotation.ctx) is not ast.Load
        or type(tree_annotation.value) is not ast.Name
        or tree_annotation.value.id != "ast"
        or type(tree_annotation.value.ctx) is not ast.Load
        or type(return_annotation) is not ast.Constant
        or return_annotation.value is not None
        or return_annotation.kind is not None
    ):
        raise AssertionError(diagnostic)
    first_statement = tree.body[0] if tree.body else None
    if (
        not isinstance(first_statement, ast.Import)
        or len(first_statement.names) != 1
        or first_statement.names[0].name != "ast"
        or first_statement.names[0].asname is not None
        or _c2b3a_oracle_module_name_bindings(tree, "exec")
        != contract["module_lexical_exec_binding_inventory"]
        or _c2b3a_oracle_module_name_bindings(tree, "ast")
        != contract["module_lexical_ast_binding_inventory"]
        or _c2b3a_oracle_module_wildcard_imports(tree)
        != contract["module_wildcard_import_inventory"]
        or _c2b3a_oracle_direct_module_dictionary_operations(tree)
        != contract[
            "direct_source_local_module_dictionary_operation_inventory"
        ]
    ):
        raise AssertionError(diagnostic)

    if (
        tuple(contract["protected_binding_names"])
        != (
            "namespace",
            "original_validate",
            "original_candidate",
            "original_expect_violation",
            "controlled_candidate",
            "instrumented_candidate",
            "instrumented_expect_violation",
            "candidate",
            "supplied_diagnostic",
            "exec",
        )
        or len(function.body) != len(contract["function_top_level_statement_kinds"])
        or tuple(ast.unparse(statement) for statement in function.body[:19])
        != contract["pre_mapping_loop_statement_sources"]
    ):
        raise AssertionError(diagnostic)

    callability_if = function.body[17]
    if (
        not isinstance(callability_if, ast.If)
        or ast.unparse(callability_if)
        != contract["pre_mapping_loop_statement_sources"][17]
        or len(callability_if.body) != 1
        or not isinstance(callability_if.body[0], ast.Raise)
        or ast.unparse(callability_if.body[0])
        != "raise AssertionError(diagnostic)"
        or callability_if.orelse
    ):
        raise AssertionError(diagnostic)

    forbidden_pattern_nodes = (
        ast.Match,
        ast.MatchAs,
        ast.MatchClass,
        ast.MatchMapping,
        ast.MatchOr,
        ast.MatchSequence,
        ast.MatchSingleton,
        ast.MatchStar,
        ast.MatchValue,
    )
    if any(
        isinstance(node, forbidden_pattern_nodes)
        for node in ast.walk(function)
    ):
        raise AssertionError(diagnostic)

    protected_binding_names = set(contract["protected_binding_names"])
    protected_bindings: list[tuple[str, str]] = []
    for node in ast.walk(function):
        if (
            isinstance(node, ast.Name)
            and node.id in protected_binding_names
            and isinstance(node.ctx, (ast.Store, ast.Del))
        ):
            protected_bindings.append(
                (
                    node.id,
                    "name_store" if isinstance(node.ctx, ast.Store) else "name_delete",
                )
            )
        elif (
            isinstance(node, ast.arg)
            and node.arg in protected_binding_names
        ):
            protected_bindings.append((node.arg, "argument"))
        elif (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node is not function
            and node.name in protected_binding_names
        ):
            protected_bindings.append((node.name, "function_definition"))
        elif (
            isinstance(node, ast.ClassDef)
            and node.name in protected_binding_names
        ):
            protected_bindings.append((node.name, "class_definition"))
        elif isinstance(node, ast.alias):
            bound_name = node.asname or node.name.split(".", 1)[0]
            if bound_name in protected_binding_names:
                protected_bindings.append((bound_name, "import_alias"))
        elif (
            isinstance(node, ast.ExceptHandler)
            and node.name in protected_binding_names
        ):
            protected_bindings.append((node.name, "exception_handler"))
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            protected_bindings.extend(
                (name, type(node).__name__.lower())
                for name in node.names
                if name in protected_binding_names
            )
        elif isinstance(node, ast.MatchAs) and node.name in protected_binding_names:
            protected_bindings.append((node.name, "match_as"))
        elif isinstance(node, ast.MatchStar) and node.name in protected_binding_names:
            protected_bindings.append((node.name, "match_star"))
        elif (
            isinstance(node, ast.MatchMapping)
            and node.rest in protected_binding_names
        ):
            protected_bindings.append((node.rest, "match_mapping_rest"))
    if tuple(sorted(protected_bindings)) != contract["protected_binding_inventory"]:
        raise AssertionError(diagnostic)

    parents = {
        child: parent
        for parent in ast.walk(function)
        for child in ast.iter_child_nodes(parent)
    }

    def enclosing_function_name(node: ast.AST) -> str:
        current = parents.get(node)
        while current is not None:
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return current.name
            current = parents.get(current)
        raise AssertionError(diagnostic)

    def enclosing_statement_source(node: ast.AST) -> str:
        current = parents.get(node)
        while current is not None:
            if isinstance(current, ast.stmt):
                return ast.unparse(current)
            current = parents.get(current)
        raise AssertionError(diagnostic)

    namespace_name = contract["execution_namespace_name"]
    captured_validator_name = contract["captured_validator_name"]
    validator_namespace_key = contract["validator_namespace_key"]
    namespace_constructions = tuple(
        statement
        for statement in function.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and statement.target.id == namespace_name
        and isinstance(statement.target.ctx, ast.Store)
    )
    exec_calls = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "exec"
    )
    compile_calls = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "compile"
    )
    if (
        len(namespace_constructions) != 1
        or len(exec_calls) != 1
        or len(compile_calls) != 1
    ):
        raise AssertionError(diagnostic)
    namespace_construction = namespace_constructions[0]
    try:
        namespace_index = function.body.index(namespace_construction)
        exec_capture_try = function.body[namespace_index + 1]
    except (IndexError, ValueError):
        raise AssertionError(diagnostic) from None
    if (
        ast.unparse(namespace_construction)
        != contract["namespace_construction_source"]
        or not isinstance(exec_capture_try, ast.Try)
        or ast.unparse(exec_capture_try) != contract["exec_capture_try_source"]
        or len(exec_capture_try.body) != 2
        or len(exec_capture_try.handlers) != 1
        or exec_capture_try.orelse
        or exec_capture_try.finalbody
    ):
        raise AssertionError(diagnostic)
    exec_statement, validator_capture = exec_capture_try.body
    handler = exec_capture_try.handlers[0]
    if (
        not isinstance(exec_statement, ast.Expr)
        or exec_statement.value is not exec_calls[0]
        or not isinstance(handler.type, ast.Name)
        or handler.type.id != "BaseException"
        or handler.name is not None
        or len(handler.body) != 1
        or ast.unparse(handler.body[0])
        != "raise AssertionError(diagnostic) from None"
    ):
        raise AssertionError(diagnostic)
    exec_call = exec_calls[0]
    compile_call = compile_calls[0]
    if (
        len(exec_call.args) != 2
        or type(exec_call.func) is not ast.Name
        or exec_call.func.id != "exec"
        or type(exec_call.func.ctx) is not ast.Load
        or exec_call.args[0] is not compile_call
        or not isinstance(exec_call.args[1], ast.Name)
        or exec_call.args[1].id != namespace_name
        or not isinstance(exec_call.args[1].ctx, ast.Load)
        or exec_call.keywords
        or ast.unparse(exec_call)
        != "exec(compile(tree, filename=str(C2B3A_ORACLE_PATH), mode='exec'), "
        "namespace)"
        or not isinstance(validator_capture, ast.Assign)
        or len(validator_capture.targets) != 1
        or not isinstance(validator_capture.targets[0], ast.Name)
        or validator_capture.targets[0].id != captured_validator_name
        or not isinstance(validator_capture.targets[0].ctx, ast.Store)
        or not isinstance(validator_capture.value, ast.Subscript)
        or not isinstance(validator_capture.value.value, ast.Name)
        or validator_capture.value.value.id != namespace_name
        or not isinstance(validator_capture.value.value.ctx, ast.Load)
        or not isinstance(validator_capture.value.slice, ast.Constant)
        or validator_capture.value.slice.value != validator_namespace_key
        or not isinstance(validator_capture.value.ctx, ast.Load)
    ):
        raise AssertionError(diagnostic)

    namespace_subscripts = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == namespace_name
        and isinstance(node.value.ctx, ast.Load)
    )
    observed_namespace_subscripts = tuple(
        sorted(
            (
                enclosing_function_name(node),
                enclosing_statement_source(node),
                ast.unparse(node),
                type(node.ctx).__name__,
            )
            for node in namespace_subscripts
        )
    )
    if (
        observed_namespace_subscripts
        != contract["namespace_subscript_inventory"]
        or any(
            isinstance(node.ctx, (ast.Store, ast.Del))
            and (
                not isinstance(node.slice, ast.Constant)
                or type(node.slice.value) is not str
            )
            for node in namespace_subscripts
        )
        or any(
            isinstance(node.ctx, (ast.Store, ast.Del))
            and isinstance(node.slice, ast.Constant)
            and node.slice.value == validator_namespace_key
            for node in namespace_subscripts
        )
    ):
        raise AssertionError(diagnostic)

    namespace_method_calls = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == namespace_name
        and isinstance(node.func.value.ctx, ast.Load)
    )
    namespace_get_calls = tuple(
        node for node in namespace_method_calls if node.func.attr == "get"
    )
    observed_namespace_gets = tuple(
        sorted(
            (
                enclosing_function_name(node),
                enclosing_statement_source(node),
                ast.unparse(node),
            )
            for node in namespace_get_calls
        )
    )
    dynamic_namespace_gets = tuple(
        node
        for node in namespace_get_calls
        if len(node.args) != 1
        or node.keywords
        or not isinstance(node.args[0], ast.Constant)
    )
    if (
        namespace_method_calls != namespace_get_calls
        or observed_namespace_gets != contract["namespace_get_inventory"]
        or len(dynamic_namespace_gets) != 1
        or ast.unparse(dynamic_namespace_gets[0])
        != "namespace.get(function_name)"
    ):
        raise AssertionError(diagnostic)

    namespace_loads = {
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Name)
        and node.id == namespace_name
        and isinstance(node.ctx, ast.Load)
    }
    allowed_namespace_loads = {
        *(node.value for node in namespace_subscripts),
        *(node.func.value for node in namespace_get_calls),
        exec_call.args[1],
    }
    if namespace_loads != allowed_namespace_loads:
        raise AssertionError(diagnostic)

    namespace_bindings = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Name)
        and node.id == namespace_name
        and isinstance(node.ctx, (ast.Store, ast.Del))
    )
    captured_validator_bindings = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Name)
        and node.id == captured_validator_name
        and isinstance(node.ctx, (ast.Store, ast.Del))
    )
    hidden_binding_names = tuple(
        node
        for node in ast.walk(function)
        if (
            isinstance(node, ast.arg)
            and node.arg in {namespace_name, captured_validator_name}
        )
        or (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node is not function
            and node.name in {namespace_name, captured_validator_name}
        )
        or (
            isinstance(node, ast.ExceptHandler)
            and node.name in {namespace_name, captured_validator_name}
        )
        or (
            isinstance(node, (ast.Global, ast.Nonlocal))
            and any(
                name in {namespace_name, captured_validator_name}
                for name in node.names
            )
        )
        or (
            isinstance(node, ast.alias)
            and (node.asname or node.name.split(".", 1)[0])
            in {namespace_name, captured_validator_name}
        )
    )
    if (
        namespace_bindings != (namespace_construction.target,)
        or captured_validator_bindings != (validator_capture.targets[0],)
        or hidden_binding_names
    ):
        raise AssertionError(diagnostic)

    namespace_aliases = tuple(
        node
        for node in ast.walk(function)
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Name)
            and node.value.id == namespace_name
        )
        or (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.value, ast.Name)
            and node.value.id == namespace_name
        )
        or (
            isinstance(node, ast.NamedExpr)
            and isinstance(node.value, ast.Name)
            and node.value.id == namespace_name
        )
    )
    validator_key_subscripts = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Subscript)
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == validator_namespace_key
    )
    namespace_mutator_calls = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr
        in {
            "update",
            "__setitem__",
            "__delitem__",
            "setdefault",
            "pop",
            "popitem",
            "clear",
        }
        and any(
            isinstance(descendant, ast.Name)
            and descendant.id == namespace_name
            for descendant in ast.walk(node.func.value)
        )
    )
    calls_receiving_namespace = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and any(
            isinstance(descendant, ast.Name)
            and descendant.id == namespace_name
            for argument in (
                tuple(node.args)
                + tuple(
                    keyword.value
                    for keyword in node.keywords
                    if keyword.arg is not None
                )
            )
            for descendant in ast.walk(argument)
        )
    )
    if (
        namespace_aliases
        or len(validator_key_subscripts) != 3
        or validator_capture.value not in validator_key_subscripts
        or any(
            not isinstance(node.ctx, ast.Load)
            for node in validator_key_subscripts
        )
        or namespace_mutator_calls
        or calls_receiving_namespace != (exec_call,)
    ):
        raise AssertionError(diagnostic)

    if (
        tuple(type(statement).__name__ for statement in function.body)
        != contract["function_top_level_statement_kinds"]
    ):
        raise AssertionError(diagnostic)
    mapping_loops = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.For)
        and isinstance(node.iter, ast.Name)
        and node.iter.id == contract["mapping_source_name"]
    )
    if len(mapping_loops) != 1:
        raise AssertionError(diagnostic)
    loop = mapping_loops[0]
    if (
        function.body[-5] is not loop
        or not isinstance(loop.target, ast.Tuple)
        or tuple(
            element.id if isinstance(element, ast.Name) else None
            for element in loop.target.elts
        )
        != contract["loop_target_names"]
        or any(
            not isinstance(element.ctx, ast.Store)
            for element in loop.target.elts
            if isinstance(element, ast.Name)
        )
        or not isinstance(loop.iter, ast.Name)
        or not isinstance(loop.iter.ctx, ast.Load)
        or loop.iter.id != contract["mapping_source_name"]
        or loop.orelse
        or loop.type_comment is not None
        or tuple(type(statement).__name__ for statement in loop.body)
        != contract["mapping_loop_statement_kinds"]
        or tuple(ast.unparse(statement) for statement in loop.body)
        != contract["mapping_loop_statement_sources"]
        or tuple(ast.unparse(statement) for statement in function.body[-4:])
        != contract["post_loop_statement_sources"]
    ):
        raise AssertionError(diagnostic)

    def walk_without_nested_functions(node: ast.AST) -> tuple[ast.AST, ...]:
        result: list[ast.AST] = [node]
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            result.extend(walk_without_nested_functions(child))
        return tuple(result)

    if any(
        isinstance(node, (ast.Break, ast.Continue, ast.Return, ast.Yield, ast.YieldFrom))
        for node in walk_without_nested_functions(loop)
    ):
        raise AssertionError(diagnostic)
    nested_names = tuple(
        statement.name
        for statement in loop.body
        if isinstance(statement, ast.FunctionDef)
    )
    if nested_names != (
        "instrumented_candidate",
        "instrumented_expect_violation",
    ):
        raise AssertionError(diagnostic)
    instrumented_candidate = next(
        statement
        for statement in loop.body
        if isinstance(statement, ast.FunctionDef)
        and statement.name == "instrumented_candidate"
    )
    instrumented_terminal = next(
        statement
        for statement in loop.body
        if isinstance(statement, ast.FunctionDef)
        and statement.name == "instrumented_expect_violation"
    )
    if (
        _c2b3a_oracle_function_parameters(instrumented_candidate)
        or instrumented_candidate.decorator_list
        or tuple(argument.arg for argument in instrumented_terminal.args.args)
        != ("candidate", "supplied_diagnostic")
        or instrumented_terminal.args.posonlyargs
        or instrumented_terminal.args.kwonlyargs
        or instrumented_terminal.args.vararg is not None
        or instrumented_terminal.args.kwarg is not None
        or instrumented_terminal.args.defaults
        or instrumented_terminal.args.kw_defaults
        or instrumented_terminal.decorator_list
    ):
        raise AssertionError(diagnostic)

    execution_assignments = tuple(
        statement
        for statement in loop.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and statement.target.id == "execution"
    )
    total_assignments = tuple(
        statement
        for statement in function.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and statement.target.id == "execution_totals"
    )
    try:
        execution_initial = ast.literal_eval(execution_assignments[0].value)
        totals_initial = ast.literal_eval(total_assignments[0].value)
    except (IndexError, TypeError, ValueError):
        raise AssertionError(diagnostic) from None
    if (
        len(execution_assignments) != 1
        or len(total_assignments) != 1
        or tuple(execution_initial) != contract["execution_record_fields"]
        or execution_initial
        != {
            "candidate_factory_calls": 0,
            "mutant_calls": 0,
            "terminal_calls": 0,
            "identical_candidate": False,
            "supplied_diagnostic": None,
            "validator_diagnostic": None,
        }
        or tuple(totals_initial) != contract["aggregate_record_fields"]
        or any(value != 0 for value in totals_initial.values())
    ):
        raise AssertionError(diagnostic)

    top_level_binding_sources = {
        ast.unparse(statement.targets[0]): ast.unparse(statement)
        for statement in function.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id
        in {
            "original_candidate",
            "original_expect_violation",
            "contract_violation",
        }
    }
    if top_level_binding_sources != {
        "original_candidate": "original_candidate = namespace.get('_candidate')",
        "original_expect_violation": (
            "original_expect_violation = namespace.get('_expect_violation')"
        ),
        "contract_violation": (
            "contract_violation = namespace.get('_ContractViolation')"
        ),
    }:
        raise AssertionError(diagnostic)

    mapped_calls = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "mutant_function"
    )
    mapped_stores = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Name)
        and node.id == "mutant_function"
        and isinstance(node.ctx, ast.Store)
    )
    real_validator_calls = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "original_validate"
    )
    candidate_factory_calls = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "original_candidate"
    )
    restoration_tries = tuple(
        statement
        for statement in loop.body
        if isinstance(statement, ast.Try)
        and mapped_calls
        and mapped_calls[0] in tuple(ast.walk(statement))
    )
    if (
        len(mapped_calls) != 1
        or len(mapped_stores) != 1
        or len(real_validator_calls) != 2
        or len(candidate_factory_calls) != 1
        or len(restoration_tries) != 1
        or len(restoration_tries[0].body) != 2
        or not isinstance(restoration_tries[0].body[1], ast.Expr)
        or restoration_tries[0].body[1].value is not mapped_calls[0]
        or tuple(ast.unparse(statement) for statement in restoration_tries[0].finalbody)
        != (
            "namespace['_candidate'] = original_candidate",
            "namespace['_expect_violation'] = original_expect_violation",
        )
        or ast.unparse(real_validator_calls[0])
        != "original_validate(controlled_candidate)"
        or ast.unparse(real_validator_calls[1]) != "original_validate(candidate)"
        or ast.unparse(candidate_factory_calls[0]) != "original_candidate()"
    ):
        raise AssertionError(diagnostic)


def _assert_c2b3a_positive_body_semantics(tree: ast.Module) -> None:
    diagnostic = "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"

    def literal_value(name: str) -> object:
        try:
            assignment = _c2b3a_oracle_literal_assignment(tree, name)
            if not _c2b3a_oracle_closed_literal(assignment.value):
                raise AssertionError
            return ast.literal_eval(assignment.value)
        except (AssertionError, SyntaxError, ValueError):
            raise AssertionError(diagnostic) from None

    process_expected = literal_value(
        "EXPECTED_PROCESS_CONTROL_REFERENCE_CASES"
    )
    cleanup_fields = literal_value("CLEANUP_SAFE_PROJECTION_FIELDS")
    cleanup_inputs = literal_value("CLEANUP_REFERENCE_INPUT_CASES")
    cleanup_expected = literal_value("EXPECTED_CLEANUP_REFERENCE_CASES")
    required_cleanup_fields = (
        "state", "entered", "completed", "admission_open", "wrapper_reachable",
        "ordinary_closing", "connection_owned", "connection_closed_proved",
        "credential_authority", "mutation_slot_owned", "database_binding_owned",
        "writer_lock_release", "descriptor_outcome", "descriptor_retryable",
        "descriptor_owned", "authority_lock_terminal",
        "authority_lock_registry_present", "writer_session_registry_present",
        "close_attempts", "unlock_attempts", "descriptor_close_attempts",
        "finalizer_attempted", "retry_reachable", "effective_cleanup_outcome",
        "selected_outward", "cleanup_failure_suppressed", "X",
        "recovery_admitted", "replay_admitted", "new_operation_admitted",
    )
    if (
        type(process_expected) is not dict
        or tuple(process_expected) != C2B3A_PROCESS_CONTROL_EXPECTED_CASE_IDS
        or len(process_expected) != 16
        or any(
            type(value) is not tuple or len(value) != 17
            for value in process_expected.values()
        )
        or type(cleanup_fields) is not tuple
        or cleanup_fields != required_cleanup_fields
        or type(cleanup_inputs) is not tuple
        or len(cleanup_inputs) != 55
        or tuple(case_id for case_id, _inputs in cleanup_inputs)
        != C2B3A_CLEANUP_EXPECTED_CASE_IDS
        or any(
            type(case_id) is not str
            or type(inputs) is not tuple
            or len(inputs) != 9
            for case_id, inputs in cleanup_inputs
        )
        or type(cleanup_expected) is not dict
        or tuple(cleanup_expected) != C2B3A_CLEANUP_EXPECTED_CASE_IDS
        or len(cleanup_expected) != 55
        or any(
            type(value) is not tuple or len(value) != len(required_cleanup_fields)
            for value in cleanup_expected.values()
        )
    ):
        raise AssertionError(diagnostic)

    if (
        tuple(process_expected[case_id][0] for case_id in C2B3A_PROCESS_CONTROL_EXPECTED_CASE_IDS[:9])
        != ("distinct_instance",) * 9
        or tuple(process_expected[case_id][0] for case_id in C2B3A_PROCESS_CONTROL_EXPECTED_CASE_IDS[9:12])
        != ("same_instance",) * 3
        or process_expected["prelinked-cause"][6:15]
        != (2, 1, True, True, None, "GeneratorExit", None, None, None)
        or process_expected["prelinked-context"][6:15]
        != (2, 1, True, True, None, None, "KeyboardInterrupt", None, None)
        or process_expected["linked-cycle"][6:15]
        != (2, 3, True, True, None, "KeyboardInterrupt", None, None, "KeyboardInterrupt")
        or process_expected["private-payload"][2:4]
        != (
            (("opaque-synthetic-payload", 40),),
            ("opaque-synthetic-payload", 40),
        )
        or process_expected["private-payload"][10:15]
        != (
            (("opaque-synthetic-payload", 40),),
            "GeneratorExit",
            None,
            None,
            "KeyboardInterrupt",
        )
        or any(value[-2:] != (False, False) for value in process_expected.values())
    ):
        raise AssertionError(diagnostic)

    initial_states = {inputs[0] for _case_id, inputs in cleanup_inputs}
    fault_steps = {inputs[1] for _case_id, inputs in cleanup_inputs}
    fault_positions = {inputs[2] for _case_id, inputs in cleanup_inputs}
    connection_outcomes = {inputs[3] for _case_id, inputs in cleanup_inputs}
    finalizer_postures = {inputs[6] for _case_id, inputs in cleanup_inputs}
    cleanup_outcomes = {inputs[7] for _case_id, inputs in cleanup_inputs}
    earlier_primaries = {inputs[8] for _case_id, inputs in cleanup_inputs}
    if (
        initial_states != {"A", "QU", "QK", "PU", "PK"}
        or fault_steps
        != {None, "P0", "C1", "C2", "R1", "R2", "R3", "L1", "H1", "H2", "T1", "H3"}
        or fault_positions != {None, "before", "between", "after"}
        or connection_outcomes
        != {"normal", "ordinary", "KeyboardInterrupt", "SystemExit", "GeneratorExit"}
        or finalizer_postures != {False, True}
        or cleanup_outcomes
        != {"normal", "ordinary", "KeyboardInterrupt", "SystemExit", "GeneratorExit"}
        or earlier_primaries
        != {"none", "KeyboardInterrupt", "SystemExit", "GeneratorExit"}
    ):
        raise AssertionError(diagnostic)

    def named_assignment(
        statements: list[ast.stmt],
        index: int,
        name: str,
    ) -> ast.Assign:
        statement = statements[index]
        if (
            not isinstance(statement, ast.Assign)
            or len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
            or statement.targets[0].id != name
        ):
            raise AssertionError(diagnostic)
        return statement

    def exact_subscript(node: ast.AST, root: str, field: str) -> bool:
        return (
            isinstance(node, ast.Subscript)
            and isinstance(node.ctx, ast.Load)
            and isinstance(node.value, ast.Name)
            and isinstance(node.value.ctx, ast.Load)
            and node.value.id == root
            and isinstance(node.slice, ast.Constant)
            and node.slice.value == field
        )

    def exact_assert_compare(
        statement: ast.stmt,
        *,
        left: ast.AST,
        operator: type[ast.cmpop],
        right: ast.AST,
    ) -> None:
        if (
            not isinstance(statement, ast.Assert)
            or not isinstance(statement.test, ast.Compare)
            or len(statement.test.ops) != 1
            or type(statement.test.ops[0]) is not operator
            or len(statement.test.comparators) != 1
            or ast.dump(statement.test.left, include_attributes=False)
            != ast.dump(left, include_attributes=False)
            or ast.dump(statement.test.comparators[0], include_attributes=False)
            != ast.dump(right, include_attributes=False)
        ):
            raise AssertionError(diagnostic)

    def load_name(name: str) -> ast.Name:
        return ast.Name(id=name, ctx=ast.Load())

    def load_field(root: str, field: str) -> ast.Subscript:
        return ast.Subscript(
            value=load_name(root),
            slice=ast.Constant(value=field),
            ctx=ast.Load(),
        )

    def parsed_expression(source: str) -> ast.expr:
        return ast.parse(source, mode="eval").body

    def exact_positive_outer_loop(
        function: ast.FunctionDef,
        *,
        cases_value: ast.expr,
        inventory_left: ast.expr,
        inventory_name: str,
    ) -> ast.For:
        if len(function.body) != 3:
            raise AssertionError(diagnostic)
        cases_assignment = named_assignment(function.body, 0, "cases")
        if ast.dump(cases_assignment.value, include_attributes=False) != ast.dump(
            cases_value,
            include_attributes=False,
        ):
            raise AssertionError(diagnostic)
        exact_assert_compare(
            function.body[1],
            left=inventory_left,
            operator=ast.Eq,
            right=parsed_expression(f"tuple({inventory_name})"),
        )
        loop = function.body[2]
        if (
            not isinstance(loop, ast.For)
            or not isinstance(loop.iter, ast.Name)
            or not isinstance(loop.iter.ctx, ast.Load)
            or loop.iter.id != "cases"
            or loop.orelse
        ):
            raise AssertionError(diagnostic)
        return loop

    def reject_alias_rebind_or_mutation(
        function: ast.FunctionDef,
        names: tuple[str, ...],
    ) -> None:
        for name in names:
            stores = tuple(
                node for node in ast.walk(function)
                if isinstance(node, ast.Name)
                and node.id == name
                and isinstance(node.ctx, ast.Store)
            )
            if len(stores) != 1:
                raise AssertionError(diagnostic)
        for node in ast.walk(function):
            if (
                isinstance(node, (ast.Attribute, ast.Subscript))
                and isinstance(node.ctx, (ast.Store, ast.Del))
                and _c2b3a_oracle_store_root(node) in names
            ):
                raise AssertionError(diagnostic)
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                value = node.value
                targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
                target_names = {
                    assigned
                    for target in targets
                    for assigned in _c2b3a_oracle_assigned_names(target)
                }
                loaded = {
                    descendant.id
                    for descendant in ast.walk(value)
                    if isinstance(descendant, ast.Name)
                    and isinstance(descendant.ctx, ast.Load)
                    and descendant.id in names
                }
                if loaded and not target_names.intersection(names):
                    raise AssertionError(diagnostic)
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {
                    "update", "clear", "pop", "popitem", "setdefault",
                    "__setitem__", "append", "extend", "insert", "remove",
                }
                and _c2b3a_oracle_store_root(node.func) in names
            ):
                raise AssertionError(diagnostic)
        for comparison in (
            node for node in ast.walk(function)
            if isinstance(node, ast.Compare)
        ):
            operands = (comparison.left, *comparison.comparators)
            for left_index, left in enumerate(operands):
                for right in operands[left_index + 1:]:
                    if ast.dump(left, include_attributes=False) == ast.dump(
                        right,
                        include_attributes=False,
                    ):
                        raise AssertionError(diagnostic)
                    left_roots = {
                        descendant.id
                        for descendant in ast.walk(left)
                        if isinstance(descendant, ast.Name)
                        and isinstance(descendant.ctx, ast.Load)
                        and descendant.id in names
                    }
                    right_roots = {
                        descendant.id
                        for descendant in ast.walk(right)
                        if isinstance(descendant, ast.Name)
                        and isinstance(descendant.ctx, ast.Load)
                        and descendant.id in names
                    }
                    if left_roots.intersection(right_roots):
                        raise AssertionError(diagnostic)

    matrix = _c2b3a_oracle_top_level_function(
        tree,
        "test_commit_close_addendum_direct_oracle_matrix_is_closed",
    )
    matrix_assignment = named_assignment(matrix.body, 0, "addendum")
    if (
        not exact_subscript(
            matrix_assignment.value,
            "_owner_contract",
            "commit_close_outcome_addendum",
        )
    ):
        value = matrix_assignment.value
        if not (
            isinstance(value, ast.Subscript)
            and isinstance(value.value, ast.Call)
            and isinstance(value.value.func, ast.Name)
            and value.value.func.id == "_owner_contract"
            and not value.value.args
            and not value.value.keywords
            and isinstance(value.slice, ast.Constant)
            and value.slice.value == "commit_close_outcome_addendum"
        ):
            raise AssertionError(diagnostic)
    exact_assert_compare(
        matrix.body[1],
        left=load_name("addendum"),
        operator=ast.Eq,
        right=load_name("EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM"),
    )

    custody = _c2b3a_oracle_top_level_function(
        tree,
        "test_commit_close_addendum_custody_recovery_and_scope_are_exact",
    )
    custody_assignment = named_assignment(custody.body, 0, "addendum")
    if not (
        isinstance(custody_assignment.value, ast.Call)
        and isinstance(custody_assignment.value.func, ast.Name)
        and custody_assignment.value.func.id == "deepcopy"
        and len(custody_assignment.value.args) == 1
        and isinstance(custody_assignment.value.args[0], ast.Name)
        and custody_assignment.value.args[0].id
        == "EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM"
        and not custody_assignment.value.keywords
    ):
        raise AssertionError(diagnostic)

    relational = _c2b3a_oracle_top_level_function(
        tree,
        "test_commit_close_relational_process_control_reference_cases_are_exact",
    )
    relational_loop = exact_positive_outer_loop(
        relational,
        cases_value=parsed_expression("_process_control_reference_cases()"),
        inventory_left=parsed_expression(
            "tuple(case_id for case_id, _, _ in cases)"
        ),
        inventory_name="EXPECTED_PROCESS_CONTROL_REFERENCE_CASES",
    )
    if (
        not isinstance(relational_loop.target, ast.Tuple)
        or tuple(
            element.id if isinstance(element, ast.Name) else None
            for element in relational_loop.target.elts
        ) != ("case_id", "primary", "secondary")
        or not isinstance(relational_loop.iter, ast.Name)
        or relational_loop.iter.id != "cases"
        or len(relational_loop.body) != 8
    ):
        raise AssertionError(diagnostic)
    observed_assignment = named_assignment(relational_loop.body, 0, "observed")
    expected_assignment = named_assignment(relational_loop.body, 1, "expected")
    if not (
        isinstance(observed_assignment.value, ast.Call)
        and isinstance(observed_assignment.value.func, ast.Name)
        and observed_assignment.value.func.id
        == "_relational_process_control_reference"
        and tuple(
            argument.id if isinstance(argument, ast.Name) else None
            for argument in observed_assignment.value.args
        ) == ("primary", "secondary")
        and not observed_assignment.value.keywords
        and isinstance(expected_assignment.value, ast.Subscript)
        and isinstance(expected_assignment.value.value, ast.Name)
        and expected_assignment.value.value.id
        == "EXPECTED_PROCESS_CONTROL_REFERENCE_CASES"
        and isinstance(expected_assignment.value.slice, ast.Name)
        and expected_assignment.value.slice.id == "case_id"
    ):
        raise AssertionError(diagnostic)
    exact_assert_compare(
        relational_loop.body[2],
        left=load_field("observed", "safe_projection"),
        operator=ast.Eq,
        right=load_name("expected"),
    )
    identity_fields = (
        ("provided_primary", "primary"),
        ("provided_secondary", "secondary"),
        ("caught_primary", "primary"),
        ("caught_secondary", "secondary"),
        ("outward_primary", "primary"),
    )
    for statement, (field, input_name) in zip(
        relational_loop.body[3:],
        identity_fields,
        strict=True,
    ):
        exact_assert_compare(
            statement,
            left=load_field("observed", field),
            operator=ast.Is,
            right=load_name(input_name),
        )
    reject_alias_rebind_or_mutation(
        relational,
        ("cases", "observed", "expected"),
    )

    cleanup = _c2b3a_oracle_top_level_function(
        tree,
        "test_post_close_cleanup_reference_model_covers_every_release_point",
    )
    cleanup_loop = exact_positive_outer_loop(
        cleanup,
        cases_value=load_name("CLEANUP_REFERENCE_INPUT_CASES"),
        inventory_left=parsed_expression(
            "tuple(case_id for case_id, _ in cases)"
        ),
        inventory_name="EXPECTED_CLEANUP_REFERENCE_CASES",
    )
    if (
        not isinstance(cleanup_loop.target, ast.Tuple)
        or tuple(
            element.id if isinstance(element, ast.Name) else None
            for element in cleanup_loop.target.elts
        ) != ("case_id", "inputs")
        or not isinstance(cleanup_loop.iter, ast.Name)
        or cleanup_loop.iter.id != "cases"
        or len(cleanup_loop.body) != 3
    ):
        raise AssertionError(diagnostic)
    observed_assignment = named_assignment(cleanup_loop.body, 0, "observed")
    expected_assignment = named_assignment(cleanup_loop.body, 1, "expected")
    if not (
        isinstance(observed_assignment.value, ast.Call)
        and isinstance(observed_assignment.value.func, ast.Name)
        and observed_assignment.value.func.id == "_cleanup_reference"
        and len(observed_assignment.value.args) == 1
        and isinstance(observed_assignment.value.args[0], ast.Starred)
        and isinstance(observed_assignment.value.args[0].value, ast.Name)
        and observed_assignment.value.args[0].value.id == "inputs"
        and not observed_assignment.value.keywords
        and isinstance(expected_assignment.value, ast.Subscript)
        and isinstance(expected_assignment.value.value, ast.Name)
        and expected_assignment.value.value.id == "EXPECTED_CLEANUP_REFERENCE_CASES"
        and isinstance(expected_assignment.value.slice, ast.Name)
        and expected_assignment.value.slice.id == "case_id"
    ):
        raise AssertionError(diagnostic)
    exact_assert_compare(
        cleanup_loop.body[2],
        left=load_name("observed"),
        operator=ast.Eq,
        right=load_name("expected"),
    )
    reject_alias_rebind_or_mutation(
        cleanup,
        ("cases", "observed", "expected"),
    )

    namespace: dict[str, object] = {
        "__file__": str(C2B3A_ORACLE_PATH),
        "__name__": "c2b3a_positive_execution_probe",
    }
    try:
        exec(
            compile(tree, filename=str(C2B3A_ORACLE_PATH), mode="exec"),
            namespace,
        )
    except BaseException:
        raise AssertionError(diagnostic) from None
    relational_positive = namespace.get(
        "test_commit_close_relational_process_control_reference_cases_are_exact"
    )
    cleanup_positive = namespace.get(
        "test_post_close_cleanup_reference_model_covers_every_release_point"
    )
    original_relational_helper = namespace.get(
        "_relational_process_control_reference"
    )
    original_cleanup_helper = namespace.get("_cleanup_reference")
    if not all(
        callable(value)
        for value in (
            relational_positive,
            cleanup_positive,
            original_relational_helper,
            original_cleanup_helper,
        )
    ):
        raise AssertionError(diagnostic)

    class TrackingExpected(dict[object, object]):
        def __init__(
            self,
            value: dict[object, object],
            observed_ids: list[object],
        ) -> None:
            super().__init__(value)
            self.observed_ids = observed_ids

        def __getitem__(self, key: object) -> object:
            self.observed_ids.append(key)
            return super().__getitem__(key)

    process_helper_calls = 0
    process_observed_ids: list[object] = []

    def instrumented_relational_helper(
        primary: object,
        secondary: object,
    ) -> object:
        nonlocal process_helper_calls
        process_helper_calls += 1
        return original_relational_helper(primary, secondary)

    original_process_expected = namespace.get(
        "EXPECTED_PROCESS_CONTROL_REFERENCE_CASES"
    )
    namespace["EXPECTED_PROCESS_CONTROL_REFERENCE_CASES"] = TrackingExpected(
        process_expected,
        process_observed_ids,
    )
    namespace["_relational_process_control_reference"] = (
        instrumented_relational_helper
    )
    try:
        process_result = relational_positive()
    except BaseException:
        raise AssertionError(diagnostic) from None
    finally:
        namespace["EXPECTED_PROCESS_CONTROL_REFERENCE_CASES"] = (
            original_process_expected
        )
        namespace["_relational_process_control_reference"] = (
            original_relational_helper
        )
    if (
        process_result is not None
        or process_helper_calls != len(C2B3A_PROCESS_CONTROL_EXPECTED_CASE_IDS)
        or tuple(process_observed_ids)
        != C2B3A_PROCESS_CONTROL_EXPECTED_CASE_IDS
        or len(set(process_observed_ids)) != len(process_observed_ids)
    ):
        raise AssertionError(diagnostic)

    cleanup_helper_calls = 0
    cleanup_observed_ids: list[object] = []

    def instrumented_cleanup_helper(*inputs: object) -> object:
        nonlocal cleanup_helper_calls
        cleanup_helper_calls += 1
        return original_cleanup_helper(*inputs)

    original_cleanup_expected = namespace.get("EXPECTED_CLEANUP_REFERENCE_CASES")
    namespace["EXPECTED_CLEANUP_REFERENCE_CASES"] = TrackingExpected(
        cleanup_expected,
        cleanup_observed_ids,
    )
    namespace["_cleanup_reference"] = instrumented_cleanup_helper
    try:
        cleanup_result = cleanup_positive()
    except BaseException:
        raise AssertionError(diagnostic) from None
    finally:
        namespace["EXPECTED_CLEANUP_REFERENCE_CASES"] = original_cleanup_expected
        namespace["_cleanup_reference"] = original_cleanup_helper
    if (
        cleanup_result is not None
        or cleanup_helper_calls != len(C2B3A_CLEANUP_EXPECTED_CASE_IDS)
        or tuple(cleanup_observed_ids) != C2B3A_CLEANUP_EXPECTED_CASE_IDS
        or len(set(cleanup_observed_ids)) != len(cleanup_observed_ids)
    ):
        raise AssertionError(diagnostic)


def _assert_c2b3a_oracle_semantic_execution(tree: ast.Module) -> None:
    _assert_c2b3a_addendum_literal_semantics(tree)
    _assert_c2b3a_expect_violation_semantics(tree)
    _assert_c2b3a_reference_helper_semantics(tree)
    _assert_c2b3a_mutant_dataflow_semantics(tree)
    _assert_c2b3a_positive_body_semantics(tree)


def _assert_c2b3a_independent_oracle_architecture(source: str) -> None:
    diagnostic = "C2B3A_INDEPENDENT_ORACLE_ARCHITECTURE_INVALID"
    try:
        tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    except SyntaxError:
        raise AssertionError(diagnostic) from None
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    _assert_c2b3a_oracle_semantic_execution(tree)
    _assert_c2b3a_oracle_collection_architecture(tree, parents)
    top_level_ids = {id(statement) for statement in tree.body}

    import_signatures: list[tuple[str, str, str | None]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if id(node) not in top_level_ids:
                raise AssertionError(diagnostic)
            for item in node.names:
                if item.asname is not None:
                    raise AssertionError(diagnostic)
                import_signatures.append(("import", item.name, None))
        elif isinstance(node, ast.ImportFrom):
            if id(node) not in top_level_ids or node.level != 0:
                raise AssertionError(diagnostic)
            if node.module is None:
                raise AssertionError(diagnostic)
            for item in node.names:
                if item.asname is not None:
                    raise AssertionError(diagnostic)
                import_signatures.append(("from", node.module, item.name))
    if tuple(import_signatures) != (
        ("import", "ast", None),
        ("from", "copy", "deepcopy"),
        ("from", "pathlib", "Path"),
        ("import", "pytest", None),
    ):
        raise AssertionError(diagnostic)
    if tuple(sorted({item[1] for item in import_signatures})) != tuple(
        sorted(C2B3A_ORACLE_ALLOWED_IMPORTS)
    ):
        raise AssertionError(diagnostic)

    expected_names = C2B3A_ORACLE_PROTECTED_EXPECTED_VALUE_NAMES
    expected_assignments = {
        name: _c2b3a_oracle_literal_assignment(tree, name)
        for name in expected_names
    }
    if any(isinstance(node, (ast.Global, ast.Nonlocal)) for node in ast.walk(tree)):
        raise AssertionError(diagnostic)

    protected_callable_bindings = set(C2B3A_ORACLE_ALLOWED_DIRECT_CALLS) | {
        "ast",
        "deepcopy",
        "Path",
        "pytest",
    }
    for node in ast.walk(tree):
        bindings: tuple[str, ...] = ()
        if isinstance(node, ast.Assign):
            bindings = tuple(
                name
                for target in node.targets
                for name in _c2b3a_oracle_assigned_names(target)
            )
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            bindings = _c2b3a_oracle_assigned_names(node.target)
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
            bindings = _c2b3a_oracle_assigned_names(node.target)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            bindings = tuple(
                name
                for item in node.items
                if item.optional_vars is not None
                for name in _c2b3a_oracle_assigned_names(item.optional_vars)
            )
        elif isinstance(node, ast.ExceptHandler) and node.name is not None:
            bindings = (node.name,)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            bindings = (node.name,) + _c2b3a_oracle_function_parameters(node)
        elif isinstance(node, ast.ClassDef):
            bindings = (node.name,)
        elif isinstance(
            node,
            (
                ast.MatchAs,
                ast.MatchStar,
                ast.MatchMapping,
                ast.MatchSequence,
                ast.MatchClass,
                ast.MatchOr,
            ),
        ):
            bindings = _c2b3a_oracle_assigned_names(node)
        elif isinstance(node, ast.Delete):
            bindings = tuple(
                name
                for target in node.targets
                for name in _c2b3a_oracle_assigned_names(target)
            )
        for name in bindings:
            if name in expected_names:
                if not (
                    isinstance(node, ast.Assign)
                    and node is expected_assignments[name]
                    and id(node) in top_level_ids
                ):
                    raise AssertionError(diagnostic)
            if name in protected_callable_bindings:
                permitted_definition = (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == name
                    and id(node) in top_level_ids
                ) or (
                    isinstance(node, ast.ClassDef)
                    and node.name == "_ContractViolation"
                    and name == "_ContractViolation"
                    and id(node) in top_level_ids
                )
                if not permitted_definition:
                    raise AssertionError(diagnostic)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            parent = parents.get(node)
            while parent is not None:
                if isinstance(
                    parent,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                ):
                    raise AssertionError(diagnostic)
                parent = parents.get(parent)

    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    forbidden_dynamic_names = {
        "eval",
        "exec",
        "compile",
        "getattr",
        "setattr",
        "delattr",
        "globals",
        "locals",
        "vars",
        "__import__",
        "import_module",
        "builtins",
        "__builtins__",
        "hash",
        "open",
    }
    forbidden_file_attributes = {
        "open",
        "read_bytes",
        "readlink",
        "glob",
        "rglob",
        "iterdir",
        "cwd",
        "home",
    }
    read_text_calls: list[ast.Call] = []
    path_calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in forbidden_dynamic_names:
                raise AssertionError(diagnostic)
        if isinstance(node, ast.Attribute):
            if node.attr in forbidden_dynamic_names or node.attr == "__call__":
                raise AssertionError(diagnostic)
            if node.attr in forbidden_file_attributes:
                raise AssertionError(diagnostic)
            if node.attr == "read_text":
                parent = parents.get(node)
                if not isinstance(parent, ast.Call) or parent.func is not node:
                    raise AssertionError(diagnostic)
        if isinstance(node, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp)):
            if isinstance(node, ast.Lambda):
                raise AssertionError(diagnostic)
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            call_name = node.func.id
            if call_name not in C2B3A_ORACLE_ALLOWED_DIRECT_CALLS:
                raise AssertionError(diagnostic)
            enclosing = _c2b3a_oracle_enclosing_function(node, parents)
            if (
                enclosing is not None
                and call_name in _c2b3a_oracle_function_parameters(enclosing)
            ):
                raise AssertionError(diagnostic)
            if call_name == "Path":
                path_calls.append(node)
            if call_name == "_read_allowed_text":
                if (
                    len(node.args) != 1
                    or not isinstance(node.args[0], ast.Name)
                    or node.args[0].id
                    not in {"OWNER_PATH", "PLANNING_PATH", "TEST_PATH"}
                    or node.keywords
                ):
                    raise AssertionError(diagnostic)
        elif isinstance(node.func, ast.Attribute):
            chain = _c2b3a_oracle_attribute_chain(node.func)
            literal_scope_join = (
                chain is None
                and node.func.attr == "join"
                and isinstance(node.func.value, ast.Constant)
                and node.func.value.value == " "
                and len(node.args) == 1
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "prose"
                and not node.keywords
                and _c2b3a_oracle_enclosing_function(node, parents)
                is not None
                and _c2b3a_oracle_enclosing_function(node, parents).name
                == "_validate_planning_status"
            )
            if (
                chain not in C2B3A_ORACLE_ALLOWED_ATTRIBUTE_CALLS
                and not literal_scope_join
            ):
                raise AssertionError(diagnostic)
            if chain == "resolved.read_text":
                read_text_calls.append(node)
        else:
            raise AssertionError(diagnostic)

    if len(path_calls) != 1:
        raise AssertionError(diagnostic)
    path_call = path_calls[0]
    path_parent = parents.get(path_call)
    if (
        len(path_call.args) != 1
        or not isinstance(path_call.args[0], ast.Name)
        or path_call.args[0].id != "__file__"
        or path_call.keywords
        or not isinstance(path_parent, ast.Assign)
        or id(path_parent) not in top_level_ids
        or len(path_parent.targets) != 1
        or not isinstance(path_parent.targets[0], ast.Name)
        or path_parent.targets[0].id != "ORACLE_SOURCE_PATH"
    ):
        raise AssertionError(diagnostic)
    if len(read_text_calls) != 1:
        raise AssertionError(diagnostic)
    read_call = read_text_calls[0]
    read_owner = _c2b3a_oracle_enclosing_function(read_call, parents)
    if (
        read_owner is None
        or read_owner.name != "_read_allowed_text"
        or read_call.args
        or len(read_call.keywords) != 1
        or read_call.keywords[0].arg != "encoding"
        or not isinstance(read_call.keywords[0].value, ast.Constant)
        or read_call.keywords[0].value.value != "utf-8"
    ):
        raise AssertionError(diagnostic)

    relative_assignments = tuple(
        statement
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "ALLOWED_ORACLE_RELATIVE_PATHS"
    )
    if len(relative_assignments) != 1:
        raise AssertionError(diagnostic)
    relative_assignment = relative_assignments[0]
    if not _c2b3a_oracle_closed_literal(relative_assignment.value):
        raise AssertionError(diagnostic)
    try:
        relative_reads = ast.literal_eval(relative_assignment.value)
    except (SyntaxError, ValueError):
        raise AssertionError(diagnostic) from None
    if relative_reads != C2B3A_ORACLE_ALLOWED_RELATIVE_READS:
        raise AssertionError(diagnostic)
    helper_calls = {
        _c2b3a_oracle_attribute_chain(node.func)
        for node in ast.walk(read_owner)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    if not {
        "path.relative_to",
        "relative.as_posix",
            "expected_path.is_symlink",
            "expected_path.resolve",
        "resolved.read_text",
    }.issubset(helper_calls):
        raise AssertionError(diagnostic)
    helper_comparisons = tuple(
        node for node in ast.walk(read_owner) if isinstance(node, ast.Compare)
    )
    helper_compare_source = " ".join(ast.unparse(node) for node in helper_comparisons)
    if (
        "requested in ALLOWED_ORACLE_RELATIVE_PATHS" not in helper_compare_source
        or "resolved == expected_path" not in helper_compare_source
        or "path == expected_path" not in helper_compare_source
    ):
        raise AssertionError(diagnostic)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lowered_name = node.name.lower()
            if any(
                token in lowered_name
                for token in ("dispatcher", "runner", "case_executor")
            ):
                raise AssertionError(diagnostic)
            defaults = tuple(node.args.defaults) + tuple(
                default
                for default in node.args.kw_defaults
                if default is not None
            )
            if any(not _c2b3a_oracle_closed_literal(default) for default in defaults):
                raise AssertionError(diagnostic)
            annotations = tuple(
                annotation
                for annotation in (
                    node.returns,
                    *(argument.annotation for argument in node.args.posonlyargs),
                    *(argument.annotation for argument in node.args.args),
                    *(argument.annotation for argument in node.args.kwonlyargs),
                    node.args.vararg.annotation if node.args.vararg else None,
                    node.args.kwarg.annotation if node.args.kwarg else None,
                )
                if annotation is not None
            )
            for annotation in annotations:
                if any(isinstance(item, (ast.Call, ast.Lambda)) for item in ast.walk(annotation)):
                    raise AssertionError(diagnostic)
                if any(
                    isinstance(item, ast.Name) and item.id in function_names
                    for item in ast.walk(annotation)
                ):
                    raise AssertionError(diagnostic)
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    raise AssertionError(diagnostic)
                if (
                    _c2b3a_oracle_attribute_chain(decorator.func)
                    != "pytest.mark.parametrize"
                ):
                    raise AssertionError(diagnostic)
                if any(
                    not _c2b3a_oracle_closed_literal(argument)
                    for argument in decorator.args
                ):
                    raise AssertionError(diagnostic)
                if any(
                    keyword.arg is None
                    or not _c2b3a_oracle_closed_literal(keyword.value)
                    for keyword in decorator.keywords
                ):
                    raise AssertionError(diagnostic)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            target_names = tuple(
                name
                for target in targets
                for name in _c2b3a_oracle_assigned_names(target)
            )
            if any(
                (
                    token in name.lower()
                    and name
                    not in {
                        "authority_lock_registry_present",
                        "writer_session_registry_present",
                    }
                )
                for name in target_names
                for token in ("registry", "dispatcher", "runners", "callables")
            ):
                raise AssertionError(diagnostic)
            value = node.value
            if value is None:
                continue
            for item in ast.walk(value):
                if not isinstance(item, ast.Name) or item.id not in function_names:
                    continue
                parent = parents.get(item)
                if isinstance(parent, ast.Call) and parent.func is item:
                    continue
                raise AssertionError(diagnostic)

    expected_aliases = set(expected_names)
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            value_root = node.value
            while isinstance(value_root, (ast.Attribute, ast.Subscript)):
                value_root = value_root.value
            if (
                not isinstance(value_root, ast.Name)
                or value_root.id not in expected_aliases
            ):
                continue
            aliases = _c2b3a_oracle_assigned_names(node.targets[0])
            for alias in aliases:
                if alias not in expected_aliases:
                    expected_aliases.add(alias)
                    changed = True
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete)):
            targets: tuple[ast.AST, ...]
            if isinstance(node, ast.Assign):
                targets = tuple(node.targets)
            elif isinstance(node, ast.Delete):
                targets = tuple(node.targets)
            else:
                targets = (node.target,)
            for target in targets:
                root = target
                while isinstance(root, (ast.Attribute, ast.Subscript)):
                    root = root.value
                if (
                    isinstance(root, ast.Name)
                    and root.id in expected_aliases
                    and not isinstance(target, ast.Name)
                ):
                    raise AssertionError(diagnostic)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            root = node.func.value
            while isinstance(root, (ast.Attribute, ast.Subscript)):
                root = root.value
            if isinstance(root, ast.Name) and root.id in expected_aliases:
                raise AssertionError(diagnostic)

    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.AsyncFor)):
            loop_names = set(_c2b3a_oracle_assigned_names(node.target))
            for descendant in ast.walk(node):
                if (
                    isinstance(descendant, ast.Call)
                    and isinstance(descendant.func, ast.Name)
                    and descendant.func.id in loop_names
                ):
                    raise AssertionError(diagnostic)
        if isinstance(node, ast.comprehension):
            loop_names = set(_c2b3a_oracle_assigned_names(node.target))
            parent = parents.get(node)
            while parent is not None and not isinstance(
                parent,
                (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp),
            ):
                parent = parents.get(parent)
            if parent is None:
                raise AssertionError(diagnostic)
            for descendant in ast.walk(parent):
                if (
                    isinstance(descendant, ast.Call)
                    and isinstance(descendant.func, ast.Name)
                    and descendant.func.id in loop_names
                ):
                    raise AssertionError(diagnostic)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            chain = _c2b3a_oracle_attribute_chain(node.func)
            if chain is not None and any(
                token in chain.lower()
                for token in ("hexdigest", "sha256", "source_hash", "candidate_hash")
            ):
                raise AssertionError(diagnostic)

    if not set(C2B3A_ORACLE_PROTECTED_READER_PARSER_NAMES).issubset(
        C2B3A_ORACLE_PROTECTED_CALLABLE_NAMES
    ):
        raise AssertionError(diagnostic)
    if not set(C2B3A_ORACLE_PROTECTED_VALIDATION_HELPER_NAMES).issubset(
        C2B3A_ORACLE_PROTECTED_CALLABLE_NAMES
    ):
        raise AssertionError(diagnostic)
    observed_load_sites = _c2b3a_oracle_protected_load_sites(tree, parents)
    if observed_load_sites != _c2b3a_oracle_expected_protected_load_sites():
        raise AssertionError(diagnostic)


def _c2b3a_bounded_oracle_source() -> str:
    diagnostic = "C2B3A_INDEPENDENT_ORACLE_ARCHITECTURE_INVALID"
    if C2B3A_ORACLE_PATH.is_symlink():
        raise AssertionError(diagnostic)
    try:
        resolved = C2B3A_ORACLE_PATH.resolve(strict=True)
    except (OSError, RuntimeError):
        raise AssertionError(diagnostic) from None
    if resolved != C2B3A_ORACLE_PATH:
        raise AssertionError(diagnostic)
    return resolved.read_text(encoding="utf-8")


def _c2b3a_process_control_candidate(source: str) -> dict[str, object]:
    try:
        tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
        assignment = _c2b3a_oracle_literal_assignment(
            tree,
            "EXPECTED_INITIALIZATION_CONTRACT",
        )
        candidate = ast.literal_eval(assignment.value)
    except (AssertionError, SyntaxError, ValueError):
        raise AssertionError("C2B3A_PROCESS_CONTROL_BRANCH_INVENTORY") from None
    if type(candidate) is not dict:
        raise AssertionError("C2B3A_PROCESS_CONTROL_BRANCH_INVENTORY")
    return candidate


def _assert_c2b3a_process_control_candidate(candidate: object) -> None:
    try:
        close_not_proved = candidate["commit_uncertainty_cleanup_gate"][
            "close_not_proved"
        ]
        branches = close_not_proved["process_control_exceptions"]
    except (KeyError, TypeError):
        raise AssertionError("C2B3A_PROCESS_CONTROL_BRANCH_INVENTORY") from None
    if type(branches) is not dict or tuple(branches) != (
        "KeyboardInterrupt",
        "SystemExit",
        "GeneratorExit",
    ):
        raise AssertionError("C2B3A_PROCESS_CONTROL_BRANCH_INVENTORY")
    for branch_name in (
        "KeyboardInterrupt",
        "SystemExit",
        "GeneratorExit",
    ):
        branch = branches[branch_name]
        if type(branch) is not dict:
            raise AssertionError("C2B3A_PROCESS_CONTROL_PUBLICATION_ORDER")
        if branch.get("exception_identity_preserved") is not True:
            raise AssertionError("C2B3A_PROCESS_CONTROL_EXCEPTION_IDENTITY")
        if any(
            identity_key in branch
            for identity_key in (
                "replacement_exception_object",
                "changed_exception_args",
                "changed_system_exit_code",
            )
        ):
            raise AssertionError("C2B3A_PROCESS_CONTROL_EXCEPTION_IDENTITY")
    if close_not_proved.get(
        "process_control_close_interruption_ordered_steps"
    ) != C2B3A_PROCESS_CONTROL_ORDERED_STEPS:
        raise AssertionError("C2B3A_PROCESS_CONTROL_PUBLICATION_ORDER")
    if branches != C2B3A_PROCESS_CONTROL_BRANCH_FACTS:
        raise AssertionError("C2B3A_PROCESS_CONTROL_PUBLICATION_ORDER")
    ledger = close_not_proved.get("process_control_exception_graph_ledger")
    if type(ledger) is not tuple or ledger != C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_LEDGER:
        raise AssertionError("C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID")
    if tuple(row.get("branch_name") for row in ledger) != (
        "KeyboardInterrupt",
        "SystemExit",
        "GeneratorExit",
    ):
        raise AssertionError("C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID")
    if any(
        type(row) is not dict
        or tuple(row) != C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_FIELDS
        for row in ledger
    ):
        raise AssertionError("C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID")
    privacy = candidate["commit_uncertainty_cleanup_gate"].get(
        "process_control_exception_graph_privacy"
    )
    if privacy != C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_PRIVACY:
        raise AssertionError("C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_PRIVACY_INVALID")
    forbidden_material = candidate["commit_uncertainty_cleanup_gate"].get(
        "forbidden_outward_material"
    )
    if forbidden_material != (
        "raw connection",
        "cursor",
        "transaction controller",
        "mutation-slot object",
        "writer-lock object",
        "quarantine object",
        "ordinary commit exception",
        "close implementation details",
        "SQLite path",
        "SQL or parameters",
        "WorkSpec material",
    ):
        raise AssertionError("C2B3A_PROCESS_CONTROL_PUBLICATION_ORDER")


def _assert_c2b3a_process_control_failure(
    candidate: object,
    diagnostic: str,
) -> None:
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_process_control_candidate(candidate)
    assert str(exc_info.value) == diagnostic


def _assert_c2b3a_process_control_oracle_controls(source: str) -> None:
    graph_diagnostic = "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID"
    privacy_diagnostic = "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_PRIVACY_INVALID"
    try:
        tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    except SyntaxError:
        raise AssertionError(graph_diagnostic) from None
    top_level_functions = {
        statement.name: statement
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for branch_name, function_name, expected_argument in (
        C2B3A_PROCESS_CONTROL_POSITIVE_MODELS
    ):
        function = top_level_functions.get(function_name)
        if function is None:
            raise AssertionError(graph_diagnostic)
        function_source = ast.get_source_segment(source, function)
        if function_source is None:
            raise AssertionError(graph_diagnostic)
        if "repair4-private-" in function_source:
            raise AssertionError(privacy_diagnostic)

        injected_assignments = tuple(
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "injected_exception"
        )
        if len(injected_assignments) != 1:
            raise AssertionError(graph_diagnostic)
        injected = injected_assignments[0].value
        if (
            not isinstance(injected, ast.Call)
            or not isinstance(injected.func, ast.Name)
            or injected.func.id != branch_name
            or len(injected.args) != 1
            or not isinstance(injected.args[0], ast.Constant)
            or injected.args[0].value != expected_argument
            or injected.keywords
        ):
            raise AssertionError(graph_diagnostic)

        caught_handlers = tuple(
            node
            for node in ast.walk(function)
            if isinstance(node, ast.ExceptHandler)
            and isinstance(node.type, ast.Name)
            and node.type.id == branch_name
            and node.name == "caught_exception"
        )
        propagated_handlers = tuple(
            node
            for node in ast.walk(function)
            if isinstance(node, ast.ExceptHandler)
            and isinstance(node.type, ast.Name)
            and node.type.id == branch_name
            and node.name == "propagated_exception"
        )
        if len(caught_handlers) != 1 or len(propagated_handlers) != 1:
            raise AssertionError(graph_diagnostic)
        caught_handler = caught_handlers[0]
        raises = tuple(
            node for node in ast.walk(caught_handler) if isinstance(node, ast.Raise)
        )
        if (
            len(raises) != 1
            or caught_handler.body[-1] is not raises[0]
            or raises[0].exc is not None
            or raises[0].cause is not None
        ):
            raise AssertionError(graph_diagnostic)

        for node in ast.walk(caught_handler):
            targets: tuple[ast.AST, ...] = ()
            if isinstance(node, ast.Assign):
                targets = tuple(node.targets)
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
                targets = (node.target,)
            for target in targets:
                root = target
                while isinstance(root, (ast.Attribute, ast.Subscript)):
                    root = root.value
                if isinstance(root, ast.Name) and root.id == "caught_exception":
                    raise AssertionError(graph_diagnostic)
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "caught_exception"
                and node.func.attr in {"add_note", "with_traceback"}
            ):
                raise AssertionError(graph_diagnostic)

        direct_calls = {
            node.func.id
            for node in ast.walk(function)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        if not {
            "_bare_reraise_reference",
            "_exception_graph_snapshot",
            "_process_control_exception_graph_contains_private_material",
            "_traceback_signature",
        }.issubset(direct_calls):
            raise AssertionError(graph_diagnostic)
        required_source = (
            "caught_traceback_tail = caught_exception.__traceback__",
            "propagated_exception.__traceback__ is caught_traceback_tail",
            "caught_exception_graph == (None, None, False, False, None)",
            "len(propagated_traceback_signature) - len(caught_traceback_signature) == 0",
        )
        normalized_source = ast.unparse(function)
        if any(item not in normalized_source for item in required_source):
            raise AssertionError(graph_diagnostic)


def _c2b3a_process_control_oracle_mutant(
    source: str,
    branch_name: str,
    replacement: str,
) -> str:
    caught_anchor = f"        except {branch_name} as caught_exception:\n"
    propagated_anchor = f"    except {branch_name} as propagated_exception:\n"
    caught_index = source.index(caught_anchor)
    propagated_index = source.index(propagated_anchor, caught_index)
    bare_raise = "            raise\n"
    raise_index = source.rfind(bare_raise, caught_index, propagated_index)
    if raise_index < 0:
        raise AssertionError("C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID")
    return source[:raise_index] + replacement + source[raise_index + len(bare_raise) :]


def _assert_c2b3a_protected_factory_policy(source: str) -> None:
    diagnostic = "C2B3A_PROTECTED_EXPECTED_FACTORY_ROUTE_INVALID"
    try:
        tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    except SyntaxError:
        raise AssertionError(diagnostic) from None
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    observed = tuple(
        record
        for record in _c2b3a_oracle_protected_load_sites(tree, parents)
        if record[0] in {"_candidate", "_golden_candidate"}
    )
    expected = tuple(
        record
        for record in _c2b3a_oracle_expected_protected_load_sites()
        if record[0] in {"_candidate", "_golden_candidate"}
    )
    if observed != expected or any(record[3] != "direct_call_func" for record in observed):
        raise AssertionError(diagnostic)


def _c2b3a_physically_import_and_collect_mutant(
    tmp_path: Path,
    mutant_id: str,
    source: str,
    expected_nodes: tuple[str, ...] | None = C2B3A_ORACLE_EXPECTED_TEST_NODE_NAMES,
) -> None:
    mirror_root = tmp_path / mutant_id.lower()
    tests_root = mirror_root / "tests"
    tests_root.mkdir(mode=0o700, parents=True)
    mutant_path = tests_root / C2B3A_ORACLE_PATH.name
    written = mutant_path.write_text(source, encoding="utf-8")
    assert written == len(source)
    compile(source, str(mutant_path), "exec")

    import_tmp = mirror_root / "import-tmp"
    import_pycache = mirror_root / "import-pycache"
    collect_tmp = mirror_root / "collect-tmp"
    collect_pycache = mirror_root / "collect-pycache"
    collect_basetemp = mirror_root / "collect-basetemp"
    for directory in (
        import_tmp,
        import_pycache,
        collect_tmp,
        collect_pycache,
    ):
        directory.mkdir(mode=0o700)

    import_program = (
        "import importlib.util,pathlib,sys; "
        "path=pathlib.Path(sys.argv[1]).resolve(strict=True); "
        "spec=importlib.util.spec_from_file_location(sys.argv[2],path); "
        "module=importlib.util.module_from_spec(spec); "
        "sys.modules[spec.name]=module; "
        "spec.loader.exec_module(module); "
        "assert module.TEST_PATH == path"
    )
    imported = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            import_program,
            str(mutant_path),
            "c2b3a_" + mutant_id.lower(),
        ),
        cwd=ROOT,
        env={
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONPYCACHEPREFIX": str(import_pycache),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "TMPDIR": str(import_tmp),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert imported.returncode == 0, imported.stderr
    assert imported.stdout == ""
    assert imported.stderr == ""

    collected = subprocess.run(
        (
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            f"--basetemp={collect_basetemp}",
            "--collect-only",
            "-q",
            str(mutant_path),
        ),
        cwd=ROOT,
        env={
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONPYCACHEPREFIX": str(collect_pycache),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "TMPDIR": str(collect_tmp),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert collected.returncode == 0, collected.stderr
    collected_nodes = tuple(
        line.split("::", 1)[1]
        for line in collected.stdout.splitlines()
        if C2B3A_ORACLE_PATH.name + "::" in line
    )
    if expected_nodes is not None:
        assert collected_nodes == expected_nodes
        assert f"{len(expected_nodes)} tests collected" in collected.stdout
    else:
        assert collected_nodes
        assert " tests collected" in collected.stdout
    assert " warning" not in collected.stdout.lower()
    assert collected.stderr == ""


def _c2b3a_physically_import_and_collect_checker(
    tmp_path: Path,
    mutant_id: str,
    source: str,
) -> str:
    mirror_root = tmp_path / mutant_id.lower()
    tests_root = mirror_root / "tests"
    tests_root.mkdir(mode=0o700, parents=True)
    mutant_path = tests_root / Path(__file__).name
    assert mutant_path.write_text(source, encoding="utf-8") == len(source)
    physical_source = mutant_path.read_text(encoding="utf-8")
    compile(physical_source, str(mutant_path), "exec")

    import_tmp = mirror_root / "import-tmp"
    import_pycache = mirror_root / "import-pycache"
    collect_tmp = mirror_root / "collect-tmp"
    collect_pycache = mirror_root / "collect-pycache"
    collect_basetemp = mirror_root / "collect-basetemp"
    for directory in (import_tmp, import_pycache, collect_tmp, collect_pycache):
        directory.mkdir(mode=0o700)

    import_program = (
        "import importlib.util,pathlib,sys; "
        "path=pathlib.Path(sys.argv[1]).resolve(strict=True); "
        "spec=importlib.util.spec_from_file_location(sys.argv[2],path); "
        "module=importlib.util.module_from_spec(spec); "
        "sys.modules[spec.name]=module; "
        "spec.loader.exec_module(module); "
        "assert pathlib.Path(module.__file__).resolve() == path"
    )
    imported = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            import_program,
            str(mutant_path),
            "c2b3a_checker_" + mutant_id.lower().replace("-", "_"),
        ),
        cwd=ROOT,
        env={
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONPYCACHEPREFIX": str(import_pycache),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "TMPDIR": str(import_tmp),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert imported.returncode == 0, imported.stderr
    assert imported.stdout == ""
    assert imported.stderr == ""

    collected = subprocess.run(
        (
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            f"--basetemp={collect_basetemp}",
            "--collect-only",
            "-q",
            str(mutant_path),
        ),
        cwd=ROOT,
        env={
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONPYCACHEPREFIX": str(collect_pycache),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "TMPDIR": str(collect_tmp),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert collected.returncode == 0, collected.stderr
    assert (
        Path(__file__).name
        + "::test_c2b3a_m16_m65_executable_efficacy_is_exact"
        in collected.stdout
    )
    assert " tests collected" in collected.stdout
    assert " warning" not in collected.stdout.lower()
    assert collected.stderr == ""
    return physical_source


def _c2b3a_physically_run_checker_guard_rejection(
    tmp_path: Path,
    mutant_id: str,
) -> None:
    mirror_root = tmp_path / mutant_id.lower()
    mutant_path = mirror_root / "tests" / Path(__file__).name
    execute_tmp = mirror_root / "guard-execute-tmp"
    execute_pycache = mirror_root / "guard-execute-pycache"
    for directory in (execute_tmp, execute_pycache):
        directory.mkdir(mode=0o700)
    execute_program = (
        "import importlib.util\n"
        "import pathlib\n"
        "import sys\n"
        "path = pathlib.Path(sys.argv[1]).resolve(strict=True)\n"
        "spec = importlib.util.spec_from_file_location(sys.argv[2], path)\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "sys.modules[spec.name] = module\n"
        "spec.loader.exec_module(module)\n"
        "try:\n"
        "    module.test_c2b3a_m16_m65_executable_efficacy_is_exact()\n"
        "except AssertionError as exc:\n"
        "    assert exc.args == "
        "('C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID',)\n"
        "else:\n"
        "    raise AssertionError('C2B3A_EFFICACY_CHECKER_GUARD_BYPASS')\n"
    )
    executed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            execute_program,
            str(mutant_path),
            "c2b3a_guard_" + mutant_id.lower().replace("-", "_"),
        ),
        cwd=ROOT,
        env={
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONPYCACHEPREFIX": str(execute_pycache),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "TMPDIR": str(execute_tmp),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert executed.returncode == 0, executed.stderr
    assert executed.stdout == ""
    assert executed.stderr == ""


def _c2b3a_physically_reject_planning_counterfactual(
    tmp_path: Path,
    mutant_id: str,
    direct_source: str,
    planning_counterfactual: str,
) -> None:
    test_name = "test_stage_specific_planning_counterfactual_is_rejected"
    physical_source = (
        direct_source
        + "\n\ndef "
        + test_name
        + "() -> None:\n"
        + "    planning_counterfactual = "
        + repr(planning_counterfactual)
        + "\n"
        + "    with pytest.raises(_ContractViolation) as exc_info:\n"
        + "        _validate_planning_status(planning_counterfactual)\n"
        + "    assert str(exc_info.value) == "
        + repr("C2B3A_PLANNING_PROJECTION_INVALID")
        + "\n"
    )
    _c2b3a_physically_import_and_collect_mutant(
        tmp_path,
        mutant_id,
        physical_source,
        expected_nodes=None,
    )

    mirror_root = tmp_path / mutant_id.lower()
    mutant_path = mirror_root / "tests" / C2B3A_ORACLE_PATH.name
    execute_tmp = mirror_root / "execute-tmp"
    execute_pycache = mirror_root / "execute-pycache"
    execute_basetemp = mirror_root / "execute-basetemp"
    for directory in (execute_tmp, execute_pycache):
        directory.mkdir(mode=0o700)
    executed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            f"--basetemp={execute_basetemp}",
            "-q",
            str(mutant_path) + "::" + test_name,
        ),
        cwd=ROOT,
        env={
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONPYCACHEPREFIX": str(execute_pycache),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "TMPDIR": str(execute_tmp),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert executed.returncode == 0, executed.stderr
    assert "1 passed" in executed.stdout
    assert " warning" not in executed.stdout.lower()
    assert executed.stderr == ""


def _c2b3a_semantic_function_body_mutant(
    source: str,
    function_name: str,
    replacement_body: str,
) -> str:
    tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    function = _c2b3a_oracle_top_level_function(tree, function_name)
    if not function.body or function.end_lineno is None:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    source_lines = source.splitlines(keepends=True)
    indentation = " " * function.body[0].col_offset
    replacement_lines = replacement_body.splitlines()
    replacement = "".join(
        indentation + line + "\n" if line else "\n"
        for line in replacement_lines
    )
    return "".join(
        source_lines[: function.body[0].lineno - 1]
        + [replacement]
        + source_lines[function.end_lineno :]
    )


def _c2b3a_semantic_assertions_true_mutant(
    source: str,
    function_name: str,
) -> str:
    tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    function = _c2b3a_oracle_top_level_function(tree, function_name)
    assertions = tuple(
        node for node in ast.walk(function) if isinstance(node, ast.Assert)
    )
    if not assertions:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    for assertion in assertions:
        assertion.test = ast.copy_location(ast.Constant(value=True), assertion.test)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def _c2b3a_semantic_assertions_self_comparison_mutant(
    source: str,
    function_name: str,
) -> str:
    tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    function = _c2b3a_oracle_top_level_function(tree, function_name)
    assertions = tuple(
        node for node in ast.walk(function) if isinstance(node, ast.Assert)
    )
    if not assertions:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    for assertion in assertions:
        rendered = ast.unparse(assertion.test)
        replacement = ast.parse(
            f"({rendered}) == ({rendered})",
            mode="eval",
        ).body
        assertion.test = ast.copy_location(replacement, assertion.test)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def _c2b3a_semantic_expected_literal_inventory_mutant(
    source: str,
    literal_name: str,
    function_name: str,
    *,
    remove: bool,
) -> str:
    tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    assignment = _c2b3a_oracle_literal_assignment(tree, literal_name)
    function = _c2b3a_oracle_top_level_function(tree, function_name)
    if remove:
        tree.body.remove(assignment)
    elif isinstance(assignment.value, ast.Dict):
        assignment.value = ast.copy_location(ast.Dict(keys=[], values=[]), assignment.value)
    elif isinstance(assignment.value, ast.Tuple):
        assignment.value = ast.copy_location(ast.Tuple(elts=[], ctx=ast.Load()), assignment.value)
    else:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    function.body = [
        ast.copy_location(ast.Assert(test=ast.Constant(value=True)), function.body[0])
    ]
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def _c2b3a_semantic_replace_in_function(
    source: str,
    function_name: str,
    old: str,
    new: str,
) -> str:
    tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    function = _c2b3a_oracle_top_level_function(tree, function_name)
    if function.end_lineno is None:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    source_lines = source.splitlines(keepends=True)
    start = function.lineno - 1
    end = function.end_lineno
    function_source = "".join(source_lines[start:end])
    if function_source.count(old) != 1:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    replacement = function_source.replace(old, new, 1)
    return "".join(source_lines[:start] + [replacement] + source_lines[end:])


def _c2b3a_semantic_top_level_loop_pass_mutant(
    source: str,
    function_name: str,
) -> str:
    tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    function = _c2b3a_oracle_top_level_function(tree, function_name)
    loops = tuple(
        statement for statement in function.body if isinstance(statement, ast.For)
    )
    if len(loops) != 1 or loops[0].end_lineno is None:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    loop = loops[0]
    source_lines = source.splitlines(keepends=True)
    replacement = " " * loop.col_offset + "pass\n"
    return "".join(
        source_lines[: loop.lineno - 1]
        + [replacement]
        + source_lines[loop.end_lineno :]
    )


def _c2b3a_efficacy_loop_pass_mutant(source: str) -> str:
    tree = ast.parse(source, filename=Path(__file__).name)
    function = _c2b3a_oracle_top_level_function(
        tree,
        "_assert_c2b3a_mutant_dataflow_semantics",
    )
    loops = tuple(
        statement
        for statement in function.body
        if isinstance(statement, ast.For)
        and isinstance(statement.iter, ast.Name)
        and statement.iter.id == "C2B3A_LINEAR_MUTANT_FUNCTIONS"
    )
    if len(loops) != 1 or not loops[0].body or loops[0].end_lineno is None:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    loop = loops[0]
    first = loop.body[0]
    source_lines = source.splitlines(keepends=True)
    replacement = " " * first.col_offset + "pass\n"
    return "".join(
        source_lines[: first.lineno - 1]
        + [replacement]
        + source_lines[loop.end_lineno :]
    )


def _c2b3a_efficacy_loop_iter_mutant(source: str, expression: str) -> str:
    tree = ast.parse(source, filename=Path(__file__).name)
    function = _c2b3a_oracle_top_level_function(
        tree,
        "_assert_c2b3a_mutant_dataflow_semantics",
    )
    loops = tuple(
        statement
        for statement in function.body
        if isinstance(statement, ast.For)
        and isinstance(statement.iter, ast.Name)
        and statement.iter.id == "C2B3A_LINEAR_MUTANT_FUNCTIONS"
    )
    if len(loops) != 1:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    loops[0].iter = ast.copy_location(
        ast.parse(expression, mode="eval").body,
        loops[0].iter,
    )
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def _c2b3a_cleanup_step_removed_mutant(source: str, step: str) -> str:
    tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    function = _c2b3a_oracle_top_level_function(tree, "_cleanup_reference")

    def records_entry(statement: ast.stmt) -> bool:
        return any(
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "entered"
            and isinstance(node.op, ast.Add)
            and isinstance(node.value, ast.Tuple)
            and len(node.value.elts) == 1
            and isinstance(node.value.elts[0], ast.Constant)
            and node.value.elts[0].value == step
            for node in ast.walk(statement)
        )

    matching_indexes = tuple(
        index
        for index, statement in enumerate(function.body)
        if records_entry(statement)
    )
    if len(matching_indexes) != 1:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    index = matching_indexes[0]
    first = function.body[index]
    last = first
    if step == "P0":
        if index + 1 >= len(function.body):
            raise AssertionError(
                "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
            )
        last = function.body[index + 1]
        if not any(
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "completed"
            and isinstance(node.value, ast.Tuple)
            and len(node.value.elts) == 1
            and isinstance(node.value.elts[0], ast.Constant)
            and node.value.elts[0].value == "P0"
            for node in ast.walk(last)
        ):
            raise AssertionError(
                "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
            )
    if first.end_lineno is None or last.end_lineno is None:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    source_lines = source.splitlines(keepends=True)
    return "".join(
        source_lines[: first.lineno - 1] + source_lines[last.end_lineno :]
    )


def _c2b3a_physically_execute_semantic_mutant(
    tmp_path: Path,
    mutant_id: str,
    source: str,
    selected_node: str,
    require_selected_pass: bool = False,
) -> None:
    _c2b3a_physically_import_and_collect_mutant(tmp_path, mutant_id, source)
    mirror_root = tmp_path / mutant_id.lower()
    mutant_path = mirror_root / "tests" / C2B3A_ORACLE_PATH.name
    execute_tmp = mirror_root / "execute-tmp"
    execute_pycache = mirror_root / "execute-pycache"
    execute_basetemp = mirror_root / "execute-basetemp"
    execute_tmp.mkdir(mode=0o700)
    execute_pycache.mkdir(mode=0o700)
    executed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            f"--basetemp={execute_basetemp}",
            "-q",
            "--tb=no",
            f"{mutant_path}::{selected_node}",
        ),
        cwd=ROOT,
        env={
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONPYCACHEPREFIX": str(execute_pycache),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "TMPDIR": str(execute_tmp),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert executed.returncode in (0, 1), executed.stderr
    if require_selected_pass:
        assert executed.returncode == 0
        assert "1 passed" in executed.stdout
    else:
        assert "1 passed" in executed.stdout or "1 failed" in executed.stdout
    assert " skipped" not in executed.stdout
    assert " xfailed" not in executed.stdout
    assert " deselected" not in executed.stdout
    assert " warning" not in executed.stdout.lower()
    assert executed.stderr == ""


def _assert_c2b3a_semantic_mutant_is_physical(
    tmp_path: Path,
    mutant_id: str,
    source: str,
    selected_node: str,
    require_selected_pass: bool = False,
) -> None:
    _c2b3a_physically_execute_semantic_mutant(
        tmp_path,
        mutant_id,
        source,
        selected_node,
        require_selected_pass,
    )
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_independent_oracle_architecture(source)
    assert (
        str(exc_info.value)
        == "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
    )


def _section(text: str, heading: str) -> str:
    role = "c2b0.owner"
    headings, _unfenced = _markdown_scan(text, role=role)
    matches = tuple(item for item in headings if item[1] == heading)
    _require(bool(matches), f"{role}|heading={heading}|failure=missing")
    _require(len(matches) == 1, f"{role}|heading={heading}|failure=duplicate")
    selected = matches[0]
    _require(selected[0] == 2, f"{role}|heading={heading}|failure=wrong_level")
    selected_index = headings.index(selected)
    boundaries = tuple(
        following
        for following in headings[selected_index + 1 :]
        if following[0] <= selected[0]
    )
    if boundaries:
        end = boundaries[0][2]
    else:
        _require(
            heading == SECTION_HEADINGS[-1],
            f"{role}|heading={heading}|failure=missing_same_or_higher_boundary",
        )
        end = len(text)
    return text[selected[3] : end]


def _section_prose(text: str, heading: str) -> str:
    return _compact(
        _unfenced_markdown(
            _section(text, heading),
            role=f"c2b0.owner.section.{heading}",
        )
    )


def _assert_c2b3a_owner_addendum_prose(text: str) -> None:
    diagnostic = "C2B3A_COMMIT_CLOSE_OWNER_PROSE_INVALID"
    narrowing_heading = "## 36. C2B3 Vertical-Slice Governing Narrowing Addendum\n"
    if type(text) is str and narrowing_heading in text:
        if text.count(narrowing_heading) != 1:
            raise AssertionError(diagnostic)
        try:
            _assert_narrowed_reset_governing_surface(
                _narrowed_reset_addendum(text)
            )
        except AssertionError:
            raise AssertionError(diagnostic) from None
        text = text[: text.index(narrowing_heading)].rstrip("\n") + "\n"
    section_heading = "## 35. C2B3A Program-Initialization Contract Freeze\n"
    markers = (
        "    # C2B3A_OWNER_ADDENDUM_BEGIN",
        "    # C2B3A_OWNER_ADDENDUM_STRUCTURED_END",
        "<!-- C2B3_PROGRAM_INITIALIZATION_GOLDEN_VECTOR_PYTHON_BEGIN -->",
        "<!-- C2B3_PROGRAM_INITIALIZATION_GOLDEN_VECTOR_PYTHON_END -->",
        "<!-- C2B3A_OWNER_ADDENDUM_EXPLANATORY_BEGIN -->",
        "<!-- C2B3A_OWNER_AUTHORITY_PROSE_BEGIN -->",
        "<!-- C2B3A_OWNER_AUTHORITY_PROSE_END -->",
        "<!-- C2B3A_OWNER_PROCESS_CONTROL_PROSE_BEGIN -->",
        "<!-- C2B3A_OWNER_PROCESS_CONTROL_PROSE_END -->",
        "<!-- C2B3A_OWNER_CLEANUP_PROSE_BEGIN -->",
        "<!-- C2B3A_OWNER_CLEANUP_PROSE_END -->",
        "<!-- C2B3A_OWNER_FUTURE_SCOPE_PROSE_BEGIN -->",
        "<!-- C2B3A_OWNER_FUTURE_SCOPE_PROSE_END -->",
        "<!-- C2B3A_OWNER_RETAINED_TAIL_BEGIN -->",
        "<!-- C2B3A_OWNER_RETAINED_TAIL_END -->",
        "<!-- C2B3A_OWNER_ADDENDUM_END -->",
    )
    if type(text) is not str or text.count(section_heading) != 1:
        raise AssertionError(diagnostic)
    if any(text.count(marker) != 1 for marker in markers):
        raise AssertionError(diagnostic)
    positions = tuple(text.index(marker) for marker in markers)
    if positions != tuple(sorted(positions)):
        raise AssertionError(diagnostic)

    section_start = text.index(section_heading)
    addendum_begin = positions[0]
    structured_end = positions[1]
    vector_begin = positions[2]
    vector_end = positions[3]
    explanatory_begin = positions[4]
    if (
        text[section_start:addendum_begin]
        != C2B3A_OWNER_PRE_ADDENDUM_SECTION_35_PREFIX
    ):
        raise AssertionError(diagnostic)

    structured_open = (
        "    # C2B3A_OWNER_ADDENDUM_BEGIN\n"
        "    # C2B3A COMMIT/close outcome addendum\n"
        "    \"commit_close_outcome_addendum\": {\n"
    )
    if not text.startswith(structured_open, addendum_begin):
        raise AssertionError(diagnostic)
    structured_region = text[
        addendum_begin : structured_end + len(markers[1])
    ]
    comment_lines = tuple(
        line for line in structured_region.splitlines()
        if line.lstrip().startswith("#")
    )
    if comment_lines != (
        "    # C2B3A_OWNER_ADDENDUM_BEGIN",
        "    # C2B3A COMMIT/close outcome addendum",
        "    # C2B3A_OWNER_ADDENDUM_STRUCTURED_END",
    ):
        raise AssertionError(diagnostic)
    for required_source in (
        '    "commit_close_outcome_addendum": {',
        '        "normative_surface_and_precedence": {',
        '        "legacy_exception_probe_ledger_classification": {',
        '            "future_implementation_scope_supersession": {',
    ):
        if structured_region.count(required_source) != 1:
            raise AssertionError(diagnostic)

    structured_to_vector_end = vector_begin + len(markers[2]) + 1
    if (
        text[structured_end:structured_to_vector_end]
        != C2B3A_OWNER_STRUCTURED_TO_VECTOR_BRIDGE
    ):
        raise AssertionError(diagnostic)
    if (
        text[vector_end:explanatory_begin]
        != C2B3A_OWNER_VECTOR_TO_EXPLANATORY_BRIDGE
    ):
        raise AssertionError(diagnostic)
    if text[explanatory_begin:] != C2B3A_OWNER_EXPLANATORY_SUFFIX:
        raise AssertionError(diagnostic)
    if not text.endswith(markers[-1] + "\n"):
        raise AssertionError(diagnostic)


def _summary_section(text: str, heading: str, *, role: str) -> str:
    headings, _unfenced = _markdown_scan(text, role=role)
    matches = tuple(item for item in headings if item[1] == heading)
    _require(bool(matches), f"{role}|heading={heading}|failure=missing")
    _require(len(matches) == 1, f"{role}|heading={heading}|failure=duplicate")
    selected = matches[0]
    _require(selected[0] == 2, f"{role}|heading={heading}|failure=wrong_level")
    selected_index = headings.index(selected)
    boundary = next(
        (
            following
            for following in headings[selected_index + 1 :]
            if following[0] <= selected[0]
        ),
        None,
    )
    end = len(text) if boundary is None else boundary[2]
    return text[selected[3] : end]


def _assert_summary_target(
    text: str,
    *,
    role: str,
    heading: str,
    required: str,
) -> None:
    section = _compact(
        _unfenced_markdown(
            _summary_section(text, heading, role=role),
            role=f"{role}.section",
        )
    )
    _require(
        required in section,
        f"{role}|heading={heading}|failure=target_claim_missing",
    )
    visible = _unfenced_markdown(text, role=role).lower()
    for forbidden in (
        "no migration number is reserved here",
        "No migration number is reserved.",
        "Exact C2B schema remains wholly open.",
        "C2B is currently implemented.",
        "C2B migrations 0002 and 0003 are installed.",
        "0002 is absent.",
        "0003 is installed.",
        "Application generation is currently 3.",
    ):
        _require(
            forbidden.lower() not in visible,
            f"{role}|heading={heading}|failure=contradictory_current_status",
        )


def _assert_sqlite_migration_summary(text: str) -> None:
    role = "c2b0.sqlite_migration"
    heading = "C2B0 Target Migration Sequence"
    section = _summary_section(text, heading, role=role)
    prose = _compact(_unfenced_markdown(section, role=f"{role}.section"))
    blocks = _text_blocks(section)
    for phrase in (
        "`CURRENT IMPLEMENTED CONTRACT` for C2B2 Slice 1 generation 2 / terminal 0002",
        "`ACCEPTED TARGET CONTRACT` for migration 0003",
        "C2B1 is a framework-only source/test reset with no SQL or database change",
        "C2B2 Slice 1 advances implemented application generation from 1 to 2",
        "makes the terminal catalog tip 0002",
        "C2B3 remains generation 2 with terminal tip 0002",
        "C2B4 adds migration 0003 while retaining application generation 2",
        "C2B5 and C2B6 remain generation 2 with terminal tip 0003",
        "historical migration 0001 remains `[1,1]`, while 0002 and 0003 are `[2,2]`",
        "Ordinary open never silently migrates and never accepts an older prefix",
        "one exact non-empty supported older catalog prefix",
        "gaps, unknown or partial rows, and divergent bounds are rejected",
        "one exact contiguous suffix leading to the current terminal tip",
        "the complete intended packaged suffix is one administrative transaction",
        "Failure before commit restores the complete exact prior supported prefix",
        "If an administrative commit attempt raises, migration recovery must",
        "An `unresolved` result forbids automatic rerun and automatic append of a missing remainder",
        "generation-1 binary rejects sequences 2 and 3 as newer and unsupported",
        "generation-2 terminal-0002 binary ordinarily opens exact 0002 and rejects 0003 as newer",
        "generation-2 terminal-0003 binary ordinarily opens exact 0003",
        "no cumulative schema snapshot is introduced",
    ):
        _require(
            phrase in prose,
            f"{role}|heading={heading}|failure=generation_prefix_or_rollback",
        )
    _require(
        blocks
        == (
            MIGRATION_PATHS,
            MIGRATION_TRANSACTION_PATHS,
            MIGRATION_TRANSACTION_COMPONENTS,
            MIGRATION_RECOVERY_STEPS,
            MIGRATION_COMMITTED_EXACT,
            MIGRATION_DEFINITELY_NOT_COMMITTED,
            MIGRATION_UNRESOLVED,
            SQLITE_MIGRATION_DEFINITIONS,
            SQLITE_MIGRATION_SCHEMA_TOTALS,
        ),
        f"{role}|heading={heading}|failure=transaction_or_recovery_mapping",
    )
    lowered = prose.lower()
    for forbidden in (*MIGRATION_FORBIDDEN_CLAIMS, *C2B1_REPAIR1_FORBIDDEN_CLAIMS):
        _require(
            forbidden not in lowered,
            f"{role}|heading={heading}|failure=forbidden_migration_claim",
        )


def _assert_owner_structure(text: str) -> None:
    role = "c2b0.owner"
    headings, _unfenced = _markdown_scan(text, role=role)
    h1 = tuple(title for level, title, _start, _end in headings if level == 1)
    h2 = tuple(title for level, title, _start, _end in headings if level == 2)
    _require(
        h1 == ("C2B Durable Development State",),
        "c2b0.owner|heading=C2B Durable Development State|failure=missing_duplicate_or_relocated",
    )
    _require(
        h2 == SECTION_HEADINGS,
        "c2b0.owner|heading=<inventory>|failure=missing_duplicate_reordered_or_relocated",
    )
    for heading in SECTION_HEADINGS[:-1]:
        _section(text, heading)
    _section(text, SECTION_HEADINGS[-1])


def _text_blocks(section: str) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(line for line in block.content.splitlines() if line)
        for block in _top_level_fenced_blocks(section, role="c2b0.text_blocks")
        if block.info.strip(" \t") == "text"
    )


def _semantic_inventory_text(section: str, *, role: str) -> str:
    visible = _unfenced_markdown(section, role=role)
    block_text = "\n".join("\n".join(block) for block in _text_blocks(section))
    return visible + "\n" + block_text


def _replace_once(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1
    return text.replace(old, new, 1)


def _inventory_pseudo_closer_mutation(
    text: str,
    *,
    final_item: str,
    hidden_addition: str,
    closer_suffix: str,
) -> str:
    return _replace_once(
        text,
        final_item + "\n```",
        final_item
        + "\n```"
        + closer_suffix
        + "\n"
        + hidden_addition
        + "\n````",
    )


def _outer_nonsemantic_inventory_examples(hidden_addition: str) -> str:
    return (
        "~~~~example\n"
        "```text\n"
        + hidden_addition
        + "\n```\n"
        "~~~~\n\n"
        "````example\n"
        "~~~text\n"
        + hidden_addition
        + "\n~~~\n"
        "````\n"
    )


def _insert_before_owner_heading(
    text: str,
    *,
    next_heading: str,
    insertion: str,
) -> str:
    marker = "\n## " + next_heading + "\n"
    return _replace_once(text, marker, "\n" + insertion + marker)


def _assert_decision_and_cancel_contract(text: str) -> None:
    decisions = _section(text, SECTION_HEADINGS[5])
    cancel = _compact(_section(text, SECTION_HEADINGS[6]))
    _require(
        _text_blocks(decisions) == (DECISION_KINDS, DECISION_VERSION_EFFECTS),
        "c2b0.decisions|heading=6. Exact Decision-Kind Inventory|failure=closed_inventory",
    )
    _require(
        re.search(r"\bretry\b", _section_prose(text, SECTION_HEADINGS[5]), re.IGNORECASE)
        is None,
        "c2b0.decisions|heading=6. Exact Decision-Kind Inventory|failure=ninth_kind",
    )
    assert "cancel: no program-version advance" in decisions
    assert "`cancel` is a real immutable Coordinator decision" in cancel
    assert "Targets of class `cancel_effect` or `local_git_commit` are rejected." in cancel
    assert "An author target forbids the paired capsule fields." in cancel
    assert "A validation or review target requires the exact paired capsule-manifest ref and portable digest." in cancel
    assert "creates no version, attempt, candidate, command, effect, delivery, observation" in cancel
    for forbidden in (
        "block substitutes for cancel",
        "cancel creates a semantic attempt",
        "cancel creates a candidate",
        "cancel creates a WorkerCommandV1",
        "author target requires capsule fields",
    ):
        assert forbidden not in cancel


def _assert_basis_and_effect_contract(text: str) -> None:
    basis = _compact(_section(text, SECTION_HEADINGS[7]))
    cardinality = _compact(_section(text, SECTION_HEADINGS[8]))
    author = _compact(_section(text, SECTION_HEADINGS[9]))
    bound = _compact(_section(text, SECTION_HEADINGS[10]))
    assert "basis_decision_ref TEXT NOT NULL" in basis
    assert "REFERENCES development_decisions(decision_ref)" in basis
    assert "exact initialize, repair, or attempt-selecting replan decision" in basis
    assert "exact selection decision already bound to the existing attempt" in basis
    assert "exact cancel decision that preassigned the cancellation effect" in basis
    assert "`block` and `terminal_reject` cannot be a cancellation basis." in basis
    assert "`accept` and `redeliver` cannot be an author basis." in basis
    assert "development_effect_intents.command_ref: non-unique foreign key" in cardinality
    assert "one author_candidate effect per command" in cardinality
    assert "two originating commands for K1 is rejected" in cardinality
    assert "semantic attempt candidate identity through the attempt graph" in author
    assert "one originating WorkerCommandV1" in author
    for required_existing in (
        "existing semantic attempt",
        "existing candidate",
        "existing AttemptFence",
        "existing originating command",
        "existing post-bound author EffectFence",
    ):
        assert required_existing in bound
    assert "It creates no new semantic attempt, candidate, `WorkerCommandV1`, author effect, program version" in bound
    assert "Cancellation CAS-updates the target effect knowledge to `cancellation_effect_established`." in bound
    compacted_text = _compact(text).lower()
    for forbidden in (
        "basis_decision_ref TEXT NULL",
        "validation creates a second semantic attempt",
        "review creates a second WorkerCommandV1",
        "development_effect_intents.command_ref: unique foreign key",
        "two author effects per command are permitted",
    ):
        assert forbidden.lower() not in compacted_text


def _assert_stop_contract(text: str) -> None:
    section = _section(text, SECTION_HEADINGS[14])
    blocks = _text_blocks(section)
    matrix = next(block for block in blocks if block[0] == "initialize program: block")
    required = (
        "establish author effect: block",
        "establish validation effect: block",
        "establish review effect: block",
        "redeliver productive effect: block",
        "ingest source observation: permit",
        "record cancel decision: permit",
        "establish cancellation effect and initial cancellation delivery: permit",
        "redeliver an existing cancellation effect: permit",
        "perform external cancellation: not implemented",
    )
    for rule in required:
        assert rule in matrix
    compact = _compact(section)
    assert "`coding_global_stop_active` and creates no receipt" in compact
    assert "`global_stop_version_conflict` and creates no receipt" in compact
    assert "Exact replay of an already committed operation precedes fresh stop/head checks" in compact


def _assert_privacy_contract(text: str) -> None:
    custody = _compact(_section(text, SECTION_HEADINGS[15]))
    values = _compact(_section(text, SECTION_HEADINGS[16]))
    compacted = _compact(text)
    assert "The physical custodian is explicitly deferred." in custody
    assert "Coordinator SQLite is a safe-reference holder, not a private-material store." in custody
    assert "A safe ref is not retrieval authority." in custody
    assert "SQLite cannot reconstruct the private WorkSpec." in custody
    assert "Restart-safe author establishment and worker launch remain blocked" in custody
    assert "WorkSpecV1: safe projection only; exclude objective, requirements, exclusions" in values
    assert "CapsuleEntryV1: persist nothing" in values
    assert "Candidate and capsule bytes, capsule entries, paths, modes, file digests, lengths" in values
    for forbidden in (
        "C2B may retain objective text",
        "A safe ref is retrieval authority",
        "SQLite can reconstruct the private WorkSpec",
        "CapsuleEntryV1: persist complete mapping",
    ):
        _require(
            forbidden not in compacted,
            "c2b0.privacy|heading=<all>|failure=forbidden_privacy_claim",
        )


def _assert_schema_contract(text: str) -> None:
    migration_0001 = _section_prose(text, SECTION_HEADINGS[19])
    migration_0002 = _section(text, SECTION_HEADINGS[20])
    migration_0003 = _section(text, SECTION_HEADINGS[21])
    totals_section = _section(text, SECTION_HEADINGS[22])
    totals = _section_prose(text, SECTION_HEADINGS[22])
    indexes = _section(text, SECTION_HEADINGS[23])
    assert "Migration `0001_initial` retains immutable bytes, checksum, history, and meanings." in migration_0001, (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=0001_immutability"
    )
    assert "C2B1 is the framework-only source/test reset that added no SQL or database change" in migration_0001, (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=c2b1_scope"
    )
    blocks_0002 = _text_blocks(migration_0002)
    blocks_0003 = _text_blocks(migration_0003)
    semantic_0002 = _semantic_inventory_text(
        migration_0002,
        role="c2b0.schema.migration_0002",
    )
    semantic_0003 = _semantic_inventory_text(
        migration_0003,
        role="c2b0.schema.migration_0003",
    )
    semantic_totals = _semantic_inventory_text(
        totals_section,
        role="c2b0.schema.totals",
    )
    semantic_indexes = _semantic_inventory_text(
        indexes,
        role="c2b0.schema.indexes",
    )
    trigger_semantics = "\n".join((semantic_0002, semantic_0003, semantic_totals))
    trigger_lines = tuple(line.strip() for line in trigger_semantics.splitlines())
    schema_role_claims = tuple(
        line
        for line in trigger_lines
        if re.match(r"^schema(?: tip)? [0-9]{4}[ \t]*:", line, re.IGNORECASE)
        and "trigger" in line.lower()
    )
    _require(
        schema_role_claims == TRIGGER_SCHEMA_ROLE_CLAIMS,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_role_inventory",
    )
    migration_addition_role_claims = tuple(
        line
        for line in trigger_lines
        if re.match(r"^000[0-9][ \t]*:[ \t]*[0-9]+[ \t]+tables[ \t]*,", line, re.IGNORECASE)
        and "trigger" in line.lower()
    )
    _require(
        migration_addition_role_claims == TRIGGER_MIGRATION_ADDITION_ROLE_CLAIMS,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_role_inventory",
    )
    aggregate_role_claims = tuple(
        _compact(match.group(0))
        for match in re.finditer(
            r"\bC2B(?:[ \t]+also)?[ \t]+adds\b[^.]*\btriggers\b[^.]*\.",
            trigger_semantics,
            re.IGNORECASE,
        )
    )
    _require(
        aggregate_role_claims == TRIGGER_AGGREGATE_ROLE_CLAIMS,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_role_inventory",
    )
    _require(
        blocks_0002.count(TABLES_0002) == 1,
        "c2b0.schema|heading=21. Migration 0002|failure=table_inventory",
    )
    _require(
        blocks_0003.count(TABLES_0003) == 1,
        "c2b0.schema|heading=22. Migration 0003|failure=table_inventory",
    )
    _require(
        _text_blocks(indexes) == (EXPLICIT_INDEXES,),
        "c2b0.schema|heading=24. Exact Explicit Indexes|failure=index_inventory",
    )
    identifiers_0002 = set(re.findall(r"\bdevelopment_[a-z0-9_]+\b", semantic_0002))
    identifiers_0003 = set(re.findall(r"\bdevelopment_[a-z0-9_]+\b", semantic_0003))
    _require(
        identifiers_0002 == set(TABLES_0002),
        "c2b0.schema|heading=21. Migration 0002|failure=additive_table_inventory",
    )
    _require(
        identifiers_0003 == set(TABLES_0003),
        "c2b0.schema|heading=22. Migration 0003|failure=additive_table_inventory",
    )
    _require(
        "C2B adds exactly twenty-eight tables, forty-six triggers, and two explicit indexes." in totals,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=addition_totals",
    )
    arithmetic_blocks = tuple(
        block
        for block in _text_blocks(totals_section)
        if block and block[0].startswith("0002: 15 immutable tables")
    )
    _require(
        len(arithmetic_blocks) == 1,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_arithmetic",
    )
    arithmetic = arithmetic_blocks[0]
    _require(
        arithmetic == TRIGGER_ARITHMETIC,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_arithmetic",
    )
    _require(
        _text_blocks(totals_section)
        == (SCHEMA_TOTALS, MIGRATION_ADDITION_TOTALS, TRIGGER_ARITHMETIC),
        "c2b0.schema|heading=23. Exact Schema Totals|failure=closed_totals_blocks",
    )
    arithmetic_claims = tuple(
        line.strip()
        for line in "\n".join(
            (semantic_0002, semantic_0003, semantic_totals)
        ).splitlines()
        if re.match(r"^[ \t]*000[0-9][ \t]*:", line, re.IGNORECASE)
    )
    _require(
        arithmetic_claims == MIGRATION_ADDITION_TOTALS + TRIGGER_ARITHMETIC,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=additive_trigger_arithmetic",
    )
    _require(
        "one available latch row" in totals,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=latch_seed",
    )
    visible = _unfenced_markdown(text, role="c2b0.owner")
    _require(
        "third_explicit_index" not in visible,
        "c2b0.schema|heading=24. Exact Explicit Indexes|failure=extra_index",
    )
    _require(
        "one broad migration" not in visible,
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=broad_migration",
    )
    index_identifiers = set(
        re.findall(r"\b(?:idx|uq)_[a-z0-9_]+\b", semantic_indexes)
    )
    _require(
        index_identifiers == set(EXPLICIT_INDEXES),
        "c2b0.schema|heading=24. Exact Explicit Indexes|failure=additive_index",
    )
    trigger_identifier_sections = semantic_0002 + semantic_0003 + semantic_totals
    _require(
        re.search(
            r"\b[a-z0-9]+(?:_[a-z0-9]+)*_trigger(?:_[a-z0-9]+)*\b",
            trigger_identifier_sections,
        )
        is None,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=additive_trigger",
    )
    lowered_schema = _compact(
        semantic_0002 + semantic_0003 + semantic_totals + semantic_indexes
    ).lower()
    for forbidden in (
        "migration 0002 also creates an additional table",
        "migration 0003 also creates an additional table",
        "migration 0003 also creates an extra trigger",
        "one trigger is omitted",
        "the latch update is unrestricted",
        "a third explicit index is added",
        "a reporting index is added",
        "a lineage index is added",
        "a browsing index is added",
        "an analytics index is added",
    ):
        _require(
            forbidden not in lowered_schema,
            "c2b0.schema|heading=<inventory>|failure=additive_schema_claim",
        )
    mutable = set(MUTABLE_HEADS) - {"development_first_slice_latch"}
    immutable = (set(TABLES_0002) | set(TABLES_0003)) - set(MUTABLE_HEADS)
    for table in mutable:
        _require(
            f"{table} is immutable" not in lowered_schema,
            "c2b0.schema|heading=<inventory>|failure=mutable_immutable_swap",
        )
    for table in immutable:
        _require(
            f"{table} is mutable" not in lowered_schema,
            "c2b0.schema|heading=<inventory>|failure=mutable_immutable_swap",
        )


def _assert_tranche_contract(text: str) -> None:
    section = _section(text, SECTION_HEADINGS[25])
    blocks = _text_blocks(section)
    _require(
        bool(blocks),
        "c2b0.tranches|heading=26. Exact Target Tranche Sequence|failure=missing_sequence",
    )
    block = blocks[0]
    _require(
        tuple(line.split(":", 1)[0] for line in block) == TRANCHES,
        "c2b0.tranches|heading=26. Exact Target Tranche Sequence|failure=labels",
    )
    _require(
        block == TRANCHE_LINES,
        "c2b0.tranches|heading=26. Exact Target Tranche Sequence|failure=ownership_or_generation",
    )
    prose = _section_prose(text, SECTION_HEADINGS[25])
    assert "Productive redelivery is blocked by active stop" in prose
    assert "cancellation redelivery remains risk-reducing and permitted" in prose
    lowered = prose.lower()
    for forbidden in (
        "c2b4 owns initialize decision representation.",
        "c2b4 is the first tranche where durable decision rows are representable.",
        "c2b3 introduces a separate development_initialization_decisions table.",
        "c2b4 and c2b5 both own source-observation ingest.",
        "no tranche owns bound validation or review effect establishment.",
        "c2b4 and c2b5 both own the same mechanic.",
    ):
        _require(
            forbidden not in lowered,
            "c2b0.tranches|heading=26. Exact Target Tranche Sequence|failure=additive_ownership",
        )


def _assert_current_target_status(text: str) -> None:
    status = _section_prose(text, SECTION_HEADINGS[0])
    required = (
        "The current implemented application generation is 2",
        "C2B1 migration mechanics remain implemented",
        "managed database tip through `0002_development_program_and_effect_state`",
        "schema-0001 migration bytes or meanings",
        "Migration `0003_development_observation_and_progression_state` remains reserved",
        "`0003_development_observation_and_progression_state`",
        "exact responsibilities and inventories are frozen below",
        "No 0003 SQL, C2B2 production reader caller, product writer, product mutation transaction",
        "No public or product-integrated C2B reader, writer, mutation, ingest",
    )
    for phrase in required:
        _require(
            phrase in status,
            "c2b0.status|heading=1. Status, Classification, And Layering|failure=current_target_distinction",
        )
    visible = _unfenced_markdown(text, role="c2b0.owner").lower()
    for stale in (
        "no migration number is reserved here",
        "no migration number is reserved.",
        "exact future state shape, schema, migrations",
        "exact c2b schema remains wholly open.",
        "c2b is currently implemented",
        "migrations 0002 and 0003 are currently installed",
        "0002 is absent.",
        "0003 is installed.",
        "application generation is currently 3.",
    ):
        _require(
            stale not in visible,
            "c2b0.status|heading=1. Status, Classification, And Layering|failure=stale_or_current_claim",
        )


def _assert_application_generation_contract(text: str) -> None:
    strategy = _section_prose(text, SECTION_HEADINGS[19])
    for phrase in (
        "C2B1 is the framework-only source/test reset that added no SQL or database change",
        "C2B2 Slice 1 now uses that framework at implemented application generation 2",
        "current catalog and terminal tip `0002_development_program_and_effect_state`",
        "C2B2 Slice 1 advances the implemented application generation from 1 to 2",
        "makes its catalog terminal tip 0002",
        "C2B3 remains application generation 2 with terminal migration 0002",
        "C2B4 adds migration 0003 while retaining application generation 2",
        "terminal tip becomes 0003",
        "C2B5 and C2B6 remain application generation 2 with terminal migration 0003",
    ):
        assert phrase in strategy, (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=application_generation"
        )
    lowered = strategy.lower()
    for forbidden in MIGRATION_FORBIDDEN_CLAIMS[:6]:
        _require(
            forbidden not in lowered,
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=application_generation",
        )
    _assert_tranche_contract(text)


def _assert_cumulative_migration_contract(text: str) -> None:
    strategy_section = _section(text, SECTION_HEADINGS[19])
    strategy = _section_prose(text, SECTION_HEADINGS[19])
    assert MIGRATION_PATHS in _text_blocks(strategy_section), (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=cumulative_paths"
    )
    assert ORDINARY_OPEN_RULES in _text_blocks(strategy_section), (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=open_or_prefix_rule"
    )
    assert MIGRATION_TRANSACTION_PATHS in _text_blocks(strategy_section), (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=complete_suffix_transaction"
    )
    assert MIGRATION_TRANSACTION_COMPONENTS in _text_blocks(strategy_section), (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=complete_suffix_transaction"
    )
    for phrase in (
        "Ordinary product or writer open requires all of the following",
        "Ordinary open never silently migrates and never accepts an older prefix.",
        "one exact non-empty supported older catalog prefix",
        "exact packaged checksum and metadata",
        "no gaps, unknown rows, partial rows, divergent bounds, or ambiguous catalog resolution",
        "one exact contiguous packaged suffix leads to the current terminal tip",
        "migration-eligible only; it is not ordinarily product-openable before migration",
        "the complete intended packaged suffix is one administrative transaction",
        "No suffix migration may commit before a later migration in the same selected suffix is attempted",
        "Ordinary product or writer open never performs migration",
    ):
        assert phrase in strategy, (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=open_or_prefix_rule"
        )
    lowered = strategy.lower()
    for forbidden in MIGRATION_FORBIDDEN_CLAIMS[6:17]:
        _require(
            forbidden not in lowered,
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_prefix_or_suffix_claim",
        )


def _assert_migration_failure_and_history_contract(text: str) -> None:
    strategy_section = _section(text, SECTION_HEADINGS[19])
    strategy = _section_prose(text, SECTION_HEADINGS[19])
    for phrase in (
        "Every installed migration row remains immutable",
        "The persisted projection contains sequence, migration ID, checksum, `applied_at`, and compatibility bounds",
        "`schema_migrations` has no `destructive` column",
        "Historical `0001_initial` therefore remains `[1,1]`",
        "migrations 0002 and 0003 are each `[2,2]`",
        "do not require every historical row to include the running application generation",
        "Every migration selected for that suffix contributes all of the following to the same administrative transaction",
        "Failure before commit restores the complete exact prior supported prefix",
        "never rewrites 0001",
        "If an administrative commit attempt raises, migration recovery must",
        "An `unresolved` result forbids automatic rerun and automatic append of a missing remainder",
        "An operator or separately accepted recovery must complete before another migration attempt",
    ):
        assert phrase in strategy, (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=history_or_rollback"
        )
    blocks = _text_blocks(strategy_section)
    _require(
        blocks
        == (
            ORDINARY_OPEN_RULES,
            MIGRATION_PATHS,
            MIGRATION_TRANSACTION_PATHS,
            MIGRATION_TRANSACTION_COMPONENTS,
            MIGRATION_RECOVERY_STEPS,
            MIGRATION_COMMITTED_EXACT,
            MIGRATION_DEFINITELY_NOT_COMMITTED,
            MIGRATION_UNRESOLVED,
        ),
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=commit_uncertainty_mapping",
    )
    lowered = strategy.lower()
    for forbidden in MIGRATION_FORBIDDEN_CLAIMS[16:]:
        _require(
            forbidden not in lowered,
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_recovery_claim",
        )


def _assert_decision_tranche_ownership(text: str) -> None:
    migration_0002 = _section_prose(text, SECTION_HEADINGS[20])
    for phrase in (
        "C2B2 owns and lands both the base decision envelope and initialize-decision row treatment",
        "without adding a mutation API",
        "C2B3 later uses that representation for program initialization",
        "C2B4 adds only non-initialize, evidence-bearing decision contracts",
        "it neither owns initialize representation nor is the first point at which a durable decision row is representable",
        "not a generic decision metadata bag",
    ):
        assert phrase in migration_0002, (
            "c2b0.tranches|heading=21. Migration 0002|failure=decision_representation_ownership"
        )
    lowered = migration_0002.lower()
    for forbidden in (
        "c2b4 owns initialize decision representation.",
        "c2b4 is the first tranche where durable decision rows are representable.",
        "c2b3 introduces a separate development_initialization_decisions table.",
    ):
        _require(
            forbidden not in lowered,
            "c2b0.tranches|heading=21. Migration 0002|failure=additive_decision_ownership",
        )
    _assert_tranche_contract(text)


def _assert_observation_ingest_authority(text: str) -> None:
    observation_section = _section(text, SECTION_HEADINGS[12])
    observation = _section_prose(text, SECTION_HEADINGS[12])
    for phrase in (
        "A source observation is a source-authored record and digest.",
        "An ingest disposition is a Coordinator-authored classification.",
        "A progression decision is a separate Coordinator-authored semantic judgment.",
        "No observation or disposition directly authorizes acceptance, repair, replan, redelivery, publication, or program completion.",
    ):
        assert phrase in observation, (
            "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=authorship_or_acceptance_collapse"
        )
    _require(
        _text_blocks(observation_section) == (OBSERVATION_INGEST_STEPS, DISPOSITIONS),
        "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=disposition_inventory",
    )
    lowered = observation.lower()
    for forbidden in (
        "source observation and ingest disposition share one authorship identity",
        "source observation and coordinator ingest disposition use one identity and author row",
        "coordinator authors source observations",
        "the source authors coordinator ingest dispositions",
        "an ingest disposition directly creates accept",
        "an ingest disposition directly creates semantic acceptance",
        "an ingest disposition directly creates repair",
        "an ingest disposition directly creates replan",
        "an ingest disposition directly creates publication eligibility",
    ):
        _require(
            forbidden not in lowered,
            "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=additive_authorship_or_acceptance",
        )
    _require(
        re.search(r"\baccepted\b", observation, re.IGNORECASE) is None,
        "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=disposition_inventory",
    )


def _assert_global_latch_scope(text: str) -> None:
    latch = _section(text, SECTION_HEADINGS[18])
    blocks = _text_blocks(latch)
    contracts = tuple(
        block for block in blocks if block and block[0].startswith("latch_ref:")
    )
    _require(
        len(contracts) == 1,
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=contract_inventory",
    )
    contract = contracts[0]
    _require(
        contract == LATCH_CONTRACT,
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=scope",
    )
    _require(
        blocks == (contract,),
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=contract_inventory",
    )
    _require(
        "scope: per program" not in contract,
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=per_program_scope",
    )
    latch_prose = _unfenced_markdown(
        latch,
        role="c2b0.owner.section.19. First-Slice One-Shot Latch",
    )
    lowered = _compact(latch_prose).lower()
    _require(
        re.search(r"^[ \t]*(?:latch_ref|reuse)[ \t]*:", latch_prose, re.IGNORECASE | re.MULTILINE)
        is None,
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=additive_scope_or_lifecycle",
    )
    migration_0003 = _section(text, SECTION_HEADINGS[21])
    seed_contracts = tuple(
        block
        for block in _text_blocks(migration_0003)
        if block and re.match(r"^latch_ref[ \t]*:", block[0], re.IGNORECASE)
    )
    _require(
        len(seed_contracts) == 1,
        "c2b0.semantic|heading=22. Migration 0003|failure=latch_seed_binding",
    )
    _require(
        seed_contracts[0] == LATCH_SEED_CONTRACT,
        "c2b0.semantic|heading=22. Migration 0003|failure=latch_seed_binding",
    )
    owner_semantics = _semantic_inventory_text(
        text,
        role="c2b0.semantic.latch_owner",
    )
    declarations = tuple(
        line.strip()
        for line in owner_semantics.splitlines()
        if re.match(r"^[ \t]*(?:latch_ref|reuse)[ \t]*:", line, re.IGNORECASE)
    )
    _require(
        declarations == LATCH_DECLARATION_INVENTORY,
        "c2b0.semantic|heading=<owner>|failure=latch_declaration_inventory",
    )
    for forbidden in (
        "the latch is per-program durable truth",
        "the latch is per-program-version durable truth",
        "the latch is per-work-item durable truth",
        "the consumed latch may be reset to available",
        "the latch is reusable",
        "the latch row may be deleted",
        "the latch row may be recreated",
        "the latch is scheduler-authoritative",
        "the latch is queue-authoritative",
        "the latch is general program truth",
    ):
        _require(
            forbidden not in lowered,
            "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=additive_scope_or_lifecycle",
        )


def _assert_closed_ledger_metadata_and_trigger_contract(text: str) -> None:
    hybrid = _section_prose(text, SECTION_HEADINGS[3])
    migration_0002 = _section_prose(text, SECTION_HEADINGS[20])
    migration_0003 = _section_prose(text, SECTION_HEADINGS[21])
    assert "C2B rejects one mutable aggregate JSON row, fully mutable normalized history, one generic event ledger" in hybrid, (
        "c2b0.semantic|heading=4. Hybrid Durable Representation|failure=generic_event_ledger"
    )
    assert "not a generic decision metadata bag" in migration_0002, (
        "c2b0.semantic|heading=21. Migration 0002|failure=generic_decision_bag"
    )
    assert "closed role-specific relation, not a metadata bag" in migration_0003, (
        "c2b0.semantic|heading=22. Migration 0003|failure=generic_evidence_bag"
    )
    migration_0003_section = _section(text, SECTION_HEADINGS[21])
    _require(
        _text_blocks(migration_0003_section).count(CANCELLATION_EVIDENCE_ROLES) == 1,
        "c2b0.semantic|heading=22. Migration 0003|failure=evidence_role_inventory",
    )
    lowered = " ".join((hybrid, migration_0002, migration_0003)).lower()
    for forbidden in (
        "c2b also uses one generic event ledger as durable program truth",
        "c2b uses one generic event ledger as durable program truth",
        "c2b also uses one generic evidence metadata bag",
        "c2b also uses one generic decision json bag",
        "decision evidence permits arbitrary role strings",
        "durable decisions permit arbitrary payload json metadata",
        "decision payloads are open-ended",
    ):
        _require(
            forbidden not in lowered,
            "c2b0.semantic|heading=<closed-structure>|failure=additive_generic_structure",
        )
    _assert_schema_contract(text)


def _assert_mutation_and_recovery_family_contract(text: str) -> None:
    section = _section(text, SECTION_HEADINGS[11])
    blocks = _text_blocks(section)
    _require(
        blocks == (MUTATION_FAMILIES, RECOVERY_FAMILIES),
        "c2b0.families|heading=12. Complete Target Mutation Families|failure=closed_blocks",
    )
    identifiers = set(
        re.findall(
            r"(?<![A-Za-z0-9])_[a-z][a-z0-9_]*",
            _semantic_inventory_text(section, role="c2b0.families"),
        )
    )
    _require(
        identifiers == set(MUTATION_FAMILIES + RECOVERY_FAMILIES),
        "c2b0.families|heading=12. Complete Target Mutation Families|failure=additive_family",
    )


def test_owner_is_unique_and_section_inventory_is_exact() -> None:
    text = _owner()
    _assert_owner_structure(text)
    owner_headings = tuple(
        path
        for path in (ROOT / ".docs").glob("*.md")
        if path.read_text(encoding="utf-8").startswith("# C2B Durable Development State\n")
    )
    assert owner_headings == (OWNER_PATH,)


def test_current_versus_target_and_one_writer_are_explicit() -> None:
    text = _owner()
    _assert_current_target_status(text)
    status = _section_prose(text, SECTION_HEADINGS[0])
    authority = _compact(_section(text, SECTION_HEADINGS[1]))
    for phrase in (
        "Classification: `CURRENT IMPLEMENTED CONTRACT` for C2B1 migration administration, C2B2 Slice 1 physical schema representability, and C2B2 Slice 2 pure private row/value behavior, plus C2B2 Slice 3 private reader behavior",
        "C2B0 was the historical documentation-and-direct-contract-test tranche.",
        "C2B2 Slice 1 implements migration 0002 and physical representability",
        "C2B2 Slice 2 implements four pure private row/value modules",
        "C2B2 Slice 3 implements exactly two private reader modules",
        "The current implemented application generation is 2",
        "one existing Coordinator SQLite database",
        "one existing writer issuance and fencing authority",
        "one existing operation guard",
        "one existing mutation slot",
        "one existing transaction controller",
        "no second database, writer, session authority, transaction controller",
        "Persistence of a reference or digest never transfers authorship",
    ):
        assert phrase in status or phrase in authority


def test_identity_and_hybrid_representation_are_closed() -> None:
    identities = _section(_owner(), SECTION_HEADINGS[2])
    hybrid = _compact(_section(_owner(), SECTION_HEADINGS[3]))
    assert len(_text_blocks(identities)[0]) == 21
    assert MUTABLE_HEADS in _text_blocks(_section(_owner(), SECTION_HEADINGS[3]))
    assert "one-way `available` to `consumed` transition" in hybrid
    assert "one generic event ledger" in hybrid
    assert "reuse of `work_items` or `transition_events` as target truth" in hybrid


def test_program_genesis_and_deferred_cycle_are_exact() -> None:
    genesis = _compact(_section(_owner(), SECTION_HEADINGS[4]))
    for phrase in (
        "real immutable `initialize` decision",
        "program_version_number: 1",
        "program_version_kind: initial",
        "creating_decision_ref: required and non-null",
        "initial program head revision: 0",
        "preassigned semantic attempt: required",
        "preassigned candidate: required",
        "It creates no semantic-attempt row, effect, command, delivery, observation",
        "`DEFERRABLE INITIALLY DEFERRED`",
        "Foreign keys are never disabled.",
    ):
        assert phrase in genesis


def test_decisions_cancel_basis_and_effect_roles_are_exact() -> None:
    text = _owner()
    _assert_decision_and_cancel_contract(text)
    _assert_basis_and_effect_contract(text)


def test_mutation_and_recovery_family_inventories_are_independent_literals() -> None:
    section = _section(_owner(), SECTION_HEADINGS[11])
    blocks = _text_blocks(section)
    assert blocks == (MUTATION_FAMILIES, RECOVERY_FAMILIES)
    assert "not public package APIs or stable external methods" in _compact(section)
    assert "C2B0 implements none of them." in section
    _assert_mutation_and_recovery_family_contract(_owner())


def test_observation_disposition_and_redelivery_boundaries_are_exact() -> None:
    _assert_observation_ingest_authority(_owner())
    observation = _section(_owner(), SECTION_HEADINGS[12])
    redelivery = _compact(_section(_owner(), SECTION_HEADINGS[13]))
    assert DISPOSITIONS in _text_blocks(observation)
    assert "Source-observation identity is `(observation_ref, observation_digest)`." in observation
    assert "A malformed observation creates no claim, disposition, receipt, or head change." in _compact(observation)
    assert "No observation or disposition directly authorizes acceptance, repair, replan, redelivery, publication, or program completion." in _compact(observation)
    for phrase in (
        "Unknown source observation",
        "Coordinator redeliver decision",
        "successor delivery attempt",
        "actual redelivery remain distinct",
        "C2B does not perform redelivery",
        "timeout-as-failure",
        "Bridge recovery authority",
    ):
        assert phrase in redelivery


def test_split_stop_matrix_is_exact() -> None:
    _assert_stop_contract(_owner())


def test_workspec_and_c2a_value_privacy_are_exact() -> None:
    _assert_privacy_contract(_owner())


def test_authority_evaluation_and_latch_are_non_authoritative_and_one_shot() -> None:
    authority = _compact(_section(_owner(), SECTION_HEADINGS[17]))
    latch = _compact(_section(_owner(), SECTION_HEADINGS[18]))
    for state in ("pending", "verified", "blocked", "stale", "revoked", "expired"):
        assert state in authority
    assert "A separately accepted external verifier must supply `verified`" in authority
    assert "or Coordinator decision is not executable authorization" in authority
    assert "latch_ref: direct_local_first_productive_acceptance" in latch
    assert "initial state: available" in latch
    assert "initial version: 0" in latch
    assert "final state: consumed" in latch
    assert "final version: 1" in latch
    assert "reset: forbidden" in latch
    assert "delete: forbidden" in latch
    assert "blocks a second productive acceptance" in latch
    _assert_global_latch_scope(_owner())


def test_migration_tables_totals_triggers_indexes_and_bootstrap_are_exact() -> None:
    _assert_schema_contract(_owner())
    _assert_application_generation_contract(_owner())
    _assert_cumulative_migration_contract(_owner())
    _assert_migration_failure_and_history_contract(_owner())
    _assert_decision_tranche_ownership(_owner())


def test_transaction_replay_cas_uncertainty_and_tranches_are_exact() -> None:
    transaction = _compact(_section(_owner(), SECTION_HEADINGS[24]))
    for phrase in (
        "1. exact command-local preflight",
        "7. durable writer fencing",
        "8. mutation-receipt lookup",
        "9. exact replay or same-key conflict",
        "14. capability invalidation",
        "15. exactly one commit attempt",
        "same mutation_ref + same canonical digest: exact replay",
        "mutation_ref_reuse_conflict",
        "program_head_conflict",
        "target_effect_state_conflict",
        "coding_global_stop_active",
        "commit_outcome_unknown",
        "committed_exact",
        "definitely_not_committed",
        "unresolved",
        "No mutation automatically retries",
    ):
        assert phrase in transaction
    _assert_tranche_contract(_owner())


def test_c2b0_current_and_target_status_are_consistent() -> None:
    _assert_current_target_status(_owner())


def test_c2b0_stale_no_migration_reserved_wording_is_rejected() -> None:
    text = _owner()
    mutations = (
        _replace_once(
            text,
            "Migration `0003_development_observation_and_progression_state` remains reserved",
            "No migration number is reserved here; a future C2B requires a separately accepted durable schema and forward migration.",
        ),
        text + "\nExact future state shape, schema, migrations remain wholly open.\n",
        text + "\nC2B is currently implemented.\n",
        text + "\nMigrations 0002 and 0003 are currently installed.\n",
    )
    for mutation in mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_current_target_status(mutation)
        assert "c2b0.status|heading=1. Status, Classification, And Layering|failure=" in str(
            rejected.value
        )


def test_c2b0_current_target_status_rejects_all_additive_stale_claims() -> None:
    text = _owner()
    stale_claims = (
        "Exact C2B schema remains wholly open.",
        "0002 is absent.",
        "0003 is installed.",
        "Application generation is currently 3.",
        "No migration number is reserved.",
        "C2B is currently implemented.",
    )
    for stale in stale_claims:
        with pytest.raises(AssertionError) as rejected:
            _assert_current_target_status(text + f"\n{stale}\n")
        assert str(rejected.value) == (
            "c2b0.status|heading=1. Status, Classification, And Layering|failure=stale_or_current_claim"
        )

    fenced = text + "\n~~~example`info\n" + "\n".join(stale_claims) + "\n~~~\n"
    _assert_current_target_status(fenced)


def test_c2b0_markdown_parsers_reject_invalid_backtick_info_authority_bypass() -> None:
    text = _owner()
    mutation = (
        text
        + "\n```bad`info\nC2B is currently implemented.\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_current_target_status(mutation)
    assert str(rejected.value) == (
        "c2b0.status|heading=1. Status, Classification, And Layering|failure=stale_or_current_claim"
    )

    valid_tilde = text + "\n~~~bad`info\nC2B is currently implemented.\n~~~\n"
    _assert_current_target_status(valid_tilde)


def test_c2b0_markdown_parsers_reject_invalid_backtick_info_duplicate_heading_bypass() -> None:
    text = _owner()
    mutation = (
        text
        + "\n```bad`info\n## 1. Status, Classification, And Layering\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_owner_structure(mutation)
    assert str(rejected.value) == (
        "c2b0.owner|heading=<inventory>|failure=missing_duplicate_reordered_or_relocated"
    )


def test_c2b0_application_generation_transition_is_exact() -> None:
    text = _owner()
    _assert_application_generation_contract(text)
    sqlite_text = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_sqlite_migration_summary(sqlite_text)
    for mutation in (
        _replace_once(
            text,
            "C2B2 Slice 1 advances the implemented application generation from 1 to 2",
            "C2B2 leaves the implemented application generation at 1",
        ),
        _replace_once(
            text,
            "C2B4 adds migration 0003\nwhile retaining application generation 2",
            "C2B4 adds migration 0003 and advances application generation to 3",
        ),
    ):
        with pytest.raises(AssertionError) as rejected:
            _assert_application_generation_contract(mutation)
        assert "c2b0.migration|heading=20. Migration-Framework Strategy|failure=application_generation" in str(
            rejected.value
        )
    sqlite_mutation = _replace_once(
        sqlite_text,
        "C2B2 Slice 1 advances implemented application generation from 1 to 2",
        "C2B2 leaves implemented application generation at 1",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_sqlite_migration_summary(sqlite_mutation)
    assert str(rejected.value) == (
        "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=generation_prefix_or_rollback"
    )


def test_c2b0_cumulative_fresh_install_and_supported_prefix_rules_are_exact() -> None:
    text = _owner()
    _assert_cumulative_migration_contract(text)
    _assert_sqlite_migration_summary(_text(".docs/sqlite-bootstrap-and-migrations.md"))
    for mutation in (
        _replace_once(
            text,
            "C2B4-or-later fresh installation: 0001 -> 0002 -> 0003",
            "C2B4-or-later fresh installation: apply only 0003",
        ),
        _replace_once(
            text,
            "Ordinary open never silently migrates and never accepts an older prefix.",
            "Ordinary open accepts exact 0001 or 0002 as an older prefix.",
        ),
        _replace_once(
            text,
            "one exact non-empty supported older\ncatalog prefix",
            "any non-exact or unsupported older catalog prefix",
        ),
    ):
        with pytest.raises(AssertionError) as rejected:
            _assert_cumulative_migration_contract(mutation)
        assert "c2b0.migration|heading=20. Migration-Framework Strategy|failure=" in str(
            rejected.value
        )


def test_c2b0_migration_failure_and_history_immutability_are_exact() -> None:
    text = _owner()
    _assert_migration_failure_and_history_contract(text)
    _assert_sqlite_migration_summary(_text(".docs/sqlite-bootstrap-and-migrations.md"))
    for mutation in (
        _replace_once(text, "Historical `0001_initial` therefore remains `[1,1]`", "Historical `0001_initial` is rewritten to `[1,2]`"),
        _replace_once(text, "Historical `0001_initial` therefore remains `[1,1]`", "Historical `0001_initial` is rewritten to `[2,2]`"),
        _replace_once(
            text,
            "Failure before commit restores the complete exact prior supported\nprefix with no partial DDL, invariant change, or history row",
            "Failure before commit may retain partial DDL or a partial history row",
        ),
    ):
        with pytest.raises(AssertionError) as rejected:
            _assert_migration_failure_and_history_contract(mutation)
        assert "c2b0.migration|heading=20. Migration-Framework Strategy|failure=history_or_rollback" in str(
            rejected.value
        )


def test_c2b0_complete_migration_suffix_uses_one_administrative_transaction() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_cumulative_migration_contract(owner)
    _assert_sqlite_migration_summary(sqlite)

    split_claim = "C2B4 upgrade from exact 0001 commits 0002 before starting 0003."
    owner_mutation = _replace_once(
        owner,
        "Ordinary product or writer open never performs migration.",
        "Ordinary product or writer open never performs migration.\n\n" + split_claim,
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_cumulative_migration_contract(owner_mutation)
    assert str(rejected.value) == (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_prefix_or_suffix_claim"
    )

    sqlite_mutation = _replace_once(
        sqlite,
        "Ordinary product or writer open never performs migration.",
        "Ordinary product or writer open never performs migration.\n\n" + split_claim,
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_sqlite_migration_summary(sqlite_mutation)
    assert str(rejected.value) == (
        "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=forbidden_migration_claim"
    )


def test_c2b0_migration_commit_uncertainty_mapping_is_exact() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_migration_failure_and_history_contract(owner)
    _assert_sqlite_migration_summary(sqlite)

    contradictions = (
        "Matching migration history alone is committed_exact even when the live schema differs.",
        "Matching live schema alone is committed_exact even when migration history differs.",
    )
    for contradiction in contradictions:
        owner_mutation = _replace_once(
            owner,
            "The evidence classifications are exact:",
            "The evidence classifications are exact:\n\n" + contradiction,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_migration_failure_and_history_contract(owner_mutation)
        assert str(rejected.value) == (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_recovery_claim"
        )

        sqlite_mutation = _replace_once(
            sqlite,
            "The evidence classifications are exact:",
            "The evidence classifications are exact:\n\n" + contradiction,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_sqlite_migration_summary(sqlite_mutation)
        assert str(rejected.value) == (
            "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=forbidden_migration_claim"
        )


def test_c2b0_unresolved_migration_forbids_automatic_rerun() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    contradiction = "After an unresolved migration commit, the suffix is automatically rerun."
    owner_mutation = _replace_once(
        owner,
        "This migration-specific rule is distinct",
        contradiction + "\n\nThis migration-specific rule is distinct",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_migration_failure_and_history_contract(owner_mutation)
    assert str(rejected.value) == (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_recovery_claim"
    )

    sqlite_mutation = _replace_once(
        sqlite,
        "This migration-specific rule is distinct",
        contradiction + "\n\nThis migration-specific rule is distinct",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_sqlite_migration_summary(sqlite_mutation)
    assert str(rejected.value) == (
        "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=forbidden_migration_claim"
    )


def test_c2b0_owner_sections_are_fence_aware_unique_and_ordered() -> None:
    text = _owner()
    _assert_owner_structure(text)

    fenced_shadows = (
        text
        + "\n```markdown\n## 1. Status, Classification, And Layering\n````\n"
        + "~~~~markdown\n  ## 2. One Database, One Writer, And Fact Ownership ###\n~~~~~\n"
    )
    _assert_owner_structure(fenced_shadows)

    lower_level = _replace_once(
        text,
        "later C2B2 integration plus C2B3-C2B6\nbehavior below.\n\nC2B0 was",
        "later C2B2 integration plus C2B3-C2B6\nbehavior below.\n\n### Local Detail\n\nC2B0 was",
    )
    _assert_current_target_status(lower_level)

    mutations = (
        "```markdown\n" + text + "```\n",
        text + "\n## 1. Status, Classification, And Layering\n",
        text + "\n  ## 1. Status, Classification, And Layering ###\n",
        text + "\n##\t1. Status, Classification, And Layering\n",
        _replace_once(
            text,
            "## 1. Status, Classification, And Layering\n",
            "",
        ),
        _replace_once(
            _replace_once(
                text,
                "## 1. Status, Classification, And Layering",
                "## TEMPORARY OWNER HEADING",
            ),
            "## 2. One Database, One Writer, And Fact Ownership",
            "## 1. Status, Classification, And Layering",
        ).replace(
            "## TEMPORARY OWNER HEADING",
            "## 2. One Database, One Writer, And Fact Ownership",
            1,
        ),
        text + "\n~~~markdown\n## 1. Status, Classification, And Layering\n```\n",
    )
    for mutation in mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_owner_structure(mutation)
        assert str(rejected.value).startswith("c2b0.owner|heading=")

    for boundary in ("## Relocated Status", "# Relocated Status"):
        mutation = _replace_once(
            text,
            "later C2B2 integration plus C2B3-C2B6\nbehavior below.\n\nC2B0 was",
            f"later C2B2 integration plus C2B3-C2B6\nbehavior below.\n\n{boundary}\n\nC2B0 was",
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_current_target_status(mutation)
        assert "c2b0.status|heading=1. Status, Classification, And Layering|failure=current_target_distinction" in str(
            rejected.value
        )


def test_c2b0_summary_sections_ignore_fenced_target_claims() -> None:
    summaries = (
        (
            _text(".docs/durable-state-model.md"),
            "c2b0.summary.durable_state",
            "C2B0 Accepted Durable-Development Target",
            "The accepted complete target comprises implemented migration",
        ),
        (
                _text(".docs/architecture.md"),
                "c2b0.summary.architecture",
                "C2B0 Accepted Durable-State Target Topology",
                "C2B2 Slice 1 physically represents the nineteen-table core",
        ),
        (
            _text(".docs/autonomous-software-development-operating-model.md"),
            "c2b0.summary.operating_model",
            "C2B0 Accepted Durable-State Composition Overlay",
            "C2B0 closes only the target durable-state seams",
        ),
        (
            _text(".docs/software-development-progression-boundary.md"),
            "c2b0.summary.progression",
            "C2B0 Accepted Durable Progression Closure",
            "durable C2B progression remains unimplemented.",
        ),
    )
    for text, role, heading, required in summaries:
        _assert_summary_target(text, role=role, heading=heading, required=required)

    durable, role, heading, required = summaries[0]
    fenced_only = _replace_once(durable, required, f"```text\n{required}\n```")
    with pytest.raises(AssertionError) as rejected:
        _assert_summary_target(fenced_only, role=role, heading=heading, required=required)
    assert str(rejected.value) == (
        "c2b0.summary.durable_state|heading=C2B0 Accepted Durable-Development Target|failure=target_claim_missing"
    )

    contradictory = durable + "\n# Contradictory Current Status\n\nC2B is currently implemented.\n"
    with pytest.raises(AssertionError) as rejected:
        _assert_summary_target(contradictory, role=role, heading=heading, required=required)
    assert str(rejected.value) == (
        "c2b0.summary.durable_state|heading=C2B0 Accepted Durable-Development Target|failure=contradictory_current_status"
    )


def test_c2b0_observation_ingest_and_decision_authorship_are_distinct() -> None:
    text = _owner()
    _assert_observation_ingest_authority(text)
    mutations = (
        _replace_once(
            text,
            "A source observation is a source-authored\nrecord and digest. An ingest disposition is a Coordinator-authored\nclassification.",
            "A source observation and Coordinator ingest disposition use one identity and author row.",
        ),
        _replace_once(
            text,
            "No observation or disposition directly authorizes acceptance, repair,\nreplan, redelivery, publication, or program completion.",
            "An ingest disposition directly creates semantic acceptance.",
        ),
    )
    for mutation in mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_observation_ingest_authority(mutation)
        assert "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=authorship_or_acceptance_collapse" in str(
            rejected.value
        )


def test_c2b0_first_slice_latch_scope_is_global_bootstrap() -> None:
    text = _owner()
    _assert_global_latch_scope(text)
    mutation = _replace_once(
        text,
        "scope: global Coordinator bootstrap",
        "scope: per program",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_global_latch_scope(mutation)
    assert "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=scope" in str(
        rejected.value
    )


def test_c2b0_decision_representation_tranche_ownership_is_exact() -> None:
    text = _owner()
    _assert_decision_tranche_ownership(text)
    mutations = (
        _replace_once(
            text,
            "C2B2 owns and lands both the base\ndecision envelope and initialize-decision row treatment",
            "C2B2 omits the base decision envelope and initialize-decision row treatment",
        ),
        _replace_once(
            text,
            "C2B4 adds only non-initialize, evidence-bearing decision contracts; it neither\nowns initialize representation nor is the first point at which a durable\ndecision row is representable.",
            "C2B4 is the first tranche where a durable decision row is representable and owns initialize representation.",
        ),
    )
    for mutation in mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_decision_tranche_ownership(mutation)
        assert "c2b0.tranches|heading=21. Migration 0002|failure=decision_representation_ownership" in str(
            rejected.value
        )


def test_c2b0_trigger_inventory_has_no_extra_trigger() -> None:
    text = _owner()
    _assert_schema_contract(text)
    for extra in (
        "0003: extra immutable table * no-update/no-delete = 2",
        "0003: one extra trigger without a table-count change = 1",
    ):
        mutation = _replace_once(
            text,
            "0003: latch one-way update guard = 1\n```",
            f"0003: latch one-way update guard = 1\n{extra}\n```",
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_schema_contract(mutation)
        assert "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_arithmetic" in str(
            rejected.value
        )


def test_c2b0_rejects_generic_event_ledger_and_metadata_bags() -> None:
    text = _owner()
    _assert_closed_ledger_metadata_and_trigger_contract(text)
    mutations = (
        _replace_once(
            text,
            "C2B rejects one mutable aggregate JSON row, fully mutable normalized history,\none generic event ledger",
            "C2B introduces one generic event ledger as durable program truth and uses one mutable aggregate JSON row",
        ),
        _replace_once(
            text,
            "closed role-specific relation,\nnot a metadata bag",
            "generic evidence metadata bag",
        ),
        _replace_once(
            text,
            "closed\nkind-specific contract, not a generic decision metadata bag",
            "generic decision metadata bag",
        ),
    )
    for mutation in mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_closed_ledger_metadata_and_trigger_contract(mutation)
        assert "c2b0.semantic|heading=" in str(rejected.value)


def test_c2b0_observation_ingest_and_decision_contract_is_additively_closed() -> None:
    text = _owner()
    marker = (
        "No observation or disposition directly authorizes acceptance, repair,\n"
        "replan, redelivery, publication, or program completion."
    )
    contradictions = (
        "A source observation and ingest disposition share one authorship identity.",
        "Coordinator authors source observations.",
        "The source authors Coordinator ingest dispositions.",
        "An ingest disposition directly creates accept.",
        "An ingest disposition directly creates repair.",
        "An ingest disposition directly creates replan.",
        "An ingest disposition directly creates publication eligibility.",
    )
    for contradiction in contradictions:
        mutation = _replace_once(text, marker, marker + "\n\n" + contradiction)
        with pytest.raises(AssertionError) as rejected:
            _assert_observation_ingest_authority(mutation)
        assert str(rejected.value) == (
            "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=additive_authorship_or_acceptance"
        )

    added_disposition = _replace_once(
        text,
        "late_retained\nrecorded\n```",
        "late_retained\nrecorded\naccepted\n```",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_observation_ingest_authority(added_disposition)
    assert str(rejected.value) == (
        "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=disposition_inventory"
    )


def test_c2b0_first_slice_latch_contract_is_additively_closed() -> None:
    text = _owner()
    marker = "The latch is not a scheduler, queue, backlog, lease, or general program truth."
    contradictions = (
        "The latch is per-program durable truth.",
        "The latch is per-program-version durable truth.",
        "The latch is per-work-item durable truth.",
        "The consumed latch may be reset to available.",
        "The latch is reusable for every productive acceptance.",
        "The latch row may be deleted and recreated.",
        "The latch row may be recreated.",
        "The latch is scheduler-authoritative.",
        "The latch is queue-authoritative.",
        "The latch is general program truth.",
    )
    for contradiction in contradictions:
        mutation = _replace_once(text, marker, marker + "\n\n" + contradiction)
        with pytest.raises(AssertionError) as rejected:
            _assert_global_latch_scope(mutation)
        assert str(rejected.value) == (
            "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=additive_scope_or_lifecycle"
        )


def test_c2b0_generic_structures_and_schema_inventory_are_additively_closed() -> None:
    text = _owner()
    generic_mutations = (
        _replace_once(
            text,
            "C2B rejects one mutable aggregate JSON row, fully mutable normalized history,\none generic event ledger",
            "C2B rejects one mutable aggregate JSON row, fully mutable normalized history,\none generic event ledger\n\nC2B also uses one generic event ledger as durable program truth.",
        ),
        _replace_once(
            text,
            "closed role-specific relation,\nnot a metadata bag",
            "closed role-specific relation,\nnot a metadata bag. C2B also uses one generic evidence metadata bag.",
        ),
        _replace_once(
            text,
            "closed\nkind-specific contract, not a generic decision metadata bag",
            "closed\nkind-specific contract, not a generic decision metadata bag. C2B also uses one generic decision JSON bag.",
        ),
        _replace_once(
            text,
            "cancel_source_evidence\n```",
            "cancel_source_evidence\narbitrary_role\n```",
        ),
        _replace_once(
            text,
            "not a generic decision metadata bag.",
            "not a generic decision metadata bag. Decision payloads are open-ended.",
        ),
    )
    for mutation in generic_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_closed_ledger_metadata_and_trigger_contract(mutation)
        assert str(rejected.value).startswith("c2b0.semantic|")
        assert str(rejected.value)

    schema_mutations = (
        (
            _replace_once(
                text,
                "development_mutation_receipts\n```",
                "development_mutation_receipts\ndevelopment_extra_0002_table\n```",
            ),
            "c2b0.schema|heading=21. Migration 0002|failure=table_inventory",
        ),
        (
            _replace_once(
                text,
                "development_publication_eligibility\ndevelopment_first_slice_latch\n```",
                "development_publication_eligibility\ndevelopment_first_slice_latch\ndevelopment_extra_0003_table\n```",
            ),
            "c2b0.schema|heading=22. Migration 0003|failure=table_inventory",
        ),
        (
            _replace_once(
                text,
                "development_program_versions\n",
                "",
            ),
            "c2b0.schema|heading=21. Migration 0002|failure=table_inventory",
        ),
        (
            _replace_once(
                text,
                "Migration 0003 seeds exactly the one available latch row described above; all\nother new C2B tables begin empty.",
                "Migration 0003 seeds exactly the one available latch row described above; all\nother new C2B tables begin empty.\n\nhidden_extra_trigger is also created.",
            ),
            "c2b0.schema|heading=23. Exact Schema Totals|failure=additive_trigger",
        ),
        (
            _replace_once(
                text,
                "0003: latch no-delete = 1\n",
                "",
            ),
            "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_arithmetic",
        ),
        (
            _replace_once(
                text,
                "Migration 0003 seeds exactly the one available latch row described above; all\nother new C2B tables begin empty.",
                "Migration 0003 seeds exactly the one available latch row described above; all\nother new C2B tables begin empty.\n\ndevelopment_program_heads is immutable.",
            ),
            "c2b0.schema|heading=<inventory>|failure=mutable_immutable_swap",
        ),
        (
            _replace_once(
                text,
                "idx_development_source_observation_claims_digest\n```",
                "idx_development_source_observation_claims_digest\nidx_additional_reporting\n```",
            ),
            "c2b0.schema|heading=24. Exact Explicit Indexes|failure=index_inventory",
        ),
        (
            _replace_once(
                text,
                "SQLite-managed primary-key and unique\nautoindexes are excluded from explicit-index totals.",
                "A reporting index is added. SQLite-managed primary-key and unique\nautoindexes are excluded from explicit-index totals.",
            ),
            "c2b0.schema|heading=<inventory>|failure=additive_schema_claim",
        ),
    )
    for mutation, diagnostic in schema_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_schema_contract(mutation)
        assert str(rejected.value) == diagnostic


def test_c2b0_decision_mutation_recovery_inventories_are_additively_closed() -> None:
    text = _owner()
    for added_kind in ("retry", "Accept"):
        mutation = _replace_once(
            text,
            "redeliver\ncancel\n```",
            f"redeliver\ncancel\n{added_kind}\n```",
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_decision_and_cancel_contract(mutation)
        assert str(rejected.value) == (
            "c2b0.decisions|heading=6. Exact Decision-Kind Inventory|failure=closed_inventory"
        )

    family_mutations = (
        _replace_once(
            text,
            "_record_development_progression_decision\n```",
            "_record_development_progression_decision\n_sixth_development_mutation\n```",
        ),
        _replace_once(
            text,
            "_resolve_development_progression_decision_commit_outcome\n```",
            "_resolve_development_progression_decision_commit_outcome\n_resolve_sixth_development_commit_outcome\n```",
        ),
    )
    for mutation in family_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_mutation_and_recovery_family_contract(mutation)
        assert str(rejected.value) == (
            "c2b0.families|heading=12. Complete Target Mutation Families|failure=closed_blocks"
        )


def test_c2b0_tranche_ownership_is_unique_and_complete() -> None:
    text = _owner()
    decision_marker = "not a generic decision metadata bag."
    decision_contradictions = (
        "C2B4 owns initialize decision representation.",
        "C2B4 is the first tranche where durable decision rows are representable.",
        "C2B3 introduces a separate development_initialization_decisions table.",
    )
    for contradiction in decision_contradictions:
        mutation = _replace_once(
            text,
            decision_marker,
            decision_marker + "\n\n" + contradiction,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_decision_tranche_ownership(mutation)
        assert str(rejected.value) == (
            "c2b0.tranches|heading=21. Migration 0002|failure=additive_decision_ownership"
        )

    tranche_marker = "cancellation redelivery remains\nrisk-reducing and permitted."
    tranche_contradictions = (
        "C2B4 and C2B5 both own source-observation ingest.",
        "No tranche owns bound validation or review effect establishment.",
        "C2B4 and C2B5 both own the same mechanic.",
    )
    for contradiction in tranche_contradictions:
        mutation = _replace_once(
            text,
            tranche_marker,
            tranche_marker + "\n\n" + contradiction,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_tranche_contract(mutation)
        assert str(rejected.value) == (
            "c2b0.tranches|heading=26. Exact Target Tranche Sequence|failure=additive_ownership"
        )


def test_c2b0_repair2_full_audit_counterfactual_matrix() -> None:
    text = _owner()
    migration_marker = "Ordinary product or writer open never performs migration."

    for stale in (
        "Exact C2B schema remains wholly open.",
        "0002 is absent.",
        "0003 is installed.",
        "Application generation is currently 3.",
        "No migration number is reserved.",
        "C2B is currently implemented.",
    ):
        with pytest.raises(AssertionError):
            _assert_current_target_status(text + f"\n{stale}\n")

    for contradiction in MIGRATION_FORBIDDEN_CLAIMS[:6]:
        mutation = _replace_once(
            text,
            migration_marker,
            migration_marker + "\n\n" + contradiction,
        )
        with pytest.raises(AssertionError):
            _assert_application_generation_contract(mutation)

    for contradiction in MIGRATION_FORBIDDEN_CLAIMS[6:17]:
        mutation = _replace_once(
            text,
            migration_marker,
            migration_marker + "\n\n" + contradiction,
        )
        with pytest.raises(AssertionError):
            _assert_cumulative_migration_contract(mutation)

    for contradiction in MIGRATION_FORBIDDEN_CLAIMS[17:]:
        mutation = _replace_once(
            text,
            "The evidence classifications are exact:",
            "The evidence classifications are exact:\n\n" + contradiction,
        )
        with pytest.raises(AssertionError):
            _assert_migration_failure_and_history_contract(mutation)

    invalid_info_authority = (
        text
        + "\n```bad`info\nC2B is currently implemented.\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError):
        _assert_current_target_status(invalid_info_authority)
    invalid_info_duplicate = (
        text
        + "\n```bad`info\n## 1. Status, Classification, And Layering\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError):
        _assert_owner_structure(invalid_info_duplicate)

    observation_marker = (
        "No observation or disposition directly authorizes acceptance, repair,\n"
        "replan, redelivery, publication, or program completion."
    )
    for contradiction in (
        "A source observation and ingest disposition share one authorship identity.",
        "Coordinator authors source observations.",
        "The source authors Coordinator ingest dispositions.",
        "An ingest disposition directly creates accept.",
        "An ingest disposition directly creates repair.",
        "An ingest disposition directly creates replan.",
        "An ingest disposition directly creates publication eligibility.",
    ):
        mutation = _replace_once(
            text,
            observation_marker,
            observation_marker + "\n\n" + contradiction,
        )
        with pytest.raises(AssertionError):
            _assert_observation_ingest_authority(mutation)
    with pytest.raises(AssertionError):
        _assert_observation_ingest_authority(
            _replace_once(
                text,
                "late_retained\nrecorded\n```",
                "late_retained\nrecorded\naccepted\n```",
            )
        )

    latch_marker = "The latch is not a scheduler, queue, backlog, lease, or general program truth."
    for contradiction in (
        "The latch is per-program durable truth.",
        "The latch is per-program-version durable truth.",
        "The latch is per-work-item durable truth.",
        "The consumed latch may be reset to available.",
        "The latch is reusable for every productive acceptance.",
        "The latch row may be deleted and recreated.",
        "The latch row may be recreated.",
        "The latch is scheduler-authoritative.",
        "The latch is queue-authoritative.",
    ):
        mutation = _replace_once(text, latch_marker, latch_marker + "\n\n" + contradiction)
        with pytest.raises(AssertionError):
            _assert_global_latch_scope(mutation)

    with pytest.raises(AssertionError):
        _assert_closed_ledger_metadata_and_trigger_contract(
            _replace_once(
                text,
                "C2B rejects one mutable aggregate JSON row, fully mutable normalized history,\none generic event ledger",
                "C2B rejects one mutable aggregate JSON row, fully mutable normalized history,\none generic event ledger\n\nC2B also uses one generic event ledger as durable program truth.",
            )
        )
    with pytest.raises(AssertionError):
        _assert_schema_contract(
            _replace_once(
                text,
                "idx_development_source_observation_claims_digest\n```",
                "idx_development_source_observation_claims_digest\nidx_third_explicit_index\n```",
            )
        )
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(
            _replace_once(text, "redeliver\ncancel\n```", "redeliver\ncancel\nretry\n```")
        )
    with pytest.raises(AssertionError):
        _assert_mutation_and_recovery_family_contract(
            _replace_once(
                text,
                "_record_development_progression_decision\n```",
                "_record_development_progression_decision\n_sixth_development_mutation\n```",
            )
        )
    with pytest.raises(AssertionError):
        _assert_mutation_and_recovery_family_contract(
            _replace_once(
                text,
                "_resolve_development_progression_decision_commit_outcome\n```",
                "_resolve_development_progression_decision_commit_outcome\n_resolve_sixth_development_commit_outcome\n```",
            )
        )
    with pytest.raises(AssertionError):
        _assert_decision_tranche_ownership(
            _replace_once(
                text,
                "not a generic decision metadata bag.",
                "not a generic decision metadata bag.\n\nC2B4 owns initialize decision representation.",
            )
        )
    with pytest.raises(AssertionError):
        _assert_tranche_contract(
            _replace_once(
                text,
                "cancellation redelivery remains\nrisk-reducing and permitted.",
                "cancellation redelivery remains\nrisk-reducing and permitted.\n\nC2B4 and C2B5 both own source-observation ingest.",
            )
        )


def test_c2b0_full_audit_counterfactual_matrix() -> None:
    text = _owner()

    markdown_mutations = (
        "```markdown\n" + text + "```\n",
        text + "\n  ## 1. Status, Classification, And Layering ###\n",
        text + "\n##\t1. Status, Classification, And Layering\n",
        text + "\n~~~markdown\n## 1. Status, Classification, And Layering\n```\n",
    )
    for mutation in markdown_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_owner_structure(mutation)
        diagnostic = str(rejected.value)
        assert diagnostic.startswith("c2b0.owner|heading=")

    fenced_target = _replace_once(
        text,
        "Migration `0003_development_observation_and_progression_state` remains reserved",
        "```text\nMigration `0003_development_observation_and_progression_state` remains reserved\n```",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_current_target_status(fenced_target)
    assert "c2b0.status|heading=1. Status, Classification, And Layering|failure=" in str(
        rejected.value
    )

    same_or_higher = _replace_once(
        text,
        "later C2B2 integration plus C2B3-C2B6\nbehavior below.\n\nC2B0 was",
        "later C2B2 integration plus C2B3-C2B6\nbehavior below.\n\n# Relocated Status\n\nC2B0 was",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_current_target_status(same_or_higher)
    assert "c2b0.status|heading=1. Status, Classification, And Layering|failure=" in str(
        rejected.value
    )

    semantic_observation_mutations = (
        _replace_once(
            text,
            "A source observation is a source-authored\nrecord and digest. An ingest disposition is a Coordinator-authored\nclassification.",
            "A source observation and ingest disposition share one authorship identity.",
        ),
        _replace_once(
            text,
            "No observation or disposition directly authorizes acceptance, repair,\nreplan, redelivery, publication, or program completion.",
            "An ingest disposition directly creates acceptance.",
        ),
    )
    for mutation in semantic_observation_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_observation_ingest_authority(mutation)
        assert "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=" in str(
            rejected.value
        )

    per_program_latch = _replace_once(
        text,
        "scope: global Coordinator bootstrap",
        "scope: per program",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_global_latch_scope(per_program_latch)
    assert "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=" in str(
        rejected.value
    )

    semantic_shape_mutations = (
        _replace_once(
            text,
            "C2B rejects one mutable aggregate JSON row, fully mutable normalized history,\none generic event ledger",
            "C2B introduces one generic event ledger as durable program truth",
        ),
        _replace_once(
            text,
            "closed role-specific relation,\nnot a metadata bag",
            "generic evidence metadata bag",
        ),
        _replace_once(
            text,
            "closed\nkind-specific contract, not a generic decision metadata bag",
            "generic decision metadata bag",
        ),
    )
    for mutation in semantic_shape_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_closed_ledger_metadata_and_trigger_contract(mutation)
        assert "c2b0.semantic|heading=" in str(rejected.value)

    extra_trigger = _replace_once(
        text,
        "0003: latch one-way update guard = 1\n```",
        "0003: latch one-way update guard = 1\n0003: extra trigger = 1\n```",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_schema_contract(extra_trigger)
    assert "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_arithmetic" in str(
        rejected.value
    )

    decision_ownership_mutations = (
        _replace_once(
            text,
            "C2B2 owns and lands both the base\ndecision envelope and initialize-decision row treatment",
            "C2B2 omits the base decision envelope and initialize-decision row treatment",
        ),
        _replace_once(
            text,
            "C2B4 adds only non-initialize, evidence-bearing decision contracts; it neither\nowns initialize representation nor is the first point at which a durable\ndecision row is representable.",
            "C2B4 first represents durable decisions and owns initialize representation.",
        ),
    )
    for mutation in decision_ownership_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_decision_tranche_ownership(mutation)
        assert "c2b0.tranches|heading=21. Migration 0002|failure=" in str(rejected.value)

    generation_mutations = (
        _replace_once(
            text,
            "C2B2 Slice 1 advances the implemented application generation from 1 to 2",
            "C2B2 leaves the implemented application generation at 1",
        ),
        _replace_once(
            text,
            "C2B4 adds migration 0003\nwhile retaining application generation 2",
            "C2B4 advances application generation to 3 when it adds migration 0003",
        ),
    )
    for mutation in generation_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_application_generation_contract(mutation)
        assert "c2b0.migration|heading=20. Migration-Framework Strategy|failure=application_generation" in str(
            rejected.value
        )

    prefix_mutations = (
        _replace_once(
            text,
            "C2B4-or-later fresh installation: 0001 -> 0002 -> 0003",
            "C2B4-or-later fresh installation: apply only 0003",
        ),
        _replace_once(
            text,
            "Ordinary open never silently migrates and never accepts an older prefix.",
            "Ordinary open accepts an exact older prefix without explicit migration.",
        ),
        _replace_once(
            text,
            "one exact non-empty supported older\ncatalog prefix",
            "a non-exact or unsupported older catalog prefix",
        ),
    )
    for mutation in prefix_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_cumulative_migration_contract(mutation)
        assert "c2b0.migration|heading=20. Migration-Framework Strategy|failure=" in str(
            rejected.value
        )

    rollback_mutations = (
        _replace_once(
            text,
            "Historical `0001_initial` therefore remains `[1,1]`",
            "Historical `0001_initial` is rewritten to `[2,2]`",
        ),
        _replace_once(
            text,
            "Failure before commit restores the complete exact prior supported\nprefix with no partial DDL, invariant change, or history row",
            "Failure before commit leaves partial DDL or history",
        ),
    )
    for mutation in rollback_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_migration_failure_and_history_contract(mutation)
        assert "c2b0.migration|heading=20. Migration-Framework Strategy|failure=history_or_rollback" in str(
            rejected.value
        )

    status_mutations = (
        _replace_once(
            text,
            "Migration `0003_development_observation_and_progression_state` remains reserved",
            "No migration number is reserved here",
        ),
        text + "\nExact future state shape, schema, migrations remain wholly open.\n",
        text + "\nC2B is currently implemented.\n",
    )
    for mutation in status_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_current_target_status(mutation)
        assert "c2b0.status|heading=1. Status, Classification, And Layering|failure=" in str(
            rejected.value
        )


def test_c2b0_history_and_current_c2b2_source_boundary_are_distinct() -> None:
    nonimplementation = _compact(_section(_owner(), SECTION_HEADINGS[26]))
    for phrase in (
        "creates no source module, SQL, schema object, migration, database row",
        "writer method, transaction, reader, observation ingest, decision runtime",
        "authority verifier, worker, process, capsule store, Git effect",
        "direct-local adapter, ES client, service, API, IPC, scheduler, queue",
        "adds no dependency, package-root export, public DTO, public `StateStore` method, or public `WriterSession` method",
        "performs no Bridge or ES change",
        "makes no effect dispatch-eligible",
    ):
        assert phrase in nonimplementation

    assert (ROOT / "src/ge_nwp_coordinator/sqlite_migrations/0002_development_program_and_effect_state.sql").is_file()
    assert not (ROOT / "src/ge_nwp_coordinator/sqlite_migrations/0003_development_observation_and_progression_state.sql").exists()
    assert not any("c2b" in path.name.lower() for path in (ROOT / "src").rglob("*.py"))
    slice2_sources = {
        ROOT / "src/ge_nwp_coordinator/_development_row_value_support.py",
        ROOT / "src/ge_nwp_coordinator/_development_program_row_values.py",
        ROOT / "src/ge_nwp_coordinator/_development_effect_row_values.py",
        ROOT / "src/ge_nwp_coordinator/_development_decision_row_values.py",
    }
    slice3_sources = {
        ROOT / "src/ge_nwp_coordinator/_sqlite_development_reader_contracts.py",
        ROOT / "src/ge_nwp_coordinator/_sqlite_development_readers.py",
    }
    assert {
        path
        for path in (ROOT / "src/ge_nwp_coordinator").glob("*development*.py")
    } == slice2_sources | slice3_sources

    production_sources = {
        path: path.read_text(encoding="utf-8")
        for path in (ROOT / "src").rglob("*.py")
    }
    source = "\n".join(production_sources.values())
    migration_source = production_sources.pop(SQLITE_MIGRATION_PATH)
    non_c2b_source = "\n".join(
        value
        for path, value in production_sources.items()
        if path not in slice2_sources | slice3_sources
    )
    _assert_sqlite_migration_c2b_structure(migration_source)
    schema = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (ROOT / "schemas", ROOT / "src/ge_nwp_coordinator/sqlite_migrations")
        for path in root.rglob("*")
        if path.is_file()
    )
    for token in TABLES_0002:
        assert token not in non_c2b_source
        assert token in schema
    for token in TABLES_0003:
        assert token not in source
        assert token not in schema
    assert "CURRENT_APPLICATION_SCHEMA = 2" in source

    pyproject = tomllib.loads(_text("pyproject.toml"))
    assert pyproject["project"]["dependencies"] == []
    assert "scripts" not in pyproject["project"]
    package_root = _text("src/ge_nwp_coordinator/__init__.py")
    for token in ("DevelopmentProgram", "DevelopmentDecision", "DevelopmentEffectIntent"):
        assert token not in package_root
    assert not re.search(
        r"^\s*(?:from|import)\s+(?:execution_substrate|openai_bridge)(?:\.|\s|$)",
        source,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    assert "ExecutionSubstrateClient" not in source
    assert "OpenAIBridgeClient" not in source


def test_sqlite_migration_c2b_references_match_exact_migration_only_allowlist() -> None:
    inventory = _assert_sqlite_migration_c2b_structure(
        SQLITE_MIGRATION_PATH.read_text(encoding="utf-8")
    )
    table_entries = tuple(entry for entry in inventory if entry[2] in TABLES_0002)
    assert len(table_entries) == 38
    assert frozenset(entry[2] for entry in table_entries) == frozenset(TABLES_0002)
    assert all(
        entry[3]
        in {
            "literal migration catalog/resource metadata",
            "schema introspection and verification",
            "sequence-scoped migration-completion zero-seed checks",
            "the SQLite runtime-floor gate",
        }
        for entry in inventory
    )


@pytest.mark.parametrize(
    "mutant",
    (
        """
def _read_development_program_head(connection):
    return connection.execute("SELECT * FROM development_program_heads").fetchone()
""",
        """
def _decode_development_program_head(row):
    return {"development_program_heads": row}
""",
        """
def _mutate_development_program_head(connection):
    connection.execute("INSERT INTO development_program_heads VALUES (?)", ("x",))
""",
        """
class _DevelopmentProgramValue:
    pass
""",
    ),
    ids=("private-reader", "row-decoder", "insert-mutation", "value-class"),
)
def test_sqlite_migration_c2b_structural_allowlist_rejects_runtime_mutants(
    mutant: str,
) -> None:
    live = SQLITE_MIGRATION_PATH.read_text(encoding="utf-8")
    with pytest.raises(AssertionError):
        _assert_sqlite_migration_c2b_structure(live + mutant)


def test_direct_negative_decision_basis_effect_and_stop_mutations_fail() -> None:
    text = _owner()

    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "redeliver\ncancel\n", "redeliver\n"))
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "redeliver\ncancel\n", "redeliver\ncancel\ncancel_request\n"))
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "cancel: no program-version advance", "cancel: appends a program version"))
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "`cancel` is a real immutable Coordinator decision.", "`block` substitutes for cancel."))
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "It creates no\nversion, attempt, candidate, command, effect, delivery, observation,", "It creates no\nversion or observation; cancel creates a semantic attempt, candidate, and WorkerCommandV1,"))
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(_replace_once(text, "basis_decision_ref TEXT NOT NULL", "basis_decision_ref TEXT NULL"))
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(_replace_once(text, "exact cancel decision that preassigned the cancellation effect", "exact block decision that preassigned the cancellation effect"))
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(_replace_once(text, "exact initialize, repair, or attempt-selecting replan decision", "exact initialize, accept, redeliver, repair, or attempt-selecting replan decision"))
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(_replace_once(text, "development_effect_intents.command_ref: non-unique foreign key", "development_effect_intents.command_ref: unique foreign key"))
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(_replace_once(text, "one author_candidate effect per command", "two author effects per command are permitted"))
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(text + "\nValidation creates a second semantic attempt.\n")
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(text + "\nReview creates a second WorkerCommandV1.\n")
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "An author\ntarget forbids the paired capsule fields.", "An author target requires capsule fields."))
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "requires the exact paired capsule-manifest ref and portable digest", "permits absent capsule bindings"))
    with pytest.raises(AssertionError):
        _assert_stop_contract(_replace_once(text, "establish author effect: block", "establish author effect: permit"))
    with pytest.raises(AssertionError):
        _assert_stop_contract(_replace_once(text, "ingest source observation: permit", "ingest source observation: block"))
    with pytest.raises(AssertionError):
        _assert_stop_contract(_replace_once(text, "record cancel decision: permit", "record cancel decision: block"))
    with pytest.raises(AssertionError):
        _assert_stop_contract(_replace_once(text, "creates no\nreceipt. Stop-version disagreement", "creates a receipt. Stop-version disagreement"))


def test_direct_negative_privacy_schema_scope_and_tranche_mutations_fail() -> None:
    text = _owner()

    with pytest.raises(AssertionError):
        _assert_privacy_contract(_replace_once(text, "objective text\nrequirements\nexclusions", "C2B may retain objective text\nrequirements\nexclusions"))
    with pytest.raises(AssertionError):
        _assert_privacy_contract(_replace_once(text, "A safe ref is not retrieval authority.", "A safe ref is retrieval authority."))
    with pytest.raises(AssertionError):
        _assert_schema_contract(_replace_once(text, "retains immutable bytes, checksum, history, and\nmeanings", "permits a migration 0001 rewrite"))
    with pytest.raises(AssertionError):
        _assert_schema_contract(_replace_once(text, "idx_development_source_observation_claims_digest\n```", "idx_development_source_observation_claims_digest\nthird_explicit_index\n```"))
    with pytest.raises(AssertionError):
        _assert_schema_contract(_replace_once(text, "development_mutation_receipts\n```", "development_mutation_receipts\ndevelopment_extra_table\n```"))
    with pytest.raises(AssertionError):
        _assert_schema_contract(_replace_once(text, "forty-six triggers", "forty-seven triggers"))
    with pytest.raises(AssertionError):
        _assert_schema_contract(text + "\nC2B uses one broad migration.\n")
    with pytest.raises(AssertionError):
        _assert_tranche_contract(
            _replace_once(
                text,
                "C2B5: application generation 2; terminal tip 0003; source-observation ingest, cancel and redeliver decisions, bound validation/review/cancellation effects, knowledge and recovery; no external I/O",
                "C2B5: application generation 2; terminal tip 0003; source-observation ingest, cancel and redeliver decisions, no bound-effect owner, knowledge and recovery; no external I/O",
            )
        )

    hybrid = _compact(_section(text, SECTION_HEADINGS[3]))
    assert "one generic event ledger" in hybrid
    assert "one mutable aggregate JSON row" in hybrid
    assert "no second database, writer" in _compact(_section(text, SECTION_HEADINGS[1]))
    assert "public `StateStore` method" in _compact(_section(text, SECTION_HEADINGS[26]))
    assert "performs no Bridge or ES change" in _compact(_section(text, SECTION_HEADINGS[26]))


def test_c2b0_migration_recovery_contradictions_reject_through_both_validators() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_migration_failure_and_history_contract(owner)
    _assert_sqlite_migration_summary(sqlite)

    contradictions = (
        "History and live-schema disagreement is committed_exact.",
        "A partial intended suffix is committed_exact.",
        "An unknown or divergent migration-history row is committed_exact.",
        "An unexpected live-schema object is committed_exact.",
        "Incomplete exact history or live-schema verification is committed_exact.",
    )
    for contradiction in contradictions:
        owner_mutation = _replace_once(
            owner,
            "This migration-specific rule is distinct",
            contradiction + "\n\nThis migration-specific rule is distinct",
        )
        with pytest.raises(AssertionError) as owner_rejected:
            _assert_migration_failure_and_history_contract(owner_mutation)
        assert str(owner_rejected.value) == (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_recovery_claim"
        )

        sqlite_mutation = _replace_once(
            sqlite,
            "This migration-specific rule is distinct",
            contradiction + "\n\nThis migration-specific rule is distinct",
        )
        with pytest.raises(AssertionError) as sqlite_rejected:
            _assert_sqlite_migration_summary(sqlite_mutation)
        assert str(sqlite_rejected.value) == (
            "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=forbidden_migration_claim"
        )


def test_c2b0_unresolved_remainder_append_is_forbidden_through_both_validators() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    contradiction = (
        "After an unresolved migration commit, the missing migration-suffix "
        "remainder is automatically appended."
    )

    owner_mutation = _replace_once(
        owner,
        "This migration-specific rule is distinct",
        contradiction + "\n\nThis migration-specific rule is distinct",
    )
    with pytest.raises(AssertionError) as owner_rejected:
        _assert_migration_failure_and_history_contract(owner_mutation)
    assert str(owner_rejected.value) == (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_recovery_claim"
    )

    sqlite_mutation = _replace_once(
        sqlite,
        "This migration-specific rule is distinct",
        contradiction + "\n\nThis migration-specific rule is distinct",
    )
    with pytest.raises(AssertionError) as sqlite_rejected:
        _assert_sqlite_migration_summary(sqlite_mutation)
    assert str(sqlite_rejected.value) == (
        "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=forbidden_migration_claim"
    )


def test_c2b1_required_documentation_negative_matrix() -> None:
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    marker = "An `unresolved` result forbids automatic rerun and automatic append of a"
    _assert_sqlite_migration_summary(sqlite)

    for contradiction in C2B1_REPAIR1_FORBIDDEN_CLAIMS:
        mutation = _replace_once(
            sqlite,
            marker,
            contradiction + "\n\n" + marker,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_sqlite_migration_summary(mutation)
        assert str(rejected.value) == (
            "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|"
            "failure=forbidden_migration_claim"
        )


def test_c2b0_markdown_closer_suffix_is_ascii_space_tab_only() -> None:
    for valid_suffix in ("", " ", "\t", " \t"):
        sample = f"~~~text\n## Hidden\n~~~{valid_suffix}\n## Visible\n"
        headings, visible = _markdown_scan(sample, role="c2b0.repair3")
        assert tuple(item[1] for item in headings) == ("Visible",)
        assert visible == "## Visible\n"

    for invalid_suffix in ("\u00a0", "\u2003", "not-a-closer"):
        closed_later = (
            "~~~text\n"
            f"~~~{invalid_suffix}\n"
            "C2B is currently implemented.\n"
            "## 1. Status, Classification, And Layering\n"
            "~~~\n"
        )
        assert _markdown_scan(closed_later, role="c2b0.repair3") == ((), "")

        with pytest.raises(AssertionError) as scan_rejected:
            _markdown_scan(
                f"~~~text\n~~~{invalid_suffix}\n",
                role="c2b0.repair3",
            )
        assert str(scan_rejected.value) == (
            "c2b0.repair3|heading=<none>|failure=unbalanced_fence"
        )

        with pytest.raises(AssertionError) as block_rejected:
            _top_level_fenced_blocks(
                f"~~~text\n~~~{invalid_suffix}\n",
                role="c2b0.repair3.blocks",
            )
        assert str(block_rejected.value) == (
            "c2b0.repair3.blocks|block=<none>|failure=unbalanced_fence"
        )


def test_c2b0_top_level_fenced_block_reader_rejects_text_bearing_closer_bypass() -> None:
    sample = "  ```text\nalpha\n```not-a-closer\nbeta\n````\n"
    blocks = _top_level_fenced_blocks(sample, role="c2b0.repair3.blocks")
    assert len(blocks) == 1
    block = blocks[0]
    assert block.marker == "`"
    assert block.opener_length == 3
    assert block.info == "text"
    assert block.opening_line == "  ```text\n"
    assert block.closing_line == "````\n"
    assert block.opening_line_number == 1
    assert block.closing_line_number == 5
    assert block.start_offset == 0
    assert block.end_offset == len(sample)
    assert block.content_start_offset == len(block.opening_line)
    assert block.content_end_offset == sample.index("````\n")
    assert block.content == "alpha\n```not-a-closer\nbeta\n"
    assert _text_blocks(sample) == (("alpha", "```not-a-closer", "beta"),)

    with pytest.raises(AssertionError) as rejected:
        _top_level_fenced_blocks(
            "```text\nalpha\n```not-a-closer\nbeta\n",
            role="c2b0.repair3.blocks",
        )
    assert str(rejected.value) == (
        "c2b0.repair3.blocks|block=<none>|failure=unbalanced_fence"
    )


def test_c2b0_top_level_fenced_block_reader_respects_outer_tilde_fences() -> None:
    sample = (
        "~~~~example\n"
        "```text\nouter-tilde-hidden\n```\n"
        "~~~~\n"
        "````example\n"
        "~~~text\nouter-backtick-hidden\n~~~\n"
        "````\n"
        "```text\nvisible-semantic-block\n```\n"
    )
    blocks = _top_level_fenced_blocks(sample, role="c2b0.repair3.blocks")
    assert tuple(block.marker for block in blocks) == ("~", "`", "`")
    assert tuple(block.opener_length for block in blocks) == (4, 4, 3)
    assert tuple(block.info for block in blocks) == ("example", "example", "text")
    assert _text_blocks(sample) == (("visible-semantic-block",),)


def test_c2b0_decision_inventory_cannot_be_truncated_by_pseudo_closer() -> None:
    text = _owner()
    for closer_suffix in ("not-a-closer", "\u00a0", "\u2003"):
        mutation = _inventory_pseudo_closer_mutation(
            text,
            final_item="cancel",
            hidden_addition="retry",
            closer_suffix=closer_suffix,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_decision_and_cancel_contract(mutation)
        assert str(rejected.value) == (
            "c2b0.decisions|heading=6. Exact Decision-Kind Inventory|failure=closed_inventory"
        )

    outer_examples = _insert_before_owner_heading(
        text,
        next_heading=SECTION_HEADINGS[6],
        insertion=_outer_nonsemantic_inventory_examples("retry"),
    )
    _assert_decision_and_cancel_contract(outer_examples)


def test_c2b0_disposition_inventory_cannot_be_truncated_by_pseudo_closer() -> None:
    text = _owner()
    for closer_suffix in ("not-a-closer", "\u00a0", "\u2003"):
        mutation = _inventory_pseudo_closer_mutation(
            text,
            final_item="recorded",
            hidden_addition="accepted",
            closer_suffix=closer_suffix,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_observation_ingest_authority(mutation)
        assert str(rejected.value) == (
            "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=disposition_inventory"
        )

    outer_examples = _insert_before_owner_heading(
        text,
        next_heading=SECTION_HEADINGS[13],
        insertion=_outer_nonsemantic_inventory_examples("accepted"),
    )
    _assert_observation_ingest_authority(outer_examples)


def test_c2b0_latch_inventory_cannot_be_truncated_by_pseudo_closer() -> None:
    text = _owner()
    for closer_suffix in ("not-a-closer", "\u00a0", "\u2003"):
        mutation = _inventory_pseudo_closer_mutation(
            text,
            final_item="reuse: forbidden",
            hidden_addition="reuse: allowed",
            closer_suffix=closer_suffix,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_global_latch_scope(mutation)
        assert str(rejected.value) == (
            "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=scope"
        )

    outer_examples = _insert_before_owner_heading(
        text,
        next_heading=SECTION_HEADINGS[19],
        insertion=_outer_nonsemantic_inventory_examples("reuse: allowed"),
    )
    _assert_global_latch_scope(outer_examples)


def test_c2b0_migration_and_trigger_inventories_cannot_be_truncated() -> None:
    text = _owner()
    cases = (
        (
            "development_mutation_receipts",
            "development_extra_0002_table",
            "c2b0.schema|heading=21. Migration 0002|failure=table_inventory",
        ),
        (
            "development_publication_eligibility\ndevelopment_first_slice_latch",
            "development_extra_0003_table",
            "c2b0.schema|heading=22. Migration 0003|failure=table_inventory",
        ),
        (
            "0003: latch one-way update guard = 1",
            "0003: extra trigger = 1",
            "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_arithmetic",
        ),
        (
            "idx_development_source_observation_claims_digest",
            "idx_third_explicit_index",
            "c2b0.schema|heading=24. Exact Explicit Indexes|failure=index_inventory",
        ),
    )
    for final_item, hidden_addition, diagnostic in cases:
        for closer_suffix in ("not-a-closer", "\u00a0", "\u2003"):
            mutation = _inventory_pseudo_closer_mutation(
                text,
                final_item=final_item,
                hidden_addition=hidden_addition,
                closer_suffix=closer_suffix,
            )
            with pytest.raises(AssertionError) as rejected:
                _assert_schema_contract(mutation)
            assert str(rejected.value) == diagnostic

    outer_examples = _insert_before_owner_heading(
        text,
        next_heading=SECTION_HEADINGS[21],
        insertion=_outer_nonsemantic_inventory_examples(
            "development_extra_0002_table"
        ),
    )
    outer_examples = _insert_before_owner_heading(
        outer_examples,
        next_heading=SECTION_HEADINGS[22],
        insertion=_outer_nonsemantic_inventory_examples(
            "development_extra_0003_table"
        ),
    )
    outer_examples = _insert_before_owner_heading(
        outer_examples,
        next_heading=SECTION_HEADINGS[23],
        insertion=_outer_nonsemantic_inventory_examples("0003: extra trigger = 1"),
    )
    outer_examples = _insert_before_owner_heading(
        outer_examples,
        next_heading=SECTION_HEADINGS[24],
        insertion=_outer_nonsemantic_inventory_examples("idx_third_explicit_index"),
    )
    _assert_schema_contract(outer_examples)


def test_c2b0_mutation_and_recovery_families_cannot_be_truncated() -> None:
    text = _owner()
    cases = (
        (
            "_record_development_progression_decision",
            "_sixth_development_mutation",
        ),
        (
            "_resolve_development_progression_decision_commit_outcome",
            "_resolve_sixth_development_commit_outcome",
        ),
    )
    for final_item, hidden_addition in cases:
        for closer_suffix in ("not-a-closer", "\u00a0", "\u2003"):
            mutation = _inventory_pseudo_closer_mutation(
                text,
                final_item=final_item,
                hidden_addition=hidden_addition,
                closer_suffix=closer_suffix,
            )
            with pytest.raises(AssertionError) as rejected:
                _assert_mutation_and_recovery_family_contract(mutation)
            assert str(rejected.value) == (
                "c2b0.families|heading=12. Complete Target Mutation Families|failure=closed_blocks"
            )

    outer_examples = _insert_before_owner_heading(
        text,
        next_heading=SECTION_HEADINGS[12],
        insertion=_outer_nonsemantic_inventory_examples(
            "_sixth_development_mutation\n_resolve_sixth_development_commit_outcome"
        ),
    )
    _assert_mutation_and_recovery_family_contract(outer_examples)


def test_c2b0_first_slice_latch_requires_reuse_forbidden() -> None:
    text = _owner()
    _assert_global_latch_scope(text)

    missing = _replace_once(text, "reuse: forbidden\n", "")
    with pytest.raises(AssertionError) as missing_rejected:
        _assert_global_latch_scope(missing)
    assert str(missing_rejected.value) == (
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=scope"
    )

    for widened in ("reuse: allowed", "reuse: permitted", "reuse: true", "reuse: once_more"):
        mutation = _replace_once(text, "reuse: forbidden", widened)
        with pytest.raises(AssertionError) as rejected:
            _assert_global_latch_scope(mutation)
        assert str(rejected.value) == (
            "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=scope"
        )


def test_c2b0_repair3_full_audit_counterfactual_matrix() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_migration_failure_and_history_contract(owner)
    _assert_sqlite_migration_summary(sqlite)
    _assert_global_latch_scope(owner)

    recovery_contradictions = (
        "History and live-schema disagreement is committed_exact.",
        "A partial intended suffix is committed_exact.",
        "An unknown or divergent migration-history row is committed_exact.",
        "An unexpected live-schema object is committed_exact.",
        "Incomplete exact history or live-schema verification is committed_exact.",
        "After an unresolved migration commit, the missing migration-suffix remainder is automatically appended.",
    )
    for contradiction in recovery_contradictions:
        owner_mutation = _replace_once(
            owner,
            "This migration-specific rule is distinct",
            contradiction + "\n\nThis migration-specific rule is distinct",
        )
        with pytest.raises(AssertionError) as owner_rejected:
            _assert_migration_failure_and_history_contract(owner_mutation)
        assert str(owner_rejected.value).endswith("failure=forbidden_recovery_claim")

        sqlite_mutation = _replace_once(
            sqlite,
            "This migration-specific rule is distinct",
            contradiction + "\n\nThis migration-specific rule is distinct",
        )
        with pytest.raises(AssertionError) as sqlite_rejected:
            _assert_sqlite_migration_summary(sqlite_mutation)
        assert str(sqlite_rejected.value).endswith("failure=forbidden_migration_claim")

    for invalid_suffix in ("\u00a0", "\u2003"):
        with pytest.raises(AssertionError) as rejected:
            _markdown_scan(
                f"```text\n```{invalid_suffix}\n",
                role="c2b0.repair3.matrix",
            )
        assert str(rejected.value) == (
            "c2b0.repair3.matrix|heading=<none>|failure=unbalanced_fence"
        )

    decision_mutation = _inventory_pseudo_closer_mutation(
        owner,
        final_item="cancel",
        hidden_addition="retry",
        closer_suffix="not-a-closer",
    )
    with pytest.raises(AssertionError) as decision_rejected:
        _assert_decision_and_cancel_contract(decision_mutation)
    assert str(decision_rejected.value) == (
        "c2b0.decisions|heading=6. Exact Decision-Kind Inventory|failure=closed_inventory"
    )

    disposition_mutation = _inventory_pseudo_closer_mutation(
        owner,
        final_item="recorded",
        hidden_addition="accepted",
        closer_suffix="not-a-closer",
    )
    with pytest.raises(AssertionError) as disposition_rejected:
        _assert_observation_ingest_authority(disposition_mutation)
    assert str(disposition_rejected.value) == (
        "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=disposition_inventory"
    )

    latch_mutation = _inventory_pseudo_closer_mutation(
        owner,
        final_item="reuse: forbidden",
        hidden_addition="reuse: allowed",
        closer_suffix="not-a-closer",
    )
    with pytest.raises(AssertionError) as latch_rejected:
        _assert_global_latch_scope(latch_mutation)
    assert str(latch_rejected.value) == (
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=scope"
    )


def test_c2b0_migration_recovery_all_semantic_blocks_are_closed() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    owner_section = _section(owner, SECTION_HEADINGS[19])
    sqlite_section = _summary_section(
        sqlite,
        "C2B0 Target Migration Sequence",
        role="c2b0.repair4.sqlite",
    )
    assert _text_blocks(owner_section) == (
        ORDINARY_OPEN_RULES,
        MIGRATION_PATHS,
        MIGRATION_TRANSACTION_PATHS,
        MIGRATION_TRANSACTION_COMPONENTS,
        MIGRATION_RECOVERY_STEPS,
        MIGRATION_COMMITTED_EXACT,
        MIGRATION_DEFINITELY_NOT_COMMITTED,
        MIGRATION_UNRESOLVED,
    )
    assert _text_blocks(sqlite_section) == (
        MIGRATION_PATHS,
        MIGRATION_TRANSACTION_PATHS,
        MIGRATION_TRANSACTION_COMPONENTS,
        MIGRATION_RECOVERY_STEPS,
        MIGRATION_COMMITTED_EXACT,
        MIGRATION_DEFINITELY_NOT_COMMITTED,
        MIGRATION_UNRESOLVED,
        SQLITE_MIGRATION_DEFINITIONS,
        SQLITE_MIGRATION_SCHEMA_TOTALS,
    )

    marker = "An `unresolved` result forbids automatic rerun and automatic append of a"
    addition = "```text\nanother recovery classification\n```\n\n"
    with pytest.raises(AssertionError) as owner_rejected:
        _assert_migration_failure_and_history_contract(
            _replace_once(owner, marker, addition + marker)
        )
    assert str(owner_rejected.value) == (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=commit_uncertainty_mapping"
    )

    with pytest.raises(AssertionError) as sqlite_rejected:
        _assert_sqlite_migration_summary(
            _replace_once(sqlite, marker, addition + marker)
        )
    assert str(sqlite_rejected.value) == (
        "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=transaction_or_recovery_mapping"
    )

    outer = _outer_nonsemantic_inventory_examples("another recovery classification")
    _assert_migration_failure_and_history_contract(
        _replace_once(owner, marker, outer + "\n" + marker)
    )
    _assert_sqlite_migration_summary(
        _replace_once(sqlite, marker, outer + "\n" + marker)
    )


def test_c2b0_migration_recovery_nine_prohibitions_reject_through_both_validators() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    marker = "An `unresolved` result forbids automatic rerun and automatic append of a"
    contradictions = (
        "History and live-schema disagreement is committed_exact.",
        "A partial intended suffix is committed_exact.",
        "An unknown or divergent migration-history row is committed_exact.",
        "An unexpected live-schema object is committed_exact.",
        "Incomplete exact history or live-schema verification is committed_exact.",
        "Matching migration history alone is committed_exact even when the live schema differs.",
        "Matching live schema alone is committed_exact even when migration history differs.",
        "After an unresolved migration commit, the suffix is automatically rerun.",
        "After an unresolved migration commit, the missing migration-suffix remainder is automatically appended.",
    )
    for contradiction in contradictions:
        block = f"```text\n{contradiction}\n```\n\n"
        with pytest.raises(AssertionError) as owner_rejected:
            _assert_migration_failure_and_history_contract(
                _replace_once(owner, marker, block + marker)
            )
        owner_diagnostic = str(owner_rejected.value)
        assert owner_diagnostic == (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=commit_uncertainty_mapping"
        )
        assert contradiction not in owner_diagnostic

        with pytest.raises(AssertionError) as sqlite_rejected:
            _assert_sqlite_migration_summary(
                _replace_once(sqlite, marker, block + marker)
            )
        sqlite_diagnostic = str(sqlite_rejected.value)
        assert sqlite_diagnostic == (
            "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=transaction_or_recovery_mapping"
        )
        assert contradiction not in sqlite_diagnostic


def test_c2b0_disposition_inventory_is_closed_across_all_semantic_blocks() -> None:
    owner = _owner()
    section = _section(owner, SECTION_HEADINGS[12])
    assert _text_blocks(section) == (OBSERVATION_INGEST_STEPS, DISPOSITIONS)

    appended = _replace_once(owner, "recorded\n```", "recorded\naccepted\n```")
    with pytest.raises(AssertionError) as appended_rejected:
        _assert_observation_ingest_authority(appended)
    assert str(appended_rejected.value).endswith("failure=disposition_inventory")

    duplicate = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[13],
        insertion="```text\n" + "\n".join(DISPOSITIONS) + "\n```\n",
    )
    with pytest.raises(AssertionError) as duplicate_rejected:
        _assert_observation_ingest_authority(duplicate)
    assert str(duplicate_rejected.value).endswith("failure=disposition_inventory")

    alias = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[13],
        insertion="```text\nrecorded_alias\n```\n",
    )
    with pytest.raises(AssertionError) as alias_rejected:
        _assert_observation_ingest_authority(alias)
    assert str(alias_rejected.value).endswith("failure=disposition_inventory")


def test_c2b0_separate_block_accepted_disposition_is_rejected() -> None:
    mutation = _insert_before_owner_heading(
        _owner(),
        next_heading=SECTION_HEADINGS[13],
        insertion="```text\naccepted\n```\n",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_observation_ingest_authority(mutation)
    assert str(rejected.value) == (
        "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=disposition_inventory"
    )


def test_c2b0_latch_contract_is_unique_and_complete() -> None:
    owner = _owner()
    _assert_global_latch_scope(owner)
    latch = _section(owner, SECTION_HEADINGS[18])
    assert _text_blocks(latch) == (LATCH_CONTRACT,)

    missing = _replace_once(owner, "reuse: forbidden\n", "")
    with pytest.raises(AssertionError) as missing_rejected:
        _assert_global_latch_scope(missing)
    assert str(missing_rejected.value).endswith("failure=scope")

    duplicate = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[19],
        insertion="```text\n" + "\n".join(LATCH_CONTRACT) + "\n```\n",
    )
    with pytest.raises(AssertionError) as duplicate_rejected:
        _assert_global_latch_scope(duplicate)
    assert str(duplicate_rejected.value).endswith("failure=contract_inventory")

    second_latch = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[19],
        insertion="latch_ref: second_productive_acceptance\n",
    )
    with pytest.raises(AssertionError) as second_latch_rejected:
        _assert_global_latch_scope(second_latch)
    assert str(second_latch_rejected.value).endswith(
        "failure=additive_scope_or_lifecycle"
    )


def test_c2b0_additional_latch_reuse_declarations_are_rejected() -> None:
    owner = _owner()
    for declaration in (
        "reuse: allowed",
        "reuse: permitted",
        "reuse: true",
        "reuse: once_more",
    ):
        mutation = _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[19],
            insertion=declaration + "\n",
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_global_latch_scope(mutation)
        assert str(rejected.value).endswith("failure=additive_scope_or_lifecycle")

    separate_block = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[19],
        insertion="```text\nreuse: allowed\n```\n",
    )
    with pytest.raises(AssertionError) as block_rejected:
        _assert_global_latch_scope(separate_block)
    assert str(block_rejected.value).endswith("failure=contract_inventory")


def test_c2b0_visible_additional_trigger_arithmetic_is_rejected() -> None:
    owner = _owner()
    _assert_schema_contract(owner)

    visible = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion="0003: extra trigger = 1\n",
    )
    with pytest.raises(AssertionError) as visible_rejected:
        _assert_schema_contract(visible)
    assert str(visible_rejected.value).endswith("failure=additive_trigger_arithmetic")

    totals_block = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion="```text\n0003: extra trigger = 1\n```\n",
    )
    with pytest.raises(AssertionError) as totals_block_rejected:
        _assert_schema_contract(totals_block)
    assert str(totals_block_rejected.value).endswith("failure=closed_totals_blocks")

    migration_block = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="```text\n0003: extra trigger = 1\n```\n",
    )
    with pytest.raises(AssertionError) as migration_block_rejected:
        _assert_schema_contract(migration_block)
    assert str(migration_block_rejected.value).endswith(
        "failure=additive_trigger_arithmetic"
    )


def test_c2b0_repair4_full_audit_counterfactual_matrix() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_migration_failure_and_history_contract(owner)
    _assert_sqlite_migration_summary(sqlite)
    _assert_observation_ingest_authority(owner)
    _assert_global_latch_scope(owner)
    _assert_schema_contract(owner)

    marker = "An `unresolved` result forbids automatic rerun and automatic append of a"
    contradictions = (
        "History and live-schema disagreement is committed_exact.",
        "A partial intended suffix is committed_exact.",
        "An unknown or divergent migration-history row is committed_exact.",
        "An unexpected live-schema object is committed_exact.",
        "Incomplete exact history or live-schema verification is committed_exact.",
        "Matching migration history alone is committed_exact even when the live schema differs.",
        "Matching live schema alone is committed_exact even when migration history differs.",
        "After an unresolved migration commit, the suffix is automatically rerun.",
        "After an unresolved migration commit, the missing migration-suffix remainder is automatically appended.",
    )
    for contradiction in contradictions:
        block = f"```text\n{contradiction}\n```\n\n"
        with pytest.raises(AssertionError) as owner_rejected:
            _assert_migration_failure_and_history_contract(
                _replace_once(owner, marker, block + marker)
            )
        assert str(owner_rejected.value) == (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=commit_uncertainty_mapping"
        )

        with pytest.raises(AssertionError) as sqlite_rejected:
            _assert_sqlite_migration_summary(
                _replace_once(sqlite, marker, block + marker)
            )
        assert str(sqlite_rejected.value) == (
            "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=transaction_or_recovery_mapping"
        )

    disposition = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[13],
        insertion="```text\naccepted\n```\n",
    )
    with pytest.raises(AssertionError) as disposition_rejected:
        _assert_observation_ingest_authority(disposition)
    assert str(disposition_rejected.value).endswith("failure=disposition_inventory")

    for declaration in (
        "reuse: allowed",
        "reuse: permitted",
        "reuse: true",
        "reuse: once_more",
    ):
        latch = _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[19],
            insertion=declaration + "\n",
        )
        with pytest.raises(AssertionError) as latch_rejected:
            _assert_global_latch_scope(latch)
        assert str(latch_rejected.value).endswith("failure=additive_scope_or_lifecycle")

    latch_block = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[19],
        insertion="```text\nreuse: allowed\n```\n",
    )
    with pytest.raises(AssertionError) as latch_block_rejected:
        _assert_global_latch_scope(latch_block)
    assert str(latch_block_rejected.value).endswith("failure=contract_inventory")

    trigger = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion="0003: extra trigger = 1\n",
    )
    with pytest.raises(AssertionError) as trigger_rejected:
        _assert_schema_contract(trigger)
    assert str(trigger_rejected.value).endswith("failure=additive_trigger_arithmetic")

    outer_owner = _replace_once(
        owner,
        marker,
        _outer_nonsemantic_inventory_examples(
            "History and live-schema disagreement is committed_exact."
        )
        + "\n"
        + marker,
    )
    outer_sqlite = _replace_once(
        sqlite,
        marker,
        _outer_nonsemantic_inventory_examples(
            "History and live-schema disagreement is committed_exact."
        )
        + "\n"
        + marker,
    )
    _assert_migration_failure_and_history_contract(outer_owner)
    _assert_sqlite_migration_summary(outer_sqlite)

    for invalid_suffix in ("not-a-closer", "\u00a0", "\u2003"):
        with pytest.raises(AssertionError) as closer_rejected:
            _markdown_scan(
                f"```text\n```{invalid_suffix}\n",
                role="c2b0.repair4.matrix",
            )
        assert str(closer_rejected.value) == (
            "c2b0.repair4.matrix|heading=<none>|failure=unbalanced_fence"
        )


def test_c2b0_semantic_text_blocks_are_marker_neutral() -> None:
    expected = (("alpha", "beta"),)
    assert _text_blocks("```text\nalpha\nbeta\n```\n") == expected
    assert _text_blocks("~~~text\nalpha\nbeta\n~~~\n") == expected
    assert _text_blocks("~~~ text \t\nalpha\nbeta\n~~~\n") == expected
    assert _text_blocks(
        _outer_nonsemantic_inventory_examples("alpha\nbeta")
    ) == ()

    for unclosed in (
        "```text\nalpha\n",
        "~~~text\nalpha\n",
    ):
        with pytest.raises(AssertionError) as rejected:
            _text_blocks(unclosed)
        assert str(rejected.value) == (
            "c2b0.text_blocks|block=<none>|failure=unbalanced_fence"
        )


def test_c2b0_migration_recovery_nine_prohibitions_reject_under_both_delimiters_and_validators() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    insertion_marker = "An `unresolved` result forbids automatic rerun and automatic append of a"
    contradictions = (
        "History and live-schema disagreement is committed_exact.",
        "A partial intended suffix is committed_exact.",
        "An unknown or divergent migration-history row is committed_exact.",
        "An unexpected live-schema object is committed_exact.",
        "Incomplete exact history or live-schema verification is committed_exact.",
        "Matching migration history alone is committed_exact even when the live schema differs.",
        "Matching live schema alone is committed_exact even when migration history differs.",
        "After an unresolved migration commit, the suffix is automatically rerun.",
        "After an unresolved migration commit, the missing migration-suffix remainder is automatically appended.",
    )

    rejection_count = 0
    for delimiter in ("```", "~~~"):
        for contradiction in contradictions:
            semantic_block = f"{delimiter}text\n{contradiction}\n{delimiter}\n\n"
            owner_mutation = _replace_once(
                owner,
                insertion_marker,
                semantic_block + insertion_marker,
            )
            with pytest.raises(AssertionError) as owner_rejected:
                _assert_migration_failure_and_history_contract(owner_mutation)
            owner_diagnostic = str(owner_rejected.value)
            assert owner_diagnostic == (
                "c2b0.migration|heading=20. Migration-Framework Strategy|failure=commit_uncertainty_mapping"
            )
            assert contradiction not in owner_diagnostic
            rejection_count += 1

            sqlite_mutation = _replace_once(
                sqlite,
                insertion_marker,
                semantic_block + insertion_marker,
            )
            with pytest.raises(AssertionError) as sqlite_rejected:
                _assert_sqlite_migration_summary(sqlite_mutation)
            sqlite_diagnostic = str(sqlite_rejected.value)
            assert sqlite_diagnostic == (
                "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=transaction_or_recovery_mapping"
            )
            assert contradiction not in sqlite_diagnostic
            rejection_count += 1

    assert rejection_count == 36


def test_c2b0_tilde_disposition_inventory_is_closed() -> None:
    owner = _owner()
    _assert_observation_ingest_authority(owner)

    primary = _replace_once(owner, "recorded\n```", "recorded\naccepted\n```")
    with pytest.raises(AssertionError) as primary_rejected:
        _assert_observation_ingest_authority(primary)
    assert str(primary_rejected.value).endswith("failure=disposition_inventory")

    for delimiter in ("```", "~~~"):
        separate = _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[13],
            insertion=f"{delimiter}text\naccepted\n{delimiter}\n",
        )
        with pytest.raises(AssertionError) as separate_rejected:
            _assert_observation_ingest_authority(separate)
        assert str(separate_rejected.value).endswith("failure=disposition_inventory")

        duplicate = _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[13],
            insertion=delimiter + "text\n" + "\n".join(DISPOSITIONS) + "\n" + delimiter + "\n",
        )
        with pytest.raises(AssertionError) as duplicate_rejected:
            _assert_observation_ingest_authority(duplicate)
        assert str(duplicate_rejected.value).endswith("failure=disposition_inventory")

    case_variant = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[13],
        insertion="~~~text\nRecorded\n~~~\n",
    )
    with pytest.raises(AssertionError) as case_rejected:
        _assert_observation_ingest_authority(case_variant)
    assert str(case_rejected.value).endswith("failure=disposition_inventory")

    outer = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[13],
        insertion=_outer_nonsemantic_inventory_examples("accepted"),
    )
    _assert_observation_ingest_authority(outer)


def test_c2b0_latch_governing_and_seed_roles_are_unique_and_bound() -> None:
    owner = _owner()
    _assert_global_latch_scope(owner)

    wrong_seed_identity = _replace_once(
        owner,
        "latch_ref: direct_local_first_productive_acceptance\nstate: available",
        "latch_ref: wrong_first_productive_acceptance\nstate: available",
    )
    wrong_seed_state = _replace_once(
        owner,
        "state: available\nversion: 0\nconsumed bindings: null",
        "state: consumed\nversion: 0\nconsumed bindings: null",
    )
    wrong_seed_version = _replace_once(
        owner,
        "state: available\nversion: 0\nconsumed bindings: null",
        "state: available\nversion: 1\nconsumed bindings: null",
    )
    non_null_seed_binding = _replace_once(
        owner,
        "state: available\nversion: 0\nconsumed bindings: null",
        "state: available\nversion: 0\nconsumed bindings: decision_ref",
    )
    second_seed = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="```text\n" + "\n".join(LATCH_SEED_CONTRACT) + "\n```\n",
    )
    second_governing = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[19],
        insertion="~~~text\n" + "\n".join(LATCH_CONTRACT) + "\n~~~\n",
    )
    missing_reuse = _replace_once(owner, "reuse: forbidden\n", "")

    for mutation in (
        wrong_seed_identity,
        wrong_seed_state,
        wrong_seed_version,
        non_null_seed_binding,
        second_seed,
        second_governing,
        missing_reuse,
    ):
        with pytest.raises(AssertionError) as rejected:
            _assert_global_latch_scope(mutation)
        diagnostic = str(rejected.value)
        assert diagnostic
        assert diagnostic.startswith("c2b0.semantic|heading=")
        assert "failure=" in diagnostic


def test_c2b0_out_of_section_latch_reuse_is_rejected() -> None:
    owner = _owner()
    section_19_tilde = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[19],
        insertion="~~~text\nreuse: allowed\n~~~\n",
    )
    section_22_visible = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="reuse: allowed\n",
    )
    section_22_tilde = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="~~~text\nreuse: allowed\n~~~\n",
    )
    section_22_backtick = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="```text\nreuse: allowed\n```\n",
    )

    for mutation in (
        section_19_tilde,
        section_22_visible,
        section_22_tilde,
        section_22_backtick,
    ):
        with pytest.raises(AssertionError) as rejected:
            _assert_global_latch_scope(mutation)
        diagnostic = str(rejected.value)
        assert diagnostic
        assert diagnostic.startswith("c2b0.semantic|heading=")
        assert "failure=" in diagnostic

    outer = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion=_outer_nonsemantic_inventory_examples("reuse: allowed"),
    )
    _assert_global_latch_scope(outer)


def test_c2b0_trigger_totals_are_role_unique() -> None:
    owner = _owner()
    _assert_schema_contract(owner)

    conflicting_schema_tip = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion="schema tip 0003: 39 user tables, 2 explicit application indexes, 63 triggers\n",
    )
    conflicting_aggregate = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion="C2B adds exactly twenty-eight tables, forty-seven triggers, and two explicit indexes.\n",
    )
    duplicate_schema_tip = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion=TRIGGER_SCHEMA_ROLE_CLAIMS[2] + "\n",
    )
    duplicate_aggregate = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion=TRIGGER_AGGREGATE_ROLE_CLAIMS[0] + "\n",
    )
    extra_backtick = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="```text\n0003: extra trigger = 1\n```\n",
    )
    extra_tilde = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="~~~text\n0003: extra trigger = 1\n~~~\n",
    )

    for mutation in (
        conflicting_schema_tip,
        conflicting_aggregate,
        duplicate_schema_tip,
        duplicate_aggregate,
        extra_backtick,
        extra_tilde,
    ):
        with pytest.raises(AssertionError) as rejected:
            _assert_schema_contract(mutation)
        diagnostic = str(rejected.value)
        assert diagnostic
        assert diagnostic.startswith("c2b0.schema|heading=")
        assert "failure=" in diagnostic


def test_c2b0_tilde_trigger_arithmetic_is_closed() -> None:
    owner = _owner()
    mutation = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="~~~text\n0003: extra trigger = 1\n~~~\n",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_schema_contract(mutation)
    assert str(rejected.value).endswith("failure=additive_trigger_arithmetic")

    outer = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion=_outer_nonsemantic_inventory_examples("0003: extra trigger = 1"),
    )
    _assert_schema_contract(outer)


def test_c2b0_repair5_full_audit_counterfactual_matrix() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_migration_failure_and_history_contract(owner)
    _assert_sqlite_migration_summary(sqlite)
    _assert_observation_ingest_authority(owner)
    _assert_global_latch_scope(owner)
    _assert_schema_contract(owner)

    insertion_marker = "An `unresolved` result forbids automatic rerun and automatic append of a"
    contradictions = (
        "History and live-schema disagreement is committed_exact.",
        "A partial intended suffix is committed_exact.",
        "An unknown or divergent migration-history row is committed_exact.",
        "An unexpected live-schema object is committed_exact.",
        "Incomplete exact history or live-schema verification is committed_exact.",
        "Matching migration history alone is committed_exact even when the live schema differs.",
        "Matching live schema alone is committed_exact even when migration history differs.",
        "After an unresolved migration commit, the suffix is automatically rerun.",
        "After an unresolved migration commit, the missing migration-suffix remainder is automatically appended.",
    )
    migration_rejections = 0
    for delimiter in ("```", "~~~"):
        for contradiction in contradictions:
            block = f"{delimiter}text\n{contradiction}\n{delimiter}\n\n"
            owner_mutation = _replace_once(owner, insertion_marker, block + insertion_marker)
            with pytest.raises(AssertionError) as owner_rejected:
                _assert_migration_failure_and_history_contract(owner_mutation)
            assert str(owner_rejected.value) == (
                "c2b0.migration|heading=20. Migration-Framework Strategy|failure=commit_uncertainty_mapping"
            )
            assert contradiction not in str(owner_rejected.value)
            migration_rejections += 1

            sqlite_mutation = _replace_once(sqlite, insertion_marker, block + insertion_marker)
            with pytest.raises(AssertionError) as sqlite_rejected:
                _assert_sqlite_migration_summary(sqlite_mutation)
            assert str(sqlite_rejected.value) == (
                "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=transaction_or_recovery_mapping"
            )
            assert contradiction not in str(sqlite_rejected.value)
            migration_rejections += 1
    assert migration_rejections == 36

    for delimiter in ("```", "~~~"):
        disposition = _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[13],
            insertion=f"{delimiter}text\naccepted\n{delimiter}\n",
        )
        with pytest.raises(AssertionError) as disposition_rejected:
            _assert_observation_ingest_authority(disposition)
        assert str(disposition_rejected.value).endswith("failure=disposition_inventory")

    latch_mutations = (
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[19],
            insertion="~~~text\nreuse: allowed\n~~~\n",
        ),
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[22],
            insertion="reuse: allowed\n",
        ),
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[22],
            insertion="~~~text\nreuse: allowed\n~~~\n",
        ),
        _replace_once(
            owner,
            "latch_ref: direct_local_first_productive_acceptance\nstate: available",
            "latch_ref: wrong_first_productive_acceptance\nstate: available",
        ),
        _replace_once(
            owner,
            "state: available\nversion: 0\nconsumed bindings: null",
            "state: consumed\nversion: 0\nconsumed bindings: null",
        ),
        _replace_once(
            owner,
            "state: available\nversion: 0\nconsumed bindings: null",
            "state: available\nversion: 1\nconsumed bindings: null",
        ),
        _replace_once(
            owner,
            "state: available\nversion: 0\nconsumed bindings: null",
            "state: available\nversion: 0\nconsumed bindings: decision_ref",
        ),
    )
    for latch_mutation in latch_mutations:
        with pytest.raises(AssertionError) as latch_rejected:
            _assert_global_latch_scope(latch_mutation)
        assert str(latch_rejected.value).startswith("c2b0.semantic|heading=")

    trigger_mutations = (
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[22],
            insertion="~~~text\n0003: extra trigger = 1\n~~~\n",
        ),
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[23],
            insertion="schema tip 0003: 39 user tables, 2 explicit application indexes, 63 triggers\n",
        ),
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[23],
            insertion="C2B adds exactly twenty-eight tables, forty-seven triggers, and two explicit indexes.\n",
        ),
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[23],
            insertion=TRIGGER_SCHEMA_ROLE_CLAIMS[2] + "\n",
        ),
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[23],
            insertion=TRIGGER_AGGREGATE_ROLE_CLAIMS[0] + "\n",
        ),
    )
    for trigger_mutation in trigger_mutations:
        with pytest.raises(AssertionError) as trigger_rejected:
            _assert_schema_contract(trigger_mutation)
        assert str(trigger_rejected.value).startswith("c2b0.schema|heading=")

    outer_owner = _replace_once(
        owner,
        insertion_marker,
        _outer_nonsemantic_inventory_examples(contradictions[0]) + "\n" + insertion_marker,
    )
    outer_sqlite = _replace_once(
        sqlite,
        insertion_marker,
        _outer_nonsemantic_inventory_examples(contradictions[0]) + "\n" + insertion_marker,
    )
    _assert_migration_failure_and_history_contract(outer_owner)
    _assert_sqlite_migration_summary(outer_sqlite)
    _assert_observation_ingest_authority(
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[13],
            insertion=_outer_nonsemantic_inventory_examples("accepted"),
        )
    )
    _assert_global_latch_scope(
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[22],
            insertion=_outer_nonsemantic_inventory_examples("reuse: allowed"),
        )
    )
    _assert_schema_contract(
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[23],
            insertion=_outer_nonsemantic_inventory_examples("0003: extra trigger = 1"),
        )
    )

    for invalid_suffix in ("not-a-closer", "\u00a0", "\u2003"):
        with pytest.raises(AssertionError) as closer_rejected:
            _markdown_scan(
                f"~~~text\n~~~{invalid_suffix}\n",
                role="c2b0.repair5.matrix",
            )
        assert str(closer_rejected.value) == (
            "c2b0.repair5.matrix|heading=<none>|failure=unbalanced_fence"
        )

    for unclosed in ("```text\n", "~~~text\n"):
        with pytest.raises(AssertionError) as unclosed_rejected:
            _text_blocks(unclosed)
        assert str(unclosed_rejected.value) == (
            "c2b0.text_blocks|block=<none>|failure=unbalanced_fence"
        )


def test_c2b2_field_level_freeze_has_physical_and_pure_value_slices() -> None:
    owner = _owner()
    classification = _compact(_section(owner, SECTION_HEADINGS[27]))
    ledger = _section(owner, SECTION_HEADINGS[28])
    coherence = _compact(_section(owner, SECTION_HEADINGS[29]))
    graph = _compact(_section(owner, SECTION_HEADINGS[30]))
    readers = _compact(_section(owner, SECTION_HEADINGS[31]))
    replay = _compact(_section(owner, SECTION_HEADINGS[32]))
    absent = _compact(_section(owner, SECTION_HEADINGS[33]))

    assert "CURRENT IMPLEMENTED CONTRACT: C2B2 Slice 1 migration administration and physical representation" in classification
    assert "plus Slice 2 pure private row/value source" in classification
    assert "and Slice 3 private reader source" in classification
    assert "ACCEPTED C2B2 FIELD-LEVEL TARGET CONTRACT" in classification
    assert "LATER-TRANCHE TARGET CONTRACT" in classification
    assert "ABSENT: C2B private-reader production caller or public API, C2B mutations, exact replay, recovery, and C2B product runtime caller" in classification
    assert "<!-- C2B2_FIELD_LEVEL_CONTRACT_JSON_BEGIN -->" in ledger
    assert "<!-- C2B2_FIELD_LEVEL_CONTRACT_JSON_END -->" in ledger
    assert "redeliver` and `cancel` do not advance a version" in coherence
    assert "eighteen receipt fields other than `mutation_graph_digest`" in graph
    assert "type(capability) is _SQLiteMutationReadCapability" in readers
    assert "complete mutation-family replay" in replay
    assert "C2B4: migration-0003 row contracts/readers only; not a mutation tranche" in replay
    assert "field-level freeze and contract-reset tranches created documentation and contract tests only" in absent
    assert "Slice 3 implements production-unintegrated private SELECT readers" in absent

    assert (
        ROOT
        / "src/ge_nwp_coordinator/sqlite_migrations/0002_development_program_and_effect_state.sql"
    ).is_file()
    assert not (ROOT / "tests/test_c2b2_field_level_contract.py").is_symlink()


def test_c2b3a_status_is_frozen_without_initialization_or_author_source(
    tmp_path: Path,
) -> None:
    owner = _owner()
    planning = C2B3A_PLANNING_PATH.read_text(encoding="utf-8")
    _assert_c2b3a_owner_addendum_prose(owner)
    _assert_c2b3a_planning_status(planning)
    assert (
        owner[owner.index("## 35. C2B3A Program-Initialization Contract Freeze\n")
              : owner.index("    # C2B3A_OWNER_ADDENDUM_BEGIN")]
        == C2B3A_OWNER_PRE_ADDENDUM_SECTION_35_PREFIX
    )
    assert planning == C2B3A_PLANNING_PROJECTION_APPROVED_TEXT
    for required in (
        '"structured_owner": "commit_close_outcome_addendum"',
        '"planning_is_semantic_authority": False',
        '"planning_may_resolve_or_change_owner_truth": False',
        '"expected_actual_write_paths": 27',
        '"maximum_paths": 28',
        '"active_stop_path_ordinal": 29',
        '"consumers_may_use": False',
    ):
        assert required in owner
    for required in (
        "planning and implementation-status projection only",
        "The unstaged C2B Pre-I/O VS1A",
        "controller-exclusive connection custody and an exact scope-",
        "selects the actual successor, and publishes",
        "retained-custody owner's direct exact-object `close()`",
        "single-owned structural cursors replace\nthe rejected broad",
        "Cleanup claims bind the\nexact `threading.Thread` object with explicit dead-owner takeover",
        "private rollback-only regression\nadaptation to the selected close-proof owner",
        "pre-existing HEAD-exact test-\nresource hygiene, strict warning-promotion debt",
            "exactly twenty-two dirty\npaths",
            "twenty-one tracked modifications",
            "zero staged paths",
            "intentional B3c1a contract\nreplacement",
            "tests/test_b3c1a_writer_session_authority.py",
            "A fresh\nindependent audit remains pending",
            "accepted B4b one-byte zero-Coordinator-\nframe privacy contract replacement",
            "two vulnerable retained-lease public\ncallers",
            "pre-admission correlation creation",
            "private immutable exact-object token exists",
            "never derives correlation from a returned lease or post-return handle",
            "represented incomplete from represented cleanup-owned",
                "Absence proves neither no admission nor\nprior final assignment",
            "bounded cycle-aware sanitizer clears traceback fields",
            "One exact match is followed immediately by direct poison",
            "reads no lifecycle property and calls no project\nor policy helper",
            "direct fork-invalid\nowner-PID sentinel",
            "controller resolution with\n`_CleanupRequiredAfterResolution`",
            "Bound base-class descriptors\nand exact built-in operations",
            "Subclass\ndynamic descriptors, arbitrary subclass slots",
            "One ordinary primary-traversal or call-boundary failure is contained",
            "through each\ngenuine bound public operation guard",
            "`require_usable_for_mutation` use remains an already fail-closed",
            "These scope\ncounts are report-only observations",
            "runtime causal cases, compiled complete-module",
            "one literal tuple of selected node IDs",
            "Source mutants use external\ncopies and leave the live repository unchanged",
            "report\nevidence rather than governing architecture",
            "Section-35 C2B3 initialization recovery/replay remains target-only",
            "Existing transition and global-stop idempotency/\nreplay remain same-wrapper capable",
            "application generation 2 at terminal",
        "initialization command, durable development row, reader, replay, recovery",
        "C2B3B/VS1B remains absent and unauthorized",
        "historical and non-operative",
        "Production is exactly six paths",
        "Documentation/status is exactly ten paths",
        "Required changed tests are exactly eleven paths",
        "Future C2B3B tests use private temporary databases only",
        "They never open\noperator state, migrate operator state, or inspect operator-state contents",
        "an accepted fresh independent read-only source-acceptance audit",
        "a distinct committed Coordinator repository baseline",
        "a refreshed exact Coordinator snapshot, or an explicitly equivalent exact",
        "an accepted independent audit of the committed C2B3A contract baseline",
        "a committed clean Coordinator baseline",
        "a refreshed exact Coordinator snapshot or explicitly equivalent exact",
        "an exact C2B3B source implementation prompt",
        "fresh opening repository and patch provenance",
        "C2B3D cannot begin before the\nC2B3C owner questions are closed",
        "0003 remains reserved and unimplemented",
        "authorizes no production mutation",
    ):
        assert required in planning

    def physical_copy(name: str, value: str) -> str:
        path = tmp_path / (name + ".md")
        assert path.write_text(value, encoding="utf-8") == len(value)
        return path.read_text(encoding="utf-8")

    owner_begin = "    # C2B3A_OWNER_ADDENDUM_BEGIN"
    owner_end = "<!-- C2B3A_OWNER_ADDENDUM_END -->"
    explanatory_begin = "<!-- C2B3A_OWNER_ADDENDUM_EXPLANATORY_BEGIN -->"
    process_begin = "<!-- C2B3A_OWNER_PROCESS_CONTROL_PROSE_BEGIN -->"
    authority_begin = "<!-- C2B3A_OWNER_AUTHORITY_PROSE_BEGIN -->"
    owner_swapped = (
        owner.replace(owner_begin, "__C2B3A_OWNER_BEGIN__", 1)
        .replace(owner_end, owner_begin, 1)
        .replace("__C2B3A_OWNER_BEGIN__", owner_end, 1)
    )
    owner_mutants = (
        (
            "process-after-end",
            owner + "C2B3 preserves the caught traceback tail.\n",
        ),
        (
            "process-before-begin",
            owner.replace(
                owner_begin,
                "The interpreter graph is unchanged.\n" + owner_begin,
                1,
            ),
        ),
        (
            "unmarked-explanatory",
            owner.replace(
                explanatory_begin,
                explanatory_begin
                + "\nThis second explanatory paragraph is unmarked.",
                1,
            ),
        ),
        (
            "old-scope-after-end",
            owner + "The earlier manifest governs C2B3B.\n",
        ),
        (
            "old-scope-unmarked",
            owner.replace(
                explanatory_begin,
                "The implementation is limited to the earlier manifest.\n"
                + explanatory_begin,
                1,
            ),
        ),
        (
            "duplicate-begin",
            owner.replace(owner_begin, owner_begin + "\n" + owner_begin, 1),
        ),
        ("remove-begin", owner.replace(owner_begin, "", 1)),
        (
            "duplicate-end",
            owner.replace(owner_end, owner_end + "\n" + owner_end, 1),
        ),
        ("remove-end", owner.replace(owner_end, "", 1)),
        ("reordered", owner_swapped),
        (
            "nested",
            owner.replace(process_begin, owner_begin + "\n" + process_begin, 1),
        ),
        (
            "unrecognized-block",
            owner.replace(
                authority_begin,
                "<!-- C2B3A_OWNER_UNRECOGNIZED_BEGIN -->\n"
                "One extra path is allowed.\n"
                "<!-- C2B3A_OWNER_UNRECOGNIZED_END -->\n"
                + authority_begin,
                1,
            ),
        ),
    )
    assert len(owner_mutants) == 12
    for mutant_id, owner_mutant in owner_mutants:
        owner_mutant = physical_copy("owner-" + mutant_id, owner_mutant)
        with pytest.raises(AssertionError) as exc_info:
            _assert_c2b3a_owner_addendum_prose(owner_mutant)
        assert str(exc_info.value) == "C2B3A_COMMIT_CLOSE_OWNER_PROSE_INVALID"

    planning_begin = "<!-- C2B3A_PLANNING_PROJECTION_BEGIN -->"
    planning_end = "<!-- C2B3A_PLANNING_PROJECTION_END -->"
    planning_swapped = (
        planning.replace(planning_begin, "__C2B3A_PLANNING_BEGIN__", 1)
        .replace(planning_end, planning_begin, 1)
        .replace("__C2B3A_PLANNING_BEGIN__", planning_end, 1)
    )
    planning_mutants = (
        ("before", "The earlier manifest governs C2B3B.\n" + planning),
        ("after", planning + "One extra path is allowed.\n"),
        ("nonnumeric", planning + "The next path requires reassessment.\n"),
        (
            "old-manifest",
            planning + "The implementation is limited to the earlier manifest.\n",
        ),
        ("numeric-23", planning + "23 expected paths are operative.\n"),
        ("numeric-24", planning + "24 paths are the active maximum.\n"),
        ("numeric-25", planning + "Path 25 may proceed.\n"),
        (
            "duplicate-begin",
            planning.replace(
                planning_begin,
                planning_begin + "\n" + planning_begin,
                1,
            ),
        ),
        ("remove-begin", planning.replace(planning_begin, "", 1)),
        (
            "duplicate-end",
            planning.replace(planning_end, planning_end + "\n" + planning_end, 1),
        ),
        ("remove-end", planning.replace(planning_end, "", 1)),
        ("reordered", planning_swapped),
        (
            "nested",
            planning.replace(
                "<!-- C2B3A_PLANNING_CURRENT_STATUS_BEGIN -->",
                planning_begin
                + "\n<!-- C2B3A_PLANNING_CURRENT_STATUS_BEGIN -->",
                1,
            ),
        ),
        (
            "unrecognized-block",
            planning.replace(
                "<!-- C2B3A_PLANNING_ACTIVE_SCOPE_BEGIN -->",
                "<!-- C2B3A_PLANNING_UNRECOGNIZED_BEGIN -->\n"
                "One extra path is allowed.\n"
                "<!-- C2B3A_PLANNING_UNRECOGNIZED_END -->\n"
                "<!-- C2B3A_PLANNING_ACTIVE_SCOPE_BEGIN -->",
                1,
            ),
        ),
        (
            "private-temp-database-removed",
            planning.replace(
                "Future C2B3B tests use private temporary databases only. ",
                "Future C2B3B tests may use any database. ",
                1,
            ),
        ),
        (
            "operator-state-open-permitted",
            planning.replace("They never open\noperator state", "They may open\noperator state", 1),
        ),
        (
            "operator-state-migration-permitted",
            planning.replace(
                "migrate operator state",
                "may migrate operator state",
                1,
            ),
        ),
        (
            "operator-state-inspection-permitted",
            planning.replace(
                "or inspect operator-state contents",
                "or may inspect operator-state contents",
                1,
            ),
        ),
        (
            "source-acceptance-audit-removed",
            planning.replace(
                "- an accepted fresh independent read-only source-acceptance audit;\n",
                "",
                1,
            ),
        ),
        (
            "source-acceptance-committed-coordinator-baseline-removed",
            planning.replace(
                "- a distinct committed Coordinator repository baseline;\n",
                "",
                1,
            ),
        ),
        (
            "source-acceptance-refreshed-snapshot-removed",
            planning.replace(
                "- a refreshed exact Coordinator snapshot, or an explicitly equivalent exact\n"
                "  strategic baseline, produced after and bound to that committed baseline;\n",
                "",
                1,
            ),
        ),
        (
            "source-acceptance-refreshed-snapshot-not-exact",
            planning.replace(
                "- a refreshed exact Coordinator snapshot, or an explicitly equivalent exact\n",
                "- a refreshed Coordinator snapshot, or an explicitly equivalent strategic\n",
                1,
            ),
        ),
        (
            "source-acceptance-baseline-snapshot-collapsed",
            planning.replace(
                "- a distinct committed Coordinator repository baseline;\n"
                "- a refreshed exact Coordinator snapshot, or an explicitly equivalent exact\n"
                "  strategic baseline, produced after and bound to that committed baseline;\n",
                "- one committed Coordinator snapshot or equivalent strategic baseline;\n",
                1,
            ),
        ),
        (
            "source-acceptance-one-item-serves-both",
            planning.replace(
                "- a distinct committed Coordinator repository baseline;\n"
                "- a refreshed exact Coordinator snapshot, or an explicitly equivalent exact\n"
                "  strategic baseline, produced after and bound to that committed baseline;\n",
                "- one committed Coordinator repository baseline used as both the baseline "
                "and refreshed snapshot;\n",
                1,
            ),
        ),
        (
            "source-start-contract-baseline-not-committed",
            planning.replace(
                "- an accepted independent audit of the committed C2B3A contract baseline;\n",
                "- an accepted independent audit of the C2B3A contract baseline;\n",
                1,
            ),
        ),
        (
            "source-start-coordinator-baseline-unqualified",
            planning.replace(
                "- a committed clean Coordinator baseline;\n",
                "- a Coordinator baseline;\n",
                1,
            ),
        ),
        (
            "source-start-coordinator-baseline-not-clean",
            planning.replace(
                "- a committed clean Coordinator baseline;\n",
                "- a committed Coordinator baseline;\n",
                1,
            ),
        ),
        (
            "source-start-snapshot-not-exact",
            planning.replace(
                "- a refreshed exact Coordinator snapshot or explicitly equivalent exact\n",
                "- a refreshed Coordinator snapshot or explicitly equivalent strategic\n",
                1,
            ),
        ),
        (
            "source-start-snapshot-not-refreshed",
            planning.replace(
                "- a refreshed exact Coordinator snapshot or explicitly equivalent exact\n",
                "- an exact Coordinator snapshot or explicitly equivalent exact\n",
                1,
            ),
        ),
        (
            "source-start-snapshot-replaced-by-baseline",
            planning.replace(
                "- a refreshed exact Coordinator snapshot or explicitly equivalent exact\n"
                "  strategic baseline bound to that clean committed baseline;\n",
                "- the committed clean Coordinator baseline;\n",
                1,
            ),
        ),
        (
            "exact-source-prompt-removed",
            planning.replace(
                "- an exact C2B3B source implementation prompt;\n",
                "",
                1,
            ),
        ),
        (
            "fresh-provenance-removed",
            planning.replace(
                "- fresh opening repository and patch provenance;\n",
                "",
                1,
            ),
        ),
        (
            "c2b3c-skipped",
            planning.replace(
                "C2B3D cannot begin before the\nC2B3C owner questions are closed.",
                "C2B3D may begin directly from C2B3B without C2B3C.",
                1,
            ),
        ),
        (
            "migration-0003-activated",
            planning.replace(
                "Migration\n0003 remains reserved and unimplemented.",
                "Migration\n0003 is active and implemented.",
                1,
            ),
        ),
        (
            "planning-alone-accepts-source",
            planning.replace(
                "Acceptance of this planning projection is not acceptance of future source.",
                "Acceptance of this planning projection accepts future source.",
                1,
            ),
        ),
    )
    assert len(planning_mutants) == 35
    stage_specific_physical_ids = {
        "source-acceptance-committed-coordinator-baseline-removed",
        "source-acceptance-refreshed-snapshot-removed",
        "source-acceptance-refreshed-snapshot-not-exact",
        "source-acceptance-baseline-snapshot-collapsed",
        "source-acceptance-one-item-serves-both",
        "source-start-contract-baseline-not-committed",
        "source-start-coordinator-baseline-unqualified",
        "source-start-coordinator-baseline-not-clean",
        "source-start-snapshot-not-exact",
        "source-start-snapshot-not-refreshed",
        "source-start-snapshot-replaced-by-baseline",
        "exact-source-prompt-removed",
        "fresh-provenance-removed",
    }
    assert len(stage_specific_physical_ids) == 13
    direct_source = _c2b3a_bounded_oracle_source()
    for mutant_id, planning_mutant in planning_mutants:
        assert planning_mutant != planning
        planning_mutant = physical_copy("planning-" + mutant_id, planning_mutant)
        with pytest.raises(AssertionError) as exc_info:
            _assert_c2b3a_planning_status(planning_mutant)
        assert str(exc_info.value) == "C2B3A_PLANNING_PROJECTION_INVALID"
        if mutant_id in stage_specific_physical_ids:
            _c2b3a_physically_reject_planning_counterfactual(
                tmp_path,
                "planning-physical-" + mutant_id,
                direct_source,
                planning_mutant,
            )

    for forbidden_path in (
        ROOT / "src/ge_nwp_coordinator/_development_program_initialization_contracts.py",
        ROOT / "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py",
        ROOT / "tests/test_c2b3_private_atomic_program_initialization.py",
        ROOT / "tests/test_c2b3_program_initialization_recovery.py",
        ROOT / "tests/test_c2b3_private_program_initialization_delegation.py",
    ):
        assert not forbidden_path.exists()


def test_c2b3a_protected_callable_inventory_has_exact_twenty_names() -> None:
    assert C2B3A_ORACLE_PROTECTED_CALLABLE_NAMES == (
        "_assert_future_c2b3b_scope",
        "_assert_oracle_architecture",
        "_assert_original_apply_outcome",
        "_assert_preassigned_binding",
        "_bare_reraise_reference",
        "_candidate",
        "_cleanup_reference",
        "_cleanup_reference_result",
        "_exception_graph_identity_walk",
        "_expect_golden_violation",
        "_expect_violation",
        "_golden_candidate",
        "_named_reraise_reference",
        "_owner_contract",
        "_owner_golden_vector",
        "_read_allowed_text",
        "_relational_process_control_reference",
        "_validate_contract",
        "_validate_golden_vector",
        "_validate_planning_status",
    )
    source = _c2b3a_bounded_oracle_source()
    _assert_c2b3a_protected_factory_policy(source)
    tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    factory_records = tuple(
        record
        for record in _c2b3a_oracle_protected_load_sites(tree, parents)
        if record[0] in {"_candidate", "_golden_candidate"}
    )
    assert sum(record[0] == "_candidate" for record in factory_records) == 177
    assert sum(record[0] == "_golden_candidate" for record in factory_records) == 16


@pytest.mark.parametrize(
    ("mutant_id", "snippet"),
    (
        (
            "F12",
            "\ndef __getattr__(name):\n    if name == 'repair4_candidate_truth':\n        return _candidate()\n    raise AttributeError\n",
        ),
        (
            "F13",
            "\ndef _repair4_golden_wrapper():\n    return _golden_candidate()\n",
        ),
        (
            "F14",
            "\ndef _repair4_candidate_wrapper():\n    return _candidate()\n",
        ),
        (
            "F15",
            "\ndef __getattr__(name):\n    if name == 'repair4_golden_truth':\n        return _golden_candidate()\n    raise AttributeError\n",
        ),
    ),
    ids=("F12", "F13", "F14", "F15"),
)
def test_c2b3a_protected_expected_factories_reject_f12_through_f15_physically(
    mutant_id: str,
    snippet: str,
    tmp_path: Path,
) -> None:
    source = _c2b3a_bounded_oracle_source()
    insertion = "\ndef test_owner_literal_equals_independent_expected_contract"
    assert insertion in source
    mutant = source.replace(insertion, snippet + insertion, 1)
    ast.parse(mutant, filename=mutant_id)
    _c2b3a_physically_import_and_collect_mutant(
        tmp_path,
        mutant_id,
        mutant,
    )
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_protected_factory_policy(mutant)
    assert str(exc_info.value) == "C2B3A_PROTECTED_EXPECTED_FACTORY_ROUTE_INVALID"


def test_c2b3a_process_control_contract_has_independent_literal_truth() -> None:
    source = _c2b3a_bounded_oracle_source()
    candidate = _c2b3a_process_control_candidate(source)
    _assert_c2b3a_process_control_candidate(candidate)


def test_c2b3a_process_control_exception_graph_has_independent_literal_truth() -> None:
    source = _c2b3a_bounded_oracle_source()
    candidate = _c2b3a_process_control_candidate(source)
    _assert_c2b3a_process_control_candidate(candidate)
    gate = candidate["commit_uncertainty_cleanup_gate"]
    ledger = gate["close_not_proved"][
        "process_control_exception_graph_ledger"
    ]
    assert ledger == C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_LEDGER
    assert tuple(tuple(row) for row in ledger) == (
        C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_FIELDS,
        C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_FIELDS,
        C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_FIELDS,
    )
    assert gate["process_control_exception_graph_privacy"] == (
        C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_PRIVACY
    )


def test_c2b3a_process_control_exception_graph_ledger_counterfactuals_fail_closed() -> None:
    source = _c2b3a_bounded_oracle_source()

    candidate = _c2b3a_process_control_candidate(source)
    del candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exception_graph_ledger"
    ][0]["cause_before"]
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID",
    )

    candidate = _c2b3a_process_control_candidate(source)
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exception_graph_ledger"
    ][1]["extra"] = None
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID",
    )

    candidate = _c2b3a_process_control_candidate(source)
    row = candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exception_graph_ledger"
    ][2]
    branch_name = row.pop("branch_name")
    row["branch_name"] = branch_name
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID",
    )

    candidate = _c2b3a_process_control_candidate(source)
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exception_graph_ledger"
    ][0]["branch_name"] = "KeyboardInterruptAlias"
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID",
    )

    candidate = _c2b3a_process_control_candidate(source)
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exception_graph_ledger"
    ][1]["repair_owned_traceback_frame_delta"] = 1
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID",
    )

    candidate = _c2b3a_process_control_candidate(source)
    candidate["commit_uncertainty_cleanup_gate"][
        "process_control_exception_graph_privacy"
    ]["forbidden_surfaces"] = ()
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_PRIVACY_INVALID",
    )


def test_c2b3a_process_control_oracle_controls_are_independently_exact() -> None:
    source = _c2b3a_bounded_oracle_source()
    _assert_c2b3a_process_control_oracle_controls(source)


def test_c2b3a_process_control_counterfactuals_p01_through_p16_fail_closed() -> None:
    source = _c2b3a_bounded_oracle_source()

    candidate = _c2b3a_process_control_candidate(source)
    branches = candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exceptions"
    ]
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exceptions"
    ] = {
        "alpha": branches["KeyboardInterrupt"],
        "beta": branches["SystemExit"],
        "gamma": branches["GeneratorExit"],
    }
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_BRANCH_INVENTORY",
    )

    candidate = _c2b3a_process_control_candidate(source)
    del candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exceptions"
    ]["KeyboardInterrupt"]
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_BRANCH_INVENTORY",
    )

    candidate = _c2b3a_process_control_candidate(source)
    del candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exceptions"
    ]["SystemExit"]
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_BRANCH_INVENTORY",
    )

    candidate = _c2b3a_process_control_candidate(source)
    del candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exceptions"
    ]["GeneratorExit"]
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_BRANCH_INVENTORY",
    )

    candidate = _c2b3a_process_control_candidate(source)
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exceptions"
    ]["FourthProcessControl"] = C2B3A_PROCESS_CONTROL_BRANCH_FACTS[
        "KeyboardInterrupt"
    ]
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_BRANCH_INVENTORY",
    )

    candidate = _c2b3a_process_control_candidate(source)
    steps = list(
        candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
            "process_control_close_interruption_ordered_steps"
        ]
    )
    steps[4], steps[7] = steps[7], steps[4]
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_close_interruption_ordered_steps"
    ] = tuple(steps)
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_PUBLICATION_ORDER",
    )

    candidate = _c2b3a_process_control_candidate(source)
    steps = list(
        candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
            "process_control_close_interruption_ordered_steps"
        ]
    )
    steps[3], steps[7] = steps[7], steps[3]
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_close_interruption_ordered_steps"
    ] = tuple(steps)
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_PUBLICATION_ORDER",
    )

    candidate = _c2b3a_process_control_candidate(source)
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exceptions"
    ]["KeyboardInterrupt"]["mutation_slot_retained_before_propagation"] = False
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_PUBLICATION_ORDER",
    )

    candidate = _c2b3a_process_control_candidate(source)
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exceptions"
    ]["SystemExit"]["writer_lock_retained_before_propagation"] = False
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_PUBLICATION_ORDER",
    )

    candidate = _c2b3a_process_control_candidate(source)
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exceptions"
    ]["KeyboardInterrupt"]["replacement_exception_object"] = True
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_EXCEPTION_IDENTITY",
    )

    candidate = _c2b3a_process_control_candidate(source)
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exceptions"
    ]["SystemExit"]["changed_system_exit_code"] = True
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_EXCEPTION_IDENTITY",
    )

    candidate = _c2b3a_process_control_candidate(source)
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exceptions"
    ]["GeneratorExit"]["changed_exception_args"] = True
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_EXCEPTION_IDENTITY",
    )

    candidate = _c2b3a_process_control_candidate(source)
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exceptions"
    ]["KeyboardInterrupt"]["ordinary_store_error_conversion"] = True
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_PUBLICATION_ORDER",
    )

    for replacement in (
        "commit_outcome_unknown",
        "mutation_failed",
        "unresolved",
    ):
        candidate = _c2b3a_process_control_candidate(source)
        candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
            "process_control_exceptions"
        ]["SystemExit"]["replacement_outcome"] = replacement
        _assert_c2b3a_process_control_failure(
            candidate,
            "C2B3A_PROCESS_CONTROL_PUBLICATION_ORDER",
        )

    candidate = _c2b3a_process_control_candidate(source)
    generator_branch = candidate["commit_uncertainty_cleanup_gate"][
        "close_not_proved"
    ]["process_control_exceptions"]["GeneratorExit"]
    generator_branch["same_session_database_recovery_allowed"] = True
    generator_branch["operation_lease_allowed_before_close_proof"] = True
    generator_branch["database_open_allowed_before_close_proof"] = True
    generator_branch["begin_allowed_before_close_proof"] = True
    generator_branch["sql_allowed_before_close_proof"] = True
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_PUBLICATION_ORDER",
    )

    candidate = _c2b3a_process_control_candidate(source)
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "process_control_exceptions"
    ]["KeyboardInterrupt"]["automatic_semantic_retry"] = True
    _assert_c2b3a_process_control_failure(
        candidate,
        "C2B3A_PROCESS_CONTROL_PUBLICATION_ORDER",
    )


@pytest.mark.parametrize(
    "branch_name",
    ("KeyboardInterrupt", "SystemExit", "GeneratorExit"),
    ids=("KeyboardInterrupt", "SystemExit", "GeneratorExit"),
)
@pytest.mark.parametrize(
    ("mutant_id", "replacement", "diagnostic"),
    (
        (
            "T01",
            "            raise caught_exception\n",
            "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID",
        ),
        (
            "T02",
            "            raise caught_exception from None\n",
            "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID",
        ),
        (
            "T03",
            "            private_cause = RuntimeError('repair4-private-cause')\n            raise caught_exception from private_cause\n",
            "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_PRIVACY_INVALID",
        ),
        (
            "T04",
            "            caught_exception.__context__ = RuntimeError('repair4-private-context')\n            raise\n",
            "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_PRIVACY_INVALID",
        ),
        (
            "T05",
            "            caught_exception.add_note('repair4-private-note')\n            raise\n",
            "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_PRIVACY_INVALID",
        ),
        (
            "T06",
            "            caught_exception.__suppress_context__ = True\n            raise\n",
            "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID",
        ),
        (
            "T07",
            "            raise type(caught_exception)(*caught_exception.args)\n",
            "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID",
        ),
        (
            "T08",
            "            return _repair4_named_reraise_helper(caught_exception)\n",
            "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_INVALID",
        ),
        (
            "T09",
            "            repair4_private_commit_material = 'repair4-private-commit-material'\n            raise caught_exception\n",
            "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_PRIVACY_INVALID",
        ),
        (
            "T10",
            "            caught_exception.add_note('repair4-private-cleanup-material')\n            raise\n",
            "C2B3A_PROCESS_CONTROL_EXCEPTION_GRAPH_PRIVACY_INVALID",
        ),
    ),
    ids=("T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10"),
)
def test_c2b3a_process_control_exception_mutants_t01_through_t10_are_physical(
    branch_name: str,
    mutant_id: str,
    replacement: str,
    diagnostic: str,
    tmp_path: Path,
) -> None:
    source = _c2b3a_bounded_oracle_source()
    mutant = _c2b3a_process_control_oracle_mutant(
        source,
        branch_name,
        replacement,
    )
    ast.parse(mutant, filename=f"{mutant_id}-{branch_name}")
    _c2b3a_physically_import_and_collect_mutant(
        tmp_path,
        f"{mutant_id}-{branch_name}",
        mutant,
    )
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_process_control_oracle_controls(mutant)
    assert str(exc_info.value) == diagnostic


@pytest.mark.parametrize(
    ("mutant_id", "snippet"),
    (
        (
            "A01",
            "\ndef _a01():\n    import hashlib\n    return hashlib\n",
        ),
        (
            "A02",
            "\ndef _a02():\n    import sqlite3\n    return sqlite3\n",
        ),
        (
            "A03",
            "\ndef _a03():\n    import importlib\n    return importlib\n",
        ),
        (
            "A04",
            "\ndef _a04():\n    dynamic = eval\n    return dynamic('0')\n",
        ),
        (
            "A05",
            "\ndef _a05():\n    return builtins.eval('0')\n",
        ),
        (
            "A06",
            "\ndef _a06():\n    dynamic = __import__\n    return dynamic('ast')\n",
        ),
        (
            "A07",
            "\ndef _a07(importlib):\n    loader = importlib.import_module\n    return loader('ast')\n",
        ),
        (
            "A08",
            "\ndef _a08():\n    reader = Path.read_text\n    return reader(Path(__file__))\n",
        ),
        (
            "A09",
            "\ndef _a09():\n    return Path('/alternate').read_text(encoding='utf-8')\n",
        ),
        (
            "A10",
            "\ndef _a10():\n    return Path('/alternate').read_bytes()\n",
        ),
        (
            "A11",
            "\nEXPECTED_INITIALIZATION_CONTRACT = {}\n",
        ),
        (
            "A12",
            "\nEXPECTED_INITIALIZATION_GOLDEN_VECTOR = {}\n",
        ),
        (
            "A13",
            "\ndef _a13():\n    EXPECTED_INITIALIZATION_CONTRACT = {}\n    return EXPECTED_INITIALIZATION_CONTRACT\n",
        ),
        (
            "A14",
            "\ndef _a14(value=EXPECTED_INITIALIZATION_CONTRACT):\n    return value\n",
        ),
        (
            "A15",
            "\ndef _a15():\n    value = EXPECTED_INITIALIZATION_CONTRACT\n    def replace():\n        nonlocal value\n        value = {}\n    return replace\n",
        ),
        (
            "A16",
            "\nEXPECTED_INITIALIZATION_CONTRACT = _owner_contract()\n",
        ),
        (
            "A17",
            "\ndef _production_contract():\n    source = Path('src/ge_nwp_coordinator/sqlite_writer_session.py').read_text(encoding='utf-8')\n    return ast.literal_eval(source)\nEXPECTED_INITIALIZATION_CONTRACT = _production_contract()\n",
        ),
        (
            "A18",
            "\nEXPECTED_INITIALIZATION_GOLDEN_VECTOR = ast.literal_eval(Path('/tmp/generated-vector.py').read_text(encoding='utf-8'))\n",
        ),
        (
            "A19",
            "\ndef _a19():\n    import hashlib\n    source = _read_allowed_text(TEST_PATH)\n    return hashlib.sha256(source.encode('utf-8')).hexdigest() == '0' * 64\n",
        ),
        (
            "A20",
            "\nVALIDATOR_REGISTRY = {}\nVALIDATOR_REGISTRY.update({'contract': _validate_contract})\n",
        ),
        (
            "A21",
            "\nCALLABLES = dict(contract=_validate_contract)\n",
        ),
        (
            "A22",
            "\nCALLABLES = {'contract': _validate_contract}\nCALLABLES['contract']({})\n",
        ),
        (
            "A23",
            "\nCALLABLES = (_validate_contract,)\nfor callback in CALLABLES:\n    callback({})\n",
        ),
        (
            "A24",
            "\nCALLABLE_RESULTS = tuple(callback({}) for callback in (_validate_contract,))\n",
        ),
        (
            "A25",
            "\nclass CallableHolder:\n    registry = {'contract': _validate_contract}\ndef _a25():\n    return CallableHolder.registry['contract']({})\n",
        ),
        (
            "A26",
            "\ndef _a26(callback):\n    return callback.__call__({})\n",
        ),
        (
            "A27",
            "\ndef _a27(callback=_validate_contract):\n    return callback({})\n",
        ),
        (
            "A28",
            "\ndef _owner_conversion_decorator(function):\n    _owner_contract()\n    return function\n@_owner_conversion_decorator\ndef _a28():\n    return None\n",
        ),
        (
            "A29",
            "\ndef _a29(callback: _validate_contract):\n    return callback({})\n",
        ),
        (
            "A30",
            "\ndef _generic_validator_runner(validator, value):\n    return validator(value)\n",
        ),
    ),
    ids=(
        "A01",
        "A02",
        "A03",
        "A04",
        "A05",
        "A06",
        "A07",
        "A08",
        "A09",
        "A10",
        "A11",
        "A12",
        "A13",
        "A14",
        "A15",
        "A16",
        "A17",
        "A18",
        "A19",
        "A20",
        "A21",
        "A22",
        "A23",
        "A24",
        "A25",
        "A26",
        "A27",
        "A28",
        "A29",
        "A30",
    ),
)
def test_c2b3a_independent_oracle_architecture_rejects_a01_through_a30(
    mutant_id: str,
    snippet: str,
) -> None:
    source = _c2b3a_bounded_oracle_source()
    insertion = "\ndef test_owner_literal_equals_independent_expected_contract"
    assert insertion in source
    mutant = source.replace(insertion, snippet + insertion, 1)
    ast.parse(mutant, filename=mutant_id)
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_independent_oracle_architecture(mutant)
    expected_diagnostic = (
        "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
        if mutant_id in {"A11", "A16", "A17", "A18", "A22", "A23", "A24"}
        else "C2B3A_INDEPENDENT_ORACLE_ARCHITECTURE_INVALID"
    )
    assert str(exc_info.value) == expected_diagnostic


def test_c2b3a_positive_execution_counts_and_order_are_exact() -> None:
    source = _c2b3a_bounded_oracle_source()
    tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    _assert_c2b3a_positive_body_semantics(tree)


def test_c2b3a_efficacy_guard_assurance_boundary_is_direct_independent_and_exact(
) -> None:
    source = Path(__file__).resolve().read_text(encoding="utf-8")
    tree = ast.parse(source, filename=Path(__file__).name, type_comments=True)
    assignments = tuple(
        statement
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id
        == "C2B3A_EFFICACY_GUARD_ASSURANCE_BOUNDARY"
    )
    assert len(assignments) == 1
    assignment = assignments[0]
    assert isinstance(assignment.value, ast.Dict)
    assert _c2b3a_oracle_closed_literal(assignment.value)
    observed = ast.literal_eval(assignment.value)
    assert type(observed) is dict
    assert observed == C2B3A_EFFICACY_GUARD_ASSURANCE_BOUNDARY
    assert tuple(observed) == (
        "classification",
        "in_scope_guarantees",
        "explicit_non_claims",
        "external_assurance_chain",
        "external_assurance_role",
    )
    assert observed["classification"] == "bounded exact-byte self-test assurance"
    assert observed["in_scope_guarantees"] == (
        "the exact checked-in efficacy function header and body match the independently authored bounded AST/dataflow grammar",
        "the exact checked-in function has no local or lexical binding of exec",
        "the exact checked-in module has no ordinary lexical module binding of exec that changes the efficacy function resolution",
        "the exact checked-in source contains no directly recognized source-local module-dictionary replacement of exec",
        "the exact checked-in source contains no wildcard import capable of supplying exec",
        "the efficacy function in-function namespace, immediate validator capture, baseline validation, terminal validation, one-mutant invocation, restoration, and aggregate behavior retain their existing exact protections",
        "runtime instrumentation on the exact audited bytes observes builtins.exec as the callable used by the checked execution path",
        "runtime instrumentation observes 100 calls to the exec-produced validator and zero calls to an alternate validator",
    )
    assert observed["explicit_non_claims"] == (
        "resistance to malicious coordinated editing of both the efficacy checker and its higher-order guard",
        "resistance to mutation of builtins.exec or the builtins object",
        "resistance to mutation through __builtins__",
        "resistance to a pre-poisoned or malicious sys.modules environment",
        "resistance to mutation of imported module objects",
        "resistance to custom import hooks or loaders",
        "resistance to tracing, profiling, debugger, coverage, or interpreter instrumentation that changes execution",
        "resistance to hostile monkeypatching performed outside the bounded source-local forms",
        "resistance to arbitrary Python metaprogramming",
        "resistance to process or interpreter compromise",
    )
    assert observed["external_assurance_chain"] == (
        "exact patch provenance",
        "fresh independent read-only audit",
        "staged-blob equality",
        "committed-blob equality",
        "Git object and ref truth",
    )
    assert observed["external_assurance_role"] == (
        "provenance and audit are external assurance mechanisms, not semantics "
        "owned by this test"
    )
    assert _c2b3a_oracle_direct_hostile_environment_operations(tree) == ()
    assert _c2b3a_oracle_module_name_bindings(tree, "exec") == ()
    assert _c2b3a_oracle_module_wildcard_imports(tree) == ()
    assert _c2b3a_oracle_direct_module_dictionary_operations(tree) == ()

    exact = '"classification": "bounded exact-byte self-test assurance"'
    assert source.count(exact) == 3
    mutant = source.replace(
        exact,
        '"classification": "hostile-source and interpreter verifier"',
        1,
    )
    compile(mutant, Path(__file__).name, "exec")
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_mutant_efficacy_checker_structure(mutant)
    assert exc_info.value.args == (
        "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID",
    )


def test_c2b3a_m16_m65_executable_efficacy_is_exact() -> None:
    higher_order_source = Path(__file__).resolve().read_text(encoding="utf-8")
    _assert_c2b3a_mutant_efficacy_checker_structure(higher_order_source)
    source = _c2b3a_bounded_oracle_source()
    tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    _assert_c2b3a_mutant_dataflow_semantics(tree)


def test_c2b3a_exact_bytes_runtime_observes_builtins_exec() -> None:
    higher_order_source = Path(__file__).resolve().read_text(encoding="utf-8")
    _assert_c2b3a_mutant_efficacy_checker_structure(higher_order_source)
    source = _c2b3a_bounded_oracle_source()
    tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    observed: list[object] = []

    def observe_builtin_calls(
        frame: object,
        event: str,
        argument: object,
    ) -> None:
        if (
            event == "c_call"
            and argument is builtins.exec
            and frame.f_code
            is _assert_c2b3a_mutant_dataflow_semantics.__code__
        ):
            observed.append(argument)

    assert "exec" not in globals()
    assert exec is builtins.exec
    prior_profile = sys.getprofile()
    sys.setprofile(observe_builtin_calls)
    try:
        _assert_c2b3a_mutant_dataflow_semantics(tree)
    finally:
        sys.setprofile(prior_profile)
    assert observed == [builtins.exec]


def test_c2b3a_mutant_efficacy_checker_physical_counterfactuals_are_rejected(
    tmp_path: Path,
) -> None:
    source = Path(__file__).resolve().read_text(encoding="utf-8")
    loop_header = (
        "    for mutant_id, function_name in C2B3A_LINEAR_MUTANT_FUNCTIONS:\n"
    )
    produced_diagnostic_dead_branch = _c2b3a_semantic_replace_in_function(
        source,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "            if execution[\"validator_diagnostic\"] != expected_diagnostic:\n"
        "                raise AssertionError(diagnostic)\n",
        "            if False:\n"
        "                if execution[\"validator_diagnostic\"] != expected_diagnostic:\n"
        "                    raise AssertionError(diagnostic)\n",
    )
    produced_diagnostic_dead_branch = _c2b3a_semantic_replace_in_function(
        produced_diagnostic_dead_branch,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "            or execution[\"validator_diagnostic\"] != expected_diagnostic\n",
        "            or False\n",
    )
    terminal_one_or_two = _c2b3a_semantic_replace_in_function(
        source,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "            if execution[\"terminal_calls\"] != 1:\n",
        "            if execution[\"terminal_calls\"] not in {1, 2}:\n",
    )
    terminal_one_or_two = _c2b3a_semantic_replace_in_function(
        terminal_one_or_two,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "            or execution[\"terminal_calls\"] != 1\n",
        "            or execution[\"terminal_calls\"] not in {1, 2}\n",
    )
    terminal_at_most_two = _c2b3a_semantic_replace_in_function(
        source,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "            if execution[\"terminal_calls\"] != 1:\n",
        "            if execution[\"terminal_calls\"] > 2:\n",
    )
    terminal_at_most_two = _c2b3a_semantic_replace_in_function(
        terminal_at_most_two,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "            or execution[\"terminal_calls\"] != 1\n",
        "            or execution[\"terminal_calls\"] > 2\n",
    )
    m16_after_restoration = _c2b3a_semantic_replace_in_function(
        source,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "            namespace[\"_expect_violation\"] = original_expect_violation\n\n"
        "        if (\n",
        "            namespace[\"_expect_violation\"] = original_expect_violation\n\n"
        "        if mutant_id == \"M16\":\n"
        "            mutant_function()\n\n"
        "        if (\n",
    )
    mapped_twice = _c2b3a_semantic_replace_in_function(
        source,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "            mutant_function()\n",
        "            mutant_function()\n"
        "            mutant_function()\n",
    )
    mapped_before_instrumentation = _c2b3a_semantic_replace_in_function(
        source,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "        namespace[\"_candidate\"] = instrumented_candidate\n",
        "        mutant_function()\n"
        "        namespace[\"_candidate\"] = instrumented_candidate\n",
    )
    supplied_diagnostic_self_comparison = _c2b3a_semantic_replace_in_function(
        source,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "            if execution[\"validator_diagnostic\"] != expected_diagnostic:\n",
        "            if execution[\"supplied_diagnostic\"] != "
        "execution[\"supplied_diagnostic\"]:\n",
    )
    supplied_diagnostic_self_comparison = _c2b3a_semantic_replace_in_function(
        supplied_diagnostic_self_comparison,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "            or execution[\"validator_diagnostic\"] != expected_diagnostic\n",
        "            or False\n",
    )
    restoration_outside_finally = _c2b3a_semantic_replace_in_function(
        source,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "        finally:\n"
        "            namespace[\"_candidate\"] = original_candidate\n"
        "            namespace[\"_expect_violation\"] = original_expect_violation\n",
        "        finally:\n"
        "            pass\n"
        "        namespace[\"_candidate\"] = original_candidate\n"
        "        namespace[\"_expect_violation\"] = original_expect_violation\n",
    )
    invocation_after_loop = _c2b3a_semantic_replace_in_function(
        source,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "    if tuple(signatures) != expected_m16_m65_ids:\n",
        "    mutant_function()\n\n"
        "    if tuple(signatures) != expected_m16_m65_ids:\n",
    )
    forged_fifty_after_forty_nine = _c2b3a_semantic_replace_in_function(
        source,
        "_assert_c2b3a_mutant_dataflow_semantics",
        loop_header,
        "    for mutant_id, function_name in "
        "C2B3A_LINEAR_MUTANT_FUNCTIONS[:49]:\n",
    )
    forged_fifty_after_forty_nine = _c2b3a_semantic_replace_in_function(
        forged_fifty_after_forty_nine,
        "_assert_c2b3a_mutant_dataflow_semantics",
        "    if tuple(signatures) != expected_m16_m65_ids:\n",
        "    execution_totals[\"mutant_invocations\"] = 50\n\n"
        "    if tuple(signatures) != expected_m16_m65_ids:\n",
    )
    counterfactuals = (
        ("checker-loop-pass", _c2b3a_efficacy_loop_pass_mutant(source)),
        (
            "checker-mutant-invocation-removed",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                "            mutant_function()\n",
                "            pass\n",
            ),
        ),
        (
            "checker-candidate-factory-not-installed",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                '        namespace["_candidate"] = instrumented_candidate\n',
                "        pass\n",
            ),
        ),
        (
            "checker-terminal-interceptor-not-installed",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                '        namespace["_expect_violation"] = instrumented_expect_violation\n',
                "        pass\n",
            ),
        ),
        (
            "checker-reached-forged",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                "            mutant_function()\n",
                '            execution["reached"] = True\n',
            ),
        ),
        (
            "checker-baseline-validation-omitted",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                "            original_validate(controlled_candidate)\n",
                "            pass\n",
            ),
        ),
        (
            "checker-candidate-change-omitted",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                "        if controlled_candidate == valid_baseline:\n"
                "            raise AssertionError(diagnostic)\n",
                "        if False:\n"
                "            raise AssertionError(diagnostic)\n",
            ),
        ),
        (
            "checker-identical-object-omitted",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                "            if candidate is not controlled_candidate:\n"
                "                raise AssertionError(diagnostic)\n",
                "            if False:\n"
                "                raise AssertionError(diagnostic)\n",
            ),
        ),
        (
            "checker-exact-diagnostic-omitted",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                "            if supplied_diagnostic != expected_diagnostic:\n"
                "                raise AssertionError(diagnostic)\n",
                "            if False:\n"
                "                raise AssertionError(diagnostic)\n",
            ),
        ),
        (
            "checker-fresh-candidate-validated",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                "                original_validate(candidate)\n",
                "                original_validate(original_candidate())\n",
            ),
        ),
        (
            "checker-produced-diagnostic-dead-branch",
            produced_diagnostic_dead_branch,
        ),
        ("checker-terminal-one-or-two", terminal_one_or_two),
        ("checker-terminal-at-most-two", terminal_at_most_two),
        ("checker-m16-after-restoration", m16_after_restoration),
        ("checker-mapped-mutant-twice", mapped_twice),
        ("checker-mapped-before-instrumentation", mapped_before_instrumentation),
        (
            "checker-real-validator-call-removed",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                "                original_validate(candidate)\n",
                "                pass\n",
            ),
        ),
        (
            "checker-supplied-diagnostic-self-comparison",
            supplied_diagnostic_self_comparison,
        ),
        (
            "checker-candidate-factory-not-restored",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                "            namespace[\"_candidate\"] = original_candidate\n",
                "            pass\n",
            ),
        ),
        (
            "checker-terminal-helper-not-restored",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                "            namespace[\"_expect_violation\"] = original_expect_violation\n",
                "            pass\n",
            ),
        ),
        ("checker-restoration-outside-finally", restoration_outside_finally),
        (
            "checker-only-forty-nine",
            _c2b3a_efficacy_loop_iter_mutant(
                source,
                "C2B3A_LINEAR_MUTANT_FUNCTIONS[:49]",
            ),
        ),
        (
            "checker-skip-m16",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                loop_header,
                loop_header
                + '        if mutant_id == "M16":\n'
                + "            continue\n",
            ),
        ),
        (
            "checker-skip-m65",
            _c2b3a_efficacy_loop_iter_mutant(
                source,
                "C2B3A_LINEAR_MUTANT_FUNCTIONS[:-1]",
            ),
        ),
        ("checker-invocation-after-loop", invocation_after_loop),
        ("checker-forged-fifty-after-forty-nine", forged_fifty_after_forty_nine),
        (
            "checker-terminal-count-without-interceptor",
            _c2b3a_semantic_replace_in_function(
                source,
                "_assert_c2b3a_mutant_dataflow_semantics",
                "            mutant_function()\n",
                "            execution[\"terminal_calls\"] += 1\n",
            ),
        ),
    )
    assert len(counterfactuals) == 27
    for mutant_id, mutant in counterfactuals:
        physical_source = _c2b3a_physically_import_and_collect_checker(
            tmp_path,
            mutant_id,
            mutant,
        )
        try:
            _assert_c2b3a_mutant_efficacy_checker_structure(physical_source)
        except AssertionError as exc:
            assert str(exc) == (
                "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
            )
        else:
            raise AssertionError(
                "C2B3A_EFFICACY_CHECKER_COUNTERFACTUAL_ACCEPTED:" + mutant_id
            )


def test_c2b3a_exec_produced_validator_provenance_counterfactuals_are_rejected(
    tmp_path: Path,
) -> None:
    source = Path(__file__).resolve().read_text(encoding="utf-8")
    function_name = "_assert_c2b3a_mutant_dataflow_semantics"
    exec_capture_tail = (
        "        )\n"
        "        original_validate = namespace[\"_validate_contract\"]\n"
    )
    handler_tail = (
        "    except BaseException:\n"
        "        raise AssertionError(diagnostic) from None\n"
        "    original_candidate = namespace.get(\"_candidate\")\n"
    )
    alternating_definition = (
        "        forged_validator_calls = 0\n\n"
        "        def synthetic_validate(candidate: object) -> None:\n"
        "            nonlocal forged_validator_calls\n"
        "            forged_validator_calls += 1\n"
        "            if forged_validator_calls % 2:\n"
        "                return\n"
        "            raise namespace[\"_ContractViolation\"](\n"
        "                \"C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID\"\n"
        "            )\n\n"
    )
    alternating_validator = _c2b3a_semantic_replace_in_function(
        source,
        function_name,
        exec_capture_tail,
        "        )\n"
        + alternating_definition
        + "        namespace[\"_validate_contract\"] = synthetic_validate\n"
        + "        original_validate = namespace[\"_validate_contract\"]\n",
    )
    namespace_update = _c2b3a_semantic_replace_in_function(
        source,
        function_name,
        exec_capture_tail,
        "        )\n"
        "        namespace.update(\n"
        "            {\"_validate_contract\": lambda candidate: None}\n"
        "        )\n"
        "        original_validate = namespace[\"_validate_contract\"]\n",
    )
    namespace_setitem = _c2b3a_semantic_replace_in_function(
        source,
        function_name,
        exec_capture_tail,
        "        )\n"
        "        namespace.__setitem__(\n"
        "            \"_validate_contract\", lambda candidate: None\n"
        "        )\n"
        "        original_validate = namespace[\"_validate_contract\"]\n",
    )
    namespace_alias_mutation = _c2b3a_semantic_replace_in_function(
        source,
        function_name,
        exec_capture_tail,
        "        )\n"
        "        namespace_alias = namespace\n"
        "        namespace_alias[\"_validate_contract\"] = lambda candidate: None\n"
        "        original_validate = namespace[\"_validate_contract\"]\n",
    )
    second_exec = _c2b3a_semantic_replace_in_function(
        source,
        function_name,
        exec_capture_tail,
        "        )\n"
        "        exec(\n"
        "            \"_validate_contract = lambda candidate: None\", namespace\n"
        "        )\n"
        "        original_validate = namespace[\"_validate_contract\"]\n",
    )
    get_capture = _c2b3a_semantic_replace_in_function(
        source,
        function_name,
        "        original_validate = namespace[\"_validate_contract\"]\n",
        "        original_validate = namespace.get(\"_validate_contract\")\n",
    )
    alias_capture = _c2b3a_semantic_replace_in_function(
        source,
        function_name,
        "        original_validate = namespace[\"_validate_contract\"]\n",
        "        namespace_alias = namespace\n"
        "        original_validate = namespace_alias[\"_validate_contract\"]\n",
    )
    validator_rebind = _c2b3a_semantic_replace_in_function(
        source,
        function_name,
        handler_tail,
        "    except BaseException:\n"
        "        raise AssertionError(diagnostic) from None\n"
        "    original_validate = lambda candidate: None\n"
        "    original_candidate = namespace.get(\"_candidate\")\n",
    )
    validator_recapture = _c2b3a_semantic_replace_in_function(
        source,
        function_name,
        "        original_validate = namespace[\"_validate_contract\"]\n",
        "        original_validate = namespace[\"_validate_contract\"]\n"
        "        namespace[\"_validate_contract\"] = lambda candidate: None\n"
        "        original_validate = namespace[\"_validate_contract\"]\n",
    )
    conditional_capture = _c2b3a_semantic_replace_in_function(
        source,
        function_name,
        "        original_validate = namespace[\"_validate_contract\"]\n",
        "        original_validate = (\n"
        "            namespace[\"_validate_contract\"]\n"
        "            if False\n"
        "            else (lambda candidate: None)\n"
        "        )\n",
    )

    dead_branch_synthetic = _c2b3a_semantic_replace_in_function(
        source,
        function_name,
        handler_tail,
        "    except BaseException:\n"
        "        raise AssertionError(diagnostic) from None\n"
        "    synthetic_validator_calls = 0\n\n"
        "    def synthetic_validate(candidate: object) -> None:\n"
        "        nonlocal synthetic_validator_calls\n"
        "        synthetic_validator_calls += 1\n"
        "        if synthetic_validator_calls % 2:\n"
        "            return\n"
        "        raise namespace[\"_ContractViolation\"](\n"
        "            \"C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID\"\n"
        "        )\n\n"
        "    original_candidate = namespace.get(\"_candidate\")\n",
    )
    dead_branch_synthetic = _c2b3a_semantic_replace_in_function(
        dead_branch_synthetic,
        function_name,
        "            original_validate(controlled_candidate)\n",
        "            if False:\n"
        "                original_validate(controlled_candidate)\n"
        "            synthetic_validate(controlled_candidate)\n",
    )
    dead_branch_synthetic = _c2b3a_semantic_replace_in_function(
        dead_branch_synthetic,
        function_name,
        "            with pytest.raises(contract_violation) as exc_info:\n"
        "                original_validate(candidate)\n"
        "            execution[\"validator_diagnostic\"] = str(exc_info.value)\n"
        "            if execution[\"validator_diagnostic\"] != expected_diagnostic:\n"
        "                raise AssertionError(diagnostic)\n",
        "            if False:\n"
        "                with pytest.raises(contract_violation) as dead_exc_info:\n"
        "                    original_validate(candidate)\n"
        "                execution[\"validator_diagnostic\"] = str(\n"
        "                    dead_exc_info.value\n"
        "                )\n"
        "                if (\n"
        "                    execution[\"validator_diagnostic\"]\n"
        "                    != expected_diagnostic\n"
        "                ):\n"
        "                    raise AssertionError(diagnostic)\n"
        "            with pytest.raises(contract_violation) as exc_info:\n"
        "                synthetic_validate(candidate)\n"
        "            execution[\"validator_diagnostic\"] = str(exc_info.value)\n"
        "            if execution[\"validator_diagnostic\"] != expected_diagnostic:\n"
        "                raise AssertionError(diagnostic)\n",
    )

    counterfactuals = (
        ("checker-rd1-alternating-validator", alternating_validator),
        ("checker-rd1-namespace-update", namespace_update),
        ("checker-rd1-namespace-setitem", namespace_setitem),
        ("checker-rd1-namespace-alias-mutation", namespace_alias_mutation),
        ("checker-rd1-second-exec", second_exec),
        ("checker-rd1-get-capture", get_capture),
        ("checker-rd1-alias-capture", alias_capture),
        ("checker-rd1-validator-rebind", validator_rebind),
        ("checker-rd1-validator-recapture", validator_recapture),
        ("checker-rd1-conditional-capture", conditional_capture),
        ("checker-rd1-dead-branch-synthetic", dead_branch_synthetic),
    )
    assert len(counterfactuals) == 11
    for mutant_id, mutant in counterfactuals:
        physical_source = _c2b3a_physically_import_and_collect_checker(
            tmp_path,
            mutant_id,
            mutant,
        )
        try:
            _assert_c2b3a_mutant_efficacy_checker_structure(physical_source)
        except AssertionError as exc:
            assert str(exc) == (
                "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
            )
        else:
            raise AssertionError(
                "C2B3A_RD1_VALIDATOR_PROVENANCE_COUNTERFACTUAL_ACCEPTED:"
                + mutant_id
            )

    selected_test_name = "test_c2b3a_m16_m65_executable_efficacy_is_exact"
    alternating_runtime = _c2b3a_semantic_replace_in_function(
        alternating_validator,
        selected_test_name,
        "    _assert_c2b3a_mutant_efficacy_checker_structure(higher_order_source)\n",
        "    assert higher_order_source\n",
    )
    runtime_id = "checker-rd1-alternating-validator-runtime-proof"
    _c2b3a_physically_import_and_collect_checker(
        tmp_path,
        runtime_id,
        alternating_runtime,
    )
    runtime_root = tmp_path / runtime_id
    for relative_path in (
        Path(".docs/c2b-durable-development-state.md"),
        Path(".docs/c2b3-program-initialization.md"),
        Path("tests/test_c2b3_program_initialization_contract.py"),
    ):
        source_path = ROOT / relative_path
        destination = runtime_root / relative_path
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        source_bytes = source_path.read_bytes()
        assert destination.write_bytes(source_bytes) == len(source_bytes)

    runtime_test_path = runtime_root / "tests" / Path(__file__).name
    execute_tmp = runtime_root / "execute-tmp"
    execute_pycache = runtime_root / "execute-pycache"
    execute_basetemp = runtime_root / "execute-basetemp"
    for directory in (execute_tmp, execute_pycache):
        directory.mkdir(mode=0o700)
    executed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            f"--basetemp={execute_basetemp}",
            "-q",
            str(runtime_test_path) + "::" + selected_test_name,
        ),
        cwd=ROOT,
        env={
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONPYCACHEPREFIX": str(execute_pycache),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "TMPDIR": str(execute_tmp),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert executed.returncode == 0, executed.stderr
    assert "1 passed" in executed.stdout
    assert " warning" not in executed.stdout.lower()
    assert executed.stderr == ""


def test_c2b3a_closed_efficacy_checker_grammar_counterfactuals_are_rejected(
    tmp_path: Path,
) -> None:
    source = Path(__file__).resolve().read_text(encoding="utf-8")
    function_name = "_assert_c2b3a_mutant_dataflow_semantics"
    callability_tail = (
        "    ):\n"
        "        raise AssertionError(diagnostic)\n\n"
        "    execution_totals: dict[str, int] = {\n"
    )

    def insert_after_callability(insertion: str) -> str:
        return _c2b3a_semantic_replace_in_function(
            source,
            function_name,
            callability_tail,
            "    ):\n"
            "        raise AssertionError(diagnostic)\n\n"
            + insertion
            + "\n    execution_totals: dict[str, int] = {\n",
        )

    def add_callability_else(body: str) -> str:
        return _c2b3a_semantic_replace_in_function(
            source,
            function_name,
            callability_tail,
            "    ):\n"
            "        raise AssertionError(diagnostic)\n"
            "    else:\n"
            + body
            + "\n\n    execution_totals: dict[str, int] = {\n",
        )

    combined_audit_bypass = add_callability_else(
        "        synthetic_validator_calls = 0\n\n"
        "        def synthetic_validate(candidate: object) -> None:\n"
        "            nonlocal synthetic_validator_calls\n"
        "            synthetic_validator_calls += 1\n"
        "            if synthetic_validator_calls % 2:\n"
        "                return\n"
        "            raise contract_violation(\n"
        "                \"C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID\"\n"
        "            )\n\n"
        "        match synthetic_validate:\n"
        "            case original_validate:\n"
        "                pass\n"
        "        namespace[\"_validate_\" + \"contract\"] = original_validate"
    )
    match_as_rebind = insert_after_callability(
        "    match original_validate:\n"
        "        case original_validate:\n"
        "            pass\n"
    )
    nested_sequence_star = insert_after_callability(
        "    match [None, [original_validate]]:\n"
        "        case [_, [*original_validate]]:\n"
        "            pass\n"
    )
    mapping_rest_alias = insert_after_callability(
        "    match namespace:\n"
        "        case {\"_validate_contract\": _, **namespace}:\n"
        "            pass\n"
    )
    concatenated_validator_store = insert_after_callability(
        "    namespace[\"_validate_\" + \"contract\"] = original_validate\n"
    )
    formatted_validator_store = insert_after_callability(
        "    namespace[f\"{'_validate_'}contract\"] = original_validate\n"
    )
    called_validator_store = insert_after_callability(
        "    namespace[\"\".join((\"_validate_\", \"contract\"))] = "
        "original_validate\n"
    )
    empty_else = add_callability_else("        pass")
    synthetic_else = add_callability_else(
        "        def synthetic_validate(candidate: object) -> None:\n"
        "            return None"
    )
    nonliteral_allowed_key_store = insert_after_callability(
        "    namespace[\"_\" + \"candidate\"] = original_candidate\n"
    )
    extra_dynamic_load = insert_after_callability(
        "    assert namespace[\"_\" + \"candidate\"] is original_candidate\n"
    )
    nested_function_pattern = _c2b3a_semantic_replace_in_function(
        source,
        function_name,
        "        def instrumented_candidate() -> object:\n"
        "            execution[\"candidate_factory_calls\"] = (\n",
        "        def instrumented_candidate() -> object:\n"
        "            match None:\n"
        "                case original_validate:\n"
        "                    pass\n"
        "            execution[\"candidate_factory_calls\"] = (\n",
    )
    alternate_combined = insert_after_callability(
        "    match (original_validate,):\n"
        "        case [original_validate]:\n"
        "            pass\n"
        "    namespace[f\"{'_validate'}{'_contract'}\"] = original_validate\n"
    )

    counterfactuals = (
        ("checker-rd1-closed-combined-audit-bypass", combined_audit_bypass),
        ("checker-rd1-closed-match-as", match_as_rebind),
        ("checker-rd1-closed-nested-sequence-star", nested_sequence_star),
        ("checker-rd1-closed-mapping-rest-alias", mapping_rest_alias),
        (
            "checker-rd1-closed-concatenated-validator-store",
            concatenated_validator_store,
        ),
        ("checker-rd1-closed-formatted-validator-store", formatted_validator_store),
        ("checker-rd1-closed-called-validator-store", called_validator_store),
        ("checker-rd1-closed-empty-else", empty_else),
        ("checker-rd1-closed-synthetic-else", synthetic_else),
        (
            "checker-rd1-closed-nonliteral-allowed-key-store",
            nonliteral_allowed_key_store,
        ),
        ("checker-rd1-closed-extra-dynamic-load", extra_dynamic_load),
        ("checker-rd1-closed-nested-function-pattern", nested_function_pattern),
        ("checker-rd1-closed-alternate-combined", alternate_combined),
    )
    assert len(counterfactuals) == 13
    for mutant_id, mutant in counterfactuals:
        physical_source = _c2b3a_physically_import_and_collect_checker(
            tmp_path,
            mutant_id,
            mutant,
        )
        with pytest.raises(AssertionError) as exc_info:
            _assert_c2b3a_mutant_efficacy_checker_structure(physical_source)
        assert exc_info.value.args == (
            "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID",
        )
        _c2b3a_physically_run_checker_guard_rejection(tmp_path, mutant_id)

    selected_test_name = "test_c2b3a_m16_m65_executable_efficacy_is_exact"
    combined_guard_disabled = _c2b3a_semantic_replace_in_function(
        combined_audit_bypass,
        selected_test_name,
        "    _assert_c2b3a_mutant_efficacy_checker_structure(higher_order_source)\n",
        "    assert higher_order_source\n",
    )
    runtime_id = "checker-rd1-closed-combined-runtime-proof"
    _c2b3a_physically_import_and_collect_checker(
        tmp_path,
        runtime_id,
        combined_guard_disabled,
    )
    runtime_root = tmp_path / runtime_id
    for relative_path in (
        Path(".docs/c2b-durable-development-state.md"),
        Path(".docs/c2b3-program-initialization.md"),
        Path("tests/test_c2b3_program_initialization_contract.py"),
    ):
        source_path = ROOT / relative_path
        destination = runtime_root / relative_path
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        source_bytes = source_path.read_bytes()
        assert destination.write_bytes(source_bytes) == len(source_bytes)

    runtime_test_path = runtime_root / "tests" / Path(__file__).name
    execute_tmp = runtime_root / "execute-tmp"
    execute_pycache = runtime_root / "execute-pycache"
    for directory in (execute_tmp, execute_pycache):
        directory.mkdir(mode=0o700)
    execute_program = (
        "import builtins\n"
        "import importlib.util\n"
        "import pathlib\n"
        "import sys\n"
        "path = pathlib.Path(sys.argv[1]).resolve(strict=True)\n"
        "spec = importlib.util.spec_from_file_location(sys.argv[2], path)\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "sys.modules[spec.name] = module\n"
        "spec.loader.exec_module(module)\n"
        "genuine_code = None\n"
        "counts = {'genuine': 0, 'synthetic': 0}\n"
        "def recording_exec(code, namespace):\n"
        "    global genuine_code\n"
        "    result = builtins.exec(code, namespace)\n"
        "    genuine_code = namespace['_validate_contract'].__code__\n"
        "    return result\n"
        "def trace_calls(frame, event, arg):\n"
        "    if event == 'call':\n"
        "        if frame.f_code is genuine_code:\n"
        "            counts['genuine'] += 1\n"
        "        elif frame.f_code.co_name == 'synthetic_validate':\n"
        "            counts['synthetic'] += 1\n"
        "    return trace_calls\n"
        "module.exec = recording_exec\n"
        "sys.settrace(trace_calls)\n"
        "try:\n"
        "    module.test_c2b3a_m16_m65_executable_efficacy_is_exact()\n"
        "finally:\n"
        "    sys.settrace(None)\n"
        "assert genuine_code is not None\n"
        "assert counts == {'genuine': 0, 'synthetic': 100}\n"
    )
    executed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            execute_program,
            str(runtime_test_path),
            "c2b3a_closed_combined_runtime",
        ),
        cwd=runtime_root,
        env={
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONPYCACHEPREFIX": str(execute_pycache),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "TMPDIR": str(execute_tmp),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert executed.returncode == 0, executed.stderr
    assert executed.stdout == ""
    assert executed.stderr == ""


def test_c2b3a_outer_header_and_bounded_source_local_counterfactuals_are_rejected(
    tmp_path: Path,
) -> None:
    source = Path(__file__).resolve().read_text(encoding="utf-8")
    function_name = "_assert_c2b3a_mutant_dataflow_semantics"
    exact_header = (
        "def _assert_c2b3a_mutant_dataflow_semantics("
        "tree: ast.Module) -> None:\n"
    )

    def replace_outer_header(
        candidate_source: str,
        replacement: str,
    ) -> str:
        return _c2b3a_semantic_replace_in_function(
            candidate_source,
            function_name,
            exact_header,
            replacement,
        )

    def insert_after_ast_import(
        candidate_source: str,
        insertion: str,
    ) -> str:
        anchor = "import ast\n"
        assert candidate_source.count(anchor) == 1
        return candidate_source.replace(anchor, anchor + insertion, 1)

    exploit_support = (
        "_C2B3A_RD2_COUNTS = {\n"
        "    \"synthetic\": 0,\n"
        "    \"baseline\": 0,\n"
        "    \"terminal\": 0,\n"
        "    \"identity\": 0,\n"
        "}\n"
        "_C2B3A_RD2_GENUINE_CODE = None\n"
        "_C2B3A_RD2_SYNTHETIC_CODE = None\n\n\n"
        "def _c2b3a_rd2_exec_wrapper(\n"
        "    code: object,\n"
        "    execution_namespace: dict[str, object],\n"
        ") -> None:\n"
        "    global _C2B3A_RD2_GENUINE_CODE\n"
        "    global _C2B3A_RD2_SYNTHETIC_CODE\n"
        "    builtins.exec(code, execution_namespace)\n"
        "    _C2B3A_RD2_GENUINE_CODE = (\n"
        "        execution_namespace[\"_validate_contract\"].__code__\n"
        "    )\n\n"
        "    def synthetic_validate(candidate: object) -> None:\n"
        "        del candidate\n"
        "        _C2B3A_RD2_COUNTS[\"synthetic\"] += 1\n"
        "        caller = sys._getframe(1)\n"
        "        if caller.f_code.co_name == (\n"
        "            \"_assert_c2b3a_mutant_dataflow_semantics\"\n"
        "        ):\n"
        "            _C2B3A_RD2_COUNTS[\"baseline\"] += 1\n"
        "        elif caller.f_code.co_name == \"instrumented_expect_violation\":\n"
        "            _C2B3A_RD2_COUNTS[\"terminal\"] += 1\n"
        "        if (\n"
        "            execution_namespace[\"_validate_contract\"]\n"
        "            is synthetic_validate\n"
        "            and caller.f_locals.get(\"original_validate\")\n"
        "            is synthetic_validate\n"
        "        ):\n"
        "            _C2B3A_RD2_COUNTS[\"identity\"] += 1\n"
        "        if _C2B3A_RD2_COUNTS[\"synthetic\"] % 2 == 0:\n"
        "            raise execution_namespace[\"_ContractViolation\"](\n"
        "                \"C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID\"\n"
        "            )\n\n"
        "    _C2B3A_RD2_SYNTHETIC_CODE = synthetic_validate.__code__\n"
        "    namespace_alias = execution_namespace\n"
        "    namespace_alias[\"_validate_contract\"] = synthetic_validate\n\n\n"
        "def _c2b3a_rd2_install_exec_wrapper() -> None:\n"
        "    globals()[\"exec\"] = _c2b3a_rd2_exec_wrapper\n\n\n"
    )
    exploit = insert_after_ast_import(source, "import builtins\n")
    exploit = replace_outer_header(
        exploit,
        exploit_support
        + "def _assert_c2b3a_mutant_dataflow_semantics(\n"
        + "    tree: ast.Module = _c2b3a_rd2_install_exec_wrapper(),\n"
        + ") -> None:\n",
    )

    decorator_support = (
        "def _c2b3a_rd2_mutating_decorator(function: object) -> object:\n"
        "    globals()[\"exec\"] = lambda code, namespace: None\n"
        "    return function\n\n\n"
    )
    header_counterfactuals = (
        (
            "checker-rd2-benign-positional-default",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: ast.Module = None) -> None:\n",
            ),
        ),
        (
            "checker-rd2-global-mutating-default",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics(\n"
                "    tree: ast.Module = globals().__setitem__(\n"
                "        \"_c2b3a_rd2_default_marker\", True\n"
                "    ),\n"
                ") -> None:\n",
            ),
        ),
        (
            "checker-rd2-missing-tree-annotation",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics(tree) -> None:\n",
            ),
        ),
        (
            "checker-rd2-simple-tree-annotation",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: object) -> None:\n",
            ),
        ),
        (
            "checker-rd2-string-tree-annotation",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: \"ast.Module\") -> None:\n",
            ),
        ),
        (
            "checker-rd2-union-tree-annotation",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: ast.Module | None) -> None:\n",
            ),
        ),
        (
            "checker-rd2-subscripted-tree-annotation",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: tuple[ast.Module]) -> None:\n",
            ),
        ),
        (
            "checker-rd2-call-tree-annotation",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: globals().get(\"ast\").Module) -> None:\n",
            ),
        ),
        (
            "checker-rd2-named-expression-tree-annotation",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: (rd2_annotation := ast.Module)) -> None:\n",
            ),
        ),
        (
            "checker-rd2-conditional-tree-annotation",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: (ast.Module if True else object)) -> None:\n",
            ),
        ),
        (
            "checker-rd2-lambda-tree-annotation",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: (lambda: ast.Module)) -> None:\n",
            ),
        ),
        (
            "checker-rd2-comprehension-tree-annotation",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics(\n"
                "    tree: [item for item in (ast.Module,)],\n"
                ") -> None:\n",
            ),
        ),
        (
            "checker-rd2-formatted-string-tree-annotation",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: f\"{ast.Module}\") -> None:\n",
            ),
        ),
        (
            "checker-rd2-tree-argument-type-comment",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics(\n"
                "    tree: ast.Module,  # type: ast.Module\n"
                ") -> None:\n",
            ),
        ),
        (
            "checker-rd2-second-ordinary-argument",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: ast.Module, extra: object) -> None:\n",
            ),
        ),
        (
            "checker-rd2-positional-only-tree",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: ast.Module, /) -> None:\n",
            ),
        ),
        (
            "checker-rd2-vararg",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: ast.Module, *extra: object) -> None:\n",
            ),
        ),
        (
            "checker-rd2-keyword-only-argument",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: ast.Module, *, extra: object) -> None:\n",
            ),
        ),
        (
            "checker-rd2-keyword-only-default",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: ast.Module, *, extra: object = None) -> None:\n",
            ),
        ),
        (
            "checker-rd2-kwargs",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: ast.Module, **extra: object) -> None:\n",
            ),
        ),
        (
            "checker-rd2-benign-decorator",
            replace_outer_header(
                source,
                "@(lambda function: function)\n" + exact_header,
            ),
        ),
        (
            "checker-rd2-altered-return-annotation",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: ast.Module) -> object:\n",
            ),
        ),
        (
            "checker-rd2-function-type-comment",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics("
                "tree: ast.Module) -> None:  "
                "# type: (ast.Module) -> None\n",
            ),
        ),
        (
            "checker-rd2-type-parameter",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics[T]("
                "tree: ast.Module) -> None:\n",
            ),
        ),
        (
            "checker-rd2-type-parameter-bound",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics[T: object]("
                "tree: ast.Module) -> None:\n",
            ),
        ),
        (
            "checker-rd2-type-parameter-constraints",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics["
                "T: (str, bytes)](tree: ast.Module) -> None:\n",
            ),
        ),
        (
            "checker-rd2-type-parameter-default",
            replace_outer_header(
                source,
                "def _assert_c2b3a_mutant_dataflow_semantics[T = object]("
                "tree: ast.Module) -> None:\n",
            ),
        ),
        (
            "checker-rd2-indirect-exec-mutating-decorator",
            replace_outer_header(
                source,
                decorator_support
                + "@_c2b3a_rd2_mutating_decorator\n"
                + exact_header,
            ),
        ),
    )
    module_binding_counterfactuals = (
        (
            "checker-rd2-module-exec-assignment",
            insert_after_ast_import(
                source,
                "exec = lambda code, namespace: None\n",
            ),
        ),
        (
            "checker-rd2-module-exec-named-expression",
            insert_after_ast_import(
                source,
                "(exec := (lambda code, namespace: None))\n",
            ),
        ),
        (
            "checker-rd2-module-exec-import-alias",
            insert_after_ast_import(source, "import builtins as exec\n"),
        ),
        (
            "checker-rd2-module-exec-function-definition",
            insert_after_ast_import(
                source,
                "def exec(code, namespace):\n"
                "    del code, namespace\n\n\n",
            ),
        ),
        (
            "checker-rd2-module-exec-class-definition",
            insert_after_ast_import(
                source,
                "class exec:\n"
                "    pass\n\n\n",
            ),
        ),
        (
            "checker-rd2-module-exec-exception-target",
            insert_after_ast_import(
                source,
                "try:\n"
                "    raise RuntimeError\n"
                "except RuntimeError as exec:\n"
                "    pass\n",
            ),
        ),
        (
            "checker-rd2-module-exec-pattern-binding",
            insert_after_ast_import(
                source,
                "match (lambda code, namespace: None):\n"
                "    case exec:\n"
                "        pass\n",
            ),
        ),
        (
            "checker-rd2-module-exec-global-declaration",
            insert_after_ast_import(source, "global exec\n"),
        ),
        (
            "checker-rd2-module-exec-loop-target",
            insert_after_ast_import(
                source,
                "for exec in (lambda code, namespace: None,):\n"
                "    pass\n",
            ),
        ),
    )
    ast_proxy_support = (
        "_C2B3A_BOUNDARY_REAL_AST = ast\n"
        "class _C2B3A_BOUNDARY_AST_PROXY:\n"
        "    def __getattr__(self, name):\n"
        "        return getattr(_C2B3A_BOUNDARY_REAL_AST, name)\n\n\n"
    )
    bounded_source_local_counterfactuals = (
        (
            "checker-boundary-wildcard-exec-import",
            insert_after_ast_import(source, "from builtins import *\n"),
        ),
        (
            "checker-boundary-globals-exec-write",
            insert_after_ast_import(
                source,
                'globals()["exec"] = lambda code, namespace: None\n',
            ),
        ),
        (
            "checker-boundary-vars-module-exec-write",
            insert_after_ast_import(
                source,
                "import sys\n"
                'vars(sys.modules[__name__])["exec"] = '
                "lambda code, namespace: None\n",
            ),
        ),
        (
            "checker-boundary-setattr-module-exec-write",
            insert_after_ast_import(
                source,
                "import sys\n"
                'setattr(sys.modules[__name__], "exec", '
                "lambda code, namespace: None)\n",
            ),
        ),
        (
            "checker-boundary-globals-exec-delete",
            insert_after_ast_import(
                source,
                'globals().setdefault("exec", exec)\n'
                'del globals()["exec"]\n',
            ),
        ),
        (
            "checker-boundary-vars-module-exec-delete",
            insert_after_ast_import(
                source,
                "import sys\n"
                'vars(sys.modules[__name__]).setdefault("exec", exec)\n'
                'del vars(sys.modules[__name__])["exec"]\n',
            ),
        ),
        (
            "checker-boundary-delattr-module-exec-delete",
            insert_after_ast_import(
                source,
                "import sys\n"
                'vars(sys.modules[__name__]).setdefault("exec", exec)\n'
                'delattr(sys.modules[__name__], "exec")\n',
            ),
        ),
        (
            "checker-boundary-lexical-ast-write",
            insert_after_ast_import(
                source,
                ast_proxy_support + "ast = _C2B3A_BOUNDARY_AST_PROXY()\n",
            ),
        ),
        (
            "checker-boundary-globals-ast-write",
            insert_after_ast_import(
                source,
                ast_proxy_support
                + 'globals()["ast"] = _C2B3A_BOUNDARY_AST_PROXY()\n',
            ),
        ),
        (
            "checker-boundary-vars-module-ast-write",
            insert_after_ast_import(
                source,
                "import sys\n"
                + ast_proxy_support
                + 'vars(sys.modules[__name__])["ast"] = '
                "_C2B3A_BOUNDARY_AST_PROXY()\n",
            ),
        ),
        (
            "checker-boundary-setattr-module-ast-write",
            insert_after_ast_import(
                source,
                "import sys\n"
                + ast_proxy_support
                + 'setattr(sys.modules[__name__], "ast", '
                "_C2B3A_BOUNDARY_AST_PROXY())\n",
            ),
        ),
    )
    counterfactuals = (
        ("checker-rd2-default-expression-exploit", exploit),
        *header_counterfactuals,
        *module_binding_counterfactuals,
        *bounded_source_local_counterfactuals,
    )
    assert len(header_counterfactuals) == 28
    assert len(module_binding_counterfactuals) == 9
    assert len(bounded_source_local_counterfactuals) == 11
    assert len(counterfactuals) == 49
    for mutant_id, mutant in counterfactuals:
        physical_source = _c2b3a_physically_import_and_collect_checker(
            tmp_path,
            mutant_id,
            mutant,
        )
        with pytest.raises(AssertionError) as exc_info:
            _assert_c2b3a_mutant_efficacy_checker_structure(physical_source)
        assert exc_info.value.args == (
            "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID",
        )
        _c2b3a_physically_run_checker_guard_rejection(tmp_path, mutant_id)

    selected_test_name = "test_c2b3a_m16_m65_executable_efficacy_is_exact"
    exploit_guard_disabled = _c2b3a_semantic_replace_in_function(
        exploit,
        selected_test_name,
        "    _assert_c2b3a_mutant_efficacy_checker_structure("
        "higher_order_source)\n",
        "    assert higher_order_source\n",
    )
    runtime_id = "checker-rd2-default-expression-runtime-proof"
    _c2b3a_physically_import_and_collect_checker(
        tmp_path,
        runtime_id,
        exploit_guard_disabled,
    )
    runtime_root = tmp_path / runtime_id
    for relative_path in (
        Path(".docs/c2b-durable-development-state.md"),
        Path(".docs/c2b3-program-initialization.md"),
        Path("tests/test_c2b3_program_initialization_contract.py"),
    ):
        source_path = ROOT / relative_path
        destination = runtime_root / relative_path
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        source_bytes = source_path.read_bytes()
        assert destination.write_bytes(source_bytes) == len(source_bytes)

    runtime_test_path = runtime_root / "tests" / Path(__file__).name
    execute_tmp = runtime_root / "execute-tmp"
    execute_pycache = runtime_root / "execute-pycache"
    for directory in (execute_tmp, execute_pycache):
        directory.mkdir(mode=0o700)
    execute_program = (
        "import importlib.util\n"
        "import pathlib\n"
        "import sys\n"
        "path = pathlib.Path(sys.argv[1]).resolve(strict=True)\n"
        "spec = importlib.util.spec_from_file_location(sys.argv[2], path)\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "sys.modules[spec.name] = module\n"
        "spec.loader.exec_module(module)\n"
        "profile = {'genuine': 0}\n"
        "def trace_calls(frame, event, argument):\n"
        "    del argument\n"
        "    if (\n"
        "        event == 'call'\n"
        "        and frame.f_code is module._C2B3A_RD2_GENUINE_CODE\n"
        "    ):\n"
        "        profile['genuine'] += 1\n"
        "    return trace_calls\n"
        "sys.settrace(trace_calls)\n"
        "try:\n"
        "    module.test_c2b3a_m16_m65_executable_efficacy_is_exact()\n"
        "finally:\n"
        "    sys.settrace(None)\n"
        "assert module._C2B3A_RD2_GENUINE_CODE is not None\n"
        "assert module._C2B3A_RD2_SYNTHETIC_CODE is not None\n"
        "assert profile == {'genuine': 0}\n"
        "assert module._C2B3A_RD2_COUNTS == {\n"
        "    'synthetic': 100,\n"
        "    'baseline': 50,\n"
        "    'terminal': 50,\n"
        "    'identity': 100,\n"
        "}\n"
    )
    executed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            execute_program,
            str(runtime_test_path),
            "c2b3a_rd2_default_expression_runtime",
        ),
        cwd=runtime_root,
        env={
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONPYCACHEPREFIX": str(execute_pycache),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "TMPDIR": str(execute_tmp),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert executed.returncode == 0, executed.stderr
    assert executed.stdout == ""
    assert executed.stderr == ""


def test_c2b3a_exec_produced_validator_identity_and_restoration_are_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    higher_order_source = Path(__file__).resolve().read_text(encoding="utf-8")
    _assert_c2b3a_mutant_efficacy_checker_structure(higher_order_source)
    direct_source = _c2b3a_bounded_oracle_source()
    direct_tree = ast.parse(direct_source, filename=C2B3A_ORACLE_PATH.name)
    real_exec = exec
    assert real_exec is builtins.exec
    captured: dict[str, object] = {}
    profile = {
        "genuine": 0,
        "baseline": 0,
        "terminal": 0,
        "alternate": 0,
        "identity": 0,
        "unexpected_caller": 0,
    }

    def alternate_validate(candidate: object) -> None:
        raise AssertionError(candidate)

    alternate_code = alternate_validate.__code__

    def recording_exec(code: object, namespace: dict[str, object]) -> None:
        real_exec(code, namespace)
        validator = namespace["_validate_contract"]
        captured["namespace"] = namespace
        captured["validator"] = validator
        captured["validator_code"] = validator.__code__
        captured["candidate"] = namespace["_candidate"]
        captured["expect_violation"] = namespace["_expect_violation"]

    def trace_validator_calls(
        frame: object,
        event: str,
        argument: object,
    ) -> object:
        del argument
        if event != "call":
            return trace_validator_calls
        if frame.f_code is alternate_code:
            profile["alternate"] += 1
        if frame.f_code is captured.get("validator_code"):
            profile["genuine"] += 1
            caller = frame.f_back
            if caller is None:
                profile["unexpected_caller"] += 1
            elif caller.f_code.co_name == function_name:
                profile["baseline"] += 1
            elif caller.f_code.co_name == "instrumented_expect_violation":
                profile["terminal"] += 1
            else:
                profile["unexpected_caller"] += 1
            namespace = captured["namespace"]
            validator = captured["validator"]
            if (
                namespace["_validate_contract"] is validator
                and caller is not None
                and caller.f_locals.get("original_validate") is validator
            ):
                profile["identity"] += 1
        return trace_validator_calls

    function_name = "_assert_c2b3a_mutant_dataflow_semantics"
    with monkeypatch.context() as context:
        context.setitem(globals(), "exec", recording_exec)
        sys.settrace(trace_validator_calls)
        try:
            _assert_c2b3a_mutant_dataflow_semantics(direct_tree)
        finally:
            sys.settrace(None)

    assert profile == {
        "genuine": 100,
        "baseline": 50,
        "terminal": 50,
        "alternate": 0,
        "identity": 100,
        "unexpected_caller": 0,
    }
    normal_namespace = captured["namespace"]
    assert normal_namespace["_validate_contract"] is captured["validator"]
    assert normal_namespace["_candidate"] is captured["candidate"]
    assert (
        normal_namespace["_expect_violation"]
        is captured["expect_violation"]
    )

    def assert_forced_failure_restores(mutant_source: str) -> None:
        forced_capture: dict[str, object] = {}

        def forced_recording_exec(
            code: object,
            namespace: dict[str, object],
        ) -> None:
            real_exec(code, namespace)
            forced_capture["namespace"] = namespace
            forced_capture["validator"] = namespace["_validate_contract"]
            forced_capture["candidate"] = namespace["_candidate"]
            forced_capture["expect_violation"] = namespace["_expect_violation"]

        mutant_tree = ast.parse(mutant_source, filename=C2B3A_ORACLE_PATH.name)
        with monkeypatch.context() as context:
            context.setitem(globals(), "exec", forced_recording_exec)
            with pytest.raises(AssertionError) as exc_info:
                _assert_c2b3a_mutant_dataflow_semantics(mutant_tree)
        assert exc_info.value.args == (
            "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID",
        )
        namespace = forced_capture["namespace"]
        assert namespace["_validate_contract"] is forced_capture["validator"]
        assert namespace["_candidate"] is forced_capture["candidate"]
        assert (
            namespace["_expect_violation"]
            is forced_capture["expect_violation"]
        )

    m16_name = "test_commit_close_mutant_m16_missing_matrix_row_is_rejected"
    exact_terminal = (
        '_expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")'
    )
    forced_preterminal = _c2b3a_semantic_function_body_mutant(
        direct_source,
        m16_name,
        "candidate = _candidate()\n"
        "candidate['unused'] = 1 / 0\n"
        + exact_terminal,
    )
    forced_terminal = _c2b3a_semantic_function_body_mutant(
        direct_source,
        m16_name,
        "candidate = _candidate()\n"
        "candidate['commit_close_outcome_addendum']['outcome_matrix'] = "
        "candidate['commit_close_outcome_addendum']['outcome_matrix'][:-1]\n"
        + exact_terminal
        + "\n"
        + exact_terminal,
    )
    assert_forced_failure_restores(forced_preterminal)
    assert_forced_failure_restores(forced_terminal)


@pytest.mark.parametrize(
    "function_name",
    (
        "test_commit_close_addendum_direct_oracle_matrix_is_closed",
        "test_commit_close_addendum_custody_recovery_and_scope_are_exact",
        "test_commit_close_relational_process_control_reference_cases_are_exact",
        "test_post_close_cleanup_reference_model_covers_every_release_point",
    ),
)
def test_c2b3a_semantic_guard_rejects_every_protected_positive_body_as_pass(
    function_name: str,
    tmp_path: Path,
) -> None:
    source = _c2b3a_bounded_oracle_source()
    mutant = _c2b3a_semantic_function_body_mutant(source, function_name, "pass")
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-positive-pass-" + function_name,
        mutant,
        function_name,
    )


def test_c2b3a_positive_outer_execution_physical_counterfactuals_are_rejected(
    tmp_path: Path,
) -> None:
    source = _c2b3a_bounded_oracle_source()
    process = (
        "test_commit_close_relational_process_control_reference_cases_are_exact"
    )
    cleanup = "test_post_close_cleanup_reference_model_covers_every_release_point"
    process_loop = "    for case_id, primary, secondary in cases:\n"
    cleanup_loop = "    for case_id, inputs in cases:\n"
    process_last = '        assert observed["outward_primary"] is primary\n'
    cleanup_last = "        assert observed == expected\n"
    process_assert_end = (
        "        EXPECTED_PROCESS_CONTROL_REFERENCE_CASES\n"
        "    )\n"
    )
    cleanup_assert_end = (
        "        EXPECTED_CLEANUP_REFERENCE_CASES\n"
        "    )\n"
    )

    process_mutants = (
        (
            "process-return-before-loop",
            _c2b3a_semantic_replace_in_function(
                source,
                process,
                process_loop,
                "    return\n\n" + process_loop,
            ),
        ),
        (
            "process-return-after-first",
            _c2b3a_semantic_replace_in_function(
                source,
                process,
                process_last,
                process_last + "        return\n",
            ),
        ),
        (
            "process-post-assert-tail-slice",
            _c2b3a_semantic_replace_in_function(
                source,
                process,
                process_assert_end,
                process_assert_end + "    cases = cases[:-1]\n",
            ),
        ),
        (
            "process-post-assert-head-slice",
            _c2b3a_semantic_replace_in_function(
                source,
                process,
                process_assert_end,
                process_assert_end + "    cases = cases[1:]\n",
            ),
        ),
        (
            "process-loop-tail-slice",
            _c2b3a_semantic_replace_in_function(
                source,
                process,
                "in cases:\n",
                "in cases[:-1]:\n",
            ),
        ),
        (
            "process-loop-tuple-tail-slice",
            _c2b3a_semantic_replace_in_function(
                source,
                process,
                "in cases:\n",
                "in tuple(cases)[:-1]:\n",
            ),
        ),
        (
            "process-break-after-one",
            _c2b3a_semantic_replace_in_function(
                source,
                process,
                process_last,
                process_last + "        break\n",
            ),
        ),
        (
            "process-continue-first",
            _c2b3a_semantic_replace_in_function(
                source,
                process,
                process_loop,
                process_loop
                + '        if case_id == "cross-k-s":\n'
                + "            continue\n",
            ),
        ),
        (
            "process-if-filter",
            _c2b3a_semantic_replace_in_function(
                source,
                process,
                "in cases:\n",
                'in (case for case in cases if case[0] != "cross-k-s"):\n',
            ),
        ),
        (
            "process-empty-cases",
            _c2b3a_semantic_replace_in_function(
                source,
                process,
                "    cases = _process_control_reference_cases()\n",
                "    cases = ()\n",
            ),
        ),
        (
            "process-remove-one-after-assert",
            _c2b3a_semantic_replace_in_function(
                source,
                process,
                process_assert_end,
                process_assert_end
                + '    cases = tuple(case for case in cases if case[0] != "private-payload")\n',
            ),
        ),
        (
            "process-loop-pass",
            _c2b3a_semantic_top_level_loop_pass_mutant(source, process),
        ),
        (
            "process-helper-skipped-for-one",
            _c2b3a_semantic_replace_in_function(
                source,
                process,
                process_loop,
                process_loop
                + '        if case_id == "cross-k-s":\n'
                + "            continue\n",
            ),
        ),
    )

    cleanup_mutants = (
        (
            "cleanup-return-before-loop",
            _c2b3a_semantic_replace_in_function(
                source,
                cleanup,
                cleanup_loop,
                "    return\n\n" + cleanup_loop,
            ),
        ),
        (
            "cleanup-return-after-first",
            _c2b3a_semantic_replace_in_function(
                source,
                cleanup,
                cleanup_last,
                cleanup_last + "        return\n",
            ),
        ),
        (
            "cleanup-post-assert-tail-slice",
            _c2b3a_semantic_replace_in_function(
                source,
                cleanup,
                cleanup_assert_end,
                cleanup_assert_end + "    cases = cases[:-1]\n",
            ),
        ),
        (
            "cleanup-post-assert-head-slice",
            _c2b3a_semantic_replace_in_function(
                source,
                cleanup,
                cleanup_assert_end,
                cleanup_assert_end + "    cases = cases[1:]\n",
            ),
        ),
        (
            "cleanup-loop-tail-slice",
            _c2b3a_semantic_replace_in_function(
                source,
                cleanup,
                "in cases:\n",
                "in cases[:-1]:\n",
            ),
        ),
        (
            "cleanup-loop-tuple-tail-slice",
            _c2b3a_semantic_replace_in_function(
                source,
                cleanup,
                "in cases:\n",
                "in tuple(cases)[:-1]:\n",
            ),
        ),
        (
            "cleanup-break-after-one",
            _c2b3a_semantic_replace_in_function(
                source,
                cleanup,
                cleanup_last,
                cleanup_last + "        break\n",
            ),
        ),
        (
            "cleanup-continue-first",
            _c2b3a_semantic_replace_in_function(
                source,
                cleanup,
                cleanup_loop,
                cleanup_loop
                + '        if case_id == "normal-a":\n'
                + "            continue\n",
            ),
        ),
        (
            "cleanup-if-filter",
            _c2b3a_semantic_replace_in_function(
                source,
                cleanup,
                "in cases:\n",
                'in (case for case in cases if case[0] != "normal-a"):\n',
            ),
        ),
        (
            "cleanup-empty-cases",
            _c2b3a_semantic_replace_in_function(
                source,
                cleanup,
                "    cases = CLEANUP_REFERENCE_INPUT_CASES\n",
                "    cases = ()\n",
            ),
        ),
        (
            "cleanup-remove-one-after-assert",
            _c2b3a_semantic_replace_in_function(
                source,
                cleanup,
                cleanup_assert_end,
                cleanup_assert_end
                + '    cases = tuple(case for case in cases if case[0] != "descriptor-unknown")\n',
            ),
        ),
        (
            "cleanup-loop-pass",
            _c2b3a_semantic_top_level_loop_pass_mutant(source, cleanup),
        ),
        (
            "cleanup-helper-skipped-for-one",
            _c2b3a_semantic_replace_in_function(
                source,
                cleanup,
                "        observed = _cleanup_reference(*inputs)\n"
                "        expected = EXPECTED_CLEANUP_REFERENCE_CASES[case_id]\n",
                "        expected = EXPECTED_CLEANUP_REFERENCE_CASES[case_id]\n"
                '        if case_id == "normal-a":\n'
                "            observed = expected\n"
                "        else:\n"
                "            observed = _cleanup_reference(*inputs)\n",
            ),
        ),
    )

    assert len(process_mutants) == 13
    assert len(cleanup_mutants) == 13
    for mutant_id, mutant in process_mutants:
        _assert_c2b3a_semantic_mutant_is_physical(
            tmp_path,
            mutant_id,
            mutant,
            process,
        )
    for mutant_id, mutant in cleanup_mutants:
        _assert_c2b3a_semantic_mutant_is_physical(
            tmp_path,
            mutant_id,
            mutant,
            cleanup,
        )


def test_c2b3a_semantic_guard_rejects_constant_reference_helper(
    tmp_path: Path,
) -> None:
    source = _c2b3a_bounded_oracle_source()
    positive = (
        "test_commit_close_relational_process_control_reference_cases_are_exact"
    )

    constant_helper = _c2b3a_semantic_function_body_mutant(
        source,
        "_relational_process_control_reference",
        "return {'constant': True}",
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "relational-constant-helper",
        constant_helper,
        positive,
    )

    mutants = (
        (
            "relational-all-assertions-self",
            _c2b3a_semantic_assertions_self_comparison_mutant(
                source,
                positive,
            ),
        ),
        (
            "relational-full-observed-self",
            _c2b3a_semantic_replace_in_function(
                source,
                positive,
                '        assert observed["safe_projection"] == expected\n',
                "        assert observed == observed\n",
            ),
        ),
        (
            "relational-expected-rebound",
            _c2b3a_semantic_replace_in_function(
                source,
                positive,
                "        expected = EXPECTED_PROCESS_CONTROL_REFERENCE_CASES[case_id]\n"
                '        assert observed["safe_projection"] == expected\n',
                "        expected = observed\n"
                "        assert observed == expected\n",
            ),
        ),
        (
            "relational-expected-reconstructed",
            _c2b3a_semantic_replace_in_function(
                source,
                positive,
                "        expected = EXPECTED_PROCESS_CONTROL_REFERENCE_CASES[case_id]\n",
                '        expected = observed["safe_projection"]\n',
            ),
        ),
        (
            "relational-same-field",
            _c2b3a_semantic_replace_in_function(
                source,
                positive,
                '        assert observed["safe_projection"] == expected\n',
                '        assert observed["safe_projection"] == observed["safe_projection"]\n',
            ),
        ),
        (
            "relational-field-aliases",
            _c2b3a_semantic_replace_in_function(
                source,
                positive,
                '        assert observed["safe_projection"] == expected\n',
                '        left_alias = observed["safe_projection"]\n'
                '        right_alias = observed["safe_projection"]\n'
                "        assert left_alias == right_alias\n",
            ),
        ),
        (
            "relational-identity-self",
            _c2b3a_semantic_replace_in_function(
                source,
                positive,
                '        assert observed["provided_primary"] is primary\n',
                "        assert primary is primary\n",
            ),
        ),
        (
            "relational-expected-removed",
            _c2b3a_semantic_expected_literal_inventory_mutant(
                source,
                "EXPECTED_PROCESS_CONTROL_REFERENCE_CASES",
                positive,
                remove=True,
            ),
        ),
    )
    for mutant_id, mutant in mutants:
        _assert_c2b3a_semantic_mutant_is_physical(
            tmp_path,
            mutant_id,
            mutant,
            positive,
            require_selected_pass=True,
        )


def test_c2b3a_semantic_guard_rejects_helper_result_overwrites_and_mutation(
    tmp_path: Path,
) -> None:
    source = _c2b3a_bounded_oracle_source()
    positive = "test_post_close_cleanup_reference_model_covers_every_release_point"

    constant_helper = _c2b3a_semantic_function_body_mutant(
        source,
        "_cleanup_reference",
        "return ()",
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "cleanup-constant-helper",
        constant_helper,
        positive,
    )

    mutants = (
        (
            "cleanup-all-assertions-self",
            _c2b3a_semantic_assertions_self_comparison_mutant(
                source,
                positive,
            ),
        ),
        (
            "cleanup-full-observed-self",
            _c2b3a_semantic_replace_in_function(
                source,
                positive,
                "        assert observed == expected\n",
                "        assert observed == observed\n",
            ),
        ),
        (
            "cleanup-expected-rebound",
            _c2b3a_semantic_replace_in_function(
                source,
                positive,
                "        expected = EXPECTED_CLEANUP_REFERENCE_CASES[case_id]\n"
                "        assert observed == expected\n",
                "        expected = observed\n"
                "        assert observed == expected\n",
            ),
        ),
        (
            "cleanup-expected-reconstructed",
            _c2b3a_semantic_replace_in_function(
                source,
                positive,
                "        expected = EXPECTED_CLEANUP_REFERENCE_CASES[case_id]\n",
                "        expected = tuple(observed)\n",
            ),
        ),
        (
            "cleanup-same-field",
            _c2b3a_semantic_replace_in_function(
                source,
                positive,
                "        assert observed == expected\n",
                "        assert observed[0] == observed[0]\n",
            ),
        ),
        (
            "cleanup-field-aliases",
            _c2b3a_semantic_replace_in_function(
                source,
                positive,
                "        assert observed == expected\n",
                "        left_alias = observed[0]\n"
                "        right_alias = observed[0]\n"
                "        assert left_alias == right_alias\n",
            ),
        ),
        (
            "cleanup-observed-overwrite",
            _c2b3a_semantic_replace_in_function(
                source,
                positive,
                "        expected = EXPECTED_CLEANUP_REFERENCE_CASES[case_id]\n",
                "        expected = EXPECTED_CLEANUP_REFERENCE_CASES[case_id]\n"
                "        observed = expected\n",
            ),
        ),
        (
            "cleanup-expected-emptied",
            _c2b3a_semantic_expected_literal_inventory_mutant(
                source,
                "EXPECTED_CLEANUP_REFERENCE_CASES",
                positive,
                remove=False,
            ),
        ),
    )
    for mutant_id, mutant in mutants:
        _assert_c2b3a_semantic_mutant_is_physical(
            tmp_path,
            mutant_id,
            mutant,
            positive,
            require_selected_pass=True,
        )


def test_c2b3a_semantic_guard_rejects_removed_legacy_ledger_classification(
    tmp_path: Path,
) -> None:
    source = _c2b3a_bounded_oracle_source()
    classification_start = '    "legacy_exception_probe_ledger_classification": {'
    cleanup_start = '    "post_close_cleanup_contract": {'
    assert source.count(classification_start) == 1
    assert source.count(cleanup_start) == 1
    before, classification_and_later = source.split(classification_start, 1)
    _classification, after = classification_and_later.split(cleanup_start, 1)
    mutant = before + cleanup_start + after
    ast.parse(mutant, filename="legacy-ledger-classification-removed")
    _c2b3a_physically_import_and_collect_mutant(
        tmp_path,
        "legacy-ledger-classification-removed",
        mutant,
    )
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_independent_oracle_architecture(mutant)
    assert str(exc_info.value) == (
        "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
    )


def test_c2b3a_executable_efficacy_rejects_runtime_mutant_counterfactuals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _c2b3a_bounded_oracle_source()
    m16_name = "test_commit_close_mutant_m16_missing_matrix_row_is_rejected"
    terminal = (
        '_expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")'
    )
    runtime_counterfactuals = (
        (
            "m16-mapped-current-value-noop",
            "candidate = _candidate()\n"
            "candidate['commit_close_outcome_addendum']['outcome_matrix'] = "
            "candidate['commit_close_outcome_addendum']['outcome_matrix']\n"
            + terminal,
            "candidate['commit_close_outcome_addendum']['outcome_matrix'] = "
            "candidate['commit_close_outcome_addendum']['outcome_matrix']",
        ),
        (
            "m16-mapped-preterminal-failure",
            "candidate = _candidate()\n"
            "candidate['unused'] = 1 / 0\n"
            + terminal,
            "candidate['unused'] = 1 / 0",
        ),
    )
    for mutant_id, body, mapped_mutation in runtime_counterfactuals:
        mutant = _c2b3a_semantic_function_body_mutant(
            source,
            m16_name,
            body,
        )
        _c2b3a_physically_import_and_collect_mutant(
            tmp_path,
            mutant_id,
            mutant,
        )
        tree = ast.parse(mutant, filename=mutant_id)
        function = _c2b3a_oracle_top_level_function(tree, m16_name)
        assert tuple(ast.unparse(statement) for statement in function.body[1:-1]) == (
            mapped_mutation,
        )
        with monkeypatch.context() as context:
            context.setitem(
                C2B3A_M16_M65_EXPECTED_MUTATION_SOURCE,
                "M16",
                (mapped_mutation,),
            )
            with pytest.raises(AssertionError) as exc_info:
                _assert_c2b3a_independent_oracle_architecture(mutant)
        assert str(exc_info.value) == (
            "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
        )

    double_terminal = _c2b3a_semantic_function_body_mutant(
        source,
        m16_name,
        "candidate = _candidate()\n"
        "candidate['commit_close_outcome_addendum']['outcome_matrix'] = "
        "candidate['commit_close_outcome_addendum']['outcome_matrix'][:-1]\n"
        + terminal
        + "\n"
        + terminal,
    )
    _c2b3a_physically_import_and_collect_mutant(
        tmp_path,
        "m16-terminal-twice",
        double_terminal,
    )
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_independent_oracle_architecture(double_terminal)
    assert str(exc_info.value) == (
        "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
    )


def test_c2b3a_semantic_guard_rejects_linear_mutant_counterfactuals(
    tmp_path: Path,
) -> None:
    source = _c2b3a_bounded_oracle_source()
    m16_name = "test_commit_close_mutant_m16_missing_matrix_row_is_rejected"
    m31_name = "test_commit_close_mutant_m31_same_class_implies_same_object_is_rejected"
    m32_name = "test_commit_close_mutant_m32_distinct_same_class_routing_is_rejected"
    m33_name = "test_commit_close_mutant_m33_same_instance_routing_is_rejected"
    m34_name = "test_commit_close_mutant_m34_prelinked_cause_promise_is_rejected"
    m35_name = "test_commit_close_mutant_m35_prelinked_context_promise_is_rejected"
    m32_mutation = (
        '    candidate["commit_close_outcome_addendum"]["matrix_identity_overlay"]'
        '["diagonal_discriminator"] = "same exact class always selects same_instance"\n'
    )
    exact_terminal = (
        '    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")\n'
    )

    def physical_rejection(
        label: str,
        mutant: str,
        *,
        exact_collection: bool = True,
    ) -> None:
        ast.parse(mutant, filename=label)
        _c2b3a_physically_import_and_collect_mutant(
            tmp_path,
            label,
            mutant,
            C2B3A_ORACLE_EXPECTED_TEST_NODE_NAMES if exact_collection else None,
        )
        with pytest.raises(AssertionError) as exc_info:
            _assert_c2b3a_independent_oracle_architecture(mutant)
        assert str(exc_info.value) == (
            "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID"
        )

    m16_exact_mutation = (
        "candidate['commit_close_outcome_addendum']['outcome_matrix'] = "
        "candidate['commit_close_outcome_addendum']['outcome_matrix'][:-1]"
    )
    m16_exact_terminal = (
        "_expect_violation(candidate, "
        "'C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID')"
    )
    m16_counterfactual_bodies = (
        (
            "m16-current-value-no-op",
            "candidate = _candidate()\n"
            "candidate['commit_close_outcome_addendum']['outcome_matrix'] = "
            "candidate['commit_close_outcome_addendum']['outcome_matrix']\n"
            + m16_exact_terminal,
        ),
        (
            "m16-zero-step-open-slice",
            "candidate = _candidate()\n"
            "candidate[::0] = 0\n"
            + m16_exact_terminal,
        ),
        (
            "m16-zero-step-bounded-slice",
            "candidate = _candidate()\n"
            "candidate[1:4:0] = ()\n"
            + m16_exact_terminal,
        ),
        (
            "m16-dict-copy-rebind",
            "candidate = _candidate()\n"
            "candidate = dict(candidate)\n"
            + m16_exact_mutation
            + "\n"
            + m16_exact_terminal,
        ),
        (
            "m16-union-copy-rebind",
            "candidate = _candidate()\n"
            "candidate = candidate | {}\n"
            + m16_exact_mutation
            + "\n"
            + m16_exact_terminal,
        ),
        (
            "m16-temporary-copy-mutation",
            "candidate = _candidate()\n"
            "temporary = dict(candidate)\n"
            "temporary['commit_close_outcome_addendum']['outcome_matrix'] = "
            "temporary['commit_close_outcome_addendum']['outcome_matrix'][:-1]\n"
            + m16_exact_terminal,
        ),
        (
            "m16-exact-mutation-fresh-validation-candidate",
            "candidate = _candidate()\n"
            + m16_exact_mutation
            + "\n"
            "_expect_violation(_candidate(), "
            "'C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID')",
        ),
        (
            "m16-mutation-removed",
            "candidate = _candidate()\n" + m16_exact_terminal,
        ),
        (
            "m16-diagnostic-changed",
            "candidate = _candidate()\n"
            + m16_exact_mutation
            + "\n"
            "_expect_violation(candidate, 'C2B3A_WRONG_DIAGNOSTIC')",
        ),
        (
            "m16-terminal-removed",
            "candidate = _candidate()\n" + m16_exact_mutation,
        ),
        (
            "m16-terminating-target-expression",
            "candidate = _candidate()\n"
            "(candidate if 1 / 0 else candidate)['unused'] = 0\n"
            + m16_exact_terminal,
        ),
        (
            "m16-terminating-key-expression",
            "candidate = _candidate()\n"
            "candidate[1 / 0] = 0\n"
            + m16_exact_terminal,
        ),
        (
            "m16-terminating-slice-expression",
            "candidate = _candidate()\n"
            "candidate[1 / 0:2] = ()\n"
            + m16_exact_terminal,
        ),
        (
            "m16-terminating-rhs-expression",
            "candidate = _candidate()\n"
            "candidate['unused'] = 1 / 0\n"
            + m16_exact_terminal,
        ),
    )
    for label, body in m16_counterfactual_bodies:
        mutant = _c2b3a_semantic_function_body_mutant(source, m16_name, body)
        physical_rejection(label, mutant)

    for label, inserted in (
        ("linear-candidate-union-rebind", "    candidate = candidate | {}\n"),
        ("linear-candidate-dict-rebind", "    candidate = dict(candidate)\n"),
        ("linear-implicit-division", "    early_termination = 1 / 0\n"),
        ("linear-terminating-target-slice", "    candidate[1 / 0] = 0\n"),
        ("linear-unrelated-call", "    len(candidate)\n"),
        ("linear-second-factory", "    candidate = _candidate()\n"),
    ):
        mutant = _c2b3a_semantic_replace_in_function(
            source,
            m32_name,
            m32_mutation,
            m32_mutation + inserted,
        )
        physical_rejection(label, mutant)

    different_object = _c2b3a_semantic_replace_in_function(
        source,
        m32_name,
        exact_terminal,
        '    _expect_violation({}, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")\n',
    )
    physical_rejection("linear-different-validation-object", different_object)

    tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    m32_function = _c2b3a_oracle_top_level_function(tree, m32_name)
    if m32_function.end_lineno is None:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    lines = source.splitlines(keepends=True)
    missing_m32 = "".join(
        lines[: m32_function.lineno - 1] + lines[m32_function.end_lineno :]
    )
    physical_rejection("inventory-m32-deleted", missing_m32, exact_collection=False)

    m31_body = (
        "candidate = _candidate()\n"
        'candidate["commit_close_outcome_addendum"]["matrix_identity_overlay"]'
        '["same_exact_class_implies_same_object"] = True\n'
        '_expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")'
    )
    m32_body = (
        "candidate = _candidate()\n"
        'candidate["commit_close_outcome_addendum"]["matrix_identity_overlay"]'
        '["diagonal_discriminator"] = "same exact class always selects same_instance"\n'
        '_expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")'
    )
    m33_body = (
        "candidate = _candidate()\n"
        'candidate["commit_close_outcome_addendum"]'
        '["process_control_relational_policy"]["same_instance"]'
        '["selection"] = "always distinct_instance"\n'
        '_expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")'
    )
    duplicate_m31_as_m32 = _c2b3a_semantic_function_body_mutant(
        source,
        m32_name,
        m31_body,
    )
    physical_rejection("inventory-m31-duplicated-as-m32", duplicate_m31_as_m32)

    swapped = _c2b3a_semantic_function_body_mutant(source, m32_name, m33_body)
    swapped = _c2b3a_semantic_function_body_mutant(swapped, m33_name, m32_body)
    physical_rejection("inventory-m32-m33-swapped", swapped)

    duplicate_diagnostic_and_mutation = _c2b3a_semantic_function_body_mutant(
        source,
        m35_name,
        "candidate = _candidate()\n"
        'candidate["commit_close_outcome_addendum"]'
        '["process_control_relational_policy"]["distinct_prelinked"]'
        '["exact_link_preservation_promised"] = True\n'
        '_expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")',
    )
    physical_rejection(
        "inventory-duplicate-diagnostic-and-mutation",
        duplicate_diagnostic_and_mutation,
    )

    fallback_dispatcher = source + (
        "\n@pytest.mark.parametrize('mutant_id', ('M31-fallback', 'M32-fallback'))\n"
        "def test_commit_close_mutant_fallback_dispatcher(mutant_id: str) -> None:\n"
        "    candidate = _candidate()\n"
        "    if mutant_id == 'M31-fallback':\n"
        "        candidate['commit_close_outcome_addendum']['matrix_identity_overlay']"
        "['same_exact_class_implies_same_object'] = True\n"
        "    else:\n"
        "        candidate['commit_close_outcome_addendum']['matrix_identity_overlay']"
        "['diagonal_discriminator'] = 'same exact class always selects same_instance'\n"
        "    _expect_violation(candidate, 'C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID')\n"
    )
    physical_rejection(
        "inventory-fallback-dispatcher",
        fallback_dispatcher,
        exact_collection=False,
    )


@pytest.mark.parametrize(
    "step",
    ("P0", "C1", "C2", "R1", "R2", "R3", "L1", "H1", "H2", "T1", "H3"),
)
def test_c2b3a_semantic_guard_rejects_each_removed_cleanup_step(
    step: str,
    tmp_path: Path,
) -> None:
    source = _c2b3a_bounded_oracle_source()
    mutant = _c2b3a_cleanup_step_removed_mutant(source, step)
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-cleanup-step-" + step,
        mutant,
        "test_post_close_cleanup_reference_model_covers_every_release_point",
    )


def test_c2b3a_semantic_guard_rejects_cleanup_scope_ordering_noops(
    tmp_path: Path,
) -> None:
    source = _c2b3a_bounded_oracle_source()
    cleanup_positive = (
        "test_post_close_cleanup_reference_model_covers_every_release_point"
    )

    P0_admission_retained = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        "        admission_open = False\n",
        "        admission_open = True\n",
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-P0-admission-retained",
        P0_admission_retained,
        cleanup_positive,
    )

    R2_slot_retained = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        "            mutation_slot_owned = False\n",
        "            mutation_slot_owned = True\n",
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-R2-slot-retained",
        R2_slot_retained,
        cleanup_positive,
    )

    R3_binding_retained = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        "            database_binding_owned = False\n",
        "            database_binding_owned = True\n",
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-R3-binding-retained",
        R3_binding_retained,
        cleanup_positive,
    )

    missing_cleanup_outcome_input = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        "    cleanup_outcome: str,\n",
        "",
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-cleanup-outcome-input-removed",
        missing_cleanup_outcome_input,
        cleanup_positive,
    )

    primary_precedence_removed = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        '        if earlier_primary != "none":\n',
        '        if earlier_primary == "none":\n',
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-active-primary-precedence-removed",
        primary_precedence_removed,
        cleanup_positive,
    )

    primary_dropped_at_X = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        "    if not finalizer:\n"
        '        if earlier_primary != "none":\n',
        "    if halted and not finalizer:\n"
        '        if earlier_primary != "none":\n',
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-primary-dropped-on-successful-X",
        primary_dropped_at_X,
        cleanup_positive,
    )

    cleanup_selected_over_primary = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        "    if not finalizer:\n"
        '        if earlier_primary != "none":\n'
        '            selected_outward = "commit_" + earlier_primary\n'
        "        elif halted and effective_cleanup_outcome in (\n"
        '            "KeyboardInterrupt",\n'
        '            "SystemExit",\n'
        '            "GeneratorExit",\n'
        "        ):\n"
        '            selected_outward = "cleanup_" + effective_cleanup_outcome\n',
        "    if not finalizer:\n"
        "        if halted and effective_cleanup_outcome in (\n"
        '            "KeyboardInterrupt",\n'
        '            "SystemExit",\n'
        '            "GeneratorExit",\n'
        "        ):\n"
        '            selected_outward = "cleanup_" + effective_cleanup_outcome\n'
        '        elif earlier_primary != "none":\n'
        '            selected_outward = "commit_" + earlier_primary\n',
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-cleanup-primary-selected-over-commit-primary",
        cleanup_selected_over_primary,
        cleanup_positive,
    )

    primary_suppressed_outside_finalizer = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        '        if earlier_primary != "none":\n',
        '        if halted and earlier_primary != "none":\n',
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-primary-suppressed-outside-finalizer",
        primary_suppressed_outside_finalizer,
        cleanup_positive,
    )

    finalizer_propagates_primary = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        "    if not finalizer:\n",
        '    if not finalizer or earlier_primary != "none":\n',
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-finalizer-propagates-primary",
        finalizer_propagates_primary,
        cleanup_positive,
    )

    closure_proved_pending_with_custody = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        "                connection_owned = False\n",
        "                connection_owned = True\n",
    )
    closure_proved_pending_with_custody = _c2b3a_semantic_replace_in_function(
        closure_proved_pending_with_custody,
        "_cleanup_reference",
        '                state = "PU" if initial_state == "QU" else "PK"\n',
        "                state = initial_state\n",
    )
    closure_proved_pending_with_custody = _c2b3a_semantic_replace_in_function(
        closure_proved_pending_with_custody,
        "_cleanup_reference",
        "    assert not (\n"
        "        connection_closed_proved\n"
        '        and (state in ("QU", "QK") or connection_owned)\n'
        "    )\n"
        '    assert not (state in ("PU", "PK") and connection_owned)\n',
        "    assert True\n    assert True\n",
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-closure-proved-QU-QK-with-custody",
        closure_proved_pending_with_custody,
        cleanup_positive,
    )

    proved_state_with_custody = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        "                connection_owned = False\n",
        "                connection_owned = True\n",
    )
    proved_state_with_custody = _c2b3a_semantic_replace_in_function(
        proved_state_with_custody,
        "_cleanup_reference",
        "    assert not (\n"
        "        connection_closed_proved\n"
        '        and (state in ("QU", "QK") or connection_owned)\n'
        "    )\n"
        '    assert not (state in ("PU", "PK") and connection_owned)\n',
        "    assert True\n    assert True\n",
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-PU-PK-with-custody",
        proved_state_with_custody,
        cleanup_positive,
    )

    X_before_release = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        '                writer_lock_release = "release_proved"\n'
        '                completed += ("L1",)\n',
        '                state = "X"\n'
        '                writer_lock_release = "release_proved"\n'
        '                completed += ("L1",)\n',
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-X-before-release-proof",
        X_before_release,
        cleanup_positive,
    )

    registry_before_terminal = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        "            authority_lock_terminal = True\n"
        '            if fault_step == "H2" and fault_position == "between":\n',
        "            authority_lock_registry_present = False\n"
        "            authority_lock_terminal = True\n"
        '            if fault_step == "H2" and fault_position == "between":\n',
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-authority-registry-before-terminal",
        registry_before_terminal,
        cleanup_positive,
    )

    A_to_X_erased = _c2b3a_semantic_replace_in_function(
        source,
        "_cleanup_reference",
        '            state = "A-closing"\n',
        "            halted = True\n",
    )
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-A-to-X-erased",
        A_to_X_erased,
        cleanup_positive,
    )

    if source.count('"expected_actual_write_paths": 27') != 3:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    if source.count('"maximum_paths": 28') != 3:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    stale_scope = source.replace(
        '"expected_actual_write_paths": 27',
        '"expected_actual_write_paths": 23',
        1,
    ).replace('"maximum_paths": 28', '"maximum_paths": 24', 1)
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-scope-23-24",
        stale_scope,
        "test_commit_close_addendum_custody_recovery_and_scope_are_exact",
    )

    supersession_removed = source.replace(
        '"classification": "historical and non-operative for C2B3B after this addendum"',
        '"classification": "active authority for C2B3B"',
        1,
    )
    if supersession_removed == source:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-scope-supersession-removed",
        supersession_removed,
        "test_commit_close_addendum_custody_recovery_and_scope_are_exact",
    )

    historical_scope_reactivated = source.replace(
        '"old_values_may_be_used_as_active_authority": False',
        '"old_values_may_be_used_as_active_authority": True',
        1,
    )
    if historical_scope_reactivated == source:
        raise AssertionError("C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID")
    _assert_c2b3a_semantic_mutant_is_physical(
        tmp_path,
        "semantic-historical-scope-reactivated",
        historical_scope_reactivated,
        "test_commit_close_addendum_custody_recovery_and_scope_are_exact",
    )


def test_c2b3a_strict_legal_protected_load_site_allowlist_is_exact() -> None:
    source = _c2b3a_bounded_oracle_source()
    tree = ast.parse(source, filename=C2B3A_ORACLE_PATH.name)
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    observed = _c2b3a_oracle_protected_load_sites(tree, parents)
    assert observed == _c2b3a_oracle_expected_protected_load_sites()
    assert len(observed) == 525
    assert (
        sum(record[3] == "direct_call_func" for record in observed),
        sum(record[3] == "direct_candidate_argument" for record in observed),
        sum(record[3] == "direct_comparison_operand" for record in observed),
        sum(record[3] == "direct_assert_operand" for record in observed),
        sum(record[3] is None for record in observed),
    ) == (429, 36, 39, 0, 21)
    assert tuple(C2B3A_ORACLE_LEGAL_LOAD_SITE_FIELDS) == (
        "protected_name",
        "enclosing_top_level_function",
        "enclosing_nested_function",
        "load_role",
        "ancestor_kind_chain",
        "ordinal",
    )
    assert all(
        record[3]
        in {
            "direct_call_func",
            "direct_comparison_operand",
            "direct_assert_operand",
            "direct_candidate_argument",
            None,
        }
        for record in observed
    )


def test_c2b3a_dedicated_oracle_physically_imports_collects_and_executes(
    tmp_path: Path,
) -> None:
    import_tmp = tmp_path / "physical-import-tmp"
    import_pycache = tmp_path / "physical-import-pycache"
    collect_tmp = tmp_path / "physical-collect-tmp"
    collect_pycache = tmp_path / "physical-collect-pycache"
    execute_tmp = tmp_path / "physical-execute-tmp"
    execute_pycache = tmp_path / "physical-execute-pycache"
    collect_basetemp = tmp_path / "physical-collect-basetemp"
    execute_basetemp = tmp_path / "physical-execute-basetemp"
    for directory in (
        import_tmp,
        import_pycache,
        collect_tmp,
        collect_pycache,
        execute_tmp,
        execute_pycache,
    ):
        directory.mkdir(mode=0o700)

    import_environment = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONPYCACHEPREFIX": str(import_pycache),
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "TMPDIR": str(import_tmp),
    }
    import_program = (
        "import importlib.util,pathlib,sys; "
        "path=pathlib.Path(sys.argv[1]).resolve(strict=True); "
        "spec=importlib.util.spec_from_file_location('c2b3a_physical_oracle',path); "
        "module=importlib.util.module_from_spec(spec); "
        "sys.modules[spec.name]=module; "
        "spec.loader.exec_module(module); "
        "assert module.TEST_PATH == path"
    )
    imported = subprocess.run(
        (sys.executable, "-B", "-c", import_program, str(C2B3A_ORACLE_PATH)),
        cwd=ROOT,
        env=import_environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert imported.returncode == 0, imported.stderr
    assert imported.stdout == ""
    assert imported.stderr == ""

    collect_environment = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONPYCACHEPREFIX": str(collect_pycache),
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "TMPDIR": str(collect_tmp),
    }
    collected = subprocess.run(
        (
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            f"--basetemp={collect_basetemp}",
            "--collect-only",
            "-q",
            str(C2B3A_ORACLE_PATH),
        ),
        cwd=ROOT,
        env=collect_environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert collected.returncode == 0, collected.stderr
    node_prefix = "tests/test_c2b3_program_initialization_contract.py::"
    collected_nodes = tuple(
        line[len(node_prefix) :]
        for line in collected.stdout.splitlines()
        if line.startswith(node_prefix)
    )
    assert collected_nodes == C2B3A_ORACLE_EXPECTED_TEST_NODE_NAMES
    assert (
        f"{len(C2B3A_ORACLE_EXPECTED_TEST_NODE_NAMES)} tests collected"
        in collected.stdout
    )
    assert collected.stderr == ""

    execute_environment = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONPYCACHEPREFIX": str(execute_pycache),
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "TMPDIR": str(execute_tmp),
    }
    executed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            f"--basetemp={execute_basetemp}",
            "-vv",
            "--tb=no",
            str(C2B3A_ORACLE_PATH),
        ),
        cwd=ROOT,
        env=execute_environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert executed.returncode == 0, executed.stderr
    executed_nodes = tuple(
        line[len(node_prefix) :].split(" PASSED", 1)[0]
        for line in executed.stdout.splitlines()
        if line.startswith(node_prefix) and " PASSED" in line
    )
    assert executed_nodes == C2B3A_ORACLE_EXPECTED_TEST_NODE_NAMES
    assert f"{len(C2B3A_ORACLE_EXPECTED_TEST_NODE_NAMES)} passed" in executed.stdout
    assert " skipped" not in executed.stdout
    assert " xfailed" not in executed.stdout
    assert " deselected" not in executed.stdout
    assert " warning" not in executed.stdout.lower()
    assert executed.stderr == ""


@pytest.mark.parametrize(
    ("mutant_id", "snippet", "position"),
    (
        (
            "R01",
            "\nR01_ALIAS = {'contract': EXPECTED_INITIALIZATION_CONTRACT}\n",
            "before-tests",
        ),
        (
            "R02",
            "\nR02_ALIAS = {'vector': (EXPECTED_INITIALIZATION_GOLDEN_VECTOR,)}\n",
            "before-tests",
        ),
        (
            "R03",
            "\nR03_VALUES = [EXPECTED_INITIALIZATION_CONTRACT]\n",
            "before-tests",
        ),
        (
            "R04",
            "\nR04_VALUES = {'nested': ({'vector': EXPECTED_INITIALIZATION_GOLDEN_VECTOR},)}\n",
            "before-tests",
        ),
        (
            "R05",
            "\nfor r05_alias in (EXPECTED_INITIALIZATION_CONTRACT,):\n    pass\n",
            "before-tests",
        ),
        (
            "R06",
            "\nR06_VALUES = (r06_alias for r06_alias in (EXPECTED_INITIALIZATION_GOLDEN_VECTOR,))\n",
            "before-tests",
        ),
        (
            "R07",
            "\nR07_VALUE = EXPECTED_INITIALIZATION_CONTRACT if True else {}\n",
            "before-tests",
        ),
        (
            "R08",
            "\nR08_VALUE = repr(EXPECTED_INITIALIZATION_GOLDEN_VECTOR)\n",
            "before-tests",
        ),
        (
            "R09",
            "\nR09_VALUE = (r09_alias := EXPECTED_INITIALIZATION_CONTRACT)\n",
            "before-tests",
        ),
        (
            "R10",
            "\nR10_VALUE: object = EXPECTED_INITIALIZATION_GOLDEN_VECTOR\n",
            "before-tests",
        ),
        (
            "R11",
            "\ndef _r11(value=EXPECTED_INITIALIZATION_CONTRACT):\n    return value\n",
            "before-tests",
        ),
        (
            "R12",
            "\ndef _r12():\n    captured = EXPECTED_INITIALIZATION_GOLDEN_VECTOR\n    def nested():\n        return captured\n    return nested\n",
            "before-tests",
        ),
        (
            "R13",
            "\nR13_VALUES = []\nR13_VALUES += [EXPECTED_INITIALIZATION_CONTRACT]\n",
            "before-tests",
        ),
        (
            "R14",
            "\nmoved = []\nmoved.append(EXPECTED_INITIALIZATION_GOLDEN_VECTOR)\n",
            "before-tests",
        ),
        (
            "R15",
            "\nnames = []\nnames.extend((EXPECTED_INITIALIZATION_CONTRACT,))\n",
            "before-tests",
        ),
        (
            "R16",
            "\nmoved = []\nmoved.append(_validate_contract)\n",
            "before-tests",
        ),
        (
            "R17",
            "\nnames = []\nnames.extend((_validate_contract,))\n",
            "before-tests",
        ),
        (
            "R18",
            "\nmoved = []\nmoved += [_validate_contract]\n",
            "before-tests",
        ),
        (
            "R19",
            "\nR19_CALLABLES = {}\nR19_CALLABLES['contract'] = _validate_contract\n",
            "before-tests",
        ),
        (
            "R20",
            "\nR20_CALLABLES = tuple((_validate_contract,))\n",
            "before-tests",
        ),
        (
            "R21",
            "\ndef _r21():\n    for r21_callable in (_validate_contract,):\n        r21_callable({})\n",
            "before-tests",
        ),
        (
            "R22",
            "\ndef _r22():\n    return tuple(r22_callable({}) for r22_callable in (_validate_contract,))\n",
            "before-tests",
        ),
        (
            "R23",
            "\ndef _r23():\n    r23_callables = {'contract': _validate_contract}\n    return r23_callables['contract']({})\n",
            "before-tests",
        ),
        (
            "R24",
            "\nclass R24Holder:\n    callable = _validate_contract\n",
            "before-tests",
        ),
        (
            "R25",
            "\ndef _r25():\n    callable_value = _validate_contract\n    return callable_value.__call__({})\n",
            "before-tests",
        ),
        (
            "R26",
            "\nif False:\n    EXPECTED_INITIALIZATION_CONTRACT = _owner_contract()\n",
            "before-tests",
        ),
        (
            "R27",
            "\nif False:\n    EXPECTED_INITIALIZATION_CONTRACT = {'planning': _read_allowed_text(PLANNING_PATH)}\n",
            "before-tests",
        ),
        (
            "R28",
            "\nif False:\n    EXPECTED_INITIALIZATION_GOLDEN_VECTOR = _owner_golden_vector()\n",
            "before-tests",
        ),
        (
            "R29",
            "\nif False:\n    EXPECTED_INITIALIZATION_GOLDEN_VECTOR = {'planning': _read_allowed_text(PLANNING_PATH)}\n",
            "before-tests",
        ),
        (
            "R30",
            "\nif False:\n    EXPECTED_INITIALIZATION_CONTRACT = _owner_contract() or EXPECTED_INITIALIZATION_CONTRACT\n",
            "before-tests",
        ),
        ("R31", "\nif False:\n    __test__ = False\n", "tail"),
        ("R32", "\nif False:\n    pytestmark = pytest.mark.skip\n", "tail"),
        ("R33", "\nif False:\n    pytestmark = pytest.mark.xfail\n", "tail"),
        (
            "R34",
            "\nif False:\n    pytest.skip('suppressed', allow_module_level=True)\n",
            "tail",
        ),
        (
            "R35",
            "\nif False:\n    del test_nonimplementation_surface_is_closed\n",
            "tail",
        ),
        (
            "R36",
            "\nif False:\n    def test_r36_conditionally_defined():\n        pass\n",
            "before-tests",
        ),
    ),
    ids=(
        "R01",
        "R02",
        "R03",
        "R04",
        "R05",
        "R06",
        "R07",
        "R08",
        "R09",
        "R10",
        "R11",
        "R12",
        "R13",
        "R14",
        "R15",
        "R16",
        "R17",
        "R18",
        "R19",
        "R20",
        "R21",
        "R22",
        "R23",
        "R24",
        "R25",
        "R26",
        "R27",
        "R28",
        "R29",
        "R30",
        "R31",
        "R32",
        "R33",
        "R34",
        "R35",
        "R36",
    ),
)
def test_c2b3a_strict_oracle_provenance_rejects_r01_through_r36(
    mutant_id: str,
    snippet: str,
    position: str,
    tmp_path: Path,
) -> None:
    source = _c2b3a_bounded_oracle_source()
    if position == "before-tests":
        insertion = "\ndef test_owner_literal_equals_independent_expected_contract"
        assert insertion in source
        mutant = source.replace(insertion, snippet + insertion, 1)
    else:
        mutant = source + snippet
    ast.parse(mutant, filename=mutant_id)
    _c2b3a_physically_import_and_collect_mutant(
        tmp_path,
        mutant_id,
        mutant,
    )
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_independent_oracle_architecture(mutant)
    assert str(exc_info.value) == "C2B3A_INDEPENDENT_ORACLE_ARCHITECTURE_INVALID"


def _c2b3a_planning_mutant_at_position(
    text: str,
    claim: str,
    position: str,
) -> str:
    if position == "prelude":
        return text.replace(
            "# C2B3 Program Initialization\n",
            "# C2B3 Program Initialization\n\n" + claim + "\n",
            1,
        )
    if position == "middle":
        return text.replace(
            "<!-- C2B3A_PLANNING_CURRENT_STATUS_BEGIN -->",
            claim + "\n\n<!-- C2B3A_PLANNING_CURRENT_STATUS_BEGIN -->",
            1,
        )
    if position == "after-source-layout":
        return text.replace(
            "<!-- C2B3A_PLANNING_PRODUCTION_NONIMPLEMENTATION_BEGIN -->",
            claim
            + "\n\n<!-- C2B3A_PLANNING_PRODUCTION_NONIMPLEMENTATION_BEGIN -->",
            1,
        )
    assert position == "tail"
    return text.rstrip("\n") + "\n\n" + claim + "\n"


def test_c2b3a_planning_status_baseline_scans_complete_document() -> None:
    planning = C2B3A_PLANNING_PATH.read_text(encoding="utf-8")
    _assert_c2b3a_planning_status(planning)


@pytest.mark.parametrize(
    "position",
    ("prelude", "middle", "after-source-layout", "tail"),
)
@pytest.mark.parametrize(
    "claim",
    (
        "The planning document is semantic authority.",
        "The planning document co-owns semantic truth.",
        "Program initialization source is current.",
        "Program initialization is implemented.",
        "Private delegation is current.",
        "Receipt persistence is current.",
        "Replay runtime is current.",
        "Recovery runtime is current.",
        "Author-effect source is current.",
        "One extra path is allowed.",
        "The next path requires reassessment.",
        "The earlier manifest governs C2B3B.",
        "The implementation is limited to the earlier manifest.",
        "The expected path count is 23 and the maximum is 24.",
    ),
)
def test_c2b3a_planning_additive_status_contradictions_are_rejected_everywhere(
    claim: str,
    position: str,
) -> None:
    planning = C2B3A_PLANNING_PATH.read_text(encoding="utf-8")
    mutant = _c2b3a_planning_mutant_at_position(planning, claim, position)
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_planning_status(mutant)
    assert str(exc_info.value) == "C2B3A_PLANNING_PROJECTION_INVALID"


@pytest.mark.parametrize("marker", ("```", "~~~"))
def test_c2b3a_planning_fenced_outside_projection_claim_is_rejected(
    marker: str,
) -> None:
    planning = C2B3A_PLANNING_PATH.read_text(encoding="utf-8")
    fenced = marker + "text\nAuthor-effect source is current.\n" + marker
    mutant = _c2b3a_planning_mutant_at_position(planning, fenced, "middle")
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_planning_status(mutant)
    assert str(exc_info.value) == "C2B3A_PLANNING_PROJECTION_INVALID"


def test_c2b3a_planning_unclosed_and_pseudo_fences_are_bounded() -> None:
    planning = C2B3A_PLANNING_PATH.read_text(encoding="utf-8")
    unclosed = _c2b3a_planning_mutant_at_position(
        planning,
        "```text\nAuthor-effect source is current.",
        "tail",
    )
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_planning_status(unclosed)
    assert str(exc_info.value) == "C2B3A_PLANNING_PROJECTION_INVALID"

    fenced = (
        "```text\n"
        "``` text-bearing pseudo-closer\n"
        "> - Author-effect source is current.\n"
        "```"
    )
    pseudo_closer = _c2b3a_planning_mutant_at_position(
        planning,
        fenced,
        "middle",
    )
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_planning_status(pseudo_closer)
    assert str(exc_info.value) == "C2B3A_PLANNING_PROJECTION_INVALID"


def test_c2b3a_planning_markdown_prefixes_do_not_hide_claims() -> None:
    planning = C2B3A_PLANNING_PATH.read_text(encoding="utf-8")
    mutant = _c2b3a_planning_mutant_at_position(
        planning,
        "> - Author-effect\t source   is current.",
        "tail",
    )
    with pytest.raises(AssertionError) as exc_info:
        _assert_c2b3a_planning_status(mutant)
    assert str(exc_info.value) == "C2B3A_PLANNING_PROJECTION_INVALID"


NARROWED_RESET_BEGIN_MARKER = "<!-- C2B3_NARROWED_RESET_CONTRACT_PYTHON_BEGIN -->"
NARROWED_RESET_END_MARKER = "<!-- C2B3_NARROWED_RESET_CONTRACT_PYTHON_END -->"
EXPECTED_NARROWED_RESET_TRAILING_PROSE = (
    "\n\nThis addendum has higher precedence only for the finite paths named in\n"
    "`finite_supersession.supersedes_only`. Every other committed C2B3A semantic,\n"
    "including its transaction and cleanup authority, remains operative. Open\n"
    "questions in the deferral ledger must be resolved immediately before the phase\n"
    "that needs them and require a separately authorized source tranche and fresh\n"
    "independent audit.\n"
)

VS1A_BEGIN_MARKER = "<!-- C2B_PRE_IO_VS1A_SHARED_CLEANUP_CONTRACT_PYTHON_BEGIN -->"
VS1A_END_MARKER = "<!-- C2B_PRE_IO_VS1A_SHARED_CLEANUP_CONTRACT_PYTHON_END -->"
EXPECTED_VS1A_PATHS = (
    ".docs/c2b-durable-development-state.md",
    ".docs/c2b3-program-initialization.md",
    ".docs/sqlite-operations-and-recovery.md",
    ".docs/sqlite-threat-model.md",
    ".docs/writer-session-authority.md",
    "AGENTS.md",
    "README.md",
    "src/ge_nwp_coordinator/sqlite_connection.py",
    "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
    "src/ge_nwp_coordinator/sqlite_writer_session.py",
    "src/ge_nwp_coordinator/state_authority_lock.py",
    "tests/test_b3c1a_writer_session_authority.py",
    "tests/test_b3c1b_rollback_only_writer_fencing.py",
    "tests/test_b3c3_rollback_only_transition_dry_run.py",
    "tests/test_b3c4b_private_atomic_transition_persistence.py",
    "tests/test_b3c4c_prerequisite_contract.py",
    "tests/test_b4b_private_atomic_global_stop_persistence.py",
    "tests/test_c2b0_durable_state_contract.py",
    "tests/test_c2b3_program_initialization_contract.py",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py",
    "tests/test_sqlite_b2c_writer_session.py",
    "tests/test_state_authority_lock.py",
)
EXPECTED_VS1A_TRAILING_PROSE = """

The controller constructs one private connection scope before publishing any
resource controller-resolution state. That scope is the sole active connection
custodian. The resource acknowledges the exact scope token before COMMIT can
begin. The controller later supplies only immutable intent and close-proof or
retained-custody facts. Under the existing resource condition lock, the resource
revalidates the token, operation, slot, proof or custody, and current disposal
posture; merges cleanup-wins policy; constructs the actual successor; and
publishes it at one exact lifecycle-state assignment. The controller never
precomputes that actual successor. Only after the exact publication
acknowledgment returns may the scope clear its raw and retained aliases. The
resource assignment itself invalidates scope use, so a stale scope cannot
borrow, commit, rollback, close, or publish even if acknowledgment delivery is
interrupted.

C1/C2 proof is connection-free and arises only when `close()` returns normally
for the exact retained connection on its exact owner process and Thread object.
An ordinary failure or process-control interruption before that return creates
no proof. While proof remains absent, cleanup may later repeat `close()` on
that same object. Once C2 exists, no further close is permitted. No
`in_transaction`, `ProgrammingError`, exception-text, SQL, reopen, or
reconstruction probe supplies closure proof. The retained-custody owner itself
calls `sqlite3.Connection.close(exact_connection)`; the generic transaction
cleanup helper is not a proof owner, no caller-supplied successful callback may
mint proof, and the production proof has one exact construction site.

Pre-close policy is not a lifecycle result. Resume-if-close-proved-and-still-
eligible may strengthen only to cleanup-required. Field-free `ResumeActive` is
constructed only after exact close proof and only while the resource lock still
finds resumption eligible. Explicit disposal before publication strengthens the
policy; disposal after proof publication atomically replaces resumption with
proof-backed cleanup. Disposal after exact mutation release but before operation
completion likewise makes proof-backed cleanup current while preserving the
outstanding exact operation until completion. Operation or mutation completion
cannot restore Active after disposal. `ContinueCleanup` is always
non-admitting.

For exact `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`, the original
object, args, identity, and `SystemExit.code` retain outward precedence. Each
retained public caller obtains one private immutable invocation-correlation
token from its exact resource before calling the helper that can admit an
operation. Admission validates that resource/PID/epoch binding, rejects a token
already bound to a represented operation, and publishes the token-bearing exact
handle only through the immutable resource-owned operation record in the same
condition-protected lifecycle assignment. The caller never derives correlation
from the returned lease or a post-return handle capture. The token is ephemeral
identity only: it cannot admit, mutate, retire, publish, replay, or authorize;
it is not persisted, serialized, logged, exported, or registered.

On governing process control, the resource checks only the token's exact type,
directly stored resource identity, and the direct fork-invalid owner-PID
sentinel before taking its condition. It then
directly inspects the exact current lifecycle-state type and exact immutable
operation-record tuple. Direct frozen/slotted field access, exact type checks,
and token-object identity are the only selection operations. It reads no
lifecycle property and calls no project or policy helper. One exact current
match is followed immediately by direct poison assignment under the condition.
Only after poison may `_state_authority` derive authority and validate PID,
epoch, resource, correlation, record, and handle consistency. A consistency
failure leaves poison set and admission denied. Only a represented record
causes poison, while an absent current record proves neither no admission nor
final assignment. Classification, detailed record replacement, successor
construction, and notification occur only after poison and cannot reset it. A
controller-resolution state carrying `_CleanupRequiredAfterResolution` is
represented cleanup-owned; represented pre-final-assignment work without an
existing cleanup owner is represented incomplete.

After the bounded stabilization attempt, the public envelope runs a bounded,
cycle-aware sanitizer over the supported graph: the governing exception's and
reachable exceptions' `BaseException` base traceback, cause, context, args, and
base instance dictionary; `BaseExceptionGroup` base children; and
`BaseException` values recursively reached through exact built-in `tuple`,
`list`, `dict`, `set`, and `frozenset` containers. It invokes bound base-class
descriptors and bound exact built-in operations, clearing an exception's base
traceback before reading its other base fields. It does not invoke subclass
dynamic descriptors, arbitrary subclass slots, arbitrary user-object
attributes, or custom container iteration. It preserves exact object and
cause/context/group-child identity, type, args, `SystemExit.code`, suppression,
notes, and instance-dictionary content. One ordinary failure in the primary
traversal or at its call boundary is contained and followed by one independently
bound non-dispatching fallback; the original exception remains outward and is
bare-reraised. No Coordinator traceback frame remains in the supported outward
exception graph. Repeated asynchronous interruption, catastrophic allocation
failure, and unsupported private mutation of bound defaults or C-level
descriptors remain outside the guarantee.
The resource lifecycle state, not handle-local compatibility fields, remains
the operation authority. This is an ordinary Python private-object boundary,
not a claim of cryptographic resistance to arbitrary private reflection.

Phase 1 records preparation under the existing resource condition, retains the
operation record, verifies exact mutation release, and makes or keeps the
resource non-admitting. Normal retirement has exactly one owner: the live lease
already named by that record. While holding the same condition, the resource
checks the exact record, lease, handle, finalizer, PID, epoch, preparation,
mutation-release, and cleanup posture; records exact local terminality; invokes
`detach()` on that exact admission-bound finalizer; and accepts only the
successful result returned by that call. Only after that result does a complete
lifecycle-state replacement record `EXPLICIT_RETIRED`. A merely dead finalizer,
`alive == False`, a cleared weakref, or a caller-built acknowledgment is never
normal-retirement evidence.

Operation-finalizer execution, direct finalizer invocation, and lease loss
before `EXPLICIT_RETIRED` are abnormal-loss signals. They classify the record as
orphaned and cleanup-required, freeze admission, and enter the existing cleanup
continuation. Cleanup may remove the orphan and reach X without a live lease or
live finalizer; it never restores Active for that operation. The exact weakref
callback is an immediate cleanup caller, and explicit session/resource close or
the existing session finalizer can make the same progress. The active-resource
registry remains only the existing fork/lifetime registry, not a retry scanner.
If lease loss occurs after the resource already recorded `EXPLICIT_RETIRED`, the
loss adds no fact: the stored phase may finish the already-authorized final
publication, or current disposal may select cleanup.

Final normal publication requires the exact represented resource record,
preparation identity, `EXPLICIT_RETIRED` phase, exact mutation-release posture,
and absence of cleanup-required disposition. It does not reconstruct success
from weakref or finalizer state and does not consult handle-carried binding
fields. Phase 2 selects the complete successor under the same condition. For a
claimed sole operation, credential and lock cleanup precede the final assignment.
The one `self._lifecycle_state = final_successor` assignment remains the
operation-completion linearization point; Python return is only caller
observation. Absent handles still reject, and postassignment response loss stays
within transition/global-stop replay and conflict semantics. No completion
receipt, second registry, scanner, queue, background service, or new global lock
is introduced.

The rejected broad optional lifecycle snapshot is absent. Exact closed variants
make prohibited combinations unconstructible: QU/QK contain the exact retained
connection and slot; PU/PK contain a close proof and no connection; active-idle
operation or slot states are invalid; and X contains no authority, operation,
slot, claim, connection, proof, or cursor. Finite structural cursors encode
R1/R2/R3/L1/H1/H2/T1 consequences. There is no generic completed-step set from
which removed custody could be reconstructed. Authority and operations live in
one activity value; the mutation slot lives in one mutation frame and then its
slot-bearing cursor; resolution, custody/proof, cursor, claim, binding/lock, and
terminal facts likewise each have one structural owner. Cross-wired authority,
operation record, slot, token, retained custody, proof, cursor, or claim values
are rejected by one exact private resource identity. Each writer resource allocates
one opaque identity. Every live lifecycle component carries that same object
directly or through its structural owner, and every authority comparison uses
`is`. It is not persistent, serializable, registered globally, exported,
rendered as evidence, or included in safe errors. PID, lifecycle epoch,
operation number, and value equality remain insufficient.

Each operation handle, lease, exact finalizer, lease-loss weakref callback, and
immutable resource record is constructed before active publication.
Construction or publication failure unwinds the never-published values. A
callback for a never-published handle is a non-authoritative no-op. An absent
record always rejects publication; handle-local history cannot prove prior
linearization. Preparation precedes resource-recorded local terminality, the
exact successful detach precedes `EXPLICIT_RETIRED`, and that resource phase
precedes the final assignment. After successful detach but before assignment,
the live explicit lease may retry; if the lease disappears, its weakref callback
may finish only because `EXPLICIT_RETIRED` is already stored. Before successful
detach, operation or lease loss belongs only to cleanup. The retained wrapper,
explicit resource close, and session finalizer remain bounded cleanup callers.
A fork child cannot complete or clean a parent operation or resource.

A cleanup claim binds one weak reference to the exact `threading.Thread`
object, resource identity, process, lifecycle epoch, and claim epoch. Its
claimed wrapper, rather than duplicate identity or cursor fields, owns the
pending state. The exact live owner may resume; another live
Thread may not. If the weak reference is dead or the Thread is no longer alive,
an explicit takeover creates a new token and newer epoch. Reuse of a numeric
thread identifier grants no authority. If exact thread-affine connection
custody can no longer perform close, the state remains truthfully unproved.

Ordinary safe-error traceback privacy uses the same supported base-storage
boundary and one-ordinary-failure containment through the genuine bound
transition and global-stop operation guards. Prohibited identities must not
occur through any reached base traceback, cause, context, base exception-group
child, args, base instance dictionary, or recursive exact built-in `tuple`,
`list`, `dict`, `set`, and `frozenset` container. The guarantee does not invoke
subclass dynamic descriptors or custom iterators and does not traverse
arbitrary subclass slots or user-object attributes. Separate transition and
global-stop cursor-producing faults
target their exact idempotency SELECTs. The tests capture and really close the
exact built-in cursor, database `Path` and resolved string, SQL, parameter
tuple, and every parameter string, and exclude them by identity and exact
built-in value. Sensitive transaction frames return a connection-free safe
disposition carrying the one exact content-free `SQLiteMutationStoreError`
created for that failure occurrence. Outer bindings are cleared before the same
object becomes active in the outer public catch, is sanitized in place, and is
bare-reraised by identity; no second store error is reconstructed at the public
boundary. Subclassed, malformed, noted, or content-bearing
candidates fail closed to a fresh content-free integrity error. Raw governing
process-control exceptions remain outside the safe-disposition path. Their
exact identity remains primary, but after exact-token lifecycle stabilization
every supported reachable traceback is cleared before bare re-raise so no
Coordinator-owned frame can retain an operation lease or record, correlation token, session/resource,
command or decision, credential/lock, SQLite connection/cursor/path/SQL/
parameters, or private result payload. Real underlying-COMMIT probes for
transition and global stop retain exactly one durable event and recover only
through later exact replay.

After commit uncertainty, a normal close of the transaction connection with no
pending explicit disposal or orphan cleanup selects `ResumeActive`. Completion of
the mutation and operation releases restores the same concrete writer-session
resource to its valid active variant without connection, scope, proof, slot, or
cleanup-claim residue. A later explicit call on that same wrapper uses a new
operation lease and fresh transaction connection: a definitely absent commit
is applied fresh, while an underlying commit is returned only as exact
idempotency replay. Transition and global-stop retries perform no duplicate
event, sequence, CAS, current-state, or receipt effect, and the original public
call never retries automatically. The same explicit fresh/replay/conflict rule
resolves caller response loss after operation linearization; transition and
global-stop response-loss selectors prove one durable event and exact replay,
with changed-digest conflict and no duplicate effect. QU/QK retained-connection custody, pending
explicit disposal or orphan cleanup, and governing process-control cleanup remain
non-reusable and continue monotonically toward X. The future C2B3
initialization-recovery rule remains separately Section-35 governed and X-gated;
it is not a fresh-session rule for existing transition or global-stop replay.

The change in `tests/test_b3c1b_rollback_only_writer_fencing.py` is test-resource
lifetime hygiene only. Every directly test-owned SQLite connection now has an
explicit close after its preserved commit or rollback boundary; fault-injection
setup retains local ownership through all throwing steps and closes the exact
connection on any `BaseException` before bare-reraising it. An immediately
installed, identity-scoped, idempotent, nonthrowing ledger cleanup covers
expected-error mismatches and assertion exits, clears synthetic close faults,
and explicitly closes genuinely unproved connections. Helper-level failure
replacements perform the real close first where closure is meant to be proved.
No warning filter or suppression is used, and rollback-only fencing, error
precedence, mutation-slot behavior, and safe-error vocabulary are unchanged.

The change in
`tests/test_b3c3_rollback_only_transition_dry_run.py` is a private rollback-only
regression adaptation to the selected close-proof owner, with no B3c3 result,
durability, public, or authority widening. It instruments and delegates to the
sealed retained-custody proof owner rather than patching the generic
`_close_connection` cleanup helper. Ordinary rollback-only ordering and the
non-persisted dry-run result remain unchanged. A close-unproved failure retains
the exact governed connection and mutation slot until later explicit cleanup;
it does not falsely release custody. B3c3 gains no COMMIT, commit-unknown
result, mutation SQL, sequence allocation, CAS, or durable event. Its owning
documentation remains unchanged.

The unchanged B2b lock-integration issue is recorded only as: pre-existing
HEAD-exact test-resource hygiene; strict warning-promotion debt; not repaired by
VS1A; not VS1A authority or semantic behavior. It is not part of the changed-
path inventory, and no warning suppression is added.

Section 35's L1/H1/H2/T1/H3 meanings, existing transition/global-stop apply and
replay, QK/QU truth, rollback-only behavior, public delegation, lock boundary,
fork rules, and finalizer posture remain unchanged. Program initialization and
development durable-row mutation remain absent; VS1B remains unauthorized.
Independent audit acceptance, staging, commit, push, and publication have not
occurred.
"""

EXPECTED_NARROWED_SUPERSEDES_ONLY = (
    "owner_decisions.planned_adapter_kind as initialization route selection",
    "later_author_effect_owner_decisions.planned_adapter_kind for the first delivery",
    "later_author_effect_owner_decisions.direct_local_bootstrap_selected for the first delivery",
    "direct_local_first_productive_acceptance as the required durable representation",
    "horizontal C2B3B/C2B4/C2B5/C2B6 order as implementation order",
    "future C2B3B path-count manifests as implementation authority",
    "existing migration-0003 inventory and totals as selected target",
    "existing initialization version and graph shape as mandatory vertical-slice selection",
    "Section 26 target tranche sequence as operative implementation order",
    "Section 4 C2B4 ownership order as operative implementation order",
)

EXPECTED_NARROWED_ROUTE_DISPOSITIONS = (
    (
        "owner_decisions.planned_adapter_kind",
        "execution_substrate",
        "non-operative during route-neutral initialization",
    ),
    (
        "later_author_effect_owner_decisions.planned_adapter_kind",
        "execution_substrate",
        "first author-effect delivery selects direct_local_bootstrap",
    ),
    (
        "later_author_effect_owner_decisions.direct_local_bootstrap_selected",
        False,
        "first author-effect delivery selects direct_local_bootstrap",
    ),
)

EXPECTED_NARROWED_DEPENDENCY_ORDER = (
    "pre-I/O Coordinator progression",
    "remote worker contact through semantic decision",
    "separate local-Git effect and stop",
    "migration to ES before another productive bootstrap slice",
)

EXPECTED_NARROWED_EFFECT_CEILINGS = {
    "local_feature_branch_commits": 1,
    "pushes": 0,
    "remote_ref_mutations": 0,
    "pull_requests": 0,
    "merges": 0,
    "deployments": 0,
    "publication_effects": 0,
}

EXPECTED_NARROWED_JIT_DEFERRALS = {
    "meaning": "required questions, not selected schemas",
    "pre_IO_durable_progression": (
        "exact route-neutral initialization versioning",
        "minimum initialization and author-effect durable graph",
        "whether existing migration-0002 structures suffice",
        "exact replay and recovery for records this phase writes",
        "durable representation of the one-shot bootstrap ceiling",
    ),
    "remote_worker_contact": (
        "minimum safe WorkSpec custody and retrieval contract",
        "external verifier-result persistence",
        "source invocation identity and lookup",
        "capsule custody",
        "validation and review evidence",
        "only migration-0003 relations required by the executable path",
    ),
    "local_Git_effect": (
        "Git command, delivery, invocation, and observation values",
        "authority binding",
        "Git reconciliation",
        "evidence sufficient for committed, absent, or unresolved",
        "no-blind-retry enforcement",
    ),
    "ES_migration": (
        "reliable keyed submit",
        "caller-response-loss recovery",
        "Nomad ambiguous-registration reconciliation",
        "retained-result and capsule transport",
        "Coordinator adapter conformance",
        "bootstrap disablement after migration",
    ),
}

EXPECTED_NARROWED_NON_SELECTIONS = (
    "custody receipt fields, digests, authenticity ordering, or canonical vectors",
    "initialization command version, fields, digest, row count, graph rank, or recovery graph",
    "custody relation fields, indexes, foreign keys, or SQL feasibility",
    "verifier-result fields, enums, unions, cardinalities, attestations, or relation",
    "local-Git command, delivery, invocation, observation fields, or digests",
    "generic worker/local-Git union schema",
    "source-journal or definite-absence proof schema",
    "authority/Git digest DAG or topological order",
    "migration-0003 relation names, counts, indexes, triggers, or totals",
    "future-schema SQLite fixture",
    "future-value canonical vectors",
    "cross-record resealing matrix or implementation-level mutants",
    "new latch row or value",
)

EXPECTED_QUALIFIED_REMOTE_HOST_READINESS_EVIDENCE_GATE = (
    "satisfied only by accepted evidence produced through the owning remote-host readiness process",
    "establishes that one remote Linux host is qualified for the exact first-route activities about to occur",
    "before acceptance no real WorkSpec retrieval, process-separated worker or Codex invocation, validation, review, or local-Git execution may begin",
    "operational/readiness evidence only; not semantic identity, execution authority, a parent grant, Coordinator progression truth, runtime truth, or permission for Mac fallback",
    "failure or absence authorizes neither execution on the user's Mac nor execution on the Coordinator host",
    "evidence schema, producer implementation, transport, profile format, and durable storage mechanism remain deferred",
)

EXPECTED_ACCEPTED_CLEAN_EXACT_ES_OID_AND_OWNING_REPOSITORY_CONTRACT_ADOPTION_EVIDENCE_GATE = (
    "before recorded ES scenario initialization or execution requires all three jointly bound facts: one accepted clean ES repository baseline established by accepted repository-status evidence, that same accepted clean baseline resolved to one concrete exact ES Git object OID, and accepted owning-ES-repository contract/adoption evidence applicable to that exact OID and recorded scenario",
    "cleanliness qualifies the accepted ES repository baseline, not the Git OID; the exact OID identifies the immutable Git object to which that accepted baseline and adoption evidence are bound",
    "exact-OID evidence without accepted baseline-cleanliness evidence is insufficient, and accepted clean-baseline evidence without a concrete exact Git object OID is insufficient",
    "the baseline-cleanliness evidence and exact-OID evidence must identify the same accepted baseline; independently supplied or otherwise unbound evidence is insufficient",
    "owning-repository contract/adoption evidence must apply to that same exact OID and recorded scenario; evidence for another OID or another scenario is insufficient",
    "a branch name, moving ref, worktree path, snapshot title, chat label, Codex report, ChatGPT report, or prose assertion cannot satisfy any missing component by itself",
    "the gate transfers no ES admission, runtime, lifecycle, retained-result, or contract authority to Coordinator",
    "gate DTO, persistent gate schema, exact evidence file format, exact Git command, ignored-file treatment, reliable-submit DTO or implementation, Coordinator-to-ES adapter protocol, and any new migration-0003 surface remain deferred",
)

EXPECTED_NARROWED_TOP_LEVEL_KEYS = (
    "contract_identity",
    "finite_supersession",
    "governing_decisions",
    "critical_path_order",
    "just_in_time_design_deferrals",
    "explicit_non_selections",
    "preserved_C2B3A",
    "current_and_target_status",
)
EXPECTED_NARROWED_TOP_LEVEL_TYPES = (
    dict, dict, dict, dict, dict, tuple, dict, dict,
)
EXPECTED_NARROWED_IDENTITY_KEYS = (
    "workstream",
    "semantic_owner",
    "status",
    "scope",
    "rejected_identity_schema_candidate_operative",
)
EXPECTED_NARROWED_IDENTITY_TYPES = (str, str, str, str, bool)
EXPECTED_NARROWED_FINITE_SUPERSESSION_KEYS = (
    "all_non_superseded_C2B3A_semantics_remain_operative",
    "supersedes_only",
    "preserved_route_field_dispositions",
    "route_specific_latch_disposition",
    "migration_0003_disposition",
    "initialization_shape_disposition",
)
EXPECTED_NARROWED_FINITE_SUPERSESSION_TYPES = (
    bool, tuple, tuple, str, str, str,
)
EXPECTED_NARROWED_GOVERNING_DECISION_KEYS = (
    "horizontal_implementation_sequence_superseded",
    "initialization_route_neutral",
    "initialization_forbids",
    "route_selection_boundary",
    "first_route",
    "first_route_meaning",
    "first_route_does_not_mean",
    "intended_first_physical_topology",
    "topology_profile_transport_are_operational_evidence_only",
    "topology_profile_transport_are_semantic_identity_or_authority",
    "adapter_kinds_remain",
    "third_adapter_kind_introduced",
    "authority_separation",
    "raw_WorkSpec_in_Coordinator_SQLite",
    "retrieval_bearer_authority_in_Coordinator_SQLite",
    "ref_or_digest_is_retrieval_authority",
    "productive_bootstrap_acceptance_maximum",
    "productive_bootstrap_exact_durable_representation",
    "local_Git_effect_separate_after_semantic_acceptance",
    "effect_ceilings",
    "ambiguous_Git_outcome_permits_blind_second_commit",
    "qualified_remote_host_readiness_evidence_gate",
    "accepted_clean_exact_es_oid_and_owning_repository_contract_adoption_evidence_gate",
    "post_acceptance_bootstrap_gate",
)
EXPECTED_NARROWED_GOVERNING_DECISION_TYPES = (
    bool, bool, tuple, str, str, str, tuple, str, bool, bool, tuple, bool,
    tuple, bool, bool, bool, int, str, bool, dict, bool, tuple, tuple, str,
)
EXPECTED_NARROWED_EFFECT_CEILING_KEYS = (
    "local_feature_branch_commits",
    "pushes",
    "remote_ref_mutations",
    "pull_requests",
    "merges",
    "deployments",
    "publication_effects",
)
EXPECTED_NARROWED_EFFECT_CEILING_TYPES = (int, int, int, int, int, int, int)
EXPECTED_NARROWED_CRITICAL_PATH_ORDER_KEYS = (
    "dependency_order",
    "mandatory_program_or_tranche_count_frozen",
    "checkpoint_division_rule",
)
EXPECTED_NARROWED_CRITICAL_PATH_ORDER_TYPES = (tuple, bool, str)
EXPECTED_NARROWED_JIT_DEFERRAL_KEYS = (
    "meaning",
    "pre_IO_durable_progression",
    "remote_worker_contact",
    "local_Git_effect",
    "ES_migration",
)
EXPECTED_NARROWED_JIT_DEFERRAL_TYPES = (str, tuple, tuple, tuple, tuple)
EXPECTED_NARROWED_PRESERVED_C2B3A_KEYS = (
    "transaction_and_cleanup_semantics",
    "C2A_values_or_vectors_changed",
)
EXPECTED_NARROWED_PRESERVED_C2B3A_TYPES = (tuple, bool)
EXPECTED_NARROWED_CURRENT_AND_TARGET_STATUS_KEYS = (
    "current",
    "absent_target_capabilities",
    "production_source_changed_or_authorized",
    "runtime_implemented_or_authorized",
    "independent_audit_performed",
)
EXPECTED_NARROWED_CURRENT_AND_TARGET_STATUS_TYPES = (
    tuple, tuple, bool, bool, bool,
)


def _narrowed_reset_addendum(text: str | None = None) -> dict[str, object]:
    source = _owner() if text is None else text
    diagnostic = "C2B3_NARROWED_RESET_OWNER_INVALID"
    _require(type(source) is str, diagnostic)
    _require(source.count(NARROWED_RESET_BEGIN_MARKER) == 1, diagnostic)
    _require(source.count(NARROWED_RESET_END_MARKER) == 1, diagnostic)
    _require(source.count(VS1A_BEGIN_MARKER) == 1, diagnostic)
    _require(source.count(VS1A_END_MARKER) == 1, diagnostic)
    _require(
        source.split(VS1A_END_MARKER, 1)[1] == EXPECTED_VS1A_TRAILING_PROSE,
        diagnostic,
    )
    before, remainder = source.split(NARROWED_RESET_BEGIN_MARKER, 1)
    payload, after = remainder.split(NARROWED_RESET_END_MARKER, 1)
    _require(before.endswith("\n"), diagnostic)
    _require(after.startswith(EXPECTED_NARROWED_RESET_TRAILING_PROSE + "\n## 37. "), diagnostic)
    lines = payload.strip().splitlines()
    _require(lines[0] == "```python" and lines[-1] == "```", diagnostic)
    try:
        parsed = ast.literal_eval("\n".join(lines[1:-1]))
    except (SyntaxError, ValueError):
        raise AssertionError(diagnostic) from None
    _require(type(parsed) is dict, diagnostic)
    _require(tuple(parsed) == ("critical_path_narrowing_addendum",), diagnostic)
    value = parsed["critical_path_narrowing_addendum"]
    _require(type(value) is dict, diagnostic)
    return value


def _require_closed_narrowed_mapping(
    value: object,
    expected_keys: tuple[str, ...],
    expected_types: tuple[type, ...],
    diagnostic: str,
) -> None:
    _require(type(value) is dict, diagnostic)
    _require(type(expected_keys) is tuple, diagnostic)
    _require(type(expected_types) is tuple, diagnostic)
    _require(len(expected_keys) == len(expected_types), diagnostic)
    _require(tuple(value) == expected_keys, diagnostic)
    for key, expected_type in zip(expected_keys, expected_types, strict=True):
        _require(type(value[key]) is expected_type, diagnostic)


def _assert_narrowed_reset_governing_surface(value: object) -> None:
    diagnostic = "C2B3_NARROWED_RESET_INVALID"
    _require_closed_narrowed_mapping(
        value,
        EXPECTED_NARROWED_TOP_LEVEL_KEYS,
        EXPECTED_NARROWED_TOP_LEVEL_TYPES,
        diagnostic,
    )

    identity = value["contract_identity"]
    _require_closed_narrowed_mapping(
        identity,
        EXPECTED_NARROWED_IDENTITY_KEYS,
        EXPECTED_NARROWED_IDENTITY_TYPES,
        diagnostic,
    )
    _require(identity == {
        "workstream": "COORDINATOR_VERTICAL_SLICE_GOVERNING_NARROWING",
        "semantic_owner": ".docs/c2b-durable-development-state.md#36-c2b3-vertical-slice-governing-narrowing-addendum",
        "status": "accepted governing target; production implementation absent",
        "scope": "architecture, sequencing, authority, effect ceilings, prerequisites, current status, and just-in-time deferrals only",
        "rejected_identity_schema_candidate_operative": False,
    }, diagnostic)

    finite = value["finite_supersession"]
    _require_closed_narrowed_mapping(
        finite,
        EXPECTED_NARROWED_FINITE_SUPERSESSION_KEYS,
        EXPECTED_NARROWED_FINITE_SUPERSESSION_TYPES,
        diagnostic,
    )
    _require(finite["all_non_superseded_C2B3A_semantics_remain_operative"] is True, diagnostic)
    _require(finite["supersedes_only"] == EXPECTED_NARROWED_SUPERSEDES_ONLY, diagnostic)
    _require(finite["preserved_route_field_dispositions"] == EXPECTED_NARROWED_ROUTE_DISPOSITIONS, diagnostic)
    _require(finite["route_specific_latch_disposition"] == "policy ceiling retained; exact durable representation deferred", diagnostic)
    _require(finite["migration_0003_disposition"] == "inventory, names, counts, indexes, triggers, and totals reopened rather than replaced", diagnostic)
    _require(finite["initialization_shape_disposition"] == "exact version, records, graph, replay, and recovery reopened for pre-I/O just-in-time design", diagnostic)

    decisions = value["governing_decisions"]
    _require_closed_narrowed_mapping(
        decisions,
        EXPECTED_NARROWED_GOVERNING_DECISION_KEYS,
        EXPECTED_NARROWED_GOVERNING_DECISION_TYPES,
        diagnostic,
    )
    _require(decisions["horizontal_implementation_sequence_superseded"] is True, diagnostic)
    _require(decisions["initialization_route_neutral"] is True, diagnostic)
    _require(decisions["initialization_forbids"] == (
        "adapter", "host", "transport", "endpoint", "delivery", "external request",
    ), diagnostic)
    _require(decisions["route_selection_boundary"] == "author-effect delivery", diagnostic)
    _require(decisions["first_route"] == "direct_local_bootstrap", diagnostic)
    _require(decisions["first_route_meaning"] == "bounded direct/non-ES bootstrap", diagnostic)
    _require(decisions["first_route_does_not_mean"] == (
        "user Mac", "Coordinator host", "physical colocation",
    ), diagnostic)
    _require(decisions["intended_first_physical_topology"] == "one qualified remote Linux host", diagnostic)
    _require(decisions["topology_profile_transport_are_operational_evidence_only"] is True, diagnostic)
    _require(decisions["topology_profile_transport_are_semantic_identity_or_authority"] is False, diagnostic)
    _require(decisions["adapter_kinds_remain"] == (
        "execution_substrate", "direct_local_bootstrap",
    ), diagnostic)
    _require(decisions["third_adapter_kind_introduced"] is False, diagnostic)
    _require(decisions["authority_separation"] == (
        "Coordinator owns durable progression only",
        "external source owns the parent standing grant",
        "external verifier supplies current verification",
        "Coordinator cannot issue its parent grant or author verified",
        "persisted authority evidence is not automatically fresh permission",
        "user is not a routine per-effect approver",
        "worker has no Coordinator SQLite or writer access",
        "Git owns object and ref truth",
        "validators and reviewers own their evidence",
        "reports, model output, Bridge records, and transport receipts remain evidence only",
    ), diagnostic)
    _require(decisions["raw_WorkSpec_in_Coordinator_SQLite"] is False, diagnostic)
    _require(decisions["retrieval_bearer_authority_in_Coordinator_SQLite"] is False, diagnostic)
    _require(decisions["ref_or_digest_is_retrieval_authority"] is False, diagnostic)
    _require(decisions["productive_bootstrap_acceptance_maximum"] == 1, diagnostic)
    _require(decisions["productive_bootstrap_exact_durable_representation"] == "deferred", diagnostic)
    _require(decisions["local_Git_effect_separate_after_semantic_acceptance"] is True, diagnostic)
    effect_ceilings = decisions["effect_ceilings"]
    _require_closed_narrowed_mapping(
        effect_ceilings,
        EXPECTED_NARROWED_EFFECT_CEILING_KEYS,
        EXPECTED_NARROWED_EFFECT_CEILING_TYPES,
        diagnostic,
    )
    _require(effect_ceilings == EXPECTED_NARROWED_EFFECT_CEILINGS, diagnostic)
    _require(decisions["ambiguous_Git_outcome_permits_blind_second_commit"] is False, diagnostic)
    _require(
        decisions["qualified_remote_host_readiness_evidence_gate"]
        == EXPECTED_QUALIFIED_REMOTE_HOST_READINESS_EVIDENCE_GATE,
        diagnostic,
    )
    _require(
        decisions["accepted_clean_exact_es_oid_and_owning_repository_contract_adoption_evidence_gate"]
        == EXPECTED_ACCEPTED_CLEAN_EXACT_ES_OID_AND_OWNING_REPOSITORY_CONTRACT_ADOPTION_EVIDENCE_GATE,
        diagnostic,
    )
    _require(decisions["post_acceptance_bootstrap_gate"] == "no second productive bootstrap slice before accepted ES reliable-submit and adapter-conformance gates", diagnostic)

    order = value["critical_path_order"]
    _require_closed_narrowed_mapping(
        order,
        EXPECTED_NARROWED_CRITICAL_PATH_ORDER_KEYS,
        EXPECTED_NARROWED_CRITICAL_PATH_ORDER_TYPES,
        diagnostic,
    )
    _require(order == {
        "dependency_order": EXPECTED_NARROWED_DEPENDENCY_ORDER,
        "mandatory_program_or_tranche_count_frozen": False,
        "checkpoint_division_rule": "future implementation prompts may divide or combine internal checkpoints while preserving authority, validation, and provenance boundaries",
    }, diagnostic)
    jit_deferrals = value["just_in_time_design_deferrals"]
    _require_closed_narrowed_mapping(
        jit_deferrals,
        EXPECTED_NARROWED_JIT_DEFERRAL_KEYS,
        EXPECTED_NARROWED_JIT_DEFERRAL_TYPES,
        diagnostic,
    )
    _require(jit_deferrals == EXPECTED_NARROWED_JIT_DEFERRALS, diagnostic)
    _require(value["explicit_non_selections"] == EXPECTED_NARROWED_NON_SELECTIONS, diagnostic)

    preserved = value["preserved_C2B3A"]
    _require_closed_narrowed_mapping(
        preserved,
        EXPECTED_NARROWED_PRESERVED_C2B3A_KEYS,
        EXPECTED_NARROWED_PRESERVED_C2B3A_TYPES,
        diagnostic,
    )
    _require(preserved["transaction_and_cleanup_semantics"] == (
        "one Coordinator writer", "one shared mutation slot",
        "existing transaction controller", "BEGIN IMMEDIATE",
        "writer and session fencing", "receipt-first replay", "CAS",
        "one commit attempt", "commit uncertainty",
        "A/QU/QK/PU/PK/X cleanup states and order", "lock-release proof",
        "finalizer and liveness treatment", "privacy and process-control precedence",
        "exact committed, definitely-not-committed, and unresolved recovery classifications",
        "no external I/O",
    ), diagnostic)
    _require(preserved["C2A_values_or_vectors_changed"] is False, diagnostic)

    status = value["current_and_target_status"]
    _require_closed_narrowed_mapping(
        status,
        EXPECTED_NARROWED_CURRENT_AND_TARGET_STATUS_KEYS,
        EXPECTED_NARROWED_CURRENT_AND_TARGET_STATUS_TYPES,
        diagnostic,
    )
    _require(status["current"] == (
        "application generation 2", "terminal migration 0002", "C2A1 values",
        "C2B2 row and value modules", "C2B2 private production-unintegrated readers",
        "existing bounded transaction and writer authority",
    ), diagnostic)
    _require(status["absent_target_capabilities"] == (
        "worker", "custodian", "external verifier", "migration 0003",
        "source invocation", "evidence and decision runtime", "Git effect runtime",
        "Execution Substrate adapter", "publication",
    ), diagnostic)
    _require(status["production_source_changed_or_authorized"] is False, diagnostic)
    _require(status["runtime_implemented_or_authorized"] is False, diagnostic)
    _require(status["independent_audit_performed"] is False, diagnostic)

    serialized = repr(value)
    for forbidden in (
        "WorkSpecCustodyReceiptV1",
        "VerifiedAuthorityResultV1",
        "LocalGitCommandV1",
        "LocalGitDeliveryV1",
        "LocalGitObservationV1",
        "canonical_positive_vectors",
        "digest_domain",
        "ordered_fields",
        "field_contracts",
        "dependency_dag",
        "table_count",
        "trigger_count",
        "explicit_index_count",
        "CREATE TABLE",
        "sqlite3.connect",
        "prerequisite_00061",
        "prerequisite_00054",
    ):
        _require(forbidden not in serialized, diagnostic)


def test_narrowed_reset_owner_is_exact_governing_contract() -> None:
    value = _narrowed_reset_addendum()
    _assert_narrowed_reset_governing_surface(value)


def test_narrowed_reset_intrinsic_prerequisite_gate_keys_and_non_authority() -> None:
    value = _narrowed_reset_addendum()
    decisions = value["governing_decisions"]
    remote_key = "qualified_remote_host_readiness_evidence_gate"
    es_key = "accepted_clean_exact_es_oid_and_owning_repository_contract_adoption_evidence_gate"
    numeric_labels = ("prerequisite_00061", "prerequisite_00054")

    assert remote_key in decisions
    assert es_key in decisions
    assert all(label not in decisions for label in numeric_labels)
    owner = _owner()
    assert owner.count(f'"{remote_key}"') == 1
    assert owner.count(f'"{es_key}"') == 1
    assert all(label not in owner for label in numeric_labels)

    remote_gate = " ".join(decisions[remote_key])
    for required in (
        "accepted evidence",
        "owning remote-host readiness process",
        "one remote Linux host is qualified",
        "WorkSpec retrieval",
        "process-separated worker or Codex invocation",
        "operational/readiness evidence only",
        "not semantic identity",
        "execution authority",
        "parent grant",
        "Coordinator progression truth",
        "runtime truth",
        "permission for Mac fallback",
        "Coordinator host",
    ):
        assert required in remote_gate

    es_gate = " ".join(decisions[es_key])
    for required in (
        "all three jointly bound facts",
        "accepted clean ES repository baseline",
        "accepted repository-status evidence",
        "same accepted clean baseline resolved to one concrete exact ES Git object OID",
        "cleanliness qualifies the accepted ES repository baseline, not the Git OID",
        "exact OID identifies the immutable Git object",
        "exact-OID evidence without accepted baseline-cleanliness evidence is insufficient",
        "accepted clean-baseline evidence without a concrete exact Git object OID is insufficient",
        "must identify the same accepted baseline",
        "owning-ES-repository contract/adoption evidence",
        "same exact OID and recorded scenario",
        "another OID or another scenario is insufficient",
        "branch name, moving ref, worktree path, snapshot title, chat label, Codex report, ChatGPT report, or prose assertion",
        "cannot satisfy any missing component by itself",
        "transfers no ES admission, runtime, lifecycle, retained-result, or contract authority",
        "gate DTO, persistent gate schema",
        "ignored-file treatment",
        "any new migration-0003 surface remain deferred",
    ):
        assert required in es_gate
    assert "accepted clean exact ES Git OID" not in es_gate

    for path in (
        ROOT / ".docs/software-development-progression-boundary.md",
        ROOT / ".docs/worker-execution-boundary.md",
    ):
        projection = path.read_text(encoding="utf-8")
        assert remote_key in projection
        assert all(label not in projection for label in numeric_labels)
    progression = (ROOT / ".docs/software-development-progression-boundary.md").read_text(
        encoding="utf-8"
    )
    assert es_key in progression
    progression_compact = " ".join(progression.split())
    for required in (
        f"The earlier formulation that `{es_key}` requires an accepted clean exact ES Git OID is rejected",
        "cleanliness qualifies the accepted ES repository baseline, not the Git OID",
        "three jointly bound facts",
        "same accepted clean baseline resolved to one concrete exact ES Git object OID",
        "contract/adoption evidence applicable to that same exact OID and recorded scenario",
        "adoption evidence for another OID or another scenario is insufficient",
        "branch name, moving ref, worktree path, snapshot title, chat label, Codex report, ChatGPT report, or prose assertion",
        "transfers no ES admission, runtime, lifecycle, retained-result, or contract authority",
    ):
        assert required in progression_compact


def test_narrowed_reset_every_normative_mapping_is_closed_world() -> None:
    value = _narrowed_reset_addendum()
    mappings_and_keys = (
        (value, EXPECTED_NARROWED_TOP_LEVEL_KEYS),
        (value["contract_identity"], EXPECTED_NARROWED_IDENTITY_KEYS),
        (value["finite_supersession"], EXPECTED_NARROWED_FINITE_SUPERSESSION_KEYS),
        (value["governing_decisions"], EXPECTED_NARROWED_GOVERNING_DECISION_KEYS),
        (
            value["governing_decisions"]["effect_ceilings"],
            EXPECTED_NARROWED_EFFECT_CEILING_KEYS,
        ),
        (value["critical_path_order"], EXPECTED_NARROWED_CRITICAL_PATH_ORDER_KEYS),
        (value["just_in_time_design_deferrals"], EXPECTED_NARROWED_JIT_DEFERRAL_KEYS),
        (value["preserved_C2B3A"], EXPECTED_NARROWED_PRESERVED_C2B3A_KEYS),
        (
            value["current_and_target_status"],
            EXPECTED_NARROWED_CURRENT_AND_TARGET_STATUS_KEYS,
        ),
    )
    for mapping, expected_keys in mappings_and_keys:
        assert type(mapping) is dict
        assert tuple(mapping) == expected_keys
    _assert_narrowed_reset_governing_surface(value)


NARROWED_NORMATIVE_MAPPING_PATHS = (
    ("top_level", ()),
    ("contract_identity", ("contract_identity",)),
    ("finite_supersession", ("finite_supersession",)),
    ("governing_decisions", ("governing_decisions",)),
    ("effect_ceilings", ("governing_decisions", "effect_ceilings")),
    ("critical_path_order", ("critical_path_order",)),
    ("just_in_time_design_deferrals", ("just_in_time_design_deferrals",)),
    ("preserved_C2B3A", ("preserved_C2B3A",)),
    ("current_and_target_status", ("current_and_target_status",)),
)

NARROWED_REQUIRED_ADDITIVE_AND_WEAKENED_CASES = (
    "add_initialization_adapter_direct_local_bootstrap",
    "add_initialization_adapter_execution_substrate",
    "add_initialization_delivery",
    "add_initialization_transport_and_host",
    "add_remote_bootstrap_adapter_kind",
    "add_exact_migration_0003_inventory",
    "add_coordinator_authors_verified",
    "add_worker_coordinator_sqlite_access",
    "add_false_current_capability",
    "add_chat_identifier_authority",
    "add_harmless_unknown_identity_field",
    "reintroduce_prerequisite_00061",
    "reintroduce_prerequisite_00054",
    "weaken_remote_host_qualified_readiness_evidence",
    "weaken_es_exact_oid_requirement",
    "weaken_es_owning_repository_adoption_evidence",
)

NARROWED_PRECEDING_TWENTY_FOUR_CASES = (
    "battery_initialization_execution_substrate",
    "battery_initialization_direct_local_bootstrap",
    "battery_initialization_delivery_transport_host",
    "battery_direct_local_means_mac_or_same_host",
    "battery_third_adapter_remote_bootstrap",
    "battery_preserved_first_delivery_execution_substrate",
    "battery_restore_horizontal_order",
    "battery_freeze_four_programs_nine_tranches",
    "battery_exact_migration_0003_inventory",
    "battery_rejected_custody_dto",
    "battery_raw_work_spec_in_sqlite",
    "battery_coordinator_authors_verified",
    "battery_worker_opens_coordinator_sqlite",
    "battery_second_productive_bootstrap",
    "battery_collapse_git_into_acceptance",
    "battery_two_local_commits",
    "battery_blind_second_commit",
    "battery_remove_remote_host_gate_mac_fallback",
    "battery_remove_clean_es_oid_gate",
    "battery_report_target_runtime_current",
    "battery_chat_identifier_authority",
    "battery_demote_begin_immediate",
    "battery_jit_question_already_settled",
    "battery_remove_jit_ledger",
)

NARROWED_INTRINSIC_GATE_WORD_WEAKENING_CASES = (
    "weaken_word_qualified",
    "weaken_word_evidence",
    "weaken_word_clean",
    "weaken_word_exact",
    "weaken_word_oid",
    "weaken_word_owning_repository_contract_adoption_evidence",
)

NARROWED_ES_BASELINE_OID_ADOPTION_COUNTERFACTUAL_CASES = (
    "reject_ambiguous_clean_exact_oid_phrase",
    "reject_exact_oid_and_adoption_without_clean_baseline",
    "reject_clean_baseline_and_adoption_without_exact_oid",
    "reject_unbound_clean_baseline_and_exact_oid_evidence",
    "reject_adoption_evidence_for_different_oid",
    "reject_adoption_evidence_for_different_scenario",
    "reject_dirty_baseline_at_unchanged_oid",
    "reject_branch_or_moving_ref_as_exact_oid",
    "reject_report_or_snapshot_as_clean_baseline_evidence",
    "reject_cleanliness_as_oid_property",
)


def _narrowed_mapping_at_path(
    value: dict[str, object], path: tuple[str, ...]
) -> dict[str, object]:
    current: object = value
    for key in path:
        assert type(current) is dict
        current = current[key]
    assert type(current) is dict
    return current


def _replace_tuple_text(
    values: tuple[str, ...], old: str, new: str
) -> tuple[str, ...]:
    replaced = tuple(item.replace(old, new) for item in values)
    assert replaced != values
    return replaced


def _apply_narrowed_counterfactual(
    candidate: dict[str, object], case_name: str
) -> None:
    decisions = candidate["governing_decisions"]
    status = candidate["current_and_target_status"]
    preserved = candidate["preserved_C2B3A"]
    jit = candidate["just_in_time_design_deferrals"]
    order = candidate["critical_path_order"]
    remote_key = "qualified_remote_host_readiness_evidence_gate"
    es_key = "accepted_clean_exact_es_oid_and_owning_repository_contract_adoption_evidence_gate"

    if case_name == "add_initialization_adapter_direct_local_bootstrap":
        decisions["initialization_adapter"] = "direct_local_bootstrap"
    elif case_name == "add_initialization_adapter_execution_substrate":
        decisions["initialization_adapter"] = "execution_substrate"
    elif case_name == "add_initialization_delivery":
        decisions["initialization_delivery"] = "direct"
    elif case_name == "add_initialization_transport_and_host":
        decisions["initialization_transport"] = "ssh"
        decisions["initialization_host"] = "remote-linux"
    elif case_name == "add_remote_bootstrap_adapter_kind":
        decisions["third_adapter"] = "remote_bootstrap"
    elif case_name == "add_exact_migration_0003_inventory":
        decisions["migration_0003_inventory"] = {
            "relations": ("future_relation",),
            "cumulative_total": 1,
        }
    elif case_name == "add_coordinator_authors_verified":
        decisions["Coordinator_authors_verified"] = True
    elif case_name == "add_worker_coordinator_sqlite_access":
        decisions["worker_Coordinator_SQLite_access_allowed"] = True
    elif case_name == "add_false_current_capability":
        status["migration_0003_current"] = True
    elif case_name == "add_chat_identifier_authority":
        decisions["chat_identifier_is_architectural_authority"] = True
    elif case_name == "add_harmless_unknown_identity_field":
        candidate["contract_identity"]["harmless_unknown"] = None
    elif case_name == "reintroduce_prerequisite_00061":
        decisions["prerequisite_00061"] = "satisfied"
    elif case_name == "reintroduce_prerequisite_00054":
        decisions["prerequisite_00054"] = "satisfied"
    elif case_name == "weaken_remote_host_qualified_readiness_evidence":
        decisions[remote_key] = (
            "a remote host may be used without accepted qualified readiness evidence",
        )
    elif case_name == "weaken_es_exact_oid_requirement":
        decisions[es_key] = _replace_tuple_text(
            decisions[es_key], "concrete exact ES Git object OID", "accepted ES revision"
        )
    elif case_name == "weaken_es_owning_repository_adoption_evidence":
        decisions[es_key] = (
            "an accepted clean ES repository baseline resolved to one concrete exact ES Git object OID satisfies the gate without owning-repository adoption evidence",
        )
    elif case_name == "battery_initialization_execution_substrate":
        decisions["initialization_route"] = "execution_substrate"
    elif case_name == "battery_initialization_direct_local_bootstrap":
        decisions["initialization_route"] = "direct_local_bootstrap"
    elif case_name == "battery_initialization_delivery_transport_host":
        decisions["initialization_delivery"] = {
            "transport": "ssh",
            "host": "remote-linux",
        }
    elif case_name == "battery_direct_local_means_mac_or_same_host":
        decisions["first_route_does_not_mean"] = (
            "Coordinator host",
            "physical colocation",
        )
    elif case_name == "battery_third_adapter_remote_bootstrap":
        decisions["third_adapter"] = "remote_bootstrap"
    elif case_name == "battery_preserved_first_delivery_execution_substrate":
        decisions["first_route"] = "execution_substrate"
    elif case_name == "battery_restore_horizontal_order":
        decisions["horizontal_implementation_sequence_superseded"] = False
    elif case_name == "battery_freeze_four_programs_nine_tranches":
        order["mandatory_program_or_tranche_count_frozen"] = True
        order["mandatory_program_count"] = 4
        order["mandatory_tranche_count"] = 9
    elif case_name == "battery_exact_migration_0003_inventory":
        decisions["migration_0003_inventory"] = {
            "relations": ("future_relation",),
            "cumulative_total": 1,
        }
    elif case_name == "battery_rejected_custody_dto":
        decisions["WorkSpecCustodyReceiptV1"] = {
            "fields": ("receipt_ref", "digest"),
        }
    elif case_name == "battery_raw_work_spec_in_sqlite":
        decisions["raw_WorkSpec_in_Coordinator_SQLite"] = True
    elif case_name == "battery_coordinator_authors_verified":
        decisions["Coordinator_authors_verified"] = True
    elif case_name == "battery_worker_opens_coordinator_sqlite":
        decisions["worker_Coordinator_SQLite_access_allowed"] = True
    elif case_name == "battery_second_productive_bootstrap":
        decisions["productive_bootstrap_acceptance_maximum"] = 2
    elif case_name == "battery_collapse_git_into_acceptance":
        decisions["local_Git_effect_separate_after_semantic_acceptance"] = False
    elif case_name == "battery_two_local_commits":
        decisions["effect_ceilings"]["local_feature_branch_commits"] = 2
    elif case_name == "battery_blind_second_commit":
        decisions["ambiguous_Git_outcome_permits_blind_second_commit"] = True
    elif case_name == "battery_remove_remote_host_gate_mac_fallback":
        decisions[remote_key] = ("Mac fallback is allowed",)
    elif case_name == "battery_remove_clean_es_oid_gate":
        decisions[es_key] = ("an ES branch name satisfies the gate",)
    elif case_name == "battery_report_target_runtime_current":
        status["migration_0003_current"] = True
        status["worker_current"] = True
    elif case_name == "battery_chat_identifier_authority":
        decisions["chat_identifier_is_architectural_authority"] = True
    elif case_name == "battery_demote_begin_immediate":
        preserved["transaction_and_cleanup_semantics"] = tuple(
            item
            for item in preserved["transaction_and_cleanup_semantics"]
            if item != "BEGIN IMMEDIATE"
        )
    elif case_name == "battery_jit_question_already_settled":
        remote_questions = list(jit["remote_worker_contact"])
        remote_questions[0] = "custody schema already settled"
        jit["remote_worker_contact"] = tuple(remote_questions)
    elif case_name == "battery_remove_jit_ledger":
        candidate["just_in_time_design_deferrals"] = {}
    elif case_name == "reject_ambiguous_clean_exact_oid_phrase":
        decisions[es_key] = (
            "before recorded ES scenario initialization or execution requires one accepted clean exact ES Git OID plus accepted owning-repository adoption evidence for that OID and scenario",
        )
    elif case_name == "reject_exact_oid_and_adoption_without_clean_baseline":
        decisions[es_key] = (
            "one concrete exact ES Git object OID plus owning-repository adoption evidence suffices without an accepted clean repository baseline or baseline-cleanliness evidence",
        )
    elif case_name == "reject_clean_baseline_and_adoption_without_exact_oid":
        decisions[es_key] = (
            "an accepted clean ES repository baseline plus owning-repository adoption evidence suffices without resolving the baseline to a concrete exact Git object OID",
        )
    elif case_name == "reject_unbound_clean_baseline_and_exact_oid_evidence":
        decisions[es_key] = (
            "accepted clean-baseline evidence and exact-OID evidence may be supplied independently without proving that they identify the same accepted baseline",
        )
    elif case_name == "reject_adoption_evidence_for_different_oid":
        decisions[es_key] = (
            "owning-repository adoption evidence for a different OID may satisfy the gate",
        )
    elif case_name == "reject_adoption_evidence_for_different_scenario":
        decisions[es_key] = (
            "owning-repository adoption evidence for a different recorded scenario may satisfy the gate",
        )
    elif case_name == "reject_dirty_baseline_at_unchanged_oid":
        decisions[es_key] = (
            "a dirty repository baseline is sufficient when the exact Git object OID is unchanged",
        )
    elif case_name == "reject_branch_or_moving_ref_as_exact_oid":
        decisions[es_key] = (
            "a branch name or moving ref may substitute for the concrete exact Git object OID",
        )
    elif case_name == "reject_report_or_snapshot_as_clean_baseline_evidence":
        decisions[es_key] = (
            "a Codex report, ChatGPT report, or snapshot title may substitute for accepted clean-baseline evidence",
        )
    elif case_name == "reject_cleanliness_as_oid_property":
        decisions[es_key] = (
            "the concrete exact ES Git object OID is itself clean",
        )
    elif case_name == "weaken_word_qualified":
        decisions[remote_key] = _replace_tuple_text(
            decisions[remote_key], "is qualified", "is prepared"
        )
    elif case_name == "weaken_word_evidence":
        decisions[remote_key] = _replace_tuple_text(
            decisions[remote_key], "evidence", "material"
        )
    elif case_name == "weaken_word_clean":
        weakened = tuple(
            item.replace("cleanliness", "status")
            .replace("clean-baseline", "baseline")
            .replace("clean ", "")
            for item in decisions[es_key]
        )
        assert weakened != decisions[es_key]
        decisions[es_key] = weakened
    elif case_name == "weaken_word_exact":
        decisions[es_key] = _replace_tuple_text(
            decisions[es_key], "exact", "approximate"
        )
    elif case_name == "weaken_word_oid":
        decisions[es_key] = _replace_tuple_text(
            decisions[es_key], "OID", "revision"
        )
    elif case_name == "weaken_word_owning_repository_contract_adoption_evidence":
        weakened = tuple(
            item.replace(
                "owning-ES-repository contract/adoption evidence",
                "scenario evidence",
            )
            .replace(
                "owning-repository contract/adoption evidence",
                "scenario evidence",
            )
            .replace("owning-repository adoption evidence", "scenario evidence")
            for item in decisions[es_key]
        )
        assert weakened != decisions[es_key]
        decisions[es_key] = weakened
    else:
        raise AssertionError(f"unknown narrowed counterfactual: {case_name}")


def _assert_narrowed_counterfactual_rejected(
    candidate: dict[str, object],
    *,
    physical_copy: Path | None = None,
) -> None:
    literal = repr(candidate)
    source = literal
    source_name = "<narrowed-reset-counterfactual>"
    if physical_copy is not None:
        assert not physical_copy.exists()
        physical_copy.write_text(literal + "\n", encoding="utf-8")
        assert physical_copy.is_file() and not physical_copy.is_symlink()
        source = physical_copy.read_text(encoding="utf-8")
        source_name = str(physical_copy)
    compile(source, source_name, "eval")
    parsed = ast.literal_eval(source)
    assert type(parsed) is dict
    assert parsed == candidate
    with pytest.raises(AssertionError) as exc_info:
        _assert_narrowed_reset_governing_surface(parsed)
    assert str(exc_info.value) == "C2B3_NARROWED_RESET_INVALID"


@pytest.mark.parametrize(
    ("mapping_name", "mapping_path"),
    NARROWED_NORMATIVE_MAPPING_PATHS,
    ids=tuple(name for name, _ in NARROWED_NORMATIVE_MAPPING_PATHS),
)
def test_narrowed_reset_every_normative_mapping_rejects_unknown_addition(
    mapping_name: str, mapping_path: tuple[str, ...]
) -> None:
    candidate = deepcopy(_narrowed_reset_addendum())
    target = _narrowed_mapping_at_path(candidate, mapping_path)
    target[f"harmless_unknown_{mapping_name}"] = None
    _assert_narrowed_counterfactual_rejected(candidate)


@pytest.mark.parametrize(
    "case_name",
    NARROWED_REQUIRED_ADDITIVE_AND_WEAKENED_CASES,
    ids=NARROWED_REQUIRED_ADDITIVE_AND_WEAKENED_CASES,
)
def test_narrowed_reset_required_additive_and_weakened_counterfactuals_are_rejected(
    case_name: str,
) -> None:
    candidate = deepcopy(_narrowed_reset_addendum())
    _apply_narrowed_counterfactual(candidate, case_name)
    _assert_narrowed_counterfactual_rejected(candidate)


@pytest.mark.parametrize(
    "case_name",
    NARROWED_PRECEDING_TWENTY_FOUR_CASES,
    ids=NARROWED_PRECEDING_TWENTY_FOUR_CASES,
)
def test_narrowed_reset_preceding_twenty_four_category_battery_is_rejected(
    case_name: str,
) -> None:
    candidate = deepcopy(_narrowed_reset_addendum())
    _apply_narrowed_counterfactual(candidate, case_name)
    _assert_narrowed_counterfactual_rejected(candidate)


@pytest.mark.parametrize(
    "case_name",
    NARROWED_INTRINSIC_GATE_WORD_WEAKENING_CASES,
    ids=NARROWED_INTRINSIC_GATE_WORD_WEAKENING_CASES,
)
def test_narrowed_reset_intrinsic_gate_word_weakening_is_rejected(
    case_name: str,
) -> None:
    candidate = deepcopy(_narrowed_reset_addendum())
    _apply_narrowed_counterfactual(candidate, case_name)
    _assert_narrowed_counterfactual_rejected(candidate)


@pytest.mark.parametrize(
    "case_name",
    NARROWED_ES_BASELINE_OID_ADOPTION_COUNTERFACTUAL_CASES,
    ids=NARROWED_ES_BASELINE_OID_ADOPTION_COUNTERFACTUAL_CASES,
)
def test_narrowed_reset_es_baseline_oid_adoption_counterfactuals_are_rejected(
    case_name: str,
    tmp_path: Path,
) -> None:
    candidate = deepcopy(_narrowed_reset_addendum())
    _apply_narrowed_counterfactual(candidate, case_name)
    _assert_narrowed_counterfactual_rejected(
        candidate,
        physical_copy=tmp_path / f"{case_name}.pyexpr",
    )


def test_narrowed_reset_parser_and_governing_mutants_fail_closed() -> None:
    owner = _owner()
    for malformed in (
        owner.replace(NARROWED_RESET_BEGIN_MARKER, "", 1),
        owner.replace(NARROWED_RESET_END_MARKER, NARROWED_RESET_BEGIN_MARKER, 1),
        owner.replace("```python\n{\n    \"critical_path_narrowing_addendum\"", "```json\n{\n    \"critical_path_narrowing_addendum\"", 1),
        owner + "The earlier manifest governs C2B3B.\n",
    ):
        with pytest.raises(AssertionError, match="C2B3_NARROWED_RESET_OWNER_INVALID"):
            _narrowed_reset_addendum(malformed)

    mutations = (
        ("horizontal_implementation_sequence_superseded", False),
        ("initialization_route_neutral", False),
        ("first_route", "execution_substrate"),
        ("third_adapter_kind_introduced", True),
        ("raw_WorkSpec_in_Coordinator_SQLite", True),
        ("retrieval_bearer_authority_in_Coordinator_SQLite", True),
        ("productive_bootstrap_acceptance_maximum", 2),
        ("local_Git_effect_separate_after_semantic_acceptance", False),
        ("ambiguous_Git_outcome_permits_blind_second_commit", True),
    )
    for key, replacement in mutations:
        candidate = _narrowed_reset_addendum()
        candidate["governing_decisions"][key] = replacement
        with pytest.raises(AssertionError, match="C2B3_NARROWED_RESET_INVALID"):
            _assert_narrowed_reset_governing_surface(candidate)


def test_narrowed_reset_preserves_committed_c2b3a_and_reopens_details() -> None:
    value = _narrowed_reset_addendum()
    _assert_c2b3a_owner_addendum_prose(_owner())
    assert value["finite_supersession"]["all_non_superseded_C2B3A_semantics_remain_operative"] is True
    assert value["critical_path_order"]["mandatory_program_or_tranche_count_frozen"] is False
    assert value["just_in_time_design_deferrals"]["meaning"] == "required questions, not selected schemas"
    assert value["finite_supersession"]["migration_0003_disposition"].endswith("reopened rather than replaced")
    assert value["current_and_target_status"]["production_source_changed_or_authorized"] is False


def test_vs1a_post_section_36_contract_pins_private_cleanup_and_nonimplementation() -> None:
    owner = _owner()
    assert owner.count(VS1A_BEGIN_MARKER) == 1
    assert owner.count(VS1A_END_MARKER) == 1
    payload = owner.split(VS1A_BEGIN_MARKER, 1)[1].split(VS1A_END_MARKER, 1)[0]
    lines = payload.strip().splitlines()
    assert lines[0] == "```python"
    assert lines[-1] == "```"
    parsed = ast.literal_eval("\n".join(lines[1:-1]))
    assert tuple(parsed) == ("c2b_pre_io_vs1a_shared_cleanup_foundation",)
    value = parsed["c2b_pre_io_vs1a_shared_cleanup_foundation"]
    assert tuple(value) == (
        "status",
        "precedence",
        "implementation_scope",
        "selected_connection_custody",
        "closure_proof",
        "resolution_linearization",
        "process_control_stabilization",
        "writer_session_relation",
        "operation_liveness",
        "repair_selectors",
        "repair_counterfactuals",
        "cleanup_claim",
        "safe_error_traceback_privacy",
        "same_wrapper_uncertainty_retry",
        "b3c1b_test_resource_hygiene",
        "b3c3_compatibility",
        "b2b_baseline_hygiene",
        "preserved",
        "absent_and_unauthorized",
        "not_occurred",
    )
    assert value["status"] == (
        "selected implementation repaired after the latest independent-audit "
        "block; candidate validation is non-audit evidence; fresh independent "
        "reaudit not yet performed"
    )
    assert value["precedence"] == {
        "section_35_cleanup_owner": True,
        "section_36_governing_narrowing": True,
        "section_37_subordinate": True,
    }
    assert value["implementation_scope"] == {
        "scope_counts_are_report_only_observations_bound_to_the_exact_current_candidate": True,
        "dirty_path_count": 22,
        "tracked_modification_count": 21,
        "untracked_count": 1,
        "staged_path_count": 0,
        "paths": EXPECTED_VS1A_PATHS,
        "sole_untracked_path": (
            "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py"
        ),
        "b2b_lock_integration_in_changed_path_inventory": False,
        "b3c1a_contract_projection_path": (
            "tests/test_b3c1a_writer_session_authority.py"
        ),
        "b3c1a_contract_projection_replacement": (
            "same node ID projects pre-EXPLICIT_RETIRED GC/finalizer loss as "
            "ORPHANED -> non-admitting -> cleanup -> X"
        ),
        "b4b_privacy_contract_path": (
            "tests/test_b4b_private_atomic_global_stop_persistence.py"
        ),
        "b4b_zero_Coordinator_frame_privacy_replacement": (
            "accepted one-byte contract replacement retained unchanged"
        ),
    }
    assert value["selected_connection_custody"] == {
        "controller_exclusive_scope": True,
        "scope_constructed_before_resource_publication": True,
        "exact_activation_acknowledgment_before_COMMIT": True,
        "controller_supplies_immutable_facts_only": True,
        "actual_successor_selected_under_resource_lock": True,
        "controller_precomputes_actual_successor": False,
        "successor_publication": "one exact lifecycle-state assignment",
        "controller_aliases_cleared_only_after_exact_successor_acknowledgment": True,
        "scope_use_valid_after_successor_assignment": False,
        "resource_controller_state_contains_connection": False,
        "unproved_QU_or_QK_retains_exact_connection_and_slot": True,
        "proved_PU_or_PK_retains_connection": False,
    }
    assert value["closure_proof"] == {
        "only_source": (
            "normal return from sqlite3.Connection.close(exact_connection) called "
            "by the retained-custody owner"
        ),
        "generic_close_helper_is_proof_owner": False,
        "caller_supplied_successful_close_callback": False,
        "production_proof_construction_sites": 1,
        "same_object_repeated_close": "permitted only while proof is absent",
        "close_after_C2": False,
        "in_transaction_or_ProgrammingError_probe": False,
        "exception_message_classification": False,
        "proof_contains_connection": False,
    }
    assert value["resolution_linearization"] == {
        "pre_close_policies": (
            "resume-if-close-proved-and-still-eligible",
            "cleanup-required-after-resolution",
        ),
        "post_close_resume_result": (
            "field-free ResumeActive created only after exact close proof"
        ),
        "cleanup_wins_merge_under_resource_lock": True,
        "publication_single_assignment": True,
        "exact_acknowledgment_required_before_alias_clear": True,
        "idempotent_reentry_matches_exact_token_intent_and_proof_or_custody": True,
        "disposal_before_publication": (
            "monotonically strengthens policy to cleanup-required"
        ),
        "disposal_after_proof_publication": (
            "atomically converts resumption to proof-backed cleanup"
        ),
        "disposal_after_exact_mutation_release_before_operation_completion": (
            "non-admitting proof-backed cleanup; exact operation remains "
            "represented until completion"
        ),
        "operation_completion_can_restore_active_after_disposal": False,
    }
    assert value["process_control_stabilization"] == {
        "governing_types": (
            "KeyboardInterrupt",
            "SystemExit",
            "GeneratorExit",
        ),
        "original_object_identity_args_and_SystemExit_code_preserved": True,
        "internal_retirement_entry_boundary": (
            "the retained _close handler begins at the owner-PID check; it does "
            "not claim its own first opcode or the first opcode of __exit__"
        ),
        "entry_process_control": (
            "synchronously marks the represented operation cleanup-required "
            "under the resource condition before exact bare re-raise"
        ),
        "entry_process_control_allows_new_operation": False,
        "operation_guard_call_site_inventory": {
            "vulnerable_retained_lease": (
                "SQLiteWriterSession.apply_transition",
                "SQLiteWriterSession.apply_global_stop_update",
            ),
            "fail_closed_ephemeral_or_unbound_lease": (
                "WriterSessionResource.require_usable_for_mutation",
            ),
            "unresolved": (),
        },
        "retained_lease_caller_envelope": (
            "one public caller try around pre-admission correlation creation and "
            "one nested helper call; it covers the complete helper, compiler "
            "cleanup, __exit__, and _close escape"
        ),
        "exact_invocation_correlation": (
            "one private immutable exact-object token is created by the resource "
            "before the helper can admit; admission binds it through the exact "
            "handle retained by the immutable resource-owned operation record in "
            "the same condition-protected lifecycle assignment"
        ),
        "correlation_is_authority_or_persisted": False,
        "stabilizer_depends_on_returned_lease_or_post_return_handle": False,
        "current_record_classifications": (
            "REPRESENTED_INCOMPLETE",
            "REPRESENTED_CLEANUP_OWNED",
            "NOT_CURRENTLY_REPRESENTED",
            "INVALID_OR_WRONG_RESOURCE",
        ),
        "absence_is_historical_proof_of_final_assignment_or_no_admission": False,
        "not_currently_represented_effect": (
            "no poison for that token; semantic response-loss recovery remains "
            "fresh/replay/conflict owned"
        ),
        "traceback_privacy": (
            "after bounded exact-token stabilization, a cycle-aware sanitizer "
            "clears traceback fields in supported BaseException base storage, "
            "BaseExceptionGroup base children, the base instance dictionary, and "
            "BaseException values reached through exact built-in tuple/list/dict/"
            "set/frozenset containers; bound base descriptors avoid subclass "
            "dispatch, identity and semantic links/content are preserved, one "
            "ordinary primary or call-boundary failure is contained by an "
            "independently bound fallback, and no Coordinator frame remains in the "
            "supported graph before bare reraise"
        ),
        "traceback_sanitizer_boundary": {
            "base_storage": (
                "BaseException.__traceback__",
                "BaseException.__cause__",
                "BaseException.__context__",
                "BaseException.args",
                "BaseException.__dict__",
                "BaseExceptionGroup.exceptions",
            ),
            "base_descriptor_access": True,
            "exact_builtin_containers": (
                "tuple",
                "list",
                "dict keys and values",
                "set",
                "frozenset",
            ),
            "clear_base_traceback_before_other_base_fields": True,
            "one_ordinary_primary_or_call_boundary_failure_contained": True,
            "independently_bound_non_dispatching_fallback": True,
            "semantic_payload_preserved": True,
            "subclass_dynamic_descriptors": False,
            "arbitrary_subclass_slots": False,
            "arbitrary_user_object_attributes": False,
            "custom_container_iteration": False,
            "unsupported": (
                "repeated asynchronous interruption, catastrophic allocation "
                "failure, or private mutation of bound defaults or C-level "
                "descriptors"
            ),
        },
        "admission_poison": {
            "owner": "WriterSessionResource",
            "initial": False,
            "only_transition": "clear -> poisoned",
            "reset": False,
            "payload": None,
            "publication": (
                "after direct exact lifecycle-structure inspection finds one "
                "current record by token identity, immediate direct assignment "
                "under the resource condition occurs before notification, policy "
                "classification, record replacement, successor construction, "
                "cleanup cursor construction, callback, or any patchable project "
                "helper"
            ),
            "pre_poison_operations": (
                "exact token type, directly stored resource identity, direct fork-"
                "invalid owner-PID sentinel, condition acquisition, direct exact "
                "lifecycle-state type inspection, exact immutable tuple access, "
                "direct frozen/slotted record fields, and exact token object "
                "identity only"
            ),
            "pre_poison_lifecycle_property_or_project_helper": False,
            "project_or_patchable_policy_helper_between_match_and_poison": False,
            "exact_match_immediately_followed_by_poison": True,
            "post_poison_consistency_validation": (
                "_state_authority derivation and PID, epoch, resource, correlation, "
                "record, and handle checks occur only after poison; failure leaves "
                "poison set and admission denied"
            ),
            "post_poison_classification_and_detailed_cleanup": (
                "classification and exact cleanup-required record marking are "
                "bounded after poison; failures preserve poison and the caller's "
                "two attempts remain bounded"
            ),
            "controller_resolution_cleanup_required_classification": (
                "REPRESENTED_CLEANUP_OWNED"
            ),
            "readers": (
                "active_for_owner",
                "active lifecycle validation",
                "operation admission",
                "mutation admission and validation",
                "controller-scope admission",
                "mutation-slot release and clearing",
                "controller successor selection",
                "final operation successor selection",
            ),
            "poisoned_resource_can_publish_admitting_successor": False,
            "cleanup_can_reach_terminal_X": True,
        },
        "mutation_usability_path": (
            "separate ephemeral/unbound path; it prepublishes Phase-1 "
            "preparation for reachable exit boundaries, uses no caller envelope "
            "or poison, and its reproduced compiler-cleanup boundary still loses "
            "the last lease reference and reaches terminal-X through the existing "
            "finalizer"
        ),
        "wrong_PID_or_fork_child_gains_parent_authority": False,
        "usable_connection_scope_required_after_proof_publication": False,
        "unresolved_resume_policy_strengthens_to_cleanup_required": True,
        "published_resume_converts_to_proof_backed_cleanup": True,
        "completion_disposition_owner": (
            "immutable operation record in the resource lifecycle state"
        ),
        "completion_disposition_transition": (
            "resume-eligible to cleanup-required only"
        ),
        "operation_completion_linearization": (
            "one final lifecycle-state assignment under "
            "WriterSessionResource._condition"
        ),
        "python_method_return_is_lifecycle_authority": False,
        "pre_linearization_process_control": (
            "operation remains represented and non-admitting; synchronized "
            "cleanup-required posture wins"
        ),
        "post_linearization_process_control": (
            "assigned state remains authoritative; no retroactive cleanup "
            "demotion"
        ),
        "post_linearization_ambiguity": "caller response loss only",
        "operation_boundary": (
            "operation body through mutation cleanup, exact mutation release, "
            "and operation completion"
        ),
        "local_stabilization_error_replaces_governing_process_control": False,
        "post_poison_detailed_cleanup_RuntimeError_can_reenable_admission": False,
        "raw_process_control_retained_in_handle_or_resource": False,
        "stabilization_failure_can_restore_active": False,
        "background_retry_or_registry_scan": False,
    }
    relation = value["writer_session_relation"]
    assert relation["broad_optional_snapshot"] is False
    assert relation["arbitrary_completed_step_set"] is False
    assert relation["closed_variants"] == (
        "abort-close-unproved",
        "commit-uncertain-unproved",
        "commit-known-unproved",
        "commit-uncertain-pending-cleanup",
        "commit-known-pending-cleanup",
        "operations-closing",
        "mutation-closing",
        "ordinary-cleanup",
        "cleanup-claimed",
        "terminal-X",
    )
    assert relation["cleanup_progress"] == (
        "before-R1-with-slot",
        "before-R1-without-slot",
        "before-R2-with-slot",
        "before-R2-without-slot",
        "before-R3",
        "before-L1",
        "before-H1",
        "before-H2",
        "before-T1",
    )
    assert relation["single_structural_owners"] == {
        "authority_and_operations": (
            "WriterSessionActivity containing immutable "
            "WriterSessionOperationRecord values"
        ),
        "mutation_slot": (
            "WriterSessionMutationFrame then the slot-bearing cleanup cursor"
        ),
        "resolution_identity": "exact ControllerScopeToken",
        "retained_connection_or_close_proof": (
            "exclusive arms of RetainedSQLiteConnection before publication"
        ),
        "cleanup_cursor": "ContinueCleanup",
        "cleanup_claim": "WriterSessionCleanupClaimed",
        "terminal": "field-free WriterSessionTerminalX",
    }
    assert relation["cross_wired_authority_activity_or_slot_constructible"] is False
    assert relation["resource_identity"] == {
        "type": "private opaque WriterSessionResourceIdentity",
        "allocation": "one exact object per WriterSessionResource",
        "comparison": "identity only",
        "persistence_registry_public_export_or_safe_error_evidence": False,
        "bound_components": (
            "resource",
            "authority",
            "activity",
            "resource-owned operation record",
            "operation completion handle",
            "mutation slot and frame",
            "controller scope token",
            "connection custody, retained connection, and close proof",
            "every cleanup cursor",
            "cleanup claim",
            "unproved and proved cleanup states",
        ),
    }
    assert relation["structural_consequences"] == (
        "later cursors cannot reconstruct removed authority, operation, slot, "
        "binding, or lock custody"
    )
    assert value["operation_liveness"] == {
        "completion_handle_exists_before_publication": True,
        "lease_and_finalizer_exist_before_publication": True,
        "resource_owns_immutable_admission_record": True,
        "record_binds_exact_precreated_invocation_correlation": True,
        "record_copies_resource_operation_PID_thread_and_epoch_facts": True,
        "record_owns_exact_lease_weakref_and_finalizer_identity": True,
        "handle_binding_fields_are_authority": False,
        "construction_or_publication_BaseException_unwinds_exact_record": True,
        "never_published_callback": "non-authoritative no-op",
        "explicit_then_finalizer_completion": "non-authoritative no-op",
        "cleanup_required_is_monotonic": True,
        "cleanup_required_stores_exception_payload": False,
        "phase1_retains_exact_handle_and_blocks_admission": True,
        "exact_mutation_release_acknowledgment_is_condition_owned": True,
        "phase1_defensive_plain_mutation_release_states": (
            "mutation-active",
            "mutation-closing",
        ),
        "controller_close_proved_release_owner_changed": False,
        "phase1_sole_cleanup_blocker_uses_existing_cleanup_claim": True,
        "cleanup_claim_retains_handle_through_cleanup_actions": True,
        "standalone_local_retirement_acknowledgment": False,
        "operation_handle_binds_exact_lease_weakref_and_finalizer": False,
        "local_terminality_after_phase1_acknowledgment": True,
        "normal_retirement_owner": "explicit live admitted lease only",
        "normal_detach_evidence": (
            "successful return from the exact admission-bound finalizer.detach "
            "call while the resource condition is held"
        ),
        "already_dead_finalizer_is_detach_success": False,
        "finalizer_alive_false_is_retirement_proof": False,
        "weakref_clear_is_retirement_proof": False,
        "weakref_clear_plus_dead_finalizer_is_retirement_proof": False,
        "finalizer_or_GC_can_publish_normal_Active": False,
        "finalizer_detach_after_local_terminality": True,
        "finalizer_detach_before_resource_records_explicit_retirement": True,
        "resource_records_explicit_retirement_before_final_assignment": True,
        "direct_live_finalizer_invocation": (
            "orphan cleanup trigger only; never normal retirement"
        ),
        "collected_lease_evidence": (
            "loss signal that classifies pre-explicit-retirement operation as "
            "orphan cleanup"
        ),
        "lease_loss_after_explicit_retirement": (
            "adds no authority; existing resource phase may finish publication "
            "or current cleanup"
        ),
        "session_wrapper_retained_through_final_assignment": True,
        "claimed_cleanup_actions_precede_final_assignment": True,
        "claimed_cleanup_final_successor": (
            "terminal-X when observed lock cleanup is complete; otherwise "
            "non-admitting ordinary cleanup"
        ),
        "ordinary_operation_finalizer_forces_cleanup_without_current_disposal": True,
        "ordinary_operation_finalizer_drives_cleanup_only_when_disposal_is_current": False,
        "local_stateful_action_after_final_assignment": False,
        "matched_none_publication_acceptance": False,
        "internal_retry_after_linearization": (
            "Phase-1 observes exact handle absence and does not reauthorize publication"
        ),
        "semantic_response_loss_recovery": (
            "existing transition/global-stop fresh, replay, and conflict behavior"
        ),
        "fork_child_callback_authority": False,
    }
    assert value["repair_selectors"] == (
        "test_public_retained_lease_exit_envelope_matrix",
        "test_ordinary_invalid_preflight_process_control_context_graph_is_sanitized",
        "test_public_stabilization_helper_failures_occur_only_after_direct_poison",
        "test_public_stabilization_notification_failure_remains_poisoned_and_private",
        "test_exact_invocation_stabilizer_classifies_only_current_resource_records",
        "test_controller_resolution_cleanup_required_is_stabilizer_cleanup_owned",
        "test_invocation_correlation_invalid_wrong_unrepresented_and_duplicate_do_not_select_another_operation",
        "test_invocation_correlation_cleanup_owned_is_exact_and_fail_closed",
        "test_invocation_correlation_is_private_immutable_non_authoritative_identity",
        "test_underlying_commit_process_control_scrubs_coordinator_traceback_and_replays_once",
        "test_genuine_bound_public_guard_safe_error_has_complete_outward_privacy",
        "test_exception_traceback_sanitizer_is_cycle_bounded_and_identity_preserving",
        "test_hostile_exception_subclass_descriptors_are_not_invoked",
        "test_one_ordinary_sanitizer_core_failure_is_bounded_and_retried",
        "test_one_ordinary_failure_immediately_before_sanitizer_core_return_is_bounded",
        "test_public_primary_sanitizer_call_boundary_failure_preserves_process_control",
        "test_genuine_bound_safe_error_primary_sanitizer_failure_preserves_exact_error",
        "test_exact_record_post_poison_consistency_failure_never_reenables_admission",
        "test_mutation_usability_exit_boundaries_remain_fail_closed_without_poison",
        "test_competing_admission_before_poison_is_governed_after_linearization",
        "test_fork_child_poison_sees_invalidated_copy_and_cannot_retire_parent",
        "test_operation_retirement_entry_process_control_is_cleanup_safe",
        "test_operation_retirement_post_phase1_acknowledgment_process_control_is_cleanup_safe",
        "test_operation_retirement_post_local_terminal_pre_detach_process_control_is_cleanup_safe",
        "test_operation_retirement_post_detach_pre_final_publication_process_control_is_cleanup_safe",
        "test_operation_retirement_post_linearization_response_loss_preserves_final_state",
        "test_operation_retirement_post_linearization_durable_response_loss_uses_replay_without_duplicate_effect",
        "test_handle_side_disposition_cannot_change_resource_admission_truth",
        "test_object_setattr_on_every_handle_mirror_cannot_change_resource_record",
        "test_operation_retirement_final_assignment_is_last_authoritative_action",
        "test_operation_publication_requires_resource_owned_explicit_retirement",
        "test_direct_live_operation_finalizer_fails_closed_and_retry_reaches_terminal_x",
        "test_direct_live_finalizer_process_control_remains_fail_closed",
        "test_genuine_operation_collection_is_cleanup_only_and_reaches_x",
        "test_explicit_normal_retirement_records_detach_before_final_assignment",
        "test_lease_disappearance_phase_matrix",
        "test_session_wrapper_disappearance_matrix",
        "test_process_control_after_lease_loss_classification_reaches_terminal_x",
        "test_never_published_same_resource_and_stale_epoch_handles_reject",
        "test_cross_resource_operation_lease_cannot_authorize_retirement",
        "test_disposal_after_exact_mutation_release_before_operation_completion_remains_nonadmitting_and_reaches_terminal_x",
        "test_two_real_same_epoch_resources_reject_cross_wired_activity",
        "test_two_real_same_epoch_resources_reject_cross_wired_mutation_frame",
        "test_two_real_same_epoch_resources_reject_cross_wired_cleanup_cursor",
        "test_two_real_same_epoch_resources_reject_cross_wired_unproved_state",
    )
    assert value["repair_counterfactuals"] == {
        "selectors": (
            "test_entry_process_control_before_phase1_leaves_resource_admitting_is_causally_rejected",
            "test_vs1a_repair_counterfactual_is_causally_rejected",
            "test_vs1a_authenticity_counterfactual_is_causally_rejected",
            "test_explicit_retirement_runtime_counterfactual_fails_closed",
            "test_compiled_writer_source_mutant_is_killed",
            "test_exit_poison_compiled_source_mutant_is_causally_rejected",
        ),
        "evidence_classes": (
            "runtime causal cases",
            "compiled complete-module source mutants",
            "secondary AST/source guards",
        ),
        "exact_commands_counts_node_IDs_overlaps_and_group_inventories": (
            "report evidence, not governing architecture"
        ),
        "focused_inventory_owner": (
            "one literal selected-node-ID tuple in "
            "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py"
        ),
        "source_mutant_copies_are_external_to_the_repository": True,
        "direct_finalizer_counterfactual_04_reaches_orphan_mark_seam": True,
        "direct_finalizer_counterfactual_05_reaches_cleanup_successor_seam": True,
        "production_cases_reach_mutated_runtime_boundaries": True,
        "compiled_mutants_import_complete_writer_module_and_run_real_lifecycle": True,
        "noncausal_runtime_cases_counted": 0,
        "secondary_AST_source_guards_are_nonsemantic": True,
        "counterfactuals_pass_with_noop_owning_helper": False,
    }
    assert value["cleanup_claim"] == {
        "owner_identity": "weak reference to the exact threading.Thread object",
        "integer_get_ident_authority": False,
        "same_live_owner_resume": True,
        "other_live_thread_steal": False,
        "dead_owner_takeover": (
            "explicit new token and monotonically newer claim epoch"
        ),
        "recycled_integer_identifier_is_same_owner": False,
        "other_process_resume": False,
        "thread_affine_retained_connection_without_owner": (
            "remains truthfully unproved"
        ),
    }
    assert value["safe_error_traceback_privacy"] == {
        "scope": (
            "traceback fields in supported BaseException base traceback/cause/"
            "context/args/base-dictionary storage, BaseExceptionGroup base children, "
            "and BaseException values recursively reached through exact built-in "
            "tuple/list/dict/set/frozenset containers"
        ),
        "cycle_aware": True,
        "fixed_depth_cutoff": False,
        "base_descriptor_access": True,
        "subclass_dynamic_descriptors_or_slots": False,
        "arbitrary_user_attribute_traversal": False,
        "custom_container_iteration": False,
        "one_ordinary_primary_or_call_boundary_failure_contained": True,
        "real_cursor_producing_faults": (
            "separate transition and global-stop idempotency SELECT faults"
        ),
        "captured_cursor_path_SQL_and_parameters": (
            "covered by identity and exact built-in value"
        ),
        "cause_context_notes_args_and_rendered_content": (
            "contain no captured private authority"
        ),
        "safe_error": (
            "one exact content-free SQLiteMutationStoreError carried through a "
            "private disposition, activated on the genuine bound operation-guard "
            "path, caught at the outer public privacy boundary, sanitized in place, "
            "and bare-reraised by identity after sensitive bindings are cleared"
        ),
        "subclass_or_content_bearing_candidate": (
            "rejected and replaced by a fresh content-free "
            "database_integrity_failure"
        ),
        "governing_process_control": (
            "not converted to a safe disposition; exact object identity is "
            "preserved"
        ),
    }
    assert value["same_wrapper_uncertainty_retry"] == {
        "normal_connection_close_and_no_pending_disposal": (
            "ResumeActive after operation and mutation release"
        ),
        "transition_no_commit": (
            "later explicit call on the same wrapper is a fresh apply"
        ),
        "transition_underlying_commit": (
            "later explicit call on the same wrapper is exact replay"
        ),
        "global_stop_no_commit": (
            "later explicit call on the same wrapper is a fresh apply"
        ),
        "global_stop_underlying_commit": (
            "later explicit call on the same wrapper is exact replay"
        ),
        "retry_operation_and_connection": (
            "new operation lease and fresh transaction connection"
        ),
        "post_linearization_response_loss": (
            "later explicit same-wrapper call uses existing "
            "fresh/replay/conflict semantics"
        ),
        "automatic_retry_in_original_call": False,
        "duplicate_event_sequence_CAS_current_or_receipt_effect": False,
        "QU_or_QK_with_retained_connection": "non-reusable and cleanup-directed",
        "explicit_disposal_or_orphan_cleanup_pending": (
            "non-reusable and cleanup-directed"
        ),
        "process_control_cleanup": "ContinueCleanup toward X",
        "future_C2B3_initialization_recovery": (
            "separately Section-35 governed and X-gated; not generalized to "
            "existing replay"
        ),
    }
    assert value["b3c1b_test_resource_hygiene"] == {
        "classification": "test-resource lifetime hygiene only",
        "setup_BaseException_closes_exact_locally_owned_connection_and_bare_reraises": True,
        "ledger_installed_before_expected_error_or_assertion_exit": True,
        "ledger_cleanup": (
            "identity-scoped, idempotent, nonthrowing, and explicit"
        ),
        "direct_test_owned_connections": (
            "explicit close in finally after the preserved transaction boundary"
        ),
        "fault_injection_connections": (
            "real close before helper-level failure where proved, otherwise "
            "exact test ledger and explicit finally cleanup"
        ),
        "warning_suppression": False,
        "rollback_fencing_error_precedence_or_safe_vocabulary_changed": False,
    }
    assert value["b3c3_compatibility"] == {
        "classification": (
            "private rollback-only regression adaptation to the selected "
            "close-proof owner"
        ),
        "result_durability_public_or_authority_widening": False,
        "observes_sealed_retained_custody_proof_owner": True,
        "patches_generic_close_helper": False,
        "ordinary_rollback_only_cleanup_order_changed": False,
        "close_unproved_retains_governed_custody_until_explicit_cleanup": True,
        "COMMIT_or_commit_outcome_unknown_added": False,
        "owning_documentation_changed": False,
    }
    assert value["b2b_baseline_hygiene"] == (
        "pre-existing HEAD-exact test-resource hygiene",
        "strict warning-promotion debt",
        "not repaired by VS1A",
        "not VS1A authority or semantic behavior",
    )
    preserved = value["preserved"]
    assert preserved["cleanup_order"] == (
        "P0", "C1", "C2", "R1", "R2", "R3", "L1", "H1", "H2", "T1", "H3"
    )
    assert preserved["L1_H1_H2_T1_H3"] == "unchanged Section 35 semantics"
    assert preserved["transition_and_global_stop_nominal_apply"] is True
    assert preserved["exact_idempotency_replay"] is True
    assert preserved["QK_known_result_and_QU_uncertainty"] is True
    assert preserved["rollback_only_behavior"] is True
    assert preserved["public_delegation_shape"] is True
    assert preserved["fork_child_non_authority"] is True
    assert preserved["session_and_operation_finalizer_boundaries"] is True
    assert preserved["schema_migrations_dependencies_exports_and_public_API"] == (
        "unchanged"
    )
    assert value["absent_and_unauthorized"] == {
        "development_program_initialization": True,
        "development_durable_row_mutation": True,
        "VS1B": True,
        "worker_scheduler_service_network_Bridge_ES_or_Git_effect": True,
    }
    assert value["not_occurred"] == (
        "independent audit acceptance",
        "staging",
        "commit",
        "push",
        "publication",
    )
