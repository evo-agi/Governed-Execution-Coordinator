# B3b2a Read Capability Protocol And Query Contracts

Status: implemented private capability protocol and immutable query contracts;
private B3b2b SELECT readers now consume these contracts with no production
integration.

B3b2a is the first implementation slice after B3b1 pure row contracts. It adds
only:

- ordered schema-0001 row-column tuples in `persistence_contracts.py`;
- six immutable parameterized `SELECT` specifications in the private
  `sqlite_transition_read_scope.py` module;
- one private future-B3c transaction capability protocol.

B3b2a by itself does not execute SQL, create cursors, fetch rows, classify row
cardinality, map tuples to private mappings, invoke B3b1 row adapters, classify
missing rows, assemble `TransitionContext`, inspect idempotency or replay state,
allocate event sequences, compare expected versions, mutate work items or global
stop, widen `StateStore`, or create a public read port.

B3b2b now implements private readers in the same module. Those readers consume
the B3b2a specs only when explicitly invoked by tests and remain absent from
production call sites.

## Ordered Row Columns

The ordered row-column tuples are the single source of row-shape truth for the
six schema-0001 rows used by the B3b2b readers:

- `LEASE_IDENTITY_RECORD_ROW_COLUMNS`;
- `AUTHORIZATION_RECEIPT_ROW_COLUMNS`;
- `DEPENDENCY_RECEIPT_ROW_COLUMNS`;
- `WORK_ITEM_ROW_COLUMNS`;
- `ADMITTED_BACKLOG_ROW_COLUMNS`;
- `GLOBAL_STOP_CURRENT_ROW_COLUMNS`.

Existing full-row key sets are derived mechanically from these tuples. The
non-timestamp receipt key sets are derived by removing the one operational
`created_at` column. The tuple validation is pure and requires nonempty tuples,
string column names, no duplicates, and only safe lower-case SQL identifier
characters.

## Query Specifications

B3b2a defines exactly six private immutable query specs:

| Query | Table | Lookup column |
| --- | --- | --- |
| current work item | `work_items` | `work_item_id` |
| lease identity | `lease_identity_records` | `decision_ref` |
| authorization receipt | `authorization_decision_receipts` | `decision_ref` |
| dependency receipt | `dependency_decision_receipts` | `decision_ref` |
| admitted backlog | `admitted_backlogs` | `backlog_id` |
| global stop current | `global_stop_current` | `singleton_id` |

Each SQL string is immutable data with this shape:

```sql
SELECT <explicit ordered columns>
FROM <one exact table>
WHERE <one exact lookup column> = ?
LIMIT 2
```

The specs contain no row values, refs, paths, credentials, raw rows, canonical
JSON, private assignment data, idempotency state, replay state, event history, or
report payloads. They do not read `transition_events`, `global_stop_events`,
`schema_migrations`, `writer_ownership`, or operator-decision receipt tables.

## Private Transaction Capability Protocol

`_TransitionReadCapability` is a private protocol only. It is not runtime public
authority, not a concrete scope, and not a production implementation. B3b2a does
not provide a constructor, factory, raw-connection wrapper, transaction epoch
implementation, connection posture probe, or production object that can be
instantiated as transaction-bound read authority.

Future B3c must create any concrete capability only after B3c has acquired the
B2 operation lease, completed mutation-specific local checks, acquired the shared
per-session mutation slot, opened an existing managed read/write connection,
executed `BEGIN IMMEDIATE`, revalidated managed schema/posture inside the
transaction, and completed writer fencing gates required by final apply ordering.
The concrete B3c capability must be nominal, not trusted by Protocol conformance,
bind exactly one opaque transaction epoch, never change that epoch, invalidate
before commit or rollback, reject use after transaction end, reject use after
another transaction starts on the same connection, reject process/thread
mismatch, expose no connection property, open/close/commit/roll back nothing
through the reader interface, expose no transaction identifier publicly, and
raise only safe closed internal errors.

`connection.in_transaction` is not transaction identity. It proves only that a
connection currently reports an active transaction. It does not prove continuity
with the transaction that created a capability, `BEGIN IMMEDIATE`, writer
fencing, B2 operation-guard ownership, idempotency ordering, expected-version
ordering, or transition-context authority. Transaction-generation and
invalidation proof is deferred to the future B3c implementation and audit.

B3b2b readers accept only the private capability protocol, not raw connections,
database paths, public `StateStore`, `WriterSession`, generic objects,
callables, or connection-returning factories. The implemented internal reader
shape is:

```python
_read_current_work_item(
    capability: _TransitionReadCapability,
    work_item_id: str,
) -> WorkItemRecordEnvelope | None
```

Equivalent private readers for lease identity, authorization receipt, dependency
receipt, admitted backlog, and global-stop-current rows follow the same
capability-first shape. `_read_global_stop_current(capability)` binds singleton
integer `1` internally and exposes no caller-selectable singleton id.

## B3b2b Reader Mechanics

B3b2b implements exactly six private readers over the query specs. For work
item, decision, and backlog lookups, the reader validates the safe contract ref
before borrowing the capability or executing SQL. Malformed refs fail locally
without SQLite access and without echoing the rejected value.

All six readers borrow the connection through `_borrow_connection_for_select()`
only. Safe `_TransitionReadCapabilityError` reasons are preserved unchanged. Any
other ordinary exception from the capability borrow is sanitized to
`transition_read_capability_unavailable` after the raw exception has left active
exception context, with no retained raw cause, context, note, capability detail,
connection repr, transaction epoch, path, proof, digest, row, SQL parameter, or
secret. A returned object that is not a `sqlite3.Connection` is rejected as
`transition_read_capability_unavailable`. B3b2b performs no runtime Protocol
checking, process/thread/epoch checks, connection posture mutation, transaction
start/end, connection open, or connection close.

The shared private helper executes `spec.sql` with exactly one bound parameter,
calls `fetchmany(2)`, and always attempts cursor cleanup. It never inspects
`cursor.description`, never mutates `row_factory`, and never returns raw rows,
tuples, mappings, cursors, or connections. One fetched row must be an exact
built-in tuple whose length equals `spec.columns`. The reader builds a private
plain `dict` with `dict(zip(spec.columns, row, strict=True))` and delegates to
the B3b1 adapter for that row shape.

Zero rows return `None` for current work item, lease identity, authorization,
dependency, and admitted backlog. The global-stop current singleton is mandatory
table-local state, so zero rows raise `database_integrity_failure`. Two rows,
including any result set with more rows hidden behind `LIMIT 2` and
`fetchmany(2)`, raise `database_integrity_failure`.

SQLite errors from execute, fetch, and cursor close are classified safely.
Primary result codes for schema/query/database contradiction, including
`SQLITE_ERROR`, `SQLITE_SCHEMA`, `SQLITE_CORRUPT`, `SQLITE_NOTADB`,
`SQLITE_MISMATCH`, and `SQLITE_CONSTRAINT`, map to
`database_integrity_failure`. Every other SQLite error maps to
`mutation_failed`. `commit_outcome_unknown` is never produced by B3b2b. Raw
SQLite messages, SQL text, parameter values, rows, canonical JSON, paths,
connection reprs, transaction epochs, credentials, proofs, digests, and secrets
are not retained in public errors, exception chains, internal detail, or
formatted traceback output.

## Future Boundary

B3c0a now pins the future concrete capability owner, transaction-generation and
invalidation semantics, one-mutation-per-session policy, writer fencing,
current/expected/context ordering, missing-row apply-conflict classification,
cross-record authority binding, transaction timestamp point, rollback/commit/
close precedence, and event-ref/sequence collision posture. Later B3c stages
remain future for implementing reader ordering, lease runtime derivation,
`TransitionContext` construction, evaluator invocation, idempotency/replay,
expected-version checks, event sequencing, and mutation outcome.

B3b2a/B3b2b must remain absent from package-root exports, public `StateStore`,
CLI, MCP, connectors, reports, examples, and related repositories. The public
`StateStore` is not widened by B3b2a or B3b2b.
