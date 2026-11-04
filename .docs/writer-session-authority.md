# Writer Session Authority

Status: B2c durable writer issuance, internal writer-session acquisition,
B3c1a private WriterSession authority plumbing, and B3c1b private
rollback-only writer-fencing/capability mechanics. B3c3 adds a private
rollback-only transition dry-run runtime but no public writer-session mutation
behavior. B3c4b adds private atomic transition persistence. B3c4c adds
operation-guarded public transition delegation, public command-local
transition-apply preflight vocabulary, exact private-to-public mapping, and the
bounded import/error boundary. B4b adds private atomic global-stop persistence,
and B4c adds operation-guarded public global-stop delegation with the same
bounded import/error boundary.
B2b implements the common advisory lock and integrates it with SQLite
initialize/migrate administration. B2c adds durable generation issuance,
private proof generation and verification, `writer_ownership` acquisition
updates, and an internal concrete `WriterSession`. Private transition
persistence and B4b private global-stop persistence exist through the neutral
mutation authority, public transition delegation exists, and public global-stop
delegation exists as a guarded adapter. No general public `StateStore`
mutation backend, worker, service, scheduler, executable authorization, repair,
publication, or deployment behavior exists.
B2c implements an internal concrete `WriterSession`. B3c1a implements only the
private resource-owned mutation slot, mutation lease, operation-lease authority
checks, and durable-issuance verification. B3c1b implements only the private
rollback-only writer-fencing/capability mechanics that consume that private
verification interface.
B3c3 contracts do not change writer-session public methods and add no
production transaction caller.

C2B Pre-I/O VS1A adds the private shared cleanup foundation only. It preserves
the public `WriterSession` and `StateStore` surfaces, schema, migrations, and
commit-resolution vocabulary. The controller constructs one exclusive scope,
and the resource acknowledges its exact token before COMMIT. After direct
close, the controller supplies immutable facts only; the resource selects the
actual successor under its lifecycle lock and publishes it through one state
assignment. Exact publication acknowledgment precedes alias clearing, while
scope use is already invalid after assignment. Pre-close policy is distinct
from field-free post-proof `ResumeActive`; disposal and governing process
control can only move the resource toward cleanup. Transition and global-stop
apply are the two vulnerable retained-lease operation-guard users. Their outer
caller envelopes create one private immutable exact-object invocation-
correlation token before nested helpers can admit. Admission validates the
token's exact resource, PID, and epoch and binds it through the exact handle
owned by the immutable resource record in the same condition-protected lifecycle
assignment that publishes the record. No record is visible without its binding,
and correlation is never derived from the returned lease or post-return handle
capture. The envelopes receive every helper, compiler-cleanup, `__exit__`, and
`_close()` escape, including each first traceable opcode; the internal methods
do not claim to protect their own first opcode. Before poison, the stabilizer
checks only exact token type, its direct resource-identity slot, and the
resource's direct fork-invalid owner-PID sentinel, acquires the existing
condition, directly unwraps the exact current lifecycle state,
requires the exact immutable record tuple, and compares the exact token object
by identity. It reads no lifecycle property and calls no project helper. The
first exact match is followed immediately by direct poison assignment. Only
after poison may `_state_authority` and direct stored token/record/resource
fields validate PID, lifecycle epoch, authority, and record consistency; any
failure stays poisoned and fail-closed. Absence proves neither no admission nor
final assignment and does not poison. Classification, detailed record
replacement, successor construction, and notification are post-poison and cannot reset it;
controller resolution with `_CleanupRequiredAfterResolution` is represented
cleanup-owned. That monotonic non-persistent fact blocks all operation and
mutation admission and all admitting successors, allowing cleanup only toward
X.

After stabilization, a bounded cycle-aware sanitizer reads only the C-level
`BaseException` traceback, cause, context, args, and base instance dictionary
through bound base-class descriptors, plus the C-level
`BaseExceptionGroup.exceptions` field. It recursively follows `BaseException`
values in exact built-in tuple, list, dict keys and values, set, and frozenset
containers. Ordinary notes are covered through the base dictionary. It clears
each traceback before reading the other fields and invokes no subclass-defined
dynamic descriptor, arbitrary subclass slot, arbitrary user-object attribute,
or custom container iterator. One ordinary primary-pass failure and one
ordinary replaceable sanitizer-call failure are bounded beneath the original
exception by a fresh default-bound non-dispatching pass. Exact identity, args,
`SystemExit.code`, suppression, notes, cause/context identity, group children,
and ordinary dictionary content are preserved before bare reraise. Repeated
asynchronous interruption and catastrophic allocation failure are outside this
guarantee. Detailed marking or notification failure cannot replace the governing object. The
`require_usable_for_mutation` guard is separately classified as an already fail-
closed ephemeral/unbound-lease use: the reproduced compiler boundary releases
its last strong lease reference and existing finalizer cleanup reaches X without
an outer envelope or poison, while reachable exit paths prepublish a non-
admitting preparation. Wrong-PID and fork-child non-authority remain unchanged.
Exact closed variants and
single-owned structural cursors replace the rejected broad optional snapshot
and completed-step set. Only normal direct exact-object `close()` return by the
retained-custody owner creates proof; repeated close is allowed only while proof
is absent, the generic cleanup helper is not a proof owner, and no callback can
mint proof. Each operation's handle, lease, finalizer, loss callback, and
immutable resource-owned admission record exist before publication. The record,
not mutable handle-side binding fields, owns the exact lease/finalizer relation
and copied resource/operation/PID/thread/epoch facts. Only the live admitted
lease's serialized exact successful `detach()` records normal retirement.
Finalizer death, weak-reference clearing, GC, direct invocation, and object loss
are cleanup signals and never substitute for that proof.
Cleanup claims bind the exact live `threading.Thread`, with explicit dead-owner
takeover and no integer-identifier authority. Coordinator safe errors are
exposed only after sensitive bindings are cleared; one private disposition
carries the exact content-free error through each genuine bound public
operation guard to an outer catch that validates, sanitizes the same supported
base-storage and exact-built-in-container graph with bounded ordinary-failure
containment, and bare-reraises the same object by identity without process-
control poisoning. Dynamic subclass descriptors, arbitrary subclass slots or
user-object attributes, and custom container iteration remain outside that
boundary.
Normally closed uncertainty with no pending explicit disposal or orphan
cleanup restores the same
wrapper only after operation and mutation release, for a later explicit fresh
apply or exact replay with a new operation and connection. QU/QK and disposal-
pending paths remain non-reusable. The authority lock retains its unchanged
release/reclamation contract. VS1A is committed at
`4ffbc5f8881339dce210a50b05200e3f8e837284`; its cleanup semantics remain
current. The B3c1a contract-projection test retains its
existing node ID and replaces only the obsolete post-GC Active expectation with
`ORPHANED` -> non-admitting -> cleanup -> X. The B3c1b delta is explicit SQLite
lifetime
hygiene only. B3c3 is adapted only as a private rollback-only regression to the
selected proof owner, with no semantic widening. The unchanged B2b issue
remains pre-existing test-resource hygiene and is not VS1B authority or
behavior.

The shared-foundation test owns distinct production-causal runtime, compiled
complete-module source-mutant, and secondary AST/source-guard evidence classes.
Its one literal tuple is the sole focused-selector inventory; report counts are
computed from those selected node IDs. Source mutants use external copies and
leave the live repository unchanged. Both direct-finalizer counterfactuals
assert their actual orphan-mark or cleanup-successor seam was reached. Exact
commands, mutable node and warning totals, overlaps, and validation-group file
inventories are report evidence rather than architecture. No noncausal,
duplicate, or unreached seam receives causal credit.

## Purpose

B2a settled the writer-authority vocabulary, B2b added the shared
state-authority advisory lock, and B2c implements internal writer acquisition.
A durable SQLite row must never be enough to reconstruct mutation authority.
Live session authority is the conjunction of the common advisory lock, the
private proof held only in memory, the durable generation evidence, and the
backend-created active session resource.

Python `Protocol` conformance is not authority. A caller cannot manufacture
mutation authority by creating an object with matching methods. The concrete
session is private to the SQLite writer-session module and is not exported
from the package root.

## Concepts

### DurableWriterIssuance

`DurableWriterIssuance` is the latest durable fencing issuance stored in the
SQLite `writer_ownership` singleton row. It contains:

- `writer_ref`;
- `generation`;
- `issued_ref`;
- `issuance_proof_digest`;
- `acquired_at`.

It does not prove that a live process holds the OS advisory lock. It is not a
credential, is not sufficient for mutation, and remains latest issuance
evidence after graceful close or process crash.

### PrivateWriterCredential

`PrivateWriterCredential` is the private credential held only inside an active
internal `WriterSession`. It contains:

- `writer_ref`;
- `generation`;
- `issued_ref`;
- raw private issuance proof.

The raw proof is never persisted, never serialized publicly, never logged,
never projected, and never returned by safe read APIs. It never appears in
public errors, reports, metadata, equality, hashing, or repr output.

### WriterSession

`WriterSession` is the opaque live mutation capability. In B2c the concrete
SQLite session is internal. It owns the advisory-lock object, owns the private
credential, is bound to the acquiring process, and has an
active/closing/cleaning/closed lifecycle. Public `apply_transition()` is guarded
delegation into private atomic transition persistence. Public
`apply_global_stop_update()` is guarded delegation into private B4b atomic
global-stop persistence.
B3c1a implements the private slot that uses
`writer_session_mutation_in_progress` for a second concurrent private mutation
attempt on the same session. Public wrappers do not acquire that slot
themselves; the private neutral mutation runtime acquires and releases it after
local preflight succeeds.

### SafeWriterMetadata

`SafeWriterMetadata` contains only:

- safe `writer_ref`;
- `generation`;
- safe `issued_ref`;
- `acquired_at`.

It contains no proof, no proof digest, no lock path, no process id, and no
liveness claim. It is evidence/diagnostics only and does not authorize
mutation.

### VS1A cleanup states and custody

`A` is ordinary active session state. The controller-exclusive scope exists
before the resource acknowledges its exact token. COMMIT cannot begin before
that activation acknowledgment. After close, actual successor selection occurs
under the resource lock from immutable facts and the current cleanup posture;
the controller does not precompute it. One assignment publishes the successor,
and exact acknowledgment is required before aliases clear. `QU` records commit
uncertainty and `QK` records known commit success; both retain the exact
connection and mutation slot and reject new operations. `PU` and `PK` hold a
connection-free proof and no connection. `X` holds no operation, slot, claim,
authority, connection, proof, or cursor. None of these cleanup states changes
COMMIT truth.

Only normal return from `close()` on the exact retained object creates closure
proof. Failure or process control creates no proof; cleanup may later close that
same object while proof is absent, but never after C2. No
`sqlite3.Connection.in_transaction`, `ProgrammingError`, exception message,
SQL, reopen, or reconstructed observation is proof.

Resume-if-close-proved-and-still-eligible and cleanup-required-after-resolution
are pre-close policies. They are not `ResumeActive`, which is a field-free
post-proof result. Disposal may only strengthen the policy; after proof
publication it atomically converts resumption to proof-backed cleanup. Exact
governing process control preserves its original object while performing the
same cleanup conversion without requiring a usable post-proof scope. The
lifecycle state owns a private immutable operation record whose cleanup posture
can move only from resume-eligible to cleanup-required. It copies the exact
resource identity, operation number, PID, thread, and epoch and owns the exact
admitted handle, lease weak reference, finalizer, phase, and condition-created
acknowledgments. Handle-side binding fields are compatibility observations only.

The operation guard covers the body, mutation cleanup, exact mutation release,
and operation completion. Under the existing resource condition, Phase 1
records exact mutation release and retirement preparation, retains the record,
and blocks admission. Defensive release is limited to an exact plain mutation-
active or mutation-closing slot and leaves controller close-proved release
ownership unchanged. A sole cleanup blocker uses the existing cleanup claim and
remains represented through credential/lock cleanup. Normal retirement is
owned only by the live lease bound in the record. Under the same condition, the
resource records local terminality, calls `detach()` on the exact admitted
finalizer, and records `EXPLICIT_RETIRED` only from that call's exact successful
return. Neither a dead finalizer, `.alive == False`, weak-reference clearing,
GC, object loss, nor a caller-created acknowledgment is retirement proof.

Finalizer execution, direct invocation, or lease loss before
`EXPLICIT_RETIRED` marks the record orphaned and cleanup-required, freezes
admission, and continues cleanup toward X without restoring Active. Lease loss
after that phase adds no authority: an already-authorized publication may
finish from the stored resource phase, while current disposal still selects
cleanup. One final lifecycle assignment is the operation-completion
linearization point; Python method return is caller observation only. Pre-
assignment process control keeps the represented record and cleanup posture.
Post-assignment process control preserves the assigned state as response loss.
A local stabilization failure cannot replace the governing object or restore
Active.

The resource executes `P0`, `C1`, `C2`, `R1`, `R2`, `R3`, `L1`,
`H1`, `H2`, `T1`, and `H3` monotonically. Connection close
acknowledgment precedes credential revocation, mutation-slot release, binding
release, writer-lock release proof, descriptor housekeeping, authority-lock
terminalization, session terminal publication, and registry removal where
applicable. R2 clears the slot after R1 and before R3/L1; the slot is not
retained until X. P0 keeps the old session non-admitting. Finite structural
cursor types, not an arbitrary completed-step set, make already-removed custody
unavailable to later milestones. Authority and operations live in one activity,
the mutation slot in one frame and then one slot-bearing cursor, and resolution,
custody/proof, cleanup cursor, claim, binding/lock, and terminal facts each have
one structural owner. Cross-wired lifecycle values are unconstructible.

One private opaque resource identity is allocated for each writer resource. The
same exact object binds the resource, authority/activity, immutable operation
record and handle,
mutation slot/frame, controller token, connection custody/retained connection/
close proof, every cleanup cursor, cleanup claim, and unproved or proved cleanup
state. Constructors compare it only with `is`; PID, lifecycle epoch, operation
number, and value equality are insufficient. It is not exported, persisted,
serialized, registered globally, logged, rendered as authority, or placed in a
safe error.

An operation completion handle, lease, finalizer, loss callback, and immutable
record are constructed before active publication. A never-published callback is
a non-authoritative no-op, and an absent record always rejects publication
rather than proving prior completion. After assignment, an internal retry stops
when Phase 1 observes record absence; existing transition/global-stop replay
remains semantic response-loss recovery. After exact successful detach and
resource-recorded `EXPLICIT_RETIRED`, but before final assignment, the live
explicit lease may retry. If it disappears, its callback may finish only from
that already-stored phase. The retained session wrapper, explicit resource close,
and session finalizer remain cleanup callers, not retirement-proof owners.
No local or resource
authority mutation follows final assignment on the normal path. Disposal after exact
mutation release but before operation completion keeps the operation represented
in a non-admitting cleanup state and can reach X without Active. Cleanup claims
bind an exact `threading.Thread` weak reference. Only
that live object may resume; another live Thread cannot steal the claim, and a
dead owner requires a new token and epoch. A recycled numeric identifier is not
authority. Fork children cannot complete or publish parent cleanup.

Only normal return from the real `fcntl.flock(exact_retained_fd, LOCK_UN)` is
writer-lock release proof. Descriptor close is separate one-shot housekeeping:
the numeric descriptor is detached and the attempt consumed as unknown before
one close. Normal return publishes reclaimed; every non-normal outcome remains
unknown and is never used for numeric retry. Explicitly reachable wrappers may
resume incomplete cleanup. Finalizers make one bounded `BaseException`-quiet
attempt and establish no background cleaner or hidden lookup retry path.

H2 exact authority-lock registry removal is the same-process writer-acquisition
boundary, so a new same-process writer may acquire before T1 publishes old-
session X. A cross-process writer may acquire after kernel unlock even before
H2. Neither acquisition is atomic with X or changes old COMMIT truth. For
VS1B, successful fresh writer acquisition plus transaction writer fencing is
the cross-session initialization recovery/replay gate. Recovery receives no old
resource and does not prove or require old X. This does not change existing
transition/global-stop replay. When the transaction connection closes normally
and no explicit disposal or orphan cleanup is pending, the exact same session wrapper
returns to active only after its mutation and operation complete. A later
explicit call uses a new operation and connection, applies fresh if no commit
occurred, or returns exact replay if it did; the original call never retries
automatically and durable effects are not duplicated. Caller response loss
after the final operation assignment uses the same explicit fresh/replay/
conflict semantics and never retroactively demotes the assigned resource state.
QU/QK, retained custody,
and pending disposal continue toward cleanup rather than active reuse. H3 is
post-X housekeeping and cannot gate or reverse X.

Safe ordinary failures leave sensitive transaction frames as a private
connection-free disposition containing the one exact content-free
`SQLiteMutationStoreError`. After prohibited bindings are cleared, the public
boundary raises that same object by `is` from `None`; it does not reconstruct
an equivalent object. Malformed, subclassed, noted, or content-bearing errors
are rejected to a fresh content-free integrity failure. Governing process
control is never converted and preserves exact identity. Separate transition
and global-stop idempotency-SELECT faults capture and really close the exact
built-in cursor and cover cursor, database path and resolved string, SQL,
parameter tuple, and parameter strings by identity and exact built-in value.
The outward safe-error object remains identical.

## Durable Row And Liveness Truth

The SQLite `writer_ownership` row records the latest durable fencing issuance.
It is not current-process truth. It is not lock ownership truth. It is not an active-session registry.
Absence or presence of a row does not prove whether a lock is held. Safe metadata cannot reconstruct authority.
no B2a observer API claims liveness.
B2c still adds no latest-writer or current-writer read surface.

## Public Contract

The package root exports the `WriterSession` protocol, `SafeWriterMetadata`,
and safe session-local error vocabulary. It does not export the concrete
SQLite session, the private credential, the proof digest helper, or
`acquire_sqlite_writer_session`.

`StateStore` remains a read-side protocol. It exposes no mutation method
outside `WriterSession`. There is no `current_writer()` read surface and no
`read_latest_writer_issuance()` read surface. Direct SQLite inspection remains
test-only under temporary roots.

B3b2a added a private reader-capability protocol now neutralized as
`_MutationReadCapability` for Coordinator mutation transactions, but it is not
writer authority, not public read authority, not a `StateStore` method, not a
database handle for callers, and not a concrete production capability. B3b2b
consumes that protocol from private SELECT readers and verifies only that the
borrowed object is a `sqlite3.Connection`; this helper check is not an authority
check and does not prove transaction identity. `connection.in_transaction` is
not transaction identity and does not prove `BEGIN IMMEDIATE`, writer fencing,
private proof possession, or B2 operation guard ownership. The concrete runtime
creates one opaque epoch only after those gates, invalidates it before commit or
rollback, and rejects old epochs after transaction end or restart on the same
connection.
B3c0a additionally pins that the concrete capability is nominal. B3c1
prerequisites in `.docs/b3c1-prerequisite-contract.md` reconcile production
reachability: the capability is created only by one private transaction
controller, now `_CoordinatorMutationTransactionController`, without a second
controller or capability constructor. There is one controller construction path.
Public production invocation for transitions occurs only from
`_SQLiteWriterSession.apply_transition()`. B4c public global-stop invocation
occurs only from `_SQLiteWriterSession.apply_global_stop_update()` into the B4b
private global-stop entry. Coherent tests may invoke the same private controller
directly through private imports without adding a separate source-level
`for_test` factory. The controller entry points accept only the active operation
lease; they derive the private
state-database filesystem binding from
the WriterSession resource after mutation-slot acquisition. That binding
contains the exact CoordinatorStateLocation, state-root identity,
authority-lock-file identity, and single-link database-file identity captured
while the retained common authority lock was held. A matching
`writer_ownership` row in another database is not authority, and replaced
root/lock/database paths or hard-linked active database aliases fail closed.
The capability receives no credential, proof, proof digest, authority lock,
lock descriptor, path, filesystem identity, link count, writer metadata as
authority, process/thread identity, or transaction epoch through a public
surface.

## Failure Layer Taxonomy

| Layer | Owner | Examples | Boundary | Result semantics |
| --- | --- | --- | --- | --- |
| WriterSession lifecycle failure | `WriterSession` or its session wrapper | `writer_session_closed`, `writer_session_process_mismatch`, `writer_session_close_during_operation`, `writer_session_mutation_in_progress`, `writer_session_mutation_unavailable` | Before any `StateStore` or atomic apply call | No event, no apply conflict, no SQLite access, no idempotency disclosure, no fencing result, and no durable record. |
| Transition apply preflight failure | B3c4c public transition wrapper | `transition_apply_invalid_command`, `transition_apply_unsupported_command` | After operation-guard success and before mutation-slot acquisition or SQLite access | No event, no apply conflict, no durable record, no idempotency participation, no rollback, and no COMMIT. |
| Global-stop apply preflight failure | B4c public global-stop wrapper | `global_stop_apply_invalid_command`, `global_stop_apply_invalid_operator_decision` | After operation-guard success and before mutation-slot acquisition or SQLite access | No event, no apply conflict, no durable record, no idempotency participation, no rollback, and no COMMIT. |
| Atomic apply conflict | B3c4b fenced SQLite atomic boundary | `stale_writer_token`, `idempotency_key_reuse_conflict`, `expected_version_conflict`, `work_item_not_found`, `validation_failed` | Requires a session that passed local lifecycle checks and command-local preflight checks | No event; may require a database transaction or read; remains distinct from session-local failures. |
| Domain result | Pure evaluator reached through the atomic boundary | accepted event or domain-rejected event | Reached only after session and apply checks pass | Exactly one accepted or domain-rejected event is the durable receipt. |

`writer_session_closed`, `writer_session_process_mismatch`,
`writer_session_close_during_operation`,
`writer_session_mutation_in_progress`, and
`writer_session_mutation_unavailable` are safe session-local failure reasons.
They are not `TransitionConflict` or `GlobalStopConflict` classes and must not
be added to apply-conflict reason sets. `stale_writer_token` remains a fenced
atomic-apply conflict for an otherwise active session whose durable writer
generation or issuance proof is rejected.
`validation_failed` is reserved for locally valid typed command/context values
whose authoritative persisted bindings fail inside the fenced atomic boundary.
It is not a parser, session-lifecycle, or mutation-unavailable catch-all.
B3c4c public preflight failures use
`TransitionApplyPreflightError`, not `TransitionConflict`, `WriterSessionError`,
or `SQLiteMutationStoreError`.
B4a defines `GlobalStopApplyPreflightError` and
`GlobalStopApplyPreflightFailureReason`; B4c maps the private B4a preflight
vocabulary to those public reasons from the guarded public wrapper.

Writer-acquisition failures use a separate closed vocabulary:

- `database_not_managed`;
- `writer_generation_exhausted`;
- `writer_state_malformed`;
- `writer_acquisition_failed`.

A common lock conflict may surface as `state_authority_lock_busy`.

## Failure Precedence

Future `WriterSession` mutation calls use this order:

1. Acquire `_WriterSessionOperationLease`.

   Acquisition performs owner-process and active-session validation and returns a
   lease only after the retained authority lock is confirmed active. Any
   provisional operation registration is synchronously unwound before a failure
   is returned. If acquisition fails, no operation lease is exposed, no mutation
   slot is attempted, no SQLite connection opens, and closed/process-mismatched
   sessions fail locally with the existing `writer_session_closed` or
   `writer_session_process_mismatch` `WriterSessionError` reason. No store call.

   If the same thread attempts to close the session while it owns an active
   operation, fail locally with `writer_session_close_during_operation`. The
   session remains active, the operation remains registered, and no store call
   occurs.

2. In B2c through B3c4b, fail locally with
   `writer_session_mutation_unavailable`.

   No store call, SQLite apply call, event, apply conflict, or durable mutation
   occurs. The private operation guard is entered and exited around this local
   failure to pin future B3/B4 close-versus-apply ordering.

3. In B3c4c for transition and B4c for global stop, perform mutation-specific local command-shape
   checks through the private preflight boundary.

   Transition checks include exact `TransitionCommand` type/digest,
   non-READY dependency ref null, and zero budget cost. Global-stop checks use
   the B4a typed command/operator-decision local checks. B3c4c maps the transition private preflight reasons exactly to
   `TransitionApplyPreflightFailureReason.INVALID_COMMAND` or
   `TransitionApplyPreflightFailureReason.UNSUPPORTED_COMMAND`. These checks run
   only after operation-guard success and before mutation-slot acquisition.

   B4c maps B4a private global-stop preflight reasons exactly to
   `GlobalStopApplyPreflightFailureReason.INVALID_COMMAND` or
   `GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION`; malformed
   private preflight objects remain mutation-store integrity failures, and
   import/load failures remain mutation failures.

4. In B3c1a private plumbing, B3c4b transition mutation runtime, and B4b
   private global-stop mutation runtime, acquire the shared per-session mutation
   slot.

   If another mutation transaction is active on the same session, fail locally
   with `writer_session_mutation_in_progress`. No SQLite connection opens, no
   SQLite busy/locked error leaks, no event is created, and no apply conflict is
   returned.

   The slot is session-owned and shared by transition and global-stop mutation.
   It is retained through database open, `BEGIN IMMEDIATE`, managed validation,
   writer fencing, idempotency, reads, binding, timestamp/runtime/context
   construction, evaluation, writes, capability invalidation, commit or rollback
   attempt, transaction-outcome classification, and connection-close attempt. It
   is released only after the connection-close attempt completes and before the
   outer operation lease exits. It is released on every setup, read, evaluate,
   write, rollback, commit-uncertainty, and committed-success close-failure path.
   A second mutation cannot begin while the first is committing, rolling back,
   classifying outcome, or closing the connection.

   Publishing the slot and constructing the mutation lease are externally
   atomic: if lease construction fails, the exact just-published slot is
   released before the failure escapes, and no copied or newer slot can be
   cleared by that unwind.

5. Derive the private state-database filesystem binding from the active
   operation lease. Open one existing managed read/write connection through
   that resource-owned binding, execute `BEGIN IMMEDIATE`, revalidate the
   binding after begin, and validate managed schema/posture inside the
   transaction.

   The bound database authority contains the WriterSession resource-owned
   location, retained root identity, retained authority-lock-file identity, and
   retained single-link database-file identity. Equivalent independently
   constructed location objects are not controller inputs, path aliases cannot
   be introduced through controller invocation, and copied writer rows remain
   evidence only.

   B3c1b implements only the rollback-only setup/fencing form of this step;
   idempotency, context reads, evaluator integration, durable writes, and commit
   remain future B3/B4 behavior.

6. Load and parse the durable writer row, then validate writer generation, refs,
   and issuance proof.

   A stale proof or generation returns `stale_writer_token`. Only after writer
   fencing succeeds may the store evaluate idempotency, expected version, and
   domain logic.

A closed session must not be reclassified as stale merely because its former
credential would also fail future fencing.

## Common State-Authority Lock

The first backend uses one common state-authority advisory lock. B2b implements
that lock for macOS and Linux with standard-library `fcntl.flock` using
`LOCK_EX | LOCK_NB`. The same exclusive lock domain covers:

- initialize;
- migrate;
- writer acquisition;
- the entire active `WriterSession` lifetime.

There are not separate migration and writer lock domains. Inspection and
validation remain observational and do not create or acquire the lock.

The current on-disk filename is `coordinator-state.migration.lock`. B2b keeps
that filename for implementation compatibility, but the filename is an
implementation label, not durable schema identity and not the authority
concept. The code-owned path concept is the state-authority lock path.

B2b creates a persistent owner-only lock file at the fixed
`CoordinatorStateLocation.state_authority_lock_path`, validates it as a
regular non-symlink file with mode `0600`, acquires it nonblocking, and never
unlinks it during normal release. The state root must remain a secure local
directory with mode `0700`.

Lock possession alone is not writer authority. It is live-process exclusion
only. B2c combines the retained lock with the private proof and durable
generation inside the internal session.

## Writer Acquisition

B2c writer acquisition order for a current managed database is:

1. Observationally require an existing current `MANAGED` database.
2. Refuse `ABSENT`, `EMPTY`, `UNKNOWN`, drifted, or incompatible databases
   without creating a writer row.
3. Acquire the same exclusive state-authority lock.
4. Re-run observational managed validation while the lock is held.
5. Open the existing database create-disabled and read/write.
6. Execute `BEGIN IMMEDIATE`.
7. Revalidate schema and migration history inside the transaction using the
   B1.1 managed-connection helper.
8. Read and strictly validate the `writer_ownership` singleton row. A missing
   row is the valid pre-first-acquisition state; a present row must use an
   exact integer generation in `1..9223372036854775807`.
9. Calculate the next generation.
10. Generate independent `writer_ref`, `issued_ref`, and raw 32-byte proof.
11. Store only the domain-separated proof digest.
12. Insert the first singleton row or update the existing row with an expected
    previous generation predicate.
13. Re-read and validate the row.
14. Verify the persisted digest with `hmac.compare_digest`.
15. Commit and close the acquisition SQLite connection.
16. Publish the internal concrete session while retaining the common lock.

### F1 bounded hot rollback recovery before writer admission

F1 observational inspection recognizes only SQLite's supplied numeric extended
`SQLITE_READONLY_ROLLBACK` code 776 and returns `UNKNOWN` with closed reason
`recovery_needed`. A message, filename, primary READONLY code, or generic I/O
error cannot authorize a recovery attempt. The healthy managed acquisition
path above remains in force. If this exact reason is seen, acquisition takes
the existing common lock, reobserves under it and binds the existing
root/lock/database. A concurrently resolved store takes the ordinary path only
after that bound store validates as current managed. If recovery is still
needed, the private checker admits only the fixed adjacent DELETE rollback
journal under the owner-private local-storage model. It requires private
root/lock/database/journal metadata, no-follow journal identity and a stable
bounded structural read. Missing, disappearing, changed, malformed or
ambiguous journals, auxiliary WAL/SHM/journal arrangements, and recognizable
super-journal tails refuse before write-capable recovery access with
`recovery_unsafe`. Unsupported WAL posture is refused from the observational
file-header result without a second writer-row diagnostic open that could
create WAL sidecars.

For an admitted journal, the existing bound connection owner opens the main
database create-disabled and SQLite performs rollback under the common lock.
The checker never follows a name from journal bytes and does not replay pages.
The connection installs available nonpersistent safety controls at its first
API opportunity, then validates posture. The journal may be consumed. An
operational error after recovery access or unproved cleanup reports
`recovery_unresolved`; no automatic retry follows. Once rollback completes,
the writer rechecks binding and exact current catalog/schema/invariants before
the ordinary one-commit issuance steps above. A recovered older or otherwise
ineligible store receives no writer and no implicit migration. Refusal after
rollback can leave changed storage. A committed issuance with a lost return is
not proof of noncommit and cannot be retried blindly.

The previous F1 refusal-only branch and its controlled pre-COMMIT ATTACH
fixture remain historical evidence, not the current recovery contract. The
fixture's main journal had no super-journal dependency; an attachment in
transaction history alone does not require a second recovery path. Current
support is bounded by the admitted main journal's dependency form and the
standard SQLite VFS path under private local storage. Checked descriptors do
not make the VFS use those descriptors or prove resistance to a hostile same-
account path race. No first-live restart or broader effect authorization follows
from this storage recovery.

B2c updates `writer_ownership` only during writer acquisition. Close never
updates, deletes, or clears that row.

## Session Lifecycle

The session lifecycle is:

- acquired;
- active;
- closing;
- cleaning;
- closed;
- fork-invalid in a child copy.

B2c implements and tests an internal concrete `WriterSession`. The session
retains the B2b state-authority lock for its lifetime, holds the private
credential, exposes only safe metadata, and closes the acquisition SQLite
connection before returning to the caller.

Mutation methods in B2c first validate process identity, then enter a private
operation guard, then fail locally with `writer_session_mutation_unavailable`.
They do not open SQLite, do not call a `StateStore` apply method, do not
inspect idempotency, do not emit an event, and do not mutate state.
B3c1a implements the private mutation slot layered inside this session
boundary: at most one transition or global-stop mutation transaction may be
active per session, and a second private mutation attempt fails locally with
`writer_session_mutation_in_progress` before SQLite. Public mutation methods
still fail with `writer_session_mutation_unavailable` before acquiring the
slot. The slot is retained until after transaction resolution and
connection-close attempt, then released before the outer operation lease exits
when future runtime uses it. B3c1a also exposes the private resource-owned
bound-database accessor used by B3c1b after active mutation authority is
established; it does not expose the common authority lock, descriptor, path,
inode, device, or link count.

The private operation guard uses process-local lifecycle synchronization and a
private operation-identity registry, not a count-only authority truth. Each
operation lease captures an operation identity, the current lifecycle epoch,
the acquiring process identity, and the owning thread identity. The lease also
retains a strong reference to the concrete session wrapper so wrapper
finalization cannot release proof or lock authority while the operation is
active. Nested operations are allowed as independent private operation
identities.
That generic operation registry is not the B3c1a mutation slot. B3c0a keeps
lifecycle operation identities separate from the stricter
one-mutation-per-session rule.

Operation entry rejects foreign, fork-invalid, closing, cleaning, or closed
sessions before recording an operation identity. Explicit close transitions
active sessions to closing, rejects new operations, and waits for operations
owned by other threads to leave. When operations drain, exactly one cleanup
owner transitions closing to cleaning, detaches proof and lock resources, clears
the proof, releases the common lock, removes the active-session registry entry,
then publishes closed. Cleaning means that authoritative cleanup is in progress
outside the lifecycle critical section; closed means proof cleanup, advisory-lock
close, and registry cleanup have completed. Concurrent explicit close callers
that observe closing or cleaning wait until closed before returning.
Same-thread close during an active operation fails promptly with
`writer_session_close_during_operation`, does not transition the session to
closing, and does not clear proof or release the common lock. Close remains
idempotent after closed and performs no SQLite writer-row update.
Foreign-process cleanup and late owner-process mismatch cleanup also mark the
resource fork-invalid, clear credential, proof, operation, mutation-slot, and
retained binding authority, and remove that exact resource from the current
process-local active-session registry. The registry is not authority and cannot
establish liveness, but it must not strongly retain an inactive or fork-invalid
resource.

Fallback finalization is nonblocking. If the session wrapper or resource
finalizer runs while operations remain active, it marks closing, requests
deferred cleanup, and returns without waiting. If no operation is active, the
finalizer may become the single cleanup owner, transition to cleaning, and
publish closed after cleanup completes. If finalization observes cleaning, it
returns quietly without waiting or duplicating cleanup. The last parent-process
operation lease release may also become the single cleanup owner when closing
has been requested and the operation registry becomes empty. Finalizers are
safety fallback only, not a structured release path or authority signal.

## Graceful Close And Process Crash

B2b implements and tests the lock primitive itself. B2c implements and tests an internal concrete `WriterSession`.
The database row remains latest issuance evidence after close and the row
remains latest issuance evidence only.

| Circumstance | OS advisory lock outcome | SQLite transaction outcome | Durable `writer_ownership` row outcome | Session/credential outcome | Generation reuse rule | Next acquisition behavior |
| --- | --- | --- | --- | --- | --- | --- |
| Deliberate close | Lock descriptor is closed before the session publishes `closed`. | Close opens no new SQLite transaction. | No SQLite `writer_ownership` `UPDATE`, `DELETE`, or release-marker write occurs; the latest durable issuance row remains unchanged. | Session first becomes closing and rejects new operations, then exactly one cleanup owner enters cleaning and releases resources. Successful explicit close returns only after closed means proof cleanup, advisory-lock close, and registry cleanup are complete. Later operations fail with `writer_session_closed`; close is idempotent after closed; private-proof references are dropped; a mutable proof buffer may receive best-effort overwrite; no guaranteed Python/CPython memory zeroization is claimed. Same-thread close during an active operation fails first with `writer_session_close_during_operation` and keeps authority held until that operation exits. | Graceful close does not decrement, clear, reset, release, or reuse the durable generation. | A later writer must acquire normally and increment from the latest durable generation. |
| Process crash before lock acquisition | No OS lock has been acquired. | No issuance transaction exists. | No durable issuance effect. | No session or credential exists. | No generation is consumed. | Next acquisition starts from the latest durable generation already present. |
| Process crash after lock acquisition but before SQLite transaction | OS lock releases on process death through process/descriptor teardown. | No issuance transaction exists. | No durable issuance effect. | No returned session or usable credential exists. | No generation is consumed. | Next acquisition starts from the latest durable generation already present. |
| Process crash during uncommitted issuance transaction | OS lock releases on process death. | SQLite rolls back the uncommitted issuance transaction. | No committed writer row change survives. | No returned session or usable credential exists. | No committed generation exists to reuse. | Next acquisition reads the unchanged durable generation and increments from it. |
| Process crash after issuance commit but before session return | OS lock releases on process death. | The issuance transaction is already committed. | The committed durable generation remains latest issuance evidence only. | No session is reconstructed from the durable row; the private credential dies with the process. | The committed generation may be skipped but is never reused. | Next acquisition reads the committed durable generation and increments it. |
| Process crash while active | OS lock releases through process/descriptor teardown. | Any unrelated uncommitted SQLite transaction rolls back under normal SQLite rules. | No graceful-close update occurs; the row remains latest issuance evidence only. | Session and private credential die with the process. | The active committed generation is never reused. | Subsequent acquisition increments from the durable generation. |
| Process crash during graceful close | Process death eventually releases the descriptor. | No SQLite release-marker transaction is required. | The durable issuance row remains unchanged. | Any surviving in-memory session state is unusable because the process died. | The committed generation is never reused. | Future acquisition increments from the durable generation. |

Process crash releases the OS lock through process and descriptor teardown.
Committed generations may be skipped after a crash, but a generation is never
reused. There is no TTL, heartbeat, automatic takeover, or automatic failover.
A live hung process holding the lock requires explicit operator action.

The session removes references to the private proof on close. If the proof is
stored in a mutable buffer, implementation may attempt best-effort overwrite
before releasing references. The contract does not claim guaranteed memory
zeroization in Python or CPython. The proof must never appear in repr,
equality, hashing, serialization, exceptions, metadata, reports, or tests.
No guaranteed memory zeroization is claimed.

## Process, Fork, And Thread Rules

B2b lock primitive requirements and B2c concrete writer-session requirements:

- store the acquiring process id in the session;
- check the current process id on every lock/session operation;
- reject use in a forked child;
- mark the lock descriptor non-inheritable across exec;
- use `os.register_at_fork` where supported to invalidate child-side session
  state;
- close inherited lock descriptors in the B2b child handler where safe so the
  child cannot prolong parent authority;
- prohibit fork-after-acquisition as an authority transfer;
- protect session lifecycle and mutation calls with process-local lifecycle
  synchronization and a private operation-identity registry;
- reject duplicate active sessions through the common lock and keep any
  process-local registry non-authoritative.

`FD_CLOEXEC` alone does not solve fork inheritance.

B2c child-side session cleanup clears copied active-session registry state,
marks inherited session resources fork-invalid and inactive, increments the
child-side lifecycle epoch, clears the child operation registry, replaces every
per-session synchronization primitive with a fresh child-local primitive,
best-effort overwrites and drops the private proof in the child, and does not
issue `LOCK_UN`. B2b remains responsible for inherited lock-descriptor
closure. Parent authority remains unchanged. Later child operations fail
promptly with `writer_session_process_mismatch` before SQLite or
apply-conflict logic. A copied operation lease whose captured process identity
or lifecycle epoch no longer matches is a child-side no-op on exit or
finalization: it does not mutate the operation registry, does not underflow
operation state, does not clean proof or lock resources, does not touch
SQLite, and does not expose a raw lifecycle error.
Python's general warning about multithreaded fork still applies, and
third-party forks that bypass Python at-fork hooks remain outside the B2c
guarantee; process-identity checks fail closed on later use without acquiring a
potentially inherited per-session synchronization primitive.

## Generation And Proof Specification

Generation rules:

- first generation is `1`;
- no `writer_ownership` row is the only valid pre-first-acquisition state;
- a present row with generation `0`, a negative value, a bool-like value, or an
  overflow value is semantically malformed even though migration `0001_initial`
  remains frozen;
- committed generations are monotonically increasing;
- committed generations are never decremented;
- committed generations are never reused;
- gaps are allowed;
- a committed issuance that never becomes a usable returned session still
  consumes its generation;
- next acquisition reads the durable latest generation and increments it;
- graceful close does not decrement, clear, or release the durable generation;
- maximum generation is SQLite signed 64-bit integer maximum
  `9223372036854775807`;
- overflow is checked before increment and fails closed;
- wraparound and reuse are forbidden.

This contract must not say or imply:

- close clears the writer row;
- close resets generation;
- crash rolls back an already committed generation;
- next acquisition may reuse a skipped generation.

`writer_ref` and `issued_ref` are independently generated safe refs:

- `writer-` plus `secrets.token_hex(16)`;
- `issuance-` plus `secrets.token_hex(16)`.

Neither ref is authority by itself. Refs are not derived from process id,
hostname, paths, user names, repository names, timestamps, the proof, or one
another.

The private proof is generated independently with `secrets.token_bytes(32)`
and remains memory-only in a mutable internal buffer.

B2c implements proof generation and verification. The proof digest uses
SHA-256 with this exact domain separator:

`governed-execution.nwp-writer-issuance-proof.v1`

The canonical digest input is the UTF-8 encoding of the domain separator, a
single NUL byte, `writer_ref`, a single NUL byte, decimal `generation`, a
single NUL byte, `issued_ref`, a single NUL byte, and the raw 32-byte proof.
Verification compares digests with `hmac.compare_digest`.

## Schema Fit

Migration `0001_initial` is sufficient for the first writer-session model and
requires no migration 0002. SQLite does not store active/released status,
release timestamp, process id, lock inode, platform metadata, heartbeat,
expiry, takeover state, or liveness flag. Those are session/process facts, not
durable authority. The generation-zero rejection is a managed-state semantic
invariant layered above the frozen schema; it does not require migration 0002.

Immutable writer-issuance history remains a future evidence enhancement for
incident analysis or reporting. The latest-issuance singleton is sufficient for
current B2 fencing and recovery and is not a B3a prerequisite.

B3a corrects `WriterSession.apply_transition` to accept only
`TransitionCommand`. The concrete B2c SQLite session still enters its private
operation guard and raises `writer_session_mutation_unavailable`; no transition
persistence begins in B3a.
B3c0a preserves that runtime behavior while reserving
`writer_session_mutation_in_progress` for future B3/B4 concurrency checks.
B3c1a implements private WriterSession authority plumbing:
`_SQLiteWriterSession.apply_transition()` and `apply_global_stop_update()`
remain mutation-unavailable and open no SQLite database. B3c1b implements the
private operation-lease-only rollback-only controller, writer-fencing query,
and nominal capability, but has no production caller and does not change public
mutation behavior.
B3c3 implements the private dry-run entry point that may be called only after
the operation guard supplies an active operation lease, and command-local
preflight runs before mutation-slot acquisition. Public mutation methods still
raise `writer_session_mutation_unavailable` and have no production call into
that private dry-run path.
B3c4a does not change writer-session authority. It adds only private
pure/static transition write and the then-transition-owned commit-resolution
contracts later neutralized by B4b; it is not imported by
`_SQLiteWriterSession`. B3c4b consumes those contracts only from the private
transaction module. B3c4c makes public
`apply_transition(command)` enter the existing operation guard, perform bounded
function-local imports, map only the exact private preflight reasons, and
delegate exactly once to the B3c4b atomic entry with the operation lease and
caller command. B4b adds private global-stop persistence through the same
mutation authority. B4c makes public `apply_global_stop_update()` enter the
existing operation guard, perform bounded function-local imports, map only the
two exact private global-stop preflight reasons, and delegate exactly once to
the B4b atomic entry with the operation lease, caller command, and caller typed
operator decision.

## C2B3D Private Delegation

The concrete `_SQLiteWriterSession` now has private-only author-effect apply
and recovery helpers; the abstract/public `WriterSession` protocol and package
exports are unchanged. Raw `WorkSpecV1` and typed requirement/authority
evidence are reduced to one safe command before operation-guard entry. The
private apply helper then reuses the existing operation guard, mutation slot,
resource-bound database authority, single transaction controller, writer
fence, nominal capability, and cleanup state machine. Recovery accepts only
the already-safe command and requires a fresh valid writer session.

These helpers do not mint or verify external executable authority, expose a
credential, add another writer/connection/controller/lock, or authorize a
worker, route, dispatch, Git, Bridge, ES, or network effect. A pending authority
evaluation and planned delivery are durable bounded intent only.

## Non-Goals

B2c implements durable writer acquisition and an internal concrete session
only. B3/B4 remain future. B2c does not implement:

- transition persistence;
- global-stop persistence;
- idempotency lookup;
- expected-version checks;
- event insertion;
- work-item updates;
- global-stop updates;
- a production `StateStore` mutation backend;
- product database reads;
- reports over SQLite;
- worker, scheduler, daemon, recovery loop, repair, local commit,
  publication, deployment, or executable authorization.

B3b2a does not change B2c writer-session semantics. B3b2b private readers also
do not change B2c writer-session semantics and are not invoked by
`_SQLiteWriterSession.apply_transition`. They do not alter writer credential,
proof, lock, close, finalizer, process, fork, cleanup, mutation-unavailable, or
package-root export behavior.
B3c3 likewise does not alter writer credential, proof, lock, close, finalizer,
process, fork, cleanup, mutation-unavailable, or package-root export behavior.
It adds no second transaction controller, no second capability constructor, no
raw connection parameter, no callback, no observer, and no public
writer-session surface.

<!-- RW0_C1_CURRENT_STATUS_BEGIN -->
**RW0-C1 writer-session integration.**

The concrete `_SQLiteWriterSession` now has private-only delegates for C1 phase
establishment, evidence admission, phase recovery probes, and the stable
evidence-admission recovery selector. Each enters the existing operation guard
and passes the exact operation lease and payload once to the existing
Coordinator mutation controller. Fresh apply creates one private in-memory
commit-close witness before delegation and shares that exact object with the
module wrapper and controller. A committed C1 result is not published until
result publication, controller/module return, controller/connection cleanup,
mutation-slot and operation-lease retirement, process stabilization, and
writer-session post-operation cleanup all succeed. The resulting
`close_proof_complete` state proves internal cleanup only. The exact witness is
retained and commit-uncertainty normalization remains active through the final
writer-result handoff and successful outer-frame return. Any ordinary failure
after commit starts but before that return is the content-free
`commit_outcome_unknown`; replay and conflicts that never commit stay outside
commit uncertainty, and a standalone ordinary retirement failure on those
paths is `mutation_failed` without another commit. Recovery uses a separate
private close witness, retains its computed result through internal close, and
maps an ordinary failure after result computation through final return to
`unresolved` instead of commit uncertainty. An established safe session/store
error or private C1 safe disposition remains primary over a later ordinary
cleanup failure. Process-control handling retains its existing governing
behavior. Public `WriterSession`,
`StateStore`, package exports, writer proof/digest semantics, lock lifetime,
fork handling, close/finalizer behavior, and process-control stabilization are
unchanged. No C1 method is a public authority surface.
<!-- RW0_C1_CURRENT_STATUS_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure current candidate

The uncommitted `artificial_offline_normal.v1` candidate adds a separate private Coordinator terminal writer on generation-2 migration 0008. It consumes checked P0, phase, Section 41 A, C1 rank-15/V22 and P1 evidence under one fenced transaction and records only the five normal outcomes: accept, repair, replan, terminal_reject and block. The P1 decision remains prior decision history; its acceptance fact is bound only for accept and is never mutated. Cancellation, live supplier/contact, ES routing, Git effects, publication and executable permission remain outside this candidate. See `.docs/rw0-terminal-outcome-physical-closure.md`.

The private entry shares the current operation guard, writer fencing, nominal capability, one transaction timestamp and existing commit/cleanup witness. No independent connection owner or public API is added.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure local commit status

The exact cumulative independent audit accepted Git-compatible tree `4691af58ae0ee3107b4e2e9b6b1508032944e357` for an exact-byte commit gate after its current-ledger consistency repair. The private `artificial_offline_normal.v1` implementation was locally committed as `d3fd741c872b26aa2dfe927ab6dccc638cdcf356`, with sole parent `61d0330aba1160f7f5e7d9c541a325222d1c61e5`, that exact tree, and subject `feat: add RW0 normal terminal closure`. The staged-blob gate collected and passed 9,568 selector-free tests in the same order, with zero failures, errors, skips, xfails, or xpasses and only the three known Python 3.13 multithreaded-fork deprecation warnings. This is a local topic-branch commit; no push, PR, merge, publication, deployment, service/runtime contact, or product effect followed.

Migration `0008_rw0_terminal_outcome` is the current source/catalog suffix. The private fenced terminal owner records only normal `accept`, `repair`, `replan`, `terminal_reject`, and `block`. P0 scope admission, P1 progression decision with its acceptance-only fact, and terminal closure remain separate private fenced transactions and facts. P0 grants no current permission; P1 is prior decision history, not terminal truth. Normal accept binds the immutable acceptance fact without mutation or replenishment.

Common managed-store admission may shape-check the current global-stop singleton before writer fencing. After fencing and protected disclosure, receipt-present terminal read, replay, and recovery verify saved full head postimages, saved stop, and immutable P0/Section 41/C1/P1 predecessors without today's mutable-head or semantic stop checks. A fresh receipt miss retains current-head, current-stop, recording, and disclosure checks. The old whole-operation zero-current-stop-SELECT audit failure remains historical; the accepted two-layer rule supersedes only that overbroad requirement.

Git objects and refs own commit and publication truth. Audit packages, reports, validation, this status text, WA1/QtcM evidence, and provenance are evidence only. The local commit adds no executable permission, three cancel selectors, live supplier/custody gate, worker/provider or physical remote contact, ES/Bridge route, product Git-effect handler, service, queue, scheduler, deployment, or autonomous loop. Existing F03/F05 nonblocking provenance limits retain their recorded scope; this status does not claim their repair. Candidate-stage status elsewhere in this document is preserved history; this marked block is the current local status.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_POST_MERGE_STATUS_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure integrated capability status

Classification: `CURRENT INTEGRATED CAPABILITY STATUS`.

RW0 normal terminal closure was integrated into `trunk_dev` by squash commit `3be0096c163b456c9975326be3eb2c30d2b4bbd1`, with sole parent `61d0330aba1160f7f5e7d9c541a325222d1c61e5` and integrated capability tree `bc10382edd1b2c097fc729e4e168d72e710391fe`. This is the integration anchor for the accepted private `artificial_offline_normal.v1` source. The commit containing this status-only successor is intentionally not self-identified here; Git objects and refs own the current containing commit and publication truth.

The integrated capability records only normal `accept`, `repair`, `replan`, `terminal_reject`, and `block`. P0 scope admission, P1 progression decision with its acceptance-only fact, and terminal closure remain separate private fenced transactions and facts. Migration `0008_rw0_terminal_outcome` remains the source/catalog suffix. P0 grants no current permission; P1 remains prior decision history rather than terminal truth; normal accept binds the immutable acceptance fact without mutation or replenishment.

The accepted implementation staged-tree gate passed 9,568 / 9,568 tests. The accepted status staged-tree focused gate passed 5,655 / 5,655 tests. Independent artifact review accepted the exact status tree `bc10382edd1b2c097fc729e4e168d72e710391fe`. The accepted 9,597-test selector-free FULL record was carried evidence on that tree and was not rerun during integration. No tests ran during the integration operation itself. These records are evidence at their stated scopes, not current Git or runtime authority and not validation of this later status-only correction.

All earlier candidate-stage, local-commit-stage, and cross-stage status passages in this document are preserved historical evidence. Their statements that the implementation was uncommitted, only a local topic-branch commit, or followed by no push, PR, merge, or source publication are stage-local and are not current repository status after the integration anchor above.

The integrated source adds no active-cancel terminal family or executable permission; no live supplier/custody, worker/provider, or physical remote contact; no ES/Bridge route; no Coordinator-owned product Git-effect or runtime publication authority; and no service, queue, scheduler, deployment, or autonomous-runtime loop. Source publication by Git merge does not establish any of those product capabilities. Existing F03/F05 nonblocking provenance limits retain their recorded scope and are not repaired by this status correction.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_POST_MERGE_STATUS_SUCCESSOR_END -->

<!-- RW0_TERMINAL_ANCHOR_0009_STATUS_SUCCESSOR_BEGIN -->
## RW0 terminal anchor registry implementation status

Classification: `CURRENT UNCOMMITTED IMPLEMENTATION CANDIDATE`.

Migration `0009_rw0_terminal_anchor_registry` is the current source/catalog suffix at application schema generation 2. The integrated migration-0008 normal closure status above remains historical. Its four branch-family rows and normal semantic payload are unchanged. Explicit 0008-prefix migration registers each complete existing normal family without rewriting its rows; fresh normal receipts register an immutable anchor in the same transaction. The `rw0_terminal_anchors` phase key is the sole cross-profile route, while the selected checked branch family retains terminal semantic meaning. The registry is no independent outcome, progression decision, authorization, effect basis, or cryptographic replacement.

Migration 0009 admits only `artificial_offline_normal.v1`. Any later branch profile requires a separate explicit migration evolving the family-validation trigger; it must use the same phase-unique registry and cannot introduce a second phase-unique terminal store. This candidate adds no physical cancel capability, cancellation decision or outcome, cancellation effect or request, process observation, external source reconciliation, qualified supplier or custody, successor launch, live execution, Git effect, publication, or deployment. Git objects and refs remain publication truth; this uncommitted source status and validation are evidence only.
<!-- RW0_TERMINAL_ANCHOR_0009_STATUS_SUCCESSOR_END -->

<!-- RW0_TERMINAL_ANCHOR_EVOLUTION_POST_MERGE_STATUS_SUCCESSOR_BEGIN -->
## RW0 terminal anchor evolution integrated capability status

Classification: `CURRENT INTEGRATED CAPABILITY STATUS`.

RW0 terminal-anchor evolution was integrated into `trunk_dev` by squash commit `856c5ac7efd268f70512169c127c91cf097bd200`, with sole parent `69fc836dbaa0e2124b427bc9611de2e0fba77040` and integrated capability tree `575a8da09b4da2539e8e8d6c1deb475a71627d03`. PR #20 and source topic commit `5961cf6bb1dd810eb5260e11b9f9f9054dd41d7d` are source-publication provenance. The commit containing this status-only successor is intentionally not self-identified as the permanent current HEAD; Git objects and refs own current commit and publication truth.

Migration `0009_rw0_terminal_anchor_registry` is the current integrated catalog suffix. Migrations 0001-0008 and existing normal-family rows remain preserved. The `rw0_terminal_anchors` registry owns the sole cross-profile phase route. The selected complete branch family retains terminal outcome, graph, result, receipt, and semantic meaning. The registry is no outcome, progression decision, effect basis, authorization, or independent terminal fact. Migration 0009 admits only `artificial_offline_normal.v1`. A later terminal family requires a separate explicit migration evolving family admission while preserving the same phase-unique registry.

Active cancellation is an authorized subsequent Coordinator capability, but this integrated source implements no cancel decision, cancel effect, request, source observation, reconciliation, or terminal cancel family. Progression pause/resume remains a separate nonterminal lifecycle concern; it is not represented by the terminal registry and is not implemented here. T2-R1 remains optional fixture hardening and is not implemented by this status correction.

The accepted source validation passed 12 / 12, 421 / 421, 194 / 194, 68 / 68, 791 / 791, and a full suite of 9,648 / 9,648 tests, with only the three expected Python 3.13 fork deprecation warnings. All 68 source paths passed staged and committed blob/mode/size equality. No tests ran in the merge gate itself. These records are evidence for the integrated source tree, not validation of this later status-only correction.

Earlier candidate, repair, audit, local-commit, and publication passages in this document remain preserved historical evidence; their uncommitted or unmerged statements are stage-local rather than current repository status. The integrated source adds no live supplier/custody, worker/provider, ES, CP, Bridge, or Temporal route; no Coordinator-owned product Git effect, scheduler, queue, service, successor launch, deployment, or autonomous runtime loop. Source publication does not itself establish product runtime authority.
<!-- RW0_TERMINAL_ANCHOR_EVOLUTION_POST_MERGE_STATUS_SUCCESSOR_END -->

<!-- RW0_ACTIVE_CANCEL_PRE_EFFECT_SAFETY_CLOSURE_STATUS_SUCCESSOR_BEGIN -->
## RW0 active-cancel pre-effect safety closure candidate

Classification: `CURRENT UNCOMMITTED IMPLEMENTATION CANDIDATE`.

Migration `0010_rw0_active_cancel_pre_effect_safety_closure` is a candidate suffix to the exact `trunk_dev` baseline commit `6931ae92126abaf89a75dcf0eb3781f23b4a9363` and tree `1aea0d26cdb578267eed2c0d850c3beef40f81e1`. The prior integrated migration-0009 status remains historical and current predecessor evidence. Migration 0008 and 0009 SQL bytes are unchanged. The candidate production catalog is [0001_initial, 0002_development_program_and_effect_state, 0003_cognitive_proposal_and_selection_state, 0004_rw0_c1_durable_evidence, 0005_section41_post_execution_proposal_family, 0006_rw0_c2_scope_admission, 0007_rw0_c2_progression_decision, 0008_rw0_terminal_outcome, 0009_rw0_terminal_anchor_registry, 0010_rw0_active_cancel_pre_effect_safety_closure], with short sequence catalog [0001, 0002, 0003, 0004, 0005, 0006, 0007, 0008, 0009, 0010]; the current production SQL resource count is `10`.

The private artificial-offline candidate records one immutable generic `cancel/effect_cancellation` decision with a distinct exact receipt and closed safe evidence bindings. Receipt-first same-command replay, changed-command conflict, and exact three-way commit recovery are candidate behavior. A separate fenced verifier rereads Coordinator-owned facts. Exact proven Coordinator-owned mismatch may close one cancel-bound `pre_effect_cancel_basis_unusable` terminal `block`, after the same mismatch is proven again in the terminal transaction. There is no replacement C2B block decision. The `rw0_terminal_anchors` registry remains the sole phase route; the selected complete family owns terminal meaning.

No authenticated current external source authority exists in this candidate. Supplied source evidence is a safe binding, not permission. Missing or unavailable external source evidence is unresolved. Exact local equality returns `locally_current_source_unverified`, never effect eligibility. A missing immutable predecessor is corruption; a complete competing terminal family occupies the phase.

This candidate performs no cancellation effect, fence creation, delivery, request, signal, process control, teardown, terminal cancel, live source contact, ES, CP, Bridge, Temporal, product Git effect, publication, deployment, or pause/resume. It adds no public StateStore route. Independent read-only audit remains required before any integration claim.
<!-- RW0_ACTIVE_CANCEL_PRE_EFFECT_SAFETY_CLOSURE_STATUS_SUCCESSOR_END -->
