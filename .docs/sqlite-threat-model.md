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

C2B2 Slice 1 advances only the managed physical schema to application
generation 2 / terminal migration 0002. Its nineteen empty-at-install tables do
not add C2B row/value code, readers, mutations, runtime authority, or new
filesystem or process authority.

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
