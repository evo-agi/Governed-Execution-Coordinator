# SQLite Operations And Recovery

Status: B1.1 bootstrap/inspection/validation/migration implementation plus
future operations design.

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
is limited and must not be overclaimed.

B1.1 implements portable filesystem checks for bootstrap and existing-database
inspection:

- deterministic per-user state root from the canonical NWP Coordinator
  component name;
- no repository-checkout state root;
- fixed `coordinator-state.sqlite` database filename;
- state root mode `0700`;
- database mode `0600`;
- symlink and non-regular database rejection;
- safe closed errors without raw paths.

B1 does not implement advisory writer-lock acquisition. The migration lock path
is exposed as policy for a future tranche only.

B1.1 does not overclaim deeper filesystem confinement. Intermediate symlink
components are constrained by resolved trusted-root checks but are not a full
same-account malicious-process defense. Python `sqlite3` reopens by pathname.
Broad network-filesystem detection remains portable and incomplete. Those are
B2/B5 hardening topics, not solved B1.1 properties.

## Bootstrap And Migration Operations

B1.1 exposes split offline operations:

- inspect an existing fixed database path observationally, returning absent,
  empty, managed, or unknown without creating or mutating files;
- validate an existing managed database observationally, including journal
  posture, migration-history/catalog equality, live-schema manifest equality,
  and managed current-state invariants;
- initialize an absent or empty local database with migration `0001_initial`;
- migrate an existing managed older supported database through packaged
  forward-only migrations.

Ordinary future product operations must not run migrations implicitly merely by
opening the database.

Before applying migrations, B1.1 classifies the database:

- absent: fixed database file missing;
- empty: existing database/placeholder with no user-defined schema objects;
- managed: authoritative migration history equals the packaged catalog, the
  full live schema manifest matches, and managed current-state invariants pass;
- unknown/partially initialized: any unrecognized table, view, explicit index,
  trigger, invalid migration history, duplicate sequence or id, checksum
  mismatch, migration gap, newer unsupported schema, incompatible or non-equal
  bounds, unsupported journal posture, malformed schema, or failed current-state
  invariant.

Unknown databases fail closed. B1 does not adopt, drop, repair, or rewrite
unknown schema.

Observational inspect/validate use create-disabled opening where practical and
never issue persistent `journal_mode` changes. Wrong-posture WAL databases are
reported as unsupported/unknown instead of being converted. Migration
transactions are explicit and forward-only. Migration `0001_initial` creates
`schema_migrations` and all schema objects, verifies the schema manifest and
bootstrap seed, inserts its migration-history row, and commits as one
transaction. Failed migrations roll back; reverse migrations are not a rollback
mechanism.

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

B1 implements no backup files and no destructive migrations. Future destructive
migrations require a separately verified backup receipt before the migration
runner may proceed. Migration history records migration identity, checksum, and
compatibility bounds, not raw backup paths.

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
