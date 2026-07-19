# B3c1b Rollback-Only Writer Fencing

Status: implemented private rollback-only fencing/capability mechanics; no
B3b2 reader integration; no state mutation; no production caller.

B3c1b implements the private mechanics needed before future transition
mutation can read through a nominal transaction capability. It is
production-unintegrated and test-executed only. Public transition and
global-stop mutation methods remain `writer_session_mutation_unavailable` and
open no SQLite connection.

## Private Module

The implementation lives only in:

`src/ge_nwp_coordinator/sqlite_transition_transaction.py`

It is not imported or exported from the package root. It adds one private
controller entry point:

`_run_rollback_only_writer_fencing(operation_lease=...)`

The entry point accepts only the exact B3c1a
`_WriterSessionOperationLease` type. It accepts no caller-selected location,
database path, root path, optional override, callback, probe argument, or test
factory. Invalid private inputs fail with the safe mutation-store
`mutation_failed` class without object reprs or caller values.

## State-Root Binding

The controller database authority is derived from the active operation lease
after mutation-slot acquisition and before SQLite open. The operation lease
returns the exact private state-database filesystem-authority binding retained
by the WriterSession resource, not a caller-selected location. The invariant
is:

```text
controller database open binding
==
WriterSession resource-owned state-database binding
==
same CoordinatorStateLocation, state-root identity, authority-lock-file
identity, and database-file identity captured while the retained common
authority lock was held
```

The controller never accepts an independently constructed equivalent location
object from its caller. A caller cannot pair a lease from root A with root B,
and a matching `writer_ownership` row in another database is not authority.
Path aliases cannot be introduced through controller invocation. The retained
binding rejects a replaced visible state root, replaced visible lock file,
replaced visible database file, and hard-link aliases to the active database
file. The active fixed database file must have exactly one hard link. The
StateAuthorityLock, descriptors, paths, inode/device identities, and link
counts remain private and unexposed.

This is bounded local filesystem identity pinning. It is not a broad guarantee
against every adversarial same-account race, unsupported filesystem, or mount
namespace attack.

## Controller

`_RollbackOnlyTransitionTransactionController` is private and single-use. The
only construction path is the module-private entry point using a
module-private construction key. Tests invoke that same private entry point by
private import; there is no source-level `for_test` controller or alternate
factory.

The controller:

1. requires new same-process and same-thread execution;
2. acquires the B3c1a mutation lease from the active operation lease;
3. derives the resource-owned state-database binding through active mutation
   authority;
4. opens one fresh existing managed read/write SQLite connection through the
   private bound-existing SQLite open helper;
5. executes `BEGIN IMMEDIATE`;
6. revalidates the retained root/lock/database binding after `BEGIN`;
7. validates the current managed database through
   `_validate_current_managed_connection`;
8. reads the durable writer row with the exact B3c1 writer query;
9. reuses `_parse_writer_ownership_rows`;
10. calls only `operation_lease._verify_durable_writer_issuance(issuance)`;
11. creates exactly one nominal capability only for `MATCH`;
12. permanently invalidates the capability before rollback;
13. rolls back and closes the connection;
14. releases the mutation lease after the close attempt;
15. returns only `_WriterIssuanceMatch.MATCH` or
    `_WriterIssuanceMatch.STALE_WRITER` after cleanup succeeds.

The controller does not close the outer operation lease. The caller remains
responsible for exiting that operation guard.

## Writer Query

B3c1b adds one mutation-specific writer-fencing query:

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

The query reads only `writer_ownership`, uses explicit columns, has no
`WHERE singleton_id = 1`, uses `LIMIT 2`, and has no join, subquery, event,
idempotency, or current-state table access. Query metadata and SQL are bound
in one private immutable specification so column order and SQL cannot drift
independently.

The controller uses one cursor, calls `fetchmany(2)`, closes the cursor before
row shape validation and parsing, requires a built-in list of exact built-in
tuple rows, and passes the complete bounded row collection to
`_parse_writer_ownership_rows`. It does not duplicate the writer-row grammar.
A fetch failure remains the primary classified failure if cursor close also
fails; a successful fetch followed by cursor-close failure is `mutation_failed`.

## Fencing

The operation lease remains the only route to durable issuance verification.
B3c1b does not access private credentials, raw proofs, persisted proof digests,
lock objects, slot tokens, operation identities, writer-session resources, path
strings, filesystem identities, link counts, or safe writer metadata as
authority.

`_WriterIssuanceMatch.MATCH` is returned only after the writer issuance
matches, the nominal capability was created and invalidated, rollback
succeeded, close succeeded, no B3b2 reader was called, and no durable state
changed.

`_WriterIssuanceMatch.STALE_WRITER` is returned only after the durable writer
row is well formed, B3c1a verification returns `STALE_WRITER`, no capability
is created, rollback succeeds, and close succeeds. B3c1b does not convert that
private result to `TransitionConflict("stale_writer_token")`; future
production apply integration owns that conversion.

## Nominal Capability

`_SQLiteTransitionReadCapability` is private, nominal, constant-repr, and
constructed only by the controller through one module-private helper and
construction key. It structurally satisfies the private B3b2a
`_TransitionReadCapability` protocol by exposing only:

`_borrow_connection_for_select()`

The capability binds one exact built-in `sqlite3.Connection`, one opaque
identity-only epoch, owner process, owner thread, and a shared private
`_TransactionCapabilityState`. It has no public constructor, no public
connection or epoch property, no finalizer, no context-manager ownership, no
close method, no serialization path, and no writer metadata, credential, proof,
digest, lock, location, or operation identity.

Borrow checks run in this order:

1. owner process;
2. owner thread;
3. active capability state;
4. exact epoch;
5. exact attached connection identity;
6. active SQLite transaction.

Known failures use the existing closed private capability vocabulary:
`process_mismatch`, `thread_mismatch`,
`transition_read_capability_expired`, and
`transition_read_capability_unavailable`. Unknown connection-state failures are
sanitized to unavailable without retaining raw exception detail.

Permanent invalidation is controller-only, idempotent for the intended path,
clears the attached connection, marks the state permanently expired, and
happens before rollback. A capability cannot revive after invalidation or
during a later transaction.

## Cleanup Precedence

The mutation lease remains held through rollback and the connection-close
attempt. Cleanup order is:

1. invalidate capability if present;
2. roll back if the transaction began;
3. close the connection if it opened;
4. release the mutation lease;
5. return or raise.

Rollback or close failure returns `SQLiteMutationStoreError(mutation_failed)`
and no enum. Rollback failure still attempts close. Close failure supersedes
planned private results and planned definite errors after the controller has
accepted a connection into transaction resolution. Missing, multiple, or
malformed writer rows, managed-state contradictions, schema contradictions,
writer-query contradictions, retained filesystem-binding mismatches, replaced
root/lock/database paths, and hard-linked active database files are
`database_integrity_failure` only after cleanup. Operational
managed-validation failures are `mutation_failed` while the administrative
`SQLiteStateError` vocabulary remains unchanged. Operational filesystem open
or stat failures, `BEGIN`, operational `SELECT`, cursor-close, controller,
capability construction, capability invalidation, rollback, and close failures
are `mutation_failed`. B3c1b never uses `commit_outcome_unknown`.

Failed bound-open admission is different from controller transaction
resolution. If the bound-open helper opens a SQLite connection and then detects
a post-open structural binding contradiction, that structural contradiction
remains the primary private failure even if best-effort close of the rejected
connection also fails. If the post-open primary failure is operational, that
operational classification remains primary. The helper suppresses any rejected
connection close failure, does not retain or chain it, returns no connection,
and exposes no raw cleanup exception.

## Process, Thread, And Fork Limits

Controller execution and capability borrow are same-process and same-thread
only. Operation-lease process or thread failures remain local
`WriterSessionError` failures before SQLite where the B3c1a operation lease
owns that classification. A fork-child copy of the capability fails with
`process_mismatch` before touching the inherited SQLite connection, so the
parent transaction and mutation authority remain unaffected.

B3c1b does not claim arbitrary multithreaded-fork safety. It preserves the
existing B2/B3c1a lifecycle boundaries and adds no second session-authority
owner.

## Non-Goals

B3c1b does not call B3b2 readers, inspect idempotency, inspect transition
events, allocate sequences, read current work-item or global-stop state,
assemble `TransitionContext`, invoke `evaluate_transition`, insert events,
update current-state tables, commit, implement commit uncertainty, add
production admission or authorization, widen public `StateStore`, change
public `WriterSession` protocols, integrate with public mutation methods,
modify migration 0001, or add migration 0002.

B3c2 remains future for event, idempotency, and sequence readers.
B3c3 remains future for current/context assembly and evaluator dry run.
B3c4 remains future for atomic transition persistence and commit uncertainty.
