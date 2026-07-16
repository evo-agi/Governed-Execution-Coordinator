# Writer Session Authority

Status: B2c durable writer issuance and internal writer-session acquisition.
B2b implements the common advisory lock and integrates it with SQLite
initialize/migrate administration. B2c adds durable generation issuance,
private proof generation and verification, `writer_ownership` acquisition
updates, and an internal concrete `WriterSession`. B2c implements an internal concrete `WriterSession`.
No `StateStore` mutation backend, transition persistence, global-stop
persistence, worker, service, scheduler, executable authorization, repair,
commit, publication, or deployment behavior exists.

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
credential, is bound to the acquiring process, and has an active/closing/closed
lifecycle. Mutation methods exist on the session surface but fail locally with
`writer_session_mutation_unavailable` until B3/B4 implement storage.

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
Safe metadata cannot reconstruct authority; no B2a observer API claims liveness.
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

## Failure Layer Taxonomy

| Layer | Owner | Examples | Boundary | Result semantics |
| --- | --- | --- | --- | --- |
| WriterSession lifecycle failure | `WriterSession` or its session wrapper | `writer_session_closed`, `writer_session_process_mismatch`, `writer_session_mutation_unavailable` | Before any `StateStore` or atomic apply call | No event, no apply conflict, no SQLite access, no idempotency disclosure, no fencing result, and no durable record. |
| Atomic apply conflict | Future fenced SQLite atomic boundary | `stale_writer_token`, `idempotency_key_reuse_conflict`, `expected_version_conflict`, `work_item_not_found` | Requires a session that passed local lifecycle checks | No event; may require a database transaction or read; remains distinct from session-local failures. |
| Domain result | Pure evaluator reached through the atomic boundary | accepted event or domain-rejected event | Reached only after session and apply checks pass | Exactly one accepted or domain-rejected event is the durable receipt. |

`writer_session_closed`, `writer_session_process_mismatch`, and
`writer_session_mutation_unavailable` are safe session-local failure reasons.
They are not `TransitionConflict` or `GlobalStopConflict` classes and must not
be added to apply-conflict reason sets. `stale_writer_token` remains a fenced
atomic-apply conflict for an otherwise active session whose durable writer
generation or issuance proof is rejected.

Writer-acquisition failures use a separate closed vocabulary:

- `database_not_managed`;
- `writer_generation_exhausted`;
- `writer_state_malformed`;
- `writer_acquisition_failed`.

A common lock conflict may surface as `state_authority_lock_busy`.

## Failure Precedence

Future `WriterSession` mutation calls use this order:

1. Validate acquiring-process identity.

   If the current process identity differs, fail locally with
   `writer_session_process_mismatch`. No store call.

2. Validate session lifecycle.

   If the session is closing, closed, or inactive, fail locally with
   `writer_session_closed`. No store call.

3. In B2c, fail locally with `writer_session_mutation_unavailable`.

   No store call, SQLite apply call, event, apply conflict, or durable mutation
   occurs.

4. Delegate to the fenced SQLite apply boundary.

   This remains future B3/B4 behavior.

5. At the apply boundary, validate writer generation and issuance proof.

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
8. Read and strictly validate the `writer_ownership` singleton row.
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
- closed.

B2c implements and tests an internal concrete `WriterSession`. The session
retains the B2b state-authority lock for its lifetime, holds the private
credential, exposes only safe metadata, and closes the acquisition SQLite
connection before returning to the caller.

Mutation methods in B2c first validate process identity, then active lifecycle,
then fail locally with `writer_session_mutation_unavailable`. They do not open
SQLite, do not call a `StateStore` apply method, do not inspect idempotency, do
not emit an event, and do not mutate state.

## Graceful Close And Process Crash

B2b implements and tests the lock primitive itself. B2c implements and tests an internal concrete `WriterSession`.
The database row remains latest issuance evidence after close and the row
remains latest issuance evidence only. database row remains latest issuance
evidence after close.

| Circumstance | OS advisory lock outcome | SQLite transaction outcome | Durable `writer_ownership` row outcome | Session/credential outcome | Generation reuse rule | Next acquisition behavior |
| --- | --- | --- | --- | --- | --- | --- |
| Deliberate close | Lock descriptor is closed after in-memory invalidation. | Close opens no new SQLite transaction. | No SQLite `writer_ownership` `UPDATE`, `DELETE`, or release-marker write occurs; the latest durable issuance row remains unchanged. | Session is marked closed/inactive before resource release; later operations fail with `writer_session_closed`; close is idempotent; future DB and lock resources are closed; private-proof references are dropped; a mutable proof buffer may receive best-effort overwrite; no guaranteed Python/CPython memory zeroization is claimed. | Graceful close does not decrement, clear, reset, release, or reuse the durable generation. | A later writer must acquire normally and increment from the latest durable generation. |
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
- protect session lifecycle and mutation calls with a process-local mutex;
- reject duplicate active sessions through the common lock and keep any
  process-local registry non-authoritative.

`FD_CLOEXEC` alone does not solve fork inheritance.

B2c child-side session cleanup clears copied active-session registry state,
marks inherited session resources closed, best-effort overwrites and drops the
private proof in the child, and does not issue `LOCK_UN`. B2b remains
responsible for inherited lock-descriptor closure. Parent authority remains
unchanged. Python's general warning about multithreaded fork still applies,
and third-party forks that bypass Python at-fork hooks remain outside the B2c
guarantee; process-identity checks fail closed on later use.

## Generation And Proof Specification

Generation rules:

- first generation is `1`;
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
durable authority.

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
