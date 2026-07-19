# B3 Tests-Only Coherent Fixtures

Status: implemented tests-only fixture graph; no production admission or runtime
authority.

The B3 coherent fixture tranche, also called the B3b3 coherent-fixture slice,
adds one reusable synthetic graph under `tests/` only:

The fixtures live under `tests/` only.

- `tests/b3_coherent_transition_fixture.py`;
- `tests/test_b3_coherent_transition_fixture.py`.

No fixture module exists under `src/ge_nwp_coordinator`, and no package-root
export is added.

## Scope

The fixture creates a temporary Coordinator state root from a pytest temporary
directory, initializes the managed SQLite database through existing production
`initialize_database(...)`, directly seeds coherent synthetic authoritative rows
inside one test-setup transaction, validates the seeded database, acquires a
real internal SQLite `WriterSession`, and closes that session deterministically
through the fixture context manager.

The tests directly seed synthetic authoritative rows.

Direct seeding is not admission or product mutation. The same boundary in
lowercase is: direct seeding is not admission or product mutation. It is a
tests-only setup path for future B3c1 runtime and later B3c tests and is not
the future B3c transaction path.
It performs no writer fencing, context assembly, evaluator integration,
admission, authorization verification, product state mutation API, worker
behavior, service behavior, or publication behavior.

## Seeded Graph

The canonical synthetic graph contains:

- one valid `StandingLease`;
- one successful `LeaseIdentityValidation`;
- one `FiniteBacklog` with exactly one current work item;
- one current `WorkItemRecord` whose lease, backlog, limits, and zero scalar
  budget posture bind exactly to the lease and backlog;
- one production/default unsupported `AuthorizationDecision`;
- the migration-owned clear `global_stop_current` singleton;
- one `TransitionCommand`;
- an optional READY-only dependency receipt;
- an optional existing domain-rejected transition event and exact replay row.

The fixture uses existing model constructors, canonical JSON, canonical digests,
ordered row-column tuples, and `encode_sqlite_boolean(...)`. Before insertion,
each synthetic row is reconstructed through the existing B3b1/B3c0b row
adapter for that table. The row builder is not a second authority.

## Authority Boundaries

Required fixture truths: real writer issuance is temporary test evidence only;
unsupported authorization remains production/default; optional persisted event
is domain-rejected; no accepted executable transition is proved; B3c1
prerequisites are contract-only and B3c1 runtime plus B3c2-B3c4 remain future.

Unsupported authorization remains production/default:

- `authorization_model == unsupported`;
- `authorized == false`;
- `executable == false`;
- `reason == unsupported_authorization_model`.

The fixture does not seed accepted operator-policy authority, does not seed an
executable authorization receipt, does not treat a valid lease digest as
permission, and does not prove any accepted executable transition.

The optional persisted transition event is domain-rejected. It is produced by
the current pure evaluator from the synthetic authoritative context and then
validated through `transition_event_record_envelope_from_row(...)`. It is not a
fabricated accepted event.

Real writer issuance is temporary test evidence only. The fixture requires safe
writer metadata and generation `1` for a fresh temporary database, but it
retains no writer credential, raw proof, proof digest, lock descriptor, raw
SQLite connection, or public serialization surface.

## Readback

Tests read the graph back through the existing private B3b2b SELECT readers
using a clearly tests-only `_TransitionReadCapability` implementation over an
active test transaction. This proves the existing row readers can reconstruct
the coherent graph. It does not create production reader integration, a
concrete transaction capability, writer fencing, idempotency readers, event
readers, sequence readers, or context assembly.

Corruption helpers remain narrowly tests-only, are named with `for_test`, use
parameterized SQL, and mutate only temporary test databases. Corruption cases
must fail through existing safe row or binding contracts.

## Remaining Work

B3c1 prerequisites are contract-only; B3c1 runtime remains future for the
mutation slot, rollback-only controller, nominal transaction capability, and
writer fencing.
B3c2 remains future for event/idempotency/sequence readers. B3c3 remains
future for context assembly and evaluator dry run. B3c4 remains future for
atomic persistence, accepted-state CAS, rollback, and commit-uncertainty
runtime.

No migration 0002 is required for this tests-only tranche, and migration 0001
remains unchanged.
