# SQLite Bootstrap And Migrations

Status: B2b implements operator-local SQLite bootstrap, observational
inspection/validation, schema validation, the common state-authority lock, and
initialize/migrate lock integration. B2c implements durable writer issuance
and internal SQLite `WriterSession` acquisition for managed databases.

B1/B1.1 implements a secure local SQLite state-location policy, split
read-only and administrative connection posture, packaged migration catalog,
forward-only migration runner, initial schema installation, migration-history
catalog equality, live-schema manifest validation, managed current-state
invariant checks, schema/application compatibility checks, and a shared
state-authority advisory lock used by initialize/migrate administration. It
does not implement `StateStore` mutation semantics, work-item mutation APIs,
global-stop mutation APIs, product reads, reports over the database,
authorization, worker execution, scheduling, repair, local commit,
publication, or service behavior. B2c separately implements internal writer
ownership acquisition, writer issuance, and private operation guarding only.

Inspection and validation are observational existing-database operations.
They must not create a missing state root, create a database file, write a
SQLite header, change persistent `journal_mode`, create or delete sidecars, or
repair/adopt unknown schema. Bootstrap and migration are explicit
operator-local administrative operations. They are not connector, MCP,
command-payload, backlog, lease, work-item, report, or remote-input
operations. Normal runtime must not execute migrations concurrently with an
active Coordinator writer session. B2b ensures initialize and migrate use the
same state-authority lock that B2c writer acquisition holds. B2c owns writer
acquisition and fencing. B3/B4 own transition and global-stop
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

The database file is created with mode `0600` when absent. Existing active
database paths must be regular files, not symlinks, directories, FIFOs,
sockets, or devices, must reject group/other permissions, and must have exactly
one hard link where link count is safely testable. This single-link rule
applies to the fixed active Coordinator database path, not to backup artifacts
generally. The B2b state-authority lock file is created at the fixed path with
mode `0600`, validated as a regular non-symlink file, rejected when
group/other-accessible, rejected when hardlinked where link count is safely
testable, acquired with a nonblocking exclusive advisory lock, and left in
place after release. Public errors never echo raw paths.

Python `sqlite3` opens the database by pathname. B3c1b adds a private bounded
open helper that pins the retained state-root, authority-lock-file, and
database-file identities before open, holds temporary anchor descriptors while
SQLite opens the fixed pathname, and revalidates after open and after
`BEGIN IMMEDIATE`. This is bounded local filesystem identity pinning, not a
claim of immunity to every same-account race, unsupported filesystem, or mount
namespace attack. The owner-only parent directory mitigates other-user
replacement, but same-account malicious-process resistance remains limited.
B1 does not claim no-follow semantics that the standard library SQLite API does
not provide.

## Connection Posture

Connection posture is separate from migration DDL. Migration identity does not
include PRAGMAs from the B0 schema fixture. B1.1 no longer uses the same
create-capable connection path for every operation. Observational
inspect/validate opens only an existing file, uses create-disabled read-only
mode where practical, applies only connection-local safety settings, and
queries persistent journal posture. Administrative initialize is the only
create-capable public operation. The create-capable connection helper is an
internal administrative implementation surface used by initialize only; it is
not a supported authority API. Administrative migrate uses create-disabled
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
  result, and managed current-state invariants pass. For `writer_ownership`,
  no row is valid before first acquisition; a present row is valid only when
  generation is an exact integer in `1..9223372036854775807`;
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

B2c writer acquisition requires an existing `MANAGED` database, validates and
acquires the same lock, opens the database create-disabled read/write, executes
`BEGIN IMMEDIATE`, revalidates schema/history, issues the next generation and
proof, updates `writer_ownership`, commits, closes the acquisition connection,
and retains the lock descriptor for the `WriterSession` lifetime. Any
pre-commit failure rolls back, closes the database, releases the lock, returns
a safe failure, and creates no usable partial session. A failure after commit
but before session return may consume and skip the committed generation; it is
never reused.

B2c validates writer-row semantics with the same internal parser used by B1.1
managed validation. A present generation `0`, negative, bool-like, or overflow
row is malformed managed writer state even though migration `0001_initial`
remains unchanged and still permits zero at the SQL check layer.

B2b does not update `writer_ownership`; B2c updates it only during writer
acquisition and never during session close.

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
database, worker execution, Bridge invocation, Codex invocation, service loops,
scheduler loops, recovery loops, repair, commit, publication, or deployment.
B2b's state-authority lock is necessary exclusion only and is not writer
authority by itself. B2c's writer acquisition and private operation guard do
not implement transition or global-stop mutation storage. B3a adds
contract-only canonical persistence and provenance rules; it does not open
SQLite for transition apply, insert events, update work items, or add
admission.

## C2B0 Target Migration Sequence

Status: `ACCEPTED TARGET CONTRACT`; no target SQL is installed. The implemented
application generation and managed database tip remain 1/`0001_initial`.

C2B1 is a framework-only source/test reset with no SQL or database change. It
keeps implemented application generation 1 and the terminal catalog tip at
0001. It changes only migration-framework source and tests.

C2B2 advances implemented application generation from 1 to 2 when migration
0002 is introduced, and the terminal catalog tip becomes 0002. C2B3 remains
generation 2 with terminal tip 0002. C2B4 adds migration 0003 while retaining
application generation 2, and the terminal tip becomes 0003. C2B5 and C2B6
remain generation 2 with terminal tip 0003.

Migration compatibility bounds describe the application generations allowed
to own a database when that migration is the installed terminal tip. Every
installed row remains immutable and must exactly equal its packaged catalog
entry in sequence, migration ID, checksum, compatibility bounds, and
destructive flag. Historical rows are not required to include the running
application generation: historical migration 0001 remains `[1,1]`, while 0002
and 0003 are `[2,2]`. Migration 0001 bytes, checksum, history, bounds, and table
meanings are never rewritten.

Ordinary product or writer open requires exact complete catalog history, the
exact current terminal sequence and migration ID, terminal compatibility that
contains the current application generation, and complete final-schema
verification. Ordinary open never silently migrates and never accepts an older
prefix.

Explicit migration preflight may recognize one exact non-empty supported older
catalog prefix. Every installed row must have exact packaged checksum and
metadata; gaps, unknown or partial rows, and divergent bounds or flags are
rejected. The packaged remainder must be one exact contiguous suffix leading to
the current terminal tip. A supported older prefix is migration-eligible only,
not ordinarily product-openable before migration.

The cumulative paths are exact:

```text
C2B2 fresh installation: 0001 -> 0002
C2B4-or-later fresh installation: 0001 -> 0002 -> 0003
C2B2 upgrade from exact 0001: apply only 0002
C2B4-or-later upgrade from exact 0001: apply 0002 then 0003
C2B4-or-later upgrade from exact 0002: apply only 0003
```

For every path above, the complete intended packaged suffix is one
administrative transaction:

```text
C2B2 fresh installation transaction: [0001, 0002]
C2B4-or-later fresh installation transaction: [0001, 0002, 0003]
C2B2 upgrade from exact 0001 transaction: [0002]
C2B4-or-later upgrade from exact 0001 transaction: [0002, 0003]
C2B4-or-later upgrade from exact 0002 transaction: [0003]
```

Every migration selected for that suffix contributes all of the following to
the same administrative transaction:

```text
DDL
managed invariant changes
matching migration-history insertion
```

No suffix migration may commit before a later migration in the same selected
suffix is attempted. A history row without its schema effects, schema effects
without the matching history row, and a partially installed suffix are all
forbidden. Failure before commit restores the complete exact prior supported
prefix with no partial DDL, invariant change, or history row and never rewrites
0001. Ordinary product or writer open never performs migration.

If an administrative commit attempt raises, migration recovery must:

```text
close the uncertain connection
reopen through the migration recovery path
reread the complete exact migration history
reread the complete live-schema invariants
compare both the exact prior supported prefix and exact intended completed suffix tip
```

The evidence classifications are exact:

```text
committed_exact
history equals the prior prefix plus the complete intended suffix
every suffix row matches packaged sequence, ID, checksum, compatibility bounds, and destructive flag
live schema equals the complete intended terminal-tip schema
the prior prefix remains unchanged
no partial, extra, unknown, or divergent object exists
```

```text
definitely_not_committed
history equals the exact prior supported prefix
live schema equals the exact prior supported-prefix schema
no intended suffix history row exists
no intended suffix schema object or invariant exists
no partial or unexpected object exists
```

```text
unresolved
history and schema disagree
only part of the intended suffix is present
history-only suffix evidence exists
schema-only suffix evidence exists
an unknown or divergent history row exists
an unexpected schema object exists
either exact verification cannot be completed
```

An `unresolved` result forbids automatic rerun and automatic append of a
missing remainder. An operator or separately accepted recovery must complete
before another migration attempt. This migration-specific rule is distinct
from the semantic progression-mutation retry contract.

A generation-1 binary rejects sequences 2 and 3 as newer and unsupported. A
generation-2 terminal-0002 binary ordinarily opens exact 0002 and rejects 0003
as newer. A generation-2 terminal-0003 binary ordinarily opens exact 0003 and
treats exact 0001 or 0002 only as explicitly migratable supported prefixes.
Final schema authority is the cumulative packaged migration sequence; no
cumulative schema snapshot is introduced.

The accepted later migrations are:

```text
0002_development_program_and_effect_state: [2,2], non-destructive, 19 tables, 30 triggers, 1 explicit index, no seed rows
0003_development_observation_and_progression_state: [2,2], non-destructive, 9 tables, 16 triggers, 1 explicit index, one available latch seed
```

Exact target tips are:

```text
0001: 11 user tables, 0 explicit indexes, 16 triggers
0002: 30 user tables, 1 explicit index, 46 triggers
0003: 39 user tables, 2 explicit indexes, 62 triggers
```

The two explicit indexes are
`uq_development_effect_intents_author_command` and
`idx_development_source_observation_claims_digest`. The only 0003 bootstrap row
is `direct_local_first_productive_acceptance` in state `available`, version 0,
with null consumed bindings. `.docs/c2b-durable-development-state.md` owns the
exact target table, trigger, privacy, and transaction responsibilities.
