# SQLite Bootstrap And Migrations

Status: C2B1 is the current owner of the bounded operator-local migration
framework. The current application generation is 2 with exact production
catalog tip `0004_rw0_c1_durable_evidence` and exactly the
`0001_initial.sql`, `0002_development_program_and_effect_state.sql`,
`0003_cognitive_proposal_and_selection_state.sql`, and
`0004_rw0_c1_durable_evidence.sql` production SQL resources. C2B2 Slice 1
introduced generation 2 and migration 0002; later owners added migrations 0003
and 0004 without changing C2B2 ownership.
B1/B1.1 and B2b remain historical tranche names for bootstrap, observational
validation, and common-lock integration. B2c implements durable writer issuance
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
- migration catalog: code-owned packaged resources discovered with
  `importlib.resources`, never caller-selected or arbitrary filesystem
  migration paths. Current loading supports only a filesystem-backed
  regular non-symlink resource at the package-owned path;
- migration history: each `schema_migrations` row is the installed-definition
  persisted projection: sequence, migration ID, exact checksum, `applied_at`,
  and application compatibility bounds. `applied_at` is validated row data,
  not packaged metadata. Exact sequence/ID/checksum/bounds resolves one closed
  packaged definition. Its `destructive` flag is catalog-only and there is no
  `schema_migrations.destructive` column;
- schema compatibility checks: old binaries refuse newer unsupported schema,
  newer binaries migrate only through explicit migration calls, incompatible
  history refuses closed, checksum mismatch refuses closed, gaps refuse closed,
  unknown migrations refuse closed, and the live schema must match a
  deterministic manifest derived from the packaged migration result;
- bootstrap, inspection, validation, and migration errors: closed safe error
  classes or safe classifications that avoid raw SQL, raw DDL, absolute paths,
  database content, canonical JSON, credentials, endpoints, environment,
  SQLite exception text, and trust material. A public `SQLiteStateError` is
  constructed only after control has left any raw SQLite or filesystem
  exception handler, so it retains no raw cause or context graph;
- destructive metadata: C2B1 rejects every selected destructive definition
  before common-lock acquisition, writable open, transaction start, or
  database mutation. It implements no backup files and no destructive
  migration.

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

The catalog is forward-only, immutable, closed, and code-owned. Duplicate
sequence, migration ID, resource identity, or ambiguous persisted projection
is invalid. SQL resource bytes must match the literal catalog checksum. It does
not support downgrade or reverse migration. C2B1 refuses a selected destructive
definition before lock or writable activity and implements no backup files.
Top-level `BEGIN`, `COMMIT`, `END`, `ROLLBACK`, `SAVEPOINT`, `RELEASE`,
`PRAGMA`, `ATTACH`, `DETACH`, and `VACUUM` are rejected before mutation. After
every selected SQL statement, the administrative connection must remain in the
owned transaction.

The current resource boundary is deliberately narrower than the general
`importlib.resources` abstraction. The package container and each selected SQL
resource must resolve to concrete filesystem paths. The loader uses `lstat`,
rejects symlinks and every nonregular kind before open, opens without following
the final path where the platform supports that flag, compares pre-open and
opened-file identity, reads under a fixed byte ceiling, and rechecks regular-file
identity after the read. A missing resource, directory, FIFO, socket, device,
or replacement race fails closed as `migration_failed` without exposing the
path or resource bytes. Non-filesystem or zip-backed migration resources are
currently unsupported and fail closed before SQLite activity. This is bounded
current C2B1 support, not a permanent packaging architecture.

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

F1 current successor: observational inspection and validation keep the four
classifications and never open writable. An engine-supplied exact numeric
`SQLITE_READONLY_ROLLBACK` (776) becomes `UNKNOWN` with closed reason
`recovery_needed`; a message, journal filename, generic READONLY, or generic
I/O error cannot produce that reason. This reason establishes neither managed
schema nor corruption. `initialize_database()` and `migrate_database()` reject
it with the same safe `recovery_needed` state error; they do not auto-recover or
auto-migrate. Writer acquisition rechecks under the common lock and may let
SQLite roll back only a checked fixed adjacent DELETE journal for the bound
existing main database. An unsafe journal or dependency form refuses before
write-capable recovery access; an uncertain access or cleanup reports
`recovery_unresolved`. After rollback the writer validates the exact current
catalog/schema/invariants before ordinary issuance. Exact older prefixes still
require explicit administrative migration even if their storage has rolled
back. All five packaged SQL resources, catalog checksums, schema and
application generation remain unchanged. The earlier refusal-only F1 branch is
historical, not the current writer-entry behavior.

C2B1 preserves the public four-way classification:

The historical nine-condition private assessment below gains one F1 successor
condition, `RECOVERY_NEEDED`, only for the exact engine result described above.
It maps to public `UNKNOWN` with reason `recovery_needed`, not to corrupt
history; it never makes an old prefix current or admits administrative mutation.

- absent: the fixed database file does not exist; inspection/validation do not
  create it;
- empty: an existing empty SQLite database or private zero-byte placeholder
  with no user-defined schema objects and no migration history;
- managed: only exact complete current-catalog history with the exact current
  terminal sequence/ID, terminal compatibility containing application
  generation 2, cumulative live-schema equality, and managed invariants. The
  full live schema manifest matches the cumulative packaged migration
  result, and managed current-state invariants pass. For `writer_ownership`,
  no row is valid before first acquisition; a present row is valid only when
  generation is an exact integer in `1..9223372036854775807`;
- unknown/partially initialized: any unrecognized user-defined schema object,
  views or triggers without authoritative migration history, explicit indexes
  not in the expected manifest, invalid migration history, unexpected
  migration rows, duplicate sequence or id, checksum mismatch, migration gap,
  newer unsupported schema, incompatible or non-equal application bounds,
  unsupported journal posture, malformed schema, or failed managed invariant.

An exact supported older prefix is public `UNKNOWN`, not `MANAGED`. The private
assessment preserves nine conditions: `ABSENT`, `EMPTY`, `CURRENT`,
`SUPPORTED_OLDER_PREFIX`, `UNSUPPORTED_OLDER`, `NEWER_UNSUPPORTED`,
`CORRUPT_HISTORY`, `PARTIAL_MIGRATION`, and
`DATABASE_NOT_EMPTY_UNMANAGED`. Only explicit `migrate_database()` may admit
the exact supported non-empty prefix. Unknown databases otherwise fail closed;
C2B1 does not guess, adopt, drop, repair, or rewrite tables.

History is read with a bound of catalog-tip-plus-one rows. Rows require exact
built-in types, so Boolean-as-integer input is rejected. Sequence, migration
ID, checksum, `applied_at`, and both bounds are validated before terminal-only
application-generation compatibility. Historical rows need not include the
running generation; only the installed terminal migration is evaluated for
that compatibility.

User-defined schema accounting covers tables, views, explicit indexes, and
triggers from `sqlite_schema`. B1.1 ignores only SQLite internal `sqlite_%`
objects and autoindexes that are accounted for through table/index
introspection. A view-only database is unknown, not empty.

## Schema Manifest

C2B1 derives an expected live-schema manifest for any selected terminal by
creating a fresh isolated in-memory SQLite database, applying exact catalog
definitions `1..terminal` in order, and extracting a deterministic allowlisted
representation. There is no manifest cache, checked-in cumulative snapshot, or
second schema authority. The manifest
includes user schema objects, normalized object definitions, table columns,
declared types, nullability, defaults, primary keys, foreign keys, index lists,
index columns/order/uniqueness, views, triggers, and object relationships.

The live managed database must independently match that cumulative manifest
using bounded schema-object inspection. Migration history is authoritative
installed-migration evidence; cumulative packaged SQL is authoritative
expected schema; live schema is independently verified observation. History
alone never proves the schema.

## Transaction Model

C2B1 initialization execution order is:

1. Validate catalog metadata, filesystem resource kind and stable bytes,
   literal checksum, every lexical SQL statement plan, and terminal
   compatibility without executing catalog SQL.
2. Use bounded read-only history inspection to resolve only an absent, empty,
   or exact-current candidate without deriving an expected schema manifest.
3. Select the complete catalog for absent or empty initialization, or the empty
   suffix for exact current state, and reject any selected destructive
   definition before expected-manifest SQLite activity.
4. Only after that suffix is accepted, derive expected manifests and perform
   complete history, schema, invariant, and compatibility assessment.
5. Accept only absent, empty, or exact current state; reject every other state.
6. Acquire the common exclusive state-authority lock, repeat the history-only
   candidate and selected-suffix checks, and then repeat complete assessment.
7. For exact current state, return only after locked revalidation.
8. Use the create-capable initialization seam only when absent, then capture
   and retain the exact filesystem authority binding.
9. Open the bound database read/write, establish administrative posture, and
   start exactly one `BEGIN IMMEDIATE`.
10. Revalidate exact empty/bootstrap eligibility inside that transaction.
11. Apply the complete catalog in order, insert every matching history row with
   one planned whole-second UTC timestamp, and require the transaction after
   every SQL statement and write.
12. Verify each cumulative prefix, then exact complete history, cumulative
    terminal schema, seed, managed invariants, and terminal compatibility.
13. Attempt `COMMIT` exactly once and clean up or recover while retaining the
    common lock.

C2B1 explicit migration execution order is:

1. Validate catalog/resource metadata and lexical SQL plans without catalog SQL
   execution, then use bounded read-only history inspection to resolve only an
   exact current state or one exact supported non-empty proper prefix.
2. Resolve the entire complete contiguous suffix from that exact persisted
   projection and reject any destructive definition before expected prior-tip
   or target-tip manifest derivation. Malformed history that cannot identify
   one exact candidate prefix fails at this phase.
3. Only after suffix acceptance, derive the expected prefix and target
   manifests and perform complete history/schema/invariant assessment.
4. Acquire the same common lock; repeat history-only candidate and suffix
   checks before complete locked reassessment, and return current state only
   after locked revalidation.
5. Capture the existing database binding and open only through the
   filesystem-bound administrative seam.
6. Start one `BEGIN IMMEDIATE` and revalidate exact prefix history, cumulative
   prefix schema, and managed invariants.
7. Apply every selected migration and history projection in order with one
   planned timestamp. No earlier migration may commit before a later selected
   migration is attempted.
8. Verify exact completed history and cumulative terminal schema/invariants.
9. Attempt one commit and clean up or recover while the lock remains held.

Before commit begins, failure attempts rollback and close; successful cleanup
restores the exact opening empty state or supported prefix. Once commit begins,
rollback is forbidden. A commit exception or unprovable cleanup closes or
abandons the uncertain connection and reopens through the same filesystem-bound
path while retaining the common lock. Bounded history and cumulative schema
readback yields exactly:

- `COMMITTED_EXACT`: exact prior prefix plus the complete intended suffix,
  exact target schema/invariants, and no divergent evidence; return success;
- `DEFINITELY_NOT_COMMITTED`: exact prior history and schema with no suffix
  evidence; raise `migration_failed`;
- `UNRESOLVED`: every partial, history-only, schema-only, divergent, unknown,
  unverifiable, or recovery-open result; raise
  `migration_outcome_unresolved`.

After `UNRESOLVED`, automatic retry, automatic complete-suffix rerun, and
automatic missing-remainder append are forbidden. A later separately invoked
administrative attempt requires independently re-proven eligibility. This
migration recovery is not semantic-progression `commit_outcome_unknown`.

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

Status: `CURRENT IMPLEMENTED CONTRACT` for C2B2 Slice 1 generation 2 / terminal
0002, and `ACCEPTED TARGET CONTRACT` for migration 0003 and later C2B runtime.

C2B1 is a framework-only source/test reset with no SQL or database change and
remains the migration-mechanics foundation documented above.

C2B2 Slice 1 advances implemented application generation from 1 to 2, installs
migration 0002, and makes the terminal catalog tip 0002. C2B3 remains
generation 2 with terminal tip 0002. C2B4 adds migration 0003 while retaining
application generation 2, and the terminal tip becomes 0003. C2B5 and C2B6
remain generation 2 with terminal tip 0003.

Migration compatibility bounds describe the application generations allowed
to own a database when that migration is the installed terminal tip. Every
installed row remains immutable and must exactly equal the persisted projection
of its packaged definition in sequence, migration ID, checksum, and
compatibility bounds. Exact projection resolution supplies the catalog-only
destructive flag; history has no destructive column. Historical rows are not required to include the running
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
persisted metadata; gaps, unknown or partial rows, and divergent bounds are
rejected. The packaged remainder must be one exact contiguous suffix leading to
the current terminal tip, and every selected destructive definition is rejected
before common-lock acquisition or writable activity. A supported older prefix is migration-eligible only,
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
COMMITTED_EXACT
history equals the prior prefix plus the complete intended suffix
every suffix row's persisted projection resolves exactly to one packaged non-destructive definition
live schema equals the complete intended terminal-tip schema
the prior prefix remains unchanged
no partial, extra, unknown, or divergent object exists
```

```text
DEFINITELY_NOT_COMMITTED
history equals the exact prior supported prefix
live schema equals the exact prior supported-prefix schema
no intended suffix history row exists
no intended suffix schema object or invariant exists
no partial or unexpected object exists
```

```text
UNRESOLVED
history and schema disagree
only part of the intended suffix is present
history-only suffix evidence exists
schema-only suffix evidence exists
an unknown or divergent history row exists
an unexpected schema object exists
either exact verification cannot be completed
```

An `unresolved` result forbids automatic rerun and automatic append of a
missing remainder. It is `UNRESOLVED` and raises
`migration_outcome_unresolved`. An operator or separately accepted recovery must complete
before another migration attempt. This migration-specific rule is distinct
from the semantic progression-mutation retry contract.

A generation-1 binary rejects sequences 2 and 3 as newer and unsupported. A
generation-2 terminal-0002 binary ordinarily opens exact 0002 and rejects 0003
as newer. A generation-2 terminal-0003 binary ordinarily opens exact 0003 and
treats exact 0001 or 0002 only as explicitly migratable supported prefixes.
Final schema authority is the cumulative packaged migration sequence; no
cumulative schema snapshot is introduced.

The implemented current migration and accepted later migration are:

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

## C2B2 Slice 1 Runtime And Zero-Seed Rules

Any selected migration suffix or expected schema prefix containing migration
0002 requires SQLite 3.37.0 or newer for STRICT-table support. Failure of that
preflight is `sqlite_posture_unavailable` and occurs before state-root creation,
authority-lock acquisition, writable target open, `BEGIN IMMEDIATE`, target
mutation, or expected-manifest execution that requires STRICT.

Zero-seed verification is migration-sequence scoped. A fresh installation
checks migration 0001's original bootstrap-empty tables and canonical clear
global-stop singleton after 0001, then checks all nineteen migration-0002 C2B
tables after 0002. Exact 0001-to-0002 migration performs the same nineteen-table
check after 0002. C2B emptiness is not an ordinary exact-current managed-state
invariant and therefore does not prevent a later authorized C2B mutation tranche
from populating the schema.

The two explicit indexes are
`uq_development_effect_intents_author_command` and
`idx_development_source_observation_claims_digest`. The only 0003 bootstrap row
is `direct_local_first_productive_acceptance` in state `available`, version 0,
with null consumed bindings. `.docs/c2b-durable-development-state.md` owns the
exact target table, trigger, privacy, and transaction responsibilities.

<!-- C2B3_NARROWED_MIGRATION_BEGIN -->
## Vertical-slice migration narrowing

The previously selected migration-0003 relation inventory, object counts,
named indexes, triggers, bootstrap row, and cumulative totals are reopened and
non-operative for the first vertical-slice design. This addendum selects no
replacement schema or arithmetic.

Pre-I/O design must first determine whether migration-0002 structures suffice.
Remote-contact design may select only migration-0003 relations required by the
executable path. Local-Git and ES phases must likewise justify only their
minimum durable needs. Every selection requires separate authorization and
fresh contract/audit treatment before production SQL.

Current implemented capability remains generation 2 at terminal migration
0002. Migration 0002 bytes, catalog, and meanings are unchanged. No migration
0003 resource, schema object, bootstrap row, runtime, or operator-state
mutation is implemented or authorized here.
<!-- C2B3_NARROWED_MIGRATION_END -->

<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_BEGIN -->
## Cognitive proposal and selection runtime

Section 41 of `.docs/c2b-durable-development-state.md` remains the sole detailed
semantic owner; Section 42 records current implementation and
repository-publication status without redefining it. C2B3D private author-effect
establishment is committed at
`5e544622e5f46ddc78294322471b4fcbd2ad9172`. Migration
`0003_cognitive_proposal_and_selection_state` and the private pre-execution
proposal-selection runtime are committed at
`394d625aa63935140eeaf88ecff6f59f0547cb7e`. Git owns committed object and ref
truth; independent acceptance, audit, validation, provenance, and report
records remain external evidence rather than Coordinator durable authority or
effect permission. The source tranche ends at typed pre-execution proposal
admission plus Coordinator selection or non-selection. It performs no
model/provider invocation, dispatch, worker contact, post-execution
validation/review execution, post-execution Coordinator semantic decision,
capsule custody, Git effect, Bridge or ES handoff, publication execution,
service, scheduler, queue, or autonomous loop. The full remote-worker phase is
not reduced to this private source tranche.
<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_END -->

The earlier C2B0/C2B3 migration-0003 name, inventory, and current-tip statements
are historical target/tranche snapshots superseded by Sections 41 and 42.

<!-- RW0_C1_CURRENT_STATUS_BEGIN -->
**Current generation-2 tip after RW0-C1.**

The packaged catalog is now exactly
`[0001_initial, 0002_development_program_and_effect_state, 0003_cognitive_proposal_and_selection_state, 0004_rw0_c1_durable_evidence]`.
Fresh initialization applies `[0001, 0002, 0003, 0004]`; an exact supported
older prefix is eligible only for explicit administrative migration of the
complete contiguous suffix. Ordinary inspection, validation, writer
acquisition, and product mutation admit only the exact complete tip. Migration
0004 remains application generation 2, requires SQLite 3.37.0 before any
writable activity, is non-destructive, and seeds zero rows.
<!-- RW0_C1_CURRENT_STATUS_END -->

### Section 41 migration 0005 additive successor

At the Section 41 checkpoint, the complete catalog was `[0001, 0002, 0003, 0004, 0005_section41_post_execution_proposal_family]` at application generation 2. The 0005 SQL resource has SHA-256 `583c14e2018c84a942e2e72bbb57d24ae39b2470dc4c286c5f775afe1ef9ea87`, adds two STRICT zero-seed tables and four immutable guards, and adds no explicit index. The cumulative schema at that checkpoint had 64 user tables, 114 triggers and five explicit indexes. Fresh initialization applied all five; an exact supported 0004 prefix required explicit `migrate_database()` before ordinary validation, writer acquisition or mutation, which never auto-migrate. The four earlier SQL resources remain byte-exact. Existing SQLite 3.37.0 preflight and cumulative packaged-SQL schema verification apply to this suffix. Prior 0004-tip wording is a historical owner snapshot; the current uncommitted candidate tip is 0007 below.

<!-- RW0_C2_P0_MIGRATION_0006_CANDIDATE_BEGIN -->
## RW0-C2 P0 migration 0006 candidate

Migration `0006_rw0_c2_scope_admission` is additive, application generation
2, and program-independent. It creates four immutable STRICT tables and eight
UPDATE/DELETE rejection triggers, with no explicit index. Fresh initialization
applies the complete current catalog; an exact older managed prefix advances
only through explicit `migrate_database()`. Ordinary writer acquisition and
product mutation never migrate. Migrations 0001–0005 remain byte-identical.
This section records the artificial-offline uncommitted implementation
candidate, not a live admission supplier or durability acceptance.
<!-- RW0_C2_P0_MIGRATION_0006_CANDIDATE_END -->

<!-- RW0_C2_P1_MIGRATION_0007_CANDIDATE_BEGIN -->
## RW0-C2 P1 migration 0007 candidate

The uncommitted application-generation-2 catalog tip is now
`0007_rw0_c2_progression_decision`, SHA-256
`505d72c9c54f68e248bebab928e76564d45b853068b8b4021ebc708b640e430c`.
It adds exactly six immutable STRICT supplemental tables and twelve
UPDATE/DELETE rejection triggers; the cumulative schema has 74 user tables,
134 triggers, and five explicit indexes. Its guarded relation stores four
bounded nullable work-head witness columns, all required only for replan, with
a nullable identity FK to the existing work head. The v2 result requires the
v2 receipt graph profile. The decision-basis row CHECK requires the current
decision-basis v2 schema ID; its two typed dispositions remain inside the
existing canonical basis BLOB. Migrations 0001–0006 remain byte-identical. An exact
0006 prefix requires explicit administrative migration; ordinary inspection,
writer acquisition, and product mutation never auto-migrate. This suffix adds
no public mutation API or live authorization.
<!-- RW0_C2_P1_MIGRATION_0007_CANDIDATE_END -->

<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
## RW0-C2 committed-source migration status

The 0006 P0 and 0007 P1 candidate blocks above are exact historical
checkpoints. Independent artifact audit accepted tree `161ed4b544baf970cc26428b9805a106ea0f3edf` and local commit
`8704e6c7988250598809f3a0daf88c3e11493488` records its seven-resource generation-2 catalog. Migration 0006
remains a four-table P0-only family; migration 0007 remains a six-table P1
supplement. SQL bytes, hashes, schema counts, and the explicit migration-only
rule are unchanged. Ordinary inspection, validation, writer acquisition, and
product mutation do not auto-migrate. This local source commit neither
publishes the branch nor establishes live admission or executable permission.
<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure current candidate

The uncommitted `artificial_offline_normal.v1` candidate adds a separate private Coordinator terminal writer on generation-2 migration 0008. It consumes checked P0, phase, Section 41 A, C1 rank-15/V22 and P1 evidence under one fenced transaction and records only the five normal outcomes: accept, repair, replan, terminal_reject and block. The P1 decision remains prior decision history; its acceptance fact is bound only for accept and is never mutated. Cancellation, live supplier/contact, ES routing, Git effects, publication and executable permission remain outside this candidate. See `.docs/rw0-terminal-outcome-physical-closure.md`.

The literal 0008 SQL adds four immutable STRICT tables and eight guards without changing 0001–0007. The eight-resource catalog has 78 tables, 142 triggers and five explicit indexes. Exact prefixes require explicit migration; old-binary, partial, checksum-mismatched and divergent schemas fail closed. The frozen schema-0001 fixture is unchanged.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure local commit status

The exact cumulative independent audit accepted Git-compatible tree `4691af58ae0ee3107b4e2e9b6b1508032944e357` for an exact-byte commit gate after its current-ledger consistency repair. The private `artificial_offline_normal.v1` implementation was locally committed as `d3fd741c872b26aa2dfe927ab6dccc638cdcf356`, with sole parent `61d0330aba1160f7f5e7d9c541a325222d1c61e5`, that exact tree, and subject `feat: add RW0 normal terminal closure`. The staged-blob gate collected and passed 9,568 selector-free tests in the same order, with zero failures, errors, skips, xfails, or xpasses and only the three known Python 3.13 multithreaded-fork deprecation warnings. This is a local topic-branch commit; no push, PR, merge, publication, deployment, service/runtime contact, or product effect followed.

Migration `0008_rw0_terminal_outcome` is the current source/catalog suffix. The private fenced terminal owner records only normal `accept`, `repair`, `replan`, `terminal_reject`, and `block`. P0 scope admission, P1 progression decision with its acceptance-only fact, and terminal closure remain separate private fenced transactions and facts. P0 grants no current permission; P1 is prior decision history, not terminal truth. Normal accept binds the immutable acceptance fact without mutation or replenishment.

Common managed-store admission may shape-check the current global-stop singleton before writer fencing. After fencing and protected disclosure, receipt-present terminal read, replay, and recovery verify saved full head postimages, saved stop, and immutable P0/Section 41/C1/P1 predecessors without today's mutable-head or semantic stop checks. A fresh receipt miss retains current-head, current-stop, recording, and disclosure checks. The old whole-operation zero-current-stop-SELECT audit failure remains historical; the accepted two-layer rule supersedes only that overbroad requirement.

Git objects and refs own commit and publication truth. Audit packages, reports, validation, this status text, WA1/QtcM evidence, and provenance are evidence only. The local commit adds no executable permission, three cancel selectors, live supplier/custody gate, worker/provider or physical remote contact, ES/Bridge route, product Git-effect handler, service, queue, scheduler, deployment, or autonomous loop. Existing F03/F05 nonblocking provenance limits retain their recorded scope; this status does not claim their repair. Candidate-stage status elsewhere in this document is preserved history; this marked block is the current local status.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_POST_MERGE_STATUS_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure integrated capability status

Classification: `CURRENT INTEGRATED CAPABILITY STATUS`.

RW0 normal terminal closure was integrated into `trunk_dev` by squash commit `3be0096c163b456c9975326be3eb2c30d2b4bbd1`, with sole parent `61d0330aba1160f7f5e7d9c541a325222d1c61e5` and integrated capability tree `bc10382edd1b2c097fc729e4e168d72e710391fe`. This is the integration anchor for the accepted private `artificial_offline_normal.v1` source. The commit containing this status-only successor is intentionally not self-identified here; Git objects and refs own the current containing commit and publication truth.

The integrated capability records only normal `accept`, `repair`, `replan`, `terminal_reject`, and `block`. P0 scope admission, P1 progression decision with its acceptance-only fact, and terminal closure remain separate private fenced transactions and facts. Migration `0008_rw0_terminal_outcome` remains the source/catalog suffix. P0 grants no current permission; P1 remains prior decision history rather than terminal truth; normal accept binds the immutable acceptance fact without mutation or replenishment.

The accepted implementation staged-tree gate passed 9,568 / 9,568 tests. The accepted status staged-tree focused gate passed 5,655 / 5,655 tests. Independent artifact review accepted the exact status tree `bc10382edd1b2c097fc729e4e168d72e710391fe`. The accepted 9,597-test selector-free FULL record was carried evidence on that tree and was not rerun during integration. No tests ran during the integration operation itself. These records are evidence at their stated scopes, not current Git or runtime authority and not validation of this later status-only correction.

All earlier candidate-stage, local-commit-stage, and cross-stage status passages in this document are preserved historical evidence. Their statements that the implementation was uncommitted, only a local topic-branch commit, or followed by no push, PR, merge, or source publication are stage-local and are not current repository status after the integration anchor above.

The integrated source adds no active-cancel terminal family or executable permission; no live supplier/custody, worker/provider, or physical remote contact; no ES/Bridge route; no Coordinator-owned product Git-effect or runtime publication authority; and no service, queue, scheduler, deployment, or autonomous-runtime loop. Source publication by Git merge does not establish any of those product capabilities. Existing F03/F05 nonblocking provenance limits retain their recorded scope and are not repaired by this status correction.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_POST_MERGE_STATUS_SUCCESSOR_END -->

<!-- RW0_TERMINAL_ANCHOR_0009_STATUS_SUCCESSOR_BEGIN -->
## RW0 terminal anchor registry implementation status

Classification: `CURRENT UNCOMMITTED IMPLEMENTATION CANDIDATE`.

Migration `0009_rw0_terminal_anchor_registry` is the current source/catalog suffix at application schema generation 2. The integrated migration-0008 normal closure status above remains historical. Its four branch-family rows and normal semantic payload are unchanged. Explicit 0008-prefix migration registers each complete existing normal family without rewriting its rows; fresh normal receipts register an immutable anchor in the same transaction. The `rw0_terminal_anchors` phase key is the sole cross-profile route, while the selected checked branch family retains terminal semantic meaning. The registry is no independent outcome, progression decision, authorization, effect basis, or cryptographic replacement.

Migration 0009 admits only `artificial_offline_normal.v1`. Any later branch profile requires a separate explicit migration evolving the family-validation trigger; it must use the same phase-unique registry and cannot introduce a second phase-unique terminal store. This candidate adds no physical cancel capability, cancellation decision or outcome, cancellation effect or request, process observation, external source reconciliation, qualified supplier or custody, successor launch, live execution, Git effect, publication, or deployment. Git objects and refs remain publication truth; this uncommitted source status and validation are evidence only.

The packaged 0009 suffix has six statements: one 21-column STRICT anchor table, four immutable/admission/receipt-registration triggers, and one deterministic receipt-led normal-family backfill. The table adds one phase primary key, seven individual route uniqueness constraints, a phase-pair uniqueness constraint, and composite FKs to the phase and development decision. It has no self-digest and no unconditional FK to the normal receipt. Fresh inventory is 79 tables, 146 triggers, five explicit indexes, 1814 columns, and 242 foreign keys. Exact nonempty 0008 history remains an explicit administrative migration only. A private read-only verifier checks full normal-family and anchor one-to-one validity after statements and before the single commit attempt, and again for exact committed migration recovery. Ordinary pre-fence writer admission does not scan protected terminal rows.
<!-- RW0_TERMINAL_ANCHOR_0009_STATUS_SUCCESSOR_END -->
