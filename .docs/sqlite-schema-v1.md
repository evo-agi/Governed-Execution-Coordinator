# SQLite Schema V1

Status: B1 initial migration schema with B1.1 live-schema validation, B3a
canonical persistence contracts, B3b reader prerequisite contracts, and B3b1
pure full-row envelope contracts. B3b2a query specs and B3b2b private SELECT
readers use schema 0001 without changing migration 0001. B3c0b adds pure/static
`transition_events` row, replay, idempotency, and sequence contracts against
the same frozen schema.

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
- Future writers must bind Boolean columns through the typed Boolean encoder:
  exact Python `bool` values become exact SQLite integers `0` or `1`.
  Read-side B3a adapters accept only exact Python integers `0` or `1` from
  SQLite. SQLite affinity and CHECK constraints alone do not prove the
  original caller type, so raw numerics or caller-supplied values are not a
  valid future write boundary.
- B3b1 reconstructs already-fetched explicit row mappings for lease identity,
  authorization, dependency, and admitted-backlog rows through the canonical
  JSON plus digest/index authority already present in schema 0001.
- B3b2b private readers fetch only explicit schema-0001 column tuples from one
  table at a time, map the tuple to a private mapping, and delegate to B3b1.
  They add no new durable table or column.

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
- mutable only through B2c writer acquisition;
- stores writer ref, generation, issued ref, and issuance nonce digest;
- raw issuance values are not stored.
- records latest durable fencing issuance only;
- does not prove a live writer session or authorize mutation.

`lease_identity_records`

- primary key: `decision_ref`;
- authority: canonical JSON plus digest;
- index columns: lease ref, identity validity, lease digest;
- B3a reconstruction parses `canonical_json` as `StandingLease`, requires exact
  canonical JSON, verifies the embedded lease digest through
  `validate_identity()`, verifies row `canonical_digest`, and requires indexed
  equality with the regenerated `LeaseIdentityValidation`;
- persisted Boolean columns must be exact SQLite integers `0` or `1` on read;
  Python booleans, floats, strings, nulls, and other numeric types are
  integrity failures in B3a row adapters;
- B3b1 full-row reconstruction additionally requires `created_at` as exact
  canonical UTC `Z` operational metadata and returns an internal
  `LeaseIdentityRecordEnvelope`;
- immutable.

`authorization_decision_receipts`

- primary key: `decision_ref`;
- authority: canonical JSON plus digest;
- index columns: lease ref, lease identity ref, authorization model,
  authorized/executable booleans, reason;
- B3a canonical JSON includes `lease_identity_decision_ref`;
- B3a requires internally coherent authorization flags and reason:
  `executable` implies `authorized`, `accepted` is the only authorized reason,
  and an invalid lease identity forces both flags false;
- `operator_policy` is schema vocabulary only until a separate authorization
  contract is accepted;
- B3b1 full-row reconstruction additionally requires `created_at` as exact
  canonical UTC `Z` operational metadata and returns an internal
  `AuthorizationReceiptEnvelope`; `operator_policy` remains untrusted schema
  vocabulary, not executable authority;
- immutable.

`admitted_backlogs`

- primary key: `backlog_id`;
- authority: canonical JSON plus content digest;
- index columns: lease ref and schema version;
- future B3b typed readers must require literal canonical `FiniteBacklog` JSON,
  exact schema id/version, indexed/canonical equality, exact equality with
  `WorkItemRecord.backlog_id`, `WorkItemRecord.lease_id`,
  `StandingLease.finite_backlog_reference`, `StandingLease.lease_id`, and
  `StandingLease.finite_backlog_digest`, exactly one matching current work item,
  and item count not greater than `StandingLease.max_work_items`;
- because production admission does not exist, these are mandatory read-time
  integrity checks for the first bounded B3 slice;
- B3b1 implements the single-row part of this contract: exact full row shape,
  safe backlog id, safe lease ref, schema id
  `governed-execution.nwp-finite-backlog.v1`, exact integer schema version `1`,
  lowercase SHA-256 content digest, non-empty bounded literal canonical JSON,
  exact UTC `admitted_at`, embedded content-digest verification, and row/model
  equality for backlog id, lease ref, schema id, schema version, and content
  digest. Cross-record lease/backlog/work-item binding remains the separate
  helper that future B3b2/B3c assembly must invoke;
- immutable.

`dependency_decision_receipts`

- primary key: `decision_ref`;
- authority: canonical JSON plus digest;
- index columns: work item ref, dependencies satisfied, reason;
- B3a canonical JSON includes nullable `work_item_id`; non-null values bind
  the receipt to a future command/current work item;
- a future authoritative READY transition requires a non-null matching
  work-item binding; an unbound generic receipt is not READY authority;
- P1/B3 v1 dependency receipts are READY-only. Non-READY
  `TransitionCommand.dependency_decision_ref` must be null, no dependency receipt
  is read for non-READY targets, and neutral unbound `DependencyDecision()` is
  internal evaluator shape only, not persisted receipt evidence;
- B3b1 full-row reconstruction additionally requires `created_at` as exact
  canonical UTC `Z` operational metadata and returns an internal
  `DependencyReceiptEnvelope`;
- immutable.

`global_stop_operator_decision_receipts`

- primary key: `decision_ref`;
- authority: canonical JSON plus digest;
- index columns: authorized and reason;
- B4a defines the exact ordered row contract: `decision_ref`, `authorized`,
  `reason`, `schema_id`, `canonical_json`, `canonical_digest`, and
  `created_at`;
- B4a reconstruction requires strict SQLite Boolean encoding, exact schema id,
  closed canonical JSON containing only `schema_id`, `decision_ref`,
  `authorized`, and `reason`, literal canonical JSON equality, canonical digest
  equality, indexed field equality, and exact canonical UTC `created_at`;
- B4a does not define receipt INSERT grammar or production receipt
  provisioning;
- immutable.

`work_items`

- primary key: `work_item_id`;
- authority: normalized columns;
- foreign keys: admitted backlog;
- mutable current-state table;
- B3a maps every `WorkItemRecord` field from normalized columns. `updated_at`
  is operational transaction metadata and is excluded from replay identity and
  replay digest;
- B3b1 returns an internal `WorkItemRecordEnvelope` that retains `updated_at`
  as exact canonical UTC `Z` operational metadata while preserving
  `work_item_record_from_row(payload)` as a compatibility helper returning only
  `WorkItemRecord`;
- B3b v1 requires `max_attempts` and `max_repairs` to be exact copies of the
  standing lease values. No finite-backlog work-item field defines a narrower
  override, and a mutable current-state row cannot invent one;
- B3b v1 requires `attempt_count <= max_attempts` and
  `repair_count <= max_repairs`;
- B3b v1 requires `budget_consumed == 0` and `budget_limit == 0`. These scalar
  fields are reserved compatibility fields for the first persisted slice and do
  not map either multidimensional static budget dimension into current state;
- no private assignment payloads.

`transition_events`

- primary key: `event_ref`;
- unique: `(work_item_id, idempotency_key)`;
- authority: canonical event JSON plus event digest;
- B3a canonical event JSON includes event ref, all semantic event fields, and
  lease-identity, authorization, dependency, lease-runtime, and global-stop
  provenance fields;
- `lease_runtime` contains the complete nested `LeaseRuntimeDecision` mapping
  and is covered by event ref and event digest;
- `transition_events.created_at` must equal
  `TransitionEvent.lease_runtime.evaluated_at`;
- `event_sequence` and SQL `created_at` are operational metadata. SQL
  `created_at` is not independently part of event JSON, event digest, event
  identity, or replay digest;
- B3c0b defines the exact ordered schema-0001 full-row contract:
  `event_ref`, `event_sequence`, `work_item_id`, `lease_id`,
  `idempotency_key`, `command_digest`, `source_state`, `source_version`,
  `resulting_state`, `resulting_version`, `outcome`, `reason`,
  `evidence_refs_json`, `budget_cost_delta`, `attempt_count_delta`,
  `repair_count_delta`, `lease_identity_decision_ref`,
  `authorization_decision_ref`, `dependency_decision_ref`, `global_stop_ref`,
  `global_stop_version`, `schema_id`, `event_json`, `event_digest`,
  `replay_work_item_json`, `replay_work_item_digest`, and `created_at`;
- B3c0b full-row reconstruction requires literal canonical event JSON, event
  digest equality, indexed/event equality, exact canonical `evidence_refs_json`,
  literal canonical replay `WorkItemRecord` JSON, replay digest equality, replay
  work item/lease/state/version equality with the event result,
  `CommittedTransition(..., replayed=True)` consistency, zero replay scalar
  budget fields, zero event budget-cost delta, and exact created-at/runtime
  equality;
- B3c0b defines immutable data-only query specs for future lookup by
  `(work_item_id, idempotency_key)` with all explicit columns and for future
  `MAX(event_sequence)` inspection. These specs have no runtime caller in
  B3c0b. B3c2 consumes them through private transaction-internal readers only,
  with no apply result ownership, sequence allocation, event insertion,
  current-state update, commit, or migration 0002;
- event-owned idempotency and replay snapshot;
- append-only by schema trigger.

`global_stop_current`

- primary key: singleton `singleton_id=1`;
- authority: normalized columns;
- mutable current-state table.
- B1 migration `0001_initial` seeds exactly one canonical clear row at version
  0 with no operator decision reference. This is not a global-stop event and
  not operator authorization.
- B3b1 validates already-fetched full rows by requiring exact integer singleton
  id `1`, schema id `governed-execution.nwp-global-stop.v1`, exact
  non-negative integer version, strict SQLite Boolean `active`, exact canonical
  UTC `updated_at`, active/clear nullable-field consistency, exact canonical
  UTC active `issued_at`, and one valid `GlobalStopState`. The row contains no
  canonical JSON or digest; the explicit normalized columns are current-state
  authority.

`global_stop_events`

- primary key: `event_ref`;
- unique: `idempotency_key`;
- authority: canonical event JSON plus event digest;
- B4a defines the exact ordered row contract: `event_ref`, `event_sequence`,
  `idempotency_key`, `command_digest`, `action`, `source_version`,
  `resulting_version`, `outcome`, `reason`, `operator_decision_ref`,
  `resulting_global_stop_ref`, `resulting_status`, `schema_id`, `event_json`,
  `event_digest`, `replay_global_stop_json`, `replay_global_stop_digest`, and
  `created_at`;
- B4a treats `event_sequence` as table-local to `global_stop_events`.
  It does not share sequence state with `transition_events` and does not claim
  cross-table ordering;
- B4a reconstruction requires deterministic event-ref consistency with the
  pure evaluator identity grammar, literal canonical event JSON and digest
  equality, indexed/event equality, exact replay `GlobalStopState` JSON and
  digest equality, replay state/result equality, and exact canonical UTC
  `created_at`;
- B4a pure/static write grammar defines future event INSERT and accepted
  singleton-CAS parameter shape only. It executes no SQL in B4a;
- event-owned idempotency and replay snapshot;
- append-only by schema trigger.

## Portability

The fixture avoids `STRICT` tables because B0 does not pin a minimum SQLite
runtime version. It uses explicit `CHECK` constraints for booleans, enums,
digests, singleton rows, and bounded text where practical.
Pure B3a persisted-row adapters intentionally narrow Boolean reconstruction to
exact integer `0` or `1`, because Python bools and float/numeric lookalikes are
not authoritative SQLite Boolean values.

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
- verify index-column equality against canonical JSON for all immutable records
  and events;
- verify admitted-backlog, lease, and current work-item authority bindings at
  transition read time;
- verify exact attempt/repair limit copies and zero scalar current-state budget
  fields for the bounded B3 reader slice;
- verify finite-backlog per-item and summed `api_calls` and `compute_seconds`
  allocations do not exceed the standing lease `compute_api_budget`;
- validate B3b1 operational row timestamps only inside internal envelopes and
  keep them outside semantic model identity, replay digest, event digest unless
  independently defined, reports, and package-root exports;
- verify event-owned idempotency uniqueness;
- verify replay snapshot digests;
- verify current-state versions against accepted events where applicable;
- verify domain-rejected events do not mutate current state;
- report divergence instead of repairing automatically.

B2b, B2c, and B3a require no schema change. B2c uses the existing
`writer_ownership` singleton. It does not add active/released status, release
timestamp, process id, lock inode, platform metadata, heartbeat, expiry,
takeover state, or liveness flag to SQLite because those are session/process
facts, not durable authority.

B3a selected schema 0001 as sufficient for the first work-item transition
persistence contract. B3b prerequisite contracts and B3b1 pure row contracts pin
schema 0001 as sufficient for the historical meanings used by the bounded
typed-reader slice: admitted backlog validation, exact limit provenance, zero
scalar budget posture, READY-only dependency receipts, global-stop-current row
reconstruction, and internal timestamp envelopes. Migration 0002 is now the
generation-2 physical C2B2 extension, while migration 0003 is the current
terminal cognitive proposal-selection extension; both leave migration 0001 and
those historical row meanings unchanged. Any later contract needing additional facts
not representable by the cumulative generation-2 schema requires separately
audited schema/model evolution and must not modify migration 0001.

B3b2a uses schema 0001 without changing it. The ordered row-column tuples match
the schema-0001 columns selected for internal readers, and the immutable query
specs are parameterized one-table `SELECT ... WHERE ... = ? LIMIT 2` contract
data only. B3b2a also defines only a private future-B3c transaction capability
protocol; it adds no concrete transaction authority and no durable
transaction-epoch field.

B3b2b executes those six private SELECT specs only when explicitly invoked by
tests. The readers do not read event or history tables, inspect
idempotency/replay state, seed rows, mutate current-state tables, or require
migration 0002. Tests use in-memory setup only and do not add a production
fixture program.

B3c0b uses schema 0001 without changing migration 0001. It adds only pure
mapping, canonical equality, idempotency-match, and query-spec contracts for
already fetched or future transition-event rows. It executes no SQL and adds no
idempotency/event/sequence reader, fixture, transaction capability, mutation, or
migration 0002.

B3c2 also uses schema 0001 without changing migration 0001. Its private
idempotency reader relies on the existing `(work_item_id, idempotency_key)`
unique constraint plus `LIMIT 2` for integrity posture, and its private maximum
reader observes the existing global `event_sequence` maximum. B3c2 adds no
index, durable fact, event insertion, current-state update, commit, or migration
0002.

B3 tests-only coherent fixtures preserve schema-0001 graph meanings without
changing migration 0001. They live under `tests/` only, initialize temporary
current generation-2 / migration-0003 physical databases, directly seed only
the historical synthetic authoritative rows as test setup, validate through
existing row contracts, acquire real writer issuance as temporary test evidence,
and may persist only domain-rejected event/replay rows. Their legacy seeding
leaves all nineteen C2B tables empty. They add no production fixture, admission,
authorization, concrete capability, fencing, context assembly, C2B row/value
adapter or reader, mutation, accepted operator-policy authority, executable
transition proof, migration change, or schema authority.

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

## B3c4a/B3c4b Schema Decision

B3c4a confirms schema 0001 is sufficient for the pure/static transition write
contracts consumed by B3c4b. Existing `transition_events` columns carry event
identity, global event sequence, work-item/idempotency uniqueness,
canonical event JSON/digest, replay work-item JSON/digest, created-at
timestamp, and accepted/domain-rejected consistency. Existing `work_items`
columns support the accepted current-state CAS by work-item id and source
version. B3c4a adds no correctness-required durable fact, and B3c4b adds no
schema-ID bump, no migration 0002, and no edit to migration 0001.
