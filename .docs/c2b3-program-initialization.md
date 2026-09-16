# C2B3 Program Initialization

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
<!-- COORDINATOR_VS1B_IMPLEMENTED_CURRENT_STATUS_BEGIN -->
## VS1B implemented current status

The preceding C2B3A projection is retained as historical contract and planning evidence.
Its internal “Current status,” source-absence, candidate-scope, and
future-C2B3B statements are not current implementation claims after this
addendum. VS1A is committed at
`4ffbc5f8881339dce210a50b05200e3f8e837284`. VS1B is the current committed
private implementation at `327aa4ef6f043a94f700374546fedc456027ae83` and is
pushed to the directly verified `origin/trunk_dev` ref. The exact VS1B
pre-commit candidate received externally classified, provenance-bound
independent acceptance and its post-acceptance commit gate passed. Git owns the
commit/ref fact; the audit and validation reports remain external evidence rather than
Coordinator durable authority. Section 38 of
`.docs/c2b-durable-development-state.md` owns the private VS1B route-neutral,
single-work-item program-genesis implementation.

VS1B uses the generation-2 migration-0002 schema, the existing writer
operation guard and shared mutation slot, the existing transaction controller,
receipt-first exact replay, and read-only three-way recovery. Successful
acquisition and fencing of a fresh concrete writer session—not proof of the old resource's T1/X state—is the
cross-session recovery and replay gate. The
old session remains non-admitting and unusable. Same-process acquisition may
begin after H2 and before old T1; a different process may acquire after L1
kernel-lock release and before the old process reaches H2 or T1.

Historical replay and committed recovery continue to reconstruct the original
genesis result and eight-entry receipt graph from the immutable genesis-family
evidence. A later mutable program or work-item head is accepted only when the
immutable row named by its current ref exists exactly once, validates, belongs
to the same program and work-item owner, and carries exactly the current number
claimed by the head. The advanced current head does not replace its genesis
postimage in the historical graph. A contradictory current relation is the
existing content-free `database_integrity_failure` for apply and `unresolved`
for recovery. Separately supplied scalar refs are exactly validated before any
comparison with transient `WorkSpecV1` values.

The implementation adds no public API or package export, no schema or
migration, no route, adapter, external I/O, worker, attempt, effect, delivery,
candidate, capsule, Git effect, bootstrap latch, or automatic semantic retry.
Raw `WorkSpecV1` is transient only in the sensitive reducer. A separately
reconstructed exact safe command is accepted, but restart-safe command custody
or reconstruction remains unimplemented. Section 39 of
`.docs/c2b-durable-development-state.md` supersedes current status only and
owns the accepted-target C2B3C author-effect contract freeze. C2B3C is currently
an uncommitted contract-freeze candidate awaiting fresh independent re-audit.
C2B3D source, worker execution, and production or external effects remain
unauthorized.
<!-- COORDINATOR_VS1B_IMPLEMENTED_CURRENT_STATUS_END -->
<!-- COORDINATOR_C2B3D_IMPLEMENTED_CANDIDATE_CURRENT_STATUS_BEGIN -->
## C2B3D implemented-candidate current status

The preceding VS1B block is retained byte-for-byte as historical status
evidence. Its concluding C2B3C pending/uncommitted wording and C2B3D
source-absence statement are not current implementation claims after this
separately bounded block. The C2B3C contract freeze is a Git fact at commit
`5945a53685e7a5cb4edd7419bea712007fcdfcd1`, tree
`ce7a85c612a76dfb1f0ff1e463b3b624bdce69e3`, with parent
`327aa4ef6f043a94f700374546fedc456027ae83`.

The current working tree contains a private C2B3D author-effect establishment
implementation candidate governed by Sections 39 and 40 of
`.docs/c2b-durable-development-state.md`. It reduces transient exact
`WorkSpecV1` and typed requirement/authority evidence to a closed safe command
before entering the existing writer operation guard, shared mutation slot, and
single transaction controller. A fresh establishment persists exactly ten rows
whose receipt graph has nine entries, makes exactly one COMMIT attempt, and
supports receipt-first exact replay plus explicit three-way readback recovery.
Apply and recovery verify the complete immutable original family and bounded
current effect/delivery-head coherence. The complete set of twelve existing
C2B2 private reader roles now has this bounded private caller; the receipt
reader also retains its VS1B caller. The frozen twenty-four-query reader
inventory is unchanged. C2B3D's exact family-row locators and collision probes
are family-local private queries outside that inventory.

This candidate adds no public API or package export, schema or migration,
worker or dispatcher, external-authority issuer or verifier, route execution,
credential use, capsule custody, Git effect, Execution Substrate or Bridge
call, network or other external I/O, automatic retry after uncertainty, or
restart-safe raw-input custody. Pending authority and planned delivery remain
durable intent and bounds only, never execution permission. The candidate is
not staged, committed, pushed, published, or independently accepted; a fresh
independent audit remains required.
<!-- COORDINATOR_C2B3D_IMPLEMENTED_CANDIDATE_CURRENT_STATUS_END -->
<!-- COORDINATOR_C2B3D_COMMITTED_CURRENT_STATUS_BEGIN -->
## C2B3D committed current status

The preceding planning, VS1B, and C2B3D implemented-candidate blocks are
retained byte-for-byte as historical contract, implementation, and audit-state
evidence. Their former current-working-tree, candidate, uncommitted,
unpublished, and pending-audit labels are not current repository status after
this successor.

C2B3D private author-effect establishment was introduced and is committed at
`5e544622e5f46ddc78294322471b4fcbd2ad9172`. Git owns the committed object and
ref fact. Independent acceptance, audit, validation, provenance, and report
records remain external evidence only rather than Coordinator durable authority
or effect permission.

C2B3D remains private and non-executing. It adds no public API or package
export, schema or migration, worker or dispatcher, external-authority issuer or
verifier, route execution, credential use, capsule custody, Git effect,
Execution Substrate or Bridge call, network or other external I/O, automatic
retry after uncertainty, or restart-safe raw-input custody. Pending authority
and planned delivery remain durable intent and bounds only, never execution
permission.

<!-- COORDINATOR_C2B3D_COMMITTED_CURRENT_STATUS_END -->
