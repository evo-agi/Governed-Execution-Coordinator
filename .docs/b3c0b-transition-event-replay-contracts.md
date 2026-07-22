# B3c0b Transition Event Replay Contracts

Status: implemented pure/static contracts; no SQLite execution or mutation.
B3c2 has since implemented private transaction-internal readers over the
immutable query specs; B3c0b itself still performs no SQLite execution.

B3c0b implements only the pure transition-event row, replay, idempotency, and
sequence contracts needed before future B3c readers and mutation code exist. It
adds no concrete transaction capability, writer fencing, idempotency reader,
event reader, sequence reader, coherent fixture program, context assembler,
evaluator integration, transition/global-stop mutation, admission,
authorization verifier, worker behavior, public SQLite API, related-repo
integration, or migration 0002.

## Ordered Event Row

`TRANSITION_EVENT_ROW_COLUMNS` is the exact schema-0001 `transition_events`
full-row order:

1. `event_ref`
2. `event_sequence`
3. `work_item_id`
4. `lease_id`
5. `idempotency_key`
6. `command_digest`
7. `source_state`
8. `source_version`
9. `resulting_state`
10. `resulting_version`
11. `outcome`
12. `reason`
13. `evidence_refs_json`
14. `budget_cost_delta`
15. `attempt_count_delta`
16. `repair_count_delta`
17. `lease_identity_decision_ref`
18. `authorization_decision_ref`
19. `dependency_decision_ref`
20. `global_stop_ref`
21. `global_stop_version`
22. `schema_id`
23. `event_json`
24. `event_digest`
25. `replay_work_item_json`
26. `replay_work_item_digest`
27. `created_at`

`TRANSITION_EVENT_ROW_KEYS` is derived mechanically from that tuple. There is no
second independent full-row key list.

## Event Envelope

`TransitionEventRecordEnvelope` is an internal frozen envelope for one already
fetched row. It retains:

- `event_sequence`;
- the reconstructed `TransitionEvent`;
- the reconstructed replay `WorkItemRecord`;
- `created_at`.

The envelope has no schema id, serializer, report method, package-root export,
public reader API, SQL access, or mutation authority. The event and replay
record are hidden from repr.

The envelope is a closed internal durable row envelope. It accepts only exact
concrete nested `TransitionEvent` and `WorkItemRecord` values; subclass
conformance is outside the row-envelope contract.

## Event Reconstruction

`transition_event_record_envelope_from_row(payload)` accepts only an already
fetched mapping and performs no SQLite I/O. Malformed row content is reduced to
`SQLiteMutationStoreError(database_integrity_failure)` with no raw JSON, row
value, source exception, cause, context, note, internal detail, or traceback
payload retained.

The adapter reconstructs `TransitionEvent` from `event_json` and requires:

- non-empty bounded text;
- successful `TransitionEvent.from_json`;
- exact literal equality with `event.canonical_json()`;
- row `event_digest == event.canonical_digest()`;
- event-ref validity through `TransitionEvent` construction;
- every indexed row column to equal the reconstructed event, including schema
  id and all provenance refs;
- `evidence_refs_json` to equal the exact canonical JSON array derived from
  `event.evidence_refs`.

Alternate whitespace, alternate key order, alternate array spelling, digest
mismatch, or indexed mismatch is database-integrity failure.

`event_sequence` is operational ordering metadata. It does not affect event
ref, event digest, replay record, or replay digest.

## Replay Reconstruction

The adapter reconstructs replay from `replay_work_item_json` and requires:

- non-empty bounded text;
- successful `WorkItemRecord.from_json`;
- exact literal equality with `replay_record.canonical_json()`;
- row replay digest equality;
- replay work item id, lease id, state, and version to match the event result;
- `CommittedTransition(record=replay_record, event=event, replayed=True)` to
  construct successfully.

Replay JSON contains no SQLite `updated_at`, event sequence, writer metadata,
transaction metadata, or operational row timestamp.

For the bounded first B3 persisted slice:

- `replay_record.budget_consumed == 0`;
- `replay_record.budget_limit == 0`;
- `event.budget_cost_delta == 0`.

## Created At

`created_at` must be exact whole-second UTC `YYYY-MM-DDTHH:MM:SSZ` and must
equal `event.lease_runtime.evaluated_at`.

The SQL column is operational row metadata corresponding to the timestamp
already integrity-bound inside event JSON, event digest, and event identity
through `LeaseRuntimeDecision`. Changing `created_at` without changing the
event runtime is an integrity failure.

## Idempotency Match

`match_transition_event_idempotency(existing, command)` is pure and event-owned:

- no existing row returns `None`;
- an existing row addressed under another work item or idempotency key is
  `database_integrity_failure`;
- same work item and key with a different `command.canonical_command_digest`
  returns `TransitionConflict("idempotency_key_reuse_conflict")`;
- same work item, key, and digest returns
  `CommittedTransition(record=existing.replay_record, event=existing.event,
  replayed=True)`.

The pure idempotency matcher is a closed durable boundary. It accepts only
`None` or the exact concrete `TransitionEventRecordEnvelope`, and the exact
concrete `TransitionCommand`. Subclass conformance is not part of the persisted
idempotency contract.

After accepting an exact envelope, the matcher defensively rechecks that the
stored nested event and replay record are exact concrete `TransitionEvent` and
`WorkItemRecord` values before reading any nested semantic field. This exact-type
rule is local to the B3c0b durable row envelope and idempotency matcher; it is
not a repository-wide model, parser, evaluator, or public API policy.

The matcher does not reread context, generate a timestamp, invoke the evaluator,
allocate a sequence, mutate state, or invent another idempotency result model.

## Query Specs

`sqlite_transition_event_contracts.py` contains immutable data-only query
specifications. It performs no SQL I/O and has no runtime caller.

The idempotency lookup contract is:

```sql
SELECT <all TRANSITION_EVENT_ROW_COLUMNS>
FROM transition_events
WHERE work_item_id = ? AND idempotency_key = ?
LIMIT 2
```

The maximum sequence contract is:

```sql
SELECT MAX(event_sequence)
FROM transition_events
```

The idempotency spec uses explicit ordered columns, exactly two placeholders,
no `SELECT *`, no join, no subquery, no transaction token, and no global-stop
table. The maximum-sequence query is operational ordering only. B3c2 consumes
these specs only through private transaction-internal readers.

## Sequence Allocation

`next_transition_event_sequence(max_event_sequence)` remains pure:

- `None -> 0`;
- `0 -> 1`;
- positive maximum -> maximum plus one;
- bools, negative values, and non-integers are integrity failures;
- signed SQLite integer maximum raises `event_sequence_exhausted`.

Future B3c allocates a sequence only after evaluator outcome and before event
insert. Replay and apply conflicts allocate no sequence. Rolled-back sequence
numbers may be reused; committed sequence numbers are never reused.

## Boundary

B3c0b adds no SQL execution, idempotency reader, event reader, sequence reader,
coherent SQLite fixture, transaction capability, mutation slot, writer fencing,
context reconstruction, evaluator invocation, event insert, work-item update,
global-stop update, transaction handling, admission, authorization
implementation, worker, service, scheduler, CLI, MCP, connector, network,
repair, commit, publication, deployment behavior, migration 0002, or migration
0001 edit.

B3 tests-only coherent fixtures are implemented separately under `tests/` only.
They may persist only domain-rejected event/replay rows produced by the pure
evaluator and do not add SQL execution to B3c0b. B3c1 prerequisites are
contract/static plus B3c1a/B3c1b private authority and rollback-only
capability mechanics only. B3c2 adds private idempotency/event/sequence readers
outside B3c0b and keeps them production-unintegrated. B3c3 now calls the
idempotency reader and pure matcher from the private rollback-only dry-run
runtime for exact replay, idempotency-key reuse conflict, and miss handling.
B3c4 remains future for atomic persistence.
B3c4a now supplies the private pure/static write-side counterpart to these
read contracts: exact event-insert SQL, event/replay value construction, and
adapter round-trip proof through `transition_event_record_envelope_from_row`.
It does not execute the SQL, allocate sequence, insert rows, update current
state, commit, or alter the event/replay grammar. B3c4b remains future for
using the observed maximum-sequence reader and allocator inside a transaction.
