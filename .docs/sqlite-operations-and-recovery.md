# SQLite Operations And Recovery

Status: B0 design only.

## Filesystem Posture

The first backend state directory must be local, private, and fixed by
Coordinator configuration, not by arbitrary connector/operator input.

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

## Restore

Restore requires explicit operator action. A restored database becomes
authoritative only after:

- schema migration checksum validation;
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
