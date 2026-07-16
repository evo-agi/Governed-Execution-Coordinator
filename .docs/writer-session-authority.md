# Writer Session Authority

Status: B2a contract correction only. No OS lock, writer acquisition,
proof generation, SQLite writer-row update, concrete writer session,
`StateStore` mutation backend, worker, service, scheduler, executable
authorization, repair, commit, publication, or deployment behavior exists in
B2a.

## Purpose

B2a settles the writer-authority vocabulary before implementation. A durable
SQLite row must never be enough to reconstruct mutation authority. Future
mutation authority is an opaque live `WriterSession` created only by successful
writer acquisition while the common state-authority lock is held.

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

The first backend uses one common state-authority advisory lock. The same
future exclusive lock covers:

- initialize;
- migrate;
- writer acquisition;
- the entire active `WriterSession` lifetime.

There are not separate migration and writer lock domains. Inspection and
validation remain observational and do not acquire writer authority.

The current on-disk filename is `coordinator-state.migration.lock`. B2a keeps
that filename for implementation compatibility, but the filename is an
implementation label, not durable schema identity and not the authority
concept. The code-owned path concept is the state-authority lock path.

B2a does not create, open, or acquire the lock.

## Session Lifecycle

The session lifecycle is:

- acquired;
- active;
- closing;
- closed.

An active session is required for future mutation. The detailed close and
crash matrix below is a B2a design/static contract only. No OS lock behavior
has been implemented or live-proven, no concrete `WriterSession` exists, and
no writer has been acquired.

## Graceful Close And Process Crash

B2a pins release and crash semantics as a design/static contract only.
No OS lock behavior has been implemented or live-proven.
No concrete `WriterSession` exists, no writer has been acquired, and B2b-B2e
remain future. The database row remains latest issuance evidence after close
and does not claim liveness.

| Circumstance | OS advisory lock outcome | SQLite transaction outcome | Durable `writer_ownership` row outcome | Session/credential outcome | Generation reuse rule | Next acquisition behavior |
| --- | --- | --- | --- | --- | --- | --- |
| Deliberate close | Future lock descriptor is closed after in-memory invalidation. | Close opens no new SQLite transaction. | No SQLite `writer_ownership` `UPDATE`, `DELETE`, or release-marker write occurs; the latest durable issuance row remains unchanged. | Session is marked closed/inactive before resource release; later operations fail with `writer_session_closed`; close is idempotent; future DB and lock resources are closed; private-proof references are dropped; a mutable proof buffer may receive best-effort overwrite; no guaranteed Python/CPython memory zeroization is claimed. | Graceful close does not decrement, clear, reset, release, or reuse the durable generation. | A later writer must acquire normally and increment from the latest durable generation. |
| Process crash before lock acquisition | No future OS lock has been acquired. | No issuance transaction exists. | No durable issuance effect. | No session or credential exists. | No generation is consumed. | Next acquisition starts from the latest durable generation already present. |
| Process crash after lock acquisition but before SQLite transaction | Future OS lock releases on process death through process/descriptor teardown. | No issuance transaction exists. | No durable issuance effect. | No returned session or usable credential exists. | No generation is consumed. | Next acquisition starts from the latest durable generation already present. |
| Process crash during uncommitted issuance transaction | Future OS lock releases on process death. | SQLite rolls back the uncommitted issuance transaction. | No committed writer row change survives. | No returned session or usable credential exists. | No committed generation exists to reuse. | Next acquisition reads the unchanged durable generation and increments from it. |
| Process crash after issuance commit but before session return | Future OS lock releases on process death. | The issuance transaction is already committed. | The committed durable generation remains latest issuance evidence only. | No session is reconstructed from the durable row; the private credential dies with the process. | The committed generation may be skipped but is never reused. | Next acquisition reads the committed durable generation and increments it. |
| Process crash while active | Future OS lock releases through process/descriptor teardown. | Any unrelated uncommitted SQLite transaction rolls back under normal SQLite rules. | No graceful-close update occurs; the row remains latest issuance evidence only. | Session and private credential die with the process. | The active committed generation is never reused. | Subsequent acquisition increments from the durable generation. |
| Process crash during graceful close | Process death eventually releases the future descriptor. | No SQLite release-marker transaction is required. | The durable issuance row remains unchanged. | Any surviving in-memory session state is unusable because the process died. | The committed generation is never reused. | Future acquisition increments from the durable generation. |

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

Future implementation requirements:

- store the acquiring process id in the session;
- check the current process id on every session operation;
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

B2a specifies this contract only. B2a does not implement proof generation or
verification.
B2a does not implement proof generation or verification.

## Migration And Writer Exclusion

Future initialize/migrate ordering:

1. validate or prepare the root and lock file;
2. acquire the common state-authority lock;
3. classify and revalidate the database;
4. initialize or migrate;
5. close the database;
6. release the lock.

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

Future B2 closed failure classes:

- `unsupported_platform`;
- `unsafe_authority_lock`;
- `writer_lock_busy`;
- `writer_acquisition_failed`;
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
B2a requires no migration 0002. SQLite does not store active/released status,
release timestamp, process id, lock inode, platform metadata, heartbeat,
expiry, takeover state, or liveness flag. Those are session/process facts, not
durable authority.

## Non-Goals

B2a does not implement `fcntl` or `flock`, does not implement
`writer_ownership` updates, and does not implement concrete `WriterSession`.
B2a does not implement `writer_ownership` updates.

B2a does not implement:

- `fcntl` or `flock`;
- lock-file creation, opening, validation, or acquisition;
- writer acquisition, renewal, release, generation, or fencing checks;
- private proof generation or verification;
- SQLite `writer_ownership` updates;
- concrete `WriterSession`;
- migration lock integration;
- transition or global-stop mutation storage;
- product database reads;
- reports over SQLite;
- worker, scheduler, daemon, recovery loop, repair, local commit,
  publication, deployment, or executable authorization.
