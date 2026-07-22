# B3c4a Transition Write And Commit Contracts

B3c4a is a pure/static prerequisite tranche for B3c4 durable transition
persistence. It freezes write specifications, value builders, a private planned
transition-write container, commit-resolution state vocabulary, SQLite
classification, retry, proof, public-integration, and B4-separation contracts.
It performs no SQLite mutation, opens no database handle, integrates no
transaction controller, attempts no commit, and changes no public
`WriterSession` behavior.

B3c4 remains split as:

- B3c4a: pure/static write and commit contracts only;
- B3c4b: private atomic transition apply through the one transaction
  controller;
- B3c4c: public `_SQLiteWriterSession.apply_transition(command)`
  delegation only.

B3c4a does not create a schema ID bump, does not edit migration 0001, and adds
no migration 0002.

## Module Boundary

`sqlite_transition_write_contracts.py` is a private, unexported module. It has
`__all__ == ()`, defines no public package-root export, imports no SQLite
runtime, performs no I/O, accepts no connection or cursor, and contains no
controller, capability, writer-session, or `StateStore` authority.

The module may import existing owner contracts only:

- `state_machine.py` for `TransitionEvaluation`, `TransitionEvent`, and
  `WorkItemRecord`;
- `persistence_contracts.py` for ordered row columns, canonical adapters,
  SQLite Boolean encoding, timestamp normalization, and signed integer bounds;
- `state_store.py` only for the existing public `CommittedTransition` result
  vocabulary;
- `sqlite_errors.py` for closed mutation-store errors.

It must not duplicate event, replay, current-row, idempotency, sequence, or
Boolean grammar.

## Event Insert Spec

B3c4a owns one private immutable transition-event insert specification. Its
columns equal `TRANSITION_EVENT_ROW_COLUMNS` and contain exactly 27 positional
parameters:

```sql
INSERT INTO transition_events (
    event_ref,
    event_sequence,
    work_item_id,
    lease_id,
    idempotency_key,
    command_digest,
    source_state,
    source_version,
    resulting_state,
    resulting_version,
    outcome,
    reason,
    evidence_refs_json,
    budget_cost_delta,
    attempt_count_delta,
    repair_count_delta,
    lease_identity_decision_ref,
    authorization_decision_ref,
    dependency_decision_ref,
    global_stop_ref,
    global_stop_version,
    schema_id,
    event_json,
    event_digest,
    replay_work_item_json,
    replay_work_item_digest,
    created_at
) VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?
)
```

There is no wildcard, no dynamic identifier, no `RETURNING`, no conflict
replacement, no `INSERT OR REPLACE`, and no execution method. B3c4b must
consume this specification rather than recreate the SQL grammar.

## Accepted CAS Spec

B3c4a owns one private immutable accepted-current-state CAS specification:

```sql
UPDATE work_items
SET
    lease_id = ?,
    backlog_id = ?,
    schema_id = ?,
    state = ?,
    version = ?,
    attempt_count = ?,
    repair_count = ?,
    budget_consumed = ?,
    budget_limit = ?,
    max_attempts = ?,
    max_repairs = ?,
    cleanup_required = ?,
    updated_at = ?
WHERE work_item_id = ?
  AND version = ?
```

The SET order is exactly `WORK_ITEM_ROW_COLUMNS[1:]`; the WHERE predicate is
only work-item id plus the authoritative source version. There is no
domain-rejected update spec, no `RETURNING`, and no execution path. B3c4b must
check rowcount exactly one after using this spec.

## Event Values

The private event-value builder accepts only exact `TransitionEvaluation`
instances whose kind is `ACCEPTED` or `DOMAIN_REJECTED`. `PRE_APPLY_INVALID`,
wrong types, invalid sequences, and timestamp mismatch fail closed as
`SQLiteMutationStoreError(database_integrity_failure)`.

The caller supplies only:

- the exact evaluation;
- an already allocated non-negative built-in integer event sequence within the
  SQLite signed integer maximum;
- the transaction timestamp.

The builder first safely reconstructs the supplied evaluation through the
accepted B3c3 private-object boundary. It derives every row value from the safe
event and safe replay record. The caller cannot supply event ref, command
digest, JSON, digest, replay record, evidence JSON, schema ID, deltas, or
operational columns. Caller-owned serializers, digest helpers, callbacks, and
dynamic attributes are never trusted. Canonicalization occurs only after safe
reconstruction. `created_at` must equal both the transaction timestamp and
`event.lease_runtime.evaluated_at`. The event row zips with
`TRANSITION_EVENT_ROW_COLUMNS` and round-trips through
`transition_event_record_envelope_from_row(...)`, which remains the final
integrity authority.

## Accepted CAS Values

The private accepted-CAS builder accepts an exact authoritative source
`WorkItemRecord`, exact accepted resulting `WorkItemRecord`, and transaction
timestamp. It requires:

- same work-item id;
- same lease id and backlog id;
- exact schema ID;
- resulting version equal to source version plus one;
- all state, counters, budget fields, limits, and cleanup flag mapped from the
  resulting record;
- cleanup encoded only with `encode_sqlite_boolean(...)`;
- updated-at equal to the transaction timestamp;
- WHERE parameters equal work-item id and source version.

The resulting current row zips with `WORK_ITEM_ROW_COLUMNS` and round-trips
through `work_item_record_envelope_from_row(...)`. Domain-rejected evaluations
must not construct CAS values.

Direct private value construction is mechanically validated. Factories are
conveniences, not the only source of invariants. A direct event-value or
accepted-CAS shell must reconstruct its nested models, recompute the canonical
expected parameter tuple, require exact positional equality including exact
scalar types, round-trip through the existing read adapter, and retain only the
fresh safe records, normalized timestamp, and expected parameter tuple.

## Write Plan

B3c4a adds one private frozen slots-only write plan. It is a grammar container,
not a receipt and not commit evidence.

Accepted evaluation:

- one event insert value object;
- one accepted work-item CAS value object;
- one private planned `CommittedTransition(replayed=False)`.

Domain-rejected evaluation:

- one event insert value object;
- no work-item CAS;
- one private planned `CommittedTransition(replayed=False)` over the unchanged
  replay record and durable rejection event.

`PRE_APPLY_INVALID`, replay, and apply conflicts produce no write plan. Exact
replay is already committed and belongs to idempotency lookup in B3c4b, not to
fresh write planning.

A fresh planned `CommittedTransition` may exist only inside the private plan
before commit. It must not escape to public caller code before B3c4b observes a
successful commit. A commit-attempt failure returns only
`SQLiteMutationStoreError(commit_outcome_unknown)` and no event, record, or
transition result.

Direct plan construction enforces the same invariants as the factory. It
reconstructs the planned transition, event-value object, and accepted-CAS value
object before cross-checking them, and it does not retain caller-supplied
private shells. An accepted write plan has one normalized transaction
timestamp: event `created_at`, event lease-runtime `evaluated_at`, and accepted
CAS `updated_at` must all equal that one timestamp. Individually valid event
and CAS values with different timestamps are invalid private contracts and
produce `SQLiteMutationStoreError(database_integrity_failure)`.

## Commit Resolution

B3c4a pins the future private state vocabulary:

- `new`;
- `transaction_active`;
- `fenced`;
- `capability_active`;
- `planned_outcome`;
- `writes_performed`;
- `capability_invalidated`;
- `commit_attempt_started`;
- `commit_succeeded`;
- `commit_outcome_unknown`;
- `rollback_resolved`;
- `closed`.

Replay/conflict path:

`transaction_active -> fenced -> capability_active -> capability_invalidated
-> rollback_resolved -> closed -> result escape`.

Fresh apply path:

`transaction_active -> fenced -> capability_active -> planned_outcome
-> writes_performed -> capability_invalidated -> commit_attempt_started
-> commit_succeeded OR commit_outcome_unknown -> closed`.

Successful post-capability rollback paths:

Before a write plan exists, replay, idempotency conflict, current-row conflicts,
validation conflicts, evaluator failure, sequence overflow, and equivalent
post-capability pre-plan exits reuse the replay/conflict path:

`transaction_active -> fenced -> capability_active -> capability_invalidated
-> rollback_resolved -> closed`.

After a plan exists but before writes complete, event INSERT failure, accepted
CAS failure before `writes_performed`, and equivalent planned-outcome failures
use:

`transaction_active -> fenced -> capability_active -> planned_outcome
-> capability_invalidated -> rollback_resolved -> closed`.

After writes complete but before commit attempt begins, equivalent definite
post-write pre-commit failures use:

`transaction_active -> fenced -> capability_active -> planned_outcome
-> writes_performed -> capability_invalidated -> rollback_resolved -> closed`.

The allowed edge set therefore includes
`planned_outcome -> capability_invalidated`. It does not include
`transaction_active -> capability_invalidated`,
`capability_active -> rollback_resolved`,
`planned_outcome -> rollback_resolved`,
`writes_performed -> rollback_resolved`, or any direct rollback edge that
bypasses successful capability invalidation.

Scope:

The graph records successful commit-resolution milestones after transaction
authority has entered a graph-covered path. It is not a complete model of every
operational cleanup attempt. Stale writer is the currently proved
pre-capability conflict exit and remains outside the graph. Managed validation,
writer-row read, fencing verification, or other failures before capability
creation likewise cannot fabricate `capability_active` or
`capability_invalidated`. Pre-capability cleanup is operational cleanup outside
the successful capability-resolution graph; B3c4b remains responsible for safe
rollback, close, and error taxonomy on those paths.

Authority-cleanup failures remain outside the successful graph. Failed
capability invalidation must not claim `capability_invalidated`; failed rollback
must not claim `rollback_resolved`; close failure where successful closure
cannot truthfully be claimed must not force a later graph milestone merely to
reach a terminal enum value. Operational rollback and close may still be
attempted after cleanup failure, but those attempts do not retroactively
establish missing successful graph milestones. B3c4b must enforce the graph for
successful state transitions and must not fabricate transitions on cleanup
failure.

B3c4a does not implement these transitions against a live controller. B3c4b
consumes this vocabulary in the private transaction controller and remains
responsible for enforcing graph-covered successful milestones without
fabricating cleanup milestones on failure. B3c4b must invalidate the capability
before commit attempt, must not roll back after commit attempt in a way that
claims non-commit, and must not infer commit success from connection state
alone.

## SQLite Classification

B3c4b classification is pinned as:

| Step | Condition | Result |
| --- | --- | --- |
| maximum-sequence read | schema/query/corruption/cardinality/shape contradiction | `database_integrity_failure` |
| maximum-sequence read | operational or unknown failure | `mutation_failed` |
| event insert | event-ref collision after idempotency miss | `database_integrity_failure` |
| event insert | event-sequence collision after idempotency miss | `database_integrity_failure` |
| event insert | `(work_item_id, idempotency_key)` collision after miss | `database_integrity_failure` |
| event insert | schema or constraint contradiction | `database_integrity_failure` |
| event insert | operational failure | `mutation_failed` |
| accepted CAS | rowcount other than one | `database_integrity_failure` |
| accepted CAS | schema or constraint contradiction | `database_integrity_failure` |
| accepted CAS | operational failure | `mutation_failed` |
| rollback before commit attempt | any rollback failure | `mutation_failed` |
| commit | any exception after attempt begins | `commit_outcome_unknown` |
| close before commit attempt | failure after otherwise successful rollback | `mutation_failed` |
| close after commit success | close failure | committed success remains success |
| close after commit uncertainty | close failure | uncertainty remains `commit_outcome_unknown` |

No raw SQLite text, SQL, parameters, rows, paths, connection reprs, exception
causes, credentials, proof material, digest material, or refs may survive in
public exceptions, reprs, notes, or payloads.

## Sequence Placement

B3c4a does not read maximum sequence and does not allocate sequence from a
database. B3c4b orders fresh evaluator output as:

1. call `_read_transition_event_max_sequence(capability)` exactly once;
2. call `next_transition_event_sequence(maximum)` exactly once;
3. construct insert parameters from this module;
4. insert the event.

No maximum-sequence read occurs for stale writer, exact replay, idempotency
conflict, work-item not found, expected-version conflict, validation conflict,
or pre-evaluation errors. `None -> 0`; next sequence is maximum plus one;
allocator overflow is `event_sequence_exhausted`. Accepted and domain-rejected
events consume sequence only if committed. Rolled-back sequences may be reused;
committed sequences are never reused. Event sequence remains operational
metadata, not event identity.

## Retry After Uncertainty

The caller receives `commit_outcome_unknown`. The controller performs no hidden
automatic retry. The caller retries with the same work item, same idempotency
key, and same canonical command digest, using either the same still-valid
writer session or a newly acquired valid writer session.

If the prior commit succeeded, retry resolves by exact replay. If it did not
occur, normal apply may proceed. Same key with a different digest is an
idempotency conflict. Exact replay skips timestamp capture, context readers,
evaluator invocation, maximum-sequence read, sequence allocation, and writes.

## Public Boundary

B3c4c, not B3c4a or B3c4b, makes
`_SQLiteWriterSession.apply_transition(command)` functional. That method
enters the existing operation guard, delegates to one private atomic entry,
contains no SQL, accepts no context, timestamp,
capability, or row data from the caller, and expose only
`TransitionApplyOutcome`, `TransitionApplyPreflightError`,
`WriterSessionError`, and closed mutation-store errors.

B3c4c adds only the public command-local `TransitionApplyPreflightError` and
`TransitionApplyPreflightFailureReason` vocabulary, the exact private-to-public
preflight mapping, the function-local import boundary, and the guarded public
delegate call. The public wrapper does not use a broad delegate-execution
catch-all that can turn commit uncertainty into definite `mutation_failed`.

`apply_global_stop_update()` remains unavailable until B4. No public database
reader/store is added, and `StateStore` is not widened by B3c4a or B3c4b.

## Proof Matrix

B3c4b focused tests prove:

- sequence 0;
- sequence increment;
- signed-max overflow;
- accepted write plan;
- domain-rejected write plan;
- exact event adapter round trip;
- exact work-item adapter round trip;
- replay/conflict no write plan;
- event-ref collision;
- sequence collision;
- idempotency collision after miss;
- insert failure;
- accepted CAS rowcount mismatch;
- CAS SQLite failure;
- rollback failure;
- commit uncertainty;
- commit succeeded then close failed;
- uncertainty then same-key replay;
- uncertainty then normal apply;
- crash/restart committed replay;
- crash/restart rolled-back reapply;
- no partial event or current-state row;
- process/thread/fork/capability behavior;
- public method later delegates only.

B3c4a tests prove only pure values, static SQL, private state vocabulary,
contract matrices, and adapter round trips. B3c4b tests prove private runtime
persistence through temporary managed databases. Test rows prove
persistence-contract mechanics only. They are not admission, not authorization,
not runtime authority, not executable transition proof, and not product state
initialization.

## B4 And Post-P1 Boundary

B3c4a adds no global-stop event insert, no global-stop current update, no
operator-decision mutation, no worker execution, no service loop, no scheduler,
no repair, no repository commit, no publication, no Bridge/Codex invocation,
no Connector, CLI, or MCP execution, and no related-repository lifecycle
authority.

B4 remains the sole future persistent global-stop tranche. After B3c4 and B4,
the Coordinator durable-state program should freeze before cross-repository
integration continues elsewhere.
