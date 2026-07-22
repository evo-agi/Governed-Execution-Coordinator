# B3c4b Private Atomic Transition Persistence

Status: implemented private atomic transition persistence runtime;
production-unintegrated; no public caller; no global-stop mutation.

B3c4b is the first Coordinator tranche that may durably persist a work-item
transition, but only through the existing private transaction-controller and
nominal-capability authority path in
`src/ge_nwp_coordinator/sqlite_transition_transaction.py`.

Public `_SQLiteWriterSession.apply_transition()` still raises
`writer_session_mutation_unavailable` and does not enter this path. B3c4c
remains the future public delegation tranche. `apply_global_stop_update()`
remains unavailable until B4.

## Single Controller

B3c4b renames the one private controller to
`_TransitionTransactionController`. The old rollback-only class name is gone;
there is no compatibility alias. The controller still has one construction
key, one mutation-lease path, one bound-connection open path, one
writer-fencing path, and one nominal capability constructor.

The existing private rollback-only entries remain:

```python
_run_rollback_only_writer_fencing(
    *,
    operation_lease: _WriterSessionOperationLease,
) -> _WriterIssuanceMatch

_run_rollback_only_transition_dry_run(
    *,
    operation_lease: _WriterSessionOperationLease,
    transition_command: TransitionCommand,
) -> _RollbackOnlyTransitionDryRunResult
```

B3c4b adds one private production-unintegrated entry:

```python
_run_atomic_transition_apply(
    *,
    operation_lease: _WriterSessionOperationLease,
    transition_command: TransitionCommand,
) -> TransitionApplyOutcome
```

No public API, package export, `StateStore` widening, CLI, MCP, connector,
worker, scheduler, service, report, or related repository calls this entry.

## Preflight And Shared Resolution

The atomic entry exact-gates the operation lease, then runs the existing
transition preflight exactly once before controller construction,
mutation-slot acquisition, state-location access, SQLite open, timestamp
capture, reader calls, sequence inspection, evaluator invocation, write-plan
construction, or SQL writes.

The controller uses one closed internal transition-resolution path shared by
the rollback-only dry run and the atomic apply. That path returns exactly one
of:

- `CommittedTransition(replayed=True)` for exact replay;
- `TransitionConflict` for apply conflicts;
- a private frozen slots-only fresh intermediate containing only the
  authoritative source `WorkItemRecord`, the exact `TransitionEvaluation`, and
  the normalized transaction timestamp.

The fresh intermediate has no serializer, no export, hides payloads from
`repr`, and retains no context, capability, controller, connection, operation
lease, mutation lease, epoch, row envelope, writer metadata, or filesystem
binding.

## Ordering

After preflight, both dry-run and atomic apply use the same authoritative read
and evaluation order:

1. acquire the mutation lease through the active operation lease;
2. derive the resource-owned state-database binding;
3. open one fresh existing managed read/write SQLite connection;
4. execute `BEGIN IMMEDIATE`;
5. revalidate filesystem binding and managed connection posture;
6. read and parse the bounded `writer_ownership` row;
7. verify durable writer issuance through the operation lease;
8. for stale writer, create no capability and return only
   `stale_writer_token` after rollback and close;
9. for matching writer, create exactly one nominal capability;
10. read idempotency event through `_read_transition_event_for_idempotency`;
11. call `match_transition_event_idempotency` exactly once;
12. on exact replay or idempotency conflict, skip current/context/evaluator,
    sequence, plan, writes, and commit;
13. on idempotency miss, read current work item;
14. compare expected version;
15. read lease identity;
16. read admitted backlog;
17. read authorization receipt;
18. read READY dependency receipt only when required;
19. read `global_stop_current`;
20. bind authority through `_bind_b3c3_transition_authority`;
21. capture exactly one whole-second UTC transaction timestamp;
22. derive one lease-runtime decision;
23. construct one `TransitionContext`;
24. call `evaluate_transition(...)` exactly once.

No reader or clock call occurs after evaluator invocation begins.
`PRE_APPLY_INVALID` remains `database_integrity_failure`; ordinary evaluator
failure remains `mutation_failed`.

## Fresh Persistence

Only a fresh accepted or domain-rejected evaluation continues to durable write
planning. The atomic path then:

1. reads `_read_transition_event_max_sequence(capability)` exactly once;
2. calls `next_transition_event_sequence(maximum)` exactly once;
3. calls the frozen B3c4a `_transition_write_plan(...)` exactly once with the
   fresh evaluation, authoritative source record, allocated sequence, and
   transaction timestamp;
4. executes the frozen event INSERT before any accepted-current CAS;
5. for accepted transitions only, executes the frozen accepted work-item CAS;
6. for domain-rejected transitions, performs no work-item UPDATE;
7. successfully invalidates the capability and records `capability_invalidated`;
8. records `commit_attempt_started`;
9. attempts exactly one `COMMIT`;
10. records `commit_succeeded` or `commit_outcome_unknown`;
11. attempts connection close and records `closed` only after close succeeds;
12. returns the fresh `CommittedTransition(replayed=False)` only after commit
   success, connection-close attempt, and mutation-slot release.

The transaction module consumes only the frozen B3c4a plan fields needed for
execution: event insert SQL and parameters, optional accepted CAS SQL and
parameters, and the planned transition. It does not recreate B3c4a SQL,
parameter order, canonicalization, event/replay mapping, current-row mapping,
or write-plan grammar.

## Rollback And Commit Resolution

Replay, idempotency conflict, stale writer, missing current row,
expected-version conflict, validation conflict, reader failure, binding
failure, timestamp failure, evaluator failure, sequence overflow, write-plan
failure, event INSERT failure, CAS failure, and capability-invalidation failure
are pre-commit paths. The controller rolls back while the transaction is still
active, closes the connection, releases the mutation slot after the close
attempt, and returns or raises only after cleanup resolves.

Cleanup failure before a commit attempt is `mutation_failed` and supersedes
planned replay, conflict, fresh output, or earlier definite safe errors under
the existing B3c1/B3c3 cleanup precedence.

B3c4b now mechanically enforces the accepted B3c4a.1 resolution graph for
successful commit-resolution milestones. The sole edge owner is the frozen
B3c4a `_TRANSITION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS` constant imported by
the transaction runtime; the runtime does not copy that set or define a second
graph. Constructor initialization to `new` is the only non-edge assignment.
After construction, the controller records each successful graph milestone only
through `_set_resolution_state(...)`, which exact-gates the retained current
enum value, exact-gates the requested next enum value, checks the frozen
allowed edge before assignment, and exposes no state names, edge names,
controller detail, SQL, rows, model data, paths, credentials, proofs, process
or thread data, or private sentinels on failure.

Replay, exact idempotency conflict, missing current row, expected-version
conflict, validation conflict, evaluator failure, sequence overflow, and
equivalent post-capability pre-plan exits follow:

```text
transaction_active
-> fenced
-> capability_active
-> capability_invalidated
-> rollback_resolved
-> closed
```

Planned-outcome failures before writes complete follow:

```text
transaction_active
-> fenced
-> capability_active
-> planned_outcome
-> capability_invalidated
-> rollback_resolved
-> closed
```

Definite post-write pre-commit failures follow:

```text
transaction_active
-> fenced
-> capability_active
-> planned_outcome
-> writes_performed
-> capability_invalidated
-> rollback_resolved
-> closed
```

Fresh commit-bearing paths follow:

```text
transaction_active
-> fenced
-> capability_active
-> planned_outcome
-> writes_performed
-> capability_invalidated
-> commit_attempt_started
-> commit_succeeded | commit_outcome_unknown
-> closed
```

Stale writer and failures before nominal capability creation remain outside
the capability-resolution graph. They may roll back and close operationally,
but they do not fabricate `capability_active`, `capability_invalidated`,
`rollback_resolved`, or `closed`; the retained graph state remains at the last
successful pre-capability milestone such as `transaction_active` or `fenced`.

Failed capability invalidation does not claim `capability_invalidated`; the
retained state remains `capability_active`, `planned_outcome`, or
`writes_performed` according to the already recorded location. Failed rollback
does not claim `rollback_resolved`. Failed close does not claim `closed`.
Operational cleanup may still continue after a cleanup failure, but later
successful operations do not retroactively establish missing graph milestones.
Successful capability invalidation is recorded before any successful rollback
resolution and before any commit attempt.

Commit is attempted only after successful capability invalidation is recorded.
After a commit attempt begins, the controller never issues rollback and never
infers success from `connection.in_transaction`, database contents, cursor
state, close behavior, or SQLite error class. A normal return from the explicit
commit operation is the only success signal. Any ordinary exception after the
attempt begins is collapsed to
`SQLiteMutationStoreError(commit_outcome_unknown)`.

Close failure after commit success leaves the retained resolution state at
`commit_succeeded` and does not reverse the committed result. Close failure
after commit uncertainty leaves the retained resolution state at
`commit_outcome_unknown` and does not change the uncertainty. No result escapes
before connection close has been attempted and the mutation slot has been
released. The bounded existing caveat remains: a synthetic failure before the
underlying close can leave the raw SQLite object alive outside controller
custody until cleanup or garbage collection. B3c4b does not add a registry,
finalizer, public handle, or close-semantics redesign.

## Collision And Retry Semantics

Event-ref, event-sequence, and work-item/idempotency uniqueness collisions
after idempotency miss are `database_integrity_failure`. The controller does
not regenerate event refs, timestamps, sequences, idempotency keys, or write
plans. It has no reservation table and no hidden automatic retry.

`None` maximum sequence allocates sequence `0`; otherwise the next sequence is
maximum plus one. `event_sequence_exhausted` is a definite pre-commit error.
Rolled-back sequence numbers may be reused; committed sequence numbers are
never reused because `transition_events` is append-only.

After `commit_outcome_unknown`, callers must retry explicitly with the same
work item, same idempotency key, and same canonical command digest. If the
prior commit succeeded, retry resolves by exact replay and performs no
timestamp, context, evaluator, sequence, write, or current-state update. If
the prior commit did not occur, retry applies normally as a fresh transition.
Same key with a different canonical digest remains an idempotency conflict.

## Non-Goals

B3c4b does not implement public writer-session delegation, persistent
global-stop mutation, admission, authorization verification, worker execution,
scheduling, service loops, repair, local commit behavior, publication,
Bridge/Codex invocation, CLI/MCP/connector behavior, related-repository
integration, schema-ID bump, migration 0002, or B4 operator-decision mutation.
