# NWP Coordinator

Current repository name: Governed Execution Coordinator.

This operational repository name is provisional and may change without changing
schema, authority, or durable identifiers. The canonical component name is
NWP Coordinator.

Current status: this repository owns bounded internal durable SQLite mutation
authority for coding-work state. It has internal durable writer issuance,
writer-fenced transition and global-stop apply, guarded public delegation,
verification of already-persisted operator-decision receipts, idempotency, CAS,
exact replay, one COMMIT attempt, commit uncertainty, and explicit retry. It is
not a service, API, worker, scheduler, queue consumer, provisioner, lease issuer,
authorization issuer, CP workflow, ES runtime, publication system, or general
orchestrator.

Strategic target direction is recorded separately from current behavior. The
accepted C1 staged target is model-guided Coordinator durable progression,
followed by a transport-neutral Worker Execution Boundary, a bounded
direct-local bootstrap/proof route to a process-separated worker, an exact
immutable candidate capsule, validation and independent/model review,
Coordinator semantic decision, and at most one separately selected local
feature-branch commit. Later, the same worker artifact and versioned
command/observation/fence/capsule contracts route through Execution Substrate,
which retains admission and runtime lifecycle authority. Bridge is not the
worker owner.

The authoritative composition record is
`.docs/autonomous-software-development-operating-model.md`; specialized detail
remains in `.docs/authority-boundaries.md`,
`.docs/software-development-progression-boundary.md`,
`.docs/worker-execution-boundary.md`, `.docs/durable-state-model.md`, and
`.docs/c2a1-pure-semantic-values.md`.
C1 uses the classifications `CURRENT IMPLEMENTED CONTRACT`, `CURRENT
COMPATIBILITY EDGE`, `ACCEPTED STRATEGIC TARGET`, `FUTURE IMPLEMENTATION
DETAIL`, `DEFERRED OR BLOCKED EFFECT`, and `PROCESS-ONLY GOVERNANCE`.

C1 adds documentation and contract tests only. It adds no worker, supervisor,
runtime, schema, migration, dependency, package export, entry point, script,
model integration, capsule builder or store, ES integration, Git effect,
publication behavior, subordinate-authorization runtime, or autonomous loop.

C2A freezes the accepted first-slice semantic protocol in
`.docs/c2a-first-slice-semantic-protocol-contract.md`. C2A1 implements only one
internal standard-library pure no-I/O semantic-value module and the six named
pure coherence validators described in `.docs/c2a1-pure-semantic-values.md`.
It adds no package-root export, dependency, durable state, authorization
verification, ingest, worker launch, capsule custody, real Codex invocation,
Git effect, direct-local adapter behavior, or ES routing.

Tranche history: A2-P1/P1.1 established the original local coding-work
coordinator skeleton. Later B-tranches added the bounded SQLite authority
described above. The historical sequence includes:

- standing lease identity parsing, deterministic canonicalization, and digest
  validation for `governed-execution.nwp-standing-lease.v1`;
- closed-world v1 input parsing that rejects unknown and duplicate fields
  before canonicalization;
- a fail-closed unsupported authorization provider;
- finite backlog parsing and canonical identity;
- a pure work-item state transition evaluator that emits accepted or
  domain-rejected transition events;
- a P1.1 command/event/apply-conflict state-store protocol with no production
  backend;
- operator-owned global-stop command/event models and enforcement checks;
- closed, typed, non-authoritative report projections;
- explicit operator-local SQLite database bootstrap, observational database
  inspection/validation, connection posture, migration catalog,
  migration-history/catalog equality, live-schema manifest verification, and
  schema compatibility checks;
- a B2a writer-session authority contract that replaces reconstructable public
  token-shaped mutation authority with an opaque future `WriterSession`
  protocol and safe non-authoritative writer metadata;
- a B2b common state-authority advisory lock, used by SQLite initialize and
  migrate administration for live-process exclusion only;
- B2c durable writer issuance and internal SQLite `WriterSession` acquisition,
  with private in-memory proof material and no mutation storage;
- B3a canonical persistence and provenance contracts for future work-item
  transition persistence, with no SQLite transition mutation runtime;
- B3b prerequisite authority contracts for future typed SQLite readers, pinning
  admitted-backlog binding, exact lease-copied attempt/repair limits,
  zero-only scalar persisted budget fields, READY-only dependency receipts,
  internal timestamp-envelope posture, and schema-0001 sufficiency for the
  bounded reader slice, with no reader implementation in that tranche.
- B3b1 pure internal full-row contracts that wrap already-fetched
  schema-0001 row mappings in operational timestamp envelopes for lease
  identity, authorization, dependency, work-item, admitted-backlog, and
  global-stop-current rows, with no SQLite I/O or reader implementation.
- B3b2a private transaction-capability protocol and immutable SELECT contract
  data:
  ordered row-column tuples, six explicit-column parameterized query specs, and
  private capability-first reader contracts for B3c-managed active
  transactions, with no concrete transaction authority, SQL execution, row
  reconstruction, cardinality, missing-row classification, public read port,
  fixture insertion, or mutation behavior.
- B3b2b private SELECT readers over those specs, test-executed only through a
  tests-only capability and in-memory tables, with lookup validation,
  parameterized `SELECT ... LIMIT 2`, `fetchmany(2)`, strict tuple-to-private
  mapping conversion, B3b1 adapter delegation, safe SQLite SELECT-error
  classification, capability-exception sanitation, and cursor cleanup, but no
  production caller, concrete transaction capability, public read API, fixture
  program, context assembly, admission, authorization implementation, or
  mutation behavior.
- B3c0a contract/static prerequisite closure for the future transition mutation
  authority boundary, pinning nominal capability ownership, operation-guard and
  credential boundaries, one-mutation-per-session policy, writer-fencing
  classifications, exact apply order, context ordering, timestamp point,
  capability invalidation, transaction-resolution precedence, and collision
  posture, with no concrete capability, controller, fencing SELECT,
  idempotency/replay reader, context assembler, evaluator integration, fixture,
  transition mutation, global-stop mutation, or migration 0002.
- B3c0b pure/static transition-event row, replay, event-owned idempotency, and
  sequence contracts: exact ordered schema-0001 `transition_events` columns,
  internal event/replay envelope reconstruction, canonical JSON/digest/index
  equality checks, created-at/runtime equality, zero-budget bounded-slice
  enforcement, pure idempotency matching, immutable data-only idempotency and
  maximum-sequence query specs, and pure sequence allocation tests, with no
  SQLite execution, reader, fixture, transaction capability, fencing, context
  assembly, evaluator integration, mutation runtime, admission, authorization
  implementation, or migration 0002.
- B3c1 prerequisite/private plumbing for the production-unintegrated/test-executed
  rollback-only posture: one private controller construction path,
  resource-owned mutation slot and mutation-lease identity, operation-lease
  authority, resource-owned state-database filesystem binding, durable-issuance
  verification interfaces, writer-row query and parser ownership,
  writer-fencing taxonomy, nominal capability epoch rules, cleanup precedence,
  and B3c1a/B3c1b split. B3c1a implements only the private slot, lease,
  authority checks, resource-owned bound-database accessor, durable-issuance
  verification, atomic mutation-slot publication plus lease-construction
  unwind, and `_WriterIssuanceMatch`, with no controller, concrete capability,
  query execution, B3b2 reader integration, context assembly, evaluator
  invocation, event/state mutation, public mutation-method behavior change, or
  migration 0002. B3c1b implements only the private operation-lease-only
  rollback-only controller, one fresh managed read/write connection to the
  WriterSession resource-owned root/lock/database binding, `BEGIN IMMEDIATE`,
  post-begin binding revalidation, managed validation, bounded writer-row
  `SELECT`, parser reuse, writer fencing, one
  nominal capability with one opaque epoch, permanent invalidation, rollback,
  close, and private `_WriterIssuanceMatch` return. A matching writer row in
  another database is not authority; replaced root/lock/database paths and
  hard-linked active database aliases fail closed. It has no B3b2 reader call,
  event/idempotency/sequence reader, context assembly, evaluator invocation,
  durable state mutation, public caller, commit, or migration 0002.
- B3c2 private transaction-internal transition-event readers, with a tiny
  shared private SELECT lifecycle support module used by B3b2b and B3c2. B3c2
  adds `_read_transition_event_for_idempotency(capability, work_item_id,
  idempotency_key)` and `_read_transition_event_max_sequence(capability)`.
  These readers accept only the private transaction read capability, require
  exact built-in `str` idempotency lookup inputs before contract-ref validation
  or capability borrow, reuse the immutable B3c0b event query specs, delegate
  event/replay row integrity to the B3c0b adapter, return only `None`/hidden
  event envelopes or `None`/observed non-negative integer maximums, and remain
  production-unintegrated. Shared cursor cleanup preserves execute/fetch failure
  as primary, while close failure after successful fetch is always operational
  `mutation_failed`. Real-capability fork tests are deadline-bounded and always
  reap children. They add no matcher or allocator production call, no apply
  result, no public API, no B3b2 context-reader crossing, no durable mutation, no
  commit, and no migration 0002.
- B3c3 contracts, documented in `.docs/b3c3-prerequisite-contract.md`, and the
  runtime documented in `.docs/b3c3-rollback-only-transition-dry-run.md`, add
  only a private rollback-only transition dry run through the existing B3c1
  controller and nominal capability path. B3c3 owns command-local preflight,
  stale-writer conversion, B3c2 idempotency read, pure matcher invocation,
  current work-item read, expected-version comparison, B3b2 context-reader
  ordering, pure cross-record authority binding, one private UTC timestamp,
  lease-runtime derivation, `TransitionContext` construction, exactly one pure
  evaluator call, private non-durable result selection, and cleanup/result
  precedence. It adds no maximum-sequence read, sequence allocation, event
  insert, current-state/global-stop update, CAS, durable write, public
  API/export, `StateStore` widening, commit, or migration 0002. Fresh evaluator
  output is non-durable and non-receipt in B3c3; B3c4b is the first private
  tranche that can persist and commit it through the atomic path.
- B3c4a contracts, documented in
  `.docs/b3c4a-transition-write-and-commit-contracts.md`, add only private
  pure/static write specifications and commit-resolution contracts for durable
  transition persistence. B3c4a freezes the exact
  `transition_events` insert SQL, accepted `work_items` CAS SQL, event and CAS
  value builders, private write plan, the then-transition-owned
  commit-resolution state vocabulary later neutralized by B4b,
  SQLite classification matrix, retry-after-uncertainty contract, B3c4b proof
  matrix, and B3c4c public-integration boundary. It imports no SQLite runtime,
  executes no SQL, inserts no event, updates no work item, reads or allocates no
  sequence, integrates no controller, changes no public WriterSession behavior,
  adds no package export, and requires no schema-ID bump or migration 0002.
- B3c4b private atomic transition persistence, documented in
  `.docs/b3c4b-private-atomic-transition-persistence.md`, consumes those
  frozen B3c4a contracts through the existing single mutation transaction controller
  and nominal-capability path. B3c4b remains the sole atomic transaction owner.
  Fresh accepted or domain-rejected evaluations read the observed maximum
  transition-event sequence, allocate the next sequence, insert one transition
  event, update the current work item only by accepted CAS, invalidate the
  capability before one commit attempt, and return committed results only after
  successful commit and cleanup. Commit-attempt exceptions collapse to
  `commit_outcome_unknown`; caller retry is by the same idempotency key and
  digest. It adds no public global-stop mutation, public export, `StateStore`
  widening, schema-ID bump, or migration 0002.
- B3c4c public transition delegation, documented in
  `.docs/b3c4c-public-transition-delegation.md` and
  `.docs/b3c4c-prerequisite-contract.md`, adds only the public command-local
  transition-apply preflight vocabulary and make public `apply_transition()`
  delegate through the existing operation guard to the B3c4b atomic entry.
  The public wrapper uses a bounded function-local import, maps only the two
  exact private preflight reasons, performs no SQL or transaction work itself,
  and has no generic delegate catch-all.
- B4a global-stop prerequisite contracts, documented in
  `.docs/b4a-global-stop-prerequisite-contracts.md`, add only public
  global-stop preflight vocabulary, private no-I/O command and typed-decision
  reconstruction, persisted receipt and event/replay row contracts, private
  transaction-internal readers, table-local sequence allocation,
  receipt-binding taxonomy, and pure/static write grammar for global-stop
  persistence. B4a does not provision operator-decision
  receipts, execute global-stop mutation SQL, begin or commit a transaction,
  change transition apply, widen StateStore/outcome types, or require schema-ID
  bump or migration 0002.
- B4b private atomic global-stop persistence, documented in
  `.docs/b4b-private-atomic-global-stop-persistence.md`, uses the same neutral
  mutation controller, read capability, mutation slot, bound-open path, and
  commit-resolution graph as transition persistence. It verifies only
  already-persisted operator-decision receipts, persists accepted or
  domain-rejected events atomically, updates the singleton only by accepted CAS,
  and preserves commit uncertainty and explicit retry semantics.
- B4c public global-stop delegation, documented in
  `.docs/b4c-public-global-stop-delegation.md`, makes public
  `apply_global_stop_update()` a guarded adapter to the B4b atomic entry. The
  public wrapper enters the existing operation guard, performs bounded
  function-local imports, maps only the two exact private global-stop preflight
  reasons, classifies malformed private state as database integrity failure,
  maps pre-delegate import/load failure to mutation failure, and has no generic
  delegate catch-all. It adds no receipt provisioning, SQL, transaction
  ownership, `StateStore` widening, schema-ID bump, migration 0002, worker,
  service, scheduler, publication, or cross-repository authority.
- a B3 tests-only coherent fixture graph under `tests/` that initializes a
  temporary current-generation-2 database at terminal migration 0002 while
  directly seeding only the historical schema-0001 B3/B4 graph. All nineteen
  C2B tables remain empty. The exact physical-versus-semantic and writer
  lifecycle contract is owned by `.docs/b3-tests-only-coherent-fixtures.md`;
  the fixture adds no production module, admission, authorization verifier,
  C2B row/value source, reader, mutation, replay, or runtime authority.

P1.1 models expected-version mismatch, stale writer sessions, idempotency key
reuse, and authoritative not-found cases as apply conflicts with no event.
Domain rejections, such as invalid predecessors, global stop, budget failure,
missing evidence, and invariant P1 `stage_not_enabled`, commit exactly one
event. The event is the receipt.
For valid bound commands targeting P1-disabled worker, repair, or local-commit
states, `stage_not_enabled` precedes contextual domain reasons while the event
still retains complete runtime provenance.

Historical P1/B1 did not execute workers, invoke Bridge or Codex, start a
scheduler, run a daemon, consume a queue, create worktrees, implement
`StateStore` mutations, acquire a Coordinator writer, authorize executable work,
run validation sandboxes, repair, commit, publish, push, open pull requests, or
contact live product routes.

The P1 runtime has no supported policy, configuration, callback, or environment
path that enables future worker, repair, or local-commit stages.

B0 selected SQLite, one private local database, as the future first production
state backend architecture. B1/B1.1 implemented secure local database bootstrap
and non-mutating inspection/validation. C2B1 now implements the bounded
administrative migration framework: exact-current ordinary open, explicit
supported-prefix migration, terminal-only compatibility, cumulative
packaged-SQL schema derivation, complete-catalog initialization, whole-suffix
one-transaction migration, and three-way commit-uncertainty readback under the
retained common lock. B2a corrects the writer-session contract, and
B2b adds the shared state-authority advisory lock plus initialize/migrate
integration. B2b uses explicit close/context-manager release with a
finalizer-backed cleanup fallback for abandoned lock objects; finalization is
not a timing guarantee. Lock descriptor publication and parent-side cleanup are
serialized by one lifecycle/fork gate; the fork child handler uses the frozen
descriptor snapshot, closes inherited descriptors without `LOCK_UN`, and does
not acquire inherited Python locks. Lock possession alone is not writer
authority.

B2c acquires an internal SQLite writer session only for an existing managed
database. It increments the durable writer generation, stores only a proof
digest in `writer_ownership`, closes the acquisition connection before return,
and retains the common lock for the session lifetime. B2 hardening rejects
present generation-zero writer rows as malformed managed state, replaces
child-side inherited session synchronization after fork, and adds a private
operation-identity guard. Copied child leases no-op safely, same-thread close
fails locally with `writer_session_close_during_operation`, cross-thread close
waits for active operations, operation leases retain the concrete session
wrapper, closing and cleaning are distinct, closed is published only after
proof/lock cleanup completes, and fallback finalization is nonblocking with
deferred proof/lock cleanup by the last operation. Concurrent explicit close
callers wait for closed. At the B2c tranche point, the runtime still provided no
`StateStore` mutation backend, transition/global-stop persistence, coordinator
service, worker, scheduler, authorization path, or executable A2 capability.
B2c mutation methods entered that guard and failed locally with
`writer_session_mutation_unavailable`.

B3a is contract-only. `WriterSession.apply_transition` accepts only a
`TransitionCommand`; future transition apply must reconstruct
`TransitionContext` internally from authoritative persisted records. B3a adds
typed lease runtime status, schema-aligned authorization/dependency decisions,
provenance-complete transition events, canonical transition-event and replay
`WorkItemRecord` mappings, event-sequence and transaction-timestamp contracts,
and a safe mutation-store error taxonomy. It does not insert transition events,
update work items, perform idempotency/replay/expected-version runtime logic,
implement admission, verify operator-policy authorization, mutate global stop,
or execute work.

B3b prerequisite contracts are documented in
`.docs/b3b-reader-prerequisite-contract.md`. They are implementation-only
contract pins, not typed SQLite readers. They add no SQLite I/O, no test database
fixture insertion helper, no transition/global-stop mutation, no production
admission or authorization implementation, no executable work, and no migration
0002.

B3b1 is the first implementation under those pins. It adds pure mapping-to-value
contracts for complete explicit row shapes and retains `created_at`,
`admitted_at`, and `updated_at` only inside internal envelopes. It still adds no
SQLite `SELECT`, connection, row cardinality behavior, not-found behavior,
combined transition-input loader, fixture insertion helper, idempotency/replay,
expected-version runtime, event sequence allocation, B3c transition apply, or
B4 global-stop mutation.

B3b2a adds only internal prerequisites for those future readers: ordered
schema-0001 row-column tuples, immutable data-only SELECT specifications, and a
private future-B3c transaction capability protocol. B3b2a does not provide a
concrete production capability, raw-connection scope, reader execution, or
connection lifecycle. `connection.in_transaction` is not transaction identity.
Future B3c must own one opaque epoch per `BEGIN IMMEDIATE` transaction,
invalidate it before commit or rollback, reject old epochs after transaction end
or restart on the same connection, and remain responsible for operation-guard,
writer-fencing, idempotency, expected-version, reader ordering, context
assembly, evaluator invocation, and mutation outcome. B3b2b readers accept
only the private capability protocol.

B3b2b now implements those private readers, but keeps them unreachable from
production source. The readers validate lookup refs before capability borrow,
execute only the immutable parameterized SELECT specs, fetch at most two rows,
map exactly one built-in tuple into a private mapping, and delegate to the B3b1
row adapters. Optional readers return `None` for absence; the global-stop
singleton reader raises a safe integrity failure if the mandatory singleton is
absent. SQLite SELECT failures are reduced to safe
`SQLiteMutationStoreError` classes with no raw exception text, SQL, parameters,
rows, canonical JSON, paths, connection reprs, proofs, digests, or secrets
retained. Unknown exceptions from a capability borrow are also reduced to the
safe private unavailable capability error before any raw exception context can
escape. Tests use a tests-only structural capability; that does not prove
production transaction authority. B3c0a now freezes the future nominal concrete
capability owner, externally atomic operation-lease acquisition semantics, the
shared transition/global-stop pre-SQLite mutation prefix and mutation slot,
`BEGIN IMMEDIATE` and writer fencing order, one opaque transaction epoch,
invalidation before commit or rollback, missing-row classifications,
current/expected/context ordering, timestamp point, idempotency/replay
placement, evaluator placement, sequence and event collision posture, and
rollback/commit/close precedence. B3 tests-only coherent fixtures now provide
temporary managed graphs for future B3c tests. B3c0b/B3c1/B3c2 now cover the
pure event contracts, rollback-only nominal capability, and private
event/idempotency/observed-sequence readers. B3c3 adds runtime replay,
current/context assembly, and evaluator integration for rollback-only dry run.
B3c4b adds private event insertion, accepted current-state mutation, commit,
and commit uncertainty. B3c4c now adds operation-guarded public transition
delegation to that private atomic entry.
B3c0b now implements the pure/static event-row and replay contract portion
that B3c0a left future. It adds no runtime caller: idempotency and
maximum-sequence SQL are immutable data only, and exact replay is a pure
event-owned match over an already reconstructed envelope.
B3c1 now includes B3c1a private WriterSession authority plumbing and B3c1b
private rollback-only writer fencing/capability mechanics. It reconciles
nominal capability construction as one private rollback-only controller path,
binds the controller database open to the active operation lease's
WriterSession resource-owned root/lock/database filesystem binding and
retained common authority lock,
keeps future production invocation limited to
`_SQLiteWriterSession.apply_transition()`, allows coherent tests to invoke that
same private controller through private imports, and keeps public mutation
methods `writer_session_mutation_unavailable` with no SQLite contact.
B3c2 now adds private transaction-internal event/idempotency and observed
maximum-sequence readers only. It remains production-unintegrated and does not
own exact replay/conflict outcomes, sequence allocation, current-state loading,
evaluator integration, durable mutation, commit, or migration 0002. B3c3 now
implements private rollback-only idempotency/context/timestamp/evaluator
dry-run behavior, still production-unintegrated and non-durable. B3c4a freezes
the pure write plan. B3c4b now implements private atomic transition
persistence, and B3c4c makes public `WriterSession.apply_transition()` delegate
to it without moving SQL, transaction, sequence, event, context, evaluator, or
mutation-slot ownership into the public wrapper. B4a now freezes prerequisite
global-stop contracts, B4b adds private global-stop persistence, and B4c makes
public `WriterSession.apply_global_stop_update()` delegate to it without moving
SQL, receipt verification, evaluator, sequence, write, rollback, COMMIT, or
uncertainty ownership into the public wrapper.

The C1 operating model closes the staged topology, first effect ceiling,
capsule custody split, authority roles, direct-local stop conditions, and ES
migration gate as an `ACCEPTED STRATEGIC TARGET`. Exact IPC, supervisor,
credential, capsule-store, model/provider, Git-command, Coordinator schema, and
ES wire mechanics remain `FUTURE IMPLEMENTATION DETAIL`. Direct-local source,
the first ES scenario, publication, and production autonomy remain `DEFERRED OR
BLOCKED EFFECT` until their separately authorized tranches. This selection is
not end-to-end execution and does not reprioritize the current ES P0.

C2A1 pure semantic values and coherence relations remain the current
implementation. C2B0 historically accepted the target durable-development state contract
in `.docs/c2b-durable-development-state.md`: one existing Coordinator database
and writer authority, eight decision kinds, distinct author and bound effect
roles, privacy-safe persistence, and staged migrations 0002/0003. C2B1
migration-framework source is implemented. C2B2 Slice 1 advances the current
application generation to 2 and the terminal catalog to
`0002_development_program_and_effect_state`; the literal migration adds the
nineteen-table physical C2B core schema while preserving migration 0001 and
cumulative packaged SQL as schema authority. Fresh initialization applies
`[0001, 0002]`, explicit migration applies `[0002]` to an exact older prefix,
and ordinary product open never migrates. C2B2 pure row/value source is now
implemented only as four private pure no-I/O modules for exact
tuple decoding, immutable validation, row and result-projection digests,
bounded C2A reconstruction, WorkSpec safe projection, and supplied-entry graph
hashing. Migration 0003, C2B2 private-reader production integration, C2B
mutations, family replay/recovery, complete family graph verification, C2B3,
observation ingest, decision runtime, authority verification, WorkSpec custody,
worker/process execution, capsule storage, Git effects, direct-local execution,
ES routing, and any service, scheduler, queue, publication, or autonomous loop
remain absent.

C2B2 Slice 3 now implements the previously frozen private reader contract:
seven private aggregate/page values, twenty-four literal query specifications,
and twelve reader roles through the real nominal transaction capability seam.
The readers have synthetic execution proofs but no production caller, public
or package-root API, `StateStore`/`WriterSession` method, mutation, receipt
persistence, complete graph proof, replay, recovery, C2B3 behavior, migration
0003, or external effect.

See `.docs/` for the current architecture, authority boundary, and historical
A2-P1 contract.

## Narrowed first vertical-slice target

The accepted pivot now freezes governing architecture only. Initialization is
route-neutral; first author-effect delivery uses the existing
`direct_local_bootstrap` bounded direct/non-ES path to one qualified remote
Linux host, not the user's Mac or Coordinator host. No third adapter is added.

The dependency order is pre-I/O Coordinator progression, remote contact through
semantic decision, a separate local-Git effect and stop, then ES migration
before another productive bootstrap slice. This is not a mandatory program or
tranche count. The bootstrap route permits at most one productive acceptance;
local Git later permits at most one isolated feature-branch commit and no push,
remote-ref mutation, PR, merge, deployment, or publication.

Future initialization, custody, verifier, invocation, evidence, Git,
migration-0003, reliable-submit, and conformance details remain explicit just-
in-time design questions. Current implementation remains generation 2 at
migration 0002 with C2A1, C2B2 private values/readers, and existing bounded
writer/transaction authority only.
