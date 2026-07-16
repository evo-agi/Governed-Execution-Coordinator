# Writer Session Authority

Status: B2b shared state-authority lock implementation plus B2a writer-session
authority contract. B2b implements the common advisory lock and integrates it
with SQLite initialize/migrate administration. No writer acquisition, proof
generation, SQLite writer-row update, concrete writer session, `StateStore`
mutation backend, worker, service, scheduler, executable authorization,
repair, commit, publication, or deployment behavior exists in B2b.

## Purpose

B2a settles the writer-authority vocabulary before implementation. B2b adds
the shared state-authority advisory lock that administration and future writer
acquisition must use. A durable SQLite row must never be enough to reconstruct
mutation authority. Future mutation authority is an opaque live `WriterSession`
created only by successful writer acquisition while the common state-authority
lock is held.

Python `Protocol` conformance is not authority. A caller cannot manufacture
mutation authority by creating an object with matching methods. The future
concrete backend must validate that the live session object is the
backend-created active session before any mutation can proceed.

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
credential, is not sufficient for mutation, and remains as latest issuance
evidence after graceful close or process crash.

### PrivateWriterCredential

`PrivateWriterCredential` is the private credential held only inside an active
future `WriterSession`. It contains:

- `writer_ref`;
- `generation`;
- `issued_ref`;
- raw private issuance proof.

The raw proof is never persisted, never serialized publicly, never logged,
never projected, and never returned by safe read APIs. B2a does not expose a
public production class for this credential.

### WriterSession

`WriterSession` is the opaque live mutation capability. A future concrete
session owns the advisory-lock descriptor, owns the private credential, is
bound to the acquiring process, and has an acquired, active, closing, and
closed lifecycle. Future mutation methods require an active session. The
session becomes invalid after close or process mismatch. Database metadata
alone cannot reconstruct it.

### SafeWriterMetadata

`SafeWriterMetadata` contains only:

- safe `writer_ref`;
- `generation`;
- safe `issued_ref`;
- `acquired_at`.

It contains no proof, no proof digest, no lock path, no process id, and no
liveness claim. It is evidence/diagnostics only and does not authorize
mutation.

Each concept has one responsibility: durable issuance records fencing state,
private credential proves issuance inside a live session, writer session owns
live mutation authority, and safe metadata is non-authoritative evidence.

## Durable Row And Liveness Truth

The SQLite `writer_ownership` row records the latest durable fencing issuance.
It is not current-process truth. It is not lock ownership truth.
It is not an active-session registry.
Absence or presence of a row does not prove whether a lock is held.
Safe metadata cannot reconstruct authority, and no B2a observer API claims liveness.

## Public Contract

B2a removes standalone public-token mutation authority. The old
reconstructable token-shaped object is not a mutation capability. Future
transition and global-stop mutation methods live on `WriterSession` only.

`StateStore` remains a read-side protocol in B2a. It exposes no mutation method
outside `WriterSession`. B2a does not define a production writer-acquisition
implementation.

There is no `current_writer()` read surface. B2a deliberately does not add
`read_latest_writer_issuance()`. A future administrative observer may define a
separate read contract for latest durable issuance metadata, but that read
would not prove liveness, would not return proof or digest, would not authorize
mutation, and requires its own audience, privacy, and error semantics.

## Failure Layer Taxonomy

| Layer | Owner | Examples | Boundary | Result semantics |
| --- | --- | --- | --- | --- |
| WriterSession lifecycle failure | `WriterSession` or its session wrapper | `writer_session_closed`, `writer_session_process_mismatch` | Before any `StateStore` or atomic apply call | No event, no apply conflict, no SQLite access, no idempotency disclosure, no fencing result, and no durable record. |
| Atomic apply conflict | Future fenced SQLite atomic boundary | `stale_writer_token`, `idempotency_key_reuse_conflict`, `expected_version_conflict`, `work_item_not_found` | Requires a session that passed local lifecycle checks | No event; may require a database transaction or read; remains distinct from session-local failures. |
| Domain result | Pure evaluator reached through the atomic boundary | accepted event or domain-rejected event | Reached only after session and apply checks pass | Exactly one accepted or domain-rejected event is the durable receipt. |

`writer_session_closed` and `writer_session_process_mismatch` are safe
session-local failure reasons. They are not `TransitionConflict` or
`GlobalStopConflict` classes and must not be added to apply-conflict reason
sets. `stale_writer_token` remains a fenced atomic-apply conflict for an
otherwise active session whose durable writer generation or issuance proof is
rejected.

## Failure Precedence

Future `WriterSession` mutation calls use this order:

1. Validate acquiring-process identity.

   If the current process identity differs, fail locally with
   `writer_session_process_mismatch`. No store call.

2. Validate session lifecycle.

   If the session is closing, closed, or inactive, fail locally with
   `writer_session_closed`. No store call.

3. Delegate to the fenced SQLite apply boundary.

4. At the apply boundary, validate writer generation and issuance proof.

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
`CoordinatorStateLocation.state_authority_lock_path`, validates it as a regular
non-symlink file with mode `0600`, acquires it nonblocking, and never unlinks
it during normal release. The state root must remain a secure local directory
with mode `0700`.

B2b uses a private descriptor-resource owner for the raw lock descriptor,
acquiring process identity, lifecycle state, and process-local registry
identity. The public lock wrapper is not the sole descriptor lifecycle record.
The wrapper registers a one-shot `weakref.finalize` cleanup callback against
the private resource. Explicit `close()` invokes the same one-shot cleanup path;
later garbage collection cannot close a different file that reused the old
descriptor number. The finalizer is a best-effort safety backstop for abandoned
objects, not an operational release protocol and not a cross-implementation
timing guarantee. The finalizer is disabled at interpreter shutdown; normal
process teardown releases descriptors there without depending on Python module
shutdown order.

Every opened state-authority lock descriptor is immediately owned by a cleanup
scope until it is transferred to the private descriptor resource. The parent
lifecycle/fork gate serializes descriptor opening, validation, nonblocking
`flock`, registry insertion, finalizer publication, explicit/finalizer close,
and pre-fork snapshot creation. If any validation or publication step fails,
the descriptor is closed, any acquired lock is released by descriptor closure,
and the same-process registry is cleared before a safe error is returned.

Lock possession alone is not writer authority. It is live-process exclusion
only. B2b does not issue writer generation, does not generate or verify a
private proof, does not change `writer_ownership`, and does not create a
concrete `WriterSession`.

## Session Lifecycle

The session lifecycle is:

- acquired;
- active;
- closing;
- closed.

An active session is required for future mutation. B2b implements and tests the
lock primitive itself, including acquired/active/closing/closed lifecycle,
idempotent close, same-process duplicate rejection, cross-process exclusion,
descriptor cleanup, and finalizer-backed abandoned-object cleanup. No concrete
`WriterSession` exists, and no writer has been acquired.

## Graceful Close And Process Crash

B2b pins and implements the lock-level release and crash behavior.
B2b implements and tests the lock primitive itself.
The writer-session rows in this matrix remain future because no concrete
`WriterSession` exists, no writer has been acquired, and B2c-B2e remain
future. The database row remains latest issuance evidence after close and does
not claim liveness.
The database row remains latest issuance evidence after close; the row remains latest issuance evidence only.
No concrete `WriterSession` exists.

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

The future session must remove references to the private proof on close. If the
proof is stored in a mutable buffer, implementation may attempt best-effort
overwrite before releasing references. The contract does not claim guaranteed
memory zeroization in Python or CPython. The proof must never appear in repr,
equality, hashing, serialization, exceptions, metadata, reports, or tests.
No guaranteed memory zeroization is claimed.

## Process, Fork, And Thread Rules

B2b lock primitive requirements, and future concrete writer-session
requirements:

- store the acquiring process id in the session;
- check the current process id on every lock/session operation;
- reject use in a forked child;
- mark the lock descriptor non-inheritable across exec;
- use `os.register_at_fork` where supported to invalidate child-side session
  state;
- close the inherited lock descriptor in the child handler where safe so the
  child cannot prolong parent authority;
- prohibit fork-after-acquisition;
- protect session lifecycle and mutation calls with a process-local mutex;
- reject duplicate active sessions in one process through a local registry
  keyed by the canonical state-authority lock identity.

`FD_CLOEXEC` alone does not solve fork inheritance.

B2b implements descriptor non-inheritance, process identity checks, duplicate
same-process lock rejection, and an at-fork child handler for inherited lock
resources. The parent at-fork preparation freezes a descriptor snapshot while
holding the lifecycle/fork gate. The child handler does not acquire inherited
Python locks, marks child-copy resources closed with invalid descriptor
sentinels, closes inherited descriptors from the snapshot without issuing an
explicit `LOCK_UN`, clears only the child-side copied registry, installs a
fresh child-local lifecycle gate, and leaves the parent's authority untouched.
Fork-after-acquisition remains prohibited and is not a takeover or failover
mechanism. Python's general warning about multithreaded fork still applies,
and third-party forks that bypass Python at-fork hooks remain outside the B2b
guarantee; process-identity checks fail closed on later use.

## Generation And Proof Specification

Future generation rules:

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

`writer_ref` and `issued_ref` are independently generated safe refs. Neither is
authority by itself.

The private proof is generated independently with `secrets.token_bytes(32)` and
remains memory-only.

The future proof digest uses SHA-256 with this exact domain separator:

`governed-execution.nwp-writer-issuance-proof.v1`

The canonical digest input is the UTF-8 encoding of the domain separator, a
single NUL byte, `writer_ref`, a single NUL byte, decimal `generation`, a
single NUL byte, `issued_ref`, a single NUL byte, and the raw 32-byte proof.
Verification compares digests with `hmac.compare_digest`.

B2b still specifies this proof contract only. B2b does not implement proof
generation or verification.
B2b does not implement proof generation or verification.

## Migration And Writer Exclusion

B2b initialize ordering:

1. observational preflight classification;
2. fail on `UNKNOWN` before lock-file creation or database mutation;
3. for `ABSENT`, `EMPTY`, or `MANAGED`, prepare the secure root and fixed
   state-authority lock file;
4. acquire the common state-authority lock;
5. re-run observational classification while the lock is held;
6. refuse if the state changed to `UNKNOWN`;
7. run the existing initialize flow, including current-schema no-op handling;
8. close SQLite;
9. release the lock.

B2b migrate ordering:

1. observationally require an existing managed database;
2. refuse `ABSENT`, `EMPTY`, `UNKNOWN`, wrong-posture, or drifted databases
   before lock-file creation or lock acquisition;
3. prepare and acquire the same fixed state-authority lock;
4. revalidate classification, schema, and migration history while the lock is
   held;
5. open create-disabled read/write;
6. `BEGIN IMMEDIATE`;
7. revalidate again inside the transaction;
8. apply packaged forward migrations if any exist;
9. commit or roll back;
10. close SQLite;
11. release the lock.

A no-op current-schema initialize or migrate still acquires the common lock and
revalidates so it cannot race a future writer session.

Future writer acquisition ordering:

1. require an existing `MANAGED` database;
2. validate the fixed state-authority lock file;
3. acquire the same exclusive lock;
4. open the database create-disabled read/write;
5. `BEGIN IMMEDIATE`;
6. revalidate schema and migration history;
7. issue the next generation and private proof;
8. update `writer_ownership`;
9. commit;
10. retain the lock descriptor for the `WriterSession` lifetime.

Any failure rolls back, closes the database, releases the lock, returns a safe
failure, and produces no usable partial session.

## Safe Failure Taxonomy

B2b lock failure classes:

- `unsupported_platform`;
- `unsafe_authority_lock`;
- `state_authority_lock_busy`;
- `state_authority_lock_failed`;
- `state_authority_lock_closed`;
- `state_authority_lock_process_mismatch`.

Future writer-acquisition failure classes may add:

- `database_not_managed`;
- `writer_generation_exhausted`;
- `writer_state_malformed`;
- `writer_session_closed`;
- `writer_session_process_mismatch`;
- `stale_writer_generation`;
- `invalid_issuance_proof`;
- `administrative_writer_conflict`.

Public errors must not expose paths, process ids, lock inode, raw OS errors,
proof, proof digest, partial comparison result, or database content.

## Schema Fit

Migration `0001_initial` is sufficient for the first writer-session model.
B2b requires no migration 0002. SQLite does not store active/released status,
release timestamp, process id, lock inode, platform metadata, heartbeat,
expiry, takeover state, or liveness flag. Those are session/process facts, not
durable authority.

## Non-Goals

B2b implements the common state-authority lock only. B2c remains future. B2b
does not implement `writer_ownership` updates and does not implement concrete
`WriterSession`. B2b does not implement concrete `WriterSession`.
B2b does not implement `writer_ownership` updates.

B2b does not implement:

- writer acquisition, renewal, release, generation, or fencing checks;
- private proof generation or verification;
- SQLite `writer_ownership` updates;
- concrete `WriterSession`;
- transition or global-stop mutation storage;
- product database reads;
- reports over SQLite;
- worker, scheduler, daemon, recovery loop, repair, local commit,
  publication, deployment, or executable authorization.
