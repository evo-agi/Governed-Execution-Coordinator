# SQLite Schema V1

Status: B1 initial migration schema with B1.1 live-schema validation.

Migration `0001_initial` is the authoritative B1 schema installation source and
is packaged under `ge_nwp_coordinator.sqlite_migrations`. The
`schemas/sqlite/coordinator-state-v1.sql` file remains a non-authoritative
fixture/snapshot for static and in-memory schema tests; it includes connection
posture comments and PRAGMAs that are not part of migration identity.

B1.1 validation derives the expected live-schema manifest from the packaged
`0001_initial` migration bytes in a temporary in-memory database. The manifest
accounts for user tables, views, explicit indexes, triggers, table columns,
declared types, nullability, defaults, primary keys, foreign keys, index
introspection, trigger bodies, and normalized schema-object definitions. A
recorded migration checksum is not sufficient by itself; the live schema must
match the manifest.

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
- B1 migration runner inserts the authoritative row atomically with successful
  schema installation.
- B1.1 managed validation requires migration id, sequence, checksum,
  compatibility bounds, row ordering, and UTC `Z` timestamp shape to match the
  packaged catalog exactly.

`writer_ownership`

- primary key: singleton `singleton_id=1`;
- authority: normalized columns;
- mutable only through future writer acquisition;
- stores writer ref, generation, issued ref, and issuance nonce digest;
- raw issuance values are not stored.
- records latest durable fencing issuance only;
- does not prove a live writer session or authorize mutation.

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
- B1 migration `0001_initial` seeds exactly one canonical clear row at version
  0 with no operator decision reference. This is not a global-stop event and
  not operator authorization.

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

B1.1 integrity checks:

- reject absent/empty/unknown databases as not managed;
- reject any unrecognized user-defined table, view, explicit index, or trigger;
- compare the full live-schema manifest against the packaged migration result;
- verify migration-history/catalog equality;
- verify exactly one `global_stop_current` singleton row;
- verify global-stop active/clear field consistency without forcing all future
  managed databases back to the bootstrap clear state;
- verify zero or one `writer_ownership` singleton row with schema-valid shape;
- verify append-only trigger bodies by manifest equality.

Future B2/B3 integrity checks must:

- verify all immutable record digests;
- verify event-owned idempotency uniqueness;
- verify replay snapshot digests;
- verify current-state versions against accepted events where applicable;
- verify domain-rejected events do not mutate current state;
- report divergence instead of repairing automatically.

B2a requires no schema change. It does not add active/released status, release
timestamp, process id, lock inode, platform metadata, heartbeat, expiry,
takeover state, or liveness flag to SQLite because those are session/process
facts, not durable authority.

## B1 Initialization Guarantees

Migration `0001_initial` creates schema objects and inserts its
`schema_migrations` row in one explicit transaction. On failure, no partial
schema or orphan history row may remain.

Immediately after B1.1 initialize, bootstrap invariants are:

- exactly one canonical clear `global_stop_current` singleton;
- version 0;
- no global-stop event;
- no writer ownership row;
- no lease, backlog, decision, work-item, transition, or global-stop event rows;
- no executable authorization state.

Generic managed validation is intentionally different from bootstrap
validation. Future B2/B3 databases may have nonzero or active global-stop
current state when schema-valid and backed by future mutation authority; B1.1
does not rewrite it or force it back to version 0.

The migration does not seed:

- `writer_ownership`;
- `lease_identity_records`;
- `authorization_decision_receipts`;
- `admitted_backlogs`;
- `dependency_decision_receipts`;
- `global_stop_operator_decision_receipts`;
- `work_items`;
- `transition_events`;
- `global_stop_events`.

The migration also does not seed executable authorization. The reserved
`operator_policy` authorization vocabulary remains schema vocabulary only until
a future authorization tranche defines and implements an accepted insertion and
verification path.
