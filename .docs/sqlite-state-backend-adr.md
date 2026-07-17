# SQLite State Backend ADR

Status: accepted architecture; B2b implements bootstrap, observational
inspection/validation, migrations, and the common state-authority advisory
lock for initialize/migrate administration. B2a corrects the writer-session
authority contract. B2c implements durable writer issuance and internal
writer-session acquisition for managed SQLite databases.

B0 selects one private local SQLite database as the first production state
backend architecture for the future NWP Coordinator. B1/B1.1 implements
explicit operator-local database bootstrap, observational validation, and
migrations. B2a replaces standalone reconstructable public mutation authority
with an opaque future `WriterSession` contract and safe writer metadata. B2b
adds the common state-authority lock and uses it for initialize/migrate. B2c
adds internal writer acquisition, a private operation guard, and
session-local mutation-unavailable behavior. B2c does not implement a
production `StateStore`, start a
coordinator service, or enable executable A2 behavior.

## Decision

The first backend will use one SQLite database behind the `StateStore` port.
All transition and global-stop mutations must occur inside one SQLite
transaction that owns writer fencing, idempotency inspection, authoritative
current-state loading, decision-context verification, expected-version
comparison, pure evaluator invocation, event insertion, current-state update,
and exact replay.

Rejected first-backend alternatives:

- A bespoke append-only journal. It would need custom locking, compare-and-set,
  idempotency indexes, current-state materialization, torn-write recovery,
  migrations, backup, restore, corruption handling, and global-stop reads.
- A journal plus separate materialized-state store. It creates dual durable
  truth unless another atomic authority is invented.
- An external service. The first backend must be local, deterministic, and not
  require an external service.

## B0 Scope

B0 may contain:

- architecture documents;
- a non-production SQL schema fixture;
- static tests;
- tests that execute the fixture against `sqlite3.connect(":memory:")`.

B0 must not contain:

- production SQLite connection code;
- `sqlite3` imports under `src/`;
- persistent `.db`, `.sqlite`, journal, WAL, or SHM files;
- a migration runner;
- writer acquisition;
- a coordinator loop, worker, scheduler, daemon, queue, repair, sandbox,
  local commit, publication, or deployment behavior.

## B1 Scope

B1/B1.1 may contain:

- production SQLite connection/bootstrap code using the Python standard
  library;
- fixed local state-location and filesystem-permission validation;
- packaged migration resources loaded from the installed Coordinator package;
- observational existing-database inspection/validation that does not create or
  mutate files or persistent journal posture;
- forward-only migration execution for explicit administrative initialize and
  migrate operations;
- migration-history/catalog equality and schema/application compatibility
  validation;
- live-schema manifest verification for the initial migration;
- bootstrap and generic managed current-state invariant validation.

B1/B2b must not contain:

- a SQLite `StateStore` implementation;
- `StateStore.apply_transition` or `StateStore.apply_global_stop_update`
  implementation;
- writer acquisition, writer issuance, proof generation, or
  `writer_ownership` mutation;
- product reads or report generation over the database;
- work-item, decision receipt, transition event, global-stop event, or
  global-stop current-state mutation APIs outside schema bootstrap;
- executable authorization, scheduling, worker execution, repair, commit,
  publication, service, daemon, or deployment behavior.

B2c may contain only internal writer acquisition, proof generation/digest
verification, `writer_ownership` issuance updates, private operation guarding,
and a concrete internal `WriterSession` whose mutation methods fail locally.
B2c must not contain a SQLite `StateStore`, event persistence, work-item
mutation, global-stop mutation, reports over writer issuance, service
behavior, worker execution, or executable A2 behavior.

## Backend Responsibility Matrix

Coordinator transition service:

- validates external command and typed-context shape before calling the store;
- invokes the `StateStore` port;
- does not write SQLite directly once the production store exists;
- does not call Bridge, Codex, workers, reports, remotes, or authorization
  providers inside the mutation transaction.

SQLite `StateStore` transaction:

- is entered only through a backend-created active `WriterSession`;
- validates writer ownership before idempotency disclosure;
- performs internal idempotency lookup from event rows;
- loads authoritative current work-item or global-stop state;
- loads or verifies persisted decision receipts;
- compares expected version;
- invokes the pure evaluator with no external I/O;
- writes one event, the replay snapshot, and any current-state change
  atomically;
- returns either an apply conflict or an authoritative committed outcome.

Pure evaluator:

- owns domain rules only;
- constructs accepted or domain-rejected events;
- does not perform persistence, writer fencing, idempotency lookup, reports, or
  external authorization.

Reports:

- Reports are projections only.
- are projections only;
- are never database input;
- are never current-state authority;
- cannot expose raw rows or canonical JSON as public payloads.

Bridge, Control Plane, Execution Substrate, Maintenance Agent, and
Infrastructure Manager:

- have no database handle;
- have no state-write authority;
- remain external authorities, adapters, evidence sources, or projections
  according to their existing boundaries.

## Journal Mode Decision

The first implementation posture is:

- `journal_mode=DELETE`;
- `synchronous=FULL`;
- `locking_mode=NORMAL`;
- `BEGIN IMMEDIATE` for mutation transactions;
- `foreign_keys=ON`;
- `trusted_schema=OFF` where supported;
- bounded `busy_timeout`.

Rollback journal / DELETE mode is selected for B0 because the first backend has
one local writer, short in-process reads, simpler containment, fewer persistent
auxiliary files, and simpler offline/online backup posture.

WAL remains a future option. WAL improves reader concurrency, but it introduces
persistent `-wal` and `-shm` files, checkpoint policy, and a broader filesystem
surface. Selecting WAL requires a current source-backed concurrent-reader need
and a focused operations/recovery audit.

Journal mode is an implementation posture, not durable contract identity.
Changing it later requires an operations and recovery audit.

## Writer Ownership Model

The first local writer model is:

- one common state-authority lock file in the same secured state directory;
- an exclusive OS advisory lock for live-process exclusion;
- a durable singleton `writer_ownership` row;
- monotonically increasing generation;
- independently generated safe writer and issuance refs;
- a private random opaque 256-bit issuance proof held only in an active
  `WriterSession`;
- only a domain-separated issuance proof digest stored in the database;
- every mutation compares writer ref, generation, and issuance proof;
- new acquisition increments generation atomically;
- process crash releases the OS lock;
- no TTL, heartbeat, or automatic failover in the first backend;
- hung-writer recovery requires explicit operator action.

The OS lock is live-process exclusion. The durable generation and private
issuance proof are fencing authority. Neither is sufficient alone. The durable
row is latest issuance evidence, not liveness truth. Safe writer metadata is
not a credential. Process-local lifecycle synchronization and the private
operation guard are necessary session controls but are not sufficient
authority. Workers, Bridge, reports, readers, and adapters never receive writer
sessions or private writer credentials.

B2b implements the lock-file creation, validation, nonblocking exclusive
`fcntl.flock` acquisition, release, fork/exec descriptor hygiene, same-process
exclusion, cross-process exclusion, crash release behavior, and initialize/
migrate integration for that common lock. B2c implements writer issuance
generation, proof generation and verification, `writer_ownership` acquisition
updates, and the internal concrete writer session. It still implements no
mutation backend. The detailed writer-session contract lives in
`.docs/writer-session-authority.md`.
B2b descriptor hygiene includes immediate cleanup ownership after `os.open`,
a parent lifecycle/fork gate for publication and pre-fork snapshot creation,
and child cleanup that closes inherited descriptors without acquiring
inherited Python locks or issuing `LOCK_UN`.

## Event-Owned Idempotency

The first schema uses event-owned idempotency:

- `transition_events` owns unique `(work_item_id, idempotency_key)`;
- `global_stop_events` owns unique `idempotency_key`;
- no separate idempotency tables exist in the first schema;
- if the key and command digest match, replay returns the stored event plus the
  stored replay snapshot;
- if the key matches but digest differs, the store returns an apply conflict
  and creates no event;
- if no event exists, no idempotency record exists.

Exact replay snapshots do not become current-state truth. They are authoritative
only for replaying the original command outcome.

## Transaction Order

Transition mutation transaction:

1. `BEGIN IMMEDIATE`.
2. Verify the active writer session, writer generation, and issuance proof.
3. Look up `transition_events` by `(work_item_id, idempotency_key)`.
4. If command digest matches, return stored event and replay snapshot.
5. If command digest differs, return `idempotency_key_reuse_conflict`.
6. Load authoritative `work_items`.
7. Compare command expected version.
8. Load authoritative `global_stop_current`.
9. Load lease identity, authorization, and dependency decision receipts.
10. Require command and typed context to match persisted receipts, or rehydrate
    context exclusively from persisted receipts.
11. If locally valid typed references or digests do not match authoritative
    persisted records, return a `validation_failed` apply conflict with no
    event. Parser, model-construction, session-lifecycle, and
    mutation-unavailable failures do not reach this step.
12. Invoke the pure evaluator with no external I/O.
13. Insert exactly one transition event and replay snapshot.
14. On acceptance, update `work_items`.
15. On domain rejection, leave `work_items` unchanged.
16. Commit.
17. Return the committed event and resulting record.

Exact replay happens after writer-session fencing and idempotency match, before
changed decision or global-stop context is re-evaluated.

Global-stop mutation transaction:

1. `BEGIN IMMEDIATE`.
2. Verify the active writer session, writer generation, and issuance proof.
3. Look up `global_stop_events` by idempotency key.
4. If command digest matches, return stored event and replay snapshot.
5. If command digest differs, return `idempotency_key_reuse_conflict`.
6. Load authoritative `global_stop_current`.
7. Compare command expected version.
8. Load the operator decision receipt.
9. Verify command and typed operator decision against the persisted receipt;
   mismatch is a `validation_failed` apply conflict, not a parser/session
   failure.
10. Invoke the pure global-stop evaluator with no external I/O.
11. Insert exactly one global-stop event and replay snapshot.
12. On acceptance, update `global_stop_current`.
13. On domain rejection, leave `global_stop_current` unchanged.
14. Commit.
15. Return the committed event and resulting global-stop state.

## Context Provenance

New commands must use authoritative decision and global-stop records loaded or
verified inside the transaction:

- lease identity decision ref must exist and bind to the same lease;
- authorization decision ref must exist and bind to the same lease;
- dependency decision ref must exist when required by the target state;
- global stop is loaded from `global_stop_current`;
- command global-stop ref and version must agree with the authoritative
  snapshot;
- persisted schema ids and canonical digests must validate before evaluator
  use;
- externally supplied typed decisions are never trusted solely by shape.

This backend does not solve executable authorization. Until a separate
authorization architecture is accepted, current production truth remains
fail-closed and unsupported.

If the P1.1 conflict vocabulary is too coarse for a context-provenance mismatch,
B3 must add an explicit contract extension instead of inventing hidden backend
behavior.

## Migration Architecture

The authoritative migration source of truth is the `schema_migrations` table.
Migration ids are ordered and checksummed. Migrations are forward-only,
transactional, and require backup before destructive changes. Interrupted
migrations roll back. Old binaries must refuse newer schemas. New binaries
either migrate older schemas or refuse safely. Automatic downgrade is not
supported; restore is the rollback path.

`PRAGMA user_version`, if used later, is only a checked convenience mirror.

B1/B1.1 implements the initial migration catalog and runner. Migration SQL is
loaded only from code-owned package resources and never from arbitrary
filesystem paths. Connection PRAGMAs are set and verified by bootstrap code and
are not part of migration identity. Observational B1.1 inspection/validation
uses a separate create-disabled connection path and queries persistent journal
posture instead of changing it. Administrative initialize remains the
create-capable path. Administrative migrate requires managed observational
preflight before opening read/write. B2b initialize and migrate acquire the
same state-authority lock after observational preflight and revalidate while
the lock is held. B2c writer acquisition requires an existing managed
database, revalidates while holding that same lock, validates again inside
`BEGIN IMMEDIATE`, updates only `writer_ownership`, commits, closes the
acquisition connection, and retains the lock in the returned internal session.
B1.1 and B2c treat a missing writer row as the valid pre-first-acquisition
state and a present generation `0` row as malformed managed writer state. B2c
mutation-unavailable methods enter and exit the private operation guard so
future B3/B4 transactions can retain proof and advisory-lock authority across
the full operation. No B3/B4 persistence exists.

Migration `0001_initial` creates the first schema and seeds only a canonical
clear `global_stop_current` singleton at version 0. B1.1 validates that
bootstrap seed immediately after initialize, then validates later managed
databases with generic current-state shape rules rather than forcing permanent
version-0 clear state. The migration does not seed a writer, work items,
backlogs, lease identity records, authorization receipts, decision receipts,
transition events, global-stop events, active global stop, or executable
authorization.

## Non-Goals

B2c does not implement transition persistence, global-stop persistence,
idempotency lookup, expected-version checks, crash recovery orchestration,
production read ports, a `StateStore` mutation backend, worker execution,
scheduling, authorization, sandboxing, repair, local commit, publication, or
deployment.
