# B3b2b Private SELECT Readers

Status: private SELECT readers implemented and test-executed; no production
integration.

B3b2b implements six private functions in `sqlite_transition_read_scope.py`:

- `_read_current_work_item(capability, work_item_id)`;
- `_read_lease_identity_record(capability, decision_ref)`;
- `_read_authorization_receipt(capability, decision_ref)`;
- `_read_dependency_receipt(capability, decision_ref)`;
- `_read_admitted_backlog(capability, backlog_id)`;
- `_read_global_stop_current(capability)`.

These functions are not package-root exports, not public read APIs, not
`StateStore` methods, and not `WriterSession` methods. No production module
calls them. Tests invoke them directly through a clearly test-only structural
capability and in-memory test tables.

## Boundary

B3b2b owns only:

- lookup-ref validation before capability borrowing for work item, decision,
  and backlog refs;
- borrowing a SQLite connection through the private `_TransitionReadCapability`
  protocol method only;
- executing one immutable explicit-column parameterized `SELECT ... WHERE ... =
  ? LIMIT 2` spec;
- calling `fetchmany(2)`;
- enforcing zero/one/multiple cardinality;
- requiring one exact built-in tuple with the exact configured column count;
- constructing one private plain mapping from the ordered column tuple;
- delegating to the B3b1 single-row adapter for that table;
- safe SQLite SELECT-error classification and cursor cleanup.

B3b2b does not implement a production concrete capability, transaction
creation, transaction identity, writer fencing, idempotency lookup, replay,
event sequencing, expected-version checks, cross-record authority assembly,
lease runtime derivation, `TransitionContext` construction, evaluator
invocation, mutation, fixture insertion, admission, authorization verification,
worker/service behavior, or migration 0002.

## Capability

`_TransitionReadCapability` remains structural shape only. Protocol conformance
is not authority. The B3b2b helper calls only
`_borrow_connection_for_select()` and requires the returned object to be a
`sqlite3.Connection`; a wrong returned type fails safely with
`transition_read_capability_unavailable`. Safe capability-expired,
process-mismatch, and thread-mismatch errors raised by a future B3c capability
are preserved unchanged. Any other ordinary exception raised while borrowing is
converted to `transition_read_capability_unavailable` after the raw exception has
left active exception context, so raw exception text, capability details, notes,
causes, contexts, and traceback content do not survive on the safe error.

Production integration waits for B3c to implement and audit a nominal concrete
capability that follows the B3c0a shared prefix: B2 operation-lease acquisition,
mutation-specific local checks, shared per-session mutation slot, managed
read/write connection open, `BEGIN IMMEDIATE`, managed validation, writer
fencing, one opaque transaction epoch, invalidation before commit or rollback,
and permanent rejection after transaction end or restart.

## Missing Rows

Reader-layer missing-row behavior is deliberately narrow:

- current work-item absence returns `None`; future B3c owns
  `work_item_not_found`;
- lease identity absence returns `None`; future B3c owns `validation_failed`;
- authorization absence returns `None`; future B3c owns `validation_failed`;
- dependency absence returns `None`; future B3c owns `validation_failed`;
- admitted backlog absence returns `None`; future B3c classifies
  `database_integrity_failure` after current-state binding;
- `global_stop_current` absence raises `database_integrity_failure` directly
  because the singleton is mandatory table-local state.

No reader constructs `TransitionConflict`, `TransitionEvent`,
`TransitionContext`, or report projections.

## SQLite Errors

SQLite errors from execute, fetch, and cursor close are reduced to
`SQLiteMutationStoreError` with safe closed classes only. Primary result codes
for schema/query/database contradiction, including `SQLITE_ERROR`,
`SQLITE_SCHEMA`, `SQLITE_CORRUPT`, `SQLITE_NOTADB`, `SQLITE_MISMATCH`, and
`SQLITE_CONSTRAINT`, map to `database_integrity_failure`. All other SQLite
errors, including closed connections, busy/locked/I/O/full/interrupted, and
missing or unknown codes, map to `mutation_failed`.

`commit_outcome_unknown` is never produced by B3b2b. Raw SQLite exception text,
SQL, parameters, rows, canonical JSON, paths, connection reprs, transaction
epochs, credentials, proofs, digests, and secrets are not retained in public
errors, exception chains, internal detail, or formatted traceback output.

## Tests

`tests/test_b3b2b_select_readers.py` uses only in-memory test tables and a
tests-only capability. The tests verify validation-before-borrow,
parameterized lookup binding, `fetchmany(2)`, tuple-to-mapping strictness,
adapter delegation, global-stop singleton binding, safe capability failures,
safe SQLite error taxonomy, cursor cleanup, connection non-ownership, missing
row behavior, and production unreachability.

The tests-only capability does not prove production transaction authority and
must not be imported by production source.
