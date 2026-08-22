# C2B3 Program Initialization

Status: planning and implementation-status record for the C2B3A contract
freeze. This document is not semantic authority. The sole semantic owner is
Section 35 of `.docs/c2b-durable-development-state.md`; when wording here and
that owner differ, the owner controls and the difference is a contract defect.

## Status

C2B3A freezes the program-initialization target contract and selected
owner-level seams needed by later author-effect work. It adds documentation and
direct documentation-contract tests only. Program-initialization source,
private delegation, product mutation, receipt persistence, production reader
integration, exact replay runtime, commit-outcome recovery runtime, and the
complete author-effect contract/source are absent.

The implemented database remains application generation 2 at terminal
migration `0002_development_program_and_effect_state`. C2B3A adds no schema,
migration, row, public API, package export, dependency, service, process,
route, worker, model, Bridge, or Execution Substrate behavior. The frozen
single-initial-work shape is a bounded first slice, not a permanent program
architecture.

Audit repairs are recorded only by pointers into the Section 35 owner literal and
its adjacent direct golden-vector literal:

- `row_and_head_ledger.postimages.initialize_decision` owns the null selected
  tuple and wholly present preassigned attempt/candidate tuple;

- `initialization_golden_vector` and the
  `C2B3_PROGRAM_INITIALIZATION_GOLDEN_VECTOR_PYTHON` marker own the complete
  single-work synthetic vector;

- `commit_uncertainty_cleanup_gate` owns connection custody, close-complete
  admission, the original apply error, quarantine refusal, and the exact
  `KeyboardInterrupt` / `SystemExit` / `GeneratorExit` close-interruption
  publication order;

- `genesis_cardinality.preassigned_attempt_candidate_binding` owns the exact
  four-field caller-preassigned lineage relation while the selected tuple
  remains wholly null;

- `future_c2b3b_maximum_path_scope` owns the exact future twenty-four-path
  maximum and the five production responsibility ledgers;

- `private_outcome_ownership` and
  `commit_outcome_recovery.disposition_owner` own the future private conflict
  and recovery values; and

- `complete_graph_locator` owns the bounded four-ref physical lookup followed
  by exact returned, command, and graph `work_spec_ref` equality.

These pointers do not duplicate or co-own semantic truth. Program
initialization remains unimplemented, private delegation remains absent,
receipt persistence remains absent, and replay and recovery runtimes remain
absent.

## Planned C2B3B Source Layout

The exact future tranche name is
`C2B3B_PRIVATE_ATOMIC_INITIALIZATION`. Its implementation-path manifest is a
maximum of twenty-four paths. This manifest does not authorize any C2B3B source
or implementation in the current C2B3A repair. A twenty-fifth path is a future
implementation stop condition.

Production is exactly five paths:

- `src/ge_nwp_coordinator/_development_program_initialization_contracts.py`

  Owns private pure command, projection, result, conflict, recovery, graph,
  and quarantine-admission values. It performs no SQLite, no I/O, and has no
  package export. It owns no process-control result or enum and no
  ordinary-value representation of `KeyboardInterrupt`, `SystemExit`, or
  `GeneratorExit`.

- `src/ge_nwp_coordinator/_sqlite_development_program_initialization.py`

  Owns the sensitive same-call reducer, safe initialization command
  construction, exact replay, fresh apply, family-specific graph location and
  verification, and explicit recovery resolver. It has no public API and
  performs no external I/O. After transaction cleanup returns a named
  process-control exception for propagation, this module does not catch,
  translate, wrap, or retry it.

- `src/ge_nwp_coordinator/sqlite_transition_transaction.py`

  Preserves one-commit-attempt ownership; retains the uncertain connection and
  mutation slot after a commit exception; attempts close before custody clear;
  transfers a retained connection into the session resource when close is
  unproved; never unconditionally releases the slot after commit uncertainty;
  preserves a fresh content-free `commit_outcome_unknown`; and admits no
  semantic retry. It owns the narrow close-interruption catch point, recognizes
  exactly `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`, retains
  connection, mutation-slot, and writer-lock custody, reduces and detaches the
  ordinary commit failure before close-time process-control handling, catches
  those exact branches from close, requests session-resource quarantine
  publication, waits for publication completion, and performs a bare re-raise
  in the same catch suite only after completion. It adds no traceback frame
  beyond bare-reraise semantics and no cause, context, note, or other
  exception-graph material, and it does not execute unconditional slot release
  in that branch.

- `src/ge_nwp_coordinator/sqlite_writer_session.py`

  Owns private program-initialization delegation only,
  `_WriterSessionResource` retained-connection custody, commit-uncertain
  quarantine state, writer-lock and mutation-slot retention, rejection of new
  operations while quarantined, close/finalization-only admission while
  quarantined, and quarantine release only after proved closure and session
  disposal. It acknowledges quarantine publication before the transaction
  layer bare-reraises a process-control exception. Publication acknowledgement
  must not raise or attach an ordinary exception, and publication helpers have
  no authority to propagate or replace the caught exception. It makes no
  public `WriterSession` protocol change.

- `src/ge_nwp_coordinator/sqlite_connection.py`

  Owns one private C2B3B-only connection posture, or an equivalent explicit
  mechanism, permitting proved cross-thread closure from session-resource
  finalization. It permits no cross-thread SQL, exposes no public raw
  connection, widens no public signature, creates no second connection
  authority, and preserves existing ordinary connection behavior. It may
  surface the exact close-time `KeyboardInterrupt`, `SystemExit`, or
  `GeneratorExit`, but owns only this bounded private finalization posture.

Documentation/status is exactly nine paths:

- `.docs/c2b-durable-development-state.md`
- `.docs/c2b3-program-initialization.md`
- `.docs/c2b2-private-readers.md`
- `.docs/architecture.md`
- `.docs/durable-state-model.md`
- `.docs/sqlite-operations-and-recovery.md`
- `.docs/sqlite-threat-model.md`
- `README.md`
- `AGENTS.md`

Tests are exactly ten paths:

- `tests/test_c2b3_program_initialization_contract.py`
- `tests/test_c2b3_private_atomic_program_initialization.py`
- `tests/test_c2b3_program_initialization_recovery.py`
- `tests/test_c2b3_private_program_initialization_delegation.py`
- `tests/test_c2b2_field_level_contract.py`
- `tests/test_c2b2_private_development_readers.py`
- `tests/test_c2b2_development_reader_contracts.py`
- `tests/test_runtime_non_authority.py`
- `tests/test_architecture_contracts.py`
- `tests/test_c2b0_durable_state_contract.py`

The exact counts are five production, nine documentation/status, ten tests,
and twenty-four total. C2B3B forbids `pyproject.toml`, package `__init__.py`,
`state_store.py`, `sqlite_errors.py`, public values in `models.py`,
`sqlite_mutation_transaction_contracts.py`, migration SQL or catalog, schemas,
C2B4-C2B6 implementation, and another repository.

## Private Delegation Shape

Any later C2B3B implementation must reuse the existing concrete SQLite writer
session, operation guard/lease, shared mutation slot, resource-bound transaction
controller, writer fence, and nominal read capability. It must not create a
second database, lock, writer authority, mutation slot, controller, generic
dispatcher, or transaction abstraction.

The sensitive reducer must complete before the transaction controller is
entered. Only the owner-defined safe command may cross that boundary. Receipt
lookup follows successful fencing and precedes fresh-path stop or collision
disclosure. Fresh evaluation may build one immutable family plan, use one
transaction timestamp, and attempt commit at most once. External I/O remains
outside the transaction and outside this family.

The explicit recovery resolver is a distinct later call. It is admitted only
after the uncertain connection is proved closed and the prior writer lock is
proved released. A close-not-proved session remains quarantined with the raw
connection owned by its private session resource, its mutation slot
unavailable, and its resolver disposition `unresolved` before any operation
lease, database open, `BEGIN`, or SQL. Only a newly acquired concrete session
may later acquire a fresh operation lease and the existing shared slot, enter a
new readback-only transaction through the same controller class, fence the
writer, classify the owner-defined evidence, then roll back and close. The
resolver receives no complete WorkSpec and never automatically retries the
semantic mutation.

The exact process-control close-interruption branches are
`KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`, in that order. After
commit uncertainty has begun, each branch must preserve the identical
exception object and exact type and arguments (including `SystemExit.code`),
retain the mutation slot and writer-authority lock, transfer connection custody
and publish quarantine before propagation, and prohibit same-session mutation,
database-backed recovery, operation-lease acquisition, database open, `BEGIN`,
SQL, and automatic semantic retry. Only after those facts are published may
the identical exception propagate. It is not converted to an ordinary
`SQLiteMutationStoreError`, `commit_outcome_unknown`, `mutation_failed`, or a
private `unresolved` result.

Propagation is a bare `raise` in the same catch suite. The caught traceback
object remains the exact terminal tail, its frame-code identity and frame-name
sequence are preserved, and the repair adds zero propagation frames. Named
raise, `raise ... from ...`, explicit traceback replacement, reconstructed
exceptions, helper propagation, and later named propagation are forbidden.
The ordinary commit failure must be detached before close handling so cause
and context remain null, `__suppress_context__` remains false, and notes remain
absent before and after propagation for every branch. The separate exact
eighteen-field exception-graph ledger is closed-world and leaves the accepted
twelve-fact branch matrix unchanged.

No public or persisted value, log, or report may carry the raw connection,
cursor, transaction controller, mutation-slot object, writer-lock object,
quarantine object, ordinary commit exception, close implementation details,
SQLite path, SQL or parameters, or WorkSpec material or representations of
those objects. The process-control exception itself may propagate unchanged;
it is not a public process-control value or a durable result.
No private material may appear in its args, string or representation forms,
cause/context graph, notes, formatted traceback, C2B3-owned traceback-frame
locals, returned or persisted values, logs, or reports. The identical
process-control exception is the sole permitted outward exception object.

## Validation Plan

A later source tranche must, at minimum, add independent private tests for:

- exact built-in sensitive-ingress validation and privacy-safe reduction;

- safe projection and command canonical identity;

- transaction ordering, fencing, stop precedence, and collision
  classification;

- the exact genesis row plan and continuously enabled foreign keys;

- graph completeness, historical head postimages, and exact replay;

- commit success, pre-commit rollback, commit-attempt uncertainty, and all
  three recovery dispositions;

- operation-lease, mutation-slot, capability-epoch, cleanup, fork, and
  traceback privacy boundaries;

- nonintegration with public APIs, package exports, schemas, routes, workers,
  Bridge, and Execution Substrate.

Tests must use private temporary databases only. They must not open, migrate,
or inspect operator state.

## Audit Plan

Before C2B3B source is accepted, an independent read-only audit must verify:

- the committed C2B3A owner literal and direct independent oracle;

- the exact repository snapshot and clean opening provenance;

- the then-current generation-2 schema and accepted C2B2 row/reader identities;

- a finite production path proposal and protected complement;

- no WorkSpec custody, retrieval, leakage, or traceback retention;

- one-database/one-writer/one-slot/one-controller reuse;

- exact replay and recovery proof requirements;

- zero public, schema, migration, authority, route, or external-I/O widening.

Acceptance of this planning record is not acceptance of future source.

## Non-Goals

C2B3A does not implement or authorize:

- a program-initialization mutation or receipt;

- a C2B reader production caller or generic family graph engine;

- private WorkSpec custody, lookup, restart-safe retrieval, logging, or report
  transport;

- author-effect establishment, authority verification, dispatch eligibility,
  delivery, observation, validation, review, cancellation, repair, or Git
  effects;

- a public `StateStore` or `WriterSession` surface, package export, API, CLI,
  service, IPC, scheduler, queue, reconciler, worker, or model client;

- direct-local execution, Execution Substrate invocation, Bridge integration,
  schema change, migration 0003, or C2B4-C2B6 behavior.

## Remaining Later Boundaries

C2B3B remains the possible private atomic initialization implementation
tranche. It requires an independent audit, committed snapshot, exact source
prompt, and fresh provenance.

C2B3C remains the author-effect contract freeze. It must close the owner-listed
typed requirement-evidence, author-command, fence-ingress, row/graph, golden
vector, replay, recovery, and privacy questions before source work.

C2B3D remains the possible private atomic author-effect implementation tranche.
It cannot begin from the owner decisions alone. Pending authority evidence must
remain inert and must not become verification, permission, route eligibility,
ES admission, or worker authorization.

C2B4, C2B5, and C2B6 remain separate later tranches. Migration 0003 remains
reserved and unimplemented.

## References

- `.docs/c2b-durable-development-state.md`, Section 35: sole C2B3A semantic
  owner.

- `.docs/c2b-durable-development-state.md`, Sections 29–34: accepted C2B2
  physical/value/reader prerequisites and their remaining nonimplementation.

- `.docs/c2a-first-slice-semantic-protocol-contract.md`: semantic identity and
  effect-boundary authority.

- `.docs/c2a1-pure-semantic-values.md`: current pure semantic-value behavior.

- `.docs/sqlite-operations-and-recovery.md` and
  `.docs/sqlite-threat-model.md`: current SQLite operational and threat-model
  authority.

- `.docs/authority-boundaries.md` and
  `.docs/worker-execution-boundary.md`: component and execution authority
  boundaries.
