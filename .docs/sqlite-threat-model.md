# SQLite Backend Threat Model

Status: B2b bootstrap/inspection/validation/migration implementation plus the
common state-authority lock for initialize/migrate administration. B2c
implements durable writer issuance and internal writer-session acquisition.

This threat model applies to the first SQLite backend architecture. B2b
implements bootstrap, migrations, observational validation, and the shared
state-authority lock for administration. B2c implements writer issuance and an
internal session. The current code still has no production `StateStore`
mutation backend.

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
- B2b rejects symlink, non-regular, group/other-accessible, and hardlinked
  state-authority lock files where safely testable;
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
state-authority lock. In B2c, mutation methods still fail before any apply
boundary with `writer_session_mutation_unavailable`.

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
