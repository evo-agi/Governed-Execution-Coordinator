# B3b2a Read Capability Protocol And Query Contracts

Status: implemented private capability protocol and immutable query contracts;
no reader execution.

B3b2a is the first implementation slice after B3b1 pure row contracts. It adds
only:

- ordered schema-0001 row-column tuples in `persistence_contracts.py`;
- six immutable parameterized `SELECT` specifications in the private
  `sqlite_transition_read_scope.py` module;
- one private future-B3c transaction capability protocol.

B3b2a does not execute SQL, create cursors, fetch rows, classify row
cardinality, map tuples to private mappings, invoke B3b1 row adapters, classify
missing rows, assemble `TransitionContext`, inspect idempotency or replay state,
allocate event sequences, compare expected versions, mutate work items or global
stop, widen `StateStore`, or create a public read port.

## Ordered Row Columns

The ordered row-column tuples are the single source of row-shape truth for the
six schema-0001 rows used by the future B3b2b readers:

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

Future B3c must create any concrete capability only after B3c has entered the B2
operation guard, executed `BEGIN IMMEDIATE`, and completed writer fencing gates
required by final apply ordering. The concrete B3c capability must bind exactly
one opaque transaction epoch, never change that epoch, invalidate before commit
or rollback, reject use after transaction end, reject use after another
transaction starts on the same connection, reject process/thread mismatch,
expose no connection property, open/close/commit/roll back nothing through the
reader interface, expose no transaction identifier publicly, and raise only safe
closed internal errors.

`connection.in_transaction` is not transaction identity. It proves only that a
connection currently reports an active transaction. It does not prove continuity
with the transaction that created a capability, `BEGIN IMMEDIATE`, writer
fencing, B2 operation-guard ownership, idempotency ordering, expected-version
ordering, or transition-context authority. Transaction-generation and
invalidation proof is deferred to the future B3c implementation and audit.

Future B3b2b readers will accept only the private capability protocol, not raw
connections, database paths, public `StateStore`, `WriterSession`, generic
objects, callables, or connection-returning factories. The documented internal
reader shape is:

```python
_read_current_work_item(
    capability: _TransitionReadCapability,
    work_item_id: str,
) -> WorkItemRecordEnvelope | None
```

Equivalent private readers for lease identity, authorization receipt, dependency
receipt, admitted backlog, and global-stop-current rows follow the same
capability-first shape.

## Future Boundary

B3b2b will implement actual SELECT execution, bounded cardinality, tuple-to-
private-mapping conversion, B3b1 adapter invocation, and safe SELECT error
wrapping against `_TransitionReadCapability`. B3c will own concrete capability
creation, transaction-generation and invalidation semantics, reader ordering,
missing-row classification, cross-record authority binding, lease runtime
derivation, transaction timestamp, `TransitionContext` construction, evaluator
invocation, and mutation outcome.

B3b2a must remain absent from package-root exports, public `StateStore`, CLI,
MCP, connectors, reports, examples, and related repositories.
The public `StateStore` is not widened by B3b2a.
