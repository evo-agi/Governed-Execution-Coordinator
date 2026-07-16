# SQLite Bootstrap And Migrations

Status: B1 implemented for operator-local administrative bootstrap and schema
validation only.

B1 implements a secure local SQLite state-location policy, connection posture,
packaged migration catalog, forward-only migration runner, initial schema
installation, migration-history validation, and schema/application
compatibility checks. It does not implement `StateStore` mutation semantics,
writer ownership acquisition, advisory writer-lock acquisition, work-item
mutation APIs, global-stop mutation APIs, product reads, reports over the
database, authorization, worker execution, scheduling, repair, local commit,
publication, or service behavior.

Bootstrap and migration are explicit operator-local administrative operations.
They are not connector, MCP, command-payload, backlog, lease, work-item, report,
or remote-input operations. Normal future runtime must not execute migrations
concurrently with an active Coordinator writer. B2 owns writer acquisition and
fencing. B3/B4 own transition and global-stop atomic mutation.

## Responsibility Owners

The B1 SQLite bootstrap modules own:

- state-root selection: `CoordinatorStateLocation` derives a deterministic
  per-user local state root from the canonical NWP Coordinator component name,
  with tests injecting temporary roots;
- state-directory creation and validation: owner-only local directories,
  symlink rejection, regular-file checks, fixed database filename, and
  confinement under the trusted root;
- SQLite connection posture: `foreign_keys=ON`, rollback journal DELETE mode,
  `synchronous=FULL`, `locking_mode=NORMAL`, bounded busy timeout,
  `trusted_schema=OFF` where supported, disabled extension loading, and
  explicit transaction control;
- migration catalog: code-owned packaged resources loaded with
  `importlib.resources`, never arbitrary filesystem migration paths;
- migration history: `schema_migrations` rows record migration identity,
  sequence, exact checksum, application compatibility bounds, and application
  time of successful commit;
- schema compatibility checks: old binaries refuse newer unsupported schema,
  newer binaries migrate only through explicit migration calls, incompatible
  history refuses closed, checksum mismatch refuses closed, gaps refuse closed,
  and unknown migrations refuse closed;
- bootstrap and migration errors: closed safe error classes that avoid raw SQL,
  absolute paths, database content, canonical JSON, credentials, endpoints,
  environment, exception text, and trust material;
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
- migration/administrative lock path reserved for later use;
- backup directory path reserved for future backup receipts.

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
devices, and must reject group/other permissions. Public errors never echo raw
paths.

Python `sqlite3` opens the database by pathname. The owner-only parent
directory mitigates other-user replacement, but same-account malicious-process
resistance is limited. B1 does not claim no-follow semantics that the standard
library SQLite API does not provide.

## Connection Posture

Connection posture is separate from migration DDL. Migration identity does not
include PRAGMAs from the B0 schema fixture. B1 sets and verifies connection
PRAGMAs through fixed code-owned statements before migration classification.
Values are bounded and not arbitrary SQL input.

B1 uses rollback journal DELETE mode. WAL is not selected. Successful migration
commits must not leave persistent `-wal` or `-shm` files.

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

Before migration, B1 classifies the database:

- empty/uninitialized: no user tables, eligible for migration `0001_initial`;
- managed: `schema_migrations` exists and validates, eligible for schema
  compatibility checks and later explicit migrations;
- unknown/partially initialized: any user table without authoritative
  `schema_migrations`, invalid migration history, unexpected migration rows,
  duplicate sequence, checksum mismatch, migration gap, newer unsupported
  schema, or incompatible application bounds.

Unknown databases fail closed. B1 does not guess, adopt, drop, repair, or
rewrite tables.

## Transaction Model

Migration execution order is:

1. Securely prepare and open the local database.
2. Apply and verify connection posture.
3. Classify empty, managed, or unknown.
4. Validate existing migration history.
5. Select the exact next packaged migration.
6. Begin an explicit SQLite transaction.
7. Execute only packaged migration SQL.
8. Verify required schema objects and constraints.
9. Insert the migration-history row with checksum and compatibility bounds.
10. Commit.
11. Revalidate migration history and schema.

On failure, B1 rolls back. There must be no partial schema without history and
no history row without schema. Failed migrations return safe closed error
classes.

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
database, writer acquisition, advisory lock acquisition, worker execution,
Bridge invocation, Codex invocation, service loops, scheduler loops, recovery
loops, repair, commit, publication, or deployment.
