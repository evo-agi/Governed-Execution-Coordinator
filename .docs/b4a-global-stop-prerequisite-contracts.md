# B4a Global-Stop Prerequisite Contracts

B4a is a pure/static prerequisite tranche for persistent global-stop updates.
It adds public error vocabulary, private local preflight contracts,
persisted-row reconstruction contracts, transaction-internal SELECT readers,
table-local sequence allocation, receipt binding taxonomy, and pure write
grammar only.

B4a itself does not execute a global-stop mutation, insert a global-stop event, update
`global_stop_current`, begin a transaction, roll back, commit, make
`WriterSession.apply_global_stop_update(...)` functional, or provision
operator-decision receipts. B4b later implements private atomic global-stop
persistence, and B4c later implements guarded public global-stop delegation
without changing B4a's prerequisite ownership.

## Authority Boundary

Operator/repo policy owns global stop and operator decisions. The Coordinator
cannot mint an operator decision, cannot treat a caller-supplied
`GlobalStopOperatorDecision` as authority, and cannot manufacture a persisted
receipt from that caller input.

B4b private apply may only verify an already-persisted immutable
row in `global_stop_operator_decision_receipts`. Receipt provisioning remains a
separate governed integration seam outside B4a, B4b, and B4c. No current source
assigns that seam to Control Plane, Bridge, CLI, connector, app, channel,
Execution Substrate, Maintenance Agent, or Infrastructure Manager.

Tests may seed receipt rows only in tests-only temporary schema-0001 fixtures.
Those rows prove verification and persistence mechanics only; they are not
production operator-policy authorization.

## Public Preflight Vocabulary

B4a adds exactly two public global-stop preflight names:

| Reason | Value |
| --- | --- |
| `GlobalStopApplyPreflightFailureReason.INVALID_COMMAND` | `global_stop_apply_invalid_command` |
| `GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION` | `global_stop_apply_invalid_operator_decision` |

`GlobalStopApplyPreflightError` mirrors the transition public-preflight safety
boundary: exact enum type only, constant invalid-constructor `ValueError`, safe
string/args containing only the public reason value, constant repr, no
serializer, no canonicalization, no digest, no internal detail, and no hostile
input rendering.

These names do not widen `GlobalStopApplyOutcome`, `StateStore`, or the
`WriterSession` method signature. B4c now maps the private B4a preflight
vocabulary to these public reasons from the guarded public adapter.

## Private Preflight

`sqlite_global_stop_preflight_contracts.py` owns only no-I/O reconstruction of
`GlobalStopCommand` and `GlobalStopOperatorDecision`. It exact-gates top-level
types, extracts dataclass fields directly, reconstructs fresh safe copies,
verifies command digest consistency through the fresh command, rejects
subclasses and malformed exact shells, and never calls caller-owned serializers,
digest methods, filesystem, clock, random, network, SQLite, controller,
capability, operation lease, or mutation slot.

B4c maps private preflight as follows:

| Private condition | Future public/store classification |
| --- | --- |
| invalid command | `GlobalStopApplyPreflightFailureReason.INVALID_COMMAND` |
| invalid operator decision | `GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION` |
| malformed private preflight object or reason | `SQLiteMutationStoreError(database_integrity_failure)` |
| import/load failure before delegate invocation | `SQLiteMutationStoreError(mutation_failed)` |
| delegate exception | no generic delegate catch-all |

## Receipt Rows And Binding

`GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS` is the exact row shape:

`decision_ref`, `authorized`, `reason`, `schema_id`, `canonical_json`,
`canonical_digest`, `created_at`.

Receipt reconstruction requires strict SQLite Boolean encoding, schema
`governed-execution.nwp-global-stop-operator-decision.v1`, exact canonical UTC
`created_at`, closed canonical JSON containing only `schema_id`,
`decision_ref`, `authorized`, and `reason`, literal canonical JSON equality,
canonical digest equality, and indexed field equality. Malformed persisted
state is `database_integrity_failure`.

Receipt binding is separate from row reconstruction. A valid receipt and exact
caller/command match returns the reconstructed persisted decision for the pure
evaluator. Missing receipt, command decision-ref mismatch, caller decision-ref
mismatch, or caller field mismatch against a valid receipt is the future
`GlobalStopConflict("validation_failed")`. Persisted receipt contradictions
take precedence over caller mismatch and remain `database_integrity_failure`.
A valid unauthorized receipt is not a validation conflict; it is passed to the
evaluator and can produce a durable domain-rejected event in B4b.

## Event, Replay, And Idempotency

`GLOBAL_STOP_EVENT_ROW_COLUMNS` is the exact row shape:

`event_ref`, `event_sequence`, `idempotency_key`, `command_digest`, `action`,
`source_version`, `resulting_version`, `outcome`, `reason`,
`operator_decision_ref`, `resulting_global_stop_ref`, `resulting_status`,
`schema_id`, `event_json`, `event_digest`, `replay_global_stop_json`,
`replay_global_stop_digest`, `created_at`.

The canonical event mapping contains only `schema_id`, `event_ref`,
`command_digest`, `idempotency_key`, `action`, `source_version`,
`resulting_version`, `outcome`, `reason`, `operator_decision_ref`,
`resulting_global_stop_ref`, and `resulting_status`. Event-ref consistency is
checked against the existing pure evaluator identity grammar. `event_sequence`
and `created_at` are operational metadata outside event identity and replay
identity.

Replay is event-owned. The replay JSON/digest must reconstruct an exact
`GlobalStopState`, and its version, stop ref, and status must match the event
result. `CommittedGlobalStopUpdate(..., replayed=True)` must be valid for an
idempotency replay.

`match_global_stop_event_idempotency(existing, command)` returns:

| Existing row | Command digest | Result |
| --- | --- | --- |
| none | any | `None` |
| same idempotency key | same digest | `CommittedGlobalStopUpdate(replayed=True)` |
| same idempotency key | changed digest | `GlobalStopConflict("idempotency_key_reuse_conflict")` |
| address contradiction or malformed envelope | any | `database_integrity_failure` |

The only B4 apply-conflict classes are `stale_writer_token`,
`idempotency_key_reuse_conflict`, `expected_version_conflict`, and
`validation_failed`.

## Readers

`sqlite_global_stop_event_contracts.py` defines immutable SELECT specs for
receipt lookup by `decision_ref`, global-stop event lookup by
`idempotency_key`, maximum table-local global-stop event sequence, and
singleton current lookup for id `1`.

`sqlite_global_stop_readers.py` owns the private transaction-internal readers.
They accept only the existing nominal private transaction-read capability, use
the shared mechanical SELECT support, execute explicit parameterized SELECTs,
fetch at most two rows, interpret rows only after successful cursor close,
delegate row integrity to persistence adapters, and never begin, commit, roll
back, close the connection, invalidate capability, mutate state, or construct
public apply outcomes.

The existing transition read-scope module keeps `_read_global_stop_current` and
`_GLOBAL_STOP_CURRENT_SELECT` as mechanical compatibility imports only. The
global-stop reader module is the semantic owner for B4.

## Sequence

`next_global_stop_event_sequence(maximum)` is table-local to
`global_stop_events`. It returns `0` for an empty table, increments exact
built-in non-negative integers, rejects bool/subclass/negative/float/text or
malformed values as `database_integrity_failure`, and reports SQLite signed
integer exhaustion as `event_sequence_exhausted`. It does not share state with
`transition_events` and does not claim cross-table ordering.

## Write Grammar

`sqlite_global_stop_write_contracts.py` defines pure/static write grammar only.
It contains:

- an immutable `global_stop_events` INSERT spec with the exact schema-0001
  event columns and eighteen positional parameters;
- an immutable accepted `global_stop_current` singleton CAS spec for id `1`
  and authoritative source version;
- safe pure builders for event insert values, accepted singleton CAS values,
  accepted write plans, and domain-rejected event-only write plans.

Accepted plans contain one event insert, one singleton CAS, a planned
`CommittedGlobalStopUpdate(replayed=False)`, event/replay equality, and one
normalized transaction timestamp where event `created_at` equals current
`updated_at`.

Domain-rejected plans contain one event insert, no current update, unchanged
authoritative replay state, a planned `CommittedGlobalStopUpdate(replayed=False)`,
and one normalized event timestamp.

The module has no execution method, no receipt INSERT, no production receipt
provisioner, no `RETURNING`, no `INSERT OR REPLACE`, no `ON CONFLICT`, no
runtime caller, and no transaction control.

## B4b Transaction Order

B4b uses one existing operation lease, one shared mutation slot, one
state-root/lock/database binding, one writer-fencing path, one nominal read
capability, one commit-resolution graph, and one rollback/COMMIT/uncertainty
owner. B4b performs one closed neutralization of the previous transition-named
controller/capability/resolution vocabulary to
`_CoordinatorMutationTransactionController`, `_SQLiteMutationReadCapability`,
`_MutationReadCapability`, and `_MutationCommitResolutionState`.

B4b must preserve `_run_rollback_only_writer_fencing`,
`_run_rollback_only_transition_dry_run`, and `_run_atomic_transition_apply`.
It must reject a second controller, second capability constructor, second
mutation slot, raw connection API, public database handle, or parallel commit
state machine.

B4b order is:

1. preflight command and typed decision after session guard but before mutation
   slot or SQLite;
2. acquire the shared mutation slot;
3. derive the resource-owned binding;
4. open one existing managed read/write connection;
5. `BEGIN IMMEDIATE`;
6. revalidate binding and managed schema;
7. load and verify writer ownership;
8. writer fencing;
9. global-stop idempotency lookup;
10. exact replay or idempotency conflict exits;
11. load authoritative singleton current;
12. expected-version comparison;
13. load persisted operator-decision receipt;
14. verify command and typed decision against receipt;
15. invoke `evaluate_global_stop_update(...)` exactly once;
16. read maximum global-stop event sequence exactly once;
17. allocate sequence exactly once;
18. create the frozen write plan;
19. execute event INSERT;
20. for accepted evaluation, execute singleton CAS and require rowcount exactly
   `1`;
21. invalidate capability;
22. attempt COMMIT exactly once;
23. resolve close/result/uncertainty using accepted B3c4 rules.

There is no maximum-sequence read or write on stale writer, replay,
idempotency conflict, expected-version conflict, validation conflict, missing
receipt, or pre-evaluation failure. `PRE_APPLY_INVALID` after successful
receipt binding is `database_integrity_failure`.

## Commit, Uncertainty, And Retry

B4b reuses the accepted B3c4 contracts: capability invalidation before
rollback or COMMIT; rollback only before the COMMIT-attempt boundary; rollback
failure as `mutation_failed`; any COMMIT-attempt exception as
`commit_outcome_unknown`; no rollback after COMMIT attempt; successful COMMIT
plus close failure remains committed; uncertainty plus close failure remains
uncertain; same key/digest retry replays if the prior commit happened and fresh
applies if it did not; same key with changed digest conflicts; no hidden
automatic retry.

## Non-Claims

B4a adds no production admission, authorization verifier, worker,
orchestration, publication, Control Plane authority, Bridge authority,
Execution Substrate authority, Infrastructure Manager authority, Maintenance
Agent authority, connector authority, CLI authority, app authority, channel
authority, schema migration, schema-id bump, service, queue consumer, daemon,
or global product run truth.

B4b private atomic persistence is implemented. B4c public guarded delegation is
implemented. Receipt provisioning remains future governed work.
