# C2B3 Program Initialization

<!-- C2B3A_PLANNING_PROJECTION_BEGIN -->

<!-- C2B3A_PLANNING_NON_AUTHORITY_BEGIN -->
## Non-authority declaration

This file is a planning and implementation-status projection only. It is not
semantic authority. Section 35 of `.docs/c2b-durable-development-state.md` is
the sole C2B3A semantic owner. Planning cannot create, override, widen, narrow,
resolve, or change a structured owner value, and wording here cannot supply
operative semantics when a structured owner value exists.
<!-- C2B3A_PLANNING_NON_AUTHORITY_END -->

<!-- C2B3A_PLANNING_CURRENT_STATUS_BEGIN -->
## Current status

C2B3A remains a target-contract freeze with documentation and direct
documentation-contract tests only. The current repair changes only the owner,
this planning projection, the direct oracle, and the higher-order guard. It is
not an independent audit and does not establish acceptance. Any changed bytes
require a fresh read-only audit.

The implemented database remains application generation 2 at terminal
migration `0002_development_program_and_effect_state`. Program initialization,
private delegation, product mutation, receipt persistence, replay or recovery
runtime, retained-connection cleanup runtime, finalizer runtime, and author-
effect source remain absent.

The structured owner value
`commit_close_outcome_addendum.normative_surface_and_precedence` makes
`commit_close_outcome_addendum` the sole operative authority for COMMIT/close
outcomes, process-control relationships, cleanup states and order, finalizer
and liveness rules, recovery and replay gates, and future C2B3B path scope.
The bounded prose in Section 35 and this projection have no independent
semantic authority.
<!-- C2B3A_PLANNING_CURRENT_STATUS_END -->

<!-- C2B3A_PLANNING_LEGACY_LEDGER_BEGIN -->
## Legacy-ledger projection

Section 35 classifies
`commit_uncertainty_cleanup_gate.close_not_proved.process_control_exception_graph_ledger`
as `historical_runtime_observation`, with `normative=false`,
`operative_for_c2b3b=false`, `portable_contract=false`, and
`preserved_for_original_c2b3a_evidence=true`. Its target semantics are
superseded by `process_control_relational_policy`. No implementation, test
oracle, planning projection, or future prompt may use its observed graph or
traceback values as target requirements.

The operative process-control rule is deliberate-action-only. C2B3 does not
deliberately assign, clear, restore, scrub, sanitize, or manufacture graph or
traceback state; it deliberately creates no primary-to-secondary relation and
does not serialize, persist, log, render, report, or copy raw process control.
Interpreter-managed graph and traceback effects remain permitted, and no exact
resulting graph or traceback shape is promised.
<!-- C2B3A_PLANNING_LEGACY_LEDGER_END -->

<!-- C2B3A_PLANNING_ACTIVE_SCOPE_BEGIN -->
## Active future-scope projection

The preserved 23-expected, 24-maximum, and twenty-fifth-path-stop material is
historical and non-operative. `consumers_may_use` remains false. The only
operative future scope is the structured owner value
`commit_close_outcome_addendum.future_c2b3b_path_scope_status` for
`C2B3B_PRIVATE_ATOMIC_INITIALIZATION`.

Production is exactly six paths:

- `src/ge_nwp_coordinator/_development_program_initialization_contracts.py`
- `src/ge_nwp_coordinator/_sqlite_development_program_initialization.py`
- `src/ge_nwp_coordinator/sqlite_transition_transaction.py`
- `src/ge_nwp_coordinator/sqlite_writer_session.py`
- `src/ge_nwp_coordinator/sqlite_connection.py`
- `src/ge_nwp_coordinator/state_authority_lock.py`

Documentation/status is exactly ten paths:

- `.docs/c2b-durable-development-state.md`
- `.docs/c2b3-program-initialization.md`
- `.docs/c2b2-private-readers.md`
- `.docs/architecture.md`
- `.docs/durable-state-model.md`
- `.docs/sqlite-operations-and-recovery.md`
- `.docs/sqlite-threat-model.md`
- `.docs/writer-session-authority.md`
- `README.md`
- `AGENTS.md`

Required changed tests are exactly eleven paths:

- `tests/test_c2b3_program_initialization_contract.py`
- `tests/test_c2b3_private_atomic_program_initialization.py`
- `tests/test_c2b3_program_initialization_recovery.py`
- `tests/test_c2b3_private_program_initialization_delegation.py`
- `tests/test_c2b2_field_level_contract.py`
- `tests/test_c2b2_development_reader_contracts.py`
- `tests/test_sqlite_b2c_writer_session.py`
- `tests/test_state_authority_lock.py`
- `tests/test_runtime_non_authority.py`
- `tests/test_architecture_contracts.py`
- `tests/test_c2b0_durable_state_contract.py`

The one contingency path is
`tests/test_c2b2_private_development_readers.py`. The exact expected count is
`6 + 10 + 11 = 27`; the exact maximum is 28; a twenty-ninth path is a hard
stop and scope-reassessment condition.

The four newly required paths relative to the historical manifest are
`src/ge_nwp_coordinator/state_authority_lock.py`,
`.docs/writer-session-authority.md`,
`tests/test_state_authority_lock.py`, and
`tests/test_sqlite_b2c_writer_session.py`. This projection authorizes no C2B3B
source or implementation.
<!-- C2B3A_PLANNING_ACTIVE_SCOPE_END -->

<!-- C2B3A_PLANNING_VALIDATION_ACCEPTANCE_BEGIN -->
## Validation, source acceptance, and sequencing

These are process and acceptance gates projected from the project lifecycle;
they do not make this planning file semantic authority.

Future C2B3B tests use private temporary databases only. They never open
operator state, migrate operator state, or inspect operator-state contents.
Project-protocol existence or absence checks remain allowed, but no operator
database open or migration is permitted.

Before C2B3B source is accepted, all of the following separate evidence is
required:

- an accepted fresh independent read-only source-acceptance audit;
- the exact committed C2B3A contract baseline;
- a distinct committed Coordinator repository baseline;
- a refreshed exact Coordinator snapshot, or an explicitly equivalent exact
  strategic baseline, produced after and bound to that committed baseline;
- the committed direct independent oracle;
- the then-current generation-2 schema and accepted C2B2 row and reader
  identities;
- the exact finite 27-expected / 28-maximum / path-29-stop source proposal and
  protected complement;
- no WorkSpec custody, lookup, retrieval, leakage, logging, report transport,
  or traceback retention;
- one-database, one-writer, one-mutation-slot, and one-controller reuse;
- exact replay and recovery proof requirements; and
- zero public, schema, migration, package, authority, route, external-I/O, or
  cross-repository widening.

The committed Coordinator repository baseline and the refreshed exact
Coordinator snapshot or explicitly equivalent exact strategic baseline are
separate evidence items. Neither substitutes for the other, and the fresh
source-acceptance audit does not itself establish that the snapshot was
refreshed.

Acceptance of this planning projection is not acceptance of future source.

Before source mutation begins, C2B3B source implementation requires all of the
following separate evidence:

- an accepted independent audit of the committed C2B3A contract baseline;
- a committed clean Coordinator baseline;
- a refreshed exact Coordinator snapshot or explicitly equivalent exact
  strategic baseline bound to that clean committed baseline;
- an exact C2B3B source implementation prompt;
- fresh opening repository and patch provenance;
- the accepted 27-expected / 28-maximum future path scope and a hard stop if a
  twenty-ninth path is required; and
- the private-test database and operator-state non-access boundaries above.

A dirty four-file working tree is not a source baseline.

C2B3C is the author-effect contract freeze. C2B3D cannot begin before the
C2B3C owner questions are closed. Pending authority evidence remains inert and
is not verification, permission, route eligibility, ES admission, or worker
authorization. C2B4, C2B5, and C2B6 remain separate later tranches. Migration
0003 remains reserved and unimplemented.
<!-- C2B3A_PLANNING_VALIDATION_ACCEPTANCE_END -->

<!-- C2B3A_PLANNING_PRODUCTION_NONIMPLEMENTATION_BEGIN -->
## Production nonimplementation

C2B3A implements or authorizes no production mutation, receipt, private
delegation, recovery resolver, author effect, worker, scheduler, queue,
service, model client, direct-local execution, Execution Substrate invocation,
Bridge integration, schema, migration, package export, public model,
`StateStore` method, or `WriterSession` public-protocol change. C2B3B remains
absent and requires a separately authorized implementation tranche and a fresh
independent read-only audit.
<!-- C2B3A_PLANNING_PRODUCTION_NONIMPLEMENTATION_END -->

<!-- C2B3A_PLANNING_PROJECTION_END -->
