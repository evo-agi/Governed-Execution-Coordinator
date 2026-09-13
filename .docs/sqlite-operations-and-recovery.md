# SQLite Operations And Recovery

Status: C2B1 bounded migration administration over the B1/B1.1/B2b
bootstrap/inspection/validation and shared state-authority advisory-lock
foundation.
B2c adds durable writer issuance and internal writer-session acquisition. B3a
adds contract-only future transition persistence rules. B3c1b adds private
rollback-only writer fencing with no public mutation runtime. B3c4b adds
private atomic transition persistence with commit uncertainty handling, B3c4c
adds public transition delegation, B4b adds private global-stop persistence,
and B4c adds guarded public global-stop delegation. Receipt provisioning remains
separate, and no worker, service, scheduler, orchestration, publication, or
cross-repository authority exists.

C2B Pre-I/O VS1A adds private interruption-safe cleanup continuation without
changing the commit-resolution vocabulary or retry contract. The controller
constructs the sole active connection scope before resource publication. The
resource acknowledges that exact scope token before COMMIT. After close, the
controller supplies immutable facts only. Under the existing writer-resource
lock, the resource observes current disposal posture, merges cleanup-wins
policy, selects the actual successor, and publishes it through one lifecycle-
state assignment. Controller aliases clear only after the exact publication
acknowledgment; scope use is already invalid after assignment. `QK` preserves
known commit success and `QU` preserves uncertainty; both retain the exact
unproved connection and slot and reject new operations.

Normal return from `close()` on the exact retained connection is the only C1/C2
proof. An ordinary failure or process-control interruption creates no proof and
permits a later close of that same object; no close occurs after C2. There is no
`in_transaction`, `ProgrammingError`, exception-message, SQL, reopen, or
reconstruction proof path. Exact closed variants prevent connection/proof
co-custody, and finite structural cursors carry only custody still valid at the
next R/L/H/T milestone. The retained-custody owner directly calls the exact
base SQLite close; the generic transaction cleanup helper is not a proof owner
and no successful callback can mint proof.

Resume-if-close-proved-and-still-eligible and cleanup-required are monotonic
pre-close policies, not results. Field-free `ResumeActive` exists only after
proof. Explicit disposal or orphan cleanup before publication strengthens the
policy; disposal after proof publication atomically converts resumption to
proof-backed cleanup. Exact `KeyboardInterrupt`, `SystemExit`, and
`GeneratorExit` preserve identity through the complete operation body,
mutation cleanup, exact mutation release, and operation-completion interval.
The lifecycle state owns one immutable admission record per operation. It
copies the resource identity, operation number, PID, thread, and epoch and owns
the exact lease weak reference, finalizer identity, cleanup posture, phase, and
condition-created acknowledgments. Mutable handle-side binding fields are
non-authoritative compatibility observations.

Phase 1 records exact mutation release and retirement preparation under the
resource condition, retains the record, and blocks admission. Defensive release
is limited to the exact slot in plain mutation-active/closing states and does
not replace the controller close-proved release owner. A sole cleanup blocker
uses the existing cleanup claim and stays represented through credential/lock
cleanup. Normal retirement is owned only by the live lease named by the record.
Under the same condition, it validates the exact admitted record, records local
terminality, invokes the exact bound finalizer's `detach()`, and records
`EXPLICIT_RETIRED` only from that call's exact successful return. Finalizer
death, `.alive == False`, weak-reference clearing, GC, object loss, or a
caller-built acknowledgment is not retirement proof.

Finalizer execution, direct invocation, or lease loss before
`EXPLICIT_RETIRED` marks the operation orphaned and cleanup-required. It keeps
admission frozen and uses existing cleanup continuation, which can remove the
orphan and reach X but cannot restore Active. Lease loss afterward adds no
authority: only the already-recorded explicit phase can finish normal
publication, otherwise current cleanup wins. Phase 2 rechecks the exact
resource record and performs one final lifecycle-state assignment. That
assignment, not Python method return, is the completion linearization point.
Transition and global-stop apply are the two vulnerable retained-lease callers.
Each now has an outer process-control envelope that creates one private
immutable exact-object invocation-correlation token before its nested operation-
guard helper can admit. Admission validates the token's exact resource, PID,
and epoch and binds it through the exact handle owned by the immutable resource
record in the same condition-protected lifecycle assignment that publishes the
record. The envelope never derives correlation from the returned lease or a
post-return handle store and receives compiler-cleanup, `__exit__`, and
`_close()` escapes, including their first traceable opcodes. Neither internal
method claims protection of its own first opcode. Before poison, the stabilizer
checks only the token's exact type, directly stored resource identity, and the
resource's direct fork-invalid owner-PID sentinel, acquires the resource
condition, directly inspects the current exact lifecycle-
state type and exact immutable record tuple, and recognizes the record through
direct frozen/slotted fields and token-object identity. It reads no lifecycle
property and calls no project or policy helper. A single exact current match is
followed immediately by direct poison assignment. Only afterward may
`_state_authority` derive authority and validate PID, epoch, resource,
correlation, record, and handle consistency; every such failure keeps poison
set. Absence proves neither no admission nor final assignment and does not
poison. Classification, detailed record replacement, successor construction,
and notification occur only after poison and cannot reset it. Controller
resolution with `_CleanupRequiredAfterResolution` is represented cleanup-owned.
The one-way payload-free poison blocks operation and mutation admission and
prevents an admitting successor while bounded cleanup proceeds toward X.

After stabilization, a bounded cycle-aware sanitizer clears traceback fields
in the supported graph: `BaseException` base traceback, cause, context, args,
and base instance dictionary; `BaseExceptionGroup` base children; and
`BaseException` values recursively reached through exact built-in `tuple`,
`list`, `dict`, `set`, and `frozenset` containers. Bound base-class descriptors
and exact built-in operations avoid normal exception-field dispatch; subclass
dynamic descriptors, arbitrary subclass slots, arbitrary user-object
attributes, and custom container iteration are excluded. Each exception's base
traceback is cleared before its other base fields are read, while identity,
args, `SystemExit.code`, cause/context and group-child identities, suppression,
notes, and instance-dictionary content remain unchanged. One ordinary primary-
traversal or call-boundary failure is contained and followed by one independently
bound non-dispatching fallback, so it cannot replace the original bare-reraised
exception. Repeated asynchronous interruption, catastrophic allocation failure,
and unsupported private mutation of bound defaults or C-level descriptors are
outside the guarantee. The separate mutation-
usability operation guard remains fail-closed without this envelope or poison:
its unbound compiler-boundary lease reaches X by existing finalizer cleanup, and
its reachable exit boundaries publish non-admitting preparation. Wrong-PID and
fork-child authority remain unchanged. No local or resource authority mutation
follows the final assignment on the normal path.

An operation completion handle, lease, finalizer, lease-loss callback, and
immutable resource record exist before active publication, so every
construction/publication interruption can unwind the exact values. After exact
successful detachment and resource-recorded `EXPLICIT_RETIRED`, but before the
final assignment, the live explicit close path may retry. If it disappears, the
lease-loss callback may finish only from that already-recorded phase; the
retained wrapper, explicit resource close, and session finalizer remain cleanup
callers, not sources of normal-retirement proof. After assignment, internal
retirement observes record absence
without reauthorizing publication; existing transition/global-stop replay is
semantic response-loss recovery and no completion registry exists. Cleanup
ownership is the exact live `threading.Thread` object,
not its recyclable integer identifier. A dead owner permits explicit takeover
with a new token and epoch; another live Thread or process cannot steal it.
Authority/operations, mutation slot, resolution token, custody/proof, cleanup
cursor, cleanup claim, binding/lock, and terminal state each have one structural
owner. One private opaque resource identity is allocated per writer resource and
is carried by authority/activity, every operation and slot/frame, controller
token, retained connection/custody/proof, every cleanup cursor, and cleanup
claim. Every coherence comparison uses `is`; PID, epoch, operation number, or
value equality cannot authorize cross-wired values. The identity is neither
persistent nor public and has no global registry.
Coordinator safe errors are exposed only after sensitive transaction bindings
are cleared. The sensitive frame returns a private disposition carrying the one
exact content-free store-error object. Through each genuine bound public
operation guard, the outer boundary catches that same object, validates its safe
shape, applies the same supported base-storage sanitizer and one-ordinary-
failure containment, and bare-reraises it by identity without process-control
poisoning; malformed, subclassed, or content-bearing candidates fail closed.
Governing process-control exceptions do not enter that disposition and retain
exact identity. B4b's accepted one-byte contract replacement requires zero
Coordinator traceback frames and remains unchanged. VS1A is committed at
`4ffbc5f8881339dce210a50b05200e3f8e837284`; VS1B reuses its cleanup machinery
without changing transition/global-stop behavior.

After closure proof, R1 revokes credential authority, R2 clears the exact
resource-owned mutation slot, and R3 releases the database binding. The old
resource remains non-admitting after R2 because P0 froze its lifecycle. L1
normal unlock return proves release; H2 then removes the exact authority-lock
registry entry and permits a same-process writer even if T1 has not yet
published old-session X. VS1B initialization recovery/replay is admitted only
by successful acquisition and fencing of a different concrete writer session.
It receives no old resource and makes no claim that fresh acquisition proves
old-session X. Same-process acquisition may occur after H2 and before T1;
cross-process acquisition may occur after L1 kernel-lock release and before the
old process reaches H2 or T1. Existing transition and global-stop
idempotency/replay remain governed by their existing contracts. After normal transaction-connection close
with no pending explicit disposal or orphan cleanup, the same wrapper becomes active only after operation
and mutation release; a later explicit call uses a new operation lease and
fresh connection for fresh apply or exact replay. No original call retries
automatically. A lost response after operation linearization uses the same
fresh/replay/conflict semantics; transition and global-stop selectors prove no
duplicate durable effect. QU/QK, disposal-pending, orphan-cleanup, and governing
process-control postures remain non-reusable for the old session. Recovery does
not wait on or inspect those old-resource states. H3 is post-X housekeeping.

The post-R2 race is fixed by a deterministic real-session selector: after exact
mutation release and before exact operation completion, disposal makes proof-
backed cleanup current, preserves the outstanding operation until completion,
rejects new operations, and permits explicit cleanup to reach X without an
intermediate Active state. Direct runtime selectors cover all three governing
process-control classes before local terminality, before exact detach, after
detach but before final assignment, and after assignment for resume and cleanup
successors. Lease-loss and wrapper-loss phase matrices exercise both sides of
the stored `EXPLICIT_RETIRED` boundary. The shared-foundation test owns distinct
production-causal runtime, compiled complete-module source-mutant, and secondary
AST/source-guard evidence classes. One literal tuple there is the sole focused-
selector inventory; report counts are computed from its node IDs. Every source
mutant uses an external copy and leaves the live repository unchanged. The two
direct-finalizer counterfactuals assert reachability at the real orphan-mark and
cleanup-successor seams. Exact commands, mutable node and warning totals,
overlaps, and validation-group file inventories are report evidence rather than
architecture. No noncausal, duplicate, or unreached seam receives causal credit.

The B3c1a contract-projection test retains its existing node ID and replaces
only the obsolete post-GC Active expectation: loss before `EXPLICIT_RETIRED`
becomes `ORPHANED`, non-admitting, cleanup-owned, and eventually X. The B3c1b
test-file delta is test-resource hygiene only: directly test-owned
connections close explicitly after their preserved transaction boundary, and
fault-injection setup and immediately installed ledgers close exact locally
owned or retained connections on every assertion, mismatch, or setup exit. It
changes no rollback-only fencing, error precedence, mutation-slot behavior, or
safe-error vocabulary and uses no warning suppression. Transition and global-
stop privacy probes use separate real cursor-producing idempotency SELECT
faults, really close the exact built-in cursor, and cover cursor, database path,
resolved path, SQL, and parameters by identity and exact value while preserving
the exact outward safe error.

The B3c3 test delta is a private rollback-only regression adaptation to the
selected close-proof owner, with no B3c3 result, durability, public, or
authority widening. It observes the sealed retained-custody proof owner rather
than patching the generic close helper, preserves rollback-only ordering and no
COMMIT, and retains close-unproved custody until explicit cleanup. The unchanged
B2b issue remains pre-existing test-resource hygiene and is not VS1B authority
or behavior. VS1B adds one private route-neutral program-genesis transaction,
receipt-first replay, and a read-only resolver that uses `BEGIN IMMEDIATE`,
writer fencing, bounded family reads, capability invalidation, `ROLLBACK`, and
the existing close-proof cleanup. It adds no automatic retry.

Writer-lock release is proved only by normal return from the real
`fcntl.flock(exact_retained_fd, LOCK_UN)` call. Descriptor reclamation is a
separate one-shot step: the descriptor number is detached before close and the
attempt is consumed as reclamation-unknown before close. Normal return
publishes reclaimed; every non-normal outcome remains unknown and is never
retried by number. A reachable wrapper may resume an unproved lock release, but
a finalizer performs only one bounded, quiet attempt and supplies no hidden
recovery loop. Operators must not infer that descriptor close, garbage
collection, or registry disappearance proves transaction or lock outcome. A
cross-process writer may acquire after the kernel applies unlock before H2,
T1, X, or public close return; these facts are not atomic.

The current migration application generation is 2, the terminal catalog is
exactly `0002_development_program_and_effect_state`, and production migration
resources are exactly `0001_initial.sql` and
`0002_development_program_and_effect_state.sql`. Migration 0003 remains absent.
Migration 0002 requires SQLite 3.37.0 or newer before any selected-suffix
administrative effect. Its physical core schema adds no C2B mutation, reader,
runtime, or execution authority.

## Filesystem Posture

The first backend state directory must be local, private, and fixed by
Coordinator-owned local configuration/defaults, not by connector, MCP, command
payload, work item, lease, backlog, report, or remote input.

Required posture:

- state directory owned by the local Coordinator operator account;
- directory mode `0700`;
- restrictive process umask before creating files;
- database, rollback journal, and any future auxiliary files mode `0600`;
- reject symlink state roots;
- reject symlink or non-regular database files;
- reject non-local filesystems for the first backend unless separately audited;
- no extension loading;
- no arbitrary SQL input;
- prepared statements only;
- `foreign_keys=ON`;
- `trusted_schema=OFF` where supported;
- bounded `busy_timeout`;
- bounded database and page-size policy;
- disk-full failure is fail-closed;
- no automatic `VACUUM`, compaction, or event pruning initially.

Rollback journal DELETE mode is selected first. WAL auxiliary file handling is
not part of B0 because WAL is not selected.

The practical TOCTOU boundary is owner-only containment. A `0700` parent
prevents other-user file replacement. Same-account malicious-process resistance
is limited and must not be overclaimed. B3c1b additionally pins the retained
root, authority-lock-file, and active database-file identities for its private
rollback-only open path and rejects replaced paths or active database
hard-link aliases, but that is bounded local filesystem identity pinning, not
a universal mount-namespace or same-account race guarantee.

B1.1/B2b implement portable filesystem checks for bootstrap,
existing-database inspection, and the state-authority lock:

- deterministic per-user state root from the canonical NWP Coordinator
  component name;
- no repository-checkout state root;
- fixed `coordinator-state.sqlite` database filename;
- state root mode `0700`;
- database mode `0600`;
- fixed state-authority lock file mode `0600`;
- symlink, non-regular, group/other-accessible, and hard-linked active
  database rejection;
- symlink, non-regular, group/other-accessible, and hardlinked lock-file
  rejection where safely testable;
- safe closed errors without raw paths.

B2b implements one common state-authority advisory lock path while preserving
the current `coordinator-state.migration.lock` filename as an implementation
label only. The lock is acquired with nonblocking exclusive `fcntl.flock` on
macOS and Linux, remains persistent after release, and is used by initialize
and migrate. B2c also retains the same lock for the entire active internal
writer-session lifetime. Lock possession alone is not writer authority.

The lock descriptor is owned by a private resource object. Explicit
context-manager or `finally`-based close is still mandatory for production
callers. A one-shot `weakref.finalize` backstop performs quiet best-effort
cleanup for abandoned lock objects without logging or emitting evidence, but
it is not a deterministic release-timing mechanism. At-fork child cleanup
uses a descriptor snapshot frozen under the parent lifecycle/fork gate, does
not acquire inherited Python locks, and closes inherited descriptors without
explicitly unlocking parent authority. Every `os.open` result in the B2b lock
path is immediately owned by a cleanup scope until it is transferred to the
private resource. Python's broad multithreaded-fork warning and third-party
forks that bypass Python at-fork hooks remain accepted limitations.

B2b does not overclaim deeper filesystem confinement. Intermediate symlink
components are constrained by resolved trusted-root checks but are not a full
same-account malicious-process defense. Python `sqlite3` reopens by pathname.
Broad network-filesystem detection remains portable and incomplete. Those are
B5 hardening topics, not solved B2b properties.

## Bootstrap And Migration Operations

C2B1 exposes split offline operations:

- inspect an existing fixed database path observationally, returning absent,
  empty, managed, or unknown without creating or mutating files;
- validate an existing managed database observationally, including journal
  posture, migration-history/catalog equality, live-schema manifest equality,
  and managed current-state invariants;
- initialize an absent or empty local database with the complete current
  catalog (currently `[0001_initial, 0002_development_program_and_effect_state]`);
- migrate an exact supported non-empty older prefix through the complete
  contiguous packaged suffix.

Initialize and migrate acquire the common state-authority lock after
observational preflight and revalidate while holding the lock. A no-op
current-schema initialize or migrate still acquires and releases the lock.
Inspect and validate remain observational and do not create the state root,
database, or lock file.

Ordinary future product operations must not run migrations implicitly merely by
opening the database.

Public inspection retains absent, empty, managed, and unknown. `managed` means
only exact complete current history, the exact current terminal ID,
terminal-only compatibility, cumulative schema equality, and managed
invariants. An exact supported older prefix is public `UNKNOWN`; it is never
ordinary `MANAGED`.

Before applying migrations, C2B1 uses the closed private assessment:

- absent: fixed database file missing;
- empty: existing database/placeholder with no user-defined schema objects;
- current: exact complete current history and terminal schema;
- supported older prefix: exact non-empty proper prefix with exact cumulative
  prefix schema and a complete packaged path to the current tip;
- unsupported older, newer unsupported, corrupt history, partial migration, and
  database-not-empty-unmanaged: distinct fail-closed states.

Unknown databases fail closed. B1 does not adopt, drop, repair, or rewrite
unknown schema.

Observational inspect/validate and every ordinary product/writer open use
create-disabled opening where practical and
never issue persistent `journal_mode` changes. Wrong-posture WAL databases are
reported as unsupported/unknown instead of being converted. Ordinary open
never migrates and rejects a supported prefix.

Explicit migration validates the entire selected plan and refuses destructive
or transaction-escaping SQL before lock acquisition or writable activity. It
retains the common lock through locked revalidation, filesystem-bound writable
open, one `BEGIN IMMEDIATE`, complete suffix application, one planned
timestamp, final history/schema verification, one commit attempt, cleanup, and
any recovery. No migration in the selected suffix commits early.

Before commit starts, failure attempts rollback and close to restore the exact
opening state. After commit begins, rollback is forbidden. Raised commit or
unprovable cleanup triggers filesystem-bound readback under the retained lock:

- `COMMITTED_EXACT` returns success only for exact completed history plus exact
  cumulative target schema and invariants;
- `DEFINITELY_NOT_COMMITTED` raises `migration_failed` only for exact prior
  history/schema with no suffix evidence;
- `UNRESOLVED` raises `migration_outcome_unresolved` for every partial,
  divergent, unknown, or unverifiable result.

There is no automatic retry, complete-suffix rerun, or missing-remainder append
after unresolved evidence. Explicit operator intervention and a later separate
eligibility proof are required. This administrative graph is distinct from
semantic mutation `commit_outcome_unknown` retry.

## Writer Issuance Operation

B2c writer acquisition is an administrative/runtime authority operation for an
existing managed database. It is not an implicit migration, product read,
transition apply, or global-stop apply.

Acquisition refuses absent, empty, unknown, drifted, or incompatible databases
before creating a writer row. It acquires the common state-authority lock,
revalidates managed state while holding the lock, opens the database
create-disabled read/write, starts `BEGIN IMMEDIATE`, revalidates schema and
history inside the transaction, reads and validates the singleton
`writer_ownership` row, issues the next monotonic generation, stores only the
private-proof digest, commits, closes the acquisition connection, and returns
an internal session that retains the common lock. A missing writer row is valid
before first acquisition; a present generation `0` row is malformed managed
writer state.

B3c1b rollback-only fencing opens the database only through the retained
root/lock/database binding. A failed bound-open admission preserves its primary
structural or operational classification even if best-effort close of the
rejected connection also fails; no rejected connection is returned and no raw
cleanup exception is retained. Once a connection is admitted into the
rollback-only controller, later transaction-resolution close failure remains
`mutation_failed` and no `MATCH` or `STALE_WRITER` result is returned.

Close is explicit and idempotent after completion. It marks the session closing
before releasing resources, waits for any private operation guard to exit,
lets exactly one cleanup owner enter cleaning, best-effort overwrites and drops
the private proof, closes the common lock, then publishes closed. Concurrent
explicit close callers wait for closed. Close performs no SQLite update, delete,
release marker, or generation reset. Public transition mutation now delegates
through the private guarded path. Public global-stop mutation now delegates
through the guarded B4c public wrapper to B4b private atomic global-stop
persistence. The public wrappers own no SQL, receipt verification, evaluator,
sequence allocation, write, rollback, COMMIT, or uncertainty handling, and they
do not widen public `StateStore` or add worker, service, scheduler, ES handoff,
or runtime behavior.

## B3a Future Mutation Error Contract

B3a defines `SQLiteMutationStoreError` for future transition mutation apply. It
is separate from administrative `SQLiteStateError`, session-local
`WriterSessionError`, and `TransitionConflict`.

Closed public classes are `database_integrity_failure`,
`event_sequence_exhausted`, `mutation_failed`, and
`commit_outcome_unknown`. Public strings contain only those classes: no raw SQL,
SQLite exception text, paths, canonical JSON, rows, proof material, proof
digests, credentials, endpoints, or secrets.

`mutation_failed` means rollback/no commit is definite before a commit attempt.
`commit_outcome_unknown` means the caller must retry with the same idempotency
key and digest; exact replay resolves whether the prior attempt committed. B3a
itself does not implement commit, rollback, idempotency, or replay runtime.

## Backup

The first backend should use SQLite's backup API or a mode-compatible offline
backup procedure. Raw file copy is permitted only when the database is offline
and the rollback journal state is safe.

Backups:

- are recovery artifacts, not active state authority while the active store is
  healthy;
- must inherit private permissions;
- must include schema checksum metadata;
- must not include report projections as authoritative state.

C2B1 implements no backup files and rejects every selected destructive
definition before lock or writable activity. Migration history records the
persisted definition projection—sequence, ID, checksum, `applied_at`, and
compatibility bounds—not a destructive column or raw backup path.

## Restore

Restore requires explicit operator action. A restored database becomes
authoritative only after:

- schema migration checksum validation;
- migration-history/catalog equality validation;
- full live-schema manifest validation;
- `PRAGMA integrity_check`;
- canonical digest validation for immutable records;
- event-owned idempotency checks;
- replay snapshot digest validation;
- event/current-state reconciliation;
- global-stop current-state validation.

Automatic repair is not allowed. Corrupt active databases are quarantined and
reported with safe evidence only.

## Retention

The first backend does not prune immutable transition or global-stop events.
Growth is bounded by admitted backlog size, work-item budget limits, and an
operator-configured database size policy. Retention and compaction require a
later audit because they can affect replay and receipt history.

## Read Surfaces

Future read ports are separate from mutation authority:

- read current work item;
- read current global stop;
- read safe transition history;
- read audit/replay projection.

Read connections cannot mutate. Reads must not expose an unfenced idempotency
oracle. Raw database rows and canonical JSON are not public reports. Bridge,
Control Plane, Execution Substrate, Maintenance Agent, and Infrastructure
Manager receive no database handle.

B3a adds pure canonical row mapping helpers only. They must not open SQLite and
must not become read/report APIs.

There is no B2a latest-writer read API. A future administrative observer may
read safe durable writer issuance metadata, but such a read would not prove
liveness, would not return proof or proof digest, and would not authorize
mutation.

## B3c4a/B3c4b Recovery Boundary

B3c4a pins the transition apply recovery contract without executing it.
B3c4b privately executes that contract. Commit-attempt exceptions produce only
`commit_outcome_unknown`; close failure after commit success must not reverse a
committed result; close failure after uncertainty must not change uncertainty;
and retry after uncertainty must use the same work item, idempotency key, and
canonical command digest. B3c4a itself performs no transaction, no insert, no
CAS, no rollback, no commit, no hidden retry, and no artifact recovery. B3c4b
adds no hidden retry, no public recovery report, and no B4 global-stop recovery
behavior.

## C2B3D Private Author-Effect Recovery Boundary

C2B3D reduces raw `WorkSpecV1` and typed requirement/authority evidence to one
safe closed command before the writer operation guard. The private writer
helper then enters the existing operation guard, shared mutation slot,
resource-bound connection, `BEGIN IMMEDIATE`, writer fence, and nominal
capability. A fresh operation reads the receipt first, applies global-stop and
genesis-basis precedence, checks bounded identity collisions, captures one
whole-second UTC transaction timestamp, inserts exactly ten rows in the
Section-39 order, and attempts COMMIT exactly once. It has no hidden retry.

Same-command replay verifies the receipt, all nine original graph members, the
graph digest and result, and the bounded current effect/delivery-head predicate.
Readback recovery under a freshly acquired and fenced writer returns exactly
`committed_exact`, `definitely_not_committed`, or `unresolved`.
`definitely_not_committed` requires both receipt absence and absence of every
selected family identity. Partial, malformed, duplicated, foreign, or
contradictory evidence is unresolved. A commit-attempt exception is never
automatically retried; the affected resource follows the existing uncertainty
cleanup/custody quarantine rules before explicit recovery.

<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_BEGIN -->
## Cognitive proposal and selection candidate

Section 41 of `.docs/c2b-durable-development-state.md` is the sole detailed semantic owner
for this bounded freeze. C2B3D remains current and unchanged. Section 41 is an
uncommitted contract candidate pending independent audit. Migration 0003 and all source/runtime remain absent.
The first later source tranche ends at typed pre-execution proposal admission plus Coordinator selection or non-selection;
it performs no model invocation or dispatch. In particular, model invocation, dispatch, worker contact, post-execution review, semantic decision, Git, and publication remain blocked.
The full remote-worker phase is not reduced to that first source tranche.
<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_END -->
