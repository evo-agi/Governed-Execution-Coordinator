# B3c2 Transition Event Readers

Status: implemented private transaction-internal SELECT readers;
production-unintegrated; no sequence allocation; no mutation. B3c3 invokes the
idempotency reader from the private rollback-only dry-run runtime. B3c4b now
invokes the maximum-sequence reader only after a fresh accepted or
domain-rejected evaluation inside the private atomic apply path.

B3c2 adds only private readers for already fenced B3c transactions:

```python
def _read_transition_event_for_idempotency(
    capability: _TransitionReadCapability,
    work_item_id: str,
    idempotency_key: str,
) -> TransitionEventRecordEnvelope | None: ...

def _read_transition_event_max_sequence(
    capability: _TransitionReadCapability,
) -> int | None: ...
```

The readers live in `sqlite_transition_event_readers.py`. They are not package
exports, `StateStore` methods, `WriterSession` methods, report inputs, CLI
surfaces, MCP surfaces, connector surfaces, or related-repo APIs. B3c3 calls
only `_read_transition_event_for_idempotency(...)` from the private
rollback-only dry-run transaction after writer fencing and capability creation.

## Shared SELECT Support

`sqlite_transition_select_support.py` owns only mechanical transaction-SELECT
support shared by B3b2b and B3c2:

- `_TransitionReadCapability`;
- `_TransitionReadCapabilityError`;
- `_TransitionReadCapabilityFailureReason`;
- safe capability connection borrowing;
- cursor execute, `fetchmany(2)`, and close lifecycle;
- SQLite SELECT error classification;
- exact tuple-to-private-mapping conversion;
- safe `database_integrity_failure` and `mutation_failed` construction.

It owns no table name, query specification, row-column tuple, missing-row
policy, event/replay policy, idempotency decision, sequence arithmetic, context
assembly, transaction begin/commit/rollback, connection close, or capability
invalidation.

## Idempotency Reader

`_read_transition_event_for_idempotency(...)` first completes a two-field
preflight: `work_item_id` must be an exact built-in `str`, and then
`idempotency_key` must be an exact built-in `str`. Only after both exact-type
gates pass may either field enter the shared `require_contract_ref(...)`
validator. Shared validation then runs in lookup-address order: work item first,
idempotency key second, before borrowing the capability. Subclasses and proxy
values are rejected before truthiness, length, regex, lowercase, equality,
hashing, iteration, indexing, formatting, `str`, `repr`, or SQL can run. This
exact-type gate is local to the private B3c2 lookup-reader boundary; it does not
redefine repo-wide string validation, B3b2 reader inputs, or
`TransitionCommand` construction. The reader then executes exactly the B3c0b
immutable idempotency lookup query spec with exactly those two parameters and
`LIMIT 2`.

Reader results are deliberately narrow:

- zero rows returns `None`;
- one row returns an exact `TransitionEventRecordEnvelope`;
- two rows is `database_integrity_failure`.

The one row must be an exact built-in tuple with length
`TRANSITION_EVENT_ROW_COLUMNS`. The reader builds one private mapping from that
ordered tuple and delegates full event/replay reconstruction and integrity to
`transition_event_record_envelope_from_row(...)`.

After reconstruction, the reader requires the exact
`TransitionEventRecordEnvelope` type and exact nested `TransitionEvent` type
before reading nested fields. It rechecks that the reconstructed event's
`work_item_id` and `idempotency_key` equal the validated lookup address before
returning the envelope. Wrong-address rows are database-integrity failures.

The reader never returns `CommittedTransition`, `TransitionConflict`,
`replayed=True`, `idempotency_key_reuse_conflict`, or any apply outcome. It does
not accept `TransitionCommand` and does not call
`match_transition_event_idempotency(...)`.

B3c3 is the first rollback-only tranche allowed to call this reader and then
call the pure B3c0b matcher at the dry-run boundary. B3c2 still does not decide
exact replay or idempotency-key reuse conflict policy.

## Maximum Sequence Reader

`_read_transition_event_max_sequence(...)` executes exactly the B3c0b immutable
maximum-sequence query spec with no parameters.

The reader requires exactly one returned aggregate row. The row must be an exact
built-in tuple of length one. A `None` aggregate value means no events and
returns `None`.

An observed maximum returns only when the value is an exact built-in `int`, not
`bool`, and `0 <= value <= SQLITE_SIGNED_INT_MAX`. Negative integers, booleans,
floats, text, bytes, objects, additional columns, zero aggregate rows, multiple
aggregate rows, and out-of-range integers are database-integrity failures.

The signed SQLite maximum is a valid observed maximum. Only
`next_transition_event_sequence(maximum)` owns the later
`event_sequence_exhausted` decision. B3c2 does not call that allocator and does
not return a next, reserved, allocated, consumed, or unique sequence.

B3c4b is the first tranche allowed to call this reader, call the pure
allocator, and insert a transition event. That call remains private and
production-unintegrated.

## Capability And Transaction Ownership

Both readers accept only `_TransitionReadCapability`. They do not accept raw
`sqlite3.Connection`, `CoordinatorStateLocation`, filesystem binding,
`WriterSession`, operation lease, mutation lease, controller, or epoch objects.

B3c1b remains the owner of the concrete nominal capability, opaque epoch,
connection, `BEGIN IMMEDIATE`, writer fencing, invalidation, rollback, and
close. The B3c2 readers never begin, commit, roll back, close a connection, or
invalidate a capability.

Tests prove the readers work through the real B3c1b rollback-only controller by
monkeypatching only `_create_sqlite_transition_read_capability` to invoke the
readers while the transaction is active, then returning the real capability to
the controller. The controller still invalidates, rolls back, closes, and
releases normally, and the captured capability is expired after cleanup. The
forked child proof is tests-only and deadline-bounded: result pipe reads are
nonblocking, child status is reaped only through `waitpid(..., WNOHANG)` under
finite monotonic deadlines, timeout cleanup uses bounded terminate and kill
phases, and no unbounded child wait is accepted. The proof always closes owned
pipe ends, reaps children on normal, timeout, abnormal-exit, and cleanup-failure
paths, and observes `process_mismatch` before inherited SQLite connection use.
This proof adds no production helper, callback, authority, or API surface.

## Cursor, Errors, And Privacy

The shared support preserves execute/fetch failure as primary even if cursor
close also fails. A close failure after a successful fetch is always an
operational cleanup failure and maps to `mutation_failed`, regardless of the
SQLite result code or ordinary close exception type. Row/cardinality/adapter
interpretation begins only after successful cursor close.

Schema/query/database contradictions, malformed row shapes, adapter failures,
wrong lookup addresses, and malformed aggregates are
`database_integrity_failure`. Busy, locked, I/O, full, interrupted, readonly,
closed, and unknown operational failures are `mutation_failed`.
`commit_outcome_unknown` is not produced by B3c2.

No raw SQLite exception text, SQL, parameters, rows, canonical event JSON,
replay JSON, digests, paths, connection reprs, capability details, credentials,
proofs, filesystem bindings, or epochs survive in public errors, exception
chains, internal detail, notes, reprs, or formatted tracebacks.

## Boundaries

B3c2 does not call B3b2 context/current readers. It does not load current work
items, compare expected versions, construct `TransitionContext`, invoke
`evaluate_transition`, derive timestamps, generate events, insert events,
update current-state tables, update global stop, commit, or mutate durable
state.

Schema 0001 is sufficient. The unique `(work_item_id, idempotency_key)`
constraint plus `LIMIT 2` gives the intended integrity posture, and global
`event_sequence` remains the v1 ordering domain. B3c2 adds no migration 0002.

B3c3 now implements the rollback-only dry-run ordering: writer fencing precedes
idempotency disclosure, the idempotency reader is called only after a matching
writer and nominal capability exist, the pure matcher is called exactly once
after the reader, exact replay and key-reuse conflict skip
current/context/timestamp/evaluator work, and no maximum-sequence reader,
allocator, write, CAS, or commit belongs to B3c3. B3c4b now consumes the
observed maximum-sequence reader for allocation and durable event insertion on
fresh evaluations only.
B3c4a has since pinned only the pure/static write-side specifications and
contracts that B3c4b uses after this reader returns an observed maximum.
B3c4a itself does not call `_read_transition_event_max_sequence`, does not call
`next_transition_event_sequence`, does not allocate a sequence, and does not
insert or update rows.
