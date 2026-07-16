# SQLite Backend Threat Model

Status: B1.1 bootstrap/inspection/validation/migration implementation plus
future backend threat model. B2a defines writer-session authority contracts
only.

This threat model applies to the first SQLite backend architecture. B1
implements only bootstrap and migrations; it does not claim current code has a
production `StateStore` mutation backend.

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
- startup rejects symlink and non-regular database paths;
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

- migrations are transactional and forward-only;
- interrupted migration rolls back;
- old binary/new schema refuses;
- restore, not reverse migration, is rollback.

B1.1 adds concrete coverage for bootstrap filesystem threats, split
observational/admin connection posture, absent/empty/managed/unknown database
classification, no-mutation inspection of missing/unknown/wrong-posture
databases, migration-history/catalog equality, live-schema manifest
validation, managed current-state invariant checks, migration rollback, safe
SQLite error boundaries, and authority-boundary non-expansion. B1.1 does not
add writer acquisition, writer fencing validation, mutation APIs, worker
execution, or product read/report authority over SQLite.

B2a adds no runtime mitigation. It records that durable `writer_ownership`
metadata is latest issuance evidence only and that mutation authority requires
a future active `WriterSession` holding a private proof and the common
state-authority lock.

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
