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

The current migration application generation is 1, the terminal catalog is
exactly `0001_initial`, and `0001_initial.sql` is the sole production migration
resource. Migrations 0002/0003 and application generation 2 remain absent.

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
  catalog (currently only `0001_initial`);
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
