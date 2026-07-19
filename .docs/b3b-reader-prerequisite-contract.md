# B3b Reader Prerequisite Contract

Status: contract-only prerequisite plus later B3b2b private SELECT readers and
a separate B3 tests-only coherent fixture graph.

B3b1 status: implemented pure/model full-row contracts and internal
operational timestamp envelopes only. No test database fixture insertion helper
exists in this tranche.

B3b2a is a later implementation slice. It adds private non-executing
capability-protocol and immutable query-spec contracts only; it does not change
this B3b prerequisite tranche into an executing reader, concrete transaction
authority, or fixture implementation.

B3b2b is a later implementation slice. It adds six private SELECT readers over
the B3b2a specs, with lookup validation, private capability borrowing,
parameterized `SELECT ... LIMIT 2`, `fetchmany(2)`, bounded cardinality,
tuple-to-private-mapping conversion, B3b1 adapter delegation, safe SQLite
SELECT-error classification, and cursor cleanup. Tests execute the readers
through a tests-only capability and in-memory tables. B3b2b still does not add
production integration, a concrete transaction capability, a fixture program,
transition/global-stop mutation, admission, or authorization implementation.

This document pins the authority contracts required before integrated typed
SQLite readers and test-only authoritative fixtures can be implemented. No test
database fixture insertion helper exists in this tranche. A later B3 tests-only
coherent fixture graph now lives under `tests/` only; it is not part of this
prerequisite tranche and is not production admission, authorization, reader
integration, or runtime authority. No production SQLite reader integration is
added. No transition mutation,
global-stop mutation, event insertion, work-item update, idempotency lookup,
replay runtime, event-sequence allocation, expected-version runtime, production
admission, authorization implementation, worker, scheduler, service, CLI, MCP,
connector, repair, commit, publication, or network behavior is added.

## Authority Chain

Future B3 transition reconstruction must validate the admitted backlog as
mandatory transaction authority. Because production admission does not exist,
B3 must not assume any lease, backlog, or work-item binding was checked before
the read transaction.

For the bounded B3 persisted-state slice, these values must be exactly equal:

- `WorkItemRecord.backlog_id`;
- `admitted_backlogs.backlog_id`;
- `FiniteBacklog.backlog_id`;
- `StandingLease.finite_backlog_reference`.

These values must be exactly equal:

- `admitted_backlogs.lease_ref`;
- `FiniteBacklog.lease_reference`;
- `WorkItemRecord.lease_id`;
- `StandingLease.lease_id`.

These values must be exactly equal:

- `admitted_backlogs.content_digest`;
- `FiniteBacklog.content_digest`;
- `StandingLease.finite_backlog_digest`.

The admitted backlog row must contain literal canonical `FiniteBacklog` JSON,
the exact finite-backlog schema id and schema version, and indexed/canonical
equality for backlog id, lease reference, and content digest. The canonical
finite backlog must contain exactly one matching current work item, must contain
no duplicate current work item, and its total item count must not exceed
`StandingLease.max_work_items`.

Classification:

- a missing command-referenced decision row is `validation_failed` where that
  row is required;
- a missing admitted backlog referenced by an existing `work_items` row is
  `database_integrity_failure`;
- any lease/backlog/work-item cross-record mismatch is
  `database_integrity_failure`;
- malformed or noncanonical backlog content is `database_integrity_failure`.

## Pure Binding Helper

`validate_b3_work_item_authority_binding(lease, backlog, record)` is a pure
internal contract helper. It performs no SQLite I/O, returns the exact matched
canonical backlog `WorkItem`, and raises only the safe
`database_integrity_failure` mutation-store classification on mismatch. It is
not a reader, fixture, report projection, admission helper, or package-root
export. It must not expose canonical JSON, private assignment refs, path policy,
raw row values, database paths, or other private material through public errors.

The helper relies on the existing typed `StandingLease`, `FiniteBacklog`, and
`WorkItemRecord` contracts. It must not introduce a second independent lease or
backlog digest algorithm.

## B3b1 Pure Row Contracts

B3b1 adds pure internal adapters for already-fetched complete row mappings:

- `lease_identity_records` to `LeaseIdentityRecordEnvelope`;
- `authorization_decision_receipts` to `AuthorizationReceiptEnvelope`;
- `dependency_decision_receipts` to `DependencyReceiptEnvelope`;
- `work_items` to `WorkItemRecordEnvelope`;
- `admitted_backlogs` to `AdmittedBacklogRecordEnvelope`;
- `global_stop_current` to `GlobalStopCurrentRecordEnvelope`.

These adapters require exact explicit column sets and map malformed row shape,
type, strict SQLite Boolean, canonical JSON, digest, index-column, timestamp,
singleton, enum, and nullable-state contradictions to
`database_integrity_failure`. They return typed internal envelopes only; they do
not return raw mappings or `sqlite3.Row` values.

B3b1 does not implement SQLite `SELECT` statements, `sqlite3` imports,
database paths, connections, row cardinality, missing-row/not-found
classification, a reader object, a combined transition-input loader, fixture
insertion, seed helpers, admission helpers, idempotency/replay, event-sequence
allocation, expected-version checks, transition mutation, or global-stop
mutation. B3b2b later consumes the B3b1 adapters from private readers but still
does not assemble cross-record transition input.

The single-row admitted-backlog contract validates literal canonical
`FiniteBacklog` JSON, exact schema id/version, embedded content digest,
row/model backlog id equality, row/model lease ref equality, and row/model
content digest equality. It does not invoke the cross-record
lease/backlog/work-item authority validator by itself.

The single-row `global_stop_current` contract validates the normalized
singleton columns and constructs one `GlobalStopState`. It does not read
global-stop event history and does not implement B4 mutation.

## Limit Provenance

For B3 v1, work-item attempt and repair limits are exact copies of the standing
lease limits:

`WorkItemRecord.max_attempts == StandingLease.max_attempts`

`WorkItemRecord.max_repairs == StandingLease.max_repairs`

No current `FiniteBacklog.WorkItem` field defines a narrower per-item override.
The mutable `work_items` row cannot invent such an override. Any future per-item
override requires a new versioned contract.

Reader integrity also requires:

`WorkItemRecord.attempt_count <= WorkItemRecord.max_attempts`

`WorkItemRecord.repair_count <= WorkItemRecord.max_repairs`

Any mismatch or over-limit current-state row is `database_integrity_failure`.

## Bounded Zero-Cost Slice

The first persisted B3 slice does not choose a scalar unit for dynamic budget
accounting. The scalar fields remain reserved compatibility fields:

`WorkItemRecord.budget_consumed == 0`

`WorkItemRecord.budget_limit == 0`

Future B3c command admission for this bounded slice requires:

`TransitionCommand.budget_cost == 0`

Accepted transition events in that slice must have:

`TransitionEvent.budget_cost_delta == 0`

Nonzero `WorkItemRecord` scalar budget fields are
`database_integrity_failure` under this bounded persisted-state contract.
Nonzero `TransitionCommand.budget_cost` is a local/pre-store unsupported
contract for future apply and produces no event. This prerequisite tranche does
not implement that future apply rejection path.

Zero does not establish an unlimited-budget architecture. The bounded slice
performs no worker/API expenditure and persists or consumes no nonzero dynamic
budget. Future multidimensional dynamic consumption accounting requires a
separately audited versioned contract and may require migration 0002.

## Static Budget Policy

`StandingLease` and `FiniteBacklog` remain the canonical static budget-policy
sources. The scalar current-state budget fields are not mapped to either static
dimension.

For each backlog work item:

`budget_allocation.api_calls <= StandingLease.compute_api_budget.api_calls`

`budget_allocation.compute_seconds <= StandingLease.compute_api_budget.compute_seconds`

Across the complete finite backlog:

`sum(api_calls allocations) <= StandingLease.compute_api_budget.api_calls`

`sum(compute_seconds allocations) <= StandingLease.compute_api_budget.compute_seconds`

`wall_clock_budget_seconds` remains lease-level policy and is not copied into
`WorkItemRecord`. A budget-policy contradiction in a purported admitted read
bundle is `database_integrity_failure`.

## Dependency References

For P1/B3 v1, dependency receipts are READY-only.

Target `ready`:

- `TransitionCommand.dependency_decision_ref` is required;
- the referenced receipt is required;
- the receipt `work_item_id` must be non-null;
- the receipt `work_item_id` must equal the current
  `WorkItemRecord.work_item_id`;
- a matching false decision is valid authoritative context and produces a
  domain rejection;
- a matching true decision may pass the dependency gate.

Every non-READY target:

- `TransitionCommand.dependency_decision_ref` must be null;
- no dependency receipt is read;
- the internal assembler uses the existing neutral unbound
  `DependencyDecision()` only as a non-authoritative evaluator shape;
- the neutral value is not persisted evidence and is not a receipt.

A non-null dependency ref on a non-READY command is local/pre-apply invalid and
produces no event.

## Timestamp Envelopes

Future B3b readers may retain these operational timestamps in internal typed
envelopes only:

- lease identity `created_at`;
- authorization receipt `created_at`;
- dependency receipt `created_at`;
- admitted backlog `admitted_at`;
- work-item `updated_at`;
- global-stop `updated_at`.

operational timestamps may be retained only in internal typed envelopes.
In B3b1 they validate as exact canonical UTC `Z` timestamps and remain outside
semantic model identity unless already defined elsewhere. They are not canonical
receipt digest inputs unless already defined, not operator/public report fields,
and not package-root exports.

Changing a valid operational timestamp changes only the internal envelope
timestamp. It does not change the reconstructed `StandingLease`,
`AuthorizationDecision`, `DependencyDecision`, `FiniteBacklog`,
`WorkItemRecord`, or `GlobalStopState`, and does not change those semantic
models' canonical digests.

## Schema Decision

schema 0001 is sufficient for the bounded B3b reader slice. No migration 0002 is
required for this tranche. Scalar dynamic budget accounting remains disabled.
Future multidimensional dynamic consumption accounting may require schema/model
evolution, and that decision must be made by a separately audited contract before
executable A2 behavior. Migration 0001 must not be modified.
