# B3c0a Transition Authority And Order

Status: implemented contract/static prerequisite; no transaction capability or
mutation implementation.

B3c0a freezes the future transition mutation authority boundary before any
SQLite transition apply code exists. It adds documentation, static tests, one
future-safe writer-session failure reason, and defensive sanitation for
unexpected private read-capability exceptions. It does not implement a concrete
transaction capability, transaction controller, writer-fencing `SELECT`,
event/replay row contract, idempotency reader, event-sequence SQL, coherent
fixture, context assembler, evaluator integration, transition/global-stop
mutation, admission, authorization verification, worker behavior, CLI, MCP,
connector, or migration 0002.
B3c0b has since implemented pure/static transition-event row, replay,
idempotency, and sequence contracts only; it still does not implement any of
the B3c runtime steps above.

## Nominal Capability Ownership

Future B3c transition apply uses one private nominal transaction controller and
one private nominal transaction-read capability. The concrete class is not
trusted through structural Protocol conformance, is not a public reader, and is
not package-root exported.

The concrete capability is created only inside
`_SQLiteWriterSession.apply_transition()` while one valid
`_WriterSessionOperationLease` is active. Creation occurs only after:

1. opening one existing managed SQLite connection create-disabled and
   read/write;
2. executing `BEGIN IMMEDIATE`;
3. validating current managed schema and connection posture inside that
   transaction;
4. loading and parsing `writer_ownership`;
5. successfully verifying writer fencing.

The future implementation must use a module-private construction path or
sentinel. No raw-connection factory, public constructor, public connection
property, finalizer, independent close method, CLI/MCP/connector/report
exposure, package-root export, or `StateStore` observer API may create or hold
the capability. One opaque epoch belongs to exactly one transaction, never
changes, is never public, and cannot become valid again during a later
transaction on the same connection. The capability is invalidated before commit
or rollback, invalidation is permanent, and the object must not escape
`apply_transition()`.

B3b2a's `_TransitionReadCapability` Protocol remains only the private reader
shape. B3b2b's structural tests do not prove production transaction authority.
No B3c capability is created before or during fencing; it is created after
successful fencing.

## Operation Guard And Private Credential Boundary

The future B3c controller runs only while the B2c operation guard is active. The
operation lease spans command pre-store checks, mutation-slot ownership,
connection open, `BEGIN IMMEDIATE`, managed-schema validation, writer fencing,
reader calls, context binding, timestamp capture, evaluator invocation,
persistence, capability invalidation, commit or rollback, connection close, and
outward result construction.

Acquiring the `_WriterSessionOperationLease` is the source-backed
owner-process, active-session, and retained-lock gate with one externally atomic
result. The current B2 source has these internal phases:

1. pre-registration validation:
   - verify owner process;
   - under the lifecycle condition, require `ACTIVE` state;
   - require private credential presence;
   - require retained authority-lock presence;
2. provisional acquisition:
   - allocate and register one private operation id;
   - construct one private operation lease retaining the session, credential,
     and authority lock;
3. final retained-lock validation:
   - check `authority_lock.active`;
4. inactive-lock failure:
   - close the transient lease;
   - remove the provisional operation registration;
   - close the session;
   - raise `writer_session_closed`;
   - expose no lease to the caller;
5. successful acquisition:
   - return the lease only after the active-lock check succeeds.

Callers never receive an operation lease backed by an inactive authority lock.
An inactive-lock acquisition leaves no registered operation, closes the session,
retains no authority, attempts no mutation slot, opens no SQLite connection, and
returns the current closed `WriterSessionError`. Process-mismatched acquisition
still fails with `writer_session_process_mismatch`.

The smallest future private lease/controller interface may expose only:

1. a safe active-authority check;
2. verification of one already-parsed durable writer issuance against the
   session writer ref, generation, issued ref, and private credential proof.

It must not expose the private credential object, raw proof, proof digest,
authority lock, lock descriptor, writer metadata as authority, process/thread
identity, transaction epoch, or any raw SQLite handle. The reader capability
receives none of those values.

Closed or process-mismatched sessions fail locally before SQLite. Same-thread
close during an active operation remains `writer_session_close_during_operation`;
cross-thread close waits for the complete mutation operation. Forked-child use
remains fail-closed before SQLite.

## One Mutation Per Session

For the first B3/B4 mutation contract, at most one mutation transaction may be
active per `WriterSession`. This covers work-item transition mutation and future
global-stop mutation. The generic B2 operation registry may continue to support
other lifecycle operations; mutation transactions are additionally serialized by
a future private mutation slot.

A second concurrent mutation attempt fails locally before SQLite with
`writer_session_mutation_in_progress`. It does not block indefinitely, does not
surface SQLite busy/locked, creates no apply conflict, and creates no event. B2c
still raises `writer_session_mutation_unavailable` for mutation methods until a
future mutation tranche implements the slot.

The shared future transition/global-stop mutation prefix is:

1. acquire the B2 operation lease; acquisition performs owner-process and
   active-session validation and returns only after the retained authority lock
   is confirmed active;
2. perform mutation-specific local command-shape checks;
3. acquire the shared per-session mutation slot;
4. open one existing managed read/write connection;
5. execute `BEGIN IMMEDIATE`;
6. validate managed schema and connection posture inside the transaction;
7. load and parse the durable writer row;
8. verify writer fencing;
9. continue into mutation-specific idempotency, current-state, evaluator, event,
   and resolution behavior.

The mutation slot precedes database open, database open precedes
`BEGIN IMMEDIATE`, managed validation precedes writer fencing, and writer fencing
precedes idempotency disclosure.

## Mutation-Slot Lifetime

The complete future mutation-slot lifetime contract is:

1. the same future private session-owned mutation slot is shared by transition mutation and global-stop mutation;
2. the slot is acquired after mutation-specific local command checks and before opening any database connection;
3. the slot is retained through database open, `BEGIN IMMEDIATE`, managed validation, writer fencing, idempotency, all reads, cross-record binding, timestamp/runtime/context construction, evaluation, writes, capability invalidation, commit or rollback attempt, transaction-resolution error classification, and connection-close attempt;
4. the slot is not released merely because commit or rollback was attempted and remains held while connection cleanup is still running;
5. the slot is released only after the connection-close attempt completes and before the outer `_WriterSessionOperationLease` exits;
6. the slot is released on every path, including local transaction setup failure, reader failure, evaluator failure, write failure, rollback failure, commit uncertainty, and committed-success close failure;
7. a second transition/global-stop mutation cannot begin while the first is committing, rolling back, classifying transaction outcome, or closing the connection;
8. that second attempt fails promptly with future-only `writer_session_mutation_in_progress`, and this session-level rule never degrades into SQLite busy/locked behavior;
9. the slot remains future and unimplemented in B3c0a.

## Writer Fencing

The writer-fencing order is:

1. acquire the active `WriterSession` operation lease;
2. perform mutation-specific local command-shape checks;
3. acquire the shared per-session mutation slot;
4. open one existing managed SQLite connection create-disabled and read/write;
5. execute `BEGIN IMMEDIATE`;
6. validate current managed schema and connection posture inside the
   transaction;
7. load `writer_ownership`;
8. parse the durable writer row shape;
9. compare writer ref, generation, and issued ref;
10. verify the stored proof digest through the private credential;
11. create the nominal read capability only after successful fencing;
12. inspect event-owned idempotency only after successful fencing.

Classification matrix:

| Case | Classification |
| --- | --- |
| no writer row while an active issued session exists | `database_integrity_failure` |
| malformed writer row | `database_integrity_failure` |
| well-formed row with different writer ref | `stale_writer_token` |
| well-formed row with different generation | `stale_writer_token` |
| well-formed row with different issued ref | `stale_writer_token` |
| proof mismatch | `stale_writer_token` |
| closed session | `WriterSessionError` before SQLite |
| process-mismatched session | `WriterSessionError` before SQLite |
| schema/query contradiction while reading writer state | `database_integrity_failure` |
| operational SQLite failure | `mutation_failed` |

Stale writer precedes idempotency disclosure. A stale writer returns only
`stale_writer_token`; it receives no key-existence, replay, digest mismatch,
proof mismatch, or conflict detail. No proof or mismatch detail enters any
public error, internal detail, traceback, report, or replay payload.

## Transition Apply Order

The exact future transition apply order is:

1. acquire `_WriterSessionOperationLease`, including externally atomic owner-process, active-session, and retained-lock validation;
2. validate exact TransitionCommand type and already-established canonical digest;
3. enforce non-READY dependency ref is null and budget_cost is zero;
4. acquire the shared per-session mutation slot;
5. open one existing managed read/write connection;
6. BEGIN IMMEDIATE;
7. validate current managed schema and posture inside the transaction;
8. load and parse writer_ownership;
9. verify writer fencing;
10. create the nominal capability;
11. inspect event-owned idempotency;
12. on exact replay, skip all changed context;
13. on idempotency-key digest mismatch, return conflict;
14. read current work item;
15. if absent, work_item_not_found;
16. compare expected version;
17. if mismatch, expected_version_conflict;
18. read lease identity;
19. read admitted backlog;
20. read authorization;
21. read READY dependency only when required;
22. read global-stop singleton;
23. apply all cross-record binding and authorization-support checks;
24. capture one whole-second UTC transaction timestamp;
25. derive LeaseRuntimeDecision;
26. construct TransitionContext;
27. invoke evaluator exactly once;
28. allocate event sequence;
29. insert event and replay snapshot;
30. on acceptance, CAS-update current work item;
31. invalidate capability;
32. commit or roll back;
33. close connection;
34. return only after transaction resolution.

No B3c0a code implements any transition apply step except defensive sanitation
of unexpected private read-capability exceptions.

## Context And Error Ownership

Current work item and expected version are resolved before prerequisite context
rows. Context row order is lease identity, admitted backlog, authorization,
READY dependency only when required, then global-stop singleton. Readers return
typed row envelopes or reader-local safe errors only. No reader constructs
`TransitionConflict`, `TransitionEvent`, `TransitionContext`, reports, replay,
or mutation output.

Classification matrix:

| Case | Owner | Classification |
| --- | --- | --- |
| current work item absent | B3c apply boundary | `work_item_not_found` |
| expected-version mismatch | B3c apply boundary | `expected_version_conflict` |
| exact replay | B3c apply boundary | `CommittedTransition(replayed=True)` |
| same key with different command digest | B3c apply boundary | `idempotency_key_reuse_conflict` |
| missing lease identity | B3c apply boundary | `validation_failed` |
| missing authorization | B3c apply boundary | `validation_failed` |
| missing READY dependency | B3c apply boundary | `validation_failed` |
| missing admitted backlog after current-state binding | B3c apply boundary | `database_integrity_failure` |
| missing global-stop singleton | reader or B3c apply boundary | `database_integrity_failure` |
| command refs inconsistent with valid authoritative rows | B3c apply boundary | `validation_failed` |
| contradiction among authoritative persisted rows | B3c apply boundary | `database_integrity_failure` |
| evaluator PRE_APPLY_INVALID after successful B3c binding | B3c apply boundary | `database_integrity_failure` |
| domain rejection | B3c apply boundary | one durable event and unchanged replay/current record |
| acceptance | B3c apply boundary | one durable event and one CAS current-state update |

Authorization model `unsupported` remains the only production posture and may
lead to fail-closed domain rejection. `operator_policy` remains schema
vocabulary only and is a `validation_failed` conflict until a separate
authorization contract exists.

## Timestamp Capture

No transaction timestamp is generated on exact replay, idempotency conflict,
work-item not found, expected-version conflict, or validation conflict.

The timestamp is captured only after all prerequisite rows have been loaded and
cross-bound successfully, and before lease-runtime derivation, context
construction, evaluator invocation, sequence allocation, event insertion, or
accepted-state update. One exact whole-second UTC `Z` timestamp drives:

- `LeaseRuntimeDecision.evaluated_at`;
- `transition_events.created_at`;
- accepted `work_items.updated_at`.

Exact replay returns the stored original timestamp. Timestamp-generation failure
is `mutation_failed` with no event and no fabricated result.

## Capability Error Vocabulary And Sanitation

The private capability error vocabulary remains closed:

- `transition_read_capability_unavailable`;
- `transition_read_capability_expired`;
- `process_mismatch`;
- `thread_mismatch`.

B3b2b preserves known `_TransitionReadCapabilityError` values unchanged. If
`_borrow_connection_for_select()` raises any other ordinary exception, B3b2b
maps it to
`_TransitionReadCapabilityError(transition_read_capability_unavailable)` only
after the raw exception has left active exception context. The safe error must
retain no raw exception text, capability detail, connection repr, path, process
or thread identity, transaction epoch, credential, proof, proof digest, raw row,
canonical payload, SQL parameter, endpoint, secret, args, cause, context, note,
internal detail, or formatted traceback content. A wrong borrowed object type
uses the same unavailable classification.

This is defensive hardening only. It does not make structural Protocol
conformance authoritative.

## Capability Invalidation

The future nominal capability is invalidated before every commit or rollback
attempt. Invalidation is permanent. A leaked capability must not retain
operation authority, must not prolong private proof or lock custody, must not
borrow after the operation lease exits, and must not become valid after another
transaction starts on the same connection.

No result, event, replay snapshot, report, or public error may retain a
connection, controller, capability, operation lease, transaction epoch, private
credential, proof, proof digest, or authority lock.

## Resolution Precedence

Replay or apply conflict before writes:

- invalidate capability;
- roll back transaction;
- close connection;
- return replay or conflict only if rollback and close resolve safely.

Definite pre-commit error:

- invalidate capability;
- roll back;
- close;
- return the original safe error only if transaction resolution succeeds.

Rollback failure:

- `mutation_failed` supersedes a planned replay, conflict, or other definite
  result;
- no event or result is fabricated.

Commit attempt fails:

- capability was already invalidated;
- return `commit_outcome_unknown`;
- do not claim rollback success;
- no result is fabricated;
- retry requires the same idempotency key.

Commit succeeds and connection close fails:

- committed outcome remains committed;
- close failure is safe diagnostic-only information;
- no successful commit is converted to failure.

Primary execute, evaluate, or write failure plus close failure:

- the primary safe classification wins if rollback already succeeded;
- raw close error is suppressed and sanitized.

Event-ref or event-sequence uniqueness collision after idempotency miss:

- classify as `database_integrity_failure`;
- never regenerate event identity or sequence outside the transaction.

## Identity And Sequence Collision Posture

Transition event identity remains the canonical event-ref digest prefix. The SQL
`event_sequence` is ordering metadata, not event identity, event digest, or
replay digest. If an insert observes an event-ref collision for a different
canonical event, B3c fails safely with `database_integrity_failure`; it does not
regenerate an alternate event ref. If sequence allocation or insertion collides
after an idempotency miss, B3c fails safely with `database_integrity_failure`;
it does not allocate a replacement sequence outside the transaction.

Sequence allocation remains future SQL work. Accepted and domain-rejected events
consume sequence numbers. Replay and apply conflicts do not. Rolled-back
sequence numbers may be reused; committed sequence numbers are never reused.
Signed SQLite maximum overflow remains `event_sequence_exhausted`.

## Later Stages

B3c0b has since implemented pure/static transition-event row, replay,
event-owned idempotency, immutable data-only query specs, and sequence
allocation contracts. It executes no SQL and mutates no state.

B3 fixtures remain future for tests-only coherent managed graphs: managed schema
0001, real internal writer issuance, lease/backlog/current work item,
authorization and optional dependency receipts, global stop, and optional
existing event/replay rows. Fixtures must not become production admission or
authority.

B3c1 remains future for nominal transaction capability and writer fencing only.

B3c2 remains future for event/replay/idempotency/sequence readers.

B3c3 remains future for context assembly and evaluator dry run.

B3c4 remains future for event insertion, accepted-state CAS, rollback, and
commit-uncertainty runtime.

Each future stage requires a separate implementation patch and standalone audit.
