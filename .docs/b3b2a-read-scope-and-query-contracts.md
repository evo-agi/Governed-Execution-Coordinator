# B3b2a Read Capability Protocol And Query Contracts

Status: implemented private capability protocol and immutable query contracts;
private B3b2b SELECT readers now consume these contracts with no production
integration. B3c2 has since moved the shared capability/error/cursor lifecycle
mechanics into `sqlite_transition_select_support.py` for B3b2b and B3c2, while
leaving B3b2 query specs and missing-row policies in
`sqlite_transition_read_scope.py`.

B3b2a is the first implementation slice after B3b1 pure row contracts. It adds
only:

- ordered schema-0001 row-column tuples in `persistence_contracts.py`;
- six immutable parameterized `SELECT` specifications in the private
  `sqlite_transition_read_scope.py` module;
- one private future-B3c transaction capability protocol, now defined in the
  shared private SELECT-support module.

B3b2a by itself does not execute SQL, create cursors, fetch rows, classify row
cardinality, map tuples to private mappings, invoke B3b1 row adapters, classify
missing rows, assemble `TransitionContext`, inspect idempotency or replay state,
allocate event sequences, compare expected versions, mutate work items or global
stop, widen `StateStore`, or create a public read port.

B3b2b now implements private readers in the same module. Those readers consume
the B3b2a specs only when explicitly invoked by tests and remain absent from
production call sites.
B3c1b now implements a private nominal rollback-only transaction capability,
but its controller does not call these B3b2 readers and still performs no
state mutation. B3c2 private event readers share only the mechanical SELECT
support; they do not call B3b2 context/current readers.

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

`_MutationReadCapability` is the private protocol now shared by transition and
global-stop mutation readers. It is not runtime public authority, not a concrete
scope, and not a production implementation. B3b2a did not provide a
constructor, factory, raw-connection wrapper, transaction epoch implementation,
connection posture probe, or production object that can be instantiated as
transaction-bound read authority.

B3c1b creates the concrete capability only after B2 operation-lease authority,
the shared per-session mutation slot, managed read/write connection open,
`BEGIN IMMEDIATE`, managed validation, and writer fencing. Later B3c production
reader integration must continue to preserve those gates. The concrete B3c
capability is nominal, not trusted by Protocol conformance, binds exactly one
opaque transaction epoch, never changes that epoch, invalidates before rollback
in B3c1b and before commit or rollback in future mutation slices, rejects use
after transaction end, rejects use after another transaction starts on the same
connection, rejects process/thread mismatch, exposes no connection property,
opens/closes/commits/rolls back nothing through the reader interface, exposes no
transaction identifier publicly, and raises only safe closed internal errors.

`connection.in_transaction` is not transaction identity. It proves only that a
connection currently reports an active transaction. It does not prove continuity
with the transaction that created a capability, `BEGIN IMMEDIATE`, writer
fencing, B2 operation-guard ownership, idempotency ordering, expected-version
ordering, or transition-context authority. B3c1b supplies the private opaque
epoch and permanent invalidation mechanics; production reader integration and
mutation authority remain future.

B3b2b readers accept only the private capability protocol, not raw connections,
database paths, public `StateStore`, `WriterSession`, generic objects,
callables, or connection-returning factories. The implemented internal reader
shape is:

```python
_read_current_work_item(
    capability: _MutationReadCapability,
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
only. Safe `_MutationReadCapabilityError` reasons are preserved unchanged. Any
other ordinary exception from the capability borrow is sanitized to
`mutation_read_capability_unavailable` after the raw exception has left active
exception context, with no retained raw cause, context, note, capability detail,
connection repr, transaction epoch, path, proof, digest, row, SQL parameter, or
secret. A returned object that is not a `sqlite3.Connection` is rejected as
`mutation_read_capability_unavailable`. B3b2b performs no runtime Protocol
checking, process/thread/epoch checks, connection posture mutation, transaction
start/end, connection open, or connection close.

The shared private support helper executes `spec.sql` with exactly one bound
parameter, calls `fetchmany(2)`, and always attempts cursor cleanup. Execute or
fetch failure remains primary if cleanup also fails. Cleanup failure after a
successful fetch is always an operational `mutation_failed` cleanup result,
regardless of SQLite result code. The helper never inspects `cursor.description`,
never mutates `row_factory`, and never returns raw rows, tuples, mappings,
cursors, or connections. One fetched row must be an exact built-in tuple whose
length equals `spec.columns`. The reader builds a private plain `dict` with
`dict(zip(spec.columns, row, strict=True))` and delegates to the B3b1 adapter for
that row shape.

Zero rows return `None` for current work item, lease identity, authorization,
dependency, and admitted backlog. The global-stop current singleton is mandatory
table-local state, so zero rows raise `database_integrity_failure`. Two rows,
including any result set with more rows hidden behind `LIMIT 2` and
`fetchmany(2)`, raise `database_integrity_failure`.

SQLite errors from execute and fetch are classified safely. Cursor-close errors
after successful fetch are operational cleanup failures only.
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
remain future for implementing current/context reader ordering, lease runtime
derivation, `TransitionContext` construction, evaluator invocation,
idempotency/replay apply outcomes, expected-version checks, event sequencing,
and mutation outcome. B3c2 implements only private event/idempotency and
observed maximum-sequence readers, with no production caller.

B3b2a/B3b2b must remain absent from package-root exports, public `StateStore`,
CLI, MCP, connectors, reports, examples, and related repositories. The public
`StateStore` is not widened by B3b2a or B3b2b.

RW0-D2's private bound-effect transaction is an additional exact SQLite
consumer of the existing nominal read capability and current-global-stop
reader. It adds no B3b2a query specification, connection owner, public read
method, or transition/global-stop mutation behavior.
