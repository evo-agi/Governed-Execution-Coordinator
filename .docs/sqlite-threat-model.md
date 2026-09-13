# SQLite Backend Threat Model

Status: C2B1 bounded administrative migration framework over the B1/B1.1/B2b
bootstrap/inspection/validation and common state-authority lock foundation. B2c
implements durable writer issuance and internal writer-session acquisition.
B3a implements canonical persistence and provenance contracts only. B3c1b adds
private operation-lease-only rollback-only writer-fencing/capability mechanics
with no production caller and no durable state mutation. B3c2 adds private
transaction-internal event readers only. B3c3 adds a private rollback-only
transition dry-run runtime with reader/matcher/context/evaluator integration,
but still no durable mutation, commit, public caller, or public surface. B3c4b
adds private atomic transition persistence and commit uncertainty handling.
B3c4c adds guarded public transition delegation. B4b adds private atomic
global-stop persistence, and B4c adds guarded public global-stop delegation.
Receipt provisioning remains separate, and no worker, service, scheduler,
publication, or cross-repository authority exists.

C2B Pre-I/O VS1A closes the shared private custody and cleanup gaps. The
controller constructs the exclusive active connection scope before the
resource publishes its exact scope-token activation acknowledgment. COMMIT is
impossible before that acknowledgment. The controller later supplies immutable
close facts only. While holding the writer-resource lock, the resource observes
current disposal posture, selects the actual successor, and publishes it in one
lifecycle-state assignment. Raw controller/scope aliases clear only after the
exact publication acknowledgment, although scope use is invalid immediately
after assignment. An unproved close quarantines the session as known committed
(`QK`) or commit uncertain (`QU`), retains the exact connection and slot, and
admits no new operation.

Only normal `close()` return on that exact object proves closure. Failure or
process control before proof leaves the same object eligible for a later close;
C2 forbids another close. No getter, SQLite exception type, message, SQL,
reopen, or reconstructed observation substitutes for proof. Exact variants and
structural cursors reject contradictory connection/proof, operation, slot,
claim, authority, and terminal combinations before release. The retained-
custody owner calls the exact base close directly; neither the generic cleanup
helper nor a caller-supplied callback owns proof.

Pre-close policy can strengthen only from resume-if-proved-and-eligible to
cleanup-required; field-free `ResumeActive` is post-proof only. Disposal before
publication strengthens policy, while disposal after proof publication
atomically replaces resumption with proof-backed cleanup. Exact
`KeyboardInterrupt`, `SystemExit`, and `GeneratorExit` keep outward identity.
Transition and global-stop apply are the vulnerable retained-lease uses and now
place a caller envelope around creation of one private immutable exact-object
invocation-correlation token and the nested operation-guard helper. The token
exists before admission can begin. Admission validates its exact resource, PID,
and epoch and binds it through the exact handle owned by the immutable resource
record in the same condition-protected lifecycle assignment that publishes the
record. Correlation never depends on a returned lease or post-return handle
store. The envelope receives compiler cleanup and escapes from `__exit__` and
`_close()`, including their first traceable opcodes; neither method claims
internal coverage of its own first opcode. Before poison, the stabilizer checks
only the token's exact type, directly stored resource identity, and the
resource's direct fork-invalid owner-PID sentinel, acquires the resource
condition, directly inspects the current exact lifecycle-state type
and its exact immutable tuple, and recognizes a record using direct frozen/
slotted fields and token-object identity. It reads no lifecycle property and
calls no project or policy helper. One exact match is followed immediately by
direct poison assignment. Only after poison may `_state_authority` derive
authority and validate PID, epoch, resource, correlation, record, and handle
consistency; any failure leaves poison set and admission denied. Absence proves
neither no admission nor final assignment and does not poison. Classification,
detailed record replacement, successor construction, and notification are
post-poison and cannot reset it. Controller resolution with
`_CleanupRequiredAfterResolution` is represented cleanup-owned. Every
admitting reader and final-successor selector consults the poison, which
permits cleanup only toward X.

After stabilization, a bounded cycle-aware sanitizer clears traceback fields
in the supported graph: `BaseException` base traceback, cause, context, args,
and base instance dictionary; `BaseExceptionGroup` base children; and
`BaseException` values recursively reached through exact built-in `tuple`,
`list`, `dict`, `set`, and `frozenset` containers. It uses bound base-class
descriptors and bound exact built-in operations, clears each exception's base
traceback before reading its other base fields, and never invokes subclass
dynamic descriptors, arbitrary subclass slots, arbitrary user-object
attributes, or custom container iteration. It preserves exact identity, type,
args, `SystemExit.code`, suppression, notes, instance-dictionary content,
group-child identity, and cause/context links. One ordinary failure in the
primary traversal or at its call boundary is suppressed beneath the governing
exception and followed by one independently bound non-dispatching fallback;
the original exception remains outward before a bare reraise. Repeated
asynchronous interruption, catastrophic allocation failure, and unsupported
private mutation of bound defaults or C-level descriptors are outside this
guarantee. The record stores no exception payload. The
mutation-usability operation guard is a distinct already
fail-closed ephemeral/unbound-lease path: its compiler boundary reaches X by
existing finalizer cleanup without caller-envelope or poison dependence, and
reachable exit boundaries are prepared as non-admitting. Wrong-PID and fork-
child non-authority remain unchanged. The operation record copies resource/
operation/PID/thread/epoch facts and owns
the exact admitted lease weak reference, finalizer identity, phase, and
condition-created acknowledgments. Handle-side binding mutations cannot replace
those facts. Exact Phase-1 preparation retains the record and makes the resource non-admitting;
defensive slot release is limited to plain mutation-active/closing states, and
controller close-proved release ownership is unchanged. A sole cleanup blocker
uses the existing cleanup claim and remains represented through credential/lock
cleanup. Only the still-live lease named by the resource record can retire
normally. Under the resource condition it verifies the exact record, records
local terminality, calls `detach()` on the exact admitted finalizer, and records
`EXPLICIT_RETIRED` only from that call's exact successful return. A dead
finalizer, `.alive == False`, weak-reference clearing, GC, object loss, or a
caller-constructible acknowledgment supplies no retirement authority. One final
lifecycle assignment under that same condition is the completion
linearization point. An exception before assignment cannot select Active. An
exception after assignment cannot retroactively demote the authoritative
successor merely because Python return was not observed. A local stabilization
failure cannot replace the governing object.

The handle, lease, finalizer, loss callback, and immutable operation record all
exist before active publication. Finalizer execution, direct invocation, GC,
and lease or wrapper loss before `EXPLICIT_RETIRED` are orphan-cleanup signals,
not alternative completion owners. They freeze admission and continue cleanup
toward X without restoring Active. Loss after `EXPLICIT_RETIRED` adds no
authority; normal publication can continue only from the already-stored phase,
and current disposal still wins. Absent and never-published records reject
rather than imply historical completion. The live explicit lease can retry
between exact successful detach and the final assignment; if it disappears,
the callback can finish only from that already-recorded phase. Session/resource
close and the session finalizer remain cleanup callers. No completion receipt,
registry, scanner, or background cleaner is added. Claim authority is a weak reference to the exact
live `threading.Thread`; numeric
identifier reuse is irrelevant, live other-thread theft is rejected, and dead
ownership requires an explicit new token and epoch.
Safe SQLite errors clear sensitive bindings before exposure. The private
disposition carries one exact content-free store error out of sensitive frames;
through both genuine bound public operation guards, the outer boundary catches,
validates, sanitizes the same supported base-storage graph with the same one-
ordinary-failure containment, and bare-reraises that same object by identity
without process-control poisoning. Subclasses and content-bearing candidates
are rejected, while raw governing process control bypasses the safe path
unchanged. B4b's accepted one-byte contract replacement requires zero
Coordinator traceback frames and remains unchanged. Separate transition/
global-stop idempotency faults capture and
really close exact built-in cursors and exclude cursor, path, SQL, and parameter
evidence by identity and exact built-in value. Lifecycle authority/operations,
slot, resolution, custody/proof, cursor, claim, binding/lock, and terminal facts
each have one structural owner. Every live fact is additionally bound to one
opaque per-resource identity, compared only by `is`. Cross-wiring two real same-
process, same-epoch resources fails at activity, frame, cursor, scope/custody,
proof, state, and claim construction. The identity is not persistent, globally
registered, public, serializable, logged, or safe-error content. VS1A is
committed at `4ffbc5f8881339dce210a50b05200e3f8e837284`; its cleanup semantics remain
current and unchanged.

R1 revokes credential authority, R2 clears the mutation slot, and R3 releases
the binding. The old session remains non-admitting after R2 through its P0
lifecycle state. H2 exact registry removal, not X, is the same-process writer-
acquisition boundary. T1/X remains old-resource-local terminal truth, not the
cross-session VS1B recovery gate. A different concrete writer may recover or
replay only after successful independent acquisition and writer fencing; this
proves no old-resource X. Same-process acquisition may follow H2 before T1,
while cross-process acquisition may follow L1 kernel unlock before old-process
H2 or T1. Existing transition and global-stop idempotency/replay retain their own contracts. A
normal close with no pending explicit disposal or orphan cleanup permits an explicit retry on the same
wrapper with a new operation and connection; no-commit uncertainty is fresh and
underlying-commit uncertainty is exact replay, with no automatic retry or
duplicate durable effect. Post-linearization response loss uses those same
fresh/replay/conflict rules and does not change resource truth. QU/QK and pending-disposal cleanup remain
non-reusable. Recovery performs no registry scan, terminal-witness check,
old-condition wait, or old-resource mutation. H3 is post-X housekeeping and
cannot revoke X.

The B3c1a contract-projection test retains its existing node ID and replaces
only its obsolete post-GC Active expectation: loss before `EXPLICIT_RETIRED`
becomes `ORPHANED`, non-admitting, cleanup-owned, and eventually X. The B3c1b
test change closes test-owned connections explicitly and is
test-resource hygiene only. Setup retains exact local ownership through every
throwing step, and an immediately installed identity-scoped ledger covers
assertion and mismatch exits. It uses no warning filter and does not alter
rollback, fencing, cleanup precedence, or production error semantics. The B3c3
test change is a private rollback-only regression adaptation to the sealed
retained-custody proof owner, with no B3c3 result, durability, public, authority,
COMMIT, or commit-unknown widening; close-unproved custody remains until
explicit cleanup. The unchanged B2b issue remains pre-existing test-resource
hygiene and is not VS1B authority or behavior. VS1B's new threat boundary is
private route-neutral genesis only: raw `WorkSpecV1` is reduced before
transaction delegation, the transaction and recovery values carry only safe
refs/projections/digests, and recovery owns no old-resource lookup, witness,
registry, durable gate, external I/O, or retry authority.

The disposal threat after exact mutation release but before operation completion
has a deterministic barrier-based real-session test. Disposal is made current
while the exact operation is still structurally published; the wrapper remains
non-admitting through operation completion and explicit cleanup to X. The
interruption matrix also covers all three governing exception types at the
first executable close boundary, each later pre-assignment handoff, and after
assignment for both resume and cleanup states. The shared-foundation test owns
distinct production-causal runtime, compiled complete-module source-mutant, and
secondary AST/source-guard evidence classes. Its one literal tuple is the sole
focused-selector inventory, and report counts are computed from those node IDs.
Source mutants use external copies and leave the live repository unchanged. The
two direct-finalizer cases assert their actual production seam was reached.
Exact commands, mutable node and warning totals, overlaps, and validation-group
file inventories are report evidence rather than architecture. No noncausal,
duplicate, or unreached seam receives causal credit.

An advisory-lock release is proved only by normal return from the real
`LOCK_UN` call on the exact retained descriptor. Non-normal unlock keeps
release unproved. Descriptor close is one-shot housekeeping after numeric
detachment: the attempt is published as unknown before close, normal return
publishes reclaimed, and every failure remains unknown without numeric retry.
Descriptor close is never release proof, and a reused number cannot become a
later cleanup target. Explicitly reachable wrappers may resume; finalizers
catch `BaseException`, make one bounded attempt, and create no hidden cleaner,
registry scan, or retry authority. Fork children discard copied custody and
cannot publish the parent resource terminal. A cross-process writer may acquire
after the kernel unlock before old-process H2 or X; neither that acquisition nor
X is retroactive unlock proof.

C2B2 Slice 1 advances only the managed physical schema to application
generation 2 / terminal migration 0002. Its nineteen empty-at-install tables do
not add C2B row/value code, readers, mutations, runtime authority, or new
filesystem or process authority.

C2B2 Slice 2 adds pure private row/value validation, and Slice 3 adds twelve
production-unintegrated private reader roles plus a shared bounded `{2, 257}`
SELECT core. Slice 3 requires exact nominal capability type before borrow or
SQL, retains the existing capability error boundary, and adds no transaction,
writer, mutation, public API, production caller, filesystem/process authority,
replay, recovery, C2B3 behavior, migration 0003, or external effect.

This threat model applies to the first SQLite backend architecture. B2b
implements bootstrap, migrations, observational validation, and the shared
state-authority lock for administration. B2c implements writer issuance and an
internal session. B3c1a/B3c1b bind rollback-only transaction setup to the
WriterSession resource-owned root/lock/database filesystem binding and
retained common authority lock; a caller cannot supply another database root
to the private controller. B3c4b reuses that same controller path for private
transition event/current-state persistence. The current code still has no
public production `StateStore` mutation backend. B3a, B3c1b, B3c2, the private
B3c3 dry run, and private B3c4b atomic apply do not change public product
authority.

## First Backend Guarantees

Stale local coordinator process:

- fenced by OS advisory lock for live exclusion plus durable generation and
  issuance proof held inside an active writer session on every mutation;
- stale writer receives only `stale_writer_token` before idempotency detail.

Two coordinator processes:

- only one process can hold the writer lock;
- durable generation prevents a previously active process from mutating after
  restart or re-acquisition by another writer.

Abrupt process death:

- rollback journal DELETE mode with `synchronous=FULL` and one transaction
  leaves either the old state or the committed state/event/replay snapshot;
- crash before commit creates no event and no current-state mutation.

Power loss:

- same as abrupt death, subject to local filesystem and device honoring SQLite
  sync semantics.

Disk full:

- transaction fails closed;
- no partial acceptance is reported unless commit succeeds.

Replayed command:

- writer is fenced first;
- event-owned idempotency returns original event plus replay snapshot only for
  the same command digest;
- same key with a different digest conflicts with no event.

Stale expected version:

- expected-version mismatch is an apply conflict and creates no event.

Global stop active during restart:

- `global_stop_current` is persistent current state;
- startup must load it before admission/progression decisions.

Report failure:

- reports are projections and cannot disable global stop or mutate state.

## Filesystem Threats

Malicious or accidental file replacement:

- first backend uses a secured state directory with owner-only permissions;
- startup rejects symlink, non-regular, group/other-accessible, and
  hard-linked active database paths;
- B2b rejects symlink, non-regular, group/other-accessible, and hardlinked
  state-authority lock files where safely testable;
- B3c1b retains the state-root identity, authority-lock-file identity, and
  active database-file identity captured while the common authority lock was
  held, and it rejects visible root, lock, or database replacement before
  accepting writer authority;
- same-account malicious-process resistance is limited and must not be
  overclaimed.

Symlink path redirection:

- state root and database path must be resolved and checked before use;
- connector/operator-supplied arbitrary database paths are not accepted.

Local unprivileged process access:

- state directory mode `0700` and database/auxiliary file mode `0600` prevent
  other-user reads and writes on normal local filesystems.

Clock changes:

- writer fencing uses durable generation and nonce proof, not wall-clock TTL;
- no heartbeat or automatic failover exists in the first backend.

Hung writer:

- no TTL or automatic takeover;
- operator action is required to recover.

## Corruption And Recovery Threats

Partial or corrupt database:

- startup and backup/restore validation must run schema checksum checks,
  `PRAGMA integrity_check`, canonical digest checks, and event/current-state
  reconciliation;
- corruption quarantines the database;
- no automatic repair is authority.

Failed migration:

- the complete catalog or selected contiguous suffix is one transaction and
  no selected migration may commit early;
- before `COMMIT` begins, failure attempts rollback and close;
- once `COMMIT` begins, rollback is forbidden;
- a commit-attempt exception or unprovable cleanup is classified by exact
  filesystem-bound history/schema readback under the retained common lock;
- exact completed evidence succeeds, exact prior evidence is
  `migration_failed`, and every other result is
  `migration_outcome_unresolved`;
- unresolved evidence fails closed with no automatic retry, suffix rerun, or
  missing-remainder completion;
- old binary/new schema refuses;
- restore, not reverse migration, is rollback.

Migration-specific threats include a packaged resource/checksum escape,
top-level SQL transaction-control or `PRAGMA`/attach/vacuum escape, unbounded or
malformed history, duplicate/gapped/unknown/divergent history, history/schema
disagreement, cumulative-schema drift, symlink/hard-link/binding replacement,
recovery-open failure, and outward leakage of paths, SQL, resource bytes,
schema inventory, or raw SQLite errors. C2B1 rejects the SQL/resource plan
before mutation, bounds history and live-schema classification, independently
verifies cumulative packaged SQL against live schema, uses the common lock and
filesystem binding for mutation/recovery, and exposes only closed safe errors.

B1.1/B2b add concrete coverage for bootstrap filesystem threats, split
observational/admin connection posture, absent/empty/managed/unknown database
classification, no-mutation inspection of missing/unknown/wrong-posture
databases, migration-history/catalog equality, live-schema manifest
validation, managed current-state invariant checks, migration rollback, the
common state-authority lock for initialize/migrate, safe SQLite and lock error
boundaries, and authority-boundary non-expansion. B2c adds writer acquisition,
proof digest verification, session lifecycle checks, and mutation-unavailable
failures. It does not add transition/global-stop mutation APIs, worker
execution, or product read/report authority over SQLite.

B2c adds runtime writer issuance. Durable `writer_ownership` metadata remains
latest issuance evidence only, and mutation authority requires an active
internal `WriterSession` holding a private proof and the common
state-authority lock for the same retained state location. A copied
`writer_ownership` row in another managed database is not authority because
B3c1b derives the private bound database authority from the active operation
lease rather than from caller input. A copied row is evidence only; it cannot
replace the retained root/lock/database binding, and a hard-linked active
database alias is rejected while its link count exceeds one. In B2c, mutation
methods enter a private operation guard and still fail before any apply boundary with
`writer_session_mutation_unavailable`. The guard prevents close from releasing
the proof or advisory lock while a future operation is active. Operation
leases carry private operation identity and lifecycle epoch, retain the
concrete session wrapper, and no-op safely when a copied child lease exits
after fork. Same-thread close fails locally with
`writer_session_close_during_operation`; cross-thread and concurrent close
callers wait until proof cleanup, advisory-lock close, and registry cleanup have
completed.

B3c1b validation distinguishes durable managed-state contradictions from
operational SQLite failures while keeping the public mutation-store error graph
closed. Cursor-close failure after successful writer-row fetch is
`mutation_failed`; if fetch already failed, its original safe classification
remains primary.
The bound-open helper uses the same primary-failure rule for failed admission:
a post-open structural binding contradiction remains structural, and a
post-open operational failure remains operational, even if best-effort close of
the rejected SQLite connection also fails. That close failure is suppressed, not
chained, not retained, and no rejected connection is returned. Once a connection
has been admitted into controller transaction resolution, close failure is an
independent cleanup failure and maps to `mutation_failed`.

B3c2 private transition-event readers reuse the same closed SELECT posture for
transaction-internal event/idempotency and observed maximum-sequence reads. They
accept only `_MutationReadCapability`, expose no raw rows, JSON, digests,
SQL, parameters, paths, connection reprs, capability details, proofs, bindings,
or epochs, and reduce malformed rows, duplicate idempotency rows, wrong lookup
addresses, and malformed aggregate results to `database_integrity_failure`.
Operational SQLite failures remain `mutation_failed`. Cursor-close failure after
successful fetch is operational cleanup failure regardless of result code; if
execute or fetch failed first, that earlier safe classification remains primary.
The B3c2 idempotency lookup address must be exact built-in `str` input before
shared contract-ref validation, capability borrow, or SQL, so string subclasses
cannot run overridden behavior at this reader boundary. This is not a
repository-wide string-validation change. Real-capability fork tests are
deadline-bounded and always reap children. The readers do not call B3b2 context
readers, pure idempotency matching, pure sequence allocation, or any mutation
path.

B3c3 adds a private repr-safe dry-run result wrapper and private repr-hidden
bound-authority bundle, and the rollback-only transaction runtime must not
retain capability, connection, controller, operation lease, mutation lease,
epoch, credential, proof, filesystem binding, raw row, `TransitionContext`,
canonical JSON, digest, path, or evaluator internals in returned results or
safe errors. Preflight errors expose only closed private reason strings. The
pure binding helper classifies command/reference mismatch as
`validation_failed`, authoritative model contradiction as
`database_integrity_failure`, unsupported authorization as fail-closed
evaluator input, and `operator_policy` authorization as `validation_failed`.
B3c3 adds reader, matcher, timestamp, lease runtime, context, and evaluator
threat surface only inside one rollback-only private transaction. It adds no
maximum-sequence read, sequence allocation, write, CAS, commit, public
mutation behavior, or durable receipt surface.

B3a adds no runtime mutation authority. Its threat-model contribution is to
pin future transition context reconstruction, canonical event/replay digests,
lease runtime derivation, event-sequence overflow handling, and commit
uncertainty reporting before B3b/B3c implement SQLite readers or writes.

Descriptor lifecycle threats:

- explicit close remains the required operational release path;
- a private descriptor resource and one-shot finalizer provide fallback cleanup
  if a lock object is abandoned;
- finalizer timing is not deterministic and is not authority evidence;
- descriptor open results are immediately owned by cleanup scopes, and
  validation failures close before returning safe errors;
- a parent lifecycle/fork gate freezes a descriptor snapshot before fork;
- child fork cleanup does not acquire inherited Python locks, closes inherited
  descriptors from that snapshot, and does not explicitly unlock parent
  authority;
- B2c child session invalidation replaces inherited per-session
  synchronization with fresh child-local synchronization, increments the
  child-side lifecycle epoch, clears the child operation registry, clears the
  copied proof, and fails later child session use with
  `writer_session_process_mismatch`;
- the active-session registry is process-local and non-authoritative; inactive
  or fork-invalid resources are removed from the current process registry so
  the registry does not strongly retain stale resources;
- the at-fork child handler clears the copied active-session registry without
  acquiring inherited per-session synchronization, marks copied resources
  fork-invalid, and installs fresh child lifecycle synchronization;
- B2c session fallback finalization is nonblocking: it may mark cleanup
  deferred while operations remain active, and the last operation may become
  the single cleanup owner. Closing and cleaning are distinct; closed is
  published only after proof/lock cleanup and active-session registry cleanup
  complete;
- finalizer cleanup is quiet and must not emit paths, descriptors, process ids,
  inodes, raw OS errors, or authority reports.

The fork handling prevents this module's tracked descriptors from prolonging
authority in Python-managed forks. It does not make arbitrary multithreaded
fork safe, and third-party forks that bypass Python at-fork hooks remain an
accepted limitation; process-identity checks fail closed on later use.

Failed backup or restore:

- failed backups are not state authority;
- restore requires integrity and reconciliation validation before use.

## Future Hardening

Before executable A2, add fault-injection coverage for:

- power-loss simulation at each transaction step;
- disk-full behavior;
- migration interruption;
- backup/restore validation;
- corruption quarantine;
- stale writer after crash and restart.

B3c4a adds no new live threat surface: its write contracts are pure/static and
private, expose no SQL parameters, event contents, replay contents, command
contents, digests, refs, lease paths, credentials, proofs, state-root paths, or
raw exception causes in reprs or public errors, and are consumed only by the
private B3c4b transaction runtime and tests. B3c4b provides focused crash,
rollback, commit-uncertainty, restart, process, thread, fork, and capability
fault-injection proof pinned by the B3c4a proof matrix. B3c4b adds no public
global-stop delegation, no schema migration, and no related-repository
authority. B4b adds private global-stop persistence through the same neutral
mutation authority, verifies only already-persisted receipts, and adds no
receipt provisioner, public global-stop method, schema migration, or
related-repository authority.

## C2B3D Author-Effect Threat Boundary

C2B3D reuses the same writer, lock, mutation slot, controller, nominal
capability, connection custody, and uncertainty-cleanup authority. It creates
no second connection owner or recovery authority. Raw WorkSpec content and
typed pre-reduction evidence are cleared before transaction delegation; safe
commands, refs, digests, and persisted pending authority are correlation
evidence only. Supported ordinary errors are reduced to content-free store
errors after sensitive bindings clear, while `KeyboardInterrupt`, `SystemExit`,
and `GeneratorExit` preserve identity and use the existing process-control
stabilization boundary.

Replay and recovery reject incomplete or contradictory original families and
bounded current-head evidence. SQLite foreign keys alone are insufficient:
cancellation target/fence and immediate redelivery predecessor relations are
read and verified explicitly. The implementation performs no credential,
network, worker, Git, Bridge, ES, route-execution, capsule, logging, or other
external effect, and pending authority is never treated as permission.

<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_BEGIN -->
## Cognitive proposal and selection candidate

Section 41 of `.docs/c2b-durable-development-state.md` is the sole detailed semantic owner
for this bounded freeze. C2B3D remains current and unchanged. Section 41 is an
uncommitted contract candidate pending independent audit. Migration 0003 and all source/runtime remain absent.
The first later source tranche ends at typed pre-execution proposal admission plus Coordinator selection or non-selection;
it performs no model invocation or dispatch. In particular, model invocation, dispatch, worker contact, post-execution review, semantic decision, Git, and publication remain blocked.
The full remote-worker phase is not reduced to that first source tranche.
<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_END -->
