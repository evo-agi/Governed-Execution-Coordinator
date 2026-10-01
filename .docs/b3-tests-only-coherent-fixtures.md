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

The fixture's historical semantic scope and its current physical container are
distinct. The seeded graph retains the existing schema-0001 B3/B4 coding-work
record, transition, replay, fencing, and global-stop meanings. Its temporary
database nevertheless uses the current cumulative application generation `2`
and terminal migration `0004_rw0_c1_durable_evidence`.
Migrations 0002, 0003, and 0004 are therefore required for the current physical
fixture; they do not turn the historical graph into C2B or cognitive-selection
semantics.

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
prerequisites plus B3c1a private authority plumbing do not make the fixture
runtime authority; B3c1b rollback-only mechanics are private test-executed
only; B3c2 event/idempotency/sequence readers are private
transaction-internal tests only; B3c3 rollback-only dry-run runtime remains
private, production-unintegrated, and non-durable; B3c4b private atomic
persistence is test-executed through the same temporary managed graphs and
remains production-unintegrated.

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
writer metadata. Its first acquisition has generation `1` and is closed; the
fixture retains its second acquisition at generation `2`; the next downstream
acquisition is therefore generation `3`. It retains no writer credential, raw
proof, proof digest, lock descriptor, raw SQLite connection, or public
serialization surface.

All nineteen C2B core tables, all nine cognitive proposal-selection tables, and
all twenty-three RW0-C1 tables remain empty after fixture seeding. The fixture
does not populate or consume C2B2, cognitive-selection, or RW0-C1 durable
records and has no C2B
row/value source, reader, or mutation dependency. It does not prove C2B2
row/value, reader, mutation, family replay, or recovery behavior and does not
prove RW0-C1 admission or recovery behavior.

## Readback

Tests read the graph back through the existing private B3b2b SELECT readers
using a clearly tests-only capability shaped for `_MutationReadCapability` over
an active test transaction. This proves the existing row readers can reconstruct
the coherent graph. It does not create production reader integration, a
concrete transaction capability, writer fencing, idempotency apply integration,
context assembly, event insertion, sequence allocation, or mutation runtime.

Corruption helpers remain narrowly tests-only, are named with `for_test`, use
parameterized SQL, and mutate only temporary test databases. Corruption cases
must fail through existing safe row or binding contracts.

## Remaining Work

B3c1a private authority plumbing exists only behind private WriterSession
helpers, and B3c1b rollback-only controller, nominal transaction capability,
and writer fencing remain production-unintegrated. B3c2 now implements private
transaction-internal event/idempotency/sequence readers only. B3c3 now
implements private rollback-only dry-run result, preflight, binding,
timestamp, reader and matcher integration, context assembly execution,
evaluator dry run, and result return. B3c4b now implements private atomic
persistence, accepted-state CAS, sequence allocation, commit, and
commit-uncertainty runtime through the existing controller. B3c4c implements
public transition delegation. B4a defines global-stop receipt/read/write
contracts, B4b implements private atomic global-stop persistence, and B4c
implements guarded public global-stop delegation. Tests-only seeded receipt
evidence proves verification, public delegation, and persistence mechanics
only, not production operator-policy authorization; receipt provisioning
remains outside the B4 apply transaction.

Migrations 0002, 0003, and 0004 are required only as the current generation-2 physical
container for this tests-only fixture. Migration 0001 and the historical B3/B4
semantic graph remain unchanged. The fixture neither populates nor consumes the
nineteen C2B core tables, nine cognitive proposal-selection tables, or
twenty-three RW0-C1 tables and adds no C2B or RW0-C1 runtime authority.

<!-- RW0_C1_CURRENT_STATUS_BEGIN -->
RW0-C1 migration 0004 changes only the fixture's physical current-tip
container. The synthetic B3/B4 graph does not seed, admit, read, replay, or
recover any RW0-C1 family. All twenty-three RW0-C1 tables remain empty, just as
the nineteen C2B and nine cognitive-selection tables remain empty.
<!-- RW0_C1_CURRENT_STATUS_END -->
