# B3c3 Rollback-Only Transition Dry Run

Status: implemented private rollback-only transition dry-run runtime;
production-unintegrated; no durable mutation; no public caller.

B3c3 implements the private dry-run entry point:

```python
_run_rollback_only_transition_dry_run(
    *,
    operation_lease: _WriterSessionOperationLease,
    transition_command: TransitionCommand,
) -> _RollbackOnlyTransitionDryRunResult
```

The entry point remains module-private in
`sqlite_transition_transaction.py`. It is not package-root exported, not a
`StateStore` method, not a public `WriterSession` call site, and not used by
CLI, MCP, connectors, reports, workers, services, schedulers, or related
repositories. Public `apply_transition()` and `apply_global_stop_update()`
still fail locally with `writer_session_mutation_unavailable` and do not enter
the SQLite dry-run path.

## Controller Path

B3c3 reuses the single B3c1 rollback-only transaction controller and the single
nominal capability constructor. The unchanged fencing-only entry point still
returns `_WriterIssuanceMatch`. The dry-run entry point extends the same
mutation-lease, bound connection, `BEGIN IMMEDIATE`, managed validation,
writer-fencing, capability invalidation, rollback, close, and mutation-slot
release lifecycle. It adds no second controller, no second capability
constructor, no callback, no observer, no raw `sqlite3.Connection` parameter,
no generic mode, no caller-supplied `TransitionContext`, no caller-supplied
`LeaseRuntimeDecision`, and no caller-supplied timestamp.

Command preflight runs before mutation-slot acquisition, location binding,
SQLite open, timestamp capture, reader calls, matcher invocation, context
construction, and evaluator invocation. Local preflight failures expose only
the closed private preflight reason taxonomy and create no dry-run result.

## Ordering

After preflight, the dry run executes in this order:

1. acquire the existing mutation lease through the operation lease;
2. resolve the resource-owned bound state database;
3. open one fresh create-disabled read/write managed SQLite connection;
4. execute `BEGIN IMMEDIATE`;
5. revalidate filesystem binding and managed connection posture;
6. read and parse the bounded `writer_ownership` row;
7. verify durable issuance through the operation lease;
8. for stale writer, return only `stale_writer_token` after cleanup;
9. for matching writer, create exactly one nominal read capability;
10. read idempotency event through `_read_transition_event_for_idempotency`;
11. call `match_transition_event_idempotency` exactly once;
12. on exact replay or key-reuse conflict, skip all current/context/evaluator work;
13. on miss, read current work item;
14. compare expected version;
15. read context rows in the exact order: lease identity, admitted backlog,
    authorization receipt, READY dependency receipt if needed, global-stop
    singleton;
16. bind authority through `_bind_b3c3_transition_authority`;
17. capture exactly one private whole-second UTC transaction timestamp;
18. derive lease runtime;
19. construct exactly one `TransitionContext`;
20. invoke `evaluate_transition(current_record, command, context)` exactly once;
21. invalidate capability;
22. roll back;
23. close;
24. release the mutation lease;
25. return or raise only after cleanup succeeds.

Stale writer is decided before idempotency disclosure. Exact replay and
idempotency-key reuse conflict skip B3b2 readers, timestamp capture, lease
runtime derivation, context construction, evaluator invocation,
maximum-sequence read, sequence allocation, writes, CAS, and commit.

## Results

The dry-run result remains the private closed algebra defined in
`sqlite_transition_dry_run_contracts.py`:

- `EXACT_REPLAY` carries only an existing `CommittedTransition(replayed=True)`;
- `APPLY_CONFLICT` carries only `stale_writer_token`,
  `idempotency_key_reuse_conflict`, `work_item_not_found`,
  `expected_version_conflict`, or `validation_failed`;
- `ACCEPTED_EVALUATION_NOT_PERSISTED` carries fresh evaluator output only;
- `DOMAIN_REJECTED_EVALUATION_NOT_PERSISTED` carries fresh evaluator output
  only.

Fresh accepted and domain-rejected evaluations are candidate inspection data,
not receipts, not committed transitions, not event-history facts, and not
durable state. `PRE_APPLY_INVALID` after successful B3c3 binding is a
`database_integrity_failure`, not a dry-run result.

## Classifications

Missing current work item is `work_item_not_found`. Expected-version mismatch
is `expected_version_conflict`. Missing lease identity, missing authorization
receipt, missing READY dependency receipt, coherent command-address mismatch,
operator-policy authorization, and global-stop command mismatch are
`validation_failed`. Missing admitted backlog and missing global-stop singleton
are `database_integrity_failure`. Persisted-model contradiction remains
`database_integrity_failure` and precedes command mismatch. Unsupported
authorization and false READY dependency are retained as fail-closed evaluator
inputs where the frozen binding contract allows them.

## Timestamp And Evaluator

`_utc_transaction_timestamp() -> str` is private, zero-argument, uses current
UTC, normalizes through the existing timestamp helpers, and returns exact
whole-second `YYYY-MM-DDTHH:MM:SSZ`. It is called exactly once only after all
required rows are loaded and authority binding succeeds. Tests may monkeypatch
this exact private function. Clock or timestamp-normalization failure is
`mutation_failed` and produces no evaluator output.

After timestamp capture, B3c3 derives one `LeaseRuntimeDecision`, constructs
one `TransitionContext` from bound persisted authority plus neutral non-READY
dependency where required, and calls the pure evaluator exactly once. No reader
or clock call occurs after evaluator invocation begins.

## Cleanup And Non-Mutation

Capability invalidation occurs before rollback. Rollback failure supersedes any
planned replay, conflict, accepted evaluation, or domain-rejected evaluation
with `mutation_failed`; close failure after rollback also supersedes planned
results with `mutation_failed`. The mutation lease remains held through the
close attempt. B3c3 never returns `commit_outcome_unknown`.

B3c3 does not read maximum event sequence, call
`next_transition_event_sequence`, allocate a sequence, insert transition
events, update work items, update global-stop state, perform CAS, commit,
edit migration 0001, add migration 0002, bump schema IDs, implement admission,
implement operator authorization, or widen public behavior. B3c4 remains the
first owner of maximum-sequence integration, sequence allocation, event
insertion, state CAS/update, commit, rollback/commit resolution, and commit
uncertainty.
