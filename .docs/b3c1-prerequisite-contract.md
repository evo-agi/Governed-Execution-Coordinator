# B3c1 Prerequisite Contract

Status: implemented B3c1a private WriterSession authority plumbing; no SQLite
transaction controller, nominal capability, fencing query, reader integration,
transaction runtime, or state mutation.

B3c1 freezes the contracts needed before the first rollback-only
transaction-authority implementation. It reconciles the production reachability
posture, pins the session-owned mutation slot, defines the minimal
operation-lease authority interface, freezes writer-row fencing ownership and
classification, records the nominal capability and epoch model, and splits the
runtime work into B3c1a and B3c1b.

B3c1a implements only `_WriterSessionResource` mutation-slot ownership,
`_WriterSessionMutationLease`, operation-lease active-authority validation,
private durable-writer-issuance verification, and `_WriterIssuanceMatch`. It
does not implement a writer-row `SELECT`, add a transaction controller, add a
concrete capability, open SQLite from transition or global-stop apply, execute
`BEGIN IMMEDIATE`, call B3b2 readers, assemble context, invoke the evaluator,
insert events, update work-item or global-stop state, change public
mutation-method behavior, modify migration 0001, or add migration 0002.

## B3c1 Boundary

B3c1 is production-unintegrated and test-executed only. B3c1a is private
WriterSession authority plumbing, not transaction or mutation runtime.

The B3c1 boundary is limited to:

1. the real shared per-`WriterSession` mutation slot;
2. the smallest safe operation-lease active-authority interface;
3. the smallest safe operation-lease durable-issuance verification interface;
4. one private nominal rollback-only transaction controller;
5. one private nominal transaction-read capability;
6. one fresh existing managed read/write SQLite connection;
7. `BEGIN IMMEDIATE`;
8. managed schema and connection-posture validation;
9. durable writer-row load and parse;
10. writer ref, generation, issued ref, and proof fencing;
11. one opaque transaction epoch;
12. permanent capability invalidation;
13. rollback-only transaction resolution;
14. connection cleanup;
15. coherent-fixture tests.

B3c1 still excludes event, idempotency, and sequence readers; current-state
readers; B3b2 reader calls; context assembly; expected-version checking;
evaluator invocation; event insertion; work-item or global-stop update; commit
uncertainty; production admission or authorization; and executable A2 behavior.

## Production Reachability

The future nominal transaction capability is created only by one private
rollback-only transaction controller. There is one controller construction
path. The controller construction path is the only path that may construct the
nominal capability.

Future production invocation may occur only from
`_SQLiteWriterSession.apply_transition()`. During B3c1a, the controller has no
production caller. coherent tests may invoke the same private controller
directly through private imports without adding a separate source-level
`for_test` factory. Direct private test invocation is not a public or
production authority route.

`_SQLiteWriterSession.apply_transition()` and
`_SQLiteWriterSession.apply_global_stop_update()` remain
`writer_session_mutation_unavailable` and contact no SQLite database during
B3c1a. A method that returns `writer_session_mutation_unavailable` has not
entered the B3c1 rollback-only controller, has not acquired the mutation slot,
has not opened SQLite, and has not produced a fencing result.

## B3c1a Mutation Slot

The B3c1a mutation slot is owned by `_WriterSessionResource`.

The representation is a dedicated private
`_WriterSessionMutationLease`. A Boolean field, count, or public token is not
the authority object.

The slot is:

1. one slot per `_WriterSessionResource`;
2. shared by transition mutation and future global-stop mutation;
3. distinct from `_active_operations`;
4. acquired only through an active `_WriterSessionOperationLease`;
5. acquired after mutation-specific local command checks and before any
   database open;
6. retained through the connection-close attempt;
7. released before the outer operation lease exits.

Contention is a prompt local `writer_session_mutation_in_progress`
`WriterSessionError` before SQLite. It must never degrade into SQLite
busy/locked behavior and must not create an apply conflict or event.

The mutation-lease identity binds internally to:

1. the owning operation;
2. the resource lifecycle epoch;
3. the owner process;
4. the owner thread;
5. an opaque slot token.

Release semantics are:

1. exact owner and token release clears the slot;
2. stale, duplicate, wrong-operation, wrong-lifecycle, wrong-process,
   wrong-thread, or fork-child release cannot clear a newer slot;
3. explicit mutation-lease close is the primary lifecycle path;
4. resource operation finish defensively clears a slot owned by the operation
   being finished;
5. no mutation-lease finalizer is primary lifecycle authority;
6. every exit path releases exactly once.

## Operation-Lease Interface

The `_WriterSessionOperationLease` private interface exposes only methods
equivalent to:

```python
_acquire_mutation_lease() -> _WriterSessionMutationLease

_require_active_mutation_authority() -> None

_verify_durable_writer_issuance(
    issuance: _DurableWriterIssuance,
) -> _WriterIssuanceMatch
```

`_WriterIssuanceMatch` is a closed private result with exactly:

- `MATCH`;
- `STALE_WRITER`.

The issuance argument is the exact `_DurableWriterIssuance` type produced
by `sqlite_writer_state.py`; structural lookalikes are not accepted. The
verification method must check owner process, owner thread, lifecycle epoch,
retained lock, writer ref, generation, issued ref, and the private proof
against the stored proof digest. `acquired_at` is not credential identity.

Every well-formed mismatch returns only `STALE_WRITER`. The caller must not
learn whether writer ref, generation, issued ref, or proof failed.

The interface must not expose the private credential object, raw proof, proof
digest, authority lock, lock descriptor, operation id, lifecycle epoch, writer
metadata as authority, process id, thread id, resource, transaction epoch, raw
SQLite row, or connection. No mismatch detail may appear in errors, reprs,
reports, test output, traces, or public payloads.

## Rollback-only controller result

The future B3c1b private rollback-only controller returns exactly
`_WriterIssuanceMatch`. It has exactly two return values: `MATCH` and
`STALE_WRITER`.

It returns `_WriterIssuanceMatch.MATCH` only after all of the following have
succeeded:

1. durable issuance verification returned `MATCH`;
2. nominal capability was created;
3. nominal capability was permanently invalidated;
4. rollback succeeded;
5. connection-close attempt succeeded;
6. no B3b2 reader was called;
7. no durable state was changed.

`_WriterIssuanceMatch.MATCH` means only that writer fencing mechanics passed
and rollback-only controller cleanup passed. It does not mean transition
accepted, apply completed, event persisted, replay persisted, state changed, or
transaction committed.

It returns `_WriterIssuanceMatch.STALE_WRITER` only after all of the following:

1. the durable row was well formed;
2. writer ref, generation, issued ref, or proof verification produced the
   closed `STALE_WRITER` result;
3. no nominal capability was created;
4. rollback succeeded;
5. connection-close attempt succeeded.

The controller returns neither enum value before rollback and close complete.
Missing, multiple, or malformed writer rows and managed schema/query
contradictions produce `database_integrity_failure` and no enum. Operational
open, `BEGIN`, `SELECT`, controller, rollback, and connection-close failures
produce `mutation_failed` and no enum. No rollback-only B3c1 path returns
`commit_outcome_unknown`.

`_WriterIssuanceMatch.STALE_WRITER` is an internal private result. Future
production apply integration owns the one conversion from
`_WriterIssuanceMatch.STALE_WRITER` to
`TransitionConflict("stale_writer_token")`.

The rollback-only controller must not directly return `TransitionConflict`,
`CommittedTransition`, `TransitionApplyOutcome`, events, replay records, writer
metadata, or mismatch details. Do not add a second enum, dataclass, union, or
result model for fenced versus stale outcomes. `_WriterIssuanceMatch` remains
private and unexported.

## Writer-Row Query

The future B3c1b writer-fencing query is:

```sql
SELECT
    singleton_id,
    writer_ref,
    generation,
    issued_ref,
    issuance_nonce_digest,
    acquired_at
FROM writer_ownership
ORDER BY singleton_id
LIMIT 2
```

The query reads `writer_ownership` only. It uses explicit columns, no
`SELECT *`, no idempotency table, no event table, no current-state table, and
bounded cardinality. It requires exact built-in tuple rows.

B3c1b must reuse `_parse_writer_ownership_rows` from
`sqlite_writer_state.py`. It must not create a second writer-row grammar. It
must not reuse the acquisition reader's outward error taxonomy as-is, because
writer acquisition and mutation fencing have different safe public
classifications.

No B3c1a SQL implementation exists.

## Writer Fencing

Fencing occurs before all idempotency, current-state, event, replay, and
context reads. Stale writer results carry no event or replay and disclose no
key existence.

| Case | Classification |
| --- | --- |
| closed session | local `WriterSessionError` before SQLite |
| process-mismatched session | local `WriterSessionError` before SQLite |
| mutation slot occupied | local `writer_session_mutation_in_progress` before SQLite |
| absent writer row while an active session exists | `database_integrity_failure` |
| multiple writer rows | `database_integrity_failure` |
| malformed writer row | `database_integrity_failure` |
| managed-schema contradiction | `database_integrity_failure` |
| writer-query contradiction | `database_integrity_failure` |
| operational open failure | `mutation_failed` |
| operational BEGIN failure | `mutation_failed` |
| operational SELECT failure | `mutation_failed` |
| well-formed writer ref mismatch | `stale_writer_token` |
| well-formed generation mismatch | `stale_writer_token` |
| well-formed issued-ref mismatch | `stale_writer_token` |
| proof mismatch | `stale_writer_token` |

There is no automatic reacquisition, takeover, TTL, heartbeat, or failover.
No proof, proof digest, mismatch detail, raw row, path, endpoint, secret, SQL
parameter, or private value may enter public errors, internal details, reprs,
reports, traces, or test output.

## Nominal Capability And Epoch

The future private module is:

`src/ge_nwp_coordinator/sqlite_transition_transaction.py`

This module remains future after B3c1a.

The future module owns one private nominal rollback-only transaction controller
and one private nominal transaction-read capability. The capability has no
public constructor, no package-root export, no finalizer, no independent close,
no public connection property, and no `WriterSession` metadata, credential,
proof, digest, lock, descriptor, operation identity, process identity, thread
identity, raw row, path, endpoint, or secret.

The capability is created only by the controller after successful writer
fencing. Structural `_TransitionReadCapability` conformance is not authority.

Each transaction has one opaque epoch. The epoch is private, identity-only, not
serializable, not comparable outside the controller, not public, and never
included in errors or outputs. The capability is same-process and same-thread
only. Transaction end or permanent invalidation classifies later borrow as
`transition_read_capability_expired`. Absent controller or absent connection
classifies as `transition_read_capability_unavailable`. Arbitrary internal
borrow failure is sanitized to `transition_read_capability_unavailable`.
Process mismatch is `process_mismatch`; thread mismatch is `thread_mismatch`.

The capability is invalidated before rollback. Invalidation is permanent.
Transaction A's capability cannot revive during transaction B on the same
connection.

## Rollback-Only Controller Lifecycle

The future B3c1b private lifecycle is:

1. enter with an active operation lease;
2. acquire the mutation lease;
3. open one fresh existing managed read/write connection;
4. execute `BEGIN IMMEDIATE`;
5. validate managed schema and connection posture;
6. query and parse the writer row;
7. verify durable issuance;
8. on `MATCH`, create the nominal capability;
9. call no B3b2 reader;
10. invalidate the capability;
11. roll back;
12. close the connection;
13. release the mutation lease;
14. exit the operation lease.

B3c1 never commits. `COMMIT` and `commit_outcome_unknown` remain outside the
rollback-only B3c1 tranche.

The minimal controller states are:

- `NEW`;
- `TRANSACTION_ACTIVE`;
- `FENCED`;
- `CAPABILITY_ACTIVE`;
- `RESOLVING`;
- `CLOSED`.

Invalidation may be represented as capability state rather than a separate
controller state.

## Cleanup And Error Precedence

Session or slot failure before SQLite remains an existing local
`WriterSessionError` before controller entry.

| Situation | Controller outcome |
| --- | --- |
| Fencing matched; invalidation, rollback, and close succeed | `_WriterIssuanceMatch.MATCH` |
| Well-formed stale mismatch; rollback and close succeed | `_WriterIssuanceMatch.STALE_WRITER` |
| Missing/multiple/malformed row | `database_integrity_failure` |
| Schema/query contradiction | `database_integrity_failure` |
| Operational failure | `mutation_failed` |
| Rollback failure | `mutation_failed`; no enum |
| Close failure | `mutation_failed`; no enum |
| Any rollback-only path | never `commit_outcome_unknown` |

Capability invalidation precedes rollback. `_WriterIssuanceMatch.STALE_WRITER`
is returned only after rollback and close both succeed. The controller returns
no enum before cleanup completes. The mutation slot remains held through the
connection-close attempt. Raw SQLite, OS, path, process, thread, row,
credential, proof, digest, epoch, endpoint, and secret details are suppressed.
No finalizer is the primary cleanup path.

## Implementation Split

B3c1a implements:

- runtime mutation slot;
- `_WriterSessionMutationLease`;
- operation-lease active-authority method;
- operation-lease durable-issuance verification;
- no SQLite transaction work;
- no transaction controller;
- no nominal capability;
- no public mutation-method behavior change.

B3c1b implements only:

- private transaction module;
- rollback-only controller;
- writer-query/parser wrapper;
- writer fencing;
- nominal capability;
- coherent-fixture tests;
- no B3b2 reader calls;
- no idempotency/event/sequence readers;
- no context assembly;
- no evaluator invocation;
- no state mutation;
- public mutation methods still unavailable.

Each slice requires an implementation-only prompt, a standalone
provenance-bound audit, and a separate commit. No fresh source snapshot is
required between accepted B3c1a and B3c1b commits unless evidence conflicts.
A fresh snapshot is required only after accepted B3c1b.
