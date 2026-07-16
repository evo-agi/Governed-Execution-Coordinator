# SQLite Schema V1

Status: B0 non-production schema fixture.

The provisional schema fixture is `schemas/sqlite/coordinator-state-v1.sql`.
It is not a migration and must not be executed against a persistent file during
B0. Tests may execute it only against an in-memory SQLite database.

## Representation Authority Map

Current state and writer ownership:

- `writer_ownership`, `work_items`, and `global_stop_current` use normalized
  typed columns as authority.
- Derived or cached values must be recomputed or checked from those columns.

Immutable versioned contracts:

- lease identity records, backlog records, authorization receipts, dependency
  decision receipts, operator global-stop decision receipts, transition events,
  and global-stop events use canonical JSON plus schema id and canonical digest
  as authority.
- Index columns are derived from canonical content and must be validated before
  insertion.
- Integrity checks compare index columns to canonical JSON/digest.

Exact replay snapshots:

- `transition_events.replay_work_item_json` plus
  `transition_events.replay_work_item_digest` is authoritative only for exact
  replay of that transition command.
- `global_stop_events.replay_global_stop_json` plus
  `global_stop_events.replay_global_stop_digest` is authoritative only for exact
  replay of that global-stop command.
- Replay snapshots never supersede `work_items` or `global_stop_current` as
  current-state truth.

Projection:

- no report table exists;
- reports are generated from safe read ports and typed projection models only.

## Durable Data Scope

Authoritative current state:

- `work_items`;
- `global_stop_current`;
- `writer_ownership`;
- `schema_migrations`.

Immutable identity and decision records:

- `lease_identity_records`;
- `admitted_backlogs`;
- `authorization_decision_receipts`;
- `dependency_decision_receipts`;
- `global_stop_operator_decision_receipts`.

Immutable mutation events:

- `transition_events`;
- `global_stop_events`.

Replay state:

- exact original resulting `WorkItemRecord` snapshots on transition events;
- exact original resulting `GlobalStopState` snapshots on global-stop events.

Not stored in the first backend:

- raw work briefs;
- prompts;
- raw logs;
- credentials;
- endpoints;
- local absolute paths;
- Bridge evidence;
- connector records;
- worker artifacts;
- reports;
- support bundles;
- periodic report documents.

## Table Contract

`schema_migrations`

- primary key: `migration_id`;
- unique: `sequence`;
- authority: normalized migration id, sequence, checksum, and compatibility
  bounds;
- append-only by schema trigger;
- B0 fixture row only, no runner.

`writer_ownership`

- primary key: singleton `singleton_id=1`;
- authority: normalized columns;
- mutable only through future writer acquisition;
- stores writer ref, generation, issued ref, and issuance nonce digest;
- raw issuance values are not stored.

`lease_identity_records`

- primary key: `decision_ref`;
- authority: canonical JSON plus digest;
- index columns: lease ref, identity validity, lease digest;
- immutable.

`authorization_decision_receipts`

- primary key: `decision_ref`;
- authority: canonical JSON plus digest;
- index columns: lease ref, lease identity ref, authorization model,
  authorized/executable booleans, reason;
- immutable.

`admitted_backlogs`

- primary key: `backlog_id`;
- authority: canonical JSON plus content digest;
- index columns: lease ref and schema version;
- immutable.

`dependency_decision_receipts`

- primary key: `decision_ref`;
- authority: canonical JSON plus digest;
- index columns: work item ref, dependencies satisfied, reason;
- immutable.

`global_stop_operator_decision_receipts`

- primary key: `decision_ref`;
- authority: canonical JSON plus digest;
- index columns: authorized and reason;
- immutable.

`work_items`

- primary key: `work_item_id`;
- authority: normalized columns;
- foreign keys: admitted backlog;
- mutable current-state table;
- no private assignment payloads.

`transition_events`

- primary key: `event_ref`;
- unique: `(work_item_id, idempotency_key)`;
- authority: canonical event JSON plus event digest;
- event-owned idempotency and replay snapshot;
- append-only by schema trigger.

`global_stop_current`

- primary key: singleton `singleton_id=1`;
- authority: normalized columns;
- mutable current-state table.

`global_stop_events`

- primary key: `event_ref`;
- unique: `idempotency_key`;
- authority: canonical event JSON plus event digest;
- event-owned idempotency and replay snapshot;
- append-only by schema trigger.

## Portability

The fixture avoids `STRICT` tables because B0 does not pin a minimum SQLite
runtime version. It uses explicit `CHECK` constraints for booleans, enums,
digests, singleton rows, and bounded text where practical.

## Integrity Checks

Future integrity checks must:

- verify all immutable record digests;
- verify event-owned idempotency uniqueness;
- verify replay snapshot digests;
- verify current-state versions against accepted events where applicable;
- verify domain-rejected events do not mutate current state;
- report divergence instead of repairing automatically.
