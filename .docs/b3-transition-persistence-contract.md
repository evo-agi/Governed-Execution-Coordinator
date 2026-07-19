# B3 Transition Persistence Contract

Status: B3a contract-only prerequisites, B3b/B3b1 reader prerequisites, B3b2a
private capability-protocol/query contracts, B3b2b private SELECT readers with
no production integration, B3c0a transition-authority/order contract pins,
B3c0b pure/static transition-event row, replay, idempotency, and sequence
contracts, and a B3 tests-only coherent fixture graph with no production
admission or runtime authority. B3c1 adds contract/static prerequisite pins for
the production-unintegrated rollback-only controller posture, future
resource-owned mutation slot, operation-lease interfaces, writer-row query and
parser ownership, fencing taxonomy, nominal capability epoch, cleanup
precedence, and B3c1a/B3c1b split only.

B3a defines the canonical persistence and provenance contracts required before
work-item transition persistence can be implemented. It does not implement
SQLite transition mutation, idempotency lookup, exact replay runtime,
expected-version checks, transaction-local readers, admission, operator-policy
authorization verification, global-stop mutation, a service loop, worker
execution, repair, commit, publication, or related-repo integration.

The B3b reader prerequisite contract is documented in
`.docs/b3b-reader-prerequisite-contract.md`. It adds only pure/model contract
pins for future typed SQLite readers and test-only authoritative fixtures. It
does not implement readers, fixtures, SQLite I/O, transition mutation,
global-stop mutation, admission, authorization verification, event insertion,
work-item updates, idempotency/replay, event-sequence runtime,
expected-version runtime, or migration 0002.

B3b1 implements a bounded subset of those pins: pure internal adapters for
complete already-fetched schema-0001 rows and timestamped envelopes. It does
not implement SQLite `SELECT` statements, connection ownership, row cardinality,
not-found classification, a combined transition-input loader, test database
fixture insertion, transition/global-stop mutation, idempotency/replay,
event-sequence allocation, expected-version checks, or migration 0002.

B3b2a implements immutable SELECT specifications and a private future-B3c
transaction capability protocol. It defines ordered row-column tuples as the
source of truth for the six B3b1 row shapes and derives existing key sets from
those tuples.

B3b2b implements the six private SELECT readers over those specs. They validate
lookup refs before borrowing, borrow only through the private
`_TransitionReadCapability` method, execute parameterized `SELECT ... LIMIT 2`,
call `fetchmany(2)`, classify zero/one/multiple cardinality, map exactly one
built-in tuple to a private mapping, delegate to B3b1 adapters, classify SQLite
SELECT failures safely, and close cursors without closing the connection. Tests
execute them through a tests-only capability and in-memory tables. No production
module invokes them.

B3b2b does not load transition context, inspect idempotency/replay/event
history, perform expected-version checks, begin/commit/rollback, own or close
connections, provide a concrete transaction-bound capability, accept raw SQLite
connections as reader authority, integrate with
`WriterSession.apply_transition`, add fixtures, mutate state, or add migration
0002. `connection.in_transaction` is not transaction identity. Future B3c must
own one opaque epoch per `BEGIN IMMEDIATE` transaction, invalidate it before
commit or rollback, and reject old epochs after transaction end or restart on
the same connection.

B3c0a freezes the future transition mutation authority and ordering contract in
`.docs/b3c0a-transition-authority-and-order.md`. It pins nominal capability
ownership, operation-guard lifetime, one-mutation-per-session policy,
writer-fencing order and taxonomy, safe capability-exception handling, exact
apply ordering, timestamp capture, capability invalidation, resolution
precedence, and event-ref/sequence collision posture. It still adds no concrete
capability, transaction controller, writer-fencing SELECT, event/replay row
contract, idempotency reader, event-sequence SQL, fixture, context assembler,
evaluator integration, or mutation.

B3c0b implements the pure/static event/replay row-contract portion that B3c0a
left future. It adds exact ordered `transition_events` row columns, a hidden
internal `TransitionEventRecordEnvelope`, canonical event and replay
reconstruction, digest/index equality, created-at/runtime equality, bounded
zero-budget replay checks, pure event-owned idempotency matching, immutable
data-only idempotency and maximum-sequence query specs, and pure sequence
allocation tests. It still adds no SQL execution, idempotency reader, event
reader, sequence reader, concrete capability, writer fencing,
context assembler, evaluator integration, event insertion, current-state update,
admission, authorization verifier, or migration 0002.

B3 tests-only coherent fixtures live under `tests/` only. They initialize a
temporary managed schema-0001 database, directly seed synthetic authoritative
rows through a test-setup transaction, validate and reconstruct through existing
B3b1/B3b2b/B3c0b contracts, acquire real internal writer issuance as temporary
test evidence, and may persist only a domain-rejected event/replay row produced
by the pure evaluator. Direct seeding is not admission or product mutation, and
the fixtures prove no accepted operator-policy authority, executable transition,
production admission, production runtime authority, or migration 0002.

B3c1 prerequisites are documented in
`.docs/b3c1-prerequisite-contract.md`. They replace the over-narrow capability
construction wording with one private rollback-only controller construction
path: future production invocation may occur only from
`_SQLiteWriterSession.apply_transition()`, while B3c1 itself gives that
controller no production caller and allows coherent tests to invoke the same
private controller through private imports. Public transition and global-stop
methods remain `writer_session_mutation_unavailable` and contact no SQLite
database. B3c1 adds no runtime mutation slot, controller, concrete capability,
writer-fencing query execution, B3b2 reader integration, context assembly,
evaluator invocation, event/state mutation, or migration 0002.

## Public Shape

`WriterSession.apply_transition` accepts only a `TransitionCommand`.
Caller-supplied `TransitionContext` is not an authority input to the future
store boundary. The concrete SQLite writer session remains internal and still
enters the private B2 operation guard before failing locally with
`writer_session_mutation_unavailable`.

`TransitionContext` remains the pure evaluator input, but future B3 must
construct it inside the fenced transaction from authoritative persisted rows:
current `WorkItemRecord`, lease identity record, authorization receipt,
dependency receipt when needed, `global_stop_current`, and transaction-derived
lease runtime status.

## P1 Disabled Stage Gate

P1 future worker-cycle, repair, and local-commit targets are invariantly
disabled: `cycle_starting`, `worker_running`, `validating`, `auditing`,
`repair_admitted`, `repair_running`, `commit_eligible`, and
`local_commit_completed`.

Pre-apply binding failures still occur before domain evaluation. Unsupported
target state precedes the stage gate. For any valid bound command targeting one
of the P1-disabled states, the pure evaluator returns a domain-rejected event
with reason `stage_not_enabled` before lease runtime, global stop, terminal or
predecessor checks, authorization, dependency, evidence, safe-failure-class,
budget, attempt, or repair-limit reasons can become the outcome.

The `stage_not_enabled` event still retains the complete authoritative context
provenance reconstructed for the transaction, including the nested
`LeaseRuntimeDecision`. Changing the runtime decision changes event identity
and digest even when the rejection reason remains `stage_not_enabled`.

P1 exposes no policy, provider, callback, environment variable, or
configuration that enables these targets. Future enablement requires an
explicit versioned contract.

## Lease Runtime

`LeaseRuntimeDecision` is the typed runtime lease-status input. It contains only
safe fields: schema id, lease ref, evaluated-at UTC timestamp, status, and
closed reason. The allowed statuses are:

- `active`;
- `not_yet_valid`;
- `expired`;
- `revoked`;
- `revocation_unknown`.

`derive_lease_runtime_decision(lease, transaction_time)` is pure. It accepts a
parsed `StandingLease` and one aware UTC transaction time. Stored lease
timestamps use the same timezone-aware ISO parser as lease identity validation:
`Z`, `+00:00`, and explicit nonzero offsets are accepted for lease bounds and
normalized only for comparison. Naive or malformed lease timestamps fail.
Transaction evaluation time must be UTC and serializes as exact
`YYYY-MM-DDTHH:MM:SSZ` in the runtime decision. It uses this precedence:

1. revoked;
2. revocation_unknown;
3. not_yet_valid;
4. expired;
5. active.

No current lease-status table or receipt exists in B3a. Dynamic revocation after
admission remains future contract work.

## Persisted Decisions

`AuthorizationDecision` includes `lease_identity_decision_ref`, which binds an
authorization receipt to the lease identity receipt. Its canonical mapping is a
closed JSON object over schema id, decision ref, lease ref,
lease-identity-decision ref, lease-identity validity, authorization model,
authorized, executable, and reason. The digest is SHA-256 over that canonical
JSON.

`authorization_model=unsupported` is the only currently supported production
runtime posture. It reconstructs the exact fail-closed decision and may lead to
a durable domain rejection when B3c exists. `authorization_model=operator_policy`
is schema vocabulary only until a separate authorization contract is accepted;
future B3 apply must classify it as `validation_failed` with no event, not as
database corruption merely because the vocabulary is present.

`DependencyDecision` includes `work_item_id: str | None`. A non-null value binds
the receipt to a work item. Null remains allowed only for explicitly documented
unbound dependency evidence. An authoritative READY transition must use a
non-null dependency receipt bound to the same work item and matching the
command dependency decision ref. A generic null receipt cannot satisfy that
gate. For P1/B3 v1, dependency receipts are READY-only: every non-READY
`TransitionCommand.dependency_decision_ref` must be null, no dependency receipt
is read for those targets, and the assembler uses neutral unbound
`DependencyDecision()` only as non-authoritative evaluator shape. A non-null
dependency ref on a non-READY command is local/pre-apply invalid and produces no
event. Its canonical mapping and digest are closed.

## Lease Identity Reconstruction

Future B3 readers must validate `lease_identity_records` by:

1. parsing `canonical_json` as `StandingLease`;
2. requiring the JSON to be exact canonical JSON for the parsed lease;
3. verifying the embedded lease digest through `validate_identity()`;
4. verifying row `canonical_digest` against canonical row content;
5. regenerating `LeaseIdentityValidation`;
6. requiring exact equality for decision ref, lease ref, identity validity,
   lease digest, and schema id.

Any mismatch is a database-integrity failure, not `validation_failed`.

## Event And Replay Canonicalization

`TransitionEvent` is the durable receipt. It includes semantic transition
fields plus provenance fields:

- `lease_identity_decision_ref`;
- `authorization_decision_ref`;
- `dependency_decision_ref`;
- `lease_runtime`;
- `global_stop_ref`;
- `global_stop_version`.

The canonical transition-event JSON includes `schema_id`, `event_ref`, all
semantic event fields, and all provenance fields. `lease_runtime` is the
complete nested `LeaseRuntimeDecision` mapping: schema id, lease ref,
evaluated-at timestamp, status, and reason. `event_digest` is SHA-256 over that
exact canonical event JSON. Event-ref derivation covers the same semantic
event payload and provenance, including `lease_runtime`, while excluding
`event_ref` itself. SQL `event_sequence` and SQL `created_at` are not
independently part of event JSON, event digest, or event identity.

The existing 24-hex event-ref digest prefix is preserved. If a future insert
finds a primary-key collision for a different canonical event, B3 must fail with
a safe mutation-store integrity failure and must not silently regenerate another
reference.

The replay `WorkItemRecord` canonical mapping includes schema id, work item id,
lease id, backlog id, state, version, counters, budget fields, limits, and
cleanup flag. It excludes SQLite `updated_at`, row ids, event sequence, and
writer metadata. `replay_work_item_digest` is SHA-256 over the exact canonical
replay JSON.

B3c0b's internal `TransitionEventRecordEnvelope` reconstructs both values from
an already fetched full row. `event_json` must equal
`TransitionEvent.canonical_json()` byte-for-byte and `event_digest` must equal
`TransitionEvent.canonical_digest()`. Every indexed event row column must equal
the reconstructed event, and `evidence_refs_json` must equal the exact
canonical JSON array derived from `event.evidence_refs`. `replay_work_item_json`
must equal `WorkItemRecord.canonical_json()`, its digest must match, and the
replay record must match event work item, lease, resulting state, and resulting
version. Constructing `CommittedTransition(..., replayed=True)` must succeed.
For the first bounded persisted slice, replay budget consumed, replay budget
limit, and event budget-cost delta must all be zero.

## SQL Mapping

Future `work_items` row mapping is exact for all `WorkItemRecord` fields.
`updated_at` is operational transaction metadata; it is not part of
`WorkItemRecord`, replay identity, or replay digest. Malformed row content is
database-integrity failure and must not be echoed publicly.

B3b1 exposes this mapping through an internal `WorkItemRecordEnvelope` and
preserves `work_item_record_from_row(payload)` as a compatibility helper that
returns only `.record`. The full-row adapter validates the exact schema-0001
column set and strict SQLite Boolean shape but does not by itself assemble the
cross-record lease/backlog/work-item authority bundle.

For the first bounded persisted B3 slice, `WorkItemRecord.max_attempts` and
`WorkItemRecord.max_repairs` are exact copies of `StandingLease.max_attempts`
and `StandingLease.max_repairs`. The current finite backlog has no per-item
override. `WorkItemRecord.attempt_count` and `WorkItemRecord.repair_count` must
not exceed those limits. Any mismatch is `database_integrity_failure`.

The scalar persisted budget fields are reserved compatibility fields in this
slice. `WorkItemRecord.budget_consumed == 0` and
`WorkItemRecord.budget_limit == 0` are mandatory reader-integrity checks.
Future B3c also requires `TransitionCommand.budget_cost == 0` and accepted
`TransitionEvent.budget_cost_delta == 0` for this bounded slice. Nonzero command
cost is a local/pre-store unsupported contract and produces no event. The pure
evaluator may retain generic nonzero-budget model tests; those tests do not
describe supported persisted B3 state.

Future SQLite Boolean writes must bind caller values through the typed Boolean
encoder: exact Python `bool` values become exact SQLite integers `0` or `1`.
The read-side row adapters accept only exact Python integers `0` or `1` from
SQLite and convert them back to `bool`. SQLite affinity, Boolean-looking
numeric values, and CHECK constraints alone do not prove the original caller
type, so future B3b/B3c writers may not bind raw numeric or caller-supplied
values for Boolean columns. Negative corruption tests may bypass the encoder
with raw row content under `tests/` only. No schema migration is required for
this contract.

`global_stop_current` is read internally by future B3. `GlobalStopState` has a
closed canonical read mapping. B3 does not trust caller-supplied global stop and
does not implement B4 global-stop mutation.

B3b1 adds a pure `global_stop_current` row contract. The row has no canonical
JSON or digest; its explicit normalized columns are current-state authority.
The adapter requires singleton id `1`, schema id
`governed-execution.nwp-global-stop.v1`, non-negative integer version, strict
SQLite Boolean `active`, active/clear nullable-field consistency, exact UTC `Z`
timestamps, and one valid `GlobalStopState`.

## Future Transaction Reconstruction

Inside the future fenced transition transaction, B3 follows the exact B3c0a
order. It first acquires the operation lease. Acquisition performs owner-process
and active-session validation and returns a lease only after the retained
authority lock is confirmed active. Any provisional operation registration is
synchronously unwound before a failure is returned. B3 then validates local
transition command shape, acquires the shared transition/global-stop mutation
slot, opens the managed read/write connection, executes `BEGIN IMMEDIATE`,
validates managed schema/posture, and fences the writer before idempotency
disclosure. After writer fencing and idempotency miss, it loads current
`WorkItemRecord`, classifies absence as `work_item_not_found`, compares expected
version, and only then loads context rows in this order:

1. the canonical lease through `lease_identity_records`;
2. the admitted backlog;
3. the authorization receipt;
4. the READY dependency receipt only when required;
5. `global_stop_current`.

The assembler then validates literal canonical `FiniteBacklog` JSON, schema
id/version, content digest, indexed/canonical equality, exact lease/backlog/work
item bindings, exactly one matching current work item, backlog size within
`StandingLease.max_work_items`, exact attempt/repair limit copies, zero scalar
current-state budget fields, static multidimensional budget policy,
authorization lease ref and lease-identity decision binding, unsupported
authorization model handling, READY dependency work-item binding, non-READY null
dependency refs, and command refs/version against authoritative state. Only
after successful binding does B3 capture the single transaction timestamp,
derive `LeaseRuntimeDecision`, construct `TransitionContext`, and invoke the
pure evaluator exactly once.

B3b2b implements only the private per-table SELECT readers that can load the
six individual rows when explicitly invoked by tests. Future B3c still owns
reader ordering, missing-row apply-conflict classification, cross-record
authority binding, lease runtime derivation, transaction timestamp,
`TransitionContext` construction, idempotency/replay, expected-version checks,
and mutation. Future B3c also owns the concrete transaction capability and
transaction lifecycle.

B3b1 row contracts retain row `created_at`, `admitted_at`, or `updated_at`
values only in internal typed timestamp envelopes. They validate exact UTC
`YYYY-MM-DDTHH:MM:SSZ` shape, do not add those values to semantic model identity
unless already defined, do not include them as canonical digest input unless
already defined, and do not expose them through operator/public reports or
package-root exports.

This current-row timestamp posture is separate from the future B3a event-row
rule below: `transition_events.created_at` must equal
`TransitionEvent.lease_runtime.evaluated_at` when transition apply exists.

## Sequence And Timestamp

Future transition event sequence allocation is:

- first sequence: `0`;
- future sequence: `COALESCE(MAX(event_sequence), -1) + 1`;
- calculation occurs inside `BEGIN IMMEDIATE`;
- accepted and domain-rejected events both consume sequence;
- rolled-back allocations may be reused;
- committed sequence is never reused because events are append-only;
- signed SQLite maximum overflow fails with `event_sequence_exhausted`.

Sequence is operational ordering metadata. It is not event identity, event
digest, or replay digest.

B3c0b preserves the pure `next_transition_event_sequence(...)` behavior:
`None -> 0`, non-negative integer maximum -> maximum plus one, bools/negative
values/non-integers as integrity failures, and signed SQLite integer maximum as
`event_sequence_exhausted`. It also defines immutable data-only SQL text for
future maximum-sequence inspection. No B3c0b code runs that query.

Future apply captures no new timestamp for exact replay, idempotency conflict,
work-item not found, expected-version conflict, or validation conflict. After
all prerequisite rows are loaded and cross-bound successfully, it uses one
transaction UTC timestamp for event `created_at`, accepted work-item
`updated_at`, and lease runtime derivation. It is exact
`YYYY-MM-DDTHH:MM:SSZ`. Future `transition_events.created_at` must equal
`TransitionEvent.lease_runtime.evaluated_at`: the SQL column is derived
transaction metadata, while the same semantic timestamp is integrity-bound
inside event JSON, event digest, and event identity through `lease_runtime`.
`created_at` is not independently hashed as a separate SQL column and remains
outside replay digest. Exact replay returns stored original timestamps.

B3c0b row reconstruction requires `transition_events.created_at` to be exact
whole-second UTC `YYYY-MM-DDTHH:MM:SSZ` and equal the reconstructed event's
`lease_runtime.evaluated_at`. Changing only `event_sequence` cannot change
event identity, event digest, replay record, or replay digest. Changing
`created_at` without changing lease runtime is integrity failure.

## B3c0b Idempotency And Query Specs

Event rows own transition idempotency. B3c0b's pure matcher returns:

- `None` when no already-fetched row exists;
- `database_integrity_failure` when the row is addressed under a different work
  item or idempotency key;
- `TransitionConflict("idempotency_key_reuse_conflict")` when work item and key
  match but command digest differs;
- `CommittedTransition(record=existing.replay_record, event=existing.event,
  replayed=True)` when work item, key, and digest match.

The matcher compares only against `TransitionCommand.canonical_command_digest`.
It does not reread context, generate timestamps, allocate sequences, invoke the
evaluator, mutate state, or invent another idempotency result model.

`sqlite_transition_event_contracts.py` defines immutable data-only specs for:

```sql
SELECT <all TRANSITION_EVENT_ROW_COLUMNS>
FROM transition_events
WHERE work_item_id = ? AND idempotency_key = ?
LIMIT 2
```

and:

```sql
SELECT MAX(event_sequence)
FROM transition_events
```

These specs have no runtime caller in B3c0b. B3c2 remains future for
idempotency/event/sequence readers over those specs.

## Error Taxonomy

`SQLiteMutationStoreError` is distinct from `SQLiteStateError`,
`WriterSessionError`, and `TransitionConflict`. Its closed public classes are:

- `database_integrity_failure`;
- `event_sequence_exhausted`;
- `mutation_failed`;
- `commit_outcome_unknown`.

`database_integrity_failure` covers malformed canonical JSON, digest mismatch,
indexed/canonical disagreement, impossible evaluator `PRE_APPLY_INVALID` after
authoritative reconstruction, and CAS rowcount mismatch inconsistent with a
prior authoritative load.

B3b2b also maps table-local SELECT contradictions to
`database_integrity_failure`: duplicate rows observed through `fetchmany(2)`,
wrong row tuple type or length, malformed rows rejected by B3b1 adapters,
missing mandatory `global_stop_current`, and SQLite primary result codes for
schema/query/database contradiction such as `SQLITE_ERROR`, `SQLITE_SCHEMA`,
`SQLITE_CORRUPT`, `SQLITE_NOTADB`, `SQLITE_MISMATCH`, and
`SQLITE_CONSTRAINT`.

`mutation_failed` means rollback/no commit is definite. `commit_outcome_unknown`
means the caller must retry with the same idempotency key; exact replay resolves
whether the previous attempt committed.
B3b2b maps every other SQLite SELECT failure, including closed connections,
busy/locked/I/O/full/interrupted, and missing or unknown result codes, to
`mutation_failed`; it never produces `commit_outcome_unknown`.

B3c0a pins transaction-resolution precedence: rollback failure supersedes a
planned replay, apply conflict, or other definite result with `mutation_failed`;
commit attempt failure returns `commit_outcome_unknown` and fabricates no result;
successful commit remains committed if connection close later fails; and an
event-ref or event-sequence uniqueness collision after idempotency miss is
`database_integrity_failure` with no identity or sequence regeneration outside
the transaction.

## Admission Boundary And First Proof

B3 operates only on pre-admitted authoritative rows. B3a adds no admission API
and no production helper that inserts leases, authorization receipts, backlogs,
dependency decisions, or initial work items. B3b/B3c may use test-only fixtures
under `tests/`; those fixtures must not be package-exported.

Because production admission does not exist, B3 must not trust that admitted
backlog, lease, work-item, static budget, or limit invariants were checked
previously. The future typed-reader tranche must validate them transaction-time
from authoritative rows.

Schema 0001 is sufficient for the bounded B3b reader slice. No migration 0002 is
required for these prerequisite contracts. Future multidimensional dynamic
budget consumption accounting requires a separately audited versioned contract
and may require schema/model evolution, but it must not modify migration 0001.

The B3 tests-only coherent fixture graph uses a temporary managed DB,
test-only seeded authoritative rows, an acquired internal writer session,
production unsupported authorization for durable domain rejection, optional
READY dependency receipts, exact replay, and safe current-state read-back. It
does not prove admission, accepted operator-policy authority, executable
authorization, an accepted transition, worker execution, service behavior,
global-stop mutation, repair, commit, publication, or related-repo authority.
