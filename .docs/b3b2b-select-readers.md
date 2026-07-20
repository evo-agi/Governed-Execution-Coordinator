# B3b2b Private SELECT Readers

Status: private SELECT readers implemented and test-executed; no production
integration. B3c2 has since extracted the shared capability/error/cursor
lifecycle mechanics into `sqlite_transition_select_support.py` for B3b2b and
B3c2.

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
capability and in-memory test tables; the B3 coherent fixture tests also invoke
them over a temporary managed database through a tests-only capability.

## Boundary

B3b2b owns only:

- lookup-ref validation before capability borrowing for work item, decision,
  and backlog refs;
- using the shared private SELECT support to borrow a SQLite connection through
  the private `_TransitionReadCapability` protocol method only;
- executing one immutable explicit-column parameterized `SELECT ... WHERE ... =
  ? LIMIT 2` spec;
- calling `fetchmany(2)`;
- enforcing zero/one/multiple cardinality;
- requiring one exact built-in tuple with the exact configured column count;
- constructing one private plain mapping from the ordered column tuple;
- delegating to the B3b1 single-row adapter for that table;
- safe SQLite SELECT-error classification and cursor cleanup through the shared
  support module.

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

B3c1b now implements the nominal concrete capability only inside its private
rollback-only writer-fencing controller, after the B3c0a shared prefix of B2
operation-lease authority, shared per-session mutation slot, managed read/write
connection open, `BEGIN IMMEDIATE`, managed validation, writer fencing, one
opaque transaction epoch, and invalidation before rollback. Production
integration for B3b2 current/context readers waits for a later B3c slice. The
B3c1b controller calls no B3b2 reader, produces no reader result, and performs
no durable state mutation. B3c2 event readers share only the mechanical SELECT
support and do not call B3b2 readers.

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

SQLite errors from execute and fetch are reduced to `SQLiteMutationStoreError`
with safe closed classes only. Primary result codes for schema/query/database
contradiction, including `SQLITE_ERROR`, `SQLITE_SCHEMA`, `SQLITE_CORRUPT`,
`SQLITE_NOTADB`, `SQLITE_MISMATCH`, and `SQLITE_CONSTRAINT`, map to
`database_integrity_failure`. All other SQLite errors, including closed
connections, busy/locked/I/O/full/interrupted, and missing or unknown codes, map
to `mutation_failed`. If execute and fetch succeeded, cursor-close failure is
not classified through result-code taxonomy; it is always an operational
`mutation_failed` cleanup failure, and semantic row interpretation does not
start.

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

The B3 coherent fixture helpers live under `tests/` only. Their direct seeding
path is test setup, not B3b2b reader integration, production admission,
authorization, concrete capability construction, fencing, context assembly, or
mutation runtime.
