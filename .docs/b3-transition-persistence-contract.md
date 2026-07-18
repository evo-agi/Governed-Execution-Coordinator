# B3 Transition Persistence Contract

Status: B3a contract-only prerequisites with B3b reader prerequisite pins.

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

## SQL Mapping

Future `work_items` row mapping is exact for all `WorkItemRecord` fields.
`updated_at` is operational transaction metadata; it is not part of
`WorkItemRecord`, replay identity, or replay digest. Malformed row content is
database-integrity failure and must not be echoed publicly.

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

## Future Transaction Reconstruction

Inside the future fenced transition transaction, B3 must:

1. load current `WorkItemRecord`;
2. load the canonical lease through `lease_identity_records`;
3. revalidate lease identity and row/index equality;
4. load the admitted backlog and validate literal canonical `FiniteBacklog`
   JSON, schema id/version, content digest, indexed/canonical equality, exact
   lease/backlog/work-item bindings, exactly one matching current work item,
   backlog size within `StandingLease.max_work_items`, exact attempt/repair
   limit copies, zero scalar current-state budget fields, and static
   multidimensional budget policy;
5. load authorization receipt and verify canonical digest/index equality;
6. require authorization lease ref and lease-identity decision ref to match;
7. classify unsupported current authorization models as validation conflicts;
8. load dependency receipt only for READY commands and verify work-item binding;
9. require every non-READY command dependency ref to be null before apply;
10. load `global_stop_current`;
11. derive `LeaseRuntimeDecision` using one transaction UTC timestamp;
12. construct `TransitionContext` internally;
13. require command refs/version to match reconstructed context before the
    pure evaluator can produce an event.

B3a does not implement these reads.

Future B3b readers may retain row `created_at`, `admitted_at`, or `updated_at`
values only in internal typed timestamp envelopes. They must validate exact UTC
timestamp shape, must not add those values to semantic model identity unless
already defined, must not include them as canonical digest input unless already
defined, and must not expose them through operator/public reports or package-root
exports.

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

Future apply uses one transaction UTC timestamp for event `created_at`, accepted
work-item `updated_at`, and lease runtime derivation. It is exact
`YYYY-MM-DDTHH:MM:SSZ`. Future `transition_events.created_at` must equal
`TransitionEvent.lease_runtime.evaluated_at`: the SQL column is derived
transaction metadata, while the same semantic timestamp is integrity-bound
inside event JSON, event digest, and event identity through `lease_runtime`.
`created_at` is not independently hashed as a separate SQL column and remains
outside replay digest. Exact replay returns stored original timestamps.

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

`mutation_failed` means rollback/no commit is definite. `commit_outcome_unknown`
means the caller must retry with the same idempotency key; exact replay resolves
whether the previous attempt committed.

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

The first bounded B3 proof will use a temporary managed DB, test-only seeded
authoritative rows, an acquired internal writer session, production unsupported
authorization for durable domain rejection, an accepted non-executable
transition from an already-admitted test state, exact replay, idempotency
conflict, expected-version conflict, and not-found. It will not prove
admission, executable authorization, worker execution, service behavior,
global-stop mutation, repair, commit, publication, or related-repo authority.
