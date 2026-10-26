# NWP Coordinator Architecture


Accepted target reset: `.docs/rw0-c2-durable-progression-decision-semantic-contract.md`
owns five-branch reduction, exact replay, and one whole-family recovery classifier.
`.docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md` solely owns immutable
scope admission and acceptance-fact semantics. One scope belongs to an explicitly
standing-policy-admitted Coordinator authority lineage. Across all participating
direct-local programs at most one distinct productive acceptance may commit.
Machine/database replacement, restore, rollback, clone, passive backup, relocation,
a new grant or policy epoch never replenishes it. Later ES operation is separately
governed and non-replenishing. Mutable-latch target requirements are explicitly
superseded. Guard values, physical storage, migration treatment, provisioner,
reader, writer, public export, and runtime remain future; none is implemented.

The canonical component name is NWP Coordinator.

Current repository name: Governed Execution Coordinator. This operational
repository name is provisional. It may change without changing schema, authority, or durable identifiers.
Repository naming must not affect schema, authority, or durable identifiers.

## C1 Classification Key

C1 architecture statements distinguish `CURRENT IMPLEMENTED CONTRACT`,
`CURRENT COMPATIBILITY EDGE`, `ACCEPTED STRATEGIC TARGET`, `FUTURE
IMPLEMENTATION DETAIL`, `DEFERRED OR BLOCKED EFFECT`, and `PROCESS-ONLY
GOVERNANCE`. The authoritative C1 composition record is
`.docs/autonomous-software-development-operating-model.md`.

## Current Status

The Coordinator now owns bounded internal durable SQLite mutation authority for
coding-work state, one separate pure no-I/O C2A1 semantic-value layer, and the
private pure no-I/O C2B2 row/value layer for the nineteen migration-0002 row
families, plus twelve private C2B2 reader roles. All twelve now have the
bounded private C2B3D author-effect caller; the mutation-receipt role also has
the private VS1B program-initialization caller. The reader layer is bounded to
literal SELECTs through an already-valid nominal transaction capability. The
current implementation includes internal durable writer
issuance, private atomic transition persistence, guarded public transition
delegation, private atomic global-stop persistence, guarded public global-stop
delegation, verification of already-persisted operator-decision receipts,
writer fencing, idempotency, exact replay, accepted-current CAS, rollback, one
COMMIT attempt, commit uncertainty, and explicit retry. C2B3 now also implements
one private route-neutral program-genesis mutation and one private author-effect
establishment mutation, with exact replay and private readback-only
commit-outcome resolution for each family.

RW0-C1 is now a `CURRENT IMPLEMENTED CONTRACT`. Application generation 2
terminates at `0004_rw0_c1_durable_evidence`; the additive zero-seed migration
contributes twenty-three STRICT tables, forty-six immutable update/delete
guards, and four explicit indexes. The private implementation establishes one
immutable RW0 phase and admits one member at a time from the fixed fifteen-kind
inventory through the sole existing Coordinator mutation controller. It owns
receipt-first replay, one commit attempt, guarded readback, and explicit
`committed_exact` / `definitely_not_committed` / `unresolved` recovery. These
facts establish neither evidence completeness nor a C2 decision, acceptance
latch, terminal outcome, source authenticity, executable authority, runtime
truth, external contact, or a public storage API.

A separate post-execution pure-owner tranche now implements only private,
pure, no-I/O values, projections, evaluators, and bounded helpers. It has no
production caller; performs no runtime or I/O; makes and writes no durable
post-execution decision; adds no migration or SQLite widening; creates no
public export; and acquires no external authority or custody. It implements no
C2B progression, terminal outcome, RW0-D/E, or Execution Substrate work.

The future RW0-C2 durable progression-decision semantics are an `ACCEPTED
STRATEGIC TARGET` owned solely by
`.docs/rw0-c2-durable-progression-decision-semantic-contract.md`. The selected
semantics add no current behavior: migration 0002 remains the canonical generic
decision representation, migration 0005 is absent, and durable writer,
acceptance-latch, terminal-outcome, public, and runtime ownership remain
unimplemented.

The Coordinator still does not own or implement work-item production
provisioning, coding-work lease issuance, executable authorization issuance,
operator-decision receipt provisioning, an operational-change domain model,
operational schema, worker, scheduler, queue consumer, dispatcher, Codex
invocation, Execution Substrate runtime handoff, runtime-profile integration,
operational observation ingest, result-ingest path, repair executor, bootstrap
executor, publication path, public service/API/IPC, live operational effect, or
general orchestration. Receipt provisioning remains a separately governed
operator/repo-policy integration seam outside this repository.

Strategic target direction is separate from current implementation facts.
Coordinator may later become the component-level durable progression owner for
governed programs admitted to its target operating model. That target architecture
uses conceptual shared owner-neutral progression mechanics plus separately
versioned software-development and bounded operational-change domain contracts.
The current coding domain remains intact and coding-work-specific. The shared
mechanics do not imply one universal queue, backlog, lease, work-item/state
grammar, state machine, retry or repair counter, dependency receipt model, global
stop, acceptance grammar, effect vocabulary, schema, service, module, worker,
scheduler, or reconciler. This target direction is not implemented by the
current code and does not authorize execution.

Between the accepted durable progression semantics and any future adapter or
process, C2A freezes the first-slice semantic schemas, identities, canonical
digests, observations, fences, and capsule/Git-effect boundaries in
`.docs/c2a-first-slice-semantic-protocol-contract.md`. C2A1 now implements the
nine internal immutable values and six named pure coherence validators in one
standard-library-only no-I/O module. This pure layer adds no durable schema,
process, adapter, worker, executable authorization, ingest, capsule custody,
Git effect, direct-local behavior, or ES routing.

The accepted C1 software-development target is:

```text
reasoning model
    -> Coordinator durable software-development progression
    -> transport-neutral Worker Execution Boundary
    -> bounded direct-local bootstrap/proof adapter
    -> process-separated coding worker
    -> exact immutable candidate capsule
    -> validation and independent review observations
    -> model review proposal
    -> Coordinator acceptance, repair, replan, rejection, or block
    -> at most one local feature-branch Git commit

later, the same progression semantics, worker artifact, and versioned contracts
    -> ES reliable-submit adapter
    -> ES admission and runtime lifecycle
    -> process-separated coding worker
    -> opaque capsule result transport or retention
```

Initial worker source and release machinery are targeted to this repository,
while execution remains in a separate OS process. Direct-local is a bounded
bootstrap/proof route, not the target production path. Bridge and Bridge Core
are not worker owners. The target does not select a generic environment controller,
topology controller, universal scheduler, capability registry, background
probe loop, continuous drift reconciler, operational effect engine, or
operational production topology. Owner-route semantics, external standing
authority issuance, ES/runtime ownership, and source-observation ownership
remain separate. Operational acceptance is a future Coordinator durable
progression decision over admitted owner-source observations; it is not
ownership of the observed fact.

The reserved Worker Execution Boundary is documented in
`.docs/worker-execution-boundary.md`. It remains coding-specific and
transport-neutral. Direct-local and later ES adapters must conform to the same
versioned worker command, observation, fence, and capsule contracts. The
boundary and C1 add no worker, supervisor, scheduler, dispatcher, reconciler,
service/API/IPC, ES call, Bridge widening, Codex invocation, model/provider
client, capsule store, Git effect, schema, migration, outbox/inbox
implementation, runtime profile, connector dependency, or autonomous loop.
Exact IPC, supervisor, package, executable, credential, and deployment
mechanics remain future implementation details. The bounded operational-change
target remains separately documented in
`.docs/operational-progression-boundary.md` and is excluded from C1's first
software-development slice.

The canonical cross-repository integration architecture/status decision is
recorded at
`Execution Substrate/.docs/system_overview/hybrid_integration_architecture_adr.md`.
That pointer does not transfer Coordinator architecture ownership to Execution
Substrate. It is current cross-repository status and migration authority, not
the complete Coordinator target operating model.

## Scope

Historically, A2-P1/P1.1 established a local Coordinator skeleton for A2
coding-work state. It contains domain models, deterministic identity contracts,
a pure state transition evaluator, command/event and writer-session contracts,
and non-authoritative report projections. The later B-tranches described below
add the bounded durable SQLite mutation authority named in Current Status.

P1 versioned inputs are closed-world contracts. Unknown keys, duplicate JSON
object keys, misspelled keys, and unversioned extension bags fail before
canonicalization or digest verification.

P1/P1.1 remains historical contract context, not the current whole-repository
status. It has no worker invocation path, no scheduler, no daemon, no queue
consumer, no public `StateStore` mutation backend, no sandbox, no repair
executor, no local commit behavior, and no publication behavior. It also has no
production future-stage enablement policy or configuration.

## Authorities

The NWP Coordinator currently owns only bounded coding-work durable state. The
target Coordinator may later own durable progression decisions for admitted
software-development and bounded operational-change programs. It does not own
owner-route meaning, external standing-authority issuance,
source-observation truth, or runtime lifecycle truth.

Bridge remains a guarded adapter/evidence surface today and is not the target
worker owner or a direct-local trigger. A future direct-local supervisor/adapter
and later ES adapter may own only bounded process and transport protocol
mechanics, ephemeral invocation/session correlation, and bounded
redaction/evidence shaping. They must not own durable work selection,
scheduling policy, semantic retry or repair authority, acceptance, ES
admission, runtime lifecycle truth, Git truth, validation truth, or hidden
program state.

Execution Substrate remains execution admission/runtime authority: execution
admission, runtime-profile compatibility, prepare and submit handoff, runtime
identity and credential-handoff boundaries, submitted execution lifecycle
projection, runtime cancellation request boundary, and retained execution
results remain ES-owned. Git owns repository object and ref truth. CI or
validating runtimes own observed validation results.

Control Plane remains relevant only to current maintained MVP/demo
compatibility, migration, filming, freeze, reference, or retirement context. CP
is not part of the target autonomous-development topology. Owning
repositories/components retain route/action meaning, route eligibility,
preconditions, privilege and runtime-profile requirements, identity/signing/secret
custody, idempotency and re-entry, post-check meaning, rollback, compensation,
containment, and redaction.

Maintenance Agent currently retains only its bounded current-contract scan,
proposal, approval-record, route-matrix/eligibility handling, and bounded
foreground invocation behavior. MA is not selected as the general authorization
issuer, renewal authority, deployment authority, runtime/lifecycle authority, or
durable operational-progression owner. Infrastructure Manager outputs remain
readiness evidence, bootstrap provenance, diagnostics, and profile/support
evidence. IM is not durable progression, operational acceptance, owner-route,
orchestration, or runtime authority. MA/IM survival, migration, or retirement
remains open.

Under the current implemented contract, operator/repo policy owns lease
issuance and global stop. The Coordinator observes and enforces those decisions
but cannot issue external standing authority, clear or weaken global stop,
reinterpret authority, or self-authorize. Current executable authorization is
unsupported and fail-closed.

Under the accepted target, external standing-policy authority authors immutable
standing grants, revocation or expiry, applicable global-stop directives, and
effect ceilings. Coordinator may verify and durably bind a safe parent-grant
reference and derive only narrower subordinate attempt/effect records and
fences. It cannot exceed, extend, renew, reinterpret, or outlive the external
grant, and the external authority does not write Coordinator SQLite directly.
Subordinate authorization is not currently implemented.

Model reasoning owns cognitive intent, architectural and semantic judgment,
planning, replanning, and evidence review. Model sessions, ChatGPT state,
connector state, API request/session context, Symphony, reports, Bridge ledgers,
Bridge reports, profiles, retained bundles, MA proposals, IM readiness evidence,
CP projections, traces, request IDs, and local runner evidence remain adapters,
evidence, or projections. They are not durable A2 state or target durable program
truth.

Model output is a non-authoritative proposal, not a durable progression
decision or effect authority. The user steers major direction, priorities, and
risk posture and is not a routine synchronous per-attempt approver.

## P1 Package

The implementation namespace is `ge_nwp_coordinator`. That package name is an
implementation detail, not a durable identity and not a promise about the
repository display name.

Runtime code uses only the Python standard library. Test-only fakes live under
`tests/`; production code provides only fail-closed default authorization,
typed contract objects, pure evaluators, and state-store protocols.

The B3a transition contract flow is:

`TransitionCommand + authoritative current state + internally reconstructed
TransitionContext -> evaluator -> TransitionEvent`

A future active writer session performs mutation through the atomic store
boundary. That boundary performs fencing, idempotency, current-state load,
expected-version comparison, authoritative context reconstruction, evaluator
invocation, and atomic state/event persistence. Proposed state, events, and
caller-supplied transition context are not supplied by callers.
Expected-version mismatch is an apply conflict with no event. Safe writer
metadata is evidence only and cannot authorize mutation.

The B3b reader prerequisite contract is documented in
`.docs/b3b-reader-prerequisite-contract.md`. It is not a reader implementation.
It pins the future read bundle authority: admitted backlog is mandatory
transition authority, `WorkItemRecord` attempt/repair limits are exact copies of
standing-lease limits, scalar current-state budget fields are zero-only reserved
compatibility fields in the first persisted slice, dependency receipts are
READY-only, operational row timestamps remain internal envelope metadata, and
schema 0001 is sufficient for the bounded typed-reader slice.

B3b1 implements the pure internal row-contract subset of that prerequisite. It
converts already-fetched explicit schema-0001 row mappings for lease identity,
authorization, dependency, work items, admitted backlogs, and
`global_stop_current` into validated typed envelopes. It validates exact row
shape, strict SQLite Booleans, canonical JSON/digest/index equality where the
schema provides canonical JSON, normalized current-state columns where it does
not, and exact operational UTC `Z` timestamps. It does not add a SQLite reader,
connection, transaction, row cardinality contract, not-found classification,
fixture insertion helper, combined transition-input loader, transition/global
stop mutation, or package-root export.

B3b2a implements the next internal prerequisite. It defines ordered
schema-0001 row-column tuples as the row-shape source of truth, derives existing
row-key contracts from those tuples, defines six immutable explicit-column
parameterized SELECT specifications, and defines a private future-B3c
transaction capability protocol. B3b2a does not implement a concrete
transaction-bound capability, accept raw SQLite connections as authority,
own connection lifecycle, own transactions, widen public `StateStore`, or
integrate with `WriterSession.apply_transition`.

B3b2b implements the six private SELECT readers over those specs and keeps them
unreachable from production callers. The readers validate lookup refs before
borrowing, borrow only through `_MutationReadCapability`, execute the
parameterized specs, call `fetchmany(2)`, enforce zero/one/multiple
cardinality, require exact built-in tuples, build private mappings, delegate to
B3b1 row adapters, classify SQLite SELECT errors safely, sanitize unknown
capability borrow exceptions, and close cursors. Tests execute them with a
tests-only capability and in-memory tables. B3b2b does not add a concrete
capability, public read port, fixture program, cross-record assembly, admission,
authorization verification, transaction ownership, or mutation.
`connection.in_transaction` is not transaction identity.

B3c0a freezes the future transition mutation authority and ordering contract in
`.docs/b3c0a-transition-authority-and-order.md`. Future B3c must own one
nominal private capability and one opaque epoch per `BEGIN IMMEDIATE`
transaction, create that capability only through one private controller path
while one operation lease is active and after writer fencing, allow future
production invocation only from `_SQLiteWriterSession.apply_transition()`,
treat operation-lease acquisition as the externally atomic lifecycle/process and
retained-lock gate, share the transition/global-stop pre-SQLite mutation prefix
and one mutation slot, invalidate the capability before commit or rollback,
reject old epochs after transaction end or restart, fence before idempotency,
read current state and expected version before context rows, capture the
transaction timestamp only after authoritative row binding, and preserve the
pinned rollback/commit/close precedence. B3c0a does not implement the concrete
capability, writer-fencing SELECT, idempotency/replay, event sequence SQL,
context assembly, evaluator invocation, fixtures, or mutation outcome.

B3c0b implements the pure/static event-row and replay contracts that B3c0a left
future. It defines the exact ordered schema-0001 `transition_events` columns,
an internal hidden `TransitionEventRecordEnvelope`, canonical event/replay
reconstruction and digest/index equality checks, `created_at` equality with
`TransitionEvent.lease_runtime.evaluated_at`, bounded zero-budget replay
posture, pure event-owned idempotency matching, immutable data-only idempotency
and maximum-sequence query specs, and pure sequence allocation tests. It does
not implement SQL execution, readers, a concrete capability, writer fencing,
context assembly, evaluator invocation, mutation outcome, admission,
authorization verification, or migration 0002.

B3c2 implements private transaction-internal transition-event SELECT readers in
`sqlite_transition_event_readers.py` and a tiny shared private
`sqlite_transition_select_support.py` module for B3b2b/B3c2 cursor lifecycle,
capability borrowing, tuple mapping, and safe SQLite SELECT-error
classification. The idempotency reader validates lookup refs before borrowing,
uses the immutable B3c0b lookup spec, enforces `LIMIT 2` cardinality, delegates
full event/replay reconstruction to the B3c0b row adapter, rechecks the
reconstructed event address, and returns only `None` or an exact hidden
`TransitionEventRecordEnvelope`. The maximum-sequence reader uses the immutable
B3c0b aggregate spec, returns only `None` or an exact observed non-negative
built-in integer, and makes no allocation claim. B3c2 has no production caller,
no B3b2 context-reader call, no pure matcher or allocator production call, no
apply-result ownership, no public API/export, no durable mutation, no commit,
and no migration 0002.

B3c3 contracts are documented in `.docs/b3c3-prerequisite-contract.md`, and
the private rollback-only runtime is documented in
`.docs/b3c3-rollback-only-transition-dry-run.md`. B3c3 implements only a
private production-unintegrated dry run through the single B3c1b controller and
nominal capability path. It performs command-local preflight before
mutation-slot acquisition; fences the writer before idempotency disclosure;
reads B3c2 idempotency data; calls the pure matcher exactly once; reads current
state; compares expected version; reads B3b2 context rows in the order lease
identity, admitted backlog, authorization, READY dependency when required, and
global stop; binds authority through the frozen helper; captures one private
UTC timestamp; derives lease runtime; constructs one `TransitionContext`;
invokes the evaluator exactly once; and returns only a private non-durable
result after capability invalidation, rollback, close, and mutation-slot
release. B3c3 does not read maximum sequence, allocate sequence, write events
or state, perform CAS, commit, widen public APIs or `StateStore`, or add
migration 0002. Fresh evaluator output is explicitly non-durable and
non-receipt until B3c4 persists and commits it.

B3 tests-only coherent fixtures now live under `tests/` only. They initialize a
temporary current-generation-2 database at terminal migration
`0004_rw0_c1_durable_evidence`, while directly seeding only the historical
schema-0001 B3/B4 graph. All nineteen C2B core tables, all nine cognitive
proposal-selection tables, and all twenty-three RW0-C1 tables remain empty. The
fixture graph is not production admission, authorization, runtime authority,
product state initialization, accepted operator-policy authority, an executable
transition proof, or proof of C2B row/value, reader, mutation, or replay
behavior. The exact physical-versus-semantic and writer-lifecycle contract is
owned by `.docs/b3-tests-only-coherent-fixtures.md`.

B3c1 prerequisite contracts are documented in
`.docs/b3c1-prerequisite-contract.md`. They freeze the
production-unintegrated/test-executed rollback-only posture, the single private
controller construction path, the resource-owned mutation slot and
mutation-lease identity, the operation-lease authority and durable-issuance
verification interfaces, resource-owned state-database filesystem-authority binding, the writer-row
query/parser ownership, writer-fencing classifications, nominal capability and
epoch rules, rollback-only cleanup precedence, and the B3c1a/B3c1b split.
B3c1a implements only private
WriterSession authority plumbing: one mutation slot, one mutation lease,
operation-lease active-authority checks, resource-owned bound-database
authority, durable-issuance verification, atomic mutation-slot publication plus
lease-construction unwind, and `_WriterIssuanceMatch`. B3c1b implements only
private rollback-only writer fencing/capability mechanics: one operation-lease
only private controller entry point, one fresh managed read/write connection
opened only through the WriterSession resource-owned root/lock/database
binding, `BEGIN IMMEDIATE`, post-begin binding revalidation, managed
validation, one bounded writer-row query using the existing parser, one
nominal capability with one opaque epoch, permanent invalidation, rollback,
close, and exact private `_WriterIssuanceMatch` return. The controller
database binding contains the exact CoordinatorStateLocation, state-root
identity, authority-lock-file identity, and single-link database-file identity
captured while the retained common authority lock was held; a matching writer
row in another database is not authority. Replaced root/lock/database paths and
hard-linked active database aliases fail closed. B3c1 still adds no B3b2
reader integration, context assembly, evaluator invocation, event/state
mutation, public behavior change, commit, or migration 0002.

Report projections are closed typed models. They expose safe refs, enums,
bounded counters, global-stop status, and a fixed non-authority notice only;
they are not generic sanitized payloads and do not carry private, endpoint,
path, platform, credential, or trust material.

## B0 SQLite Backend Selection

B0 selected SQLite, one private local database, as the first bounded local state
backend architecture. B1/B1.1 add the migration runner and local administrative
database posture. B2b adds the common state-authority lock for
initialize/migrate administration. B2c adds durable writer issuance and
internal writer-session acquisition. Later B3c4/B4 tranches add the bounded
writer-session transition/global-stop mutation authority described in Current
Status. The public `StateStore` remains unwidened; the runtime still has no
coordinator service and no executable A2 capability.

The selected first-backend journal posture is rollback journal DELETE mode with
`synchronous=FULL`, `locking_mode=NORMAL`, `foreign_keys=ON`,
`trusted_schema=OFF` where supported, bounded `busy_timeout`, and
`BEGIN IMMEDIATE` mutation transactions. WAL is reserved for a later audit if a
current reader-concurrency requirement justifies its extra `-wal` and `-shm`
filesystem surface.

The B0/B2a authority, schema, threat, and operations contracts are documented
in:

- `.docs/sqlite-state-backend-adr.md`;
- `.docs/sqlite-schema-v1.md`;
- `.docs/sqlite-threat-model.md`;
- `.docs/sqlite-operations-and-recovery.md`;
- `.docs/writer-session-authority.md`.

## C2B1/C2B2 SQLite Administration And Pure Row Values

B1/B1.1 historically established explicit operator-local SQLite bootstrap and
observational validation. C2B1 owns the bounded administrative migration
transaction in `sqlite_migration.py`; C2B2 Slice 1 introduced application
generation 2 and migration 0002, and the current catalog now terminates at
migration 0003 while retaining generation 2:

- fixed per-user local state-location policy using the canonical NWP
  Coordinator component name, not the repository display name;
- owner-only filesystem preparation and validation for the state root and
  fixed database filename;
- split standard-library SQLite connection posture verification for
  observational existing-database reads, administrative initialization, and
  managed-write migration;
- closed packaged, versioned, forward-only migration catalog;
- complete-catalog installation into an explicitly requested local database;
- non-mutating absent/empty/managed/unknown classification;
- exact persisted-history/catalog equality and terminal-only
  application-compatibility validation;
- exact-current ordinary open and explicit supported-prefix migration;
- cumulative live-schema manifest verification derived from packaged migration
  bytes through the selected terminal;
- whole-suffix one-transaction application and three-way commit readback;
- bootstrap and generic managed current-state invariant checks.

The administrative runtime-capability preflight is derived from the maximum
immutable catalog target, not from the suffix suggested by the first
observation. For the generation-2 catalog, both initialization and explicit
migration require SQLite `3.37.0` before state-root creation, common-lock
acquisition, writable open, `BEGIN`, or mutation; a permitted reobservation
therefore cannot widen the selected suffix beyond the already-gated capability.

B1.1/C2B1 inspect/validate do not create missing roots or databases, do not change
persistent journal posture, do not repair or adopt unknown databases, and do
not auto-migrate. Initialize and migrate are explicit operator-local
administrative mutations. B2b initialize/migrate acquire the common
state-authority lock and revalidate while holding it. C2B1/B2b do not implement a
SQLite `StateStore`, product mutation methods, database-backed product reads,
reports over the database, coordinator service behavior, worker execution,
authorization, scheduling, repair, local commit, publication, or deployment.
B2c implements writer acquisition and `writer_ownership` issuance updates
only, not product mutations.
Normal future runtime must not run migrations concurrently with an active
Coordinator writer.

The current bootstrap and migration contract is documented in
`.docs/sqlite-bootstrap-and-migrations.md`, C2B2 Slice 1 implementation status
is recorded in `.docs/c2b2-migration-0002.md`, and Slice 2 pure row/value
status is recorded in `.docs/c2b2-pure-durable-row-values.md`. Slice 3 private
reader status is recorded in `.docs/c2b2-private-readers.md`.

This administrative transaction reuses the one common exclusion lock and
filesystem binding but is not the Coordinator product writer, not a second
progression controller, and not C2B semantic truth. Slice 2 separately provides
only private pure tuple-to-value validation, eighteen self-digest checks, five
receipt result projections, bounded C2A reconstruction, WorkSpec safe
projection, and the common supplied-entry graph digest primitive. It performs
no SQL. Slice 3 separately implements private database readers with synthetic
execution proofs. The private-reader layer remains exactly twelve private roles
and twenty-four bounded query contracts with no public surface or reader-created
durable authority. All twelve roles have the bounded private C2B3D author-effect caller,
the mutation-receipt role also retains the private VS1B program-initialization
caller, and the later Section 41 selection and RW0-C1 runtimes compose with a
bounded seven-role subset. Those later callers do not widen the reader query
contract. C2B2 did not implement or acquire ownership of migrations 0003/0004,
Section 41, or RW0-C1;
reader reports and projections remain neither durable program truth nor effect
authority. C2B3 provides its private program-genesis and author-effect families,
and Section 41 provides private pre-execution selection. Other C2B mutation
families, observation ingest, later decision runtime, effects, and
worker/runtime behavior remain absent.

## B2a Writer-Session Contract

B2a corrects the writer authority contract before implementation:

- standalone reconstructable public writer tokens are not mutation authority;
- `WriterSession` is the opaque future live mutation capability;
- safe writer metadata contains only non-secret issuance evidence and no proof,
  proof digest, lock path, process id, or liveness claim;
- no `current_writer()` read surface exists;
- one common future state-authority advisory lock covers initialize, migrate,
  writer acquisition, and the full active writer-session lifetime.

B2a does not implement writer acquisition, proof generation or verification,
SQLite `writer_ownership` updates, a concrete writer session, a `StateStore`
mutation backend, product reads, reports over SQLite, worker execution,
scheduling, repair, local commit, publication, deployment, or executable
authorization.

## B2b State-Authority Lock

B2b implements one common state-authority advisory lock for macOS and Linux.
The fixed persistent lock file remains named `coordinator-state.migration.lock`
on disk for compatibility, but the authority concept is the state-authority
lock. Initialize and migrate use that lock, including no-op current-schema
administration. Inspect and validate remain observational and do not create or
acquire the lock.

The lock provides live-process exclusion only. It is not writer authority, not
a writer credential, not durable state, and not sufficient for work-item or
global-stop mutation. B2c combines the retained lock with durable generation
issuance and a private in-memory proof inside an internal writer session.

B2b owns a real descriptor through a private resource object. Explicit
context-manager close remains the required release path; a one-shot finalizer
is only a fallback for abandoned lock objects and does not provide timing or
authority evidence. Every opened descriptor is immediately owned by a cleanup
scope until it is explicitly transferred. A parent-side lifecycle/fork gate
serializes descriptor opening, validation, `flock`, registry insertion,
finalizer publication, parent close, and pre-fork snapshot creation. Fork child
cleanup uses the frozen raw-descriptor snapshot, does not acquire inherited
Python locks, closes inherited descriptors without `LOCK_UN`, clears only the
child-side copied registry, and leaves parent authority untouched. Python
continues to warn that multithreaded fork is broadly unsafe, and third-party
forks that bypass Python at-fork hooks remain a limitation.

## B2c Writer Issuance

B2c implements internal SQLite writer acquisition for existing current managed
databases. Acquisition revalidates the managed schema while holding the common
lock, starts `BEGIN IMMEDIATE`, issues a monotonically increasing generation,
generates independent safe writer and issuance refs, stores only the
domain-separated private-proof digest, commits the singleton
`writer_ownership` row, closes the acquisition SQLite connection, and returns
an internal concrete `WriterSession` retaining the common lock.

The SQLite row remains latest issuance evidence only. It is not liveness truth,
not a credential, and not sufficient to mutate work-item or global-stop state.
B2 hardening adds generation-zero semantic rejection, child-side replacement
of inherited session synchronization after fork, and a private
operation-identity guard. Copied child leases no-op safely after fork;
same-thread close fails locally with
`writer_session_close_during_operation`; cross-thread close waits for active
operations; operation leases retain the concrete session wrapper; and
closing and cleaning are distinct so exactly one cleanup owner releases proof
and advisory-lock resources before closed is published. Nonblocking fallback
finalization may defer proof/lock cleanup until the last active operation exits,
and concurrent explicit close callers wait for closed. B2c mutation methods
enter that guard and fail locally with `writer_session_mutation_unavailable`.
B3a defines transition-persistence contracts only: command-only
`WriterSession.apply_transition`, typed lease runtime decisions,
schema-aligned decision/event provenance, canonical event/replay mappings, and
safe mutation-store errors. B3a does not add SQLite transition persistence.
B3b prerequisite contracts add pure/model reader prerequisites only: no
integrated production typed SQLite reader, production fixture insertion,
transition/global-stop mutation, admission, authorization verifier, worker,
scheduler, service, CLI, MCP, connector, repair, commit, publication, migration
0002, or executable A2 behavior. B3b1 adds only pure full-row envelope adapters
for already-fetched rows. B3b2a adds private capability-protocol and query-spec
contracts. B3b2b adds private SELECT readers with tests-only execution and no
production call sites. B3c0a adds contract/static pins only for the future
transition authority boundary. B3c0b adds pure event/replay row, idempotency,
and sequence contracts only. B3 tests-only coherent fixtures add temporary
managed graphs for future tests only. B3c1 adds prerequisite contract pins and
B3c1a private WriterSession authority plumbing for production-unintegrated
rollback-only controller construction, the mutation slot and operation-lease
interfaces, retained filesystem binding, writer-fencing taxonomy, capability
epoch rules, cleanup precedence, and the B3c1a/B3c1b split. There is still no
public or production transaction caller or mutation. B3c2 adds private event
readers only, and B3c3 adds only the private rollback-only dry run with reader
ordering, exact replay/conflict handling, context assembly, timestamp capture,
  and evaluator invocation but no durable persistence. B3c4a adds only
  pure/static transition write specifications, value builders, a private planned
  write plan, the then-transition-owned commit-resolution vocabulary later
  neutralized by B4b, SQLite classification, retry, proof, and
  public-integration boundary contracts. B3c4b now implements private atomic
  transition persistence through that same controller path: fresh evaluations
  read maximum event sequence, allocate the next sequence, consume the frozen
  write plan, insert one event, CAS-update accepted current state, invalidate
  capability, and attempt exactly one commit with `commit_outcome_unknown` on
  commit-attempt exceptions. B3c4c now makes public
  `_SQLiteWriterSession.apply_transition()` delegate to that B3c4b entry through
  the existing operation guard, with only bounded local import and exact
  preflight mapping in the public wrapper. SQL, transaction, sequence, event,
  current-state CAS, context, evaluator, capability, and mutation-slot ownership
  remain in the private atomic path. B4a now adds prerequisite global-stop
  contracts, readers, sequence allocation, receipt binding, and pure/static
  write grammar only. B4b now adds private global-stop persistence through the
  same neutral mutation controller. B4c now makes public
  `_SQLiteWriterSession.apply_global_stop_update()` delegate to that B4b entry
  through the existing operation guard, with only bounded local import and exact
  preflight mapping in the public wrapper. SQL, receipt verification, evaluator,
  sequence, write, rollback, COMMIT, and uncertainty ownership remain in the
  private atomic path. Receipt provisioning remains reopened, and no worker,
  service, scheduler, admission, orchestration, publication, or cross-repo
  authority exists.

## C2B0 Accepted Durable-State Target Topology

Status: `CURRENT IMPLEMENTED CONTRACT` for the narrow C2B3 route-neutral
program-genesis and author-effect families; the broader C2B0 topology remains
an accepted target.
C2B2 Slice 1 physically represents the nineteen-table core, Slice 2 implements
its private pure row/value layer, and Slice 3 implements the private database
readers. All twelve roles have the bounded private C2B3D production caller;
the mutation-receipt role also retains the VS1B production caller.
C2B1/C2B2-Slice-1 administrative migration source and C2B2-Slice-2 pure
row/value source are current but confer no product authority.

C2B targets private role-based durable-development modules in the existing
Coordinator SQLite database. They must reuse the existing concrete writer
issuance/fencing authority, operation guard, shared mutation slot, resource
binding, nominal transaction capability, and single transaction controller.
There is no second database, writer, controller, session authority, generic
mutation dispatcher, public `StateStore` widening, or public `WriterSession`
widening.

The target private transaction roles separate program initialization,
author-effect establishment, bound validation/review/cancellation-effect
establishment, source-observation ingest, and progression decisions. Durable
intent must precede future external I/O. C2B2 Slice 1 provides the
migration-0002 physical core at current generation 2, and Slice 2 provides
private pure row/value source for its nineteen tables. Slice 3 provides exactly
twelve private reader roles with no public surface; all twelve have the bounded
C2B3D caller, while the receipt role also retains the VS1B caller. C2B3
privately persists and exactly verifies the route-neutral nine-row/eight-entry
program-genesis family and the ten-row/nine-entry author-effect family,
including same-command replay and readback-only commit-outcome resolution.
Migration 0003 now adds only the private non-executable pre-execution
proposal-selection family with receipt-first replay and fresh-writer read-only
recovery. No bound effect, observation, post-execution progression-decision
runtime, worker, Bridge dependency, ES dependency, service, queue, scheduler,
or autonomous loop exists.

<!-- RW0_D1_CURRENT_STATUS_BEGIN -->
RW0-D1 is a current private artificial offline process and capsule proof. The guarded Coordinator program-initialization, C2B3D author-effect, Section 41 selection, and RW0-C1 phase writers remain the sole durable owners. A separate fake planner and fake coding worker run under the bounded D1 supervisor; the parent captures one temporary candidate, builds and independently verifies a CandidateCapsuleManifestV1, removes the mutable workspace, and returns a transient typed handback with separate parent-only disposable-state custody. The preassigned fixture base_git_oid is a WorkSpec coordinate, not Git authentication. RW0-D2 validation/review/model closure is next; RW0-C2 physical decision persistence follows D2. D1 grants no live provider/credential or source authentication, ES route, Git/publication effect, terminal acceptance, public service/CLI, or RW0-E runtime authority. The detailed implementation owner is .docs/rw0-d1-offline-process-and-capsule-spine.md.
<!-- RW0_D1_CURRENT_STATUS_END -->

<!-- RW0_D2_CURRENT_STATUS_BEGIN -->
RW0-D2 now contains a bounded private offline source candidate for the two
guarded validation/review effects, checked C1 evidence, separate fake
validator/reviewer/model processes, exact nine-role input, and transient
preadmission handback. This successor updates only the earlier D2-next status.
It adds no durable post-execution Section 41 proposal family, C1 rank-15
admission, C2 decision/acceptance/terminal writer, migration 0005, live model,
ES runtime, or production adapter. External-copy validation and independent
audit remain pending. The detailed owner is
`.docs/rw0-d2-offline-evidence-and-review.md`.
<!-- RW0_D2_CURRENT_STATUS_END -->

**Native post-D2 offline successor.**

The private Coordinator now has one Section 41 post-execution proposal-family writer and checked reader, reached only from an adjacent outer D2 continuation under the existing fenced writer/controller. A separate C1 transaction admits one rank-15 member from the checked twelve common rows, and pure V22 consumes final checked A/B families. Current SQLite generation 2 ends at additive migration 0005 (64 user tables, 114 triggers, five explicit indexes). Older 0004-tip/absent-0005 statements in this architecture record are historical tranche snapshots. This temporary artificial proof is neither restart-safe custody nor C2 decision/acceptance/runtime authority; live gate B remains required.

<!-- C2B3_NARROWED_ARCHITECTURE_BEGIN -->
## C2B3 vertical-slice governing narrowing

Sections 36 and 38 of `.docs/c2b-durable-development-state.md` supersede only the
named route selections, horizontal implementation order, active path-count
manifests, and previously selected initialization/migration target shapes. It
replace them with governing architecture and, for VS1B, the implemented exact
route-neutral genesis family. Later phases remain just-in-time questions.

Initialization is route-neutral. Route selection occurs only at author-effect
delivery, whose first route is the existing `direct_local_bootstrap` bounded
direct/non-ES compatibility path to one qualified remote Linux host. It does
not mean the user's Mac, the Coordinator host, or physical colocation, and it
introduces no third adapter kind.

Coordinator remains durable-progression authority only. Parent standing grant,
current verification, worker execution, Git truth, validation/review evidence,
and publication authority remain outside it. The worker receives no
Coordinator SQLite or writer access. At most one productive bootstrap
acceptance and one later isolated local feature-branch commit are permitted;
push, remote-ref mutation, PR, merge, deployment, and publication remain zero.
The implemented VS1B family uses migration 0002 unchanged, one receipt-first
transaction, exactly nine state rows and eight supplied graph entries, exact
same-command replay, and private readback-only uncertainty resolution. It adds
no route, dispatch, worker, capsule, external I/O, or executable authority.
The private C2B3D implementation was introduced and is committed at
`5e544622e5f46ddc78294322471b4fcbd2ad9172`; it reuses that same mutation
authority for exactly ten author-effect rows and nine supplied graph entries.
Git owns the committed object and ref fact; independent acceptance, audit,
validation, provenance, and report records remain external evidence rather
than Coordinator durable authority or effect permission. C2B3D persists a
planned `direct_local_bootstrap` delivery as inert intent, verifies bounded
current effect/delivery heads, and performs no dispatch, worker, capsule,
credential, network, Git, Bridge, or ES effect. Exact later-phase values and
evidence layouts remain deferred.
<!-- C2B3_NARROWED_ARCHITECTURE_END -->

<!-- RW0_C2_P0_PHYSICAL_ARCHITECTURE_CANDIDATE_BEGIN -->
## RW0-C2 artificial-offline physical candidate

The uncommitted P0 candidate adds a private program-independent admission
recording path through the existing fenced SQLite writer controller and
migration 0006. It does not alter the Section 41/C1/V22 owner path, public
StateStore, production callers, worker transport, or effect handling. P1 is a
separate decision transaction in the same planned candidate.
<!-- RW0_C2_P0_PHYSICAL_ARCHITECTURE_CANDIDATE_END -->

<!-- RW0_C2_P1_PHYSICAL_ARCHITECTURE_CANDIDATE_BEGIN -->
## RW0-C2 P1 artificial-offline physical candidate

The current uncommitted successor adds a separate private five-branch
development progression transaction on migration 0007 through the existing
fenced SQLite writer controller. Replan CAS-updates both mutable heads and
retains both historical postimages. The Section 41/C1/V22 owner path, public
StateStore, production callers, worker transport, and effect handling are
unchanged.
<!-- RW0_C2_P1_PHYSICAL_ARCHITECTURE_CANDIDATE_END -->
