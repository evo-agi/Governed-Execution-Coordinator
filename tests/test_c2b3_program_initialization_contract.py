"""Independent direct-literal oracle for the C2B3A initialization freeze."""

import ast
from copy import deepcopy
from pathlib import Path

import pytest


ORACLE_SOURCE_PATH = Path(__file__)
ORACLE_SOURCE_PARENT = ORACLE_SOURCE_PATH.parents[1]
ROOT = ORACLE_SOURCE_PARENT.resolve()
OWNER_PATH = ROOT / ".docs" / "c2b-durable-development-state.md"
PLANNING_PATH = ROOT / ".docs" / "c2b3-program-initialization.md"
TEST_PATH = ROOT / "tests" / "test_c2b3_program_initialization_contract.py"
BEGIN_MARKER = "<!-- C2B3_PROGRAM_INITIALIZATION_CONTRACT_PYTHON_BEGIN -->"
END_MARKER = "<!-- C2B3_PROGRAM_INITIALIZATION_CONTRACT_PYTHON_END -->"
VECTOR_BEGIN_MARKER = (
    "<!-- C2B3_PROGRAM_INITIALIZATION_GOLDEN_VECTOR_PYTHON_BEGIN -->"
)
VECTOR_END_MARKER = "<!-- C2B3_PROGRAM_INITIALIZATION_GOLDEN_VECTOR_PYTHON_END -->"
ALLOWED_ORACLE_IMPORTS = ("ast", "copy", "pathlib", "pytest")
ALLOWED_ORACLE_RELATIVE_PATHS = (
    ".docs/c2b-durable-development-state.md",
    ".docs/c2b3-program-initialization.md",
    "tests/test_c2b3_program_initialization_contract.py",
)
PLANNING_PROJECTION_BEGIN_MARKER = "<!-- C2B3A_PLANNING_PROJECTION_BEGIN -->"
PLANNING_PROJECTION_END_MARKER = "<!-- C2B3A_PLANNING_PROJECTION_END -->"
EXPECTED_PLANNING_PROJECTION = """# C2B3 Program Initialization

<!-- C2B3A_PLANNING_PROJECTION_BEGIN -->

<!-- C2B3A_PLANNING_NON_AUTHORITY_BEGIN -->
## Non-authority declaration

This file is a planning and implementation-status projection only. It is not
semantic authority. Section 35 of `.docs/c2b-durable-development-state.md` is
the sole C2B3A semantic owner. Planning cannot create, override, widen, narrow,
resolve, or change a structured owner value, and wording here cannot supply
operative semantics when a structured owner value exists.
<!-- C2B3A_PLANNING_NON_AUTHORITY_END -->

<!-- C2B3A_PLANNING_CURRENT_STATUS_BEGIN -->
## Current status

C2B3A remains a target-contract freeze. The unstaged C2B Pre-I/O VS1A
candidate selects controller-exclusive connection custody and an exact scope-
token activation acknowledgment before COMMIT. After close, the controller
supplies immutable facts only; under the writer-resource lock, the resource
observes current disposal posture, selects the actual successor, and publishes
it through one lifecycle assignment. Exact publication acknowledgment precedes
scope-alias clearing, and scope use is already invalid after assignment. Normal
return from the retained-custody owner's direct exact-object `close()` is the
sole closure proof; a repeated close is permitted only while proof is absent.
Pre-close resumption policy is distinct from field-free post-proof
`ResumeActive`. Disposal and governing process control strengthen or convert
resumption to cleanup, so later completion cannot restore Active. Operation
admission publishes an immutable resource-owned record containing copied
resource/operation/PID/thread/epoch facts and the exact admitted lease weak
reference and finalizer identity. Handle-side binding fields are compatibility
observations only and cannot replace that authority. Retirement first records
an exact condition-owned non-admitting preparation. Normal retirement is then
owned only by the still-live admitted lease: under that same condition, the
resource records local terminality, calls `detach()` on the exact bound
finalizer, and records `EXPLICIT_RETIRED` only from that call's exact successful
return. A dead finalizer, `alive == False`, weak-reference clearing, GC, object
loss, or a caller-built acknowledgment is never retirement proof.
Plain mutation-active/closing retirement defensively records exact slot release;
controller close-proved release ownership is unchanged. If the operation is the
sole cleanup blocker, Phase 1 uses the existing cleanup claim and retains the
record while credential/lock cleanup runs before publication. Finalizer
execution, direct invocation, GC, and lease or wrapper loss before
`EXPLICIT_RETIRED` classify only orphan cleanup, keep admission frozen, and can
reach X without restoring Active. Lease loss after `EXPLICIT_RETIRED` adds no
authority; it can only finish publication already authorized by the stored
resource phase or follow current cleanup posture.
One final resource lifecycle assignment under that same condition removes the
exact record and is the operation-completion linearization point. Python method
return is caller observation only. The two vulnerable retained-lease public
callers, transition apply and global-stop apply, now place one caller-side
process-control envelope around pre-admission correlation creation and the
nested operation-guard helper. One private immutable exact-object token exists
before that helper can admit. Admission validates the token's exact resource,
PID, and epoch and binds it through the exact handle retained by the immutable
resource record in the same condition-protected lifecycle assignment. The
envelope never derives correlation from a returned lease or post-return handle.
It receives compiler-cleanup, `__exit__`, and `_close()` escapes, including
their first traceable opcodes; neither internal method claims to protect its own
first opcode. Before poison, the stabilizer checks only the token's exact type,
directly stored resource identity, and the resource's direct fork-invalid
owner-PID sentinel, acquires the condition, directly inspects the current exact
lifecycle-state type and exact immutable record
tuple, and recognizes the current record through direct frozen/slotted fields
and token-object identity. It reads no lifecycle property and calls no project
or policy helper. One exact match is followed immediately by direct poison
assignment under the condition. Only afterward may `_state_authority` derive
authority and validate PID, epoch, resource, correlation, record, and handle
consistency; failure leaves poison set. Absence proves neither no admission nor
prior final assignment and does not poison. Post-poison classification
distinguishes represented incomplete from represented cleanup-owned. Detailed
record replacement, successor construction, and notification follow poison and
cannot reset it; controller resolution with
`_CleanupRequiredAfterResolution` is represented cleanup-owned. The one-way
poison blocks operation and mutation admission and every admitting successor
while bounded cleanup continues toward X.

After stabilization, a bounded cycle-aware sanitizer clears traceback fields
in the supported graph: `BaseException` base traceback, cause, context, args,
and base instance dictionary; `BaseExceptionGroup` base children; and
`BaseException` values recursively reached through exact built-in `tuple`,
`list`, `dict`, `set`, and `frozenset` containers. Bound base-class descriptors
and exact built-in operations prevent exception-field dispatch. Subclass
dynamic descriptors, arbitrary subclass slots, arbitrary user-object
attributes, and custom container iteration are excluded. Each base traceback
is cleared before the exception's other base fields are read. Exact identity,
type, args, `SystemExit.code`, suppression, notes, instance-dictionary content,
group-child identity, and cause/context links remain unchanged before bare
reraise. One ordinary primary-traversal or call-boundary failure is contained
and followed by one independently bound non-dispatching fallback, so it cannot
replace the outward exception. Repeated asynchronous interruption,
catastrophic allocation failure, and unsupported private mutation of bound
defaults or C-level descriptors are outside the guarantee. The same outer
privacy boundary handles an exact content-free safe store error through each
genuine bound public operation guard, without process-control poisoning or
reconstruction.
The separate `require_usable_for_mutation` use remains an already fail-closed
ephemeral/unbound-lease path: its reproduced compiler boundary loses the last
lease reference and reaches X through existing finalizer cleanup without the
caller envelope or poison, while reachable exit boundaries are prepared as
non-admitting. Wrong-PID and fork-child non-authority remain unchanged. Later
pre-assignment process control retains the record and strengthens cleanup;
post-assignment process control preserves the assigned state and uses existing
explicit fresh/replay/conflict semantics. An absent or never-published handle
cannot prove prior completion; internal retirement retry stops at exact handle
absence, with no completion receipt or registry. Each writer resource also allocates one opaque
identity shared by its authority, operations, slot/frame, controller token,
connection custody/proof, cleanup cursors, and claim, with authority comparisons
only by `is`. Exact closed variants and single-owned structural cursors replace
the rejected broad snapshot and completed-step model. Cleanup claims bind the
exact `threading.Thread` object with explicit dead-owner takeover. Sensitive
mutation frames return one private safe
disposition; after their bindings clear, the outer public boundary catches,
sanitizes, and bare-reraises the same exact content-free store-error object by
identity. A normal transaction-
connection close with no pending disposal restores the same transition/global-
stop wrapper for a later explicit fresh apply or exact replay; QU/QK and
disposal-pending postures remain non-reusable. The B3c1a contract-projection
test keeps its existing node ID and replaces only its obsolete post-GC Active
expectation: loss before `EXPLICIT_RETIRED` is `ORPHANED`, non-admitting,
cleanup-owned, and eventually X. The B3c1b change is connection-
lifetime hygiene only. The B3c3 change is a private rollback-only regression
adaptation to the selected close-proof owner with no result, durability, public,
or authority widening. The unchanged B2b issue is pre-existing HEAD-exact test-
resource hygiene, strict warning-promotion debt, not repaired by VS1A, and not
VS1A authority or semantic behavior. The candidate has exactly twenty-two dirty
paths: twenty-one tracked modifications, the sole untracked shared-foundation
test, and zero staged paths, including the intentional B3c1a contract
replacement in `tests/test_b3c1a_writer_session_authority.py`. A fresh
independent audit remains pending. The accepted B4b one-byte zero-Coordinator-
frame privacy contract replacement in
`tests/test_b4b_private_atomic_global_stop_persistence.py` remains unchanged.
These bytes have not been staged, committed, pushed, or published. These scope
counts are report-only observations bound to the exact candidate provenance,
not architectural invariants.

The repaired candidate keeps runtime causal cases, compiled complete-module
source mutants, and secondary AST/source guards as distinct evidence classes.
The shared-foundation test is the owning surface, and its focused inventory is
one literal tuple of selected node IDs. Exact commands, changing node totals,
warning totals, overlaps, and validation-group file inventories are report
evidence rather than governing architecture. Source mutants use external
copies and leave the live repository unchanged. Direct-finalizer
counterfactuals still assert reachability at their actual orphan-mark or
cleanup-successor seam. This is candidate validation evidence only; it is not
an independent-audit acceptance claim.

The implemented database remains application generation 2 at terminal
migration `0002_development_program_and_effect_state`. VS1A adds no program-
initialization command, durable development row, reader, replay, recovery, or
author-effect source; it performs no worker, model, Git, Execution Substrate,
Bridge, network, or other external effect; and it changes no schema or
migration. Section-35 C2B3 initialization recovery/replay remains target-only
and affected-resource X-gated. Existing transition and global-stop idempotency/
replay remain same-wrapper capable after proved normal close and are not subject
to that future initialization gate. C2B3B/VS1B remains absent and unauthorized.

The structured owner value
`commit_close_outcome_addendum.normative_surface_and_precedence` makes
`commit_close_outcome_addendum` the sole operative authority for COMMIT/close
outcomes, process-control relationships, cleanup states and order, finalizer
and liveness rules, recovery and replay gates, and future C2B3B path scope.
The bounded prose in Section 35 and this projection have no independent
semantic authority.
<!-- C2B3A_PLANNING_CURRENT_STATUS_END -->

<!-- C2B3A_PLANNING_LEGACY_LEDGER_BEGIN -->
## Legacy-ledger projection

Section 35 classifies
`commit_uncertainty_cleanup_gate.close_not_proved.process_control_exception_graph_ledger`
as `historical_runtime_observation`, with `normative=false`,
`operative_for_c2b3b=false`, `portable_contract=false`, and
`preserved_for_original_c2b3a_evidence=true`. Its target semantics are
superseded by `process_control_relational_policy`. No implementation, test
oracle, planning projection, or future prompt may use its observed graph or
traceback values as target requirements.

The operative process-control rule is deliberate-action-only. C2B3 does not
deliberately assign, clear, restore, scrub, sanitize, or manufacture graph or
traceback state; it deliberately creates no primary-to-secondary relation and
does not serialize, persist, log, render, report, or copy raw process control.
Interpreter-managed graph and traceback effects remain permitted, and no exact
resulting graph or traceback shape is promised.
<!-- C2B3A_PLANNING_LEGACY_LEDGER_END -->

<!-- C2B3A_PLANNING_ACTIVE_SCOPE_BEGIN -->
## Active future-scope projection

The preserved 23-expected, 24-maximum, and twenty-fifth-path-stop material is
historical and non-operative. `consumers_may_use` remains false. The only
operative future scope is the structured owner value
`commit_close_outcome_addendum.future_c2b3b_path_scope_status` for
`C2B3B_PRIVATE_ATOMIC_INITIALIZATION`.

Production is exactly six paths:

- `src/ge_nwp_coordinator/_development_program_initialization_contracts.py`
- `src/ge_nwp_coordinator/_sqlite_development_program_initialization.py`
- `src/ge_nwp_coordinator/sqlite_transition_transaction.py`
- `src/ge_nwp_coordinator/sqlite_writer_session.py`
- `src/ge_nwp_coordinator/sqlite_connection.py`
- `src/ge_nwp_coordinator/state_authority_lock.py`

Documentation/status is exactly ten paths:

- `.docs/c2b-durable-development-state.md`
- `.docs/c2b3-program-initialization.md`
- `.docs/c2b2-private-readers.md`
- `.docs/architecture.md`
- `.docs/durable-state-model.md`
- `.docs/sqlite-operations-and-recovery.md`
- `.docs/sqlite-threat-model.md`
- `.docs/writer-session-authority.md`
- `README.md`
- `AGENTS.md`

Required changed tests are exactly eleven paths:

- `tests/test_c2b3_program_initialization_contract.py`
- `tests/test_c2b3_private_atomic_program_initialization.py`
- `tests/test_c2b3_program_initialization_recovery.py`
- `tests/test_c2b3_private_program_initialization_delegation.py`
- `tests/test_c2b2_field_level_contract.py`
- `tests/test_c2b2_development_reader_contracts.py`
- `tests/test_sqlite_b2c_writer_session.py`
- `tests/test_state_authority_lock.py`
- `tests/test_runtime_non_authority.py`
- `tests/test_architecture_contracts.py`
- `tests/test_c2b0_durable_state_contract.py`

The one contingency path is
`tests/test_c2b2_private_development_readers.py`. The exact expected count is
`6 + 10 + 11 = 27`; the exact maximum is 28; a twenty-ninth path is a hard
stop and scope-reassessment condition.

The four newly required paths relative to the historical manifest are
`src/ge_nwp_coordinator/state_authority_lock.py`,
`.docs/writer-session-authority.md`,
`tests/test_state_authority_lock.py`, and
`tests/test_sqlite_b2c_writer_session.py`. This projection authorizes no C2B3B
source or implementation.
<!-- C2B3A_PLANNING_ACTIVE_SCOPE_END -->

<!-- C2B3A_PLANNING_VALIDATION_ACCEPTANCE_BEGIN -->
## Validation, source acceptance, and sequencing

These are process and acceptance gates projected from the project lifecycle;
they do not make this planning file semantic authority.

Future C2B3B tests use private temporary databases only. They never open
operator state, migrate operator state, or inspect operator-state contents.
Project-protocol existence or absence checks remain allowed, but no operator
database open or migration is permitted.

Before C2B3B source is accepted, all of the following separate evidence is
required:

- an accepted fresh independent read-only source-acceptance audit;
- the exact committed C2B3A contract baseline;
- a distinct committed Coordinator repository baseline;
- a refreshed exact Coordinator snapshot, or an explicitly equivalent exact
  strategic baseline, produced after and bound to that committed baseline;
- the committed direct independent oracle;
- the then-current generation-2 schema and accepted C2B2 row and reader
  identities;
- the exact finite 27-expected / 28-maximum / path-29-stop source proposal and
  protected complement;
- no WorkSpec custody, lookup, retrieval, leakage, logging, report transport,
  or traceback retention;
- one-database, one-writer, one-mutation-slot, and one-controller reuse;
- exact replay and recovery proof requirements; and
- zero public, schema, migration, package, authority, route, external-I/O, or
  cross-repository widening.

The committed Coordinator repository baseline and the refreshed exact
Coordinator snapshot or explicitly equivalent exact strategic baseline are
separate evidence items. Neither substitutes for the other, and the fresh
source-acceptance audit does not itself establish that the snapshot was
refreshed.

Acceptance of this planning projection is not acceptance of future source.

Before source mutation begins, C2B3B source implementation requires all of the
following separate evidence:

- an accepted independent audit of the committed C2B3A contract baseline;
- a committed clean Coordinator baseline;
- a refreshed exact Coordinator snapshot or explicitly equivalent exact
  strategic baseline bound to that clean committed baseline;
- an exact C2B3B source implementation prompt;
- fresh opening repository and patch provenance;
- the accepted 27-expected / 28-maximum future path scope and a hard stop if a
  twenty-ninth path is required; and
- the private-test database and operator-state non-access boundaries above.

A dirty four-file working tree is not a source baseline.

C2B3C is the author-effect contract freeze. C2B3D cannot begin before the
C2B3C owner questions are closed. Pending authority evidence remains inert and
is not verification, permission, route eligibility, ES admission, or worker
authorization. C2B4, C2B5, and C2B6 remain separate later tranches. Migration
0003 remains reserved and unimplemented.
<!-- C2B3A_PLANNING_VALIDATION_ACCEPTANCE_END -->

<!-- C2B3A_PLANNING_PRODUCTION_NONIMPLEMENTATION_BEGIN -->
## Production nonimplementation

C2B3A implements or authorizes no production mutation, receipt, private
delegation, recovery resolver, author effect, worker, scheduler, queue,
service, model client, direct-local execution, Execution Substrate invocation,
Bridge integration, schema, migration, package export, public model,
`StateStore` method, or `WriterSession` public-protocol change. C2B3B remains
absent and requires a separately authorized implementation tranche and a fresh
independent read-only audit.
<!-- C2B3A_PLANNING_PRODUCTION_NONIMPLEMENTATION_END -->

<!-- C2B3_NARROWED_PLANNING_BEGIN -->
## Governing vertical-slice narrowing projection

Section 36 of `.docs/c2b-durable-development-state.md` is the sole semantic
owner for this narrowing. This planning projection selects no new value,
digest, relation, migration inventory, or physical schema.

The preserved initialization and later author-effect adapter selections are
non-operative for the first vertical slice. Initialization has no adapter,
host, transport, endpoint, delivery, or external request. The first route is
selected at author-effect delivery and uses `direct_local_bootstrap`, meaning a
bounded direct/non-ES path to one qualified remote Linux host—not the user's
Mac, the Coordinator host, or physical colocation. No third adapter exists.

The old horizontal sequence, route-specific latch shape, path-count manifests,
and migration/initialization target shapes are reopened rather than replaced.
The policy still permits at most one productive bootstrap acceptance and,
after semantic acceptance, one separate isolated local feature-branch commit.
Push, remote-ref mutation, PR, merge, deployment, and publication remain zero;
an ambiguous Git outcome never permits a blind second commit.

Required dependency order is pre-I/O progression, remote contact through
semantic decision, separate local Git and stop, then ES migration before
another productive bootstrap slice. The exact initialization graph, custody,
verification, invocation, capsule, evidence, Git protocol, reconciliation,
replay/recovery, latch representation, migration relations, reliable submit,
and conformance details remain just-in-time design questions.

All non-superseded committed C2B3A one-writer, transaction, COMMIT/close,
cleanup, replay, recovery, privacy, process-control, and no-external-I/O
semantics remain operative. C2B3 source remains unauthorized.
<!-- C2B3_NARROWED_PLANNING_END -->

<!-- C2B3A_PLANNING_PROJECTION_END -->
"""


EXPECTED_INITIALIZATION_CONTRACT = {
    "contract_identity": {
        "workstream": "COORDINATOR_C2B3A_PROGRAM_INITIALIZATION_CONTRACT_FREEZE",
        "repository_tranche": "C2B3 — Program Initialization And Author-Effect Establishment",
        "this_freeze": "C2B3A program-initialization contract only",
        "semantic_owner": ".docs/c2b-durable-development-state.md#35-c2b3a-program-initialization-contract-freeze",
        "status_record": ".docs/c2b3-program-initialization.md",
        "status_record_authority": "planning only; not semantic authority",
        "implementation_status": "contract frozen; production source absent",
    },
    "tranche_boundary": {
        "C2B3A": "program-initialization contract only",
        "C2B3B": "later private atomic initialization implementation",
        "C2B3C": "later author-effect contract freeze",
        "C2B3D": "later private atomic author-effect implementation",
        "combined_family_implementation": False,
    },
    "five_path_scope": {
        "tracked_modifications": (
            ".docs/c2b-durable-development-state.md",
            "tests/test_c2b0_durable_state_contract.py",
            "AGENTS.md",
        ),
        "untracked_additions": (
            ".docs/c2b3-program-initialization.md",
            "tests/test_c2b3_program_initialization_contract.py",
        ),
        "total_paths": 5,
        "production_source_paths": (),
        "migration_paths": (),
        "schema_paths": (),
        "public_api_paths": (),
    },
    "owner_decisions": {
        "initial_work_item_count": 1,
        "initial_work_spec_count": 1,
        "membership_ordinal": 0,
        "first_author_attempt_number": 1,
        "initial_author_basis": ("initialize", "program_genesis"),
        "planned_adapter_kind": "execution_substrate",
        "route_effect": "absent",
        "work_spec_ingress": "same-call transient only",
        "work_spec_custody": "absent",
        "recovery_lifecycle": "close-complete-gated later call under a newly acquired concrete session and fresh operation lease",
        "automatic_semantic_retry": False,
        "family_graph_membership": "family-created rows only",
        "duplicate_program_classification": "semantic_identity_conflict",
    },
    "initialization_golden_vector": {
        "owner_literal_marker": "C2B3_PROGRAM_INITIALIZATION_GOLDEN_VECTOR_PYTHON",
        "oracle_literal_name": "EXPECTED_INITIALIZATION_GOLDEN_VECTOR",
        "vector_id": "c2b3a-initialization-single-work-v1",
        "vector_version": 1,
        "family": "initialize_development_program",
        "single_work": True,
        "direct_owner_literal": True,
        "direct_independent_oracle_literal": True,
        "oracle_runtime_derivation": False,
        "proves_implementation": False,
        "required_components": (
            "all safe command input values",
            "exact WorkSpec safe-projection mapping",
            "exact accepted-intent canonical mapping and UTF-8 byte-hex",
            "accepted-intent safe-projection digest",
            "exact safe-command canonical mapping and UTF-8 byte-hex",
            "command digest",
            "one transaction timestamp",
            "all nine complete persisted row mappings and applicable self-digests",
            "program-head and work-item-head historical postimages",
            "all eight ordered graph entries with rank, role, ordinal, ref, and digest",
            "exact result projection and digest",
            "mutation-graph digest",
            "complete mutation-receipt scalar envelope",
            "private committed result",
            "private exact-replay result",
        ),
    },
    "semantic_ref_ownership": {
        "owner": "semantic caller",
        "preassigned_refs": (
            "mutation_ref",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "decision_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "work_spec_ref",
            "preassigned_semantic_attempt_ref",
            "preassigned_candidate_ref",
        ),
        "initializer_generated_semantic_refs": (),
        "forbidden_ref_derivations": (
            "random",
            "UUID",
            "clock-derived",
            "rowid-derived",
            "implicit",
        ),
        "coordinator_derived_values": (
            "fixed genesis numbers and states",
            "dense ordinal 0",
            "one transaction timestamp",
            "safe projections",
            "canonical identities",
            "row digests",
            "result projection digest",
            "mutation graph digest",
            "complete locator material",
        ),
    },
    "existing_work_spec_safe_projection": {
        "semantic_name": "DevelopmentWorkSpecSafeProjection",
        "schema_id": "governed-execution.nwp-development-work-spec-safe-projection.v1",
        "digest_domain": "governed-execution.nwp-development-work-spec-safe-projection.v1.identity",
        "ordered_fields": (
            "schema_id",
            "work_spec_ref",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "repository_ref",
            "base_git_object_format",
            "base_git_oid",
            "authorized_paths",
            "validation_requirement_ref",
            "review_requirement_ref",
            "privacy_classification",
            "work_spec_digest",
            "safe_projection_digest",
        ),
        "replacement_invented": False,
        "source_or_identity_modified": False,
    },
    "accepted_intent_safe_projection": {
        "semantic_name": "DevelopmentAcceptedIntentSafeProjectionV1",
        "schema_id": "governed-execution.nwp-development-accepted-intent-safe-projection.v1",
        "digest_domain": "governed-execution.nwp-development-accepted-intent-safe-projection.v1.identity",
        "ordered_fields": (
            "schema_id",
            "source_intent_ref",
            "source_intent_digest",
            "initial_work_spec_safe_projection",
            "safe_projection_digest",
        ),
        "identity_excludes": ("safe_projection_digest",),
        "nested_projection_exact_type": "DevelopmentWorkSpecSafeProjection",
        "derived_from": (
            "caller-supplied source_intent_ref",
            "caller-supplied source_intent_digest",
            "exact transient WorkSpecV1",
            "existing WorkSpec safe-projection builder",
        ),
        "caller_forbidden": (
            "completed accepted-intent projection",
            "safe_projection_digest",
            "generic mapping",
            "substitute WorkSpec safe projection",
            "subclass or structural stand-in",
        ),
        "private_fields_absent": (
            "objective",
            "requirements text",
            "exclusions text",
            "prompt",
            "response",
            "transcript",
            "credential",
            "endpoint",
            "retrieval material",
            "capsule content",
            "workspace path",
        ),
        "persisted_row_fields": (
            "source_intent_ref",
            "source_intent_digest",
            "safe_projection_digest",
        ),
    },
    "sensitive_ingress": {
        "work_spec_type": "exact built-in WorkSpecV1",
        "work_spec_count": 1,
        "container_ingress": False,
        "additional_inputs": (
            "all preassigned safe semantic refs",
            "caller-supplied source_intent_ref",
            "caller-supplied source_intent_digest",
            "expected coding_global_stop_ref",
            "expected coding_global_stop_version",
        ),
        "caller": "future Coordinator-internal semantic/progression caller already holding the exact value",
        "possession_meaning": "input provenance only; not executable authority",
        "closed_outcomes": (
            "one complete safe initialization command",
            "one closed privacy-safe failure discriminant",
        ),
        "retrieval_by_ref": False,
        "restart_safe_retrieval": False,
        "private_custody_store": False,
    },
    "safe_command": {
        "semantic_name": "DevelopmentProgramInitializationCommandV1",
        "schema_id": "governed-execution.nwp-initialize-development-program-command.v1",
        "digest_domain": "governed-execution.nwp-initialize-development-program-command.v1.identity",
        "ordered_fields": (
            "schema_id",
            "mutation_ref",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "decision_ref",
            "preassigned_semantic_attempt_ref",
            "preassigned_candidate_ref",
            "coding_global_stop_ref",
            "coding_global_stop_version",
            "reason_code",
            "work_spec_safe_projection",
            "accepted_intent_safe_projection",
            "command_digest",
        ),
        "exact_field_types": (
            ("schema_id", "str"),
            ("mutation_ref", "str"),
            ("program_ref", "str"),
            ("program_version_ref", "str"),
            ("accepted_intent_revision_ref", "str"),
            ("decision_ref", "str"),
            ("preassigned_semantic_attempt_ref", "str"),
            ("preassigned_candidate_ref", "str"),
            ("coding_global_stop_ref", "str"),
            ("coding_global_stop_version", "int excluding bool"),
            ("reason_code", "str"),
            ("work_spec_safe_projection", "exact DevelopmentWorkSpecSafeProjection"),
            ("accepted_intent_safe_projection", "exact DevelopmentAcceptedIntentSafeProjectionV1"),
            ("command_digest", "str"),
        ),
        "reason_code": "program_genesis",
        "identity_excludes": ("command_digest",),
        "digest_owner": "Coordinator sensitive reducer",
        "cross_relations": (
            "work_spec_safe_projection.program_ref == command.program_ref",
            "work_spec_safe_projection.program_version_ref == command.program_version_ref",
            "work_spec_safe_projection.accepted_intent_revision_ref == command.accepted_intent_revision_ref",
            "accepted_intent_safe_projection.initial_work_spec_safe_projection == command.work_spec_safe_projection",
            "accepted_intent_safe_projection.source_intent_ref == persisted accepted-intent source_intent_ref",
            "accepted_intent_safe_projection.source_intent_digest == persisted accepted-intent source_intent_digest",
            "preassigned_attempt_candidate_binding.work_item_ref == safe command work_spec_safe_projection.work_item_ref == sole program-version membership work_item_ref == sole WorkSpec binding work_item_ref",
            "preassigned_attempt_candidate_binding.work_item_revision_ref == safe command work_spec_safe_projection.work_item_revision_ref == sole program-version membership work_item_revision_ref == sole WorkSpec binding work_item_revision_ref",
            "preassigned_attempt_candidate_binding.preassigned_semantic_attempt_ref == safe command preassigned_semantic_attempt_ref == initialize decision preassigned_semantic_attempt_ref",
            "preassigned_attempt_candidate_binding.preassigned_candidate_ref == safe command preassigned_candidate_ref == initialize decision preassigned_candidate_ref",
        ),
        "rejects": (
            "Boolean as integer",
            "subclasses",
            "coercion",
            "generic mappings",
            "extension fields",
            "optional metadata",
            "caller-supplied digests",
            "implicit refs",
            "zero WorkSpecs",
            "multiple WorkSpecs",
            "caller-supplied membership ordinal",
            "implicit sorting",
        ),
        "contains_complete_work_spec": False,
    },
    "genesis_cardinality": {
        "program_versions": 1,
        "accepted_intent_revisions": 1,
        "work_item_heads": 1,
        "work_item_revisions": 1,
        "program_version_memberships": 1,
        "work_spec_safe_bindings": 1,
        "preassigned_attempt_candidate_binding": {
            "ordered_fields": (
                "work_item_ref",
                "work_item_revision_ref",
                "preassigned_semantic_attempt_ref",
                "preassigned_candidate_ref",
            ),
            "relations": (
                "preassigned_attempt_candidate_binding.work_item_ref == safe command work_spec_safe_projection.work_item_ref == sole program-version membership work_item_ref == sole WorkSpec binding work_item_ref",
                "preassigned_attempt_candidate_binding.work_item_revision_ref == safe command work_spec_safe_projection.work_item_revision_ref == sole program-version membership work_item_revision_ref == sole WorkSpec binding work_item_revision_ref",
                "preassigned_attempt_candidate_binding.preassigned_semantic_attempt_ref == safe command preassigned_semantic_attempt_ref == initialize decision preassigned_semantic_attempt_ref",
                "preassigned_attempt_candidate_binding.preassigned_candidate_ref == safe command preassigned_candidate_ref == initialize decision preassigned_candidate_ref",
            ),
            "future_lineage_only": True,
            "creates_selects_authorizes_or_executes_attempt_or_candidate": False,
        },
        "hidden_selection_rule": False,
        "permanent_one_work_item_architecture": False,
        "later_additional_work_owner": "C2B6 replan mechanics",
    },
    "row_and_head_ledger": {
        "inserted_row_count": 9,
        "inserted_rows": (
            "program_head",
            "program_version",
            "accepted_intent_revision",
            "work_item_head",
            "work_item_revision",
            "program_version_work_item",
            "work_spec_binding",
            "initialize_decision",
            "mutation_receipt",
        ),
        "postimages": {
            "program_head": (
                ("current_program_version_number", 1),
                ("current_program_version_ref", "exact program_version_ref"),
                ("head_revision", 0),
                ("program_state", "active"),
            ),
            "program_version": (
                ("program_version_number", 1),
                ("program_version_kind", "initial"),
                ("creating_decision_ref", "exact decision_ref"),
            ),
            "accepted_intent_revision": (
                ("accepted_intent_revision_number", 1),
                ("prior_accepted_intent_revision_ref", None),
                ("safe_projection_digest", "derived accepted-intent safe_projection_digest"),
            ),
            "work_item_head": (
                ("current_work_item_revision_number", 1),
                ("current_work_item_revision_ref", "exact work_item_revision_ref"),
                ("head_revision", 0),
                ("work_state", "planned"),
            ),
            "work_item_revision": (
                ("work_item_revision_number", 1),
                ("work_item_revision_kind", "initial"),
                ("prior_work_item_revision_ref", None),
            ),
            "program_version_work_item": (
                ("membership_ordinal", 0),
                ("work_item_ref", "exact work_item_ref"),
                ("work_item_revision_ref", "exact work_item_revision_ref"),
            ),
            "work_spec_binding": (
                ("safe_projection", "exact existing DevelopmentWorkSpecSafeProjection"),
                ("recorded_at", "one transaction timestamp"),
            ),
            "initialize_decision": (
                ("decision_kind", "initialize"),
                ("decision_variant", "program_genesis"),
                ("basis_decision_ref", None),
                ("basis_program_version_ref", None),
                ("basis_semantic_attempt_ref", None),
                ("basis_effect_intent_ref", None),
                ("expected_program_head_revision", 0),
                ("resulting_program_version_number", 1),
                ("resulting_program_version_ref", "exact program_version_ref"),
                ("selected_semantic_attempt_ref", None),
                ("selected_candidate_ref", None),
                ("preassigned_semantic_attempt_ref", "exact preassigned_semantic_attempt_ref"),
                ("preassigned_candidate_ref", "exact preassigned_candidate_ref"),
                ("reason_code", "program_genesis"),
            ),
            "mutation_receipt": (
                ("mutation_family", "initialize_development_program"),
                ("outcome", "committed"),
            ),
        },
        "single_transaction_timestamp": True,
        "absent_rows_and_effects": (
            "revision_edge",
            "semantic_attempt",
            "effect",
            "command row",
            "delivery",
            "observation",
            "capsule",
            "Git row",
            "external request",
        ),
    },
    "write_order": {
        "foreign_keys_continuously_enabled": True,
        "ordered_rows": (
            "program_head",
            "accepted_intent_revision",
            "work_item_head",
            "work_item_revision",
            "initialize_decision",
            "program_version",
            "program_version_work_item",
            "work_spec_binding",
            "mutation_receipt",
        ),
    },
    "initialize_graph": {
        "entry_count": 8,
        "receipt_is_envelope": True,
        "receipt_is_entry": False,
        "entries": (
            (0, "program_head_postimage", 0, "program_ref"),
            (1, "accepted_intent_revision", 0, "accepted_intent_revision_ref"),
            (2, "initialize_decision", 0, "decision_ref"),
            (3, "program_version", 0, "program_version_ref"),
            (4, "work_item_head_postimage", 0, "work_item_ref"),
            (5, "work_item_revision", 0, "work_item_revision_ref"),
            (6, "program_version_work_item", 0, "work_item_ref"),
            (7, "work_spec_binding", 0, "work_spec_ref"),
        ),
        "ordering": ("rank ASC", "ordinal ASC"),
        "mutable_preimages": "exact absence; not graph entries",
        "basis_and_global_stop_rows": "verified dependencies; not graph entries",
        "same_ref_distinct_roles_allowed": "work_item_ref",
        "digest_primitive": "existing common supplied-entry mutation-graph digest primitive",
    },
    "complete_graph_locator": {
        "starts_from": ("exact safe command", "mutation receipt"),
        "lookups": (
            "receipt by mutation_ref",
            "initialize decision and resulting version by program_ref + decision_ref",
            "accepted-intent revision by program_ref + accepted_intent_revision_ref",
            "program head by program_ref",
            "sole complete membership by program_ref + program_version_ref",
            "work-item head and exact revision by program_ref + work_item_ref + work_item_revision_ref",
            "WorkSpec binding by exact program/version/work/revision identity, then exact work_spec_ref equality",
        ),
        "completeness": (
            "exactly one membership",
            "membership ordinal 0",
            "exactly one matching WorkSpec binding",
            "returned binding work_spec_ref equals safe-command work_spec_ref and graph-entry expected work_spec_ref",
            "all row self-digests valid",
            "all cross-row relations valid",
            "historical program-head postimage valid",
            "historical work-head postimage valid",
            "persisted result projection valid",
            "mutation graph digest valid",
        ),
        "physical_lookup_key": (
            "program_ref",
            "program_version_ref",
            "work_item_ref",
            "work_item_revision_ref",
        ),
        "returned_work_spec_ref_mismatch": "database_integrity_failure",
        "forbidden_selection": ("absence", "latest row", "timestamp", "rowid", "scan", "different WorkSpec"),
        "generic_graph_engine": False,
        "future_reads": "bounded family-specific absence/collision reads only",
    },
    "persisted_result_projection": {
        "schema_id": "governed-execution.nwp-initialize-development-program-result.v1",
        "digest_domain": "governed-execution.nwp-initialize-development-program-result.v1.identity",
        "ordered_fields": (
            "schema_id",
            "program_ref",
            "decision_ref",
            "result_program_version_ref",
            "result_decision_ref",
        ),
        "result_program_version_ref": "exactly program_version_ref",
        "result_decision_ref": "exactly decision_ref",
    },
    "private_apply_result": {
        "semantic_name": "DevelopmentProgramInitializationResultV1",
        "ordered_fields": (
            "disposition",
            "mutation_ref",
            "command_digest",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "decision_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "work_spec_ref",
            "preassigned_semantic_attempt_ref",
            "preassigned_candidate_ref",
            "transaction_timestamp",
        ),
        "dispositions": ("committed", "exact_replay"),
    },
    "private_outcome_ownership": {
        "future_module": "src/ge_nwp_coordinator/_development_program_initialization_contracts.py",
        "module_present_this_turn": False,
        "package_root_export": False,
        "conflict_reason": {
            "semantic_name": "DevelopmentProgramInitializationConflictReasonV1",
            "values": (
                "mutation_ref_reuse_conflict",
                "global_stop_version_conflict",
                "coding_global_stop_active",
                "semantic_identity_conflict",
            ),
        },
        "conflict_result": {
            "semantic_name": "DevelopmentProgramInitializationConflictV1",
            "ordered_fields": ("reason", "mutation_ref", "command_digest", "program_ref"),
            "reason_type": "exact DevelopmentProgramInitializationConflictReasonV1",
            "posture": (
                "not persisted",
                "not canonical durable identity",
                "not a SQLite safe error",
                "not a public apply-conflict value",
                "not package-exported",
                "not authority",
            ),
        },
        "recovery_disposition": {
            "semantic_name": "DevelopmentProgramInitializationRecoveryDispositionV1",
            "values": ("committed_exact", "definitely_not_committed", "unresolved"),
        },
        "existing_sqlite_store_error_reasons": (
            "database_integrity_failure",
            "mutation_failed",
            "commit_outcome_unknown",
        ),
        "public_surfaces_unchanged": (
            "models.APPLY_CONFLICT_REASONS",
            "sqlite_errors",
            "package root",
            "StateStore",
            "public WriterSession protocol",
        ),
    },
    "mutation_receipt": {
        "family": "initialize_development_program",
        "command_schema_id": "governed-execution.nwp-initialize-development-program-command.v1",
        "result_class": "development_program_initialized",
        "result_attempt_ref": None,
        "result_effect_ref": None,
        "result_fence_ref": None,
        "result_delivery_ref": None,
        "result_observation_ref": None,
        "outcome": "committed",
        "self_digest": None,
        "graph_entry_count": 8,
        "failed_fresh_receipt": False,
    },
    "exact_replay": {
        "after_writer_fencing": True,
        "ordered_steps": (
            "read receipt by mutation_ref",
            "absent receipt selects fresh path",
            "present receipt with different command digest is mutation_ref_reuse_conflict",
            "validate receipt family, schema, and scalar algebra",
            "locate all eight graph entries",
            "validate every row self-digest",
            "validate all program/version/decision/intent/work/membership/WorkSpec relations",
            "reconstruct historical program and work head postimages",
            "recompute accepted-intent projection, persisted result projection, and graph digest",
            "return original private result with disposition exact_replay",
        ),
        "incomplete_or_malformed_graph": "database_integrity_failure",
        "contradictory_same_revision_head": "database_integrity_failure",
        "later_valid_head_advancement": "allowed; historical replay remains exact",
        "later_C2B6_lineage_proven": False,
    },
    "commit_uncertainty_cleanup_gate": {
        "commit_attempt_exception": "controller records commit_outcome_unknown",
        "raw_connection_owner_before_close": "transaction controller retains exclusive custody",
        "close_attempt_precedes": (
            "clearing controller connection custody",
            "making the mutation slot available",
            "returning commit_outcome_unknown to the caller",
        ),
        "close_complete": {
            "controller_connection_custody": "cleared",
            "mutation_slot_available": True,
            "session_quarantined": False,
            "outward_store_error": "commit_outcome_unknown",
            "original_apply_error": {
                "type": "SQLiteMutationStoreError",
                "reason": "commit_outcome_unknown",
                "internal_detail": None,
                "cause": None,
                "context": None,
                "notes": None,
                "raised_from": None,
            },
            "slot_release_gate": "only after close proof",
            "fresh_resolver": "permitted later under a new operation lease and reacquired same shared slot",
        },
        "close_not_proved": {
            "ordered_steps": (
                "commit attempt raises",
                "controller retains connection custody and mutation slot",
                "close is attempted",
                "close not proved",
                "connection custody transfers to private _WriterSessionResource",
                "session quarantine is recorded",
                "writer-authority lock remains retained",
                "mutation slot remains unavailable",
                "fresh content-free commit_outcome_unknown is raised from None",
            ),
            "raw_connection_custody": "transferred to and retained by private _WriterSessionResource",
            "session_state": "commit-uncertain quarantined",
            "writer_authority_lock": "retained by that concrete session",
            "mutation_slot_available": False,
            "original_apply_error": {
                "type": "SQLiteMutationStoreError",
                "reason": "commit_outcome_unknown",
                "internal_detail": None,
                "cause": None,
                "context": None,
                "notes": None,
                "raised_from": None,
            },
            "close_failure_role": "secondary",
            "close_failure_replaces_primary_error": False,
            "close_failure_decorates_primary_error": False,
            "close_failure_leaks_outward": False,
            "close_exception_in_outward_error_graph": False,
            "same_session_mutation": False,
            "same_session_database_backed_resolver": False,
            "same_session_resolver_disposition": "unresolved before operation-lease acquisition, database open, BEGIN, or SQL",
            "permitted_work": "explicit close/finalization of the retained connection only",
            "new_session_resolver_before_proved_close": False,
            "definitely_not_committed": False,
            "automatic_semantic_retry": False,
            "process_control_close_interruption_ordered_steps": (
                "observe the exact process-control exception object from connection close",
                "retain the mutation slot",
                "retain the writer-authority lock",
                "transfer the uncertain raw connection into the private _WriterSessionResource",
                "publish the concrete session as commit-uncertain quarantined",
                "confirm same-session mutation and database-backed recovery remain forbidden",
                "confirm no operation lease, database open, BEGIN, or SQL can occur",
                "re-raise the identical process-control exception object",
            ),
            "process_control_exceptions": {
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
            },
            "process_control_exception_graph_ledger": (
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
            ),
        },
        "quarantine_clearance": (
            "proven retained-connection closure",
            "proven writer-authority-lock release",
            "newly acquired concrete writer session",
            "exact safe command",
        ),
        "caller_authored_clearance": False,
        "forbidden_clearance_evidence": (
            "cleanup token",
            "Boolean assertion",
            "path marker",
            "report",
            "timeout",
        ),
        "forbidden_outward_material": (
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
        ),
        "forbidden_outward_destinations": (
            "safe command",
            "receipt",
            "apply result",
            "resolver result",
            "public value",
            "exception payload",
            "log",
            "report",
            "future C2B3-owned outward traceback locals",
        ),
        "process_control_exception_graph_privacy": {
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
        },
    },
    "commit_outcome_recovery": {
        "semantic_name": "DevelopmentProgramInitializationRecoveryResultV1",
        "disposition_owner": "DevelopmentProgramInitializationRecoveryDispositionV1",
        "dispositions": (
            "committed_exact",
            "definitely_not_committed",
            "unresolved",
        ),
        "inputs": (
            "currently valid concrete _SQLiteWriterSession",
            "exact safe initialization command",
        ),
        "accepts_work_spec": False,
        "lifecycle": (
            "prior uncertain connection closure and prior writer-lock release are proven",
            "newly acquired concrete writer session",
            "new operation guard and fresh operation lease",
            "reacquire existing shared mutation slot",
            "same transaction-controller class",
            "fresh readback-only BEGIN IMMEDIATE",
            "managed schema and resource revalidation",
            "writer fencing",
            "same nominal read capability",
            "readback only",
            "rollback and close",
        ),
        "same_session_resolver_while_quarantined": False,
        "mutation_slot_available_before_close_completion": False,
        "close_not_proved_disposition": "unresolved",
        "committed_exact_requires": (
            "exact receipt",
            "exact command digest",
            "exact persisted result",
            "all eight graph entries",
            "all row self-digests",
            "all cross-row relations",
            "both historical head postimages",
            "exact result-projection digest",
            "exact mutation-graph digest",
        ),
        "definitely_not_committed_requires_all_absent": (
            "receipt for mutation_ref",
            "program head for program_ref",
            "program version for program_version_ref",
            "accepted-intent revision for accepted_intent_revision_ref",
            "decision for decision_ref",
            "work-item head for work_item_ref",
            "work-item revision for work_item_revision_ref",
            "membership for command identities",
            "WorkSpec binding for work_spec_ref",
        ),
        "unresolved_evidence": (
            "receipt-only",
            "graph-without-receipt",
            "partial graph",
            "mixed evidence",
            "malformed evidence",
            "contradictory postimage",
            "unlocatable evidence",
            "any state other than exact committed or exact all-absent",
        ),
        "basis_or_global_stop_presence_proves_family_commit": False,
        "automatic_semantic_retry": False,
        "fresh_retry_after_definitely_not_committed": "caller must supply the exact complete WorkSpecV1 again",
    },
    "conflict_precedence": {
        "after_writer_fencing": (
            (1, "exact receipt replay"),
            (2, "mutation_ref_reuse_conflict"),
            (3, "global_stop_version_conflict"),
            (4, "coding_global_stop_active"),
            (5, "semantic_identity_conflict"),
            (6, "database_integrity_failure"),
            (7, "mutation_failed"),
            (8, "commit_outcome_unknown"),
        ),
        "classification_conditions": (
            ("exact receipt replay", "same mutation_ref and same command digest with an exact complete persisted family"),
            ("mutation_ref_reuse_conflict", "same mutation_ref and different command digest"),
            ("global_stop_version_conflict", "coding-global-stop ref or version mismatch"),
            ("coding_global_stop_active", "active exact coding global stop"),
            ("semantic_identity_conflict", "pre-existing program or colliding genesis semantic identity"),
            ("database_integrity_failure", "malformed or contradictory persisted state"),
            ("mutation_failed", "operational SQLite or capability failure"),
            ("commit_outcome_unknown", "commit-attempt exception"),
        ),
        "semantic_identity_conflict_visibility": "private",
        "program_head_conflict": "reserved for later non-genesis CAS-bearing families",
        "failed_fresh_operation_creates_receipt": False,
    },
    "privacy_and_traceback": {
        "ordered_failure_boundary": (
            "sensitive WorkSpec reducer",
            "safe closed outcome",
            "raw reducer returns normally",
            "outer wrapper clears WorkSpec and caught-exception references",
            "fresh bounded outward failure from None",
        ),
        "complete_work_spec_forbidden_destinations": (
            "SQLite",
            "safe command",
            "receipt",
            "result",
            "resolver input",
            "exception payload",
            "log",
            "report",
            "traceback locals owned by future C2B3 source",
        ),
        "forbidden_custody_sources": (
            "chat",
            "model memory",
            "Bridge",
            "reports",
            "connectors",
            "logs",
            "transcripts",
        ),
        "transaction_controller_receives_work_spec": False,
        "contract_freeze_persists_or_executes_work_spec": False,
    },
    "later_author_effect_owner_decisions": {
        "complete_contract_frozen": False,
        "source_implemented": False,
        "initial_basis": ("initialize", "program_genesis"),
        "attempt_number": 1,
        "planned_adapter_kind": "execution_substrate",
        "route_effect": "absent",
        "planned_adapter_value_authority": "safe planned-row value only; no ES compatibility, dispatch permission, route eligibility, reliable submit, or current API binding",
        "adapter_safe_correlation_ref": "preassigned, safe, non-authoritative",
        "work_spec_ingress": "same-call transient only",
        "authority_evaluation": {
            "authorship": "Coordinator-authored pending evidence",
            "evaluation_scope": "effect",
            "evaluation_subject_ref": "exact effect_intent_ref",
            "semantic_attempt_ref": None,
            "effect_intent_ref": "exact effect_intent_ref",
            "authority_ref": "exact externally authored effect_authorization_ref",
            "authority_digest": "exact externally authored effect_authorization_digest",
            "authority_state": "pending",
            "reason_code": "external_verification_pending",
            "expires_at": None,
            "evaluated_at": "one transaction timestamp",
            "authority_evaluation_ref": "preassigned and command-bound",
            "dispatch_eligibility": False,
        },
        "coordinator_does_not_author": (
            "verified",
            "blocked",
            "stale",
            "revoked",
            "expired",
            "executable permission",
            "ES admission",
            "worker authorization",
        ),
        "requirement_provenance": {
            "refs": "exact validation_requirement_ref and review_requirement_ref from WorkSpec",
            "digests": "exact typed safe requirement evidence supplied in the same future private call",
            "raw_digest_only_input": False,
            "digest_inference_from_refs": False,
            "digest_inference_from_text_reports_or_runtime": False,
        },
        "recovery": "explicit fresh-lease readback",
        "graph_membership": "family-created rows only",
        "C2B3C_must_freeze_before_source": (
            "exact typed requirement evidence",
            "exact author command",
            "AttemptFence ingress",
            "all author refs",
            "effect and delivery postimages",
            "nine graph entries",
            "golden vector",
            "replay matrix",
            "recovery matrix",
            "privacy matrix",
        ),
        "direct_local_bootstrap_selected": False,
        "direct_local_posture": "separate later proof/contract; never a silently selected runtime alternative",
        "ES_invocation_or_compatibility_claim": False,
    },
    "future_c2b3b_maximum_path_scope": {
        "tranche": "C2B3B_PRIVATE_ATOMIC_INITIALIZATION",
        "maximum_paths": 24,
        "production": (
            "src/ge_nwp_coordinator/_development_program_initialization_contracts.py",
            "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py",
            "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
            "src/ge_nwp_coordinator/sqlite_writer_session.py",
            "src/ge_nwp_coordinator/sqlite_connection.py",
        ),
        "documentation_status": (
            ".docs/c2b-durable-development-state.md",
            ".docs/c2b3-program-initialization.md",
            ".docs/c2b2-private-readers.md",
            ".docs/architecture.md",
            ".docs/durable-state-model.md",
            ".docs/sqlite-operations-and-recovery.md",
            ".docs/sqlite-threat-model.md",
            "README.md",
            "AGENTS.md",
        ),
        "tests": (
            "tests/test_c2b3_program_initialization_contract.py",
            "tests/test_c2b3_private_atomic_program_initialization.py",
            "tests/test_c2b3_program_initialization_recovery.py",
            "tests/test_c2b3_private_program_initialization_delegation.py",
            "tests/test_c2b2_field_level_contract.py",
            "tests/test_c2b2_private_development_readers.py",
            "tests/test_c2b2_development_reader_contracts.py",
            "tests/test_runtime_non_authority.py",
            "tests/test_architecture_contracts.py",
            "tests/test_c2b0_durable_state_contract.py",
        ),
        "counts": {
            "production": 5,
            "documentation_status": 9,
            "tests": 10,
            "total": 24,
        },
        "production_responsibilities": {
            "src/ge_nwp_coordinator/_development_program_initialization_contracts.py": (
                "private pure command, projection, result, conflict, recovery, graph, and quarantine-admission values",
                "no process-control result or enum",
                "no ordinary-value representation of KeyboardInterrupt, SystemExit, or GeneratorExit",
                "no SQLite",
                "no I/O",
                "no package export",
            ),
            "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py": (
                "sensitive same-call reducer",
                "safe initialization command construction",
                "exact replay",
                "fresh apply",
                "family-specific graph location and verification",
                "explicit recovery resolver",
                "does not catch, translate, wrap, or retry KeyboardInterrupt, SystemExit, or GeneratorExit after transaction cleanup returns them for propagation",
                "no public API",
                "no external I/O",
            ),
            "src/ge_nwp_coordinator/sqlite_transition_transaction.py": (
                "preserve one-commit-attempt ownership",
                "retain uncertain connection and mutation slot after commit exception",
                "attempt close before custody clear",
                "transfer retained connection into session resource when close is unproved",
                "reduce and detach the ordinary commit failure before close-time process-control handling",
                "own the narrow close-interruption catch point",
                "recognize exactly KeyboardInterrupt, SystemExit, and GeneratorExit",
                "catch exactly KeyboardInterrupt, SystemExit, and GeneratorExit from close",
                "retain connection and mutation-slot custody for a named process-control close interruption",
                "retain connection, slot, and writer-lock custody",
                "request session-resource quarantine publication and wait for publication completion",
                "re-raise the identical process-control exception only after publication completion",
                "perform a bare re-raise in the same catch suite",
                "add no traceback frame beyond bare-reraise semantics",
                "add no cause, context, note, or exception-graph material",
                "do not execute unconditional slot release in a named process-control branch",
                "never unconditionally release the slot after commit uncertainty",
                "preserve fresh content-free commit_outcome_unknown",
                "admit no semantic retry",
            ),
            "src/ge_nwp_coordinator/sqlite_writer_session.py": (
                "private program-initialization delegation only",
                "_WriterSessionResource retained-connection custody",
                "commit-uncertain quarantine state",
                "writer-lock and mutation-slot retention",
                "reject new operations while quarantined",
                "acknowledge quarantine publication before the transaction layer re-raises a named process-control exception",
                "publication acknowledgement must not raise or attach an ordinary exception to the process-control exception",
                "publication helpers receive no authority to propagate or replace the caught process-control exception",
                "admit close/finalization only while quarantined",
                "release quarantine only after proved closure and session disposal",
                "no public WriterSession protocol change",
            ),
            "src/ge_nwp_coordinator/sqlite_connection.py": (
                "one private C2B3B-only connection posture or equivalent explicit mechanism permitting proved closure from session-resource finalization",
                "cross-thread close from session-resource finalization is permitted only for proved closure",
                "may surface the exact close-time KeyboardInterrupt, SystemExit, or GeneratorExit",
                "no cross-thread SQL",
                "no public raw connection",
                "no public signature widening",
                "no second connection authority",
                "existing ordinary connection behavior preserved",
            ),
        },
        "twenty_fifth_path": "future implementation stop condition",
        "forbidden": (
            "pyproject.toml",
            "package __init__.py",
            "state_store.py",
            "sqlite_errors.py",
            "models.py public values",
            "sqlite_mutation_transaction_contracts.py",
            "migration SQL or catalog",
            "schemas",
            "C2B4-C2B6 implementation",
            "another repository",
        ),
        "authorized_by_this_freeze": False,
    },
    "nonimplementation": {
        "program_initialization_source": False,
        "private_writer_session_methods": False,
        "sqlite_insert_or_update_execution": False,
        "mutation_receipt_persistence": False,
        "production_reader_integration": False,
        "exact_replay_runtime": False,
        "commit_outcome_recovery_runtime": False,
        "author_effect_source": False,
        "complete_author_effect_contract": False,
        "public_C2B_API": False,
        "StateStore_widening": False,
        "WriterSession_public_surface_widening": False,
        "package_root_export": False,
        "dependency_or_entry_surface": False,
        "WorkSpec_custody_or_retrieval": False,
        "authority_verification": False,
        "worker_or_model_execution": False,
        "direct_local_execution": False,
        "Execution_Substrate_invocation": False,
        "Bridge_integration": False,
        "schema_change": False,
        "migration_0001_change": False,
        "migration_0002_change": False,
        "migration_0003_creation": False,
        "C2B4_C2B5_C2B6_behavior": False,
        "external_IO": False,
    },
}


EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM = {
    "identity": {
        "workstream": "COORDINATOR_C2B3A_COMMIT_CLOSE_OUTCOME_ADDENDUM",
        "classification": "accepted target-contract addendum",
        "semantic_owner": ".docs/c2b-durable-development-state.md#35-c2b3a-program-initialization-contract-freeze",
        "owner_entry": "commit_close_outcome_addendum",
        "production_implementation_status": "absent",
        "four_path_scope": (
            ".docs/c2b-durable-development-state.md",
            ".docs/c2b3-program-initialization.md",
            "tests/test_c2b3_program_initialization_contract.py",
            "tests/test_c2b0_durable_state_contract.py",
        ),
        "tracked_modifications": 4,
        "tracked_additions": 0,
        "untracked_additions": 0,
        "preserves_original_five_path_scope": True,
    },
    "normative_surface_and_precedence": {
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
    },
    "commit_axis": (
        ("C1", "COMMIT returns normally"),
        ("C2", "COMMIT raises an ordinary SQLite exception"),
        ("C3", "COMMIT raises another ordinary Exception"),
        ("C4", "COMMIT raises KeyboardInterrupt"),
        ("C5", "COMMIT raises SystemExit"),
        ("C6", "COMMIT raises GeneratorExit"),
    ),
    "close_axis": (
        ("K1", "close returns normally and closure is proved"),
        ("K2", "close raises an ordinary SQLite exception"),
        ("K3", "close raises another ordinary Exception"),
        ("K4", "close raises KeyboardInterrupt"),
        ("K5", "close raises SystemExit"),
        ("K6", "close raises GeneratorExit"),
    ),
    "process_control_inventory": (
        "KeyboardInterrupt",
        "SystemExit",
        "GeneratorExit",
    ),
    "matrix_identity_overlay": {
        "matrix_axes": "exception types only; object identity is orthogonal",
        "different_exact_classes": "necessarily distinct objects",
        "diagonal_rows": ("C4K4", "C5K5", "C6K6"),
        "diagonal_discriminator": "same_instance iff commit_exception is cleanup_exception; otherwise distinct_instance",
        "same_exact_class_implies_same_object": False,
        "additional_cartesian_axis": False,
        "dynamic_generation": False,
    },
    "session_state_legend": {
        "A": "normal active session",
        "QU": "commit uncertain; retained transaction-connection closure unproved",
        "QK": "commit known committed; retained transaction-connection closure unproved",
        "PU": "commit uncertain; connection closure proved and raw connection custody cleared; residual cleanup pending",
        "PK": "commit known committed; connection closure proved and raw connection custody cleared; residual cleanup pending",
        "X": "authority-terminal after applicable connection-close proof, credential revocation, slot and binding release, writer-lock release proof, authority-lock terminalization, and exact authority-lock registry removal",
    },
    "orthogonal_cleanup_facets": {
        "writer_lock_release": (
            "not_attempted",
            "release_unproved",
            "release_proved",
        ),
        "descriptor_outcome": (
            "not_attempted",
            "reclaimed",
            "reclamation_unknown",
        ),
        "finalizer_liveness": (
            "finalizer_attempted",
            "retry_reachable",
        ),
        "wrapper_loss_after_failed_one_shot_finalizer": {
            "finalizer_attempted": True,
            "retry_reachable": False,
        },
        "X_requires_descriptor_reclaimed": False,
        "X_requires_post_X_session_registry_removal": False,
        "CLEANING": "transient single-owner execution condition; never stable custody state",
    },
    "row_field_order": (
        "row_id",
        "commit_axis_id",
        "close_axis_id",
        "known_commit_state",
        "outward_result_or_exception",
        "outward_identity_requirements",
        "raise_form",
        "repair_owned_propagation_frame_delta",
        "cause_context_suppression_notes",
        "raw_connection_disposition",
        "raw_connection_owner",
        "controller_state",
        "session_state",
        "mutation_slot_disposition",
        "operation_lease_completion",
        "writer_lock_disposition",
        "quarantine_publication",
        "new_operation_admission",
        "committed_result_delivered",
        "permitted_recovery_or_replay",
        "automatic_semantic_retry",
        "rollback_after_commit_start",
        "secondary_failure_posture",
        "C2B3_private_material_added_or_copied_outward",
    ),
    "outcome_matrix": (
        (
            "C1K1", "C1", "K1", "committed",
            "return planned committed result",
            "identical planned committed result",
            "return", "not_applicable",
            "not_applicable; no outward exception",
            "closure proved; custody cleared", "none",
            "not quarantined; controller no longer owns connection", "A",
            "released; shared mutation slot available",
            "completed and removed normally",
            "retained by active session", "not_applicable",
            "admitted under normal active-session rules", True,
            "none needed", False, False, "none", False,
        ),
        (
            "C1K2", "C1", "K2", "committed",
            "return planned committed result",
            "identical planned committed result",
            "return", "not_applicable",
            "not_applicable; no outward exception",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_SUCCEEDED_QUARANTINED", "QK",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QK and custody published before result return",
            "post_close_cleanup_contract disposal only", True,
            "no commit-outcome resolver; post_close_cleanup_contract disposal only; no replay needed",
            False, False,
            "ordinary SQLite close failure suppressed and not deliberately copied into an outward value, log, or report",
            False,
        ),
        (
            "C1K3", "C1", "K3", "committed",
            "return planned committed result",
            "identical planned committed result",
            "return", "not_applicable",
            "not_applicable; no outward exception",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_SUCCEEDED_QUARANTINED", "QK",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QK and custody published before result return",
            "post_close_cleanup_contract disposal only", True,
            "no commit-outcome resolver; post_close_cleanup_contract disposal only; no replay needed",
            False, False,
            "other ordinary close failure suppressed and not deliberately copied into an outward value, log, or report",
            False,
        ),
        (
            "C1K4", "C1", "K4", "committed",
            "propagate close-time KeyboardInterrupt",
            "identical close exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same close catch suite", 0,
            "C2B3 deliberately adds, clears, restores, scrubs, or copies no cause, context, suppression, traceback, note, relation, or private material; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_SUCCEEDED_QUARANTINED", "QK",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QK and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, normal initialization apply in a new session gives receipt-first exact replay of the identical safe command",
            False, False,
            "close-time process control is sole outward exception; committed result not delivered",
            False,
        ),
        (
            "C1K5", "C1", "K5", "committed",
            "propagate close-time SystemExit",
            "identical close exception object, exact type and args, and exact SystemExit.code",
            "bare raise in the same close catch suite", 0,
            "C2B3 deliberately adds, clears, restores, scrubs, or copies no cause, context, suppression, traceback, note, relation, or private material; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_SUCCEEDED_QUARANTINED", "QK",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QK and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, normal initialization apply in a new session gives receipt-first exact replay of the identical safe command",
            False, False,
            "close-time process control is sole outward exception; committed result not delivered",
            False,
        ),
        (
            "C1K6", "C1", "K6", "committed",
            "propagate close-time GeneratorExit",
            "identical close exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same close catch suite", 0,
            "C2B3 deliberately adds, clears, restores, scrubs, or copies no cause, context, suppression, traceback, note, relation, or private material; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_SUCCEEDED_QUARANTINED", "QK",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QK and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, normal initialization apply in a new session gives receipt-first exact replay of the identical safe command",
            False, False,
            "close-time process control is sole outward exception; committed result not delivered",
            False,
        ),
        (
            "C2K1", "C2", "K1", "unknown",
            "raise SQLiteMutationStoreError(commit_outcome_unknown)",
            "fresh content-free error distinct from commit and close exceptions",
            "explicit raise from None", "not_applicable",
            "cause=None; context=None; suppress_context=True; notes=absent",
            "closure proved; custody cleared", "none",
            "commit uncertainty recorded; controller no longer owns connection", "A",
            "released; shared mutation slot available",
            "completed and removed normally",
            "retained by active session", "not_applicable",
            "ordinary active-session rules; C2K1/C3K1 remain A and recovery requires later ordinary A -> X disposal first", False,
            "after ordinary A -> X reaches T1 through the shared proof-aware lock-release primitive, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "ordinary SQLite commit exception not retained or copied into the content-free outward safe error",
            False,
        ),
        (
            "C2K2", "C2", "K2", "unknown",
            "raise SQLiteMutationStoreError(commit_outcome_unknown)",
            "fresh content-free error distinct from commit and close exceptions",
            "explicit raise from None", "not_applicable",
            "cause=None; context=None; suppress_context=True; notes=absent",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before outward error",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "ordinary commit and SQLite close exceptions not retained or copied into the content-free outward safe error",
            False,
        ),
        (
            "C2K3", "C2", "K3", "unknown",
            "raise SQLiteMutationStoreError(commit_outcome_unknown)",
            "fresh content-free error distinct from commit and close exceptions",
            "explicit raise from None", "not_applicable",
            "cause=None; context=None; suppress_context=True; notes=absent",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before outward error",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "ordinary commit and other ordinary close exceptions not retained or copied into the content-free outward safe error",
            False,
        ),
        (
            "C2K4", "C2", "K4", "unknown",
            "propagate close-time KeyboardInterrupt",
            "identical close exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same close catch suite", 0,
            "C2B3 copies no ordinary COMMIT failure and deliberately adds, clears, restores, or scrubs no cause, context, suppression, traceback, note, relation, or private material; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "ordinary commit exception detached; close-time process control is sole outward exception",
            False,
        ),
        (
            "C2K5", "C2", "K5", "unknown",
            "propagate close-time SystemExit",
            "identical close exception object, exact type and args, and exact SystemExit.code",
            "bare raise in the same close catch suite", 0,
            "C2B3 copies no ordinary COMMIT failure and deliberately adds, clears, restores, or scrubs no cause, context, suppression, traceback, note, relation, or private material; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "ordinary commit exception detached; close-time process control is sole outward exception",
            False,
        ),
        (
            "C2K6", "C2", "K6", "unknown",
            "propagate close-time GeneratorExit",
            "identical close exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same close catch suite", 0,
            "C2B3 copies no ordinary COMMIT failure and deliberately adds, clears, restores, or scrubs no cause, context, suppression, traceback, note, relation, or private material; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "ordinary commit exception detached; close-time process control is sole outward exception",
            False,
        ),
        (
            "C3K1", "C3", "K1", "unknown",
            "raise SQLiteMutationStoreError(commit_outcome_unknown)",
            "fresh content-free error distinct from commit and close exceptions",
            "explicit raise from None", "not_applicable",
            "cause=None; context=None; suppress_context=True; notes=absent",
            "closure proved; custody cleared", "none",
            "commit uncertainty recorded; controller no longer owns connection", "A",
            "released; shared mutation slot available",
            "completed and removed normally",
            "retained by active session", "not_applicable",
            "ordinary active-session rules; C2K1/C3K1 remain A and recovery requires later ordinary A -> X disposal first", False,
            "after ordinary A -> X reaches T1 through the shared proof-aware lock-release primitive, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "other ordinary commit exception not retained or copied into the content-free outward safe error",
            False,
        ),
        (
            "C3K2", "C3", "K2", "unknown",
            "raise SQLiteMutationStoreError(commit_outcome_unknown)",
            "fresh content-free error distinct from commit and close exceptions",
            "explicit raise from None", "not_applicable",
            "cause=None; context=None; suppress_context=True; notes=absent",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before outward error",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "ordinary commit and SQLite close exceptions not retained or copied into the content-free outward safe error",
            False,
        ),
        (
            "C3K3", "C3", "K3", "unknown",
            "raise SQLiteMutationStoreError(commit_outcome_unknown)",
            "fresh content-free error distinct from commit and close exceptions",
            "explicit raise from None", "not_applicable",
            "cause=None; context=None; suppress_context=True; notes=absent",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before outward error",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "ordinary commit and other ordinary close exceptions not retained or copied into the content-free outward safe error",
            False,
        ),
        (
            "C3K4", "C3", "K4", "unknown",
            "propagate close-time KeyboardInterrupt",
            "identical close exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same close catch suite", 0,
            "C2B3 copies no ordinary COMMIT failure and deliberately adds, clears, restores, or scrubs no cause, context, suppression, traceback, note, relation, or private material; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "other ordinary commit exception detached; close-time process control is sole outward exception",
            False,
        ),
        (
            "C3K5", "C3", "K5", "unknown",
            "propagate close-time SystemExit",
            "identical close exception object, exact type and args, and exact SystemExit.code",
            "bare raise in the same close catch suite", 0,
            "C2B3 copies no ordinary COMMIT failure and deliberately adds, clears, restores, or scrubs no cause, context, suppression, traceback, note, relation, or private material; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "other ordinary commit exception detached; close-time process control is sole outward exception",
            False,
        ),
        (
            "C3K6", "C3", "K6", "unknown",
            "propagate close-time GeneratorExit",
            "identical close exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same close catch suite", 0,
            "C2B3 copies no ordinary COMMIT failure and deliberately adds, clears, restores, or scrubs no cause, context, suppression, traceback, note, relation, or private material; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "other ordinary commit exception detached; close-time process control is sole outward exception",
            False,
        ),
        (
            "C4K1", "C4", "K1", "unknown",
            "propagate original COMMIT-time KeyboardInterrupt",
            "identical original commit exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same COMMIT catch suite after post_close_cleanup_contract continuation", 0,
            "apply process_control_relational_policy; add no C2B3-owned graph edge, note, or private material",
            "closure proved; custody cleared; connection never closed again", "none",
            "_CONTROLLER_COMMIT_UNCERTAIN_CONNECTION_CLOSED_CLEANUP_PENDING", "PU",
            "retained pending monotonic cleanup; released only at X",
            "completed identity removed after PU publication without clearing the pending slot",
            "retained until post_close_cleanup_contract reaches X",
            "PU published before residual cleanup; X only after every required release completes",
            "residual cleanup only while PU; recovery blocked until X", False,
            "after T1 publishes X, explicit commit-outcome resolver in a newly acquired session with a fresh lease and identical safe command",
            False, False,
            "close returned normally; residual cleanup may reach X or remain PU with progress; original COMMIT-time process control is sole outward exception",
            False,
        ),
        (
            "C4K2", "C4", "K2", "unknown",
            "propagate original COMMIT-time KeyboardInterrupt",
            "identical original commit exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same COMMIT catch suite", 0,
            "apply process_control_relational_policy; C2B3 deliberately adds no primary-to-secondary relation; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "ordinary SQLite close failure suppressed; no deliberate primary-to-secondary relation, scrub, or restoration; exact interpreter graph shape is not promised",
            False,
        ),
        (
            "C4K3", "C4", "K3", "unknown",
            "propagate original COMMIT-time KeyboardInterrupt",
            "identical original commit exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same COMMIT catch suite", 0,
            "apply process_control_relational_policy; C2B3 deliberately adds no primary-to-secondary relation; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "other ordinary close failure suppressed; no deliberate primary-to-secondary relation, scrub, or restoration; exact interpreter graph shape is not promised",
            False,
        ),
        (
            "C4K4", "C4", "K4", "unknown",
            "propagate original COMMIT-time KeyboardInterrupt",
            "identical original commit exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same COMMIT catch suite", 0,
            "dispatch by object identity: same_instance iff commit_exception is cleanup_exception; otherwise distinct_instance; no exact graph or traceback shape is promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "object-identity discriminator selects same_instance or distinct_instance; original COMMIT-time KeyboardInterrupt remains primary and C2B3 deliberately adds no graph relation or material",
            False,
        ),
        (
            "C4K5", "C4", "K5", "unknown",
            "propagate original COMMIT-time KeyboardInterrupt",
            "identical original commit exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same COMMIT catch suite", 0,
            "apply process_control_relational_policy; C2B3 deliberately adds no primary-to-secondary relation; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "close-time SystemExit secondary relation classified by process_control_relational_policy; no deliberate C2B3-owned graph relation or material; exact interpreter graph shape is not promised",
            False,
        ),
        (
            "C4K6", "C4", "K6", "unknown",
            "propagate original COMMIT-time KeyboardInterrupt",
            "identical original commit exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same COMMIT catch suite", 0,
            "apply process_control_relational_policy; C2B3 deliberately adds no primary-to-secondary relation; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "close-time GeneratorExit secondary relation classified by process_control_relational_policy; no deliberate C2B3-owned graph relation or material; exact interpreter graph shape is not promised",
            False,
        ),
        (
            "C5K1", "C5", "K1", "unknown",
            "propagate original COMMIT-time SystemExit",
            "identical original commit exception object, exact type and args, and exact SystemExit.code",
            "bare raise in the same COMMIT catch suite after post_close_cleanup_contract continuation", 0,
            "apply process_control_relational_policy; add no C2B3-owned graph edge, note, or private material",
            "closure proved; custody cleared; connection never closed again", "none",
            "_CONTROLLER_COMMIT_UNCERTAIN_CONNECTION_CLOSED_CLEANUP_PENDING", "PU",
            "retained pending monotonic cleanup; released only at X",
            "completed identity removed after PU publication without clearing the pending slot",
            "retained until post_close_cleanup_contract reaches X",
            "PU published before residual cleanup; X only after every required release completes",
            "residual cleanup only while PU; recovery blocked until X", False,
            "after T1 publishes X, explicit commit-outcome resolver in a newly acquired session with a fresh lease and identical safe command",
            False, False,
            "close returned normally; residual cleanup may reach X or remain PU with progress; original COMMIT-time process control is sole outward exception",
            False,
        ),
        (
            "C5K2", "C5", "K2", "unknown",
            "propagate original COMMIT-time SystemExit",
            "identical original commit exception object, exact type and args, and exact SystemExit.code",
            "bare raise in the same COMMIT catch suite", 0,
            "apply process_control_relational_policy; C2B3 deliberately adds no primary-to-secondary relation; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "ordinary SQLite close failure suppressed; no deliberate primary-to-secondary relation, scrub, or restoration; exact interpreter graph shape is not promised",
            False,
        ),
        (
            "C5K3", "C5", "K3", "unknown",
            "propagate original COMMIT-time SystemExit",
            "identical original commit exception object, exact type and args, and exact SystemExit.code",
            "bare raise in the same COMMIT catch suite", 0,
            "apply process_control_relational_policy; C2B3 deliberately adds no primary-to-secondary relation; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "other ordinary close failure suppressed; no deliberate primary-to-secondary relation, scrub, or restoration; exact interpreter graph shape is not promised",
            False,
        ),
        (
            "C5K4", "C5", "K4", "unknown",
            "propagate original COMMIT-time SystemExit",
            "identical original commit exception object, exact type and args, and exact SystemExit.code",
            "bare raise in the same COMMIT catch suite", 0,
            "apply process_control_relational_policy; C2B3 deliberately adds no primary-to-secondary relation; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "close-time KeyboardInterrupt secondary relation classified by process_control_relational_policy; no deliberate C2B3-owned graph relation or material; exact interpreter graph shape is not promised",
            False,
        ),
        (
            "C5K5", "C5", "K5", "unknown",
            "propagate original COMMIT-time SystemExit",
            "identical original commit exception object, exact type and args, and exact SystemExit.code",
            "bare raise in the same COMMIT catch suite", 0,
            "dispatch by object identity: same_instance iff commit_exception is cleanup_exception; otherwise distinct_instance; no exact graph or traceback shape is promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "object-identity discriminator selects same_instance or distinct_instance; original COMMIT-time SystemExit remains primary and C2B3 deliberately adds no graph relation or material",
            False,
        ),
        (
            "C5K6", "C5", "K6", "unknown",
            "propagate original COMMIT-time SystemExit",
            "identical original commit exception object, exact type and args, and exact SystemExit.code",
            "bare raise in the same COMMIT catch suite", 0,
            "apply process_control_relational_policy; C2B3 deliberately adds no primary-to-secondary relation; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "close-time GeneratorExit secondary relation classified by process_control_relational_policy; no deliberate C2B3-owned graph relation or material; exact interpreter graph shape is not promised",
            False,
        ),
        (
            "C6K1", "C6", "K1", "unknown",
            "propagate original COMMIT-time GeneratorExit",
            "identical original commit exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same COMMIT catch suite after post_close_cleanup_contract continuation", 0,
            "apply process_control_relational_policy; add no C2B3-owned graph edge, note, or private material",
            "closure proved; custody cleared; connection never closed again", "none",
            "_CONTROLLER_COMMIT_UNCERTAIN_CONNECTION_CLOSED_CLEANUP_PENDING", "PU",
            "retained pending monotonic cleanup; released only at X",
            "completed identity removed after PU publication without clearing the pending slot",
            "retained until post_close_cleanup_contract reaches X",
            "PU published before residual cleanup; X only after every required release completes",
            "residual cleanup only while PU; recovery blocked until X", False,
            "after T1 publishes X, explicit commit-outcome resolver in a newly acquired session with a fresh lease and identical safe command",
            False, False,
            "close returned normally; residual cleanup may reach X or remain PU with progress; original COMMIT-time process control is sole outward exception",
            False,
        ),
        (
            "C6K2", "C6", "K2", "unknown",
            "propagate original COMMIT-time GeneratorExit",
            "identical original commit exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same COMMIT catch suite", 0,
            "apply process_control_relational_policy; C2B3 deliberately adds no primary-to-secondary relation; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "ordinary SQLite close failure suppressed; no deliberate primary-to-secondary relation, scrub, or restoration; exact interpreter graph shape is not promised",
            False,
        ),
        (
            "C6K3", "C6", "K3", "unknown",
            "propagate original COMMIT-time GeneratorExit",
            "identical original commit exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same COMMIT catch suite", 0,
            "apply process_control_relational_policy; C2B3 deliberately adds no primary-to-secondary relation; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "other ordinary close failure suppressed; no deliberate primary-to-secondary relation, scrub, or restoration; exact interpreter graph shape is not promised",
            False,
        ),
        (
            "C6K4", "C6", "K4", "unknown",
            "propagate original COMMIT-time GeneratorExit",
            "identical original commit exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same COMMIT catch suite", 0,
            "apply process_control_relational_policy; C2B3 deliberately adds no primary-to-secondary relation; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "close-time KeyboardInterrupt secondary relation classified by process_control_relational_policy; no deliberate C2B3-owned graph relation or material; exact interpreter graph shape is not promised",
            False,
        ),
        (
            "C6K5", "C6", "K5", "unknown",
            "propagate original COMMIT-time GeneratorExit",
            "identical original commit exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same COMMIT catch suite", 0,
            "apply process_control_relational_policy; C2B3 deliberately adds no primary-to-secondary relation; exact interpreter graph shape is not promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "close-time SystemExit secondary relation classified by process_control_relational_policy; no deliberate C2B3-owned graph relation or material; exact interpreter graph shape is not promised",
            False,
        ),
        (
            "C6K6", "C6", "K6", "unknown",
            "propagate original COMMIT-time GeneratorExit",
            "identical original commit exception object, exact type and args; SystemExit.code not applicable",
            "bare raise in the same COMMIT catch suite", 0,
            "dispatch by object identity: same_instance iff commit_exception is cleanup_exception; otherwise distinct_instance; no exact graph or traceback shape is promised",
            "closure not proved; retained connection", "private _WriterSessionResource",
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "QU",
            "retained as resource-owned and unavailable",
            "completed identity removed without clearing resource-owned slot",
            "retained by quarantined resource",
            "QU and custody published before propagation",
            "post_close_cleanup_contract disposal only", False,
            "after T1 publishes X, explicit commit-outcome resolver in a new session with a fresh lease and identical safe command",
            False, False,
            "object-identity discriminator selects same_instance or distinct_instance; original COMMIT-time GeneratorExit remains primary and C2B3 deliberately adds no graph relation or material",
            False,
        ),
    ),
    "controller_and_resource_custody": {
        "controller_states": (
            "_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED",
            "_CONTROLLER_COMMIT_SUCCEEDED_QUARANTINED",
            "_CONTROLLER_COMMIT_UNCERTAIN_CONNECTION_CLOSED_CLEANUP_PENDING",
            "_CONTROLLER_COMMIT_SUCCEEDED_CONNECTION_CLOSED_CLEANUP_PENDING",
        ),
        "writer_session_resource_states": (
            "_COMMIT_UNCERTAIN_QUARANTINED",
            "_COMMIT_SUCCEEDED_QUARANTINED",
            "_COMMIT_UNCERTAIN_CONNECTION_CLOSED_CLEANUP_PENDING",
            "_COMMIT_SUCCEEDED_CONNECTION_CLOSED_CLEANUP_PENDING",
        ),
        "state_mapping": (
            ("_CONTROLLER_COMMIT_UNCERTAIN_QUARANTINED", "_COMMIT_UNCERTAIN_QUARANTINED", "QU"),
            ("_CONTROLLER_COMMIT_SUCCEEDED_QUARANTINED", "_COMMIT_SUCCEEDED_QUARANTINED", "QK"),
            ("_CONTROLLER_COMMIT_UNCERTAIN_CONNECTION_CLOSED_CLEANUP_PENDING", "_COMMIT_UNCERTAIN_CONNECTION_CLOSED_CLEANUP_PENDING", "PU"),
            ("_CONTROLLER_COMMIT_SUCCEEDED_CONNECTION_CLOSED_CLEANUP_PENDING", "_COMMIT_SUCCEEDED_CONNECTION_CLOSED_CLEANUP_PENDING", "PK"),
        ),
        "controller_custody_through_close_attempt": True,
        "custody_transfer_when_close_not_proved": "exactly once into _WriterSessionResource",
        "publication_before_outward_result_or_exception": True,
        "operation_identity_removed_on_unwind": True,
        "quarantined_resource_slot_cleared_by_operation_lease": False,
        "operation_lease_artificially_active_after_unwind": False,
        "connection_closed_pending_state_has_raw_connection_custody": False,
        "pending_cleanup_progress_owner": "private _WriterSessionResource only",
        "new_operation_admission_while_QU_QK_PU_or_PK": False,
        "writer_lock_release_gate": "L1 normal LOCK_UN return followed by release_proved publication; descriptor close is not proof",
        "X_gate": "applicable connection proof, R1/R2/R3, L1 release_proved, and H2 complete; H1 outcome may be reclamation_unknown and H3 follows X",
        "forbidden_extra_states": (
            "COMMIT-time process control pending propagation",
            "nested close-time process-control exception",
            "stored generic exception object",
        ),
        "process_control_exception_custody": "active catch suite only; never session state",
    },
    "process_control_relational_policy": {
        "inventory": (
            "KeyboardInterrupt",
            "SystemExit",
            "GeneratorExit",
        ),
        "guarantee_scope": "C2B3 deliberate actions only",
        "forbidden_deliberate_actions": (
            "assign, clear, restore, scrub, or sanitize cause",
            "assign, clear, restore, scrub, or sanitize context",
            "assign, clear, restore, scrub, or sanitize suppression",
            "assign, clear, restore, scrub, or sanitize traceback",
            "manufacture a graph cycle or graph relationship",
            "add a note or private payload",
            "create a new primary-to-secondary relationship",
            "reconstruct the selected object to sanitize caller material",
        ),
        "interpreter_managed_changes": "cause, context, suppression, cycle, and traceback effects from nested raising and catching are permitted and are not attributed to C2B3",
        "exact_before_after_graph_reachability_cycle_or_traceback_promise": False,
        "preexisting_relation_deliberately_removed": False,
        "exact_interpreter_preservation_guaranteed": False,
        "coordinator_generated_safe_error": {
            "value": "fresh SQLiteMutationStoreError(commit_outcome_unknown)",
            "content_free": True,
            "raise_form": "explicit raise from None",
            "cause": None,
            "context": None,
            "suppress_context": True,
            "notes": "absent",
            "retained_source_exception": False,
            "forbidden_material": (
                "raw connection or cursor",
                "transaction controller or mutation slot",
                "authority lock or writer lock",
                "SQL, parameters, or path",
                "WorkSpec or safe command",
                "commit, close, cleanup, or raw process-control material",
            ),
        },
        "raw_process_control": {
            "classification": "raw control flow; never a privacy-safe report, persistence, or diagnostic value",
            "selected_outward_object_preserved": True,
            "exact_type_and_args": True,
            "SystemExit_code_preserved": True,
            "sanitize_or_reconstruct_preexisting_payload": False,
            "serialize_persist_log_format_render_or_report": False,
            "C2B3_owned_private_material_added_or_copied": False,
            "deliberate_primary_to_secondary_relation_added": False,
            "only_permitted_propagation": "bare raise in the governing catch suite while the selected primary is actively handled",
            "forbidden_propagation": (
                "named raise merely to propagate later",
                "reconstructed exception",
                "helper-owned delayed propagation",
                "explicit with_traceback",
                "raise-from transformation",
                "add_note",
            ),
        },
        "distinct_graph_disjoint": {
            "primary_precedence": "selected process control under the matrix precedence rule",
            "objects_are_distinct": True,
            "deliberate_primary_to_secondary_relation_added": False,
            "exact_full_graph_shape_promised": False,
        },
        "distinct_prelinked": {
            "primary_precedence": "selected process control under the matrix precedence rule",
            "covered_prelinks": ("cause", "context"),
            "preexisting_link_deliberately_scrubbed_or_restored": False,
            "additional_deliberate_relation_added": False,
            "interpreter_replacement_reversal_or_cycle_handling_permitted": True,
            "exact_link_preservation_promised": False,
            "absolute_secondary_unreachability_claim": False,
        },
        "separately_linked_third_exception": {
            "deliberate_scrub_restore_or_copy": False,
            "exact_reachability_or_cycle_shape_promised": False,
            "cycle_safe_identity_traversal_required_in_tests": True,
        },
        "same_instance": {
            "selection": "commit_exception is cleanup_exception",
            "original_object_remains_primary": True,
            "distinct_secondary_exists": False,
            "exact_object_type_args_and_SystemExit_code": True,
            "notes_cause_context_or_private_material_added_by_C2B3": False,
            "exact_pre_second_raise_traceback_or_complete_graph_restored": False,
            "recursive_snapshot_or_interpreter_restoration_machinery": False,
        },
        "preexisting_private_payload": {
            "may_exist_in": (
                "args or SystemExit.code",
                "notes",
                "cause or context",
                "traceback locals",
            ),
            "copied_or_added_by_C2B3": False,
            "serialized_logged_persisted_rendered_or_reported": False,
            "universal_sanitization_claim": False,
            "selected_raw_control_flow_preserved": True,
        },
    },
    "legacy_exception_probe_ledger_classification": {
        "ledger_path": "commit_uncertainty_cleanup_gate.close_not_proved.process_control_exception_graph_ledger",
        "classification": "historical_runtime_observation",
        "normative": False,
        "operative_for_c2b3b": False,
        "portable_contract": False,
        "preserved_for_original_c2b3a_evidence": True,
        "superseded_for_target_semantics_by": "process_control_relational_policy",
        "observed_values_scope": "exact traceback, cause, context, suppression, cycle, and reachability values are observations of the original bounded reference branch only",
        "consumer_rule": "no implementation, test oracle, planning projection, or future prompt may use those observed values as target requirements",
    },
    "post_close_cleanup_contract": {
        "state_legend": {
            "A": "normal active session",
            "QU": "commit uncertain; connection closure unproved",
            "QK": "commit known committed; connection closure unproved",
            "PU": "commit uncertain; connection closure proved and custody cleared; residual cleanup pending",
            "PK": "commit known committed; connection closure proved and custody cleared; residual cleanup pending",
            "X": "authority-terminal; descriptor reclamation and post-X session-registry housekeeping are not gates",
        },
        "ordered_steps": (
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
        ),
        "order_is_exact_and_not_atomic": True,
        "fault_model": {
            "before_effect": "retain the prior truthful non-admitting state and all not-yet-completed custody",
            "after_effect": "publish and retain the complete monotonic post-effect fact before suppression or propagation",
            "completed_effect_repeated_unsafely": False,
            "retry_requires_reachable_wrapper": True,
        },
        "acknowledgement_complete_boundary": {
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
        },
        "step_contracts": {
            "P0": {
                "name": "freeze admission and select one cleanup owner",
                "applies_to": ("A", "QU", "QK", "PU", "PK"),
                "A_transition": "stable non-admitting resource-owned closing posture",
                "active_operations": "drain before cleanup",
                "same_thread_active_operation": "writer_session_close_during_operation",
                "cleanup_owners": 1,
                "interruption_posture": "stable non-admitting resource-owned closing posture with monotonic progress",
            },
            "C1": {
                "name": "retained transaction-connection close",
                "applies_only_to": ("QU", "QK"),
                "proof": "observed normal retained_connection.close() return",
                "non_normal_return": "identical connection retained; preserve QU or QK",
                "retry": "same retained connection only before proof while retry_reachable=true",
                "forbidden": ("SQL", "BEGIN", "rollback", "readback", "reopen", "semantic retry"),
                "close_after_proof": False,
                "direct_C4_C6_K1_repeats_C1": False,
            },
            "C2": {
                "name": "closure-proof publication and custody clear",
                "transitions": (
                    ("QU", "PU"),
                    ("QK", "PK"),
                    ("C4-C6/K1", "PU"),
                ),
                "normal_effects": (
                    "record connection_closed_proved",
                    "clear raw connection custody",
                    "publish pending state",
                ),
                "acknowledgement_before_residual_cleanup_or_outward_propagation": True,
                "reversion_or_recustody": False,
            },
            "R1": {
                "name": "credential authority revocation and drop",
                "precondition": "no active operation",
                "authority_order": "revoke proof verification and clear every resource owner before best-effort overwrite",
                "mutable_overwrite": "best-effort memory hygiene; no Python zeroization guarantee",
                "idempotently_resumable": True,
                "scrub_failure_restores_authority": False,
                "private_proof_emitted": False,
            },
            "R2": {
                "name": "mutation-slot release",
                "precondition": "credential authority revoked",
                "effect": "clear only the exact resource-owned slot and identity under the session condition",
                "before_effect_fault": "slot retained",
                "after_effect_fault": "cleared fact retained",
                "idempotent_conditional_retry": True,
            },
            "R3": {
                "name": "database-binding release",
                "precondition": "mutation slot clear",
                "effect": "clear resource and cleanup-owner binding references",
                "idempotent_retry": True,
                "SQLite_activity": False,
            },
            "L1": {
                "name": "explicit writer-lock unlock and proof",
                "preconditions": (
                    "applicable connection closure proved",
                    "credential authority revoked",
                    "mutation slot clear",
                    "database binding released",
                    "active operations absent",
                    "exact descriptor retained",
                    "exact authority-lock registry entry present",
                ),
                "proof": "normal return from real fcntl.flock(exact_retained_fd, LOCK_UN), then release_proved publication under lifecycle/fork gate",
                "every_non_normal_exit": "release_unproved",
                "release_unproved_retains": (
                    "exact descriptor",
                    "exact authority-lock registry entry",
                    "exact writer-session registry entry",
                    "truthful session progress",
                ),
                "release_unproved_forbids": (
                    "descriptor close",
                    "X publication",
                    "recovery or replay",
                    "new same-process writer",
                ),
                "same_fd_retry": "only exact retained descriptor with no close attempt, while retry_reachable=true",
                "ordinary_failure": "suppress after release_unproved publication",
                "process_control_without_primary": "propagate exact object after release_unproved publication",
                "COMMIT_process_control_primary": "retains absolute outward precedence",
                "explicit_cleanup_uses_one_shot_finalizer_callback": False,
            },
            "H1": {
                "name": "descriptor reclamation",
                "precondition": "release_proved",
                "writer_lock_release_proof": False,
                "numeric_fd_removed_before_one_close_attempt": True,
                "normal_return": "reclaimed",
                "every_non_normal_exit": "reclamation_unknown",
                "retry_numeric_fd": False,
                "restore_fd_to_retryable_state": False,
                "gates_X": False,
            },
            "H2": {
                "name": "authority-lock terminalization and registry removal",
                "preconditions": ("release_proved", "one H1 attempt"),
                "under_lifecycle_fork_gate_order": (
                    "publish release-proved terminal facts and descriptor outcome",
                    "identity-check and remove exact _ACTIVE_LOCK_RESOURCES entry",
                ),
                "complete_after_both_effects": True,
                "before_terminal_publication_fault": "retain release-proved pending truth and registry entry",
                "between_publication_and_removal_fault": "retain terminalized-but-registered truth; exact removal retry only while retry_reachable=true",
                "release_unproved_lookup": "busy, never stale",
                "same_process_acquisition": "only after exact registry removal",
                "fork_snapshot": "every descriptor-bearing active or release-unproved resource",
                "runs_on_L1_failure": False,
            },
            "T1": {
                "name": "publish X",
                "preconditions": ("applicable C2", "R1", "R2", "R3", "L1 release_proved", "H2 complete"),
                "effects": (
                    "clear non-authoritative lock-wrapper reference",
                    "publish X under writer-session condition",
                ),
                "writer_session_registry_retained_through_X": True,
                "before_effect_fault": "prior pending state",
                "after_effect_fault": "truthful X",
                "optimistic_X": False,
                "recovery_and_replay_after_X_only": True,
            },
            "H3": {
                "name": "writer-session registry housekeeping",
                "precondition": "X",
                "effects": (
                    "identity-check and remove exact _ACTIVE_SESSION_RESOURCES entry",
                    "complete finalizer bookkeeping",
                    "record explicit close-call completion",
                ),
                "interruption_reverses_X": False,
                "stale_X_entry": "non-authoritative retention leak only",
                "retry": "idempotent only while wrapper remains reachable",
                "gates_recovery_or_replay": False,
            },
        },
        "cleanup_exception_precedence": {
            "ordinary": "suppress after truthful progress; retain every incomplete responsibility",
            "process_control_without_primary": "publish progress then propagate exact cleanup-time object under deliberate-action-only policy",
            "with_COMMIT_process_control_primary": "publish progress, suppress later ordinary failure, deliberately attach no distinct later process-control object, then bare-reraise original primary",
            "finalizer": "catch and suppress every BaseException after truthful progress publication",
        },
        "matrix_continuation": {
            "direct_entry_rows": ("C4K1", "C5K1", "C6K1"),
            "entry_state": "PU after C2 before residual cleanup",
            "possible_propagation_states": ("PU", "X"),
            "C2K1_C3K1_state": "A",
            "C2K1_C3K1_later_route": "ordinary A -> X through P0/R1/R2/R3/L1/H1/H2/T1/H3",
            "remaining_close_failure_rows": "QU or QK until a later C1/C2 continuation",
        },
        "ordinary_A_to_X": {
            "entry": "_SQLiteWriterSession.close()",
            "order": ("P0", "R1", "R2", "R3", "L1", "H1", "H2", "T1", "H3"),
            "shared_lock_release_primitive": True,
            "retained_transaction_connection_in_C2K1_or_C3K1": False,
        },
        "external_linearization": {
            "kernel_unlock_effect": "another process may acquire after the operating system applies LOCK_UN",
            "recorded_release_proof": "old process knows exclusion ended only after normal LOCK_UN return and release_proved publication",
            "same_process_acquisition": "after H2 exact authority-lock registry removal",
            "C2B3_recovery_or_replay": "after T1 publishes X",
            "cross_process_writer_between_kernel_effect_and_X": "permitted after old operations, credential, slot, binding, and applicable connection custody are gone",
            "atomic_kernel_unlock_registry_X_close_return_claim": False,
            "public_close_None_is_authority_receipt": False,
        },
        "recovery_replay_gate": {
            "blocked_states": ("A-closing", "QU", "QK", "PU", "PK"),
            "blocked_lock_facet": "release_unproved",
            "uncertainty_recovery_path": "QU -> PU -> X",
            "known_committed_replay_path": "QK -> PK -> X",
            "admitted_state": "X",
        },
    },
    "explicit_disposal": {
        "applies_to": ("A", "QU", "QK", "PU", "PK"),
        "retryable_path": "explicit close while the exact wrapper remains reachable",
        "repeatable_until_X_while_retry_reachable": True,
        "uses_weakref_finalize_callback_as_retry_mechanism": False,
        "ordinary_A_route": "P0/R1/R2/R3/L1/H1/H2/T1/H3",
        "while_QU_or_QK": "attempt retained_connection.close(); remain in the same state on unproved close",
        "proved_close_transitions": (
            ("QU", "PU"),
            ("QK", "PK"),
        ),
        "while_PU_or_PK": "never close the connection again; resume only incomplete residual cleanup",
        "connection_close_after_proof": False,
        "monotonic_progress_preserved": True,
        "X_gate": "L1 release_proved and H2 complete after applicable connection proof, credential revocation, slot release, and binding release",
        "descriptor_reclamation_gates_X": False,
        "writer_session_registry_removal_gates_X": False,
        "forbidden_actions": (
            "SQL",
            "BEGIN",
            "rollback",
            "readback",
            "reopen",
            "semantic retry",
            "caller-authored cleanup clearance",
            "connection close after PU or PK publication",
        ),
        "ordinary_close_failure_before_proof": "suppressed; QU or QK, custody, slot, lock, binding, and registry retention unchanged",
        "process_control_close_failure_before_proof": "propagate the identical raw KeyboardInterrupt, SystemExit, or GeneratorExit; QU or QK unchanged",
        "ordinary_residual_cleanup_failure": "suppressed; retain PU or PK plus actual monotonic progress",
        "process_control_residual_cleanup_failure": "publish actual progress, apply deliberate-action-only relational policy, and preserve precedence",
        "closure_proof": "normal return from retained_connection.close() only",
        "writer_lock_release_proof": "normal return from real fcntl.flock(exact_retained_fd, LOCK_UN) only",
        "public_close_result": None,
        "cleanup_token_or_authority_receipt": False,
    },
    "finalizer": {
        "weakref_finalize_invocation": "one-shot",
        "automatic_retry": False,
        "catches": "BaseException",
        "bounded_attempt": "monotonically attempt any reachable subset of C1/C2/R1/R2/R3/L1/H1/H2/T1/H3 once",
        "exception_propagated_logged_serialized_or_reported": False,
        "failure_before_close_proof": "suppress and preserve QU or QK with custody and governance resources unchanged",
        "normal_close_return": "publish PU or PK before residual cleanup; never close the connection again",
        "failure_after_close_proof": "suppress and preserve PU, PK, or ordinary-closing posture plus actual monotonic progress; never restore connection custody",
        "success_posture": "authority cleanup complete if T1 reaches X; H3 remains post-X housekeeping",
        "failure_before_X_after_wrapper_loss": {
            "finalizer_attempted": True,
            "retry_reachable": False,
            "further_in_process_attempt_promised": False,
            "posture": "truthful fail-closed state and progress until process termination",
        },
        "registry_roles": "custody and fork/process hygiene only; never lookup, disposal, scheduling, retry, orchestration, recovery, or authority handle",
        "hidden_cleanup_service_or_registry_scan": False,
        "eventual_reclamation_claim": "process termination only after failed finalization with no reachable wrapper",
        "second_finalizer_invocation": False,
        "later_disposal_after_wrapper_loss": False,
        "garbage_collection_is_closure_proof": False,
        "garbage_collection_is_cleanup_completion_proof": False,
        "fork_child": "snapshot active and release-unproved descriptor resources; close inherited child descriptors without LOCK_UN; invalidate child session authority and clear child registries without changing parent proof",
        "cross_thread_finalization": "bounded close-only or cleanup posture; never cross-thread SQL",
    },
    "recovery_and_safe_command_custody": {
        "transient_safe_command_count": 1,
        "identical_object_used_for_apply_and_recovery": True,
        "reconstructed_from_exception": False,
        "exception_contains_command": False,
        "complete_work_spec_reaches_recovery": False,
        "complete_work_spec_persisted_logged_reported_or_retained": False,
        "restart_recoverable_work_spec": False,
        "original_session_disposed_before_new_session": True,
        "original_session_state_before_new_session": "X",
        "writer_lock_release_proved_before_recovery": True,
        "authority_lock_registry_removed_before_X": True,
        "writer_session_registry_removed_before_X": False,
        "recovery_or_replay_blocked_states": ("A-closing", "QU", "QK", "PU", "PK"),
        "recovery_or_replay_blocked_lock_facet": "release_unproved",
        "recovery_or_replay_admitted_only_after": "T1 publishes X",
        "new_session_operation_lease": "fresh",
        "mutation_slot": "existing shared mutation slot",
        "commit_outcome_recovery_dispositions": (
            "committed_exact",
            "definitely_not_committed",
            "unresolved",
        ),
        "commit_time_process_control_recovery": "explicit resolver only after PU reaches X in a new concrete session",
        "known_committed_close_time_process_control": "ordinary initialization apply only after PK reaches X gives receipt-first exact replay; commit-outcome resolver forbidden",
        "fresh_apply_convenience_wrapper": "_initialize_development_program(..., work_spec=...) remains fresh-apply only and does not return a recoverable command",
        "automatic_semantic_retry": False,
    },
    "future_c2b3b_path_scope_status": {
        "required_production_paths": (
            "src/ge_nwp_coordinator/_development_program_initialization_contracts.py",
            "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py",
            "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
            "src/ge_nwp_coordinator/sqlite_writer_session.py",
            "src/ge_nwp_coordinator/sqlite_connection.py",
            "src/ge_nwp_coordinator/state_authority_lock.py",
        ),
        "required_documentation_status_paths": (
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
        ),
        "required_changed_test_paths": (
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
        ),
        "required_path_counts": (6, 10, 11),
        "expected_actual_write_paths": 27,
        "contingency_path": "tests/test_c2b2_private_development_readers.py",
        "contingency_path_status": "protected and unchanged unless later implementation proves genuine need",
        "maximum_paths": 28,
        "twenty_ninth_path": "hard stop and scope reassessment condition",
        "newly_required_relative_to_old_manifest": (
            "src/ge_nwp_coordinator/state_authority_lock.py",
            ".docs/writer-session-authority.md",
            "tests/test_state_authority_lock.py",
            "tests/test_sqlite_b2c_writer_session.py",
        ),
        "protected_unchanged_regressions": (
            "tests/test_b3c1b_rollback_only_writer_fencing.py",
            "tests/test_b3c4b_private_atomic_transition_persistence.py",
            "tests/test_sqlite_b2b_lock_integration.py",
        ),
        "forbidden_or_unnecessary": (
            "sqlite_errors.py",
            "schema or migrations",
            "package exports",
            "public models",
            "StateStore public methods",
            "pyproject.toml",
            "another repository",
        ),
        "c2b3b_source_authorized_by_addendum": False,
        "future_implementation_scope_supersession": {
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
        },
    },
    "direct_oracle_requirements": {
        "separately_authored_direct_literal": True,
        "owner_derived_expected_values": False,
        "positive_reference_cases": (
            "distinct cross-class process-control pairs",
            "distinct same-class KeyboardInterrupt, SystemExit, and GeneratorExit pairs",
            "same-instance KeyboardInterrupt, SystemExit, and GeneratorExit pairs",
            "pre-linked cause and separately pre-linked context",
            "separately linked third exception and cycle-safe identity traversal",
            "no exact interpreter graph promise and exact outward identity/type/args/SystemExit.code",
            "raw synthetic payload never copied to a safe Coordinator value or artifact",
            "QU/QK retained-close normal, ordinary, KeyboardInterrupt, SystemExit, and GeneratorExit outcomes",
            "every P0/C1/C2/R1/R2/R3/L1/H1/H2/T1/H3 before/after boundary",
            "release_unproved same-fd retry and descriptor reclamation ambiguity without numeric-fd retry",
            "H2 terminalization before authority-registry removal and X before H3",
            "finalizer failure with retry_reachable=false and ordinary A -> X",
            "pre-X rejection and recovery/replay admission only after X",
        ),
        "mutant_families": (
            "type-to-identity collapse or wrong diagonal routing",
            "exact graph, cycle, context, cause, suppression, or traceback promises",
            "deliberate graph scrub, restoration, payload copy, report, or universal sanitization",
            "descriptor close as release proof or descriptor-close retry",
            "X, authority-registry removal, same-process acquisition, recovery, or replay before their proof gates",
            "writer-session registry removal before X or descriptor reclamation required for X",
            "retry after wrapper loss, registry scan, hidden disposal, or finalizer automatic retry",
            "C2K1/C3K1 pending-state routing or ordinary A -> X lock-primitive bypass",
            "future-path omission, stale 23/24 scope, dynamic owner/oracle derivation, or C2B3B implementation claim",
        ),
        "semantic_execution_protection": {
            "diagnostic": "C2B3A_INDEPENDENT_ORACLE_SEMANTIC_EXECUTION_INVALID",
            "expect_violation_exact_validator_and_diagnostic": True,
            "mutant_dataflow": "each protected mutant has exactly one candidate = _candidate(), one or more direct candidate-rooted assignments, and the identical candidate reaches one final _expect_violation with the exact diagnostic",
            "mutant_control_flow": "each protected mutant is one branch-free linear function with no unrelated local assignment, call, or possible pre-validation termination",
            "positive_body_and_reference_helper_execution_protected": True,
            "positive_result_dataflow": "each helper result is a single immutable reaching definition consumed directly by discriminating field assertions; overwrite, deletion, mutation, alias, shadow target, and unused results are rejected",
            "bounded_isolated_physical_counterfactuals": True,
            "whole_file_source_hash_authority": False,
            "generic_semantic_dispatcher": False,
        },
    },
    "privacy_and_non_authority": {
        "C2B3_owned_forbidden_material": (
            "raw connection or cursor",
            "transaction controller",
            "mutation-slot object",
            "writer-lock object",
            "quarantine object or registry internals",
            "ordinary COMMIT or close exception",
            "SQL or parameters",
            "SQLite or operator-state path",
            "WorkSpec or complete WorkSpec representation",
            "credentials or authority-lock material",
            "private environment values",
        ),
        "C2B3_owned_forbidden_destinations": (
            "public or persisted value",
            "result or conflict",
            "recovery disposition",
            "error graph or traceback note",
            "log or report",
            "generated artifact",
        ),
        "coordinator_generated_safe_error_is_content_free": True,
        "raw_process_control_policy": "process_control_relational_policy",
        "raw_process_control_is_report_or_persistence_surface": False,
        "preexisting_raw_process_control_payload_sanitized": False,
        "new_private_payload_or_graph_material_introduced_by_C2B3": False,
        "deliberate_primary_to_secondary_relation_introduced_by_C2B3": False,
        "exact_interpreter_graph_or_traceback_shape_promised": False,
        "tests_reports_and_provenance_are_evidence_only": True,
        "new_authority": False,
    },
    "nonimplementation": {
        "production_behavior": False,
        "schema_or_migration": False,
        "public_api_or_package_export": False,
        "StateStore_or_public_WriterSession_surface": False,
        "author_effect_source": False,
        "worker_scheduler_queue_service_model_or_reconciler": False,
        "Bridge_or_Execution_Substrate_behavior": False,
        "external_IO": False,
        "new_authority": False,
    },
}


EXPECTED_INITIALIZATION_GOLDEN_VECTOR = {'vector_id': 'c2b3a-initialization-single-work-v1',
 'vector_version': 1,
 'transaction_timestamp': '2026-08-21T12:34:56Z',
 'safe_command_input_values': {'mutation_ref': 'mutation-c2b3a-1',
                               'program_ref': 'program-c2b3a-1',
                               'program_version_ref': 'program-version-c2b3a-1',
                               'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                               'decision_ref': 'decision-c2b3a-1',
                               'preassigned_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                               'preassigned_candidate_ref': 'candidate-c2b3a-1',
                               'coding_global_stop_ref': 'coding-global-stop-c2b3a-1',
                               'coding_global_stop_version': 0,
                               'reason_code': 'program_genesis',
                               'source_intent_ref': 'source-intent-c2b3a-1',
                               'source_intent_digest': '1111111111111111111111111111111111111111111111111111111111111111',
                               'work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                             'work_spec_ref': 'work-spec-c2b3a-1',
                                                             'program_ref': 'program-c2b3a-1',
                                                             'program_version_ref': 'program-version-c2b3a-1',
                                                             'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                             'work_item_ref': 'work-item-c2b3a-1',
                                                             'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                             'repository_ref': 'repository-c2b3a-1',
                                                             'base_git_object_format': 'sha1',
                                                             'base_git_oid': '2222222222222222222222222222222222222222',
                                                             'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                  'PLANS.md',
                                                                                  'docs_contract_test.go'),
                                                             'validation_requirement_ref': 'validation-c2b3a-1',
                                                             'review_requirement_ref': 'review-c2b3a-1',
                                                             'privacy_classification': 'private_work_spec',
                                                             'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                             'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'}},
 'work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                               'work_spec_ref': 'work-spec-c2b3a-1',
                               'program_ref': 'program-c2b3a-1',
                               'program_version_ref': 'program-version-c2b3a-1',
                               'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                               'work_item_ref': 'work-item-c2b3a-1',
                               'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                               'repository_ref': 'repository-c2b3a-1',
                               'base_git_object_format': 'sha1',
                               'base_git_oid': '2222222222222222222222222222222222222222',
                               'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                    'PLANS.md',
                                                    'docs_contract_test.go'),
                               'validation_requirement_ref': 'validation-c2b3a-1',
                               'review_requirement_ref': 'review-c2b3a-1',
                               'privacy_classification': 'private_work_spec',
                               'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                               'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
 'accepted_intent_safe_projection': {'schema_id': 'governed-execution.nwp-development-accepted-intent-safe-projection.v1',
                                     'source_intent_ref': 'source-intent-c2b3a-1',
                                     'source_intent_digest': '1111111111111111111111111111111111111111111111111111111111111111',
                                     'initial_work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                           'work_spec_ref': 'work-spec-c2b3a-1',
                                                                           'program_ref': 'program-c2b3a-1',
                                                                           'program_version_ref': 'program-version-c2b3a-1',
                                                                           'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                           'work_item_ref': 'work-item-c2b3a-1',
                                                                           'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                           'repository_ref': 'repository-c2b3a-1',
                                                                           'base_git_object_format': 'sha1',
                                                                           'base_git_oid': '2222222222222222222222222222222222222222',
                                                                           'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                'PLANS.md',
                                                                                                'docs_contract_test.go'),
                                                                           'validation_requirement_ref': 'validation-c2b3a-1',
                                                                           'review_requirement_ref': 'review-c2b3a-1',
                                                                           'privacy_classification': 'private_work_spec',
                                                                           'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                           'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                                     'safe_projection_digest': '8e76f55695e0f3bda1af480bb00fbd4bcff4c6c0270d80c65ffbe61f67c92ce1'},
 'accepted_intent_canonical_mapping': {'schema_id': 'governed-execution.nwp-development-accepted-intent-safe-projection.v1',
                                       'source_intent_ref': 'source-intent-c2b3a-1',
                                       'source_intent_digest': '1111111111111111111111111111111111111111111111111111111111111111',
                                       'initial_work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                             'work_spec_ref': 'work-spec-c2b3a-1',
                                                                             'program_ref': 'program-c2b3a-1',
                                                                             'program_version_ref': 'program-version-c2b3a-1',
                                                                             'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                             'work_item_ref': 'work-item-c2b3a-1',
                                                                             'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                             'repository_ref': 'repository-c2b3a-1',
                                                                             'base_git_object_format': 'sha1',
                                                                             'base_git_oid': '2222222222222222222222222222222222222222',
                                                                             'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                  'PLANS.md',
                                                                                                  'docs_contract_test.go'),
                                                                             'validation_requirement_ref': 'validation-c2b3a-1',
                                                                             'review_requirement_ref': 'review-c2b3a-1',
                                                                             'privacy_classification': 'private_work_spec',
                                                                             'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                             'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'}},
 'accepted_intent_canonical_utf8_hex': '7b22696e697469616c5f776f726b5f737065635f736166655f70726f6a656374696f6e223a7b2261636365707465645f696e74656e745f7265766973696f6e5f726566223a2261636365707465642d696e74656e742d63326233612d31222c22617574686f72697a65645f7061746873223a5b222e646f63732f73797374656d5f6f766572766965772f6879627269645f696e746567726174696f6e5f6172636869746563747572655f6164722e6d64222c22504c414e532e6d64222c22646f63735f636f6e74726163745f746573742e676f225d2c22626173655f6769745f6f626a6563745f666f726d6174223a2273686131222c22626173655f6769745f6f6964223a2232323232323232323232323232323232323232323232323232323232323232323232323232323232222c22707269766163795f636c617373696669636174696f6e223a22707269766174655f776f726b5f73706563222c2270726f6772616d5f726566223a2270726f6772616d2d63326233612d31222c2270726f6772616d5f76657273696f6e5f726566223a2270726f6772616d2d76657273696f6e2d63326233612d31222c227265706f7369746f72795f726566223a227265706f7369746f72792d63326233612d31222c227265766965775f726571756972656d656e745f726566223a227265766965772d63326233612d31222c22736166655f70726f6a656374696f6e5f646967657374223a2231613464653930343961353439623536373161653163303662323831656563393939393335393934306138623631386165663766663762343865343363656162222c22736368656d615f6964223a22676f7665726e65642d657865637574696f6e2e6e77702d646576656c6f706d656e742d776f726b2d737065632d736166652d70726f6a656374696f6e2e7631222c2276616c69646174696f6e5f726571756972656d656e745f726566223a2276616c69646174696f6e2d63326233612d31222c22776f726b5f6974656d5f726566223a22776f726b2d6974656d2d63326233612d31222c22776f726b5f6974656d5f7265766973696f6e5f726566223a22776f726b2d6974656d2d7265766973696f6e2d63326233612d31222c22776f726b5f737065635f646967657374223a2232393532633962303332353762343364363939383366616165626565383961356538383466373161356239646465366165623736393532323463643233643963222c22776f726b5f737065635f726566223a22776f726b2d737065632d63326233612d31227d2c22736368656d615f6964223a22676f7665726e65642d657865637574696f6e2e6e77702d646576656c6f706d656e742d61636365707465642d696e74656e742d736166652d70726f6a656374696f6e2e7631222c22736f757263655f696e74656e745f646967657374223a2231313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131222c22736f757263655f696e74656e745f726566223a22736f757263652d696e74656e742d63326233612d31227d',
 'accepted_intent_safe_projection_digest': '8e76f55695e0f3bda1af480bb00fbd4bcff4c6c0270d80c65ffbe61f67c92ce1',
 'safe_command': {'schema_id': 'governed-execution.nwp-initialize-development-program-command.v1',
                  'mutation_ref': 'mutation-c2b3a-1',
                  'program_ref': 'program-c2b3a-1',
                  'program_version_ref': 'program-version-c2b3a-1',
                  'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                  'decision_ref': 'decision-c2b3a-1',
                  'preassigned_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                  'preassigned_candidate_ref': 'candidate-c2b3a-1',
                  'coding_global_stop_ref': 'coding-global-stop-c2b3a-1',
                  'coding_global_stop_version': 0,
                  'reason_code': 'program_genesis',
                  'work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                'work_spec_ref': 'work-spec-c2b3a-1',
                                                'program_ref': 'program-c2b3a-1',
                                                'program_version_ref': 'program-version-c2b3a-1',
                                                'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                'work_item_ref': 'work-item-c2b3a-1',
                                                'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                'repository_ref': 'repository-c2b3a-1',
                                                'base_git_object_format': 'sha1',
                                                'base_git_oid': '2222222222222222222222222222222222222222',
                                                'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                     'PLANS.md',
                                                                     'docs_contract_test.go'),
                                                'validation_requirement_ref': 'validation-c2b3a-1',
                                                'review_requirement_ref': 'review-c2b3a-1',
                                                'privacy_classification': 'private_work_spec',
                                                'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                  'accepted_intent_safe_projection': {'schema_id': 'governed-execution.nwp-development-accepted-intent-safe-projection.v1',
                                                      'source_intent_ref': 'source-intent-c2b3a-1',
                                                      'source_intent_digest': '1111111111111111111111111111111111111111111111111111111111111111',
                                                      'initial_work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                                            'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                            'program_ref': 'program-c2b3a-1',
                                                                                            'program_version_ref': 'program-version-c2b3a-1',
                                                                                            'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                            'work_item_ref': 'work-item-c2b3a-1',
                                                                                            'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                            'repository_ref': 'repository-c2b3a-1',
                                                                                            'base_git_object_format': 'sha1',
                                                                                            'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                            'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                                 'PLANS.md',
                                                                                                                 'docs_contract_test.go'),
                                                                                            'validation_requirement_ref': 'validation-c2b3a-1',
                                                                                            'review_requirement_ref': 'review-c2b3a-1',
                                                                                            'privacy_classification': 'private_work_spec',
                                                                                            'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                            'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                                                      'safe_projection_digest': '8e76f55695e0f3bda1af480bb00fbd4bcff4c6c0270d80c65ffbe61f67c92ce1'},
                  'command_digest': 'f2e9b97cc6bc70b24b75925f534d375edec3ad51382a966e2c95930eb8a5c5c8'},
 'safe_command_canonical_mapping': {'schema_id': 'governed-execution.nwp-initialize-development-program-command.v1',
                                    'mutation_ref': 'mutation-c2b3a-1',
                                    'program_ref': 'program-c2b3a-1',
                                    'program_version_ref': 'program-version-c2b3a-1',
                                    'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                    'decision_ref': 'decision-c2b3a-1',
                                    'preassigned_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                    'preassigned_candidate_ref': 'candidate-c2b3a-1',
                                    'coding_global_stop_ref': 'coding-global-stop-c2b3a-1',
                                    'coding_global_stop_version': 0,
                                    'reason_code': 'program_genesis',
                                    'work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                  'work_spec_ref': 'work-spec-c2b3a-1',
                                                                  'program_ref': 'program-c2b3a-1',
                                                                  'program_version_ref': 'program-version-c2b3a-1',
                                                                  'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                  'work_item_ref': 'work-item-c2b3a-1',
                                                                  'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                  'repository_ref': 'repository-c2b3a-1',
                                                                  'base_git_object_format': 'sha1',
                                                                  'base_git_oid': '2222222222222222222222222222222222222222',
                                                                  'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                       'PLANS.md',
                                                                                       'docs_contract_test.go'),
                                                                  'validation_requirement_ref': 'validation-c2b3a-1',
                                                                  'review_requirement_ref': 'review-c2b3a-1',
                                                                  'privacy_classification': 'private_work_spec',
                                                                  'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                  'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                                    'accepted_intent_safe_projection': {'schema_id': 'governed-execution.nwp-development-accepted-intent-safe-projection.v1',
                                                                        'source_intent_ref': 'source-intent-c2b3a-1',
                                                                        'source_intent_digest': '1111111111111111111111111111111111111111111111111111111111111111',
                                                                        'initial_work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                                                              'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                                              'program_ref': 'program-c2b3a-1',
                                                                                                              'program_version_ref': 'program-version-c2b3a-1',
                                                                                                              'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                                              'work_item_ref': 'work-item-c2b3a-1',
                                                                                                              'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                                              'repository_ref': 'repository-c2b3a-1',
                                                                                                              'base_git_object_format': 'sha1',
                                                                                                              'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                                              'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                                                   'PLANS.md',
                                                                                                                                   'docs_contract_test.go'),
                                                                                                              'validation_requirement_ref': 'validation-c2b3a-1',
                                                                                                              'review_requirement_ref': 'review-c2b3a-1',
                                                                                                              'privacy_classification': 'private_work_spec',
                                                                                                              'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                                              'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                                                                        'safe_projection_digest': '8e76f55695e0f3bda1af480bb00fbd4bcff4c6c0270d80c65ffbe61f67c92ce1'}},
 'safe_command_canonical_utf8_hex': '7b2261636365707465645f696e74656e745f7265766973696f6e5f726566223a2261636365707465642d696e74656e742d63326233612d31222c2261636365707465645f696e74656e745f736166655f70726f6a656374696f6e223a7b22696e697469616c5f776f726b5f737065635f736166655f70726f6a656374696f6e223a7b2261636365707465645f696e74656e745f7265766973696f6e5f726566223a2261636365707465642d696e74656e742d63326233612d31222c22617574686f72697a65645f7061746873223a5b222e646f63732f73797374656d5f6f766572766965772f6879627269645f696e746567726174696f6e5f6172636869746563747572655f6164722e6d64222c22504c414e532e6d64222c22646f63735f636f6e74726163745f746573742e676f225d2c22626173655f6769745f6f626a6563745f666f726d6174223a2273686131222c22626173655f6769745f6f6964223a2232323232323232323232323232323232323232323232323232323232323232323232323232323232222c22707269766163795f636c617373696669636174696f6e223a22707269766174655f776f726b5f73706563222c2270726f6772616d5f726566223a2270726f6772616d2d63326233612d31222c2270726f6772616d5f76657273696f6e5f726566223a2270726f6772616d2d76657273696f6e2d63326233612d31222c227265706f7369746f72795f726566223a227265706f7369746f72792d63326233612d31222c227265766965775f726571756972656d656e745f726566223a227265766965772d63326233612d31222c22736166655f70726f6a656374696f6e5f646967657374223a2231613464653930343961353439623536373161653163303662323831656563393939393335393934306138623631386165663766663762343865343363656162222c22736368656d615f6964223a22676f7665726e65642d657865637574696f6e2e6e77702d646576656c6f706d656e742d776f726b2d737065632d736166652d70726f6a656374696f6e2e7631222c2276616c69646174696f6e5f726571756972656d656e745f726566223a2276616c69646174696f6e2d63326233612d31222c22776f726b5f6974656d5f726566223a22776f726b2d6974656d2d63326233612d31222c22776f726b5f6974656d5f7265766973696f6e5f726566223a22776f726b2d6974656d2d7265766973696f6e2d63326233612d31222c22776f726b5f737065635f646967657374223a2232393532633962303332353762343364363939383366616165626565383961356538383466373161356239646465366165623736393532323463643233643963222c22776f726b5f737065635f726566223a22776f726b2d737065632d63326233612d31227d2c22736166655f70726f6a656374696f6e5f646967657374223a2238653736663535363935653066336264613161663438306262303066626434626366663463366330323730643830633635666662653631663637633932636531222c22736368656d615f6964223a22676f7665726e65642d657865637574696f6e2e6e77702d646576656c6f706d656e742d61636365707465642d696e74656e742d736166652d70726f6a656374696f6e2e7631222c22736f757263655f696e74656e745f646967657374223a2231313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131222c22736f757263655f696e74656e745f726566223a22736f757263652d696e74656e742d63326233612d31227d2c22636f64696e675f676c6f62616c5f73746f705f726566223a22636f64696e672d676c6f62616c2d73746f702d63326233612d31222c22636f64696e675f676c6f62616c5f73746f705f76657273696f6e223a302c226465636973696f6e5f726566223a226465636973696f6e2d63326233612d31222c226d75746174696f6e5f726566223a226d75746174696f6e2d63326233612d31222c2270726561737369676e65645f63616e6469646174655f726566223a2263616e6469646174652d63326233612d31222c2270726561737369676e65645f73656d616e7469635f617474656d70745f726566223a2273656d616e7469632d617474656d70742d63326233612d31222c2270726f6772616d5f726566223a2270726f6772616d2d63326233612d31222c2270726f6772616d5f76657273696f6e5f726566223a2270726f6772616d2d76657273696f6e2d63326233612d31222c22726561736f6e5f636f6465223a2270726f6772616d5f67656e65736973222c22736368656d615f6964223a22676f7665726e65642d657865637574696f6e2e6e77702d696e697469616c697a652d646576656c6f706d656e742d70726f6772616d2d636f6d6d616e642e7631222c22776f726b5f737065635f736166655f70726f6a656374696f6e223a7b2261636365707465645f696e74656e745f7265766973696f6e5f726566223a2261636365707465642d696e74656e742d63326233612d31222c22617574686f72697a65645f7061746873223a5b222e646f63732f73797374656d5f6f766572766965772f6879627269645f696e746567726174696f6e5f6172636869746563747572655f6164722e6d64222c22504c414e532e6d64222c22646f63735f636f6e74726163745f746573742e676f225d2c22626173655f6769745f6f626a6563745f666f726d6174223a2273686131222c22626173655f6769745f6f6964223a2232323232323232323232323232323232323232323232323232323232323232323232323232323232222c22707269766163795f636c617373696669636174696f6e223a22707269766174655f776f726b5f73706563222c2270726f6772616d5f726566223a2270726f6772616d2d63326233612d31222c2270726f6772616d5f76657273696f6e5f726566223a2270726f6772616d2d76657273696f6e2d63326233612d31222c227265706f7369746f72795f726566223a227265706f7369746f72792d63326233612d31222c227265766965775f726571756972656d656e745f726566223a227265766965772d63326233612d31222c22736166655f70726f6a656374696f6e5f646967657374223a2231613464653930343961353439623536373161653163303662323831656563393939393335393934306138623631386165663766663762343865343363656162222c22736368656d615f6964223a22676f7665726e65642d657865637574696f6e2e6e77702d646576656c6f706d656e742d776f726b2d737065632d736166652d70726f6a656374696f6e2e7631222c2276616c69646174696f6e5f726571756972656d656e745f726566223a2276616c69646174696f6e2d63326233612d31222c22776f726b5f6974656d5f726566223a22776f726b2d6974656d2d63326233612d31222c22776f726b5f6974656d5f7265766973696f6e5f726566223a22776f726b2d6974656d2d7265766973696f6e2d63326233612d31222c22776f726b5f737065635f646967657374223a2232393532633962303332353762343364363939383366616165626565383961356538383466373161356239646465366165623736393532323463643233643963222c22776f726b5f737065635f726566223a22776f726b2d737065632d63326233612d31227d7d',
 'command_digest': 'f2e9b97cc6bc70b24b75925f534d375edec3ad51382a966e2c95930eb8a5c5c8',
 'persisted_rows': {'program_head': {'schema_id': 'governed-execution.nwp-development-program-head.v1',
                                     'program_ref': 'program-c2b3a-1',
                                     'current_program_version_ref': 'program-version-c2b3a-1',
                                     'current_program_version_number': 1,
                                     'head_revision': 0,
                                     'program_state': 'active',
                                     'updated_at': '2026-08-21T12:34:56Z',
                                     'head_digest': '79b933902d113c5dda9c054b56cb105a8f9ed25513eaf91656c72efe53ee7058'},
                    'accepted_intent_revision': {'schema_id': 'governed-execution.nwp-development-accepted-intent-revision.v1',
                                                 'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                 'program_ref': 'program-c2b3a-1',
                                                 'accepted_intent_revision_number': 1,
                                                 'prior_accepted_intent_revision_ref': None,
                                                 'source_intent_ref': 'source-intent-c2b3a-1',
                                                 'source_intent_digest': '1111111111111111111111111111111111111111111111111111111111111111',
                                                 'safe_projection_digest': '8e76f55695e0f3bda1af480bb00fbd4bcff4c6c0270d80c65ffbe61f67c92ce1',
                                                 'created_at': '2026-08-21T12:34:56Z',
                                                 'accepted_intent_revision_digest': '4f903ee159a9ee9ac8bb1ce0803ed4d899e73a16da6a8dd84621ccd30bfd60ab'},
                    'work_item_head': {'schema_id': 'governed-execution.nwp-development-work-item-head.v1',
                                       'work_item_ref': 'work-item-c2b3a-1',
                                       'program_ref': 'program-c2b3a-1',
                                       'current_work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                       'current_work_item_revision_number': 1,
                                       'head_revision': 0,
                                       'work_state': 'planned',
                                       'updated_at': '2026-08-21T12:34:56Z',
                                       'head_digest': '67acca455028e770d816c509ac1c6936cf69a7ec582da412941df2b7f0986405'},
                    'work_item_revision': {'schema_id': 'governed-execution.nwp-development-work-item-revision.v1',
                                           'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                           'program_ref': 'program-c2b3a-1',
                                           'work_item_ref': 'work-item-c2b3a-1',
                                           'work_item_revision_number': 1,
                                           'work_item_revision_kind': 'initial',
                                           'prior_work_item_revision_ref': None,
                                           'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                           'created_at': '2026-08-21T12:34:56Z',
                                           'work_item_revision_digest': '23d7354b797a03faf0bdaee2bce03752258443cc9e232a26c47a0e8a7069a215'},
                    'initialize_decision': {'schema_id': 'governed-execution.nwp-development-decision.v1',
                                            'mutation_ref': 'mutation-c2b3a-1',
                                            'decision_ref': 'decision-c2b3a-1',
                                            'program_ref': 'program-c2b3a-1',
                                            'decision_kind': 'initialize',
                                            'decision_variant': 'program_genesis',
                                            'basis_decision_ref': None,
                                            'basis_program_version_ref': None,
                                            'basis_program_version_number': None,
                                            'expected_program_head_revision': 0,
                                            'resulting_program_version_ref': 'program-version-c2b3a-1',
                                            'resulting_program_version_number': 1,
                                            'selected_semantic_attempt_ref': None,
                                            'selected_candidate_ref': None,
                                            'selected_attempt_fence_ref': None,
                                            'selected_attempt_fence_digest': None,
                                            'target_effect_intent_ref': None,
                                            'target_effect_class': None,
                                            'target_effect_fence_ref': None,
                                            'target_effect_fence_digest': None,
                                            'expected_target_effect_head_revision': None,
                                            'target_delivery_attempt_ref': None,
                                            'originating_command_ref': None,
                                            'originating_command_digest': None,
                                            'target_capsule_manifest_ref': None,
                                            'target_portable_capsule_digest': None,
                                            'coding_global_stop_ref': 'coding-global-stop-c2b3a-1',
                                            'coding_global_stop_version': 0,
                                            'source_directive_ref': None,
                                            'source_directive_digest': None,
                                            'source_evidence_ref': None,
                                            'source_evidence_digest': None,
                                            'preassigned_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                            'preassigned_candidate_ref': 'candidate-c2b3a-1',
                                            'preassigned_effect_intent_ref': None,
                                            'preassigned_effect_fence_ref': None,
                                            'preassigned_delivery_attempt_ref': None,
                                            'resulting_accepted_intent_revision_ref': None,
                                            'resulting_work_item_ref': None,
                                            'resulting_work_item_revision_ref': None,
                                            'reason_code': 'program_genesis',
                                            'decided_at': '2026-08-21T12:34:56Z',
                                            'decision_digest': 'e743c359aea93d7931250552b62bc741d84c490f9ebb68e071c8616cc5fb4b96'},
                    'program_version': {'schema_id': 'governed-execution.nwp-development-program-version.v1',
                                        'program_version_ref': 'program-version-c2b3a-1',
                                        'program_ref': 'program-c2b3a-1',
                                        'program_version_number': 1,
                                        'program_version_kind': 'initial',
                                        'creating_decision_ref': 'decision-c2b3a-1',
                                        'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                        'created_at': '2026-08-21T12:34:56Z',
                                        'program_version_digest': 'f06037aaa718343f8676ec00d5b26b2be6fd7ab58683292f6fbe4b461b8374b9'},
                    'program_version_work_item': {'schema_id': 'governed-execution.nwp-development-program-version-work-item.v1',
                                                  'program_ref': 'program-c2b3a-1',
                                                  'program_version_ref': 'program-version-c2b3a-1',
                                                  'work_item_ref': 'work-item-c2b3a-1',
                                                  'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                  'membership_ordinal': 0,
                                                  'created_at': '2026-08-21T12:34:56Z',
                                                  'membership_digest': 'e2dc7953947fe1bf8ea643b9398c1b18278a18dd27d5fb7e3ca7663e4d8b3fb9'},
                    'work_spec_binding': {'schema_id': 'governed-execution.nwp-development-work-spec-binding.v1',
                                          'work_spec_ref': 'work-spec-c2b3a-1',
                                          'program_ref': 'program-c2b3a-1',
                                          'program_version_ref': 'program-version-c2b3a-1',
                                          'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                          'work_item_ref': 'work-item-c2b3a-1',
                                          'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                          'repository_ref': 'repository-c2b3a-1',
                                          'base_git_object_format': 'sha1',
                                          'base_git_oid': '2222222222222222222222222222222222222222',
                                          'authorized_paths_json': '[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"]',
                                          'validation_requirement_ref': 'validation-c2b3a-1',
                                          'review_requirement_ref': 'review-c2b3a-1',
                                          'privacy_classification': 'private_work_spec',
                                          'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                          'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab',
                                          'recorded_at': '2026-08-21T12:34:56Z',
                                          'work_spec_binding_digest': 'ada4d473f82b01649e66c82a13e7732a257247d032cd9d7ca8d5be03a7cb3afa'},
                    'mutation_receipt': {'schema_id': 'governed-execution.nwp-development-mutation-receipt.v1',
                                         'mutation_ref': 'mutation-c2b3a-1',
                                         'mutation_family': 'initialize_development_program',
                                         'command_schema_id': 'governed-execution.nwp-initialize-development-program-command.v1',
                                         'command_digest': 'f2e9b97cc6bc70b24b75925f534d375edec3ad51382a966e2c95930eb8a5c5c8',
                                         'program_ref': 'program-c2b3a-1',
                                         'decision_ref': 'decision-c2b3a-1',
                                         'result_program_version_ref': 'program-version-c2b3a-1',
                                         'result_semantic_attempt_ref': None,
                                         'result_effect_intent_ref': None,
                                         'result_effect_fence_ref': None,
                                         'result_delivery_attempt_ref': None,
                                         'result_observation_ref': None,
                                         'result_decision_ref': 'decision-c2b3a-1',
                                         'result_class': 'development_program_initialized',
                                         'result_projection_digest': '7844ff36f20e1c6fe7fc3d687ac96d5162fc3a1f723c87512ace84d241451d76',
                                         'mutation_graph_digest': '150699722ad8e573a56b4673fbd1e41434d894757f48bb83e4826f474b1511ee',
                                         'outcome': 'committed',
                                         'committed_at': '2026-08-21T12:34:56Z'}},
 'historical_postimages': {'program_head': {'schema_id': 'governed-execution.nwp-development-program-head.v1',
                                            'program_ref': 'program-c2b3a-1',
                                            'current_program_version_ref': 'program-version-c2b3a-1',
                                            'current_program_version_number': 1,
                                            'head_revision': 0,
                                            'program_state': 'active',
                                            'updated_at': '2026-08-21T12:34:56Z',
                                            'head_digest': '79b933902d113c5dda9c054b56cb105a8f9ed25513eaf91656c72efe53ee7058'},
                           'work_item_head': {'schema_id': 'governed-execution.nwp-development-work-item-head.v1',
                                              'work_item_ref': 'work-item-c2b3a-1',
                                              'program_ref': 'program-c2b3a-1',
                                              'current_work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                              'current_work_item_revision_number': 1,
                                              'head_revision': 0,
                                              'work_state': 'planned',
                                              'updated_at': '2026-08-21T12:34:56Z',
                                              'head_digest': '67acca455028e770d816c509ac1c6936cf69a7ec582da412941df2b7f0986405'}},
 'graph_entries': ({'rank': 0,
                    'role': 'program_head_postimage',
                    'ordinal': 0,
                    'record_ref': 'program-c2b3a-1',
                    'record_digest': '79b933902d113c5dda9c054b56cb105a8f9ed25513eaf91656c72efe53ee7058'},
                   {'rank': 1,
                    'role': 'accepted_intent_revision',
                    'ordinal': 0,
                    'record_ref': 'accepted-intent-c2b3a-1',
                    'record_digest': '4f903ee159a9ee9ac8bb1ce0803ed4d899e73a16da6a8dd84621ccd30bfd60ab'},
                   {'rank': 2,
                    'role': 'initialize_decision',
                    'ordinal': 0,
                    'record_ref': 'decision-c2b3a-1',
                    'record_digest': 'e743c359aea93d7931250552b62bc741d84c490f9ebb68e071c8616cc5fb4b96'},
                   {'rank': 3,
                    'role': 'program_version',
                    'ordinal': 0,
                    'record_ref': 'program-version-c2b3a-1',
                    'record_digest': 'f06037aaa718343f8676ec00d5b26b2be6fd7ab58683292f6fbe4b461b8374b9'},
                   {'rank': 4,
                    'role': 'work_item_head_postimage',
                    'ordinal': 0,
                    'record_ref': 'work-item-c2b3a-1',
                    'record_digest': '67acca455028e770d816c509ac1c6936cf69a7ec582da412941df2b7f0986405'},
                   {'rank': 5,
                    'role': 'work_item_revision',
                    'ordinal': 0,
                    'record_ref': 'work-item-revision-c2b3a-1',
                    'record_digest': '23d7354b797a03faf0bdaee2bce03752258443cc9e232a26c47a0e8a7069a215'},
                   {'rank': 6,
                    'role': 'program_version_work_item',
                    'ordinal': 0,
                    'record_ref': 'work-item-c2b3a-1',
                    'record_digest': 'e2dc7953947fe1bf8ea643b9398c1b18278a18dd27d5fb7e3ca7663e4d8b3fb9'},
                   {'rank': 7,
                    'role': 'work_spec_binding',
                    'ordinal': 0,
                    'record_ref': 'work-spec-c2b3a-1',
                    'record_digest': 'ada4d473f82b01649e66c82a13e7732a257247d032cd9d7ca8d5be03a7cb3afa'}),
 'result_projection': {'schema_id': 'governed-execution.nwp-initialize-development-program-result.v1',
                       'program_ref': 'program-c2b3a-1',
                       'decision_ref': 'decision-c2b3a-1',
                       'result_program_version_ref': 'program-version-c2b3a-1',
                       'result_decision_ref': 'decision-c2b3a-1'},
 'result_projection_digest': '7844ff36f20e1c6fe7fc3d687ac96d5162fc3a1f723c87512ace84d241451d76',
 'mutation_graph_digest': '150699722ad8e573a56b4673fbd1e41434d894757f48bb83e4826f474b1511ee',
 'mutation_receipt': {'schema_id': 'governed-execution.nwp-development-mutation-receipt.v1',
                      'mutation_ref': 'mutation-c2b3a-1',
                      'mutation_family': 'initialize_development_program',
                      'command_schema_id': 'governed-execution.nwp-initialize-development-program-command.v1',
                      'command_digest': 'f2e9b97cc6bc70b24b75925f534d375edec3ad51382a966e2c95930eb8a5c5c8',
                      'program_ref': 'program-c2b3a-1',
                      'decision_ref': 'decision-c2b3a-1',
                      'result_program_version_ref': 'program-version-c2b3a-1',
                      'result_semantic_attempt_ref': None,
                      'result_effect_intent_ref': None,
                      'result_effect_fence_ref': None,
                      'result_delivery_attempt_ref': None,
                      'result_observation_ref': None,
                      'result_decision_ref': 'decision-c2b3a-1',
                      'result_class': 'development_program_initialized',
                      'result_projection_digest': '7844ff36f20e1c6fe7fc3d687ac96d5162fc3a1f723c87512ace84d241451d76',
                      'mutation_graph_digest': '150699722ad8e573a56b4673fbd1e41434d894757f48bb83e4826f474b1511ee',
                      'outcome': 'committed',
                      'committed_at': '2026-08-21T12:34:56Z'},
 'private_committed_result': {'disposition': 'committed',
                              'mutation_ref': 'mutation-c2b3a-1',
                              'command_digest': 'f2e9b97cc6bc70b24b75925f534d375edec3ad51382a966e2c95930eb8a5c5c8',
                              'program_ref': 'program-c2b3a-1',
                              'program_version_ref': 'program-version-c2b3a-1',
                              'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                              'decision_ref': 'decision-c2b3a-1',
                              'work_item_ref': 'work-item-c2b3a-1',
                              'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                              'work_spec_ref': 'work-spec-c2b3a-1',
                              'preassigned_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                              'preassigned_candidate_ref': 'candidate-c2b3a-1',
                              'transaction_timestamp': '2026-08-21T12:34:56Z'},
 'private_exact_replay_result': {'disposition': 'exact_replay',
                                 'mutation_ref': 'mutation-c2b3a-1',
                                 'command_digest': 'f2e9b97cc6bc70b24b75925f534d375edec3ad51382a966e2c95930eb8a5c5c8',
                                 'program_ref': 'program-c2b3a-1',
                                 'program_version_ref': 'program-version-c2b3a-1',
                                 'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                 'decision_ref': 'decision-c2b3a-1',
                                 'work_item_ref': 'work-item-c2b3a-1',
                                 'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                 'work_spec_ref': 'work-spec-c2b3a-1',
                                 'preassigned_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                 'preassigned_candidate_ref': 'candidate-c2b3a-1',
                                 'transaction_timestamp': '2026-08-21T12:34:56Z'}}


EXPECTED_PROCESS_CONTROL_REFERENCE_CASES = {'cross-k-s': ('distinct_instance', 'KeyboardInterrupt', ('cross-k-s',), 'not_applicable', ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 1, 1, True, True, None, None, None, None, None, False, False),
 'cross-k-g': ('distinct_instance', 'KeyboardInterrupt', ('cross-k-g',), 'not_applicable', ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 1, 1, True, True, None, None, None, None, None, False, False),
 'cross-s-k': ('distinct_instance', 'SystemExit', (32,), 32, ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 1, 1, True, True, None, None, None, None, None, False, False),
 'cross-s-g': ('distinct_instance', 'SystemExit', (33,), 33, ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 1, 1, True, True, None, None, None, None, None, False, False),
 'cross-g-k': ('distinct_instance', 'GeneratorExit', ('cross-g-k',), 'not_applicable', ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 1, 1, True, True, None, None, None, None, None, False, False),
 'cross-g-s': ('distinct_instance', 'GeneratorExit', ('cross-g-s',), 'not_applicable', ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 1, 1, True, True, None, None, None, None, None, False, False),
 'distinct-k': ('distinct_instance', 'KeyboardInterrupt', ('same-class-k-1',), 'not_applicable', ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 1, 1, True, True, None, None, None, None, None, False, False),
 'distinct-s': ('distinct_instance', 'SystemExit', (35,), 35, ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 1, 1, True, True, None, None, None, None, None, False, False),
 'distinct-g': ('distinct_instance', 'GeneratorExit', ('same-class-g-1',), 'not_applicable', ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 1, 1, True, True, None, None, None, None, None, False, False),
 'same-k': ('same_instance', 'KeyboardInterrupt', ('same-instance-k',), 'not_applicable', ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 1, 1, True, True, None, None, None, None, None, False, False),
 'same-s': ('same_instance', 'SystemExit', (37,), 37, ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 1, 1, True, True, None, None, None, None, None, False, False),
 'same-g': ('same_instance', 'GeneratorExit', ('same-instance-g',), 'not_applicable', ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 1, 1, True, True, None, None, None, None, None, False, False),
 'prelinked-cause': ('distinct_instance', 'SystemExit', (38,), 38, ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 2, 1, True, True, None, 'GeneratorExit', None, None, None, False, False),
 'prelinked-context': ('distinct_instance', 'GeneratorExit', ('context-primary',), 'not_applicable', ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 2, 1, True, True, None, None, 'KeyboardInterrupt', None, None, False, False),
 'linked-cycle': ('distinct_instance', 'SystemExit', (39,), 39, ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 2, 3, True, True, None, 'KeyboardInterrupt', None, None, 'KeyboardInterrupt', False, False),
 'private-payload': ('distinct_instance', 'SystemExit', (('opaque-synthetic-payload', 40),), ('opaque-synthetic-payload', 40), ('raise-primary', 'raise-secondary', 'bare-reraise-primary'), ('catch-primary', 'catch-secondary', 'bare-reraise-primary'), 2, 2, True, True, (('opaque-synthetic-payload', 40),), 'GeneratorExit', None, None, 'KeyboardInterrupt', False, False)}


CLEANUP_SAFE_PROJECTION_FIELDS = (
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


CLEANUP_REFERENCE_INPUT_CASES = (('normal-a', ('A', None, None, 'normal', 'normal', 'normal', False, 'normal', 'none')), ('normal-qu', ('QU', None, None, 'normal', 'normal', 'normal', False, 'normal', 'none')), ('normal-qk', ('QK', None, None, 'normal', 'normal', 'normal', False, 'normal', 'none')), ('normal-pu', ('PU', None, None, 'normal', 'normal', 'normal', False, 'normal', 'none')),
 ('normal-pk', ('PK', None, None, 'normal', 'normal', 'normal', False, 'normal', 'none')), ('p0-before', ('A', 'P0', 'before', 'normal', 'normal', 'normal', False, 'ordinary', 'none')), ('p0-after', ('A', 'P0', 'after', 'normal', 'normal', 'normal', False, 'KeyboardInterrupt', 'none')), ('c1-before', ('QU', 'C1', 'before', 'normal', 'normal', 'normal', False, 'SystemExit', 'none')),
 ('c1-after', ('QU', 'C1', 'after', 'normal', 'normal', 'normal', False, 'GeneratorExit', 'none')), ('c2-before', ('QU', 'C2', 'before', 'normal', 'normal', 'normal', False, 'normal', 'none')), ('c2-after', ('QU', 'C2', 'after', 'normal', 'normal', 'normal', False, 'ordinary', 'none')), ('r1-before', ('PU', 'R1', 'before', 'normal', 'normal', 'normal', False, 'KeyboardInterrupt', 'none')),
 ('r1-after', ('PU', 'R1', 'after', 'normal', 'normal', 'normal', False, 'SystemExit', 'none')), ('r2-before', ('PU', 'R2', 'before', 'normal', 'normal', 'normal', False, 'GeneratorExit', 'none')), ('r2-after', ('PU', 'R2', 'after', 'normal', 'normal', 'normal', False, 'normal', 'none')), ('r3-before', ('PU', 'R3', 'before', 'normal', 'normal', 'normal', False, 'ordinary', 'none')),
 ('r3-after', ('PU', 'R3', 'after', 'normal', 'normal', 'normal', False, 'KeyboardInterrupt', 'none')), ('l1-before', ('PU', 'L1', 'before', 'normal', 'normal', 'normal', False, 'SystemExit', 'none')), ('l1-after', ('PU', 'L1', 'after', 'normal', 'normal', 'normal', False, 'GeneratorExit', 'none')), ('h1-before', ('PU', 'H1', 'before', 'normal', 'normal', 'normal', False, 'normal', 'none')),
 ('h1-after', ('PU', 'H1', 'after', 'normal', 'normal', 'normal', False, 'ordinary', 'none')), ('h2-before', ('PU', 'H2', 'before', 'normal', 'normal', 'normal', False, 'KeyboardInterrupt', 'none')), ('h2-between', ('PU', 'H2', 'between', 'normal', 'normal', 'normal', False, 'GeneratorExit', 'none')), ('h2-after', ('PU', 'H2', 'after', 'normal', 'normal', 'normal', False, 'SystemExit', 'none')),
 ('t1-before', ('PU', 'T1', 'before', 'normal', 'normal', 'normal', False, 'GeneratorExit', 'none')), ('t1-after', ('PU', 'T1', 'after', 'normal', 'normal', 'normal', False, 'normal', 'none')), ('h3-before', ('PU', 'H3', 'before', 'normal', 'normal', 'normal', False, 'ordinary', 'none')), ('h3-after', ('PU', 'H3', 'after', 'normal', 'normal', 'normal', False, 'KeyboardInterrupt', 'none')),
 ('primary-pu-k', ('PU', None, None, 'normal', 'normal', 'normal', False, 'normal', 'KeyboardInterrupt')), ('primary-pu-s', ('PU', None, None, 'normal', 'normal', 'normal', False, 'normal', 'SystemExit')), ('primary-pu-g', ('PU', None, None, 'normal', 'normal', 'normal', False, 'normal', 'GeneratorExit')),
 ('primary-pk-k', ('PK', None, None, 'normal', 'normal', 'normal', False, 'normal', 'KeyboardInterrupt')), ('primary-pk-s', ('PK', None, None, 'normal', 'normal', 'normal', False, 'normal', 'SystemExit')), ('primary-pk-g', ('PK', None, None, 'normal', 'normal', 'normal', False, 'normal', 'GeneratorExit')),
 ('precedence-pu-k-s', ('PU', 'R1', 'before', 'normal', 'normal', 'normal', False, 'SystemExit', 'KeyboardInterrupt')), ('precedence-pu-s-g', ('PU', 'R2', 'before', 'normal', 'normal', 'normal', False, 'GeneratorExit', 'SystemExit')), ('precedence-pu-g-k', ('PU', 'R3', 'before', 'normal', 'normal', 'normal', False, 'KeyboardInterrupt', 'GeneratorExit')),
 ('precedence-pk-k-g', ('PK', 'L1', 'before', 'normal', 'normal', 'normal', False, 'GeneratorExit', 'KeyboardInterrupt')), ('precedence-pk-s-k', ('PK', 'H1', 'before', 'normal', 'normal', 'normal', False, 'KeyboardInterrupt', 'SystemExit')), ('precedence-pk-g-s', ('PK', 'H2', 'before', 'normal', 'normal', 'normal', False, 'SystemExit', 'GeneratorExit')),
 ('finalizer-cleanup-k', ('PU', 'R1', 'before', 'normal', 'normal', 'normal', True, 'KeyboardInterrupt', 'none')), ('finalizer-cleanup-s', ('PU', 'R2', 'before', 'normal', 'normal', 'normal', True, 'SystemExit', 'none')), ('finalizer-cleanup-g', ('PU', 'R3', 'before', 'normal', 'normal', 'normal', True, 'GeneratorExit', 'none')),
 ('finalizer-primary-k', ('PU', None, None, 'normal', 'normal', 'normal', True, 'normal', 'KeyboardInterrupt')), ('finalizer-primary-s', ('PU', None, None, 'normal', 'normal', 'normal', True, 'normal', 'SystemExit')), ('finalizer-primary-g', ('PU', None, None, 'normal', 'normal', 'normal', True, 'normal', 'GeneratorExit')),
 ('close-qu-ordinary', ('QU', None, None, 'ordinary', 'normal', 'normal', False, 'normal', 'none')), ('close-qu-k', ('QU', None, None, 'KeyboardInterrupt', 'normal', 'normal', False, 'normal', 'none')), ('close-qk-s', ('QK', None, None, 'SystemExit', 'normal', 'normal', False, 'normal', 'none')), ('close-qk-g', ('QK', None, None, 'GeneratorExit', 'normal', 'normal', False, 'normal', 'none')),
 ('close-qu-g-primary-k', ('QU', None, None, 'GeneratorExit', 'normal', 'normal', False, 'normal', 'KeyboardInterrupt')), ('close-qk-k-primary-s', ('QK', None, None, 'KeyboardInterrupt', 'normal', 'normal', False, 'normal', 'SystemExit')), ('unlock-unproved', ('PU', None, None, 'normal', 'unproved', 'normal', False, 'ordinary', 'none')),
 ('unlock-retry-normal', ('PU', None, None, 'normal', 'retry_normal', 'normal', False, 'normal', 'none')), ('descriptor-unknown', ('PK', None, None, 'normal', 'normal', 'unknown', False, 'normal', 'none')))

EXPECTED_CLEANUP_REFERENCE_CASES = {'normal-a': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, False, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 1, 1, False, True, 'normal', 'none', False, True, True, True, True),
 'normal-qu': ('X', ('P0', 'C1', 'C2', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'C1', 'C2', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 1, 1, 1, False, True, 'normal', 'none', False, True, True, True, True),
 'normal-qk': ('X', ('P0', 'C1', 'C2', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'C1', 'C2', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 1, 1, 1, False, True, 'normal', 'none', False, True, True, True, True),
 'normal-pu': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 1, 1, False, True, 'normal', 'none', False, True, True, True, True),
 'normal-pk': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 1, 1, False, True, 'normal', 'none', False, True, True, True, True),
 'p0-before': ('A', ('P0',), (), True, True, False, False, False, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'ordinary', 'none', True, False, False, False, False),
 'p0-after': ('A-closing', ('P0',), ('P0',), False, True, True, False, False, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'KeyboardInterrupt', 'cleanup_KeyboardInterrupt', False, False, False, False, False),
 'c1-before': ('QU', ('P0', 'C1'), ('P0',), False, True, False, True, False, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'SystemExit', 'cleanup_SystemExit', False, False, False, False, False),
 'c1-after': ('PU', ('P0', 'C1', 'C2'), ('P0', 'C1', 'C2'), False, True, False, False, True, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 1, 0, 0, False, True, 'GeneratorExit', 'cleanup_GeneratorExit', False, False, False, False, False),
 'c2-before': ('PU', ('P0', 'C1', 'C2'), ('P0', 'C1', 'C2'), False, True, False, False, True, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 1, 0, 0, False, True, 'normal', 'none', False, False, False, False, False),
 'c2-after': ('PU', ('P0', 'C1', 'C2'), ('P0', 'C1', 'C2'), False, True, False, False, True, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 1, 0, 0, False, True, 'ordinary', 'none', True, False, False, False, False),
 'r1-before': ('PU', ('P0', 'R1'), ('P0',), False, True, False, False, True, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'KeyboardInterrupt', 'cleanup_KeyboardInterrupt', False, False, False, False, False),
 'r1-after': ('PU', ('P0', 'R1'), ('P0', 'R1'), False, True, False, False, True, False, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'SystemExit', 'cleanup_SystemExit', False, False, False, False, False),
 'r2-before': ('PU', ('P0', 'R1', 'R2'), ('P0', 'R1'), False, True, False, False, True, False, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'GeneratorExit', 'cleanup_GeneratorExit', False, False, False, False, False),
 'r2-after': ('PU', ('P0', 'R1', 'R2'), ('P0', 'R1', 'R2'), False, True, False, False, True, False, False, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'normal', 'none', False, False, False, False, False),
 'r3-before': ('PU', ('P0', 'R1', 'R2', 'R3'), ('P0', 'R1', 'R2'), False, True, False, False, True, False, False, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'ordinary', 'none', True, False, False, False, False),
 'r3-after': ('PU', ('P0', 'R1', 'R2', 'R3'), ('P0', 'R1', 'R2', 'R3'), False, True, False, False, True, False, False, False, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'KeyboardInterrupt', 'cleanup_KeyboardInterrupt', False, False, False, False, False),
 'l1-before': ('PU', ('P0', 'R1', 'R2', 'R3', 'L1'), ('P0', 'R1', 'R2', 'R3'), False, True, False, False, True, False, False, False, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'SystemExit', 'cleanup_SystemExit', False, False, False, False, False),
 'l1-after': ('PU', ('P0', 'R1', 'R2', 'R3', 'L1'), ('P0', 'R1', 'R2', 'R3', 'L1'), False, True, False, False, True, False, False, False, 'release_proved', 'not_attempted', True, True, False, True, True, 0, 1, 0, False, True, 'GeneratorExit', 'cleanup_GeneratorExit', False, False, False, False, False),
 'h1-before': ('PU', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1'), ('P0', 'R1', 'R2', 'R3', 'L1'), False, True, False, False, True, False, False, False, 'release_proved', 'not_attempted', True, True, False, True, True, 0, 1, 0, False, True, 'normal', 'none', False, False, False, False, False),
 'h1-after': ('PU', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, False, True, True, 0, 1, 1, False, True, 'ordinary', 'none', True, False, False, False, False),
 'h2-before': ('PU', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, False, True, True, 0, 1, 1, False, True, 'KeyboardInterrupt', 'cleanup_KeyboardInterrupt', False, False, False, False, False),
 'h2-between': ('PU', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, True, True, 0, 1, 1, False, True, 'GeneratorExit', 'cleanup_GeneratorExit', False, False, False, False, False),
 'h2-after': ('PU', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, True, 0, 1, 1, False, True, 'SystemExit', 'cleanup_SystemExit', False, False, False, False, False),
 't1-before': ('PU', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, True, 0, 1, 1, False, True, 'GeneratorExit', 'cleanup_GeneratorExit', False, False, False, False, False),
 't1-after': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, True, 0, 1, 1, False, True, 'normal', 'none', False, True, True, True, True),
 'h3-before': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, True, 0, 1, 1, False, True, 'ordinary', 'none', True, True, True, True, True),
 'h3-after': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 1, 1, False, True, 'KeyboardInterrupt', 'cleanup_KeyboardInterrupt', False, True, True, True, True),
 'primary-pu-k': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 1, 1, False, True, 'normal', 'commit_KeyboardInterrupt', False, True, True, True, True),
 'primary-pu-s': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 1, 1, False, True, 'normal', 'commit_SystemExit', False, True, True, True, True),
 'primary-pu-g': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 1, 1, False, True, 'normal', 'commit_GeneratorExit', False, True, True, True, True),
 'primary-pk-k': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 1, 1, False, True, 'normal', 'commit_KeyboardInterrupt', False, True, True, True, True),
 'primary-pk-s': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 1, 1, False, True, 'normal', 'commit_SystemExit', False, True, True, True, True),
 'primary-pk-g': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 1, 1, False, True, 'normal', 'commit_GeneratorExit', False, True, True, True, True),
 'precedence-pu-k-s': ('PU', ('P0', 'R1'), ('P0',), False, True, False, False, True, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'SystemExit', 'commit_KeyboardInterrupt', True, False, False, False, False),
 'precedence-pu-s-g': ('PU', ('P0', 'R1', 'R2'), ('P0', 'R1'), False, True, False, False, True, False, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'GeneratorExit', 'commit_SystemExit', True, False, False, False, False),
 'precedence-pu-g-k': ('PU', ('P0', 'R1', 'R2', 'R3'), ('P0', 'R1', 'R2'), False, True, False, False, True, False, False, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'KeyboardInterrupt', 'commit_GeneratorExit', True, False, False, False, False),
 'precedence-pk-k-g': ('PK', ('P0', 'R1', 'R2', 'R3', 'L1'), ('P0', 'R1', 'R2', 'R3'), False, True, False, False, True, False, False, False, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, False, True, 'GeneratorExit', 'commit_KeyboardInterrupt', True, False, False, False, False),
 'precedence-pk-s-k': ('PK', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1'), ('P0', 'R1', 'R2', 'R3', 'L1'), False, True, False, False, True, False, False, False, 'release_proved', 'not_attempted', True, True, False, True, True, 0, 1, 0, False, True, 'KeyboardInterrupt', 'commit_SystemExit', True, False, False, False, False),
 'precedence-pk-g-s': ('PK', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, False, True, True, 0, 1, 1, False, True, 'SystemExit', 'commit_GeneratorExit', True, False, False, False, False),
 'finalizer-cleanup-k': ('PU', ('P0', 'R1'), ('P0',), False, False, False, False, True, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, True, False, 'KeyboardInterrupt', 'none', True, False, False, False, False),
 'finalizer-cleanup-s': ('PU', ('P0', 'R1', 'R2'), ('P0', 'R1'), False, False, False, False, True, False, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, True, False, 'SystemExit', 'none', True, False, False, False, False),
 'finalizer-cleanup-g': ('PU', ('P0', 'R1', 'R2', 'R3'), ('P0', 'R1', 'R2'), False, False, False, False, True, False, False, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 0, 0, 0, True, False, 'GeneratorExit', 'none', True, False, False, False, False),
 'finalizer-primary-k': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, False, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 1, 1, True, False, 'normal', 'none', False, True, True, True, True),
 'finalizer-primary-s': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, False, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 1, 1, True, False, 'normal', 'none', False, True, True, True, True),
 'finalizer-primary-g': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, False, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 1, 1, True, False, 'normal', 'none', False, True, True, True, True),
 'close-qu-ordinary': ('QU', ('P0', 'C1'), ('P0',), False, True, False, True, False, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 1, 0, 0, False, True, 'ordinary', 'none', True, False, False, False, False),
 'close-qu-k': ('QU', ('P0', 'C1'), ('P0',), False, True, False, True, False, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 1, 0, 0, False, True, 'KeyboardInterrupt', 'cleanup_KeyboardInterrupt', False, False, False, False, False),
 'close-qk-s': ('QK', ('P0', 'C1'), ('P0',), False, True, False, True, False, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 1, 0, 0, False, True, 'SystemExit', 'cleanup_SystemExit', False, False, False, False, False),
 'close-qk-g': ('QK', ('P0', 'C1'), ('P0',), False, True, False, True, False, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 1, 0, 0, False, True, 'GeneratorExit', 'cleanup_GeneratorExit', False, False, False, False, False),
 'close-qu-g-primary-k': ('QU', ('P0', 'C1'), ('P0',), False, True, False, True, False, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 1, 0, 0, False, True, 'GeneratorExit', 'commit_KeyboardInterrupt', True, False, False, False, False),
 'close-qk-k-primary-s': ('QK', ('P0', 'C1'), ('P0',), False, True, False, True, False, True, True, True, 'not_attempted', 'not_attempted', True, True, False, True, True, 1, 0, 0, False, True, 'KeyboardInterrupt', 'commit_SystemExit', True, False, False, False, False),
 'unlock-unproved': ('PU', ('P0', 'R1', 'R2', 'R3', 'L1'), ('P0', 'R1', 'R2', 'R3'), False, True, False, False, True, False, False, False, 'release_unproved', 'not_attempted', True, True, False, True, True, 0, 1, 0, False, True, 'ordinary', 'none', True, False, False, False, False),
 'unlock-retry-normal': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, True, False, False, False, 'release_proved', 'reclaimed', False, False, True, False, False, 0, 2, 1, False, True, 'normal', 'none', False, True, True, True, True),
 'descriptor-unknown': ('X', ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), ('P0', 'R1', 'R2', 'R3', 'L1', 'H1', 'H2', 'T1', 'H3'), False, True, False, False, True, False, False, False, 'release_proved', 'reclamation_unknown', False, False, True, False, False, 0, 1, 1, False, True, 'normal', 'none', False, True, True, True, True)}


class _ContractViolation(Exception):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise _ContractViolation(code)


def _read_allowed_text(path: Path) -> str:
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        raise _ContractViolation("C2B3A_ORACLE_FORBIDDEN_INPUT") from None
    requested = relative.as_posix()
    _require(
        requested in ALLOWED_ORACLE_RELATIVE_PATHS,
        "C2B3A_ORACLE_FORBIDDEN_INPUT",
    )
    expected_path = ROOT / requested
    _require(path == expected_path, "C2B3A_ORACLE_FORBIDDEN_INPUT")
    _require(not expected_path.is_symlink(), "C2B3A_ORACLE_FORBIDDEN_INPUT")
    try:
        resolved = expected_path.resolve(strict=True)
    except (OSError, RuntimeError):
        raise _ContractViolation("C2B3A_ORACLE_FORBIDDEN_INPUT") from None
    _require(resolved == expected_path, "C2B3A_ORACLE_FORBIDDEN_INPUT")
    return resolved.read_text(encoding="utf-8")


def _owner_contract(text: str | None = None) -> dict[str, object]:
    source = _read_allowed_text(OWNER_PATH) if text is None else text
    _require(type(source) is str, "C2B3A_OWNER_LITERAL_INVALID")
    _require(source.count(BEGIN_MARKER) == 1, "C2B3A_OWNER_MARKER_INVALID")
    _require(source.count(END_MARKER) == 1, "C2B3A_OWNER_MARKER_INVALID")
    before, remainder = source.split(BEGIN_MARKER, 1)
    payload, after = remainder.split(END_MARKER, 1)
    _require(before.endswith("\n"), "C2B3A_OWNER_MARKER_INVALID")
    _require(after.startswith("\n"), "C2B3A_OWNER_MARKER_INVALID")
    stripped_payload = payload.strip()
    lines = stripped_payload.splitlines()
    _require(len(lines) >= 3, "C2B3A_OWNER_LITERAL_INVALID")
    _require(lines[0] == "```python", "C2B3A_OWNER_FENCE_INVALID")
    _require(lines[-1] == "```", "C2B3A_OWNER_FENCE_INVALID")
    try:
        newline = "\n"
        value = ast.literal_eval(newline.join(lines[1:-1]))
    except (SyntaxError, ValueError):
        raise _ContractViolation("C2B3A_OWNER_LITERAL_INVALID") from None
    _require(type(value) is dict, "C2B3A_OWNER_LITERAL_INVALID")
    return value


def _owner_golden_vector(text: str | None = None) -> dict[str, object]:
    source = _read_allowed_text(OWNER_PATH) if text is None else text
    _require(type(source) is str, "C2B3A_GOLDEN_VECTOR_LITERAL_INVALID")
    _require(
        source.count(VECTOR_BEGIN_MARKER) == 1,
        "C2B3A_GOLDEN_VECTOR_MARKER_INVALID",
    )
    _require(
        source.count(VECTOR_END_MARKER) == 1,
        "C2B3A_GOLDEN_VECTOR_MARKER_INVALID",
    )
    before, remainder = source.split(VECTOR_BEGIN_MARKER, 1)
    payload, after = remainder.split(VECTOR_END_MARKER, 1)
    _require(before.endswith("\n"), "C2B3A_GOLDEN_VECTOR_MARKER_INVALID")
    _require(after.startswith("\n"), "C2B3A_GOLDEN_VECTOR_MARKER_INVALID")
    stripped_payload = payload.strip()
    lines = stripped_payload.splitlines()
    _require(len(lines) >= 3, "C2B3A_GOLDEN_VECTOR_LITERAL_INVALID")
    _require(lines[0] == "```python", "C2B3A_GOLDEN_VECTOR_FENCE_INVALID")
    _require(lines[-1] == "```", "C2B3A_GOLDEN_VECTOR_FENCE_INVALID")
    try:
        newline = "\n"
        value = ast.literal_eval(newline.join(lines[1:-1]))
    except (SyntaxError, ValueError):
        raise _ContractViolation("C2B3A_GOLDEN_VECTOR_LITERAL_INVALID") from None
    _require(type(value) is dict, "C2B3A_GOLDEN_VECTOR_LITERAL_INVALID")
    return value


def _validate_golden_vector(candidate: object) -> None:
    _require(type(candidate) is dict, "C2B3A_GOLDEN_VECTOR_INVALID")
    _require(
        candidate == EXPECTED_INITIALIZATION_GOLDEN_VECTOR,
        "C2B3A_GOLDEN_VECTOR_INVALID",
    )


def _validate_planning_status(text: object) -> None:
    _require(
        type(text) is str,
        "C2B3A_PLANNING_PROJECTION_INVALID",
    )
    _require(
        text == EXPECTED_PLANNING_PROJECTION,
        "C2B3A_PLANNING_PROJECTION_INVALID",
    )


def _validate_contract(candidate: object) -> None:
    _require(type(candidate) is dict, "C2B3A_TOP_LEVEL_INVALID")
    assert isinstance(candidate, dict)
    _require(
        tuple(candidate)
        == tuple(EXPECTED_INITIALIZATION_CONTRACT)
        + ("commit_close_outcome_addendum",),
        "C2B3A_TOP_LEVEL_INVALID",
    )
    _require(
        candidate["contract_identity"]
        == EXPECTED_INITIALIZATION_CONTRACT["contract_identity"],
        "C2B3A_CONTRACT_IDENTITY_INVALID",
    )
    _require(
        candidate["tranche_boundary"]
        == EXPECTED_INITIALIZATION_CONTRACT["tranche_boundary"],
        "C2B3A_TRANCHE_BOUNDARY_INVALID",
    )
    _require(
        candidate["five_path_scope"]
        == EXPECTED_INITIALIZATION_CONTRACT["five_path_scope"],
        "C2B3A_WRITE_SCOPE_INVALID",
    )
    _require(
        candidate["owner_decisions"]
        == EXPECTED_INITIALIZATION_CONTRACT["owner_decisions"],
        "C2B3A_OWNER_DECISIONS_INVALID",
    )
    _require(
        candidate["initialization_golden_vector"]
        == EXPECTED_INITIALIZATION_CONTRACT["initialization_golden_vector"],
        "C2B3A_GOLDEN_VECTOR_INVALID",
    )
    _require(
        candidate["semantic_ref_ownership"]
        == EXPECTED_INITIALIZATION_CONTRACT["semantic_ref_ownership"],
        "C2B3A_SEMANTIC_REFS_INVALID",
    )
    _require(
        candidate["existing_work_spec_safe_projection"]
        == EXPECTED_INITIALIZATION_CONTRACT[
            "existing_work_spec_safe_projection"
        ],
        "C2B3A_WORK_SPEC_PROJECTION_INVALID",
    )
    _require(
        candidate["accepted_intent_safe_projection"]
        == EXPECTED_INITIALIZATION_CONTRACT[
            "accepted_intent_safe_projection"
        ],
        "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID",
    )
    _require(
        candidate["sensitive_ingress"]
        == EXPECTED_INITIALIZATION_CONTRACT["sensitive_ingress"],
        "C2B3A_SENSITIVE_INGRESS_INVALID",
    )
    _require(
        candidate["safe_command"]
        == EXPECTED_INITIALIZATION_CONTRACT["safe_command"],
        "C2B3A_SAFE_COMMAND_INVALID",
    )
    _require(
        candidate["genesis_cardinality"]
        == EXPECTED_INITIALIZATION_CONTRACT["genesis_cardinality"],
        "C2B3A_GENESIS_CARDINALITY_INVALID",
    )
    _require(
        candidate["row_and_head_ledger"]
        == EXPECTED_INITIALIZATION_CONTRACT["row_and_head_ledger"],
        "C2B3A_ROW_LEDGER_INVALID",
    )
    _require(
        candidate["write_order"]
        == EXPECTED_INITIALIZATION_CONTRACT["write_order"],
        "C2B3A_WRITE_ORDER_INVALID",
    )
    _require(
        candidate["initialize_graph"]
        == EXPECTED_INITIALIZATION_CONTRACT["initialize_graph"],
        "C2B3A_GRAPH_INVALID",
    )
    _require(
        candidate["complete_graph_locator"]
        == EXPECTED_INITIALIZATION_CONTRACT["complete_graph_locator"],
        "C2B3A_LOCATOR_INVALID",
    )
    _require(
        candidate["persisted_result_projection"]
        == EXPECTED_INITIALIZATION_CONTRACT["persisted_result_projection"],
        "C2B3A_RESULT_PROJECTION_INVALID",
    )
    _require(
        candidate["private_apply_result"]
        == EXPECTED_INITIALIZATION_CONTRACT["private_apply_result"],
        "C2B3A_PRIVATE_RESULT_INVALID",
    )
    _require(
        candidate["private_outcome_ownership"]
        == EXPECTED_INITIALIZATION_CONTRACT["private_outcome_ownership"],
        "C2B3A_OUTCOME_OWNERSHIP_INVALID",
    )
    _require(
        candidate["mutation_receipt"]
        == EXPECTED_INITIALIZATION_CONTRACT["mutation_receipt"],
        "C2B3A_RECEIPT_INVALID",
    )
    _require(
        candidate["exact_replay"]
        == EXPECTED_INITIALIZATION_CONTRACT["exact_replay"],
        "C2B3A_REPLAY_INVALID",
    )
    _require(
        candidate["commit_uncertainty_cleanup_gate"]
        == EXPECTED_INITIALIZATION_CONTRACT["commit_uncertainty_cleanup_gate"],
        "C2B3A_RECOVERY_ADMISSION_INVALID",
    )
    _require(
        candidate["commit_outcome_recovery"]
        == EXPECTED_INITIALIZATION_CONTRACT["commit_outcome_recovery"],
        "C2B3A_RECOVERY_INVALID",
    )
    _require(
        candidate["conflict_precedence"]
        == EXPECTED_INITIALIZATION_CONTRACT["conflict_precedence"],
        "C2B3A_CONFLICT_PRECEDENCE_INVALID",
    )
    _require(
        candidate["privacy_and_traceback"]
        == EXPECTED_INITIALIZATION_CONTRACT["privacy_and_traceback"],
        "C2B3A_PRIVACY_INVALID",
    )
    _require(
        candidate["later_author_effect_owner_decisions"]
        == EXPECTED_INITIALIZATION_CONTRACT[
            "later_author_effect_owner_decisions"
        ],
        "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID",
    )
    _require(
        candidate["future_c2b3b_maximum_path_scope"]
        == EXPECTED_INITIALIZATION_CONTRACT[
            "future_c2b3b_maximum_path_scope"
        ],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        candidate["nonimplementation"]
        == EXPECTED_INITIALIZATION_CONTRACT["nonimplementation"],
        "C2B3A_NONIMPLEMENTATION_INVALID",
    )
    _require(
        candidate["commit_close_outcome_addendum"]
        == EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM,
        "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID",
    )


def _candidate() -> dict[str, object]:
    value = deepcopy(EXPECTED_INITIALIZATION_CONTRACT)
    assert type(value) is dict
    value["commit_close_outcome_addendum"] = deepcopy(
        EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM
    )
    return value


def _golden_candidate() -> dict[str, object]:
    value = deepcopy(EXPECTED_INITIALIZATION_GOLDEN_VECTOR)
    assert type(value) is dict
    return value


def _traceback_signature(
    traceback_object: object,
) -> tuple[tuple[int, int, str], ...]:
    signature: tuple[tuple[int, int, str], ...] = ()
    current = traceback_object
    while current is not None:
        signature += (
            (
                id(current),
                id(current.tb_frame.f_code),
                current.tb_frame.f_code.co_name,
            ),
        )
        current = current.tb_next
    return signature


def _exception_graph_snapshot(
    exception: BaseException,
) -> tuple[object, object, bool, bool, object]:
    notes_present = "__notes__" in exception.__dict__
    notes = exception.__dict__["__notes__"] if notes_present else None
    return (
        exception.__cause__,
        exception.__context__,
        exception.__suppress_context__,
        notes_present,
        notes,
    )


def _process_control_exception_graph_contains_private_material(
    exception: BaseException,
) -> bool:
    forbidden = (
        "repair4-private-",
        "ordinary commit exception",
        "ordinary close exception",
        "raw SQLite exception",
        "/private/tmp/repair4-sensitive",
        "SELECT repair4-sensitive",
        "work-spec-repair4-sensitive",
    )
    seen: tuple[int, ...] = ()
    current: BaseException | None = exception
    while current is not None and id(current) not in seen:
        seen += (id(current),)
        rendered_exception = repr(current)
        rendered_string = str(current)
        rendered_args = repr(current.args)
        rendered_dictionary = repr(current.__dict__)
        rendered_traceback = repr(
            _traceback_signature(current.__traceback__)
        )
        rendered = (
            rendered_exception,
            rendered_string,
            rendered_args,
            rendered_dictionary,
            rendered_traceback,
        )
        if any(item in value for item in forbidden for value in rendered):
            return True
        traceback_object = current.__traceback__
        while traceback_object is not None:
            for local_name in traceback_object.tb_frame.f_locals:
                local_value = repr(
                    traceback_object.tb_frame.f_locals[local_name]
                )
                if any(item in local_value for item in forbidden):
                    return True
            traceback_object = traceback_object.tb_next
        if current.__cause__ is not None:
            current = current.__cause__
        else:
            current = current.__context__
    return False


def _bare_reraise_reference(
    injected_exception: BaseException,
) -> dict[str, object]:
    caught_traceback_tail = None
    caught_signature: tuple[tuple[int, int, str], ...] = ()
    graph_before: tuple[object, object, bool, bool, object] | None = None
    try:
        try:
            raise injected_exception
        except BaseException as caught_exception:
            caught_traceback_tail = caught_exception.__traceback__
            caught_signature = _traceback_signature(caught_traceback_tail)
            graph_before = _exception_graph_snapshot(caught_exception)
            raise
    except BaseException as propagated_exception:
        propagated_signature = _traceback_signature(
            propagated_exception.__traceback__
        )
        return {
            "same_exception_object": propagated_exception is injected_exception,
            "caught_traceback_tail_identity_preserved": propagated_exception.__traceback__
            is caught_traceback_tail,
            "repair_owned_traceback_frame_delta": len(propagated_signature)
            - len(caught_signature),
            "caught_signature": caught_signature,
            "propagated_signature": propagated_signature,
            "graph_before": graph_before,
            "graph_after": _exception_graph_snapshot(propagated_exception),
            "private_material_in_exception_graph": _process_control_exception_graph_contains_private_material(
                propagated_exception
            ),
        }
    assert False


def _named_reraise_reference(
    injected_exception: BaseException,
) -> dict[str, object]:
    caught_traceback_tail = None
    caught_signature: tuple[tuple[int, int, str], ...] = ()
    try:
        try:
            raise injected_exception
        except BaseException as caught_exception:
            caught_traceback_tail = caught_exception.__traceback__
            caught_signature = _traceback_signature(caught_traceback_tail)
            raise caught_exception
    except BaseException as propagated_exception:
        propagated_signature = _traceback_signature(
            propagated_exception.__traceback__
        )
        return {
            "same_exception_object": propagated_exception is injected_exception,
            "caught_traceback_tail_identity_preserved": propagated_exception.__traceback__
            is caught_traceback_tail,
            "repair_owned_traceback_frame_delta": len(propagated_signature)
            - len(caught_signature),
            "caught_signature": caught_signature,
            "propagated_signature": propagated_signature,
        }
    assert False


def _exception_graph_identity_walk(
    exception: BaseException,
) -> tuple[int, ...]:
    pending: tuple[BaseException, ...] = (exception,)
    seen: tuple[int, ...] = ()
    while pending:
        current = pending[0]
        pending = pending[1:]
        if id(current) in seen:
            continue
        seen += (id(current),)
        if isinstance(current.__cause__, BaseException):
            pending += (current.__cause__,)
        if isinstance(current.__context__, BaseException):
            pending += (current.__context__,)
    return seen


def _relational_process_control_reference(
    primary: BaseException,
    secondary: BaseException,
) -> dict[str, object]:
    entered: tuple[str, ...] = ()
    completed: tuple[str, ...] = ()
    primary_graph_before = _exception_graph_identity_walk(primary)
    secondary_graph_before = _exception_graph_identity_walk(secondary)
    primary_notes_before = (
        primary.__dict__["__notes__"]
        if "__notes__" in primary.__dict__
        else None
    )
    primary_cause_type_name_before = (
        type(primary.__cause__).__name__
        if isinstance(primary.__cause__, BaseException)
        else None
    )
    primary_context_type_name_before = (
        type(primary.__context__).__name__
        if isinstance(primary.__context__, BaseException)
        else None
    )
    secondary_cause_type_name_before = (
        type(secondary.__cause__).__name__
        if isinstance(secondary.__cause__, BaseException)
        else None
    )
    secondary_context_type_name_before = (
        type(secondary.__context__).__name__
        if isinstance(secondary.__context__, BaseException)
        else None
    )
    caught_primary_object: BaseException | None = None
    caught_secondary_object: BaseException | None = None
    try:
        try:
            entered += ("raise-primary",)
            raise primary
        except (KeyboardInterrupt, SystemExit, GeneratorExit) as caught_primary:
            caught_primary_object = caught_primary
            completed += ("catch-primary",)
            try:
                entered += ("raise-secondary",)
                raise secondary
            except (KeyboardInterrupt, SystemExit, GeneratorExit) as caught_secondary:
                caught_secondary_object = caught_secondary
                completed += ("catch-secondary",)
            entered += ("bare-reraise-primary",)
            raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit) as outward_primary:
        completed += ("bare-reraise-primary",)
        return {
            "safe_projection": (
                "same_instance" if primary is secondary else "distinct_instance",
                type(outward_primary).__name__,
                outward_primary.args,
                (
                    outward_primary.code
                    if type(outward_primary) is SystemExit
                    else "not_applicable"
                ),
                entered,
                completed,
                len(primary_graph_before),
                len(secondary_graph_before),
                len(primary_graph_before) == len(set(primary_graph_before)),
                len(secondary_graph_before) == len(set(secondary_graph_before)),
                (
                    tuple(primary_notes_before)
                    if type(primary_notes_before) is list
                    else None
                ),
                primary_cause_type_name_before,
                primary_context_type_name_before,
                secondary_cause_type_name_before,
                secondary_context_type_name_before,
                False,
                False,
            ),
            "provided_primary": primary,
            "provided_secondary": secondary,
            "caught_primary": caught_primary_object,
            "caught_secondary": caught_secondary_object,
            "outward_primary": outward_primary,
            "identity_relation": (
                "same_instance" if primary is secondary else "distinct_instance"
            ),
            "outward_type": type(outward_primary),
            "outward_args": outward_primary.args,
            "outward_SystemExit_code": (
                outward_primary.code
                if type(outward_primary) is SystemExit
                else "not_applicable"
            ),
            "entered": entered,
            "completed": completed,
            "primary_graph_before": primary_graph_before,
            "secondary_graph_before": secondary_graph_before,
            "primary_graph_after": _exception_graph_identity_walk(outward_primary),
            "exact_interpreter_graph_promise": False,
            "Coordinator_graph_assignment_or_restoration": False,
        }
    assert False


def _cleanup_reference_result(
    *,
    state: str,
    entered: tuple[str, ...],
    completed: tuple[str, ...],
    admission_open: bool,
    wrapper_reachable: bool,
    ordinary_closing: bool,
    connection_owned: bool,
    connection_closed_proved: bool,
    credential_authority: bool,
    mutation_slot_owned: bool,
    database_binding_owned: bool,
    writer_lock_release: str,
    descriptor_outcome: str,
    descriptor_retryable: bool,
    descriptor_owned: bool,
    authority_lock_terminal: bool,
    authority_lock_registry_present: bool,
    writer_session_registry_present: bool,
    close_attempts: int,
    unlock_attempts: int,
    descriptor_close_attempts: int,
    finalizer_attempted: bool,
    retry_reachable: bool,
    effective_cleanup_outcome: str,
    selected_outward: str,
    cleanup_failure_suppressed: bool,
) -> dict[str, object]:
    return {
        "safe_projection": (
            state,
            entered,
            completed,
            admission_open,
            wrapper_reachable,
            ordinary_closing,
            connection_owned,
            connection_closed_proved,
            credential_authority,
            mutation_slot_owned,
            database_binding_owned,
            writer_lock_release,
            descriptor_outcome,
            descriptor_retryable,
            descriptor_owned,
            authority_lock_terminal,
            authority_lock_registry_present,
            writer_session_registry_present,
            close_attempts,
            unlock_attempts,
            descriptor_close_attempts,
            finalizer_attempted,
            retry_reachable,
            effective_cleanup_outcome,
            selected_outward,
            cleanup_failure_suppressed,
            state == "X",
            state == "X",
            state == "X",
            state == "X",
        ),
        "state": state,
        "entered": entered,
        "completed": completed,
        "admission_open": admission_open,
        "wrapper_reachable": wrapper_reachable,
        "ordinary_closing": ordinary_closing,
        "connection_owned": connection_owned,
        "connection_closed_proved": connection_closed_proved,
        "credential_authority": credential_authority,
        "mutation_slot_owned": mutation_slot_owned,
        "database_binding_owned": database_binding_owned,
        "writer_lock_release": writer_lock_release,
        "descriptor_outcome": descriptor_outcome,
        "descriptor_retryable": descriptor_retryable,
        "descriptor_owned": descriptor_owned,
        "authority_lock_terminal": authority_lock_terminal,
        "authority_lock_registry_present": authority_lock_registry_present,
        "writer_session_registry_present": writer_session_registry_present,
        "close_attempts": close_attempts,
        "unlock_attempts": unlock_attempts,
        "descriptor_close_attempts": descriptor_close_attempts,
        "finalizer_attempted": finalizer_attempted,
        "retry_reachable": retry_reachable,
        "effective_cleanup_outcome": effective_cleanup_outcome,
        "selected_outward": selected_outward,
        "cleanup_failure_suppressed": cleanup_failure_suppressed,
        "X": state == "X",
        "recovery_admitted": state == "X",
        "replay_admitted": state == "X",
        "new_operation_admitted": state == "X",
    }


def _cleanup_reference(
    initial_state: str,
    fault_step: str | None,
    fault_position: str | None,
    connection_outcome: str,
    unlock_outcome: str,
    descriptor_close_outcome: str,
    finalizer: bool,
    cleanup_outcome: str,
    earlier_primary: str,
) -> tuple[object, ...]:
    assert initial_state in ("A", "QU", "QK", "PU", "PK")
    assert fault_step in (
        None,
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
    assert fault_position in (None, "before", "between", "after")
    assert connection_outcome in ("normal", "ordinary", "KeyboardInterrupt", "SystemExit", "GeneratorExit")
    assert unlock_outcome in ("normal", "unproved", "retry_normal")
    assert descriptor_close_outcome in ("normal", "unknown")
    assert type(finalizer) is bool
    assert cleanup_outcome in ("normal", "ordinary", "KeyboardInterrupt", "SystemExit", "GeneratorExit")
    assert earlier_primary in ("none", "KeyboardInterrupt", "SystemExit", "GeneratorExit")
    assert (fault_step is None) == (fault_position is None)
    assert fault_position != "between" or fault_step == "H2"

    state = initial_state
    entered: tuple[str, ...] = ()
    completed: tuple[str, ...] = ()
    admission_open = initial_state == "A"
    wrapper_reachable = not finalizer
    ordinary_closing = False
    connection_owned = initial_state in ("QU", "QK")
    connection_closed_proved = initial_state in ("PU", "PK")
    credential_authority = True
    mutation_slot_owned = True
    database_binding_owned = True
    writer_lock_release = "not_attempted"
    descriptor_outcome = "not_attempted"
    descriptor_retryable = True
    descriptor_owned = True
    authority_lock_terminal = False
    authority_lock_registry_present = True
    writer_session_registry_present = True
    close_attempts = 0
    unlock_attempts = 0
    descriptor_close_attempts = 0
    finalizer_attempted = finalizer
    retry_reachable = not finalizer
    effective_cleanup_outcome = "normal"
    halted = False

    entered += ("P0",)
    if fault_step == "P0" and fault_position == "before" and not finalizer:
        effective_cleanup_outcome = cleanup_outcome
        halted = True
    else:
        admission_open = False
        if state == "A":
            state = "A-closing"
            ordinary_closing = True
        completed += ("P0",)
        if fault_step == "P0" and fault_position in ("before", "after"):
            effective_cleanup_outcome = cleanup_outcome
            halted = True

    if not halted and initial_state in ("QU", "QK"):
        entered += ("C1",)
        if fault_step == "C1" and fault_position == "before":
            effective_cleanup_outcome = cleanup_outcome
            halted = True
        else:
            close_attempts += 1
            if connection_outcome == "normal":
                completed += ("C1",)
                entered += ("C2",)
                connection_closed_proved = True
                connection_owned = False
                state = "PU" if initial_state == "QU" else "PK"
                completed += ("C2",)
                if fault_step in ("C1", "C2") and fault_position in (
                    "before",
                    "after",
                ):
                    effective_cleanup_outcome = cleanup_outcome
                    halted = True
            else:
                effective_cleanup_outcome = connection_outcome
                halted = True

    if not halted:
        entered += ("R1",)
        if fault_step == "R1" and fault_position == "before":
            effective_cleanup_outcome = cleanup_outcome
            halted = True
        else:
            credential_authority = False
            completed += ("R1",)
            if fault_step == "R1" and fault_position == "after":
                effective_cleanup_outcome = cleanup_outcome
                halted = True

    if not halted:
        entered += ("R2",)
        if fault_step == "R2" and fault_position == "before":
            effective_cleanup_outcome = cleanup_outcome
            halted = True
        else:
            mutation_slot_owned = False
            completed += ("R2",)
            if fault_step == "R2" and fault_position == "after":
                effective_cleanup_outcome = cleanup_outcome
                halted = True

    if not halted:
        entered += ("R3",)
        if fault_step == "R3" and fault_position == "before":
            effective_cleanup_outcome = cleanup_outcome
            halted = True
        else:
            database_binding_owned = False
            completed += ("R3",)
            if fault_step == "R3" and fault_position == "after":
                effective_cleanup_outcome = cleanup_outcome
                halted = True

    if not halted:
        entered += ("L1",)
        if fault_step == "L1" and fault_position == "before":
            effective_cleanup_outcome = cleanup_outcome
            halted = True
        else:
            unlock_attempts += 1
            if unlock_outcome == "unproved":
                writer_lock_release = "release_unproved"
                effective_cleanup_outcome = cleanup_outcome
                halted = True
            else:
                if unlock_outcome == "retry_normal":
                    writer_lock_release = "release_unproved"
                    unlock_attempts += 1
                writer_lock_release = "release_proved"
                completed += ("L1",)
                if fault_step == "L1" and fault_position == "after":
                    effective_cleanup_outcome = cleanup_outcome
                    halted = True

    if not halted:
        entered += ("H1",)
        if fault_step == "H1" and fault_position == "before":
            effective_cleanup_outcome = cleanup_outcome
            halted = True
        else:
            descriptor_retryable = False
            descriptor_owned = False
            descriptor_close_attempts += 1
            descriptor_outcome = (
                "reclaimed"
                if descriptor_close_outcome == "normal"
                else "reclamation_unknown"
            )
            completed += ("H1",)
            if fault_step == "H1" and fault_position == "after":
                effective_cleanup_outcome = cleanup_outcome
                halted = True

    if not halted:
        entered += ("H2",)
        if fault_step == "H2" and fault_position == "before":
            effective_cleanup_outcome = cleanup_outcome
            halted = True
        else:
            authority_lock_terminal = True
            if fault_step == "H2" and fault_position == "between":
                effective_cleanup_outcome = cleanup_outcome
                halted = True
            else:
                authority_lock_registry_present = False
                completed += ("H2",)
                if fault_step == "H2" and fault_position == "after":
                    effective_cleanup_outcome = cleanup_outcome
                    halted = True

    if not halted:
        entered += ("T1",)
        if fault_step == "T1" and fault_position == "before":
            effective_cleanup_outcome = cleanup_outcome
            halted = True
        else:
            state = "X"
            ordinary_closing = False
            completed += ("T1",)
            if fault_step == "T1" and fault_position == "after":
                effective_cleanup_outcome = cleanup_outcome
                halted = True

    if not halted:
        entered += ("H3",)
        if fault_step == "H3" and fault_position == "before":
            effective_cleanup_outcome = cleanup_outcome
            halted = True
        else:
            writer_session_registry_present = False
            completed += ("H3",)
            if fault_step == "H3" and fault_position == "after":
                effective_cleanup_outcome = cleanup_outcome
                halted = True

    selected_outward = "none"
    if not finalizer:
        if earlier_primary != "none":
            selected_outward = "commit_" + earlier_primary
        elif halted and effective_cleanup_outcome in (
            "KeyboardInterrupt",
            "SystemExit",
            "GeneratorExit",
        ):
            selected_outward = "cleanup_" + effective_cleanup_outcome
    cleanup_failure_suppressed = halted and (
        finalizer
        or earlier_primary != "none"
        or effective_cleanup_outcome == "ordinary"
    )
    assert not (
        connection_closed_proved
        and (state in ("QU", "QK") or connection_owned)
    )
    assert not (state in ("PU", "PK") and connection_owned)
    assert not (
        finalizer and not wrapper_reachable and admission_open
    )
    return _cleanup_reference_result(
        state=state,
        entered=entered,
        completed=completed,
        admission_open=admission_open,
        wrapper_reachable=wrapper_reachable,
        ordinary_closing=ordinary_closing,
        connection_owned=connection_owned,
        connection_closed_proved=connection_closed_proved,
        credential_authority=credential_authority,
        mutation_slot_owned=mutation_slot_owned,
        database_binding_owned=database_binding_owned,
        writer_lock_release=writer_lock_release,
        descriptor_outcome=descriptor_outcome,
        descriptor_retryable=descriptor_retryable,
        descriptor_owned=descriptor_owned,
        authority_lock_terminal=authority_lock_terminal,
        authority_lock_registry_present=authority_lock_registry_present,
        writer_session_registry_present=writer_session_registry_present,
        close_attempts=close_attempts,
        unlock_attempts=unlock_attempts,
        descriptor_close_attempts=descriptor_close_attempts,
        finalizer_attempted=finalizer_attempted,
        retry_reachable=retry_reachable,
        effective_cleanup_outcome=effective_cleanup_outcome,
        selected_outward=selected_outward,
        cleanup_failure_suppressed=cleanup_failure_suppressed,
    )["safe_projection"]


def _expect_violation(candidate: object, code: str) -> None:
    with pytest.raises(_ContractViolation) as exc_info:
        _validate_contract(candidate)
    assert str(exc_info.value) == code


def _expect_golden_violation(candidate: object) -> None:
    with pytest.raises(_ContractViolation) as exc_info:
        _validate_golden_vector(candidate)
    assert str(exc_info.value) == "C2B3A_GOLDEN_VECTOR_INVALID"


def _assert_preassigned_binding(
    contract: dict[str, object],
    vector: dict[str, object],
) -> None:
    relations = (
        "preassigned_attempt_candidate_binding.work_item_ref == safe command work_spec_safe_projection.work_item_ref == sole program-version membership work_item_ref == sole WorkSpec binding work_item_ref",
        "preassigned_attempt_candidate_binding.work_item_revision_ref == safe command work_spec_safe_projection.work_item_revision_ref == sole program-version membership work_item_revision_ref == sole WorkSpec binding work_item_revision_ref",
        "preassigned_attempt_candidate_binding.preassigned_semantic_attempt_ref == safe command preassigned_semantic_attempt_ref == initialize decision preassigned_semantic_attempt_ref",
        "preassigned_attempt_candidate_binding.preassigned_candidate_ref == safe command preassigned_candidate_ref == initialize decision preassigned_candidate_ref",
    )
    cardinality = contract["genesis_cardinality"]
    _require(
        "selected_attempt_candidate_binding" not in cardinality,
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        "preassigned_attempt_candidate_binding" in cardinality,
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    binding = cardinality["preassigned_attempt_candidate_binding"]
    _require(
        binding["ordered_fields"]
        == (
            "work_item_ref",
            "work_item_revision_ref",
            "preassigned_semantic_attempt_ref",
            "preassigned_candidate_ref",
        ),
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        binding["relations"] == relations,
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        tuple(contract["safe_command"]["cross_relations"][-4:]) == relations,
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    binding_rendered = repr(binding)
    binding_text = binding_rendered.lower()
    for forbidden in (
        "selected",
        "current",
        "created",
        "authorized",
        "executable",
    ):
        _require(
            forbidden not in binding_text,
            "C2B3A_PREASSIGNED_BINDING_INVALID",
        )
    _require(
        binding["future_lineage_only"] is True,
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        binding["creates_selects_authorizes_or_executes_attempt_or_candidate"]
        is False,
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )

    safe = vector["safe_command"]
    projection = safe["work_spec_safe_projection"]
    rows = vector["persisted_rows"]
    decision = rows["initialize_decision"]
    membership = rows["program_version_work_item"]
    work_spec_binding = rows["work_spec_binding"]
    _require(
        projection["work_item_ref"]
        == membership["work_item_ref"]
        == work_spec_binding["work_item_ref"],
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        projection["work_item_revision_ref"]
        == membership["work_item_revision_ref"]
        == work_spec_binding["work_item_revision_ref"],
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        safe["preassigned_semantic_attempt_ref"]
        == decision["preassigned_semantic_attempt_ref"],
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        safe["preassigned_candidate_ref"]
        == decision["preassigned_candidate_ref"],
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    for field in (
        "selected_semantic_attempt_ref",
        "selected_candidate_ref",
        "selected_attempt_fence_ref",
        "selected_attempt_fence_digest",
    ):
        _require(
            decision[field] is None,
            "C2B3A_PREASSIGNED_BINDING_INVALID",
        )
    for absent_role in ("semantic_attempt", "candidate", "attempt_fence"):
        _require(
            absent_role not in rows,
            "C2B3A_PREASSIGNED_BINDING_INVALID",
        )


def _assert_original_apply_outcome(contract: dict[str, object]) -> None:
    expected_error = {
        "type": "SQLiteMutationStoreError",
        "reason": "commit_outcome_unknown",
        "internal_detail": None,
        "cause": None,
        "context": None,
        "notes": None,
        "raised_from": None,
    }
    gate = contract["commit_uncertainty_cleanup_gate"]
    complete = gate["close_complete"]
    quarantined = gate["close_not_proved"]
    _require(
        complete.get("original_apply_error") == expected_error,
        "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
    )
    _require(
        quarantined.get("original_apply_error") == expected_error,
        "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
    )
    _require(
        quarantined["ordered_steps"]
        == (
            "commit attempt raises",
            "controller retains connection custody and mutation slot",
            "close is attempted",
            "close not proved",
            "connection custody transfers to private _WriterSessionResource",
            "session quarantine is recorded",
            "writer-authority lock remains retained",
            "mutation slot remains unavailable",
            "fresh content-free commit_outcome_unknown is raised from None",
        ),
        "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
    )
    for field in (
        "close_failure_replaces_primary_error",
        "close_failure_decorates_primary_error",
        "close_failure_leaks_outward",
        "close_exception_in_outward_error_graph",
        "mutation_slot_available",
        "same_session_database_backed_resolver",
        "new_session_resolver_before_proved_close",
        "automatic_semantic_retry",
    ):
        _require(
            quarantined[field] is False,
            "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
        )
    _require(
        quarantined["same_session_resolver_disposition"]
        == "unresolved before operation-lease acquisition, database open, BEGIN, or SQL",
        "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
    )
    _require(
        complete["session_quarantined"] is False
        and complete["mutation_slot_available"] is True
        and complete["slot_release_gate"] == "only after close proof",
        "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
    )
    _require(
        tuple(quarantined["process_control_exceptions"])
        == ("KeyboardInterrupt", "SystemExit", "GeneratorExit"),
        "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
    )


def _assert_future_c2b3b_scope(contract: dict[str, object]) -> None:
    production = (
        "src/ge_nwp_coordinator/_development_program_initialization_contracts.py",
        "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py",
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "src/ge_nwp_coordinator/sqlite_writer_session.py",
        "src/ge_nwp_coordinator/sqlite_connection.py",
    )
    documentation_status = (
        ".docs/c2b-durable-development-state.md",
        ".docs/c2b3-program-initialization.md",
        ".docs/c2b2-private-readers.md",
        ".docs/architecture.md",
        ".docs/durable-state-model.md",
        ".docs/sqlite-operations-and-recovery.md",
        ".docs/sqlite-threat-model.md",
        "README.md",
        "AGENTS.md",
    )
    tests = (
        "tests/test_c2b3_program_initialization_contract.py",
        "tests/test_c2b3_private_atomic_program_initialization.py",
        "tests/test_c2b3_program_initialization_recovery.py",
        "tests/test_c2b3_private_program_initialization_delegation.py",
        "tests/test_c2b2_field_level_contract.py",
        "tests/test_c2b2_private_development_readers.py",
        "tests/test_c2b2_development_reader_contracts.py",
        "tests/test_runtime_non_authority.py",
        "tests/test_architecture_contracts.py",
        "tests/test_c2b0_durable_state_contract.py",
    )
    scope = contract["future_c2b3b_maximum_path_scope"]
    _require(
        scope["tranche"] == "C2B3B_PRIVATE_ATOMIC_INITIALIZATION",
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        scope["maximum_paths"] == 24
        and scope["production"] == production
        and scope["documentation_status"] == documentation_status
        and scope["tests"] == tests,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        scope["counts"]
        == {
            "production": 5,
            "documentation_status": 9,
            "tests": 10,
            "total": 24,
        },
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    combined = production + documentation_status + tests
    _require(
        len(combined) == 24 and len(set(combined)) == 24,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    responsibilities = scope["production_responsibilities"]
    _require(
        tuple(responsibilities) == production,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        "no process-control result or enum"
        in responsibilities[
            "src/ge_nwp_coordinator/_development_program_initialization_contracts.py"
        ],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        "does not catch, translate, wrap, or retry KeyboardInterrupt, SystemExit, or GeneratorExit after transaction cleanup returns them for propagation"
        in responsibilities[
            "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py"
        ],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        "retain uncertain connection and mutation slot after commit exception"
        in responsibilities["src/ge_nwp_coordinator/sqlite_transition_transaction.py"],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        "re-raise the identical process-control exception only after publication completion"
        in responsibilities["src/ge_nwp_coordinator/sqlite_transition_transaction.py"],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    for exact_responsibility in (
        "reduce and detach the ordinary commit failure before close-time process-control handling",
        "catch exactly KeyboardInterrupt, SystemExit, and GeneratorExit from close",
        "retain connection, slot, and writer-lock custody",
        "perform a bare re-raise in the same catch suite",
        "add no traceback frame beyond bare-reraise semantics",
        "add no cause, context, note, or exception-graph material",
    ):
        _require(
            exact_responsibility
            in responsibilities[
                "src/ge_nwp_coordinator/sqlite_transition_transaction.py"
            ],
            "C2B3A_FUTURE_SCOPE_INVALID",
        )
    _require(
        "_WriterSessionResource retained-connection custody"
        in responsibilities["src/ge_nwp_coordinator/sqlite_writer_session.py"],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        "acknowledge quarantine publication before the transaction layer re-raises a named process-control exception"
        in responsibilities["src/ge_nwp_coordinator/sqlite_writer_session.py"],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    for exact_responsibility in (
        "publication acknowledgement must not raise or attach an ordinary exception to the process-control exception",
        "publication helpers receive no authority to propagate or replace the caught process-control exception",
    ):
        _require(
            exact_responsibility
            in responsibilities["src/ge_nwp_coordinator/sqlite_writer_session.py"],
            "C2B3A_FUTURE_SCOPE_INVALID",
        )
    connection_responsibilities = responsibilities[
        "src/ge_nwp_coordinator/sqlite_connection.py"
    ]
    _require(
        "cross-thread close from session-resource finalization is permitted only for proved closure"
        in connection_responsibilities,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        "may surface the exact close-time KeyboardInterrupt, SystemExit, or GeneratorExit"
        in connection_responsibilities,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    scope_text = repr(scope)
    _require(
        "StateStore quarantine" not in scope_text
        and "public WriterSession quarantine" not in scope_text,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        scope["twenty_fifth_path"] == "future implementation stop condition"
        and scope["authorized_by_this_freeze"] is False,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )


def _enclosing_function_name(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> str | None:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
        current = parents.get(current)
    return None


def _assigned_names(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, (ast.Tuple, ast.List)):
        names: list[str] = []
        for element in node.elts:
            names.extend(_assigned_names(element))
        return tuple(names)
    return ()


def _direct_literal_assignment(
    tree: ast.Module,
    name: str,
    expected: object,
) -> None:
    assignments = [
        statement
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == name
    ]
    _require(len(assignments) == 1, "C2B3A_ORACLE_EXPECTED_NOT_LITERAL")
    assignment = assignments[0]
    expected_node_type: type[ast.AST]
    if type(expected) is dict:
        expected_node_type = ast.Dict
    elif type(expected) is tuple:
        expected_node_type = ast.Tuple
    elif type(expected) is str:
        expected_node_type = ast.Constant
    else:
        raise _ContractViolation("C2B3A_ORACLE_EXPECTED_NOT_LITERAL")
    _require(
        isinstance(assignment.value, expected_node_type),
        "C2B3A_ORACLE_EXPECTED_NOT_LITERAL",
    )
    try:
        value = ast.literal_eval(assignment.value)
    except (SyntaxError, ValueError):
        raise _ContractViolation("C2B3A_ORACLE_EXPECTED_NOT_LITERAL") from None
    _require(value == expected, "C2B3A_ORACLE_EXPECTED_NOT_LITERAL")


def _direct_allowed_import_inventory(tree: ast.Module) -> None:
    assignments = [
        statement
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "ALLOWED_ORACLE_IMPORTS"
    ]
    _require(len(assignments) == 1, "C2B3A_ORACLE_FORBIDDEN_INPUT")
    assignment = assignments[0]
    _require(isinstance(assignment.value, ast.Tuple), "C2B3A_ORACLE_FORBIDDEN_INPUT")
    _require(
        ast.literal_eval(assignment.value) == ("ast", "copy", "pathlib", "pytest"),
        "C2B3A_ORACLE_FORBIDDEN_INPUT",
    )


def _assert_oracle_architecture(source: str) -> None:
    try:
        tree = ast.parse(source, filename=TEST_PATH.name)
    except SyntaxError:
        raise _ContractViolation("C2B3A_ORACLE_FORBIDDEN_INPUT") from None
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    top_level_nodes = {id(node) for node in tree.body}
    observed_imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            _require(id(node) in top_level_nodes, "C2B3A_ORACLE_FORBIDDEN_INPUT")
            for item in node.names:
                _require(item.asname is None, "C2B3A_ORACLE_FORBIDDEN_INPUT")
                observed_imports.append(item.name)
        elif isinstance(node, ast.ImportFrom):
            _require(id(node) in top_level_nodes, "C2B3A_ORACLE_FORBIDDEN_INPUT")
            _require(
                node.level == 0 and node.module is not None,
                "C2B3A_ORACLE_FORBIDDEN_INPUT",
            )
            for item in node.names:
                _require(item.asname is None, "C2B3A_ORACLE_FORBIDDEN_INPUT")
            observed_imports.append(node.module)
    _require(
        tuple(sorted(observed_imports)) == ("ast", "copy", "pathlib", "pytest"),
        "C2B3A_ORACLE_FORBIDDEN_INPUT",
    )

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
        "open",
    }
    allowed_read_calls = 0
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            _require(
                node.id not in forbidden_dynamic_names,
                "C2B3A_ORACLE_FORBIDDEN_INPUT",
            )
        if isinstance(node, ast.Attribute):
            _require(
                node.attr not in forbidden_dynamic_names,
                "C2B3A_ORACLE_FORBIDDEN_INPUT",
            )
        if isinstance(node, ast.Lambda):
            raise _ContractViolation("C2B3A_ORACLE_DYNAMIC_DISPATCH")
        if isinstance(node, ast.Call):
            _require(
                not isinstance(node.func, ast.Subscript),
                "C2B3A_ORACLE_DYNAMIC_DISPATCH",
            )
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "read_text",
                "read_bytes",
                "open",
            }:
                _require(
                    node.func.attr == "read_text"
                    and _enclosing_function_name(node, parents) == "_read_allowed_text"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "resolved"
                    and not node.args
                    and len(node.keywords) == 1
                    and node.keywords[0].arg == "encoding"
                    and isinstance(node.keywords[0].value, ast.Constant)
                    and node.keywords[0].value.value == "utf-8",
                    "C2B3A_ORACLE_FORBIDDEN_INPUT",
                )
                allowed_read_calls += 1
            if isinstance(node.func, ast.Name) and node.func.id == "_read_allowed_text":
                _require(
                    len(node.args) == 1
                    and isinstance(node.args[0], ast.Name)
                    and node.args[0].id in {"OWNER_PATH", "PLANNING_PATH", "TEST_PATH"}
                    and not node.keywords,
                    "C2B3A_ORACLE_FORBIDDEN_INPUT",
                )
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            normalized_name = node.name.lower()
            _require(
                "dispatch" not in normalized_name
                and "runner" not in normalized_name
                and "run_mutation" not in normalized_name
                and "run_counterfactual" not in normalized_name,
                "C2B3A_ORACLE_DYNAMIC_DISPATCH",
            )
            parameter_names = {
                argument.arg
                for argument in (
                    *node.args.posonlyargs,
                    *node.args.args,
                    *node.args.kwonlyargs,
                )
            }
            if node.args.vararg is not None:
                parameter_names.add(node.args.vararg.arg)
            if node.args.kwarg is not None:
                parameter_names.add(node.args.kwarg.arg)
            for descendant in ast.walk(node):
                if isinstance(descendant, ast.Call) and isinstance(
                    descendant.func, ast.Name
                ):
                    _require(
                        descendant.func.id not in parameter_names,
                        "C2B3A_ORACLE_DYNAMIC_DISPATCH",
                    )
        if isinstance(node, ast.For):
            loop_names = set(_assigned_names(node.target))
            for descendant in ast.walk(node):
                if isinstance(descendant, ast.Call) and isinstance(
                    descendant.func, ast.Name
                ):
                    _require(
                        descendant.func.id not in loop_names,
                        "C2B3A_ORACLE_DYNAMIC_DISPATCH",
                    )
        if isinstance(node, ast.comprehension):
            loop_names = set(_assigned_names(node.target))
            container = parents.get(node)
            while container is not None and not isinstance(
                container,
                (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp),
            ):
                container = parents.get(container)
            _require(container is not None, "C2B3A_ORACLE_DYNAMIC_DISPATCH")
            for descendant in ast.walk(container):
                if isinstance(descendant, ast.Call) and isinstance(
                    descendant.func, ast.Name
                ):
                    _require(
                        descendant.func.id not in loop_names,
                        "C2B3A_ORACLE_DYNAMIC_DISPATCH",
                    )
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            target_names = tuple(
                name for target in targets for name in _assigned_names(target)
            )
            _require(
                not any(
                    (
                        "registry" in name.lower()
                        and name
                        not in {
                            "authority_lock_registry_present",
                            "writer_session_registry_present",
                        }
                    )
                    or "dispatcher" in name.lower()
                    or "runners" in name.lower()
                    for name in target_names
                ),
                "C2B3A_ORACLE_DYNAMIC_DISPATCH",
            )
            value = node.value
            if isinstance(value, ast.Name):
                _require(
                    value.id not in function_names,
                    "C2B3A_ORACLE_DYNAMIC_DISPATCH",
                )
            if isinstance(value, (ast.Dict, ast.List, ast.Tuple, ast.Set)):
                _require(
                    not any(
                        (
                            isinstance(descendant, ast.Name)
                            and descendant.id in function_names
                            and not (
                                isinstance(parents.get(descendant), ast.Call)
                                and parents.get(descendant).func is descendant
                            )
                        )
                        or isinstance(descendant, (ast.Attribute, ast.Lambda))
                        for descendant in ast.walk(value)
                    ),
                    "C2B3A_ORACLE_DYNAMIC_DISPATCH",
                )
    _require(allowed_read_calls == 1, "C2B3A_ORACLE_FORBIDDEN_INPUT")
    _direct_allowed_import_inventory(tree)
    _direct_literal_assignment(
        tree,
        "EXPECTED_PLANNING_PROJECTION",
        EXPECTED_PLANNING_PROJECTION,
    )
    _direct_literal_assignment(
        tree,
        "EXPECTED_INITIALIZATION_CONTRACT",
        EXPECTED_INITIALIZATION_CONTRACT,
    )
    _direct_literal_assignment(
        tree,
        "EXPECTED_INITIALIZATION_GOLDEN_VECTOR",
        EXPECTED_INITIALIZATION_GOLDEN_VECTOR,
    )
    _direct_literal_assignment(
        tree,
        "EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM",
        EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM,
    )
    _direct_literal_assignment(
        tree,
        "EXPECTED_PROCESS_CONTROL_REFERENCE_CASES",
        EXPECTED_PROCESS_CONTROL_REFERENCE_CASES,
    )
    _direct_literal_assignment(
        tree,
        "CLEANUP_SAFE_PROJECTION_FIELDS",
        CLEANUP_SAFE_PROJECTION_FIELDS,
    )
    _direct_literal_assignment(
        tree,
        "CLEANUP_REFERENCE_INPUT_CASES",
        CLEANUP_REFERENCE_INPUT_CASES,
    )
    _direct_literal_assignment(
        tree,
        "EXPECTED_CLEANUP_REFERENCE_CASES",
        EXPECTED_CLEANUP_REFERENCE_CASES,
    )


def test_owner_literal_equals_independent_expected_contract() -> None:
    owner_contract_candidate = _owner_contract()
    assert owner_contract_candidate == _candidate()
    assert tuple(owner_contract_candidate) == tuple(_candidate())
    assert (
        owner_contract_candidate["commit_close_outcome_addendum"]
        == EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM
    )
    _validate_contract(owner_contract_candidate)


def test_owner_golden_vector_equals_independent_direct_literal() -> None:
    owner_golden_vector_candidate = _owner_golden_vector()
    assert owner_golden_vector_candidate == EXPECTED_INITIALIZATION_GOLDEN_VECTOR
    assert tuple(owner_golden_vector_candidate) == tuple(
        EXPECTED_INITIALIZATION_GOLDEN_VECTOR
    )
    observed_repr = repr(owner_golden_vector_candidate)
    expected_repr = repr(EXPECTED_INITIALIZATION_GOLDEN_VECTOR)
    assert observed_repr.encode("utf-8") == expected_repr.encode("utf-8")
    owner_source = _read_allowed_text(OWNER_PATH)
    owner_parts = owner_source.split(VECTOR_BEGIN_MARKER, 1)
    vector_remainder = owner_parts[1]
    vector_parts = vector_remainder.split(
        VECTOR_END_MARKER,
        1,
    )
    payload = vector_parts[0]
    stripped_payload = payload.strip()
    payload_lines = stripped_payload.splitlines()
    newline = "\n"
    owner_literal_source = newline.join(payload_lines[1:-1])
    oracle_source = _read_allowed_text(TEST_PATH)
    oracle_tree = ast.parse(oracle_source, filename=TEST_PATH.name)
    assignment = next(
        statement
        for statement in oracle_tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "EXPECTED_INITIALIZATION_GOLDEN_VECTOR"
    )
    oracle_literal_source = ast.get_source_segment(oracle_source, assignment.value)
    assert oracle_literal_source == owner_literal_source
    _validate_golden_vector(owner_golden_vector_candidate)


def test_golden_vector_is_complete_privacy_safe_single_work_ledger() -> None:
    vector = deepcopy(EXPECTED_INITIALIZATION_GOLDEN_VECTOR)
    assert vector["vector_id"] == "c2b3a-initialization-single-work-v1"
    assert vector["vector_version"] == 1
    assert vector["transaction_timestamp"] == "2026-08-21T12:34:56Z"
    rows = vector["persisted_rows"]
    assert type(rows) is dict and len(rows) == 9
    assert type(vector["graph_entries"]) is tuple and len(vector["graph_entries"]) == 8
    decision = rows["initialize_decision"]
    assert decision["selected_semantic_attempt_ref"] is None
    assert decision["selected_candidate_ref"] is None
    assert decision["preassigned_semantic_attempt_ref"] == "semantic-attempt-c2b3a-1"
    assert decision["preassigned_candidate_ref"] == "candidate-c2b3a-1"
    binding_ref = rows["work_spec_binding"]["work_spec_ref"]
    assert binding_ref == vector["safe_command"]["work_spec_safe_projection"]["work_spec_ref"]
    assert binding_ref == vector["graph_entries"][7]["record_ref"]
    assert vector["mutation_receipt"] == rows["mutation_receipt"]
    rendered = repr(vector)
    for forbidden in ("objective", "requirements text", "exclusions text", "credential", "endpoint"):
        assert forbidden not in rendered


def test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected() -> None:
    candidate = _golden_candidate()
    candidate["accepted_intent_safe_projection_digest"] = "0" * 64
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    candidate["safe_command_canonical_utf8_hex"] = "00"
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    candidate["persisted_rows"]["program_head"]["head_digest"] = "0" * 64
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    candidate["graph_entries"][0]["record_digest"] = "0" * 64
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    candidate["result_projection_digest"] = "0" * 64
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    candidate["mutation_graph_digest"] = "0" * 64
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    candidate["mutation_receipt"]["result_class"] = "different"
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    del candidate["private_exact_replay_result"]
    _expect_golden_violation(candidate)


def test_golden_vector_parser_rejects_marker_fence_and_literal_bypasses() -> None:
    text = _read_allowed_text(OWNER_PATH)
    with pytest.raises(_ContractViolation) as exc_info:
        _owner_golden_vector(text.replace(VECTOR_BEGIN_MARKER, "", 1))
    assert str(exc_info.value) == "C2B3A_GOLDEN_VECTOR_MARKER_INVALID"

    with pytest.raises(_ContractViolation) as exc_info:
        _owner_golden_vector(text.replace(VECTOR_END_MARKER, VECTOR_BEGIN_MARKER, 1))
    assert str(exc_info.value) == "C2B3A_GOLDEN_VECTOR_MARKER_INVALID"

    vector_start = text.index(VECTOR_BEGIN_MARKER)
    vector_tail = text[vector_start:]
    with pytest.raises(_ContractViolation) as exc_info:
        _owner_golden_vector(
            text[:vector_start]
            + vector_tail.replace("```python", "```json", 1)
        )
    assert str(exc_info.value) == "C2B3A_GOLDEN_VECTOR_FENCE_INVALID"

    with pytest.raises(_ContractViolation) as exc_info:
        _owner_golden_vector(
            text[:vector_start]
            + vector_tail.replace("{'vector_id'", "dict(vector_id", 1)
        )
    assert str(exc_info.value) == "C2B3A_GOLDEN_VECTOR_LITERAL_INVALID"


def test_expected_contract_is_one_direct_literal_with_bounded_oracle_inputs() -> None:
    source = _read_allowed_text(TEST_PATH)
    _assert_oracle_architecture(source)


def test_oracle_architecture_counterfactuals_are_rejected() -> None:
    source = _read_allowed_text(TEST_PATH)
    insertion = "\ndef test_owner_literal_equals_independent_expected_contract"

    composite = """
def _architecture_probe():
    import hashlib
    import sqlite3
    import importlib
    import builtins
    builtins.eval("0")
    builtins.exec("pass")
    builtins.compile("0", "x", "eval")
    builtins.getattr(object(), "x", None)
    importlib.import_module("ge_nwp_coordinator")
    Path("/alternate").read_text(encoding="utf-8")
    Path("/alternate").read_bytes()
    VALIDATOR_REGISTRY = {"contract": _validate_contract}
    VALIDATOR_REGISTRY["contract"]({})
    for validator in VALIDATOR_REGISTRY.values():
        validator({})

def _run_mutation(value):
    return _validate_contract(value)
"""
    mutant = source.replace(insertion, composite + insertion, 1)
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_oracle_architecture(mutant)
    assert str(exc_info.value) == "C2B3A_ORACLE_FORBIDDEN_INPUT"

    for snippet, expected_code in (
        (
            '\nVALIDATOR_REGISTRY = {"contract": _validate_contract}\n',
            "C2B3A_ORACLE_DYNAMIC_DISPATCH",
        ),
        (
            "\ndef _semantic_dispatcher(value):\n    return _validate_contract(value)\n",
            "C2B3A_ORACLE_DYNAMIC_DISPATCH",
        ),
        (
            "\ndef _run_mutation(value):\n    return _validate_contract(value)\n",
            "C2B3A_ORACLE_DYNAMIC_DISPATCH",
        ),
        (
            '\nALTERNATE_DATA = Path("/alternate").read_bytes()\n',
            "C2B3A_ORACLE_FORBIDDEN_INPUT",
        ),
        (
            '\nCALLABLES = {"contract": _validate_contract}\nCALLABLES["contract"]({})\n',
            "C2B3A_ORACLE_DYNAMIC_DISPATCH",
        ),
        (
            '\nCALLABLES = (_validate_contract,)\nfor callback in CALLABLES:\n    callback({})\n',
            "C2B3A_ORACLE_DYNAMIC_DISPATCH",
        ),
    ):
        mutant = source.replace(insertion, snippet + insertion, 1)
        with pytest.raises(_ContractViolation) as exc_info:
            _assert_oracle_architecture(mutant)
        assert str(exc_info.value) == expected_code

    mutant = source.replace(
        "EXPECTED_INITIALIZATION_GOLDEN_VECTOR = {",
        "EXPECTED_INITIALIZATION_GOLDEN_VECTOR = _owner_golden_vector() or {",
        1,
    )
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_oracle_architecture(mutant)
    assert str(exc_info.value) == "C2B3A_ORACLE_EXPECTED_NOT_LITERAL"

    mutant = source.replace(
        "EXPECTED_INITIALIZATION_GOLDEN_VECTOR = {",
        "EXPECTED_INITIALIZATION_GOLDEN_VECTOR = _production_vector() or {",
        1,
    )
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_oracle_architecture(mutant)
    assert str(exc_info.value) == "C2B3A_ORACLE_EXPECTED_NOT_LITERAL"

    mutant = source.replace(
        "EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM = {",
        "EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM = _owner_contract()[\"commit_close_outcome_addendum\"] or {",
        1,
    )
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_oracle_architecture(mutant)
    assert str(exc_info.value) == "C2B3A_ORACLE_EXPECTED_NOT_LITERAL"

    mutant = source.replace(
        "EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM = {",
        "EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM = _production_contract() or {",
        1,
    )
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_oracle_architecture(mutant)
    assert str(exc_info.value) == "C2B3A_ORACLE_EXPECTED_NOT_LITERAL"


def test_owner_literal_parser_rejects_marker_fence_and_literal_bypasses() -> None:
    text = _read_allowed_text(OWNER_PATH)

    _expect_code = "C2B3A_OWNER_MARKER_INVALID"
    with pytest.raises(_ContractViolation) as exc_info:
        _owner_contract(text.replace(BEGIN_MARKER, "", 1))
    assert str(exc_info.value) == _expect_code

    with pytest.raises(_ContractViolation) as exc_info:
        _owner_contract(text.replace(END_MARKER, BEGIN_MARKER, 1))
    assert str(exc_info.value) == _expect_code

    with pytest.raises(_ContractViolation) as exc_info:
        _owner_contract(text.replace("```python", "```json", 1))
    assert str(exc_info.value) == "C2B3A_OWNER_FENCE_INVALID"

    with pytest.raises(_ContractViolation) as exc_info:
        _owner_contract(text.replace("{\n    \"contract_identity\"", "dict(contract_identity", 1))
    assert str(exc_info.value) == "C2B3A_OWNER_LITERAL_INVALID"


def test_planning_status_baseline_is_exact_closed_projection() -> None:
    planning_document_candidate = _read_allowed_text(PLANNING_PATH)
    assert planning_document_candidate == EXPECTED_PLANNING_PROJECTION
    assert planning_document_candidate.count(PLANNING_PROJECTION_BEGIN_MARKER) == 1
    assert planning_document_candidate.count(PLANNING_PROJECTION_END_MARKER) == 1
    assert planning_document_candidate.endswith(
        PLANNING_PROJECTION_END_MARKER + "\n"
    )
    _validate_planning_status(planning_document_candidate)


def test_planning_projection_closed_grammar_counterfactuals_are_rejected() -> None:
    planning_document_candidate = _read_allowed_text(PLANNING_PATH)
    before_begin = "The earlier manifest governs C2B3B.\n"
    after_end = "One extra path is allowed.\n"
    unrecognized_block = (
        "<!-- C2B3A_PLANNING_UNRECOGNIZED_BEGIN -->\n"
        "The next path requires reassessment.\n"
        "<!-- C2B3A_PLANNING_UNRECOGNIZED_END -->\n"
    )
    swapped = planning_document_candidate.replace(
        PLANNING_PROJECTION_BEGIN_MARKER,
        "__C2B3A_BEGIN__",
        1,
    )
    swapped = swapped.replace(
        PLANNING_PROJECTION_END_MARKER,
        PLANNING_PROJECTION_BEGIN_MARKER,
        1,
    )
    swapped = swapped.replace(
        "__C2B3A_BEGIN__",
        PLANNING_PROJECTION_END_MARKER,
        1,
    )
    for mutant in (
        before_begin + planning_document_candidate,
        planning_document_candidate + after_end,
        planning_document_candidate.replace(
            PLANNING_PROJECTION_END_MARKER,
            unrecognized_block + PLANNING_PROJECTION_END_MARKER,
            1,
        ),
        planning_document_candidate.replace(
            PLANNING_PROJECTION_BEGIN_MARKER,
            PLANNING_PROJECTION_BEGIN_MARKER
            + "\n"
            + PLANNING_PROJECTION_BEGIN_MARKER,
            1,
        ),
        planning_document_candidate.replace(
            PLANNING_PROJECTION_END_MARKER,
            PLANNING_PROJECTION_END_MARKER
            + "\n"
            + PLANNING_PROJECTION_END_MARKER,
            1,
        ),
        planning_document_candidate.replace(
            PLANNING_PROJECTION_BEGIN_MARKER,
            "",
            1,
        ),
        planning_document_candidate.replace(
            PLANNING_PROJECTION_END_MARKER,
            "",
            1,
        ),
        planning_document_candidate.replace(
            "<!-- C2B3A_PLANNING_NON_AUTHORITY_BEGIN -->",
            PLANNING_PROJECTION_BEGIN_MARKER
            + "\n<!-- C2B3A_PLANNING_NON_AUTHORITY_BEGIN -->",
            1,
        ),
        swapped,
        planning_document_candidate
        + "The implementation is limited to the earlier manifest.\n",
        planning_document_candidate + "23 expected paths are operative.\n",
        planning_document_candidate + "24 paths are the maximum.\n",
        planning_document_candidate + "The twenty-fifth path is permitted.\n",
    ):
        with pytest.raises(_ContractViolation) as exc_info:
            _validate_planning_status(mutant)
        assert str(exc_info.value) == "C2B3A_PLANNING_PROJECTION_INVALID"

    stage_specific_mutations = (
        (
            "- a distinct committed Coordinator repository baseline;\n",
            "",
        ),
        (
            "- a refreshed exact Coordinator snapshot, or an explicitly equivalent exact\n"
            "  strategic baseline, produced after and bound to that committed baseline;\n",
            "",
        ),
        (
            "- a refreshed exact Coordinator snapshot, or an explicitly equivalent exact\n",
            "- a refreshed Coordinator snapshot, or an explicitly equivalent strategic\n",
        ),
        (
            "- a distinct committed Coordinator repository baseline;\n"
            "- a refreshed exact Coordinator snapshot, or an explicitly equivalent exact\n"
            "  strategic baseline, produced after and bound to that committed baseline;\n",
            "- one committed Coordinator snapshot or equivalent strategic baseline;\n",
        ),
        (
            "- a distinct committed Coordinator repository baseline;\n"
            "- a refreshed exact Coordinator snapshot, or an explicitly equivalent exact\n"
            "  strategic baseline, produced after and bound to that committed baseline;\n",
            "- one committed Coordinator repository baseline used as both the baseline "
            "and refreshed snapshot;\n",
        ),
        (
            "- an accepted independent audit of the committed C2B3A contract baseline;\n",
            "- an accepted independent audit of the C2B3A contract baseline;\n",
        ),
        (
            "- a committed clean Coordinator baseline;\n",
            "- a Coordinator baseline;\n",
        ),
        (
            "- a committed clean Coordinator baseline;\n",
            "- a committed Coordinator baseline;\n",
        ),
        (
            "- a refreshed exact Coordinator snapshot or explicitly equivalent exact\n",
            "- a refreshed Coordinator snapshot or explicitly equivalent strategic\n",
        ),
        (
            "- a refreshed exact Coordinator snapshot or explicitly equivalent exact\n",
            "- an exact Coordinator snapshot or explicitly equivalent exact\n",
        ),
        (
            "- a refreshed exact Coordinator snapshot or explicitly equivalent exact\n"
            "  strategic baseline bound to that clean committed baseline;\n",
            "- the committed clean Coordinator baseline;\n",
        ),
        ("- an exact C2B3B source implementation prompt;\n", ""),
        ("- fresh opening repository and patch provenance;\n", ""),
    )
    assert len(stage_specific_mutations) == 13
    for old, new in stage_specific_mutations:
        mutant = planning_document_candidate.replace(old, new, 1)
        assert mutant != planning_document_candidate
        with pytest.raises(_ContractViolation) as exc_info:
            _validate_planning_status(mutant)
        assert str(exc_info.value) == "C2B3A_PLANNING_PROJECTION_INVALID"


def test_owner_and_five_path_scope_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    del candidate["owner_decisions"]["route_effect"]
    _expect_violation(candidate, "C2B3A_OWNER_DECISIONS_INVALID")

    candidate = _candidate()
    candidate["owner_decisions"]["unknown_owner_decision"] = True
    _expect_violation(candidate, "C2B3A_OWNER_DECISIONS_INVALID")

    candidate = _candidate()
    candidate["five_path_scope"]["untracked_additions"] += ("sixth-path",)
    candidate["five_path_scope"]["total_paths"] = 6
    _expect_violation(candidate, "C2B3A_WRITE_SCOPE_INVALID")

    candidate = _candidate()
    candidate["five_path_scope"]["production_source_paths"] = ("production-source",)
    _expect_violation(candidate, "C2B3A_WRITE_SCOPE_INVALID")

    candidate = _candidate()
    candidate["five_path_scope"]["migration_paths"] = ("migration",)
    _expect_violation(candidate, "C2B3A_WRITE_SCOPE_INVALID")

    candidate = _candidate()
    candidate["five_path_scope"]["public_api_paths"] = ("public-api",)
    _expect_violation(candidate, "C2B3A_WRITE_SCOPE_INVALID")


def test_genesis_cardinality_and_selection_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["genesis_cardinality"]["work_item_heads"] = 0
    _expect_violation(candidate, "C2B3A_GENESIS_CARDINALITY_INVALID")

    candidate = _candidate()
    candidate["genesis_cardinality"]["work_item_heads"] = 2
    _expect_violation(candidate, "C2B3A_GENESIS_CARDINALITY_INVALID")

    candidate = _candidate()
    candidate["sensitive_ingress"]["work_spec_count"] = 0
    _expect_violation(candidate, "C2B3A_SENSITIVE_INGRESS_INVALID")

    candidate = _candidate()
    candidate["sensitive_ingress"]["work_spec_count"] = 2
    _expect_violation(candidate, "C2B3A_SENSITIVE_INGRESS_INVALID")

    candidate = _candidate()
    candidate["sensitive_ingress"]["container_ingress"] = True
    _expect_violation(candidate, "C2B3A_SENSITIVE_INGRESS_INVALID")

    candidate = _candidate()
    candidate["owner_decisions"]["membership_ordinal"] = 1
    _expect_violation(candidate, "C2B3A_OWNER_DECISIONS_INVALID")

    candidate = _candidate()
    rejects = candidate["safe_command"]["rejects"]
    candidate["safe_command"]["rejects"] = tuple(
        item for item in rejects if item != "caller-supplied membership ordinal"
    )
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    rejects = candidate["safe_command"]["rejects"]
    candidate["safe_command"]["rejects"] = tuple(
        item for item in rejects if item != "implicit sorting"
    )
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")


def test_genesis_decision_selected_and_preassigned_algebra_is_closed() -> None:
    expected_postimage = _candidate()["row_and_head_ledger"]["postimages"][
        "initialize_decision"
    ]

    for field, value in (
        ("selected_semantic_attempt_ref", "semantic-attempt-c2b3a-1"),
        ("selected_candidate_ref", "candidate-c2b3a-1"),
        ("preassigned_semantic_attempt_ref", None),
        ("preassigned_candidate_ref", None),
    ):
        candidate = _candidate()
        postimage = list(expected_postimage)
        position = next(
            index for index, item in enumerate(postimage) if item[0] == field
        )
        postimage[position] = (field, value)
        candidate["row_and_head_ledger"]["postimages"]["initialize_decision"] = tuple(
            postimage
        )
        _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    moved = []
    for field, value in expected_postimage:
        if field == "selected_semantic_attempt_ref":
            value = "exact preassigned_semantic_attempt_ref"
        elif field == "selected_candidate_ref":
            value = "exact preassigned_candidate_ref"
        elif field in {
            "preassigned_semantic_attempt_ref",
            "preassigned_candidate_ref",
        }:
            value = None
        moved.append((field, value))
    candidate["row_and_head_ledger"]["postimages"]["initialize_decision"] = tuple(
        moved
    )
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")


def test_accepted_intent_projection_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["accepted_intent_safe_projection"]["schema_id"] = "wrong"
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")

    candidate = _candidate()
    candidate["accepted_intent_safe_projection"]["digest_domain"] = "wrong"
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")

    candidate = _candidate()
    fields = candidate["accepted_intent_safe_projection"]["ordered_fields"]
    candidate["accepted_intent_safe_projection"]["ordered_fields"] = tuple(
        item for item in fields if item != "source_intent_ref"
    )
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")

    candidate = _candidate()
    candidate["accepted_intent_safe_projection"]["ordered_fields"] += ("objective",)
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")

    candidate = _candidate()
    forbidden = candidate["accepted_intent_safe_projection"]["caller_forbidden"]
    candidate["accepted_intent_safe_projection"]["caller_forbidden"] = tuple(
        item for item in forbidden if item != "safe_projection_digest"
    )
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")

    candidate = _candidate()
    candidate["accepted_intent_safe_projection"]["nested_projection_exact_type"] = "mapping"
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")

    candidate = _candidate()
    candidate["accepted_intent_safe_projection"]["ordered_fields"] += (
        "requirements",
        "exclusions",
    )
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")


def test_safe_command_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["safe_command"]["ordered_fields"] = candidate["safe_command"][
        "ordered_fields"
    ][:-1]
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    candidate["safe_command"]["ordered_fields"] += ("metadata",)
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    fields = list(candidate["safe_command"]["ordered_fields"])
    fields[1], fields[2] = fields[2], fields[1]
    candidate["safe_command"]["ordered_fields"] = tuple(fields)
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    candidate["safe_command"]["schema_id"] = "wrong"
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    candidate["safe_command"]["digest_domain"] = "wrong"
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    field_types = list(candidate["safe_command"]["exact_field_types"])
    field_types[9] = ("coding_global_stop_version", "bool")
    candidate["safe_command"]["exact_field_types"] = tuple(field_types)
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    rejects = candidate["safe_command"]["rejects"]
    candidate["safe_command"]["rejects"] = tuple(
        item for item in rejects if item != "subclasses"
    )
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    rejects = candidate["safe_command"]["rejects"]
    candidate["safe_command"]["rejects"] = tuple(
        item for item in rejects if item != "implicit refs"
    )
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    candidate["safe_command"]["reason_code"] = "initialize"
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    candidate["safe_command"]["identity_excludes"] = ()
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")


def test_row_write_and_graph_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["row_and_head_ledger"]["inserted_rows"] = candidate[
        "row_and_head_ledger"
    ]["inserted_rows"][:-1]
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    candidate["row_and_head_ledger"]["inserted_rows"] += ("extra_row",)
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    candidate["row_and_head_ledger"]["inserted_rows"] += ("revision_edge",)
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    candidate["row_and_head_ledger"]["inserted_rows"] += ("semantic_attempt",)
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    postimage = list(candidate["row_and_head_ledger"]["postimages"]["program_head"])
    postimage[3] = ("program_state", "accepted")
    candidate["row_and_head_ledger"]["postimages"]["program_head"] = tuple(postimage)
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    postimage = list(candidate["row_and_head_ledger"]["postimages"]["work_item_head"])
    postimage[2] = ("head_revision", 1)
    candidate["row_and_head_ledger"]["postimages"]["work_item_head"] = tuple(postimage)
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    order = list(candidate["write_order"]["ordered_rows"])
    order[0], order[1] = order[1], order[0]
    candidate["write_order"]["ordered_rows"] = tuple(order)
    _expect_violation(candidate, "C2B3A_WRITE_ORDER_INVALID")

    candidate = _candidate()
    candidate["initialize_graph"]["receipt_is_entry"] = True
    _expect_violation(candidate, "C2B3A_GRAPH_INVALID")

    candidate = _candidate()
    entries = list(candidate["initialize_graph"]["entries"])
    entries[0] = (0, "wrong_role", 0, "program_ref")
    candidate["initialize_graph"]["entries"] = tuple(entries)
    _expect_violation(candidate, "C2B3A_GRAPH_INVALID")

    candidate = _candidate()
    entries = list(candidate["initialize_graph"]["entries"])
    entries[1] = (2, "accepted_intent_revision", 0, "accepted_intent_revision_ref")
    candidate["initialize_graph"]["entries"] = tuple(entries)
    _expect_violation(candidate, "C2B3A_GRAPH_INVALID")

    candidate = _candidate()
    entries = list(candidate["initialize_graph"]["entries"])
    entries[2] = (2, "initialize_decision", 1, "decision_ref")
    candidate["initialize_graph"]["entries"] = tuple(entries)
    _expect_violation(candidate, "C2B3A_GRAPH_INVALID")

    candidate = _candidate()
    entries = list(candidate["initialize_graph"]["entries"])
    entries[3] = (3, "program_version", 0, "program_ref")
    candidate["initialize_graph"]["entries"] = tuple(entries)
    _expect_violation(candidate, "C2B3A_GRAPH_INVALID")

    candidate = _candidate()
    candidate["initialize_graph"]["entries"] += (
        (8, "coding_global_stop_dependency", 0, "coding_global_stop_ref"),
    )
    _expect_violation(candidate, "C2B3A_GRAPH_INVALID")


def test_locator_result_receipt_and_existing_projection_are_closed() -> None:
    candidate = _candidate()
    candidate["existing_work_spec_safe_projection"]["schema_id"] = "replacement"
    _expect_violation(candidate, "C2B3A_WORK_SPEC_PROJECTION_INVALID")

    candidate = _candidate()
    candidate["complete_graph_locator"]["lookups"] = candidate[
        "complete_graph_locator"
    ]["lookups"][:-1]
    _expect_violation(candidate, "C2B3A_LOCATOR_INVALID")

    candidate = _candidate()
    candidate["complete_graph_locator"]["completeness"] = candidate[
        "complete_graph_locator"
    ]["completeness"][:-1]
    _expect_violation(candidate, "C2B3A_LOCATOR_INVALID")

    candidate = _candidate()
    candidate["persisted_result_projection"]["result_program_version_ref"] = (
        "caller-selected version"
    )
    _expect_violation(candidate, "C2B3A_RESULT_PROJECTION_INVALID")

    candidate = _candidate()
    candidate["private_apply_result"]["dispositions"] += ("unknown",)
    _expect_violation(candidate, "C2B3A_PRIVATE_RESULT_INVALID")

    candidate = _candidate()
    candidate["mutation_receipt"]["self_digest"] = "present"
    _expect_violation(candidate, "C2B3A_RECEIPT_INVALID")


def test_work_spec_locator_exact_ref_relation_and_selection_are_closed() -> None:
    candidate = _candidate()
    candidate["complete_graph_locator"]["lookups"] = tuple(
        lookup.replace(", then exact work_spec_ref equality", "")
        for lookup in candidate["complete_graph_locator"]["lookups"]
    )
    _expect_violation(candidate, "C2B3A_LOCATOR_INVALID")

    candidate = _candidate()
    candidate["complete_graph_locator"]["returned_work_spec_ref_mismatch"] = (
        "select different WorkSpec"
    )
    _expect_violation(candidate, "C2B3A_LOCATOR_INVALID")

    candidate = _candidate()
    candidate["complete_graph_locator"]["forbidden_selection"] = (
        "absence",
        "scan",
    )
    _expect_violation(candidate, "C2B3A_LOCATOR_INVALID")


def test_replay_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    steps = candidate["exact_replay"]["ordered_steps"]
    candidate["exact_replay"]["ordered_steps"] = tuple(
        item for item in steps if item != "locate all eight graph entries"
    )
    _expect_violation(candidate, "C2B3A_REPLAY_INVALID")

    candidate = _candidate()
    steps = list(candidate["exact_replay"]["ordered_steps"])
    steps[2] = "present receipt with different command digest is exact replay"
    candidate["exact_replay"]["ordered_steps"] = tuple(steps)
    _expect_violation(candidate, "C2B3A_REPLAY_INVALID")

    candidate = _candidate()
    candidate["exact_replay"]["incomplete_or_malformed_graph"] = "exact_replay"
    _expect_violation(candidate, "C2B3A_REPLAY_INVALID")

    candidate = _candidate()
    candidate["exact_replay"]["later_valid_head_advancement"] = "replay failure"
    _expect_violation(candidate, "C2B3A_REPLAY_INVALID")

    candidate = _candidate()
    candidate["exact_replay"]["contradictory_same_revision_head"] = "exact_replay"
    _expect_violation(candidate, "C2B3A_REPLAY_INVALID")


def test_commit_recovery_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["commit_outcome_recovery"]["committed_exact_requires"] = (
        "exact receipt",
    )
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"]["committed_exact_requires"] = (
        "both historical head postimages",
    )
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"]["committed_exact_requires"] = (
        "partial graph",
    )
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    absent = candidate["commit_outcome_recovery"][
        "definitely_not_committed_requires_all_absent"
    ]
    candidate["commit_outcome_recovery"][
        "definitely_not_committed_requires_all_absent"
    ] = absent[:-1]
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"][
        "basis_or_global_stop_presence_proves_family_commit"
    ] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"]["automatic_semantic_retry"] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"]["accepts_work_spec"] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"][
        "mutation_slot_available_before_close_completion"
    ] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")


def test_preassigned_attempt_candidate_binding_is_exact_and_cross_related() -> None:
    _assert_preassigned_binding(
        EXPECTED_INITIALIZATION_CONTRACT,
        EXPECTED_INITIALIZATION_GOLDEN_VECTOR,
    )
    owner_contract_candidate = _owner_contract()
    _assert_preassigned_binding(
        owner_contract_candidate,
        EXPECTED_INITIALIZATION_GOLDEN_VECTOR,
    )


def test_preassigned_binding_mutants_b01_through_b08_are_rejected() -> None:
    contract = _candidate()
    cardinality = contract["genesis_cardinality"]
    binding = cardinality.pop(
        "preassigned_attempt_candidate_binding"
    )
    contract["genesis_cardinality"]["selected_attempt_candidate_binding"] = binding
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(contract, _golden_candidate())
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    contract = _candidate()
    relations = list(
        contract["genesis_cardinality"]["preassigned_attempt_candidate_binding"][
            "relations"
        ]
    )
    relations[0] = "selected attempt/candidate binding"
    contract["genesis_cardinality"]["preassigned_attempt_candidate_binding"][
        "relations"
    ] = tuple(relations)
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(contract, _golden_candidate())
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    contract = _candidate()
    relations = list(
        contract["genesis_cardinality"]["preassigned_attempt_candidate_binding"][
            "relations"
        ]
    )
    relations[1] = "bind work revision to selected null refs"
    contract["genesis_cardinality"]["preassigned_attempt_candidate_binding"][
        "relations"
    ] = tuple(relations)
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(contract, _golden_candidate())
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    vector = _golden_candidate()
    vector["safe_command"]["preassigned_semantic_attempt_ref"] = "different-attempt"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(_candidate(), vector)
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    vector = _golden_candidate()
    vector["persisted_rows"]["initialize_decision"][
        "preassigned_candidate_ref"
    ] = "different-candidate"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(_candidate(), vector)
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    vector = _golden_candidate()
    vector["persisted_rows"]["program_version_work_item"][
        "work_item_revision_ref"
    ] = "different-work-revision"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(_candidate(), vector)
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    vector = _golden_candidate()
    vector["persisted_rows"]["initialize_decision"][
        "selected_semantic_attempt_ref"
    ] = "selected-attempt"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(_candidate(), vector)
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    contract = _candidate()
    contract["genesis_cardinality"]["preassigned_attempt_candidate_binding"][
        "future_lineage_only"
    ] = "selected/current/created/authorized"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(contract, _golden_candidate())
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"


def test_original_apply_outcome_and_quarantine_branch_are_exact() -> None:
    _assert_original_apply_outcome(EXPECTED_INITIALIZATION_CONTRACT)
    _assert_original_apply_outcome(_owner_contract())


def test_original_apply_outcome_mutants_u09_through_u14_are_rejected() -> None:
    candidate = _candidate()
    del candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "original_apply_error"
    ]
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_original_apply_outcome(candidate)
    assert str(exc_info.value) == "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID"

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "original_apply_error"
    ]["reason"] = "mutation_failed"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_original_apply_outcome(candidate)
    assert str(exc_info.value) == "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID"

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "original_apply_error"
    ]["context"] = "close failed: private detail"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_original_apply_outcome(candidate)
    assert str(exc_info.value) == "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID"

    candidate = _candidate()
    steps = list(
        candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
            "ordered_steps"
        ]
    )
    steps[5], steps[7] = steps[7], steps[5]
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "ordered_steps"
    ] = tuple(steps)
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_original_apply_outcome(candidate)
    assert str(exc_info.value) == "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID"

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "original_apply_error"
    ]["reason"] = "unresolved"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_original_apply_outcome(candidate)
    assert str(exc_info.value) == "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID"

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "same_session_database_backed_resolver"
    ] = True
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_original_apply_outcome(candidate)
    assert str(exc_info.value) == "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID"


def test_process_control_close_interruption_contract_is_exact() -> None:
    close_not_proved_candidate = _candidate()["commit_uncertainty_cleanup_gate"][
        "close_not_proved"
    ]
    assert close_not_proved_candidate[
        "process_control_close_interruption_ordered_steps"
    ] == (
        "observe the exact process-control exception object from connection close",
        "retain the mutation slot",
        "retain the writer-authority lock",
        "transfer the uncertain raw connection into the private _WriterSessionResource",
        "publish the concrete session as commit-uncertain quarantined",
        "confirm same-session mutation and database-backed recovery remain forbidden",
        "confirm no operation lease, database open, BEGIN, or SQL can occur",
        "re-raise the identical process-control exception object",
    )
    process_control_candidate = close_not_proved_candidate[
        "process_control_exceptions"
    ]
    assert tuple(process_control_candidate) == (
        "KeyboardInterrupt",
        "SystemExit",
        "GeneratorExit",
    )
    assert process_control_candidate["KeyboardInterrupt"] == {
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
    }
    assert process_control_candidate["SystemExit"] == {
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
    }
    assert process_control_candidate["GeneratorExit"] == {
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
    }


def test_process_control_exception_graph_ledger_is_exact() -> None:
    expected_ledger = (
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
    gate = _candidate()["commit_uncertainty_cleanup_gate"]
    assert gate["close_not_proved"][
        "process_control_exception_graph_ledger"
    ] == expected_ledger
    assert gate["process_control_exception_graph_privacy"] == {
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


def test_bare_reraise_reference_model_distinguishes_named_reraise() -> None:
    bare = _bare_reraise_reference(
        KeyboardInterrupt("repair4-bare-reference")
    )
    named = _named_reraise_reference(
        KeyboardInterrupt("repair4-named-reference")
    )
    assert bare["same_exception_object"] is True
    assert bare["caught_traceback_tail_identity_preserved"] is True
    assert bare["repair_owned_traceback_frame_delta"] == 0
    assert bare["caught_signature"] == bare["propagated_signature"]
    assert bare["graph_before"] == (None, None, False, False, None)
    assert bare["graph_after"] == (None, None, False, False, None)
    assert bare["private_material_in_exception_graph"] is False
    assert named["same_exception_object"] is True
    assert named["caught_traceback_tail_identity_preserved"] is False
    assert named["repair_owned_traceback_frame_delta"] == 1
    assert named["caught_signature"] != named["propagated_signature"]


def test_keyboard_interrupt_close_fault_publishes_before_identical_propagation() -> None:
    reference_observation = _bare_reraise_reference(
        KeyboardInterrupt("repair4-keyboard-reference")
    )
    injected_exception = KeyboardInterrupt("repair4-keyboard")
    event_ledger: list[str] = []
    controller_connection_custody = True
    session_resource_connection_custody = False
    mutation_slot_retained = True
    writer_lock_retained = True
    quarantine_published = False
    same_session_mutation_allowed = False
    same_session_database_recovery_allowed = False
    operation_lease_count = 0
    database_open_count = 0
    begin_count = 0
    sql_count = 0
    automatic_semantic_retry_count = 0
    ordinary_store_error = None
    propagation_caught = False
    caught_traceback_tail = None
    caught_traceback_signature: tuple[tuple[int, int, str], ...] = ()
    caught_exception_graph = None

    try:
        try:
            raise injected_exception
        except KeyboardInterrupt as caught_exception:
            event_ledger.append("observe exact close exception")
            assert caught_exception is injected_exception
            caught_traceback_tail = caught_exception.__traceback__
            caught_traceback_signature = _traceback_signature(
                caught_traceback_tail
            )
            caught_exception_graph = _exception_graph_snapshot(
                caught_exception
            )
            event_ledger.append("retain mutation slot")
            assert mutation_slot_retained is True
            event_ledger.append("retain writer-authority lock")
            assert writer_lock_retained is True
            controller_connection_custody = False
            session_resource_connection_custody = True
            event_ledger.append("transfer connection custody")
            quarantine_published = True
            event_ledger.append("publish quarantine")
            event_ledger.append("forbid same-session mutation and recovery")
            assert same_session_mutation_allowed is False
            assert same_session_database_recovery_allowed is False
            event_ledger.append("forbid lease open begin and sql")
            assert (
                operation_lease_count,
                database_open_count,
                begin_count,
                sql_count,
            ) == (0, 0, 0, 0)
            event_ledger.append("re-raise identical exception")
            raise
    except KeyboardInterrupt as propagated_exception:
        propagation_caught = True
        propagated_traceback_signature = _traceback_signature(
            propagated_exception.__traceback__
        )
        assert propagated_exception is injected_exception
        assert type(propagated_exception) is KeyboardInterrupt
        assert propagated_exception.args == ("repair4-keyboard",)
        assert propagated_exception.__traceback__ is caught_traceback_tail
        assert propagated_traceback_signature == caught_traceback_signature
        assert tuple(
            item[1] for item in propagated_traceback_signature
        ) == tuple(item[1] for item in caught_traceback_signature)
        assert tuple(
            item[2] for item in propagated_traceback_signature
        ) == tuple(item[2] for item in caught_traceback_signature)
        assert propagated_traceback_signature[-1] == caught_traceback_signature[-1]
        assert len(propagated_traceback_signature) - len(
            caught_traceback_signature
        ) == 0
        assert caught_exception_graph == (None, None, False, False, None)
        assert _exception_graph_snapshot(propagated_exception) == (
            None,
            None,
            False,
            False,
            None,
        )
        assert (
            _process_control_exception_graph_contains_private_material(
                propagated_exception
            )
            is False
        )
        assert controller_connection_custody is False
        assert session_resource_connection_custody is True
        assert quarantine_published is True
        assert writer_lock_retained is True
        assert mutation_slot_retained is True
        assert ordinary_store_error is None
        assert automatic_semantic_retry_count == 0

    assert propagation_caught is True
    assert reference_observation["same_exception_object"] is True
    assert reference_observation[
        "caught_traceback_tail_identity_preserved"
    ] is True
    assert reference_observation["repair_owned_traceback_frame_delta"] == 0
    assert reference_observation["graph_before"] == (
        None,
        None,
        False,
        False,
        None,
    )
    assert reference_observation["graph_after"] == (
        None,
        None,
        False,
        False,
        None,
    )
    assert tuple(event_ledger) == (
        "observe exact close exception",
        "retain mutation slot",
        "retain writer-authority lock",
        "transfer connection custody",
        "publish quarantine",
        "forbid same-session mutation and recovery",
        "forbid lease open begin and sql",
        "re-raise identical exception",
    )


def test_system_exit_close_fault_publishes_before_identical_propagation() -> None:
    reference_observation = _bare_reraise_reference(SystemExit(43))
    injected_exception = SystemExit(41)
    event_ledger: list[str] = []
    controller_connection_custody = True
    session_resource_connection_custody = False
    mutation_slot_retained = True
    writer_lock_retained = True
    quarantine_published = False
    same_session_mutation_allowed = False
    same_session_database_recovery_allowed = False
    operation_lease_count = 0
    database_open_count = 0
    begin_count = 0
    sql_count = 0
    automatic_semantic_retry_count = 0
    ordinary_store_error = None
    propagation_caught = False
    caught_traceback_tail = None
    caught_traceback_signature: tuple[tuple[int, int, str], ...] = ()
    caught_exception_graph = None

    try:
        try:
            raise injected_exception
        except SystemExit as caught_exception:
            event_ledger.append("observe exact close exception")
            assert caught_exception is injected_exception
            caught_traceback_tail = caught_exception.__traceback__
            caught_traceback_signature = _traceback_signature(
                caught_traceback_tail
            )
            caught_exception_graph = _exception_graph_snapshot(
                caught_exception
            )
            event_ledger.append("retain mutation slot")
            assert mutation_slot_retained is True
            event_ledger.append("retain writer-authority lock")
            assert writer_lock_retained is True
            controller_connection_custody = False
            session_resource_connection_custody = True
            event_ledger.append("transfer connection custody")
            quarantine_published = True
            event_ledger.append("publish quarantine")
            event_ledger.append("forbid same-session mutation and recovery")
            assert same_session_mutation_allowed is False
            assert same_session_database_recovery_allowed is False
            event_ledger.append("forbid lease open begin and sql")
            assert (
                operation_lease_count,
                database_open_count,
                begin_count,
                sql_count,
            ) == (0, 0, 0, 0)
            event_ledger.append("re-raise identical exception")
            raise
    except SystemExit as propagated_exception:
        propagation_caught = True
        propagated_traceback_signature = _traceback_signature(
            propagated_exception.__traceback__
        )
        assert propagated_exception is injected_exception
        assert type(propagated_exception) is SystemExit
        assert propagated_exception.args == (41,)
        assert propagated_exception.code == 41
        assert propagated_exception.__traceback__ is caught_traceback_tail
        assert propagated_traceback_signature == caught_traceback_signature
        assert tuple(
            item[1] for item in propagated_traceback_signature
        ) == tuple(item[1] for item in caught_traceback_signature)
        assert tuple(
            item[2] for item in propagated_traceback_signature
        ) == tuple(item[2] for item in caught_traceback_signature)
        assert propagated_traceback_signature[-1] == caught_traceback_signature[-1]
        assert len(propagated_traceback_signature) - len(
            caught_traceback_signature
        ) == 0
        assert caught_exception_graph == (None, None, False, False, None)
        assert _exception_graph_snapshot(propagated_exception) == (
            None,
            None,
            False,
            False,
            None,
        )
        assert (
            _process_control_exception_graph_contains_private_material(
                propagated_exception
            )
            is False
        )
        assert controller_connection_custody is False
        assert session_resource_connection_custody is True
        assert quarantine_published is True
        assert writer_lock_retained is True
        assert mutation_slot_retained is True
        assert ordinary_store_error is None
        assert automatic_semantic_retry_count == 0

    assert propagation_caught is True
    assert reference_observation["same_exception_object"] is True
    assert reference_observation[
        "caught_traceback_tail_identity_preserved"
    ] is True
    assert reference_observation["repair_owned_traceback_frame_delta"] == 0
    assert reference_observation["graph_before"] == (
        None,
        None,
        False,
        False,
        None,
    )
    assert reference_observation["graph_after"] == (
        None,
        None,
        False,
        False,
        None,
    )
    assert tuple(event_ledger) == (
        "observe exact close exception",
        "retain mutation slot",
        "retain writer-authority lock",
        "transfer connection custody",
        "publish quarantine",
        "forbid same-session mutation and recovery",
        "forbid lease open begin and sql",
        "re-raise identical exception",
    )


def test_generator_exit_close_fault_publishes_before_identical_propagation() -> None:
    reference_observation = _bare_reraise_reference(
        GeneratorExit("repair4-generator-reference")
    )
    injected_exception = GeneratorExit("repair4-generator")
    event_ledger: list[str] = []
    controller_connection_custody = True
    session_resource_connection_custody = False
    mutation_slot_retained = True
    writer_lock_retained = True
    quarantine_published = False
    same_session_mutation_allowed = False
    same_session_database_recovery_allowed = False
    operation_lease_count = 0
    database_open_count = 0
    begin_count = 0
    sql_count = 0
    automatic_semantic_retry_count = 0
    ordinary_store_error = None
    propagation_caught = False
    caught_traceback_tail = None
    caught_traceback_signature: tuple[tuple[int, int, str], ...] = ()
    caught_exception_graph = None

    try:
        try:
            raise injected_exception
        except GeneratorExit as caught_exception:
            event_ledger.append("observe exact close exception")
            assert caught_exception is injected_exception
            caught_traceback_tail = caught_exception.__traceback__
            caught_traceback_signature = _traceback_signature(
                caught_traceback_tail
            )
            caught_exception_graph = _exception_graph_snapshot(
                caught_exception
            )
            event_ledger.append("retain mutation slot")
            assert mutation_slot_retained is True
            event_ledger.append("retain writer-authority lock")
            assert writer_lock_retained is True
            controller_connection_custody = False
            session_resource_connection_custody = True
            event_ledger.append("transfer connection custody")
            quarantine_published = True
            event_ledger.append("publish quarantine")
            event_ledger.append("forbid same-session mutation and recovery")
            assert same_session_mutation_allowed is False
            assert same_session_database_recovery_allowed is False
            event_ledger.append("forbid lease open begin and sql")
            assert (
                operation_lease_count,
                database_open_count,
                begin_count,
                sql_count,
            ) == (0, 0, 0, 0)
            event_ledger.append("re-raise identical exception")
            raise
    except GeneratorExit as propagated_exception:
        propagation_caught = True
        propagated_traceback_signature = _traceback_signature(
            propagated_exception.__traceback__
        )
        assert propagated_exception is injected_exception
        assert type(propagated_exception) is GeneratorExit
        assert propagated_exception.args == ("repair4-generator",)
        assert propagated_exception.__traceback__ is caught_traceback_tail
        assert propagated_traceback_signature == caught_traceback_signature
        assert tuple(
            item[1] for item in propagated_traceback_signature
        ) == tuple(item[1] for item in caught_traceback_signature)
        assert tuple(
            item[2] for item in propagated_traceback_signature
        ) == tuple(item[2] for item in caught_traceback_signature)
        assert propagated_traceback_signature[-1] == caught_traceback_signature[-1]
        assert len(propagated_traceback_signature) - len(
            caught_traceback_signature
        ) == 0
        assert caught_exception_graph == (None, None, False, False, None)
        assert _exception_graph_snapshot(propagated_exception) == (
            None,
            None,
            False,
            False,
            None,
        )
        assert (
            _process_control_exception_graph_contains_private_material(
                propagated_exception
            )
            is False
        )
        assert controller_connection_custody is False
        assert session_resource_connection_custody is True
        assert quarantine_published is True
        assert writer_lock_retained is True
        assert mutation_slot_retained is True
        assert ordinary_store_error is None
        assert automatic_semantic_retry_count == 0

    assert propagation_caught is True
    assert reference_observation["same_exception_object"] is True
    assert reference_observation[
        "caught_traceback_tail_identity_preserved"
    ] is True
    assert reference_observation["repair_owned_traceback_frame_delta"] == 0
    assert reference_observation["graph_before"] == (
        None,
        None,
        False,
        False,
        None,
    )
    assert reference_observation["graph_after"] == (
        None,
        None,
        False,
        False,
        None,
    )
    assert tuple(event_ledger) == (
        "observe exact close exception",
        "retain mutation slot",
        "retain writer-authority lock",
        "transfer connection custody",
        "publish quarantine",
        "forbid same-session mutation and recovery",
        "forbid lease open begin and sql",
        "re-raise identical exception",
    )


def test_future_c2b3b_twenty_four_path_scope_is_exact() -> None:
    _assert_future_c2b3b_scope(EXPECTED_INITIALIZATION_CONTRACT)
    _assert_future_c2b3b_scope(_owner_contract())


def test_future_c2b3b_scope_mutants_s01_through_s07_are_rejected() -> None:
    for omitted in (
        "src/ge_nwp_coordinator/sqlite_writer_session.py",
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "src/ge_nwp_coordinator/sqlite_connection.py",
    ):
        candidate = _candidate()
        scope = candidate["future_c2b3b_maximum_path_scope"]
        scope["production"] = tuple(
            path for path in scope["production"] if path != omitted
        )
        with pytest.raises(_ContractViolation) as exc_info:
            _assert_future_c2b3b_scope(candidate)
        assert str(exc_info.value) == "C2B3A_FUTURE_SCOPE_INVALID"

    candidate = _candidate()
    candidate["future_c2b3b_maximum_path_scope"]["maximum_paths"] = 23
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_future_c2b3b_scope(candidate)
    assert str(exc_info.value) == "C2B3A_FUTURE_SCOPE_INVALID"

    candidate = _candidate()
    scope = candidate["future_c2b3b_maximum_path_scope"]
    scope["tests"] += ("tests/twenty_fifth_path.py",)
    scope["counts"]["tests"] = 11
    scope["counts"]["total"] = 25
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_future_c2b3b_scope(candidate)
    assert str(exc_info.value) == "C2B3A_FUTURE_SCOPE_INVALID"

    candidate = _candidate()
    responsibilities = candidate["future_c2b3b_maximum_path_scope"][
        "production_responsibilities"
    ]
    responsibilities["src/ge_nwp_coordinator/sqlite_writer_session.py"] += (
        "StateStore quarantine or public WriterSession quarantine method",
    )
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_future_c2b3b_scope(candidate)
    assert str(exc_info.value) == "C2B3A_FUTURE_SCOPE_INVALID"

    candidate = _candidate()
    responsibilities = candidate["future_c2b3b_maximum_path_scope"][
        "production_responsibilities"
    ]
    connection_path = "src/ge_nwp_coordinator/sqlite_connection.py"
    responsibilities[connection_path] = tuple(
        item
        for item in responsibilities[connection_path]
        if not item.startswith("cross-thread close")
    )
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_future_c2b3b_scope(candidate)
    assert str(exc_info.value) == "C2B3A_FUTURE_SCOPE_INVALID"


def test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_attempt_precedes"] = (
        "clearing controller connection custody",
    )
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "raw_connection_custody"
    ] = "suppressed close failure and cleared custody"
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "same_session_database_backed_resolver"
    ] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "same_session_resolver_disposition"
    ] = "open SQLite, BEGIN, then classify unresolved"
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "definitely_not_committed"
    ] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "automatic_semantic_retry"
    ] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["caller_authored_clearance"] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["raw_connection_owner_before_close"] = (
        "outside controller and session-resource custody"
    )
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")


def test_stop_conflict_and_receipt_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    precedence = list(candidate["conflict_precedence"]["after_writer_fencing"])
    precedence[0], precedence[3] = precedence[3], precedence[0]
    candidate["conflict_precedence"]["after_writer_fencing"] = tuple(precedence)
    _expect_violation(candidate, "C2B3A_CONFLICT_PRECEDENCE_INVALID")

    candidate = _candidate()
    candidate["conflict_precedence"]["program_head_conflict"] = (
        "genesis collision classification"
    )
    _expect_violation(candidate, "C2B3A_CONFLICT_PRECEDENCE_INVALID")

    candidate = _candidate()
    precedence = list(candidate["conflict_precedence"]["after_writer_fencing"])
    precedence[3], precedence[4] = precedence[4], precedence[3]
    candidate["conflict_precedence"]["after_writer_fencing"] = tuple(precedence)
    _expect_violation(candidate, "C2B3A_CONFLICT_PRECEDENCE_INVALID")

    candidate = _candidate()
    candidate["conflict_precedence"]["failed_fresh_operation_creates_receipt"] = True
    _expect_violation(candidate, "C2B3A_CONFLICT_PRECEDENCE_INVALID")

    candidate = _candidate()
    candidate["conflict_precedence"]["semantic_identity_conflict_visibility"] = "public"
    _expect_violation(candidate, "C2B3A_CONFLICT_PRECEDENCE_INVALID")

    candidate = _candidate()
    candidate["mutation_receipt"]["failed_fresh_receipt"] = True
    _expect_violation(candidate, "C2B3A_RECEIPT_INVALID")


def test_private_conflict_and_recovery_outcome_owners_are_closed() -> None:
    candidate = _candidate()
    candidate["private_outcome_ownership"]["conflict_reason"]["values"] = candidate[
        "private_outcome_ownership"
    ]["conflict_reason"]["values"][:-1]
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")

    candidate = _candidate()
    candidate["private_outcome_ownership"]["conflict_reason"]["values"] += (
        "fifth_conflict",
    )
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")

    candidate = _candidate()
    candidate["private_outcome_ownership"]["public_surfaces_unchanged"] = tuple(
        surface
        for surface in candidate["private_outcome_ownership"][
            "public_surfaces_unchanged"
        ]
        if surface != "models.APPLY_CONFLICT_REASONS"
    )
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")

    candidate = _candidate()
    candidate["private_outcome_ownership"]["public_surfaces_unchanged"] = tuple(
        surface
        for surface in candidate["private_outcome_ownership"][
            "public_surfaces_unchanged"
        ]
        if surface != "sqlite_errors"
    )
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")

    candidate = _candidate()
    candidate["private_outcome_ownership"]["recovery_disposition"][
        "values"
    ] = ("committed_exact", "definitely_not_committed")
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")

    candidate = _candidate()
    candidate["private_outcome_ownership"]["recovery_disposition"]["values"] += (
        "fourth_disposition",
    )
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"]["disposition_owner"] = "unspecified"
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["private_outcome_ownership"]["package_root_export"] = True
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")


def test_privacy_and_custody_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    destinations = candidate["privacy_and_traceback"][
        "complete_work_spec_forbidden_destinations"
    ]
    candidate["privacy_and_traceback"][
        "complete_work_spec_forbidden_destinations"
    ] = tuple(item for item in destinations if item != "SQLite")
    _expect_violation(candidate, "C2B3A_PRIVACY_INVALID")

    candidate = _candidate()
    candidate["safe_command"]["contains_complete_work_spec"] = True
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    for destination in ("receipt", "result", "resolver input"):
        candidate = _candidate()
        destinations = candidate["privacy_and_traceback"][
            "complete_work_spec_forbidden_destinations"
        ]
        candidate["privacy_and_traceback"][
            "complete_work_spec_forbidden_destinations"
        ] = tuple(item for item in destinations if item != destination)
        _expect_violation(candidate, "C2B3A_PRIVACY_INVALID")

    for custody_source in ("chat", "Bridge", "reports"):
        candidate = _candidate()
        sources = candidate["privacy_and_traceback"]["forbidden_custody_sources"]
        candidate["privacy_and_traceback"]["forbidden_custody_sources"] = tuple(
            item for item in sources if item != custody_source
        )
        _expect_violation(candidate, "C2B3A_PRIVACY_INVALID")

    candidate = _candidate()
    candidate["sensitive_ingress"]["restart_safe_retrieval"] = True
    _expect_violation(candidate, "C2B3A_SENSITIVE_INGRESS_INVALID")

    candidate = _candidate()
    candidate["privacy_and_traceback"]["transaction_controller_receives_work_spec"] = True
    _expect_violation(candidate, "C2B3A_PRIVACY_INVALID")


def test_later_author_effect_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["later_author_effect_owner_decisions"]["authority_evaluation"][
        "authority_state"
    ] = "verified"
    _expect_violation(candidate, "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID")

    candidate = _candidate()
    candidate["later_author_effect_owner_decisions"]["authority_evaluation"][
        "semantic_attempt_ref"
    ] = "attempt-ref"
    _expect_violation(candidate, "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID")

    candidate = _candidate()
    candidate["later_author_effect_owner_decisions"][
        "direct_local_bootstrap_selected"
    ] = True
    _expect_violation(candidate, "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID")

    candidate = _candidate()
    candidate["later_author_effect_owner_decisions"][
        "ES_invocation_or_compatibility_claim"
    ] = True
    _expect_violation(candidate, "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID")

    candidate = _candidate()
    candidate["later_author_effect_owner_decisions"]["requirement_provenance"][
        "raw_digest_only_input"
    ] = True
    _expect_violation(candidate, "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID")

    candidate = _candidate()
    candidate["later_author_effect_owner_decisions"]["source_implemented"] = True
    _expect_violation(candidate, "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID")


def test_nonimplementation_surface_is_closed() -> None:
    for key in (
        "program_initialization_source",
        "private_writer_session_methods",
        "sqlite_insert_or_update_execution",
        "mutation_receipt_persistence",
        "production_reader_integration",
        "public_C2B_API",
        "StateStore_widening",
        "WriterSession_public_surface_widening",
        "schema_change",
        "migration_0003_creation",
        "external_IO",
    ):
        candidate = _candidate()
        candidate["nonimplementation"][key] = True
        _expect_violation(candidate, "C2B3A_NONIMPLEMENTATION_INVALID")


def test_commit_close_addendum_direct_oracle_matrix_is_closed() -> None:
    addendum = _owner_contract()["commit_close_outcome_addendum"]
    assert addendum == EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM
    assert tuple(addendum) == (
        "identity",
        "normative_surface_and_precedence",
        "commit_axis",
        "close_axis",
        "process_control_inventory",
        "matrix_identity_overlay",
        "session_state_legend",
        "orthogonal_cleanup_facets",
        "row_field_order",
        "outcome_matrix",
        "controller_and_resource_custody",
        "process_control_relational_policy",
        "legacy_exception_probe_ledger_classification",
        "post_close_cleanup_contract",
        "explicit_disposal",
        "finalizer",
        "recovery_and_safe_command_custody",
        "future_c2b3b_path_scope_status",
        "direct_oracle_requirements",
        "privacy_and_non_authority",
        "nonimplementation",
    )
    assert addendum["commit_axis"] == (
        ("C1", "COMMIT returns normally"),
        ("C2", "COMMIT raises an ordinary SQLite exception"),
        ("C3", "COMMIT raises another ordinary Exception"),
        ("C4", "COMMIT raises KeyboardInterrupt"),
        ("C5", "COMMIT raises SystemExit"),
        ("C6", "COMMIT raises GeneratorExit"),
    )
    assert addendum["close_axis"] == (
        ("K1", "close returns normally and closure is proved"),
        ("K2", "close raises an ordinary SQLite exception"),
        ("K3", "close raises another ordinary Exception"),
        ("K4", "close raises KeyboardInterrupt"),
        ("K5", "close raises SystemExit"),
        ("K6", "close raises GeneratorExit"),
    )
    assert addendum["row_field_order"] == (
        "row_id",
        "commit_axis_id",
        "close_axis_id",
        "known_commit_state",
        "outward_result_or_exception",
        "outward_identity_requirements",
        "raise_form",
        "repair_owned_propagation_frame_delta",
        "cause_context_suppression_notes",
        "raw_connection_disposition",
        "raw_connection_owner",
        "controller_state",
        "session_state",
        "mutation_slot_disposition",
        "operation_lease_completion",
        "writer_lock_disposition",
        "quarantine_publication",
        "new_operation_admission",
        "committed_result_delivered",
        "permitted_recovery_or_replay",
        "automatic_semantic_retry",
        "rollback_after_commit_start",
        "secondary_failure_posture",
        "C2B3_private_material_added_or_copied_outward",
    )
    matrix = addendum["outcome_matrix"]
    assert type(matrix) is tuple
    assert len(matrix) == 36
    assert tuple(row[0] for row in matrix) == (
        "C1K1", "C1K2", "C1K3", "C1K4", "C1K5", "C1K6",
        "C2K1", "C2K2", "C2K3", "C2K4", "C2K5", "C2K6",
        "C3K1", "C3K2", "C3K3", "C3K4", "C3K5", "C3K6",
        "C4K1", "C4K2", "C4K3", "C4K4", "C4K5", "C4K6",
        "C5K1", "C5K2", "C5K3", "C5K4", "C5K5", "C5K6",
        "C6K1", "C6K2", "C6K3", "C6K4", "C6K5", "C6K6",
    )
    assert len(set(row[0] for row in matrix)) == 36
    assert all(type(row) is tuple for row in matrix)
    assert all(len(row) == 24 for row in matrix)
    assert addendum["matrix_identity_overlay"] == {
        "matrix_axes": "exception types only; object identity is orthogonal",
        "different_exact_classes": "necessarily distinct objects",
        "diagonal_rows": ("C4K4", "C5K5", "C6K6"),
        "diagonal_discriminator": "same_instance iff commit_exception is cleanup_exception; otherwise distinct_instance",
        "same_exact_class_implies_same_object": False,
        "additional_cartesian_axis": False,
        "dynamic_generation": False,
    }
    assert all(
        "dispatch by object identity" in matrix[index][8]
        for index in (21, 28, 35)
    )
    assert all(
        "object-identity discriminator" in matrix[index][22]
        for index in (21, 28, 35)
    )
    assert matrix[6][12] == "A" and matrix[12][12] == "A"
    assert "ordinary A -> X" in matrix[6][17]
    assert "ordinary A -> X" in matrix[12][17]


def test_commit_close_addendum_custody_recovery_and_scope_are_exact() -> None:
    addendum = deepcopy(EXPECTED_COMMIT_CLOSE_OUTCOME_ADDENDUM)
    matrix = addendum["outcome_matrix"]
    assert matrix[1][12] == "QK"
    assert matrix[7][12] == "QU"
    assert all(matrix[index][12] == "PU" for index in (18, 24, 30))
    assert all(row[20] is False and row[21] is False for row in matrix)
    assert tuple(
        matrix[index][4]
        for index in (21, 22, 23, 27, 28, 29, 33, 34, 35)
    ) == (
        "propagate original COMMIT-time KeyboardInterrupt",
        "propagate original COMMIT-time KeyboardInterrupt",
        "propagate original COMMIT-time KeyboardInterrupt",
        "propagate original COMMIT-time SystemExit",
        "propagate original COMMIT-time SystemExit",
        "propagate original COMMIT-time SystemExit",
        "propagate original COMMIT-time GeneratorExit",
        "propagate original COMMIT-time GeneratorExit",
        "propagate original COMMIT-time GeneratorExit",
    )
    assert addendum["orthogonal_cleanup_facets"] == {
        "writer_lock_release": (
            "not_attempted",
            "release_unproved",
            "release_proved",
        ),
        "descriptor_outcome": (
            "not_attempted",
            "reclaimed",
            "reclamation_unknown",
        ),
        "finalizer_liveness": (
            "finalizer_attempted",
            "retry_reachable",
        ),
        "wrapper_loss_after_failed_one_shot_finalizer": {
            "finalizer_attempted": True,
            "retry_reachable": False,
        },
        "X_requires_descriptor_reclaimed": False,
        "X_requires_post_X_session_registry_removal": False,
        "CLEANING": "transient single-owner execution condition; never stable custody state",
    }
    cleanup = addendum["post_close_cleanup_contract"]
    assert cleanup["ordered_steps"] == (
        "P0", "C1", "C2", "R1", "R2", "R3", "L1", "H1", "H2", "T1", "H3",
    )
    assert cleanup["acknowledgement_complete_boundary"] == {
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
    }
    assert tuple(cleanup["step_contracts"]) == cleanup["ordered_steps"]
    assert cleanup["step_contracts"]["L1"]["proof"] == (
        "normal return from real fcntl.flock(exact_retained_fd, LOCK_UN), then release_proved publication under lifecycle/fork gate"
    )
    assert cleanup["step_contracts"]["L1"]["every_non_normal_exit"] == "release_unproved"
    assert cleanup["step_contracts"]["H1"]["writer_lock_release_proof"] is False
    assert cleanup["step_contracts"]["H1"]["retry_numeric_fd"] is False
    assert cleanup["step_contracts"]["H1"]["gates_X"] is False
    assert cleanup["step_contracts"]["H2"]["under_lifecycle_fork_gate_order"] == (
        "publish release-proved terminal facts and descriptor outcome",
        "identity-check and remove exact _ACTIVE_LOCK_RESOURCES entry",
    )
    assert cleanup["step_contracts"]["T1"]["writer_session_registry_retained_through_X"] is True
    assert cleanup["step_contracts"]["H3"]["precondition"] == "X"
    assert cleanup["matrix_continuation"] == {
        "direct_entry_rows": ("C4K1", "C5K1", "C6K1"),
        "entry_state": "PU after C2 before residual cleanup",
        "possible_propagation_states": ("PU", "X"),
        "C2K1_C3K1_state": "A",
        "C2K1_C3K1_later_route": "ordinary A -> X through P0/R1/R2/R3/L1/H1/H2/T1/H3",
        "remaining_close_failure_rows": "QU or QK until a later C1/C2 continuation",
    }
    relational = addendum["process_control_relational_policy"]
    assert relational["guarantee_scope"] == "C2B3 deliberate actions only"
    assert relational["exact_before_after_graph_reachability_cycle_or_traceback_promise"] is False
    assert relational["exact_interpreter_preservation_guaranteed"] is False
    assert relational["distinct_graph_disjoint"]["exact_full_graph_shape_promised"] is False
    assert relational["distinct_prelinked"]["exact_link_preservation_promised"] is False
    assert relational["same_instance"]["distinct_secondary_exists"] is False
    assert relational["same_instance"]["exact_pre_second_raise_traceback_or_complete_graph_restored"] is False
    assert relational["preexisting_private_payload"]["universal_sanitization_claim"] is False
    assert addendum["legacy_exception_probe_ledger_classification"] == {
        "ledger_path": "commit_uncertainty_cleanup_gate.close_not_proved.process_control_exception_graph_ledger",
        "classification": "historical_runtime_observation",
        "normative": False,
        "operative_for_c2b3b": False,
        "portable_contract": False,
        "preserved_for_original_c2b3a_evidence": True,
        "superseded_for_target_semantics_by": "process_control_relational_policy",
        "observed_values_scope": "exact traceback, cause, context, suppression, cycle, and reachability values are observations of the original bounded reference branch only",
        "consumer_rule": "no implementation, test oracle, planning projection, or future prompt may use those observed values as target requirements",
    }
    assert addendum["explicit_disposal"]["applies_to"] == ("A", "QU", "QK", "PU", "PK")
    assert addendum["explicit_disposal"]["uses_weakref_finalize_callback_as_retry_mechanism"] is False
    assert addendum["finalizer"]["weakref_finalize_invocation"] == "one-shot"
    assert addendum["finalizer"]["failure_before_X_after_wrapper_loss"] == {
        "finalizer_attempted": True,
        "retry_reachable": False,
        "further_in_process_attempt_promised": False,
        "posture": "truthful fail-closed state and progress until process termination",
    }
    scope = addendum["future_c2b3b_path_scope_status"]
    assert scope["required_path_counts"] == (6, 10, 11)
    assert scope["expected_actual_write_paths"] == 27
    assert scope["maximum_paths"] == 28
    assert scope["twenty_ninth_path"] == "hard stop and scope reassessment condition"
    assert len(scope["required_production_paths"]) == 6
    assert len(scope["required_documentation_status_paths"]) == 10
    assert len(scope["required_changed_test_paths"]) == 11
    assert scope["contingency_path"] == "tests/test_c2b2_private_development_readers.py"
    assert scope["future_implementation_scope_supersession"] == {
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
    }


def _process_control_reference_cases() -> tuple[
    tuple[str, BaseException, BaseException], ...
]:
    same_k = KeyboardInterrupt("same-instance-k")
    same_s = SystemExit(37)
    same_g = GeneratorExit("same-instance-g")

    cause_secondary = GeneratorExit("cause-secondary")
    cause_primary = SystemExit(38)
    cause_primary.__cause__ = cause_secondary

    context_secondary = KeyboardInterrupt("context-secondary")
    context_primary = GeneratorExit("context-primary")
    context_primary.__context__ = context_secondary

    third = KeyboardInterrupt("third")
    cycle_primary = SystemExit(39)
    cycle_secondary = GeneratorExit("cycle-secondary")
    cycle_primary.__cause__ = third
    third.__context__ = cycle_primary
    cycle_secondary.__context__ = third

    opaque_payload = ("opaque-synthetic-payload", 40)
    payload_primary = SystemExit(opaque_payload)
    payload_secondary = KeyboardInterrupt(opaque_payload)
    payload_cause = GeneratorExit(opaque_payload)
    payload_context = KeyboardInterrupt(opaque_payload)
    payload_primary.__notes__ = [opaque_payload]
    payload_primary.__cause__ = payload_cause
    payload_secondary.__context__ = payload_context

    return (
        ("cross-k-s", KeyboardInterrupt("cross-k-s"), SystemExit(31)),
        ("cross-k-g", KeyboardInterrupt("cross-k-g"), GeneratorExit("cross-g")),
        ("cross-s-k", SystemExit(32), KeyboardInterrupt("cross-s-k")),
        ("cross-s-g", SystemExit(33), GeneratorExit("cross-s-g")),
        ("cross-g-k", GeneratorExit("cross-g-k"), KeyboardInterrupt("cross-k")),
        ("cross-g-s", GeneratorExit("cross-g-s"), SystemExit(34)),
        (
            "distinct-k",
            KeyboardInterrupt("same-class-k-1"),
            KeyboardInterrupt("same-class-k-2"),
        ),
        ("distinct-s", SystemExit(35), SystemExit(36)),
        (
            "distinct-g",
            GeneratorExit("same-class-g-1"),
            GeneratorExit("same-class-g-2"),
        ),
        ("same-k", same_k, same_k),
        ("same-s", same_s, same_s),
        ("same-g", same_g, same_g),
        ("prelinked-cause", cause_primary, cause_secondary),
        ("prelinked-context", context_primary, context_secondary),
        ("linked-cycle", cycle_primary, cycle_secondary),
        ("private-payload", payload_primary, payload_secondary),
    )


def test_process_control_reference_case_fixture_is_closed_and_privacy_safe() -> None:
    cases = _process_control_reference_cases()
    by_id = {
        case_id: (primary, secondary)
        for case_id, primary, secondary in cases
    }
    assert tuple(by_id) == tuple(EXPECTED_PROCESS_CONTROL_REFERENCE_CASES)

    cause_primary, cause_secondary = by_id["prelinked-cause"]
    context_primary, context_secondary = by_id["prelinked-context"]
    cycle_primary, cycle_secondary = by_id["linked-cycle"]
    payload_primary, payload_secondary = by_id["private-payload"]
    third = cycle_primary.__cause__
    payload_cause = payload_primary.__cause__
    payload_context = payload_secondary.__context__
    opaque_payload = ("opaque-synthetic-payload", 40)

    assert cause_primary.__cause__ is cause_secondary
    assert context_primary.__context__ is context_secondary
    assert cycle_primary.__cause__ is third
    assert third is not None
    assert third.__context__ is cycle_primary
    assert cycle_secondary.__context__ is third
    identity_walk = _exception_graph_identity_walk(cycle_primary)
    assert id(cycle_primary) in identity_walk
    assert id(third) in identity_walk
    assert payload_primary.__notes__ == [opaque_payload]
    assert payload_primary.__cause__ is payload_cause
    assert payload_secondary.__context__ is payload_context

    coordinator_safe_error = ("commit_outcome_unknown", None, True)
    coordinator_logs: tuple[object, ...] = ()
    coordinator_reports: tuple[object, ...] = ()
    coordinator_serialized_values: tuple[object, ...] = ()
    coordinator_persisted_values: tuple[object, ...] = ()
    assert opaque_payload not in coordinator_safe_error
    assert opaque_payload not in coordinator_logs
    assert opaque_payload not in coordinator_reports
    assert opaque_payload not in coordinator_serialized_values
    assert opaque_payload not in coordinator_persisted_values


def test_commit_close_relational_process_control_reference_cases_are_exact() -> None:
    cases = _process_control_reference_cases()
    assert tuple(case_id for case_id, _, _ in cases) == tuple(
        EXPECTED_PROCESS_CONTROL_REFERENCE_CASES
    )

    for case_id, primary, secondary in cases:
        observed = _relational_process_control_reference(primary, secondary)
        expected = EXPECTED_PROCESS_CONTROL_REFERENCE_CASES[case_id]
        assert observed["safe_projection"] == expected
        assert observed["provided_primary"] is primary
        assert observed["provided_secondary"] is secondary
        assert observed["caught_primary"] is primary
        assert observed["caught_secondary"] is secondary
        assert observed["outward_primary"] is primary


def test_cleanup_reference_vector_shape_is_exact() -> None:
    assert len(CLEANUP_REFERENCE_INPUT_CASES) == 55
    assert len(EXPECTED_CLEANUP_REFERENCE_CASES) == 55
    assert tuple(
        case_id for case_id, _ in CLEANUP_REFERENCE_INPUT_CASES
    ) == tuple(EXPECTED_CLEANUP_REFERENCE_CASES)
    assert len(set(EXPECTED_CLEANUP_REFERENCE_CASES)) == 55
    assert len(CLEANUP_SAFE_PROJECTION_FIELDS) == 30


def test_post_close_cleanup_reference_model_covers_every_release_point() -> None:
    cases = CLEANUP_REFERENCE_INPUT_CASES
    assert tuple(case_id for case_id, _ in cases) == tuple(
        EXPECTED_CLEANUP_REFERENCE_CASES
    )
    for case_id, inputs in cases:
        observed = _cleanup_reference(*inputs)
        expected = EXPECTED_CLEANUP_REFERENCE_CASES[case_id]
        assert observed == expected



def test_commit_close_mutant_m16_missing_matrix_row_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["outcome_matrix"] = candidate["commit_close_outcome_addendum"]["outcome_matrix"][:-1]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m17_duplicate_matrix_row_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["outcome_matrix"] = candidate["commit_close_outcome_addendum"]["outcome_matrix"][:-1] + (candidate["commit_close_outcome_addendum"]["outcome_matrix"][0],)
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m18_reordered_matrix_rows_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["outcome_matrix"] = (candidate["commit_close_outcome_addendum"]["outcome_matrix"][1], candidate["commit_close_outcome_addendum"]["outcome_matrix"][0]) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][2:]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m19_c1k2_state_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["outcome_matrix"] = candidate["commit_close_outcome_addendum"]["outcome_matrix"][:1] + (candidate["commit_close_outcome_addendum"]["outcome_matrix"][1][:12] + ("QU",) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][1][13:],) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][2:]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m20_c4k1_state_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["outcome_matrix"] = candidate["commit_close_outcome_addendum"]["outcome_matrix"][:18] + (candidate["commit_close_outcome_addendum"]["outcome_matrix"][18][:12] + ("A",) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][18][13:],) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][19:]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m21_cleanup_primary_precedence_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["outcome_matrix"] = candidate["commit_close_outcome_addendum"]["outcome_matrix"][:21] + (candidate["commit_close_outcome_addendum"]["outcome_matrix"][21][:4] + ("propagate close-time KeyboardInterrupt",) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][21][5:],) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][22:]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m22_named_raise_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["outcome_matrix"] = candidate["commit_close_outcome_addendum"]["outcome_matrix"][:3] + (candidate["commit_close_outcome_addendum"]["outcome_matrix"][3][:6] + ("raise caught_exception",) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][3][7:],) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][4:]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m23_reconstructed_system_exit_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["outcome_matrix"] = candidate["commit_close_outcome_addendum"]["outcome_matrix"][:4] + (candidate["commit_close_outcome_addendum"]["outcome_matrix"][4][:5] + ("reconstructed SystemExit with normalized code",) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][4][6:],) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][5:]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m24_post_commit_rollback_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["outcome_matrix"] = candidate["commit_close_outcome_addendum"]["outcome_matrix"][:6] + (candidate["commit_close_outcome_addendum"]["outcome_matrix"][6][:20] + (True,) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][6][21:],) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][7:]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m25_slot_release_before_quarantine_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["outcome_matrix"] = candidate["commit_close_outcome_addendum"]["outcome_matrix"][:7] + (candidate["commit_close_outcome_addendum"]["outcome_matrix"][7][:13] + ("released before quarantine publication",) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][7][14:],) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][8:]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m26_pending_cleanup_sql_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["explicit_disposal"]["while_PU_or_PK"] = "recreate connection and run SQL"
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m27_finalizer_retry_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["finalizer"]["weakref_finalize_invocation"] = "repeatable"
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m28_work_spec_recovery_custody_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["recovery_and_safe_command_custody"]["complete_work_spec_reaches_recovery"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m29_production_behavior_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["nonimplementation"]["worker_scheduler_queue_service_model_or_reconciler"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m30_scope_maximum_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["maximum_paths"] = 29
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m31_same_class_implies_same_object_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["matrix_identity_overlay"]["same_exact_class_implies_same_object"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m32_distinct_same_class_routing_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["matrix_identity_overlay"]["diagonal_discriminator"] = "same exact class always selects same_instance"
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m33_same_instance_routing_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["process_control_relational_policy"]["same_instance"]["selection"] = "always distinct_instance"
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m34_prelinked_cause_promise_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["process_control_relational_policy"]["distinct_prelinked"]["exact_link_preservation_promised"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m35_prelinked_context_promise_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["process_control_relational_policy"]["exact_interpreter_preservation_guaranteed"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m36_fixed_graph_shape_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["process_control_relational_policy"]["exact_before_after_graph_reachability_cycle_or_traceback_promise"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m37_graph_scrub_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["process_control_relational_policy"]["preexisting_relation_deliberately_removed"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m38_universal_sanitization_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["process_control_relational_policy"]["preexisting_private_payload"]["universal_sanitization_claim"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m39_raw_payload_copy_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["process_control_relational_policy"]["preexisting_private_payload"]["copied_or_added_by_C2B3"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m40_raw_payload_report_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["process_control_relational_policy"]["raw_process_control"]["serialize_persist_log_format_render_or_report"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m41_descriptor_close_release_proof_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["post_close_cleanup_contract"]["step_contracts"]["L1"]["proof"] = "normal descriptor close return"
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m42_x_before_release_proof_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["post_close_cleanup_contract"]["step_contracts"]["T1"]["preconditions"] = ("applicable C2", "R1", "R2", "R3")
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m43_authority_registry_before_release_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["post_close_cleanup_contract"]["step_contracts"]["H2"]["preconditions"] = ("one H1 attempt",)
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m44_acquisition_on_unproved_release_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["post_close_cleanup_contract"]["step_contracts"]["H2"]["same_process_acquisition"] = "permitted while release_unproved"
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m45_recovery_on_unproved_release_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["post_close_cleanup_contract"]["recovery_replay_gate"]["blocked_lock_facet"] = None
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m46_replay_on_unproved_release_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["post_close_cleanup_contract"]["step_contracts"]["L1"]["release_unproved_forbids"] = ("descriptor close", "X publication", "new same-process writer")
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m47_descriptor_close_retry_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["post_close_cleanup_contract"]["step_contracts"]["H1"]["retry_numeric_fd"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m48_session_registry_before_x_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["post_close_cleanup_contract"]["step_contracts"]["H3"]["precondition"] = "PU or PK"
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m49_descriptor_reclamation_x_gate_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["orthogonal_cleanup_facets"]["X_requires_descriptor_reclaimed"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m50_retry_after_wrapper_loss_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["finalizer"]["failure_before_X_after_wrapper_loss"]["retry_reachable"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m51_hidden_registry_cleanup_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["finalizer"]["hidden_cleanup_service_or_registry_scan"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m52_c2k1_pending_state_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["outcome_matrix"] = candidate["commit_close_outcome_addendum"]["outcome_matrix"][:6] + (candidate["commit_close_outcome_addendum"]["outcome_matrix"][6][:12] + ("PU",) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][6][13:],) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][7:]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m53_c3k1_pending_state_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["outcome_matrix"] = candidate["commit_close_outcome_addendum"]["outcome_matrix"][:12] + (candidate["commit_close_outcome_addendum"]["outcome_matrix"][12][:12] + ("PK",) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][12][13:],) + candidate["commit_close_outcome_addendum"]["outcome_matrix"][13:]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m54_a_to_x_lock_bypass_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["post_close_cleanup_contract"]["ordinary_A_to_X"]["shared_lock_release_primitive"] = False
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m55_finalizer_automatic_retry_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["finalizer"]["automatic_retry"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m56_finalizer_clears_progress_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["finalizer"]["failure_after_close_proof"] = "clear every incomplete responsibility"
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m57_missing_lock_source_path_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["required_production_paths"] = candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["required_production_paths"][:5]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m58_missing_writer_authority_doc_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["required_documentation_status_paths"] = candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["required_documentation_status_paths"][:7] + candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["required_documentation_status_paths"][8:]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m59_missing_lock_test_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["required_changed_test_paths"] = candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["required_changed_test_paths"][:7] + candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["required_changed_test_paths"][8:]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m60_missing_writer_session_test_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["required_changed_test_paths"] = candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["required_changed_test_paths"][:6] + candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["required_changed_test_paths"][7:]
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m61_historical_scope_reactivation_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["expected_actual_write_paths"] = 23
    candidate["commit_close_outcome_addendum"]["future_c2b3b_path_scope_status"]["maximum_paths"] = 24
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m62_dynamic_oracle_derivation_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["matrix_identity_overlay"]["dynamic_generation"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m63_implementation_claim_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["nonimplementation"]["production_behavior"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m64_h2_order_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["post_close_cleanup_contract"]["step_contracts"]["H2"]["under_lifecycle_fork_gate_order"] = ("identity-check and remove exact _ACTIVE_LOCK_RESOURCES entry", "publish release-proved terminal facts and descriptor outcome")
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")


def test_commit_close_mutant_m65_new_operation_in_pending_state_is_rejected() -> None:
    candidate = _candidate()
    candidate["commit_close_outcome_addendum"]["post_close_cleanup_contract"]["step_contracts"]["P0"]["new_operation_admission_in_PU_or_PK"] = True
    _expect_violation(candidate, "C2B3A_COMMIT_CLOSE_ADDENDUM_INVALID")
