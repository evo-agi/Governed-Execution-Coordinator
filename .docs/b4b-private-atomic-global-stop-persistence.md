# B4b Private Atomic Global-Stop Persistence

Status: implemented private atomic global-stop persistence runtime. B4c now
adds guarded public global-stop delegation as an adapter to this private entry.

B4b adds exactly one private global-stop mutation entry through the existing
Coordinator mutation authority in
`src/ge_nwp_coordinator/sqlite_transition_transaction.py`:

```python
_run_atomic_global_stop_apply(
    *,
    operation_lease: _WriterSessionOperationLease,
    global_stop_command: GlobalStopCommand,
    typed_operator_decision: GlobalStopOperatorDecision,
) -> GlobalStopApplyOutcome
```

No package-root export, `StateStore` widening, CLI, MCP, connector, worker,
service, scheduler, report, related-repository caller, schema-ID bump, or
migration `0002` is added. B4c changes public
`WriterSession.apply_global_stop_update(...)` only by making it a guarded
adapter to this private entry; SQL, receipt verification, evaluation, sequence,
write, rollback, COMMIT, and uncertainty ownership stay here.

## Neutral Mutation Authority

B4b neutralizes the previous transition-named private transaction authority
into one Coordinator mutation authority:

- one `_CoordinatorMutationTransactionController`;
- one `_SQLiteMutationReadCapability`;
- one `_MutationCapabilityState`;
- one `_create_sqlite_mutation_read_capability(...)`;
- one `_invalidate_sqlite_mutation_read_capability(...)`;
- one shared WriterSession mutation slot;
- one resource-owned state-root/lock/database binding path;
- one connection-open path;
- one writer-fencing path;
- one commit-resolution setter;
- one COMMIT boundary.

The private commit-resolution graph is owned only by
`sqlite_mutation_transaction_contracts.py` as
`_MutationCommitResolutionState` and
`_MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS`. The graph preserves the
B3c4 state values and edges for replay/conflict rollback, planned-outcome
failure, post-write precommit failure, fresh success, and fresh uncertainty.
Transition write contracts no longer own that graph.

The transaction SELECT support vocabulary is mutation-neutral:
`_MutationReadCapability`, `_MutationReadCapabilityError`, and
`_MutationReadCapabilityFailureReason`. These are still private, structural
reader contracts only. Concrete authority remains the controller-created
nominal capability after operation-lease validation, `BEGIN IMMEDIATE`,
managed validation, writer fencing, and opaque epoch creation.

## Preserved Transition Entries

B4b preserves the existing private transition entries:

- `_run_rollback_only_writer_fencing(...)`;
- `_run_rollback_only_transition_dry_run(...)`;
- `_run_atomic_transition_apply(...)`.

Public `_SQLiteWriterSession.apply_transition(command)` is unchanged in shape:
it enters the existing operation guard, performs its bounded function-local
import, maps only the existing transition preflight reasons, delegates once to
the private transition atomic entry, and does not gain SQL, transaction,
sequence, event, CAS, context, evaluator, capability, or global-stop logic.

## Receipt Authority

Operator/repo policy owns global stop and operator decisions. B4b verifies
only already-persisted immutable rows from
`global_stop_operator_decision_receipts`.

B4b does not insert, provision, upsert, import, register, update, delete, or
manufacture operator-decision receipts. Caller-supplied
`GlobalStopOperatorDecision` is never authority and is never used as fallback
when the persisted receipt is missing or malformed. It is only preflighted
and later compared against the persisted receipt.

Tests may seed receipt rows only in temporary tests-only databases. Those rows
prove private verification and persistence mechanics only; they are not
production operator-policy authorization. Production accepted-path reachability
remains incomplete until a separately governed receipt-provisioning integration
exists. That seam is not assigned by B4b to Control Plane, Bridge, CLI,
connector, app, channel, Execution Substrate, Infrastructure Manager, or
Maintenance Agent.

## Private Apply Order

The private global-stop entry exact-gates the operation-lease type, then calls
`_validate_global_stop_apply_preflight(...)` before controller construction,
mutation-slot acquisition, binding derivation, SQLite open, reader calls,
clock access, sequence inspection, evaluator invocation, or write planning.

After writer fencing matches, B4b performs the global-stop transaction in this
order:

1. read `global_stop_events` by idempotency key;
2. call `match_global_stop_event_idempotency(...)` exactly once;
3. return exact replay or idempotency conflict without current, receipt,
   evaluator, timestamp, sequence, write, or COMMIT;
4. read authoritative `global_stop_current`;
5. compare `expected_version`;
6. return `GlobalStopConflict("expected_version_conflict")` on mismatch;
7. read the persisted operator-decision receipt by command decision ref;
8. call `_bind_global_stop_operator_decision_receipt(...)` exactly once;
9. return validation conflict for missing or mismatched valid receipts;
10. treat malformed persisted receipt state as `database_integrity_failure`;
11. call `evaluate_global_stop_update(...)` exactly once with authoritative
    current state, safe command, and reconstructed persisted decision;
12. treat `PRE_APPLY_INVALID` as `database_integrity_failure`;
13. accept only fresh `ACCEPTED` or `DOMAIN_REJECTED` evaluations;
14. capture one normalized whole-second UTC transaction timestamp after the
    fresh evaluator outcome and before sequence/write planning;
15. read table-local maximum `global_stop_events.event_sequence` exactly once;
16. call `next_global_stop_event_sequence(...)` exactly once;
17. build the frozen `_GlobalStopWritePlan`;
18. execute the frozen global-stop event INSERT;
19. execute the accepted singleton `global_stop_current` CAS only for accepted
    evaluations and require rowcount exactly built-in integer `1`;
20. invalidate the capability;
21. attempt exactly one COMMIT;
22. resolve success, rollback, close, or uncertainty through the shared
    mutation commit-resolution path.

There is no timestamp, sequence read, allocation, write plan, event INSERT,
CAS, or COMMIT on stale writer, exact replay, idempotency conflict,
expected-version conflict, validation conflict, missing receipt, receipt
mismatch, malformed receipt, or pre-evaluation failure.

## Persistence And Atomicity

Accepted fresh evaluations persist one global-stop event and then CAS-update
the singleton `global_stop_current` in the same transaction. The event INSERT
precedes the accepted CAS. Domain-rejected fresh evaluations persist one
global-stop event and do not update `global_stop_current`.

Event-ref, event-sequence, or idempotency uniqueness collisions after an
idempotency miss are `database_integrity_failure`. Schema, constraint, or
corruption contradictions are `database_integrity_failure`. Busy, locked, I/O,
full, interrupted, readonly, closed, or unknown operational write failures are
`mutation_failed`. B4b does not regenerate event refs, timestamps, sequences,
idempotency keys, or write plans after collisions.

Event insert failure leaves no event/current change. Accepted CAS failure
rolls back the inserted event. Rolled-back sequence values may be reused.
Committed global-stop event sequences are table-local to `global_stop_events`,
start at `0`, increment by one, and are not reused.

## Commit And Retry

Before the COMMIT-attempt boundary, replay/conflict/error paths invalidate the
capability, attempt rollback, close the connection, and release the mutation
slot. Rollback failure is `mutation_failed`. Close failure before COMMIT may
supersede the planned precommit result or error as `mutation_failed`.

After COMMIT attempt starts, B4b does not roll back. Any ordinary COMMIT
exception is `commit_outcome_unknown`. Close failure after successful COMMIT
does not downgrade success. Close failure after uncertainty does not downgrade
or replace `commit_outcome_unknown`.

B4b performs no hidden automatic retry. If a COMMIT attempt raised before the
underlying commit happened, retry with the same key and digest applies fresh
and eventually commits one event and, for accepted outcomes, one singleton
update. If the underlying commit happened and then an exception was raised,
retry with the same key and digest returns exact replay with no evaluator,
sequence allocation, event insert, or CAS. Same key with changed digest returns
`GlobalStopConflict("idempotency_key_reuse_conflict")`.

## Concurrency And Capability

Transition and global-stop private mutations share the same WriterSession
resource mutation slot. Concurrent transition/transition, global/global,
transition/global, and global/transition attempts fail promptly for the second
mutation with `writer_session_mutation_in_progress`. They do not wait on
SQLite locks, open a second transaction, or release the first mutation's slot.

The neutral concrete read capability preserves the existing process, thread,
epoch, and expiry behavior: same-thread transaction reads work while active;
wrong-thread and fork-child/process mismatch fail before inherited SQLite use;
parent authority remains valid; capability expiry is permanent after rollback
or commit cleanup; and old transaction epochs cannot revive on the same
connection.

## B4c Public Adapter

B4c public global-stop delegation enters the existing operation guard, performs
bounded function-local imports, maps only the exact private B4a preflight
reasons to the public global-stop preflight vocabulary, classifies malformed
private preflight state as `database_integrity_failure`, maps pre-delegate
import/load failure to `mutation_failed`, and delegates once to
`_run_atomic_global_stop_apply(...)`. It has no generic delegate catch-all and
preserves `commit_outcome_unknown` exactly.

## Non-Claims

B4b and B4c add no receipt provisioner, schema change, migration `0002`, public
database reader/store, `GlobalStopApplyOutcome` change, transition behavior
change, worker behavior, scheduling, service loop, repair, local commit
behavior, publication, CLI/MCP/connector behavior, Bridge authority, Control
Plane authority, Execution Substrate authority, Infrastructure Manager
authority, Maintenance Agent authority, or related-repository authority.
