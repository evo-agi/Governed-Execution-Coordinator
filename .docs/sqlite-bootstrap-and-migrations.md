# SQLite Bootstrap And Migrations

Status: B2b implements operator-local SQLite bootstrap, observational
inspection/validation, schema validation, the common state-authority lock, and
initialize/migrate lock integration. B2a documents the writer-session contract.

B1/B1.1 implements a secure local SQLite state-location policy, split
read-only and administrative connection posture, packaged migration catalog,
forward-only migration runner, initial schema installation, migration-history
catalog equality, live-schema manifest validation, managed current-state
invariant checks, schema/application compatibility checks, and a shared
state-authority advisory lock used by initialize/migrate administration. It
does not
implement `StateStore` mutation semantics, writer ownership acquisition,
writer acquisition, work-item mutation APIs, global-stop mutation
APIs, product reads, reports over the database, authorization, worker
execution, scheduling, repair, local commit, publication, or service behavior.

Inspection and validation are observational existing-database operations.
They must not create a missing state root, create a database file, write a
SQLite header, change persistent `journal_mode`, create or delete sidecars, or
repair/adopt unknown schema. Bootstrap and migration are explicit
operator-local administrative operations. They are not connector, MCP,
command-payload, backlog, lease, work-item, report, or remote-input
operations. Normal future runtime must not execute migrations concurrently
with an active Coordinator writer session. B2b ensures initialize and migrate
use the same state-authority lock that future writer acquisition must hold.
B2c owns writer acquisition and fencing. B3/B4 own transition and global-stop
atomic mutation.

## Responsibility Owners

The B1 SQLite bootstrap modules own:

- state-root selection: `CoordinatorStateLocation` derives a deterministic
  per-user local state root from the canonical NWP Coordinator component name,
  with tests injecting temporary roots;
- state-directory creation and validation: owner-only local directories,
  symlink rejection, regular-file checks, fixed database filename, and
  confinement under the trusted root;
- SQLite connection posture: administrative initialize applies
  `foreign_keys=ON`, rollback journal DELETE mode, `synchronous=FULL`,
  `locking_mode=NORMAL`, bounded busy timeout, `trusted_schema=OFF` where
  supported, disabled extension loading, and explicit transaction control;
  observational connections use create-disabled read-only mode where practical,
  apply only non-persistent connection-local safety settings, and query rather
  than set persistent journal posture;
- migration catalog: code-owned packaged resources loaded with
  `importlib.resources`, never arbitrary filesystem migration paths;
- migration history: `schema_migrations` rows record migration identity,
  sequence, exact checksum, application compatibility bounds, and application
  time of successful commit; managed validation requires those rows to equal
  the packaged catalog exactly, including compatibility bounds and timestamp
  shape;
- schema compatibility checks: old binaries refuse newer unsupported schema,
  newer binaries migrate only through explicit migration calls, incompatible
  history refuses closed, checksum mismatch refuses closed, gaps refuse closed,
  unknown migrations refuse closed, and the live schema must match a
  deterministic manifest derived from the packaged migration result;
- bootstrap, inspection, validation, and migration errors: closed safe error
  classes or safe classifications that avoid raw SQL, raw DDL, absolute paths,
  database content, canonical JSON, credentials, endpoints, environment,
  SQLite exception text, and trust material;
- future destructive migration backup metadata: B1 defines the boundary that a
  destructive migration requires a separately verified backup receipt, but B1
  implements no backup files and no destructive migration.

The atomic `StateStore` boundary remains future work. It will own writer
fencing, idempotency lookup, current-state loading, expected-version comparison,
pure evaluator invocation, exact replay, and atomic state/event persistence.

## State Location

The default B1 state root is a deterministic per-user local directory for the
canonical NWP Coordinator component, not the repository display name. It is not
accepted from connector, MCP, work input, command payload, lease, backlog,
report, or remote input. Tests use temporary directories and must not create
the operator's real state root.

The B1 policy exposes only:

- state root;
- fixed database file path;
- fixed state-authority lock path;
- backup directory path reserved for future backup receipts.

The lock filename remains `coordinator-state.migration.lock` for implementation
compatibility, but that filename is not durable schema identity and is not the
authority concept. The lock domain is the single common state-authority lock
domain.

The first fixed database filename is `coordinator-state.sqlite`. Alternate
database filenames and path traversal are rejected. The state root must be
private to the local operator account, outside repository checkouts, and on a
local filesystem. B1 performs only portable source-backed filesystem checks and
does not overclaim detection of every network mount type.

## Filesystem Posture

The state root is created with mode `0700` when absent. Existing roots must be
directories, not symlinks, owner-owned where portable, and free of group/other
permissions. Child paths are resolved and confined to the trusted root.

The database file is created with mode `0600` when absent. Existing database
paths must be regular files, not symlinks, directories, FIFOs, sockets, or
devices, and must reject group/other permissions. The B2b state-authority lock
file is created at the fixed path with mode `0600`, validated as a regular
non-symlink file, rejected when group/other-accessible, rejected when hardlinked
where link count is safely testable, acquired with a nonblocking exclusive
advisory lock, and left in place after release. Public errors never echo raw
paths.

Python `sqlite3` opens the database by pathname. The owner-only parent
directory mitigates other-user replacement, but same-account malicious-process
resistance is limited. B1 does not claim no-follow semantics that the standard
library SQLite API does not provide.

## Connection Posture

Connection posture is separate from migration DDL. Migration identity does not
include PRAGMAs from the B0 schema fixture. B1.1 no longer uses the same
create-capable connection path for every operation. Observational
inspect/validate opens only an existing file, uses create-disabled read-only
mode where practical, applies only connection-local safety settings, and
queries persistent journal posture. Administrative initialize is the only
create-capable public operation. Administrative migrate uses create-disabled
read/write mode only after observational managed preflight and revalidation.
Values are bounded and not arbitrary SQL input.

B1 uses rollback journal DELETE mode. WAL is not selected. Successful migration
commits must not leave persistent `-wal` or `-shm` files. A WAL-mode or other
wrong-posture database is classified safely without converting it to DELETE;
B1.1 does not use immutable reads to claim authoritative validation while
ignoring live WAL state.

## Migration Catalog

Migrations are packaged under `ge_nwp_coordinator.sqlite_migrations`. Each
migration has an id, sequence, exact SQL resource content, SHA-256 checksum over
the exact packaged bytes, minimum and maximum compatible application schema,
destructive flag, and description.

The catalog is forward-only. It does not support downgrade or reverse
migration. Destructive migrations require a separately verified backup receipt
in a future tranche; B1 refuses destructive migrations without implementing
backup files.

## Initial Migration

Migration `0001_initial` deliberately derives the B0 schema fixture by removing
connection PRAGMAs from migration identity and keeping schema DDL under package
resource authority. The migration creates:

- `schema_migrations`;
- `writer_ownership`;
- immutable lease, backlog, authorization, dependency, and operator-decision
  receipt tables;
- `work_items`;
- `transition_events`;
- `global_stop_current`;
- `global_stop_events`;
- append-only triggers, foreign keys, unique constraints, checks, and required
  schema constraints.

Migration `0001_initial` seeds one canonical clear `global_stop_current` row at
version 0. This row is not a global-stop event, not an operator decision, and
not executable authorization. It exists so future readers can fail closed
against an explicit clear current-state singleton instead of inventing a
missing default.

Migration `0001_initial` does not seed an active writer, work items, backlogs,
lease identity records, authorization receipts, dependency receipts,
transition events, global-stop events, global-stop operator decision receipts,
or executable authorization.

The reserved `operator_policy` vocabulary in the authorization receipt schema
is not an accepted authorization implementation. B1 adds no insertion API for
operator policy receipts and seeds no authorized or executable receipt.

## Database Classification

B1.1 classifies the fixed database path:

- absent: the fixed database file does not exist; inspection/validation do not
  create it;
- empty: an existing empty SQLite database or private zero-byte placeholder
  with no user-defined schema objects and no migration history;
- managed: authoritative migration history exactly matches the packaged
  catalog, the full live schema manifest matches the packaged migration
  result, and managed current-state invariants pass;
- unknown/partially initialized: any unrecognized user-defined schema object,
  views or triggers without authoritative migration history, explicit indexes
  not in the expected manifest, invalid migration history, unexpected
  migration rows, duplicate sequence or id, checksum mismatch, migration gap,
  newer unsupported schema, incompatible or non-equal application bounds,
  unsupported journal posture, malformed schema, or failed managed invariant.

Unknown databases fail closed. B1 does not guess, adopt, drop, repair, or
rewrite tables.

User-defined schema accounting covers tables, views, explicit indexes, and
triggers from `sqlite_schema`. B1.1 ignores only SQLite internal `sqlite_%`
objects and autoindexes that are accounted for through table/index
introspection. A view-only database is unknown, not empty.

## Schema Manifest

B1.1 derives an expected live-schema manifest by creating a temporary in-memory
SQLite database from the exact packaged migration bytes under the current
runtime and extracting a deterministic allowlisted representation. The manifest
includes user schema objects, normalized object definitions, table columns,
declared types, nullability, defaults, primary keys, foreign keys, index lists,
index columns/order/uniqueness, views, triggers, and object relationships.

The live managed database must match that manifest. The stored migration SQL
checksum proves only which migration resource was recorded; it is not treated
as proof that the live schema still matches that resource.

## Transaction Model

B2b initialize execution order is:

1. Observationally classify the fixed path.
2. Refuse unknown or partial databases without creating the lock file or
   mutating database posture.
3. For absent, empty, or managed databases, securely prepare the state root and
   fixed state-authority lock file.
4. Acquire the common exclusive state-authority lock.
5. Re-run observational classification while the lock is held.
6. Refuse if the database changed to unknown.
7. For an already valid current managed database, return idempotently while
   still holding and then releasing the lock.
8. Otherwise open the local database, apply and verify administrative
   connection posture, begin an explicit SQLite transaction, execute only
   packaged migration SQL, verify the live schema manifest and bootstrap
   invariants, insert the migration-history row with checksum and compatibility
   bounds, and commit.
9. Revalidate migration history, schema manifest, and managed invariants.
10. Close SQLite and release the lock.

B2b migration execution order is:

1. Observationally require an existing managed database.
2. Refuse absent, empty, unknown, wrong-posture, partial, or drifted databases
   without creating or acquiring the lock.
3. Prepare and acquire the same fixed state-authority lock.
4. Revalidate managed classification, schema, and migration history while the
   lock is held.
5. Open create-disabled read/write.
6. Begin an explicit `BEGIN IMMEDIATE` SQLite transaction.
7. Revalidate history/schema again inside the transaction.
8. Execute only packaged forward migrations when any exist.
9. Verify schema, history, and managed invariants before commit.
10. Commit or roll back, close SQLite, and release the lock.

On failure, B2b rolls back any active SQLite transaction and releases the lock.
There must be no partial schema without history and no history row without
schema. Failed migrations return safe closed error classes. A no-op
current-schema initialize or migrate still acquires the common lock and
revalidates, preventing a race with a future writer session.

B2b administrative call sites use structured context-manager closure for the
state-authority lock. The descriptor has a private resource owner and a
one-shot finalizer fallback for abandoned lock objects, but finalization is not
a release-timing guarantee and is not a substitute for explicit close. Lock
cleanup never unlinks the persistent lock file, never touches SQLite after the
administrative connection is closed, and never changes `writer_ownership`.
Every state-authority lock descriptor is immediately owned by a cleanup scope
after `os.open`; failed root or lock-file validation closes the descriptor
before returning a safe error. The parent lifecycle/fork gate covers opening,
validation, `flock`, registry insertion, finalizer publication, explicit or
finalizer close, and pre-fork snapshot creation. The at-fork child handler is
lock-free with respect to inherited Python locks and closes inherited
descriptors from the frozen snapshot without issuing `LOCK_UN`.

Future writer acquisition must require an existing `MANAGED` database, validate
and acquire the same lock, open the database create-disabled read/write,
`BEGIN IMMEDIATE`, revalidate schema/history, issue the next generation and
proof, update `writer_ownership`, commit, and retain the lock descriptor for
the `WriterSession` lifetime. Any failure rolls back, closes the database,
releases the lock, returns a safe failure, and creates no usable partial
session.

B2b does not update `writer_ownership`.

## Compatibility Rules

At explicit bootstrap or validation:

- old binary plus newer unsupported schema refuses;
- new binary plus older supported schema requires explicit migration;
- incompatible older schema refuses;
- checksum mismatch refuses;
- migration gap refuses;
- unknown migration id refuses unless a future versioned compatibility rule
  explicitly permits it.

Opening the database for ordinary future product reads or mutations must not
implicitly run migrations.

## Non-Authority Boundary

B1 does not implement `StateStore.apply_transition`,
`StateStore.apply_global_stop_update`, SQLite product reads, reports over the
database, writer acquisition, writer issuance, proof generation,
`writer_ownership` mutation, worker execution, Bridge invocation, Codex
invocation, service loops, scheduler loops, recovery loops, repair, commit,
publication, or deployment. B2b's state-authority lock is necessary exclusion
only and is not writer authority.
