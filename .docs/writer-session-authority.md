# Writer Session Authority

Status: B2c durable writer issuance, internal writer-session acquisition,
B3c1a private WriterSession authority plumbing, and B3c1b private
rollback-only writer-fencing/capability mechanics. B3c3 adds a private
rollback-only transition dry-run runtime but no public writer-session mutation
behavior.
B2b implements the common advisory lock and integrates it with SQLite
initialize/migrate administration. B2c adds durable generation issuance,
private proof generation and verification, `writer_ownership` acquisition
updates, and an internal concrete `WriterSession`. No `StateStore` mutation
backend, transition persistence, global-stop
persistence, worker, service, scheduler, executable authorization, repair,
commit, publication, or deployment behavior exists.
B2c implements an internal concrete `WriterSession`. B3c1a implements only the
private resource-owned mutation slot, mutation lease, operation-lease authority
checks, and durable-issuance verification. B3c1b implements only the private
rollback-only writer-fencing/capability mechanics that consume that private
verification interface.
B3c3 contracts do not change writer-session public methods and add no
production transaction caller.

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
active/closing/cleaning/closed lifecycle. Mutation methods exist on the session
surface but fail locally with
`writer_session_mutation_unavailable` until B3/B4 implement storage.
B3c1a implements the private slot that uses
`writer_session_mutation_in_progress` for a second concurrent private mutation
attempt on the same session. Public mutation methods still do not acquire that
slot.

### SafeWriterMetadata

`SafeWriterMetadata` contains only:

- safe `writer_ref`;
- `generation`;
- safe `issued_ref`;
- `acquired_at`.

It contains no proof, no proof digest, no lock path, no process id, and no
liveness claim. It is evidence/diagnostics only and does not authorize
mutation.

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

B3b2a adds a private `_TransitionReadCapability` protocol for future
B3c-managed transition transactions, but it is not writer authority, not public
read authority, not a `StateStore` method, not a database handle for callers,
and not a concrete production capability. B3b2b consumes that protocol from
private SELECT readers and verifies only that the borrowed object is a
`sqlite3.Connection`; this helper check is not an authority check and does not
prove transaction identity. `connection.in_transaction` is not transaction
identity and does not prove `BEGIN IMMEDIATE`, writer fencing, private proof
possession, or B2 operation guard ownership. Future B3c must create one
concrete opaque epoch only after those gates, invalidate it before commit or
rollback, and reject old epochs after transaction end or restart on the same
connection.
B3c0a additionally pins that the concrete capability is nominal. B3c1
prerequisites in `.docs/b3c1-prerequisite-contract.md` reconcile production
reachability: the capability is created only by one private rollback-only
transaction controller. There is one controller construction path. Future
production invocation may occur only from
`_SQLiteWriterSession.apply_transition()`. During B3c1b, the controller has no
production caller, and coherent tests may invoke the same private controller
directly through private imports without adding a separate source-level
`for_test` factory. The controller entry point accepts only the active
operation lease; it derives the private state-database filesystem binding from
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
| Atomic apply conflict | Future fenced SQLite atomic boundary | `stale_writer_token`, `idempotency_key_reuse_conflict`, `expected_version_conflict`, `work_item_not_found`, `validation_failed` | Requires a session that passed local lifecycle checks | No event; may require a database transaction or read; remains distinct from session-local failures. |
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

2. In B2c, fail locally with `writer_session_mutation_unavailable`.

   No store call, SQLite apply call, event, apply conflict, or durable mutation
   occurs. The private operation guard is entered and exited around this local
   failure to pin future B3/B4 close-versus-apply ordering.

3. In future B3/B4, perform mutation-specific local command-shape checks.

   Transition checks include exact `TransitionCommand` type/digest,
   non-READY dependency ref null, and zero budget cost. Global-stop checks retain
   the future typed command/operator-decision local checks without widening B4
   semantics.

4. In B3c1a private plumbing and future B3/B4 mutation runtime, acquire the
   shared per-session mutation slot.

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

B2c writer acquisition order is:

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
