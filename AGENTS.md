# NWP Coordinator Agent Rules

If `.docs/` exists, always treat `.docs/` as the source of truth.

## Ownership

This repository owns bounded internal durable SQLite mutation authority for
coding-work state. Current Coordinator code includes internal durable writer
issuance, writer-fenced transition/global-stop apply, verification of
already-persisted operator-decision receipts, idempotency, CAS, exact replay,
commit uncertainty, and explicit retry semantics.

C1 contract language distinguishes `CURRENT IMPLEMENTED CONTRACT`, `CURRENT
COMPATIBILITY EDGE`, `ACCEPTED STRATEGIC TARGET`, `FUTURE IMPLEMENTATION
DETAIL`, `DEFERRED OR BLOCKED EFFECT`, and `PROCESS-ONLY GOVERNANCE`. The
authoritative composition record is
`.docs/autonomous-software-development-operating-model.md`.

C2A is the accepted authority for exact first-slice semantic schemas,
identities, digests, fences, observations, capsule, and effect boundaries in
`.docs/c2a-first-slice-semantic-protocol-contract.md`. C2A1 now implements one
internal pure no-I/O semantic-value module and the six named pure coherence
validators governed by `.docs/c2a1-pure-semantic-values.md`. This source adds
no durable schema, migration, process, executable effect authorization, ingest,
capsule custody, Git effect, direct-local behavior, or ES routing.

Bridge remains the current guarded adapter/evidence surface and is not durable
program state, scheduler, lifecycle truth, retry/repair authority, or acceptance
authority. Execution Substrate remains execution admission/runtime authority:
admission, runtime-profile compatibility, reliable keyed submit when that future
contract is implemented, prepare/submit handoff, runtime identity and
credential-handoff boundaries, submitted-execution lifecycle projection, runtime
cancellation-request boundaries, and retained execution results remain ES-owned.
Control Plane remains relevant only to current maintained MVP/demo compatibility,
migration, filming, freeze, reference, or retirement context; CP is not part of
the target autonomous-development topology. Maintenance Agent currently retains
only its bounded current-contract scan, proposal, approval-record,
route-matrix/eligibility handling, and bounded foreground invocation behavior.
MA is not selected as the general authorization issuer, renewal authority,
deployment authority, runtime/lifecycle authority, or durable
operational-progression owner. Infrastructure Manager outputs remain readiness
evidence, bootstrap provenance, diagnostics, and profile/support evidence. IM is
not durable progression, operational acceptance, owner-route, orchestration, or
runtime authority. MA/IM survival, migration, or retirement remains open.

Under the current implemented contract, operator/repo policy owns lease
issuance and global stop. The Coordinator cannot self-authorize, cannot mint
external standing authority, and cannot treat a valid digest as execution
permission. Current executable authorization remains unsupported and
fail-closed.

Transition commands and global-stop commands remain caller inputs. Accepted or
domain-rejected transition/global-stop events and current state now have bounded
durable SQLite persistence only through the guarded writer-session mutation
paths. Reports are projections only. They are not durable state,
authorization, acceptance, publication, or product truth.

The Coordinator still does not own or implement a worker, scheduler, queue
consumer, work-item production provisioner, decision-receipt provisioner,
coding-work lease issuer, executable authorization issuer, Codex invocation, CP
workflow, ES runtime, publication, or general orchestration. Receipt
provisioning remains reopened and external to this repository.

Strategic target direction is separate from current behavior. Under the
accepted C1 software-development target, external standing-policy authority
authors immutable grants, revocation or expiry, applicable global-stop
directives, and effect ceilings. Coordinator may later verify and durably bind
a safe parent-grant reference and derive only narrower subordinate
attempt/effect authorization records and fences. It may never exceed, extend,
renew, reinterpret, or outlive the external grant, and its durable record never
becomes independent external authority. This subordinate behavior is target-only
and is not currently implemented.

Coordinator may later become the sole component-level durable progression
authority for governed programs admitted to its target operating model through
a conceptual shared owner-neutral progression kernel and separately versioned
software-development and bounded operational-change domain contracts. Shared
mechanics do not imply one universal queue, backlog, lease, work-item/state
grammar, state machine, retry or repair counter, dependency receipt model,
global stop, acceptance grammar, effect vocabulary, schema, service, module,
worker, scheduler, or reconciler. Coordinator target ownership is durable
progression decisions only: owner repositories retain action semantics,
external standing-authority issuance remains external, ES remains
admission/runtime/reliable-submit owner, and Bridge, MA, IM, CP, reports, and
artifacts remain non-authoritative within their exact current contracts. Model
reasoning creates cognitive proposals, but model sessions and responses are not
durable program truth or effect authority. The user steers major direction,
priorities, and risk posture and is not a routine synchronous per-attempt
approver.

The Worker Execution Boundary is reserved as the transport-neutral boundary
between Coordinator-owned durable development progression and ES-owned execution
authority. The accepted staged target places initial worker source and release
machinery in this repository, runs the worker as a separate OS process through
a bounded direct-local bootstrap/proof adapter, and later routes the same worker
artifact and versioned command/observation/fence/capsule contracts through ES.
Bridge and Bridge Core are not worker owners. Direct-local is not the target
production path and becomes disabled by default after accepted ES routing,
surviving only under a distinct proof/recovery policy.

RW0-D1 now implements only a private offline proof supervisor, separate fake
planner and coding-worker processes, bounded temporary workspace, parent-built
and independently verified capsule, and typed transient handback. The guarded
Coordinator program, author-effect, Section 41, and C1 paths remain the sole
durable owners. The repository still implements no production direct-local
adapter, dispatcher, reconciler, service/API/IPC, ES call, Bridge widening,
Codex invocation, live model/provider client, capsule store,
live validation/review/repair executor, Git effect handler, runtime-profile
integration, outbox/inbox, dispatch schema or migration, connector dependency,
or autonomous loop. D1 process mechanics own only bounded protocol, process,
ephemeral correlation, redaction, and evidence shaping. They do not own durable
work selection, scheduling policy, semantic retry or repair authority,
acceptance, ES admission, runtime lifecycle truth, Git truth, validation
truth, or hidden program state.

RW0-D2's bounded private offline D1-to-D2 implementation was independently
reviewed and introduced by commit `59621aa041a409c6ead27b74ffe25598c159e78e`. It continues
the D1 capsule with two guarded validation/review bound effects, 14 checked C1
members, separate fake validator/reviewer/model processes, exact nine-role
model input, and one typed transient preadmission handback. The guarded
Coordinator program, author-effect, Section 41 pre-execution selection, and
C1 paths retain durable authority. The local commit gate recorded no push, PR,
or merge; this records that gate, not live publication status. Git owns
committed object and ref truth. Audit, validation, provenance, and closeout
records are evidence, not Coordinator durable authority or permission to
perform effects. D2 adds no Section 41 post-execution proposal-family writer,
C1 rank-15 admission, physical C2 decision or terminal acceptance, migration
0005, live provider/Codex invocation, ES/Bridge route, production direct-local
adapter, product Git effect, or autonomous loop. The detailed owner is
`.docs/rw0-d2-offline-evidence-and-review.md`.

The bounded operational-change progression target is separate, target-only
documentation. First operational work is docs/docs-contracts only. The Worker
Execution Boundary remains coding-specific and untouched, current coding
`global_stop` behavior remains untouched, and source, schema, runtime, worker,
scheduler, reconciler, service/API/IPC, ES-call, Bridge-widening, adapter, and
gateway work remains blocked until separately authorized.

B1/B1.1 implements only secure local SQLite state-location, connection
bootstrap, observational inspection/validation, schema migration, migration
history/catalog equality, live-schema manifest verification, and schema
compatibility validation infrastructure. B1.1 inspect/validate must not create
or mutate the state root, database file, journal posture, sidecars, or schema.
B1.1 initialize/migrate are explicit operator-local administrative mutations,
but they still must not implement `StateStore` mutation semantics, acquire the
authoritative Coordinator writer, create work items/events/decision
receipts/global-stop changes through product APIs, or enable executable A2
behavior.

C2B1 remains the bounded administrative migration framework. C2B2 Slice 1 now
advances the implemented application generation to 2, extends the production
catalog and tip through `0002_development_program_and_effect_state`, and adds
that literal production SQL resource without changing migration 0001. Ordinary
inspection, validation, writer acquisition, and product
mutation admit only exact complete current history with terminal-only
application-generation compatibility and an exact cumulative packaged-SQL
schema/invariant match. Public inspection remains only
absent/empty/managed/unknown; a private nine-condition assessment makes an
exact supported non-empty older prefix eligible only for explicit
`migrate_database()`. Initialization applies the complete catalog and explicit
migration applies the complete contiguous suffix in one administrative
transaction with one planned timestamp and one commit attempt. Selected
destructive metadata is catalog-only, is not a `schema_migrations` column, and
is rejected before the common lock or writable activity. Pre-commit failures
attempt rollback; commit-attempt or unprovable-cleanup uncertainty is resolved
under the retained common lock by filesystem-bound readback as exactly
committed, definitely not committed, or unresolved. Unresolved migration
evidence raises `migration_outcome_unresolved` and forbids automatic retry or
suffix-remainder append. Cumulative packaged SQL is expected-schema authority;
history is installed-migration evidence and live schema is independently
verified observation.

Generation-2 administrative initialization and explicit migration preflight the
maximum immutable catalog capability, not only the suffix inferred from the
first observation. SQLite `3.37.0` is required before state-root creation,
common-lock acquisition, writable open, `BEGIN`, or mutation, so a permitted
reobservation cannot widen into an ungated migration-0002 effect.

C2B2 Slice 1 implements physical durable schema representability: nineteen
STRICT tables, thirty immutable guards, one partial unique index, generation-2
fresh initialization, exact 0001-to-0002 explicit migration, SQLite 3.37.0
runtime preflight, sequence-scoped zero-seed verification, and cumulative
schema verification through 0002. C2B2 Slice 2 adds exactly four private pure
no-I/O row/value modules for all nineteen tables, eighteen row self-digests,
five receipt result projections, bounded C2A reconstruction, WorkSpec safe
projection, and the common supplied-entry graph digest primitive. It adds no
SQL, private database reader, read capability, mutation API, family graph
locator or completeness proof, exact family replay, commit-outcome recovery,
or public surface within Slice 2 itself. VS1B consumes its safe values for the
private route-neutral genesis family, and C2B3D consumes the safe program,
effect, decision, receipt, and graph values for one private author-effect
family. The historical B3/B4
coherent fixture retains schema-0001 graph meanings inside a current physical
generation-2 temporary database and leaves all nineteen C2B tables empty.

C2B2 Slice 3 adds exactly two private reader source modules, seven private
aggregate/page values, twenty-four literal query specifications, twelve exact
private reader roles, and bounded 2/257 SELECT support. It uses only the
existing nominal mutation read capability. All twelve roles now have the
bounded private C2B3D caller; the mutation-receipt reader also retains the
private VS1B caller. The frozen twenty-four-query inventory is unchanged;
C2B3D's exact family-row locators and collision probes are private family-local
queries outside that inventory. Slice 3 adds no public/package/StateStore/
public-WriterSession reader surface, migration 0003, or external effect.

C2B1 adds no durable development record, reader, writer, mutation, observation
ingest, decision runtime, authority verifier, WorkSpec custody, worker/process
execution, capsule storage, Git effect, direct-local behavior, ES routing,
service, scheduler, queue, publication, or autonomous-loop authority.

Versioned Coordinator input schemas are closed-world in P1/P1.1. Unknown
fields, misspelled fields, duplicate JSON object keys, and unversioned
extension or metadata bags must fail before canonicalization or digest
comparison.

P1.1 transition persistence uses a command/event/apply-conflict algebra:
`TransitionCommand` contains caller intent, the pure evaluator produces exactly
one durable `TransitionEvent` for accepted or domain-rejected commands, and the
event is the receipt. Caller code must not provide proposed records, proposed
events, or receipts.

Expected-version mismatch is an apply/store conflict, not a durable domain
rejection. Writer fencing, internal idempotency lookup, authoritative current
state loading, expected-version comparison, evaluator invocation, exact replay,
and atomic state/event persistence belong to the atomic store boundary.

Apply conflicts never carry transition events. Exact replay requires a valid
active writer session plus the same idempotency key and the same canonical
command digest. Same key with a different digest conflicts. Stale writers
receive only `stale_writer_token` and no replay, key-existence, or conflict
detail.

Closed writer sessions and writer-session process mismatches fail locally before
the apply boundary; they are not `stale_writer_token` apply conflicts.

B2a corrects the writer authority contract only. Mutation authority is an
opaque future `WriterSession`, not a reconstructable public token. Safe writer
metadata is diagnostics/evidence only and carries no proof, proof digest, lock
path, process id, or liveness claim.

B2b implements the common state-authority advisory lock and integrates it with
SQLite initialize/migrate administration. That lock is necessary live-process
exclusion only; it is not writer authority, not a `WriterSession`, not durable
state, not a credential, and not sufficient to mutate work-item or global-stop
state. Because B2b owns a real descriptor, it includes finalizer-backed
fallback cleanup, but explicit context-manager or `finally`-based close remains
the required operational path. Descriptor opening, validation, acquisition,
registry insertion, finalizer installation, and parent close are serialized by
one lifecycle/fork gate; fork child cleanup uses a frozen descriptor snapshot,
does not acquire inherited Python locks, and closes inherited descriptors
without `LOCK_UN`. B2b still does not implement writer acquisition, proof
generation or verification, `writer_ownership` updates, a concrete
`WriterSession`, or `StateStore` mutation storage.

B2c implements durable writer issuance and internal SQLite `WriterSession`
acquisition only. It uses the B2b common lock, generates a private in-memory
32-byte proof, persists only the domain-separated proof digest, increments the
durable generation monotonically, closes the acquisition SQLite connection
before returning, and retains the common lock for the session lifetime. The
SQLite row remains latest issuance evidence only. B2 hardening rejects present
generation-zero writer rows as malformed managed state, replaces inherited
child-side session synchronization after fork, and adds a private
operation-identity guard so copied child leases no-op, explicit cross-thread
close waits for active operations, same-thread close fails locally with
`writer_session_close_during_operation`, operation leases retain the concrete
session wrapper, closing and cleaning are distinct, exactly one cleanup owner
releases proof/lock resources, closed is published only after cleanup
completion, and nonblocking finalizer cleanup may defer proof/lock release until
the last active operation exits. B2c mutation methods enter that guard and fail
locally with
`writer_session_mutation_unavailable`; no transition/global-stop event
persistence, work-item update, global-stop update, idempotency lookup,
expected-version check, service loop, worker execution, repair, commit, or
publication exists.

B3a implements contract-only prerequisites for future work-item transition
persistence. It corrects `WriterSession.apply_transition` to accept only a
`TransitionCommand`; requires future transition context to be reconstructed
inside the fenced store boundary; replaces raw lease runtime booleans with a
typed `LeaseRuntimeDecision`; aligns authorization/dependency decisions and
transition events with schema 0001 provenance; defines canonical event and
replay-record mappings; and adds a safe mutation-store error vocabulary. B3a
does not insert transition events, update work items, perform idempotency or
expected-version runtime checks, read SQLite for transition context, implement
admission or authorization verification, or widen executable A2 behavior.

B3b prerequisite contracts are pinned in
`.docs/b3b-reader-prerequisite-contract.md`. They add only pure/model authority
rules for the future typed-reader tranche: admitted backlog is mandatory
transition authority, work-item attempt/repair limits are exact standing-lease
copies, scalar persisted budget fields are zero-only reserved compatibility
fields for the first B3 slice, dependency receipts are READY-only, operational
timestamps may be retained only in internal envelopes, and schema 0001 remains
sufficient for that bounded slice. This tranche still adds no SQLite reader,
test database fixture insertion helper, transition/global-stop mutation,
admission, authorization verifier, worker, scheduler, service, CLI, MCP,
connector, repair, commit, publication, or migration 0002.

B3b1 implements only pure internal full-row contracts for already-fetched
schema-0001 row mappings and operational timestamp envelopes. It validates
lease identity, authorization, dependency, work-item, admitted-backlog, and
global-stop-current rows without SQLite I/O, readers, row cardinality,
not-found classification, fixture insertion, transition-input assembly,
idempotency/replay, event sequencing, expected-version checks, transition
mutation, or global-stop mutation.

B3b2a implements only private transaction-capability protocol and immutable
SELECT contract prerequisites for future B3b2b readers. It defines ordered
row-column tuples as the single source of row-shape truth, derives existing
row-key sets from those tuples, defines six data-only explicit-column
parameterized SELECT specifications with `LIMIT 2`, and adds a private
`_MutationReadCapability` protocol for future Coordinator mutation active
transactions. B3b2a does not execute SELECT, create cursors, fetch rows,
reconstruct B3b1 envelopes, classify cardinality or missing rows, assemble
transition input, inspect idempotency/replay/event state, own transactions or
connections, provide a concrete transaction-bound capability, accept raw SQLite
connections as reader authority, widen public `StateStore`, integrate with
`WriterSession.apply_transition`, add fixtures, mutate state, or add migration
0002. `connection.in_transaction` is not transaction identity. Future B3c must
own one opaque epoch per `BEGIN IMMEDIATE` transaction, invalidate it before
commit or rollback, and reject old epochs after transaction end or restart on
 the same connection. B3b2b readers accept only the private
capability protocol.

B3b2b implements only private, unreachable SELECT reader functions over the
B3b2a query specs. They validate lookup refs before borrowing, borrow only via
the private `_MutationReadCapability` protocol, execute parameterized
`SELECT ... LIMIT 2`, call `fetchmany(2)`, enforce bounded cardinality, require
exact built-in tuple rows, build one private mapping, delegate to B3b1 row
adapters, classify SQLite SELECT failures safely, sanitize unknown capability
borrow exceptions to the closed unavailable capability error, and close cursors
without owning the connection. Tests execute them through a clearly test-only
capability and in-memory database setup. No production caller, concrete
capability, transaction ownership, writer fencing, idempotency/replay,
cross-record assembly, missing-row apply-conflict construction, mutation,
fixture program, admission, authorization verifier, public read API,
`StateStore` widening, `WriterSession` integration, or migration 0002 exists.
B3c remains responsible for a nominal transaction capability with the B2
operation guard, `BEGIN IMMEDIATE`, writer fencing, one opaque epoch,
invalidation before commit/rollback, context assembly, evaluation, and atomic
mutation.

B3c0a pins only future transition mutation authority, ordering, fencing,
externally atomic operation-lease acquisition semantics, credential boundary,
shared transition/global-stop pre-SQLite mutation prefix,
one-mutation-per-session, capability-error, timestamp, transaction-resolution,
event-ref collision, and sequence-collision contracts in
`.docs/b3c0a-transition-authority-and-order.md`. It adds no concrete
capability, transaction controller, writer-fencing SELECT, event/replay row
adapter, idempotency reader, event-sequence SQL, coherent fixture, context
assembler, evaluator integration, transition/global-stop mutation, admission,
authorization verifier, worker behavior, public SQLite API, related-repo
integration, or migration 0002. Future concurrent mutation attempts are reserved
as the local `writer_session_mutation_in_progress` session failure; B2c still
raises `writer_session_mutation_unavailable`.

B3c0b implements only pure/static transition-event row, replay, event-owned
idempotency, and sequence contracts. It defines the exact ordered schema-0001
`transition_events` row columns, an internal hidden event/replay envelope,
canonical event/replay reconstruction and digest/index equality checks,
created-at/runtime equality, bounded zero-budget replay checks, pure
idempotency matching, immutable data-only idempotency and maximum-sequence query
specifications, and pure sequence allocation tests. B3c0b executes no SQLite
query and adds no idempotency/event/sequence reader, fixture program,
transaction capability, writer fencing, context assembly, evaluator
integration, mutation runtime, admission, authorization verifier, migration
0002, worker, service, CLI, MCP, connector, repair, commit, publication, or
deployment behavior.

B3c1 implements only prerequisite/private plumbing for rollback-only
transaction authority. It freezes the production-unintegrated/test-executed
posture, one private controller construction path, resource-owned mutation slot
and mutation-lease identity, operation-lease active-authority, resource-owned
state-database filesystem binding, durable-issuance verification interfaces,
writer-row query/parser ownership, writer-fencing classification matrix, nominal
capability/epoch contract, rollback-only lifecycle, cleanup/error precedence,
and the B3c1a/B3c1b split.
Future production invocation of that controller may occur only from
`_SQLiteWriterSession.apply_transition()`, but B3c1 gives it no production
caller; coherent tests may invoke the same private controller directly through
private imports and must not add a separate source-level `for_test` factory.
Public transition/global-stop mutation methods remain
`writer_session_mutation_unavailable` and contact no SQLite database. B3c1a
implements only the private mutation slot, `_WriterSessionMutationLease`,
operation-lease active-authority validation, resource-owned bound-database
authority, durable-issuance verification, atomic mutation-slot publication plus
lease-construction unwind, and `_WriterIssuanceMatch`. B3c1b implements only
the private rollback-only controller with an operation-lease-only entry point,
one fresh managed read/write connection opened only through the resource-owned
root/lock/database binding, `BEGIN IMMEDIATE`, post-begin binding
revalidation, managed validation, bounded `writer_ownership` SELECT, parser
reuse, writer fencing, one private nominal read capability with one opaque
epoch, permanent invalidation, rollback, close, and exact private
`_WriterIssuanceMatch` return. A matching writer row in another database is
not authority; replaced root/lock/database paths and hard-linked active
database aliases fail closed. It adds no B3b2 reader integration, context assembly, evaluator
invocation, idempotency/event/sequence reader, event insertion, work-item or
global-stop update, public API, migration 0002, admission, authorization,
worker, service, CLI, MCP, connector, repair, commit, publication, or
deployment behavior.

B3c2 implements only private transaction-internal transition-event SELECT
readers in `.docs/b3c2-transition-event-readers.md`: one idempotency-addressed
event/replay row reader and one observed maximum event-sequence reader, plus a
tiny shared private SELECT lifecycle support module used by B3b2b and B3c2.
The readers accept only `_MutationReadCapability`, reuse the immutable B3c0b
query specs, delegate event/replay integrity to
`transition_event_record_envelope_from_row(...)`, return only `None` or an
exact hidden envelope for idempotency lookup and `None` or an exact observed
non-negative integer maximum for sequence inspection, and are test-executed
through both fault-injected private capabilities and the real B3c1b nominal
capability seam. The readers now consume the neutral private
`_MutationReadCapability` protocol shared by transition and global-stop
mutation readers. The B3c2 idempotency reader locally requires exact built-in
`str` lookup refs before contract-ref validation or capability borrow, without
changing repository-wide string validation or B3b2 lookup-input semantics.
Shared SELECT support treats cursor-close failure after successful fetch as
operational cleanup (`mutation_failed`) while preserving earlier execute/fetch
failures as primary, and tests-only fork capability probes are
deadline-bounded and always reap child processes. B3c2 has no production
caller, no B3b2 context-reader call, no
matcher or allocator production call, no replay/conflict outcome ownership, no
sequence reservation or allocation claim, no public API/export/`StateStore`
widening, no event insertion, no current-state or global-stop update, no
commit, no migration 0002, and no related-repo consumer.

B3c3 contracts are pinned in `.docs/b3c3-prerequisite-contract.md`, and the
rollback-only runtime is documented in
`.docs/b3c3-rollback-only-transition-dry-run.md`. B3c3 implements only a
private, production-unintegrated transition dry run through the existing B3c1
single transaction controller and nominal capability path. It performs
command-local preflight before mutation-slot acquisition; opens one
resource-bound managed SQLite transaction with `BEGIN IMMEDIATE`; fences the
writer before idempotency disclosure; reads idempotency through B3c2; calls the
pure matcher exactly once; reads current work item; compares expected version;
reads B3b2 context rows in the exact order lease identity, admitted backlog,
authorization, READY dependency when required, and global stop; binds authority
through the frozen B3c3 helper; captures one private whole-second UTC
transaction timestamp; derives lease runtime; constructs one
`TransitionContext`; invokes the pure evaluator exactly once; returns only a
private non-durable dry-run result after capability invalidation, rollback,
close, and mutation-slot release. Fresh accepted or domain-rejected evaluator
output remains explicitly non-durable and non-receipt in the B3c3 dry run;
B3c4b is the first private tranche that can persist and commit it. B3c3
performs no maximum-sequence read, sequence allocation,
event insertion, work-item or global-stop update, CAS, commit,
`commit_outcome_unknown`, public API/export, `StateStore` widening, migration
0002, or related-repo consumer. Public mutation methods still raise
`writer_session_mutation_unavailable`.

B3c4a contracts are pinned in
`.docs/b3c4a-transition-write-and-commit-contracts.md`, and the implementation
is limited to the private pure/static
`sqlite_transition_write_contracts.py` module plus tests. B3c4a freezes the
exact transition-event insert specification, accepted work-item CAS
specification, event/replay and accepted-current value builders, private
planned write plan, then-transition-owned commit-resolution state vocabulary, SQLite
classification matrix, retry-after-uncertainty contract, proof matrix, and
B3c4c public-integration boundary. It adds no SQLite mutation execution, no
controller integration, no maximum-sequence read or allocation integration, no
COMMIT, no public `WriterSession.apply_transition()` behavior change, no
package-root export, no `StateStore` widening, no global-stop mutation, no
schema-ID bump, and no migration 0002. B3c4a fresh planned outcomes are
private grammar only and are not durable receipts unless the B3c4b private
atomic runtime successfully commits the frozen plan. B4b later moves the
commit-resolution state vocabulary to the neutral
`sqlite_mutation_transaction_contracts.py` module.

B3c4b contracts are pinned in
`.docs/b3c4b-private-atomic-transition-persistence.md`. B3c4b implements only
private atomic transition persistence through the existing single Coordinator
mutation transaction controller and nominal-capability path. It shares the
B3c3 read/evaluate
sequence, reads observed maximum event sequence only for fresh evaluations,
allocates the next sequence through the pure allocator, consumes the frozen
B3c4a write plan, inserts one transition event, CAS-updates the current work
item only for accepted transitions, invalidates the capability before commit,
attempts exactly one commit, returns fresh committed outcomes only after
successful commit and cleanup, and returns `commit_outcome_unknown` after any
commit-attempt exception. Replay and conflicts roll back and perform no write.
B3c4b owns private atomic transition persistence: there is no public
API/export, `StateStore` widening, public global-stop mutation, schema-ID bump,
migration 0002, worker, service, CLI, MCP, connector, repair, publication, or
related-repo consumer in that private runtime. B3c4c is the public transition
delegation tranche only; B4a freezes prerequisite global-stop contracts and
B4b adds private global-stop persistence only.

B3c4c public transition delegation contracts are pinned in
`.docs/b3c4c-public-transition-delegation.md`, building on
`.docs/b3c4c-prerequisite-contract.md`. `_SQLiteWriterSession.apply_transition()`
now enters the existing operation guard, performs a bounded function-local import
of the B3c4b private atomic entry and private preflight types, maps only the two
exact private preflight reasons to `TransitionApplyPreflightError`, delegates
exactly once with the operation lease and caller command by identity, and returns
or propagates the private result/error unchanged otherwise. The public wrapper
contains no SQL, transaction, sequence, event, CAS, context, evaluator,
capability, mutation-lease, or generic delegate catch-all logic; B3c4b remains
the sole atomic transaction owner and `commit_outcome_unknown` passes through.
Global-stop public delegation remains outside B3c4c; there is no
`TransitionApplyOutcome` change, `StateStore` widening, schema-ID bump,
migration 0002, B4 behavior, worker, service, CLI, MCP, connector,
publication, or related-repo authority in that tranche.

B4a global-stop prerequisite contracts are pinned in
`.docs/b4a-global-stop-prerequisite-contracts.md`. B4a adds only
global-stop-specific public preflight vocabulary, private no-I/O command and
operator-decision reconstruction, persisted operator-decision receipt and
global-stop event/replay row contracts, transaction-internal reader specs and
readers that gain only the B4b private transaction caller, table-local global-stop event sequence
allocation, receipt-binding taxonomy, and pure/static write grammar. B4a does
not provision decision receipts, make `apply_global_stop_update()`
functional by itself, widen `GlobalStopApplyOutcome` or `StateStore`, change
transition apply behavior, add schema-ID bump or migration 0002, or add worker,
service, CLI, MCP, connector, publication, or related-repo authority. Receipt
provisioning remains a separately governed operator/repo-policy integration
seam outside B4a/B4b/B4c; tests may seed receipts only as tests-only evidence
of verification mechanics, not production operator authorization.

B4b private atomic global-stop persistence contracts are pinned in
`.docs/b4b-private-atomic-global-stop-persistence.md`. B4b neutralizes the
transition-named private controller, read capability, and commit-resolution
vocabulary into one Coordinator mutation authority; preserves existing
transition entries and public transition behavior; adds only the private
`_run_atomic_global_stop_apply(...)` entry; verifies only already-persisted
operator-decision receipt rows; persists accepted and domain-rejected
global-stop events atomically; CAS-updates the global-stop singleton only for
accepted evaluations; preserves commit uncertainty and explicit retry
semantics. B4b does
not insert, provision, upsert, update, delete, import, register, or manufacture
operator-decision receipts; does not treat caller-supplied typed decisions as
authority; does not add a second controller, capability, mutation slot,
connection path, or commit state machine; does not modify schema or migrations;
and does not add cross-repository authority. Tests may seed receipt rows only as
temporary tests-only evidence of verification and persistence mechanics, not
production operator authorization.

B4c public global-stop delegation contracts are pinned in
`.docs/b4c-public-global-stop-delegation.md`. B4c makes public
`_SQLiteWriterSession.apply_global_stop_update(...)` functional only as an
operation-guarded adapter to the B4b private atomic entry. It performs bounded
function-local imports, maps only the two exact private global-stop preflight
reasons to public global-stop preflight reasons, classifies malformed private
preflight state as `database_integrity_failure`, maps import/load failure before
delegate invocation to `mutation_failed`, delegates exactly once with the
operation lease, caller command, and caller typed decision by identity, and has
no generic delegate catch-all. B4c does not add SQL, receipt provisioning,
receipt verification, evaluator logic, sequence ownership, write planning,
rollback, COMMIT, uncertainty handling, public exports, `StateStore` widening,
schema or migration changes, worker, service, CLI, MCP, connector,
publication, or related-repository authority.

B3 tests-only coherent fixtures are implemented only under `tests/`. They
create temporary current-generation-2 SQLite databases at terminal migration
0004 through production initialization, but directly seed only the historical
schema-0001 B3/B4 graph and leave all nineteen C2B core tables, all nine
cognitive proposal-selection tables, and all twenty-three RW0-C1 tables empty. The exact
physical-versus-semantic and writer-lifecycle contract is owned by
`.docs/b3-tests-only-coherent-fixtures.md`. They are not production admission,
authorization, runtime authority, product state initialization, accepted
operator-policy authority, an executable transition proof, or proof of C2B
row/value, reader, mutation, or replay behavior.

Global-stop updates use the same command/event/apply-conflict/outcome algebra.
The Coordinator cannot manufacture operator authorization and cannot clear,
weaken, or replace global stop without a typed operator decision.

C2B0 is the historical documentation-and-contract-test tranche that accepted
the target-only durable-development state contract governed by
`.docs/c2b-durable-development-state.md`. It selects the existing Coordinator
SQLite database, writer issuance/fencing authority, operation guard, mutation
slot, and transaction controller; it adds no second authority system and no
public `StateStore` or `WriterSession` surface. The closed first-slice decision
kinds are `initialize`, `accept`, `repair`, `replan`, `terminal_reject`,
`block`, `redeliver`, and `cancel`. Author-effect establishment is now one
private C2B3D transaction role; bound validation/review/cancellation-effect
establishment remains future. Private WorkSpec custody and restart-safe
retrieval remain deferred. C2B0 added documentation and direct contract tests
only. C2B1 now
implements only the administrative migration framework described above. C2B2
Slice 1 introduced the generation-2 physical schema and
`0002_development_program_and_effect_state`. The current physical terminal is
`0004_rw0_c1_durable_evidence`, still at application generation 2. Migration
0003 implements only the private Section 41 pre-execution proposal-selection
family described in Section 42 of the durable-state owner, while migration 0004
implements only the bounded private RW0-C1 durable-evidence boundary. C2B2
pure row/value source is now implemented only as the private no-I/O Slice-2
layer. Slice 3 private database readers and bounded SQL/capability use are
implemented. All twelve readers have the private C2B3D caller; the receipt
reader also has the VS1B caller. VS1B implements route-neutral program genesis,
and C2B3D implements private author-effect establishment with complete family
and bounded current-head verification, receipt-first exact replay, and
read-only three-way recovery. Bound effects, observation ingest, post-execution
progression decisions, latch behavior, external authority verification, worker/process
execution, Git effects, direct-local execution, and ES routing remain
unimplemented.

C2B3A froze the single-work-item program-initialization contract;
the bounded genesis shape is not a permanent one-work-item architecture. The
sole semantic authority is Section 35 of
`.docs/c2b-durable-development-state.md`.
`.docs/c2b3-program-initialization.md` is implementation-status and planning
only. Section 38 of the durable-state owner now governs the private VS1B
implementation on the committed C2B3A and VS1A foundation.
Sections 39 and 40 govern the private C2B3D author-effect implementation,
introduced and committed at
`5e544622e5f46ddc78294322471b4fcbd2ad9172`. Git owns the committed object and
ref fact; independent acceptance, audit, validation, provenance, and report
records remain external evidence rather than Coordinator durable authority or
effect permission. C2B3D adds no public/API/package surface, schema, migration,
external authority, route execution, worker, Bridge, or ES widening.

## P1 Prohibitions

P1/P1.1 must not implement worker execution, a scheduling loop, a queue
consumer, a daemon, repair, local commit behavior, publication, StateStore
mutation storage, a validation sandbox, executable lease authorization,
signing, keys, trust roots, public writer-credential export, or a
trusted-local/allow-all production authorization path. B2c's internal writer
acquisition is not a StateStore mutation backend and does not enable executable
A2 behavior.

P1 public state and report models must not include private briefs, raw prompts,
raw logs, credentials, secrets, local absolute paths, endpoints, platform
identifiers, or trust material.

P1 report projections must be closed typed models in `reports.py`. Do not add a
second report-shaped helper or a generic sanitize-and-keep payload boundary.

B1 SQLite bootstrap, inspection, validation, and migration errors are
administrative diagnostics only. They must not expose raw SQL, raw DDL,
absolute paths, database content, credentials, endpoints, environment, trust
material, SQLite exception text, or secrets in public payloads.

## Change Rules

Before changing authority-sensitive behavior, identify the governing invariant
in `.docs/` and keep architectural and security boundaries intact.

Do not bypass governance layers. Surface conflicts instead of working around
them.

Docs, tests, and code must change together for authority-sensitive behavior.
After changes, update `.docs/` to reflect reality and ensure there is no drift
between code and documentation.

## Vertical-slice governing narrowing

Sections 36 and 38 of `.docs/c2b-durable-development-state.md` supersede the
horizontal C2B3-C2B6 implementation order and only the finite route,
route-specific latch, active path-manifest, initialization-shape, and
migration-target selections it names. It freezes governing authority,
dependency order, prerequisites, and effect ceilings, not future schemas.

Initialization is route-neutral. First author-effect delivery uses the existing
`direct_local_bootstrap` bounded direct/non-ES route to one qualified remote
Linux host, never Mac fallback, and introduces no third adapter. At most one
productive bootstrap acceptance and one separate post-acceptance local feature-
branch commit are permitted; all publication effects remain zero and Git
ambiguity forbids blind retry.

VS1B now implements exact route-neutral initialization, the
nine-row/eight-entry genesis family, verification, replay, and readback-only
recovery. C2B3D now privately establishes the ten-row/nine-entry author-effect
family and verifies its original graph plus bounded current effect/delivery
heads. Its pending authority and planned delivery are not execution permission.
Custody, fresh external verification, invocation, later evidence, Git,
migration, bootstrap-guard physical representation, reliable-submit, and conformance designs remain deferred to
the phase that first needs them. Do not infer external-effect authorization.

## Pre-I/O VS1A cleanup invariant

Section 37 of `.docs/c2b-durable-development-state.md` is subordinate to the
unchanged Sections 35 and 36. The selected private mechanism constructs one
controller-exclusive connection scope before resource publication, requires the
exact scope-token activation acknowledgment before COMMIT, and lets the
resource select the actual successor under its lifecycle lock from immutable
controller facts and current disposal posture. The controller must not
precompute the actual successor. One lifecycle assignment is the publication
linearization point. Raw aliases clear only after exact publication
acknowledgment, while scope use is invalid immediately after assignment. QU/QK
retain the exact unproved connection and slot; PU/PK retain a connection-free
proof and no connection.

Normal exact-object `close()` return is the sole closure proof. Failure or
process control permits a later close of that same object only while proof is
absent; C2 forbids another close. Do not add `in_transaction`,
`ProgrammingError`, message matching, SQL, reopen, or reconstruction as proof.
The retained-custody owner must call the exact base close directly. The generic
transaction cleanup helper is not a proof owner, and no caller-supplied
successful callback may mint proof.

Keep resume-if-close-proved-and-still-eligible and cleanup-required as monotonic
pre-close policies; field-free `ResumeActive` is post-proof only. Disposal
before publication strengthens policy, and disposal after proof publication
atomically converts resumption to proof-backed cleanup. Classify operation-guard
uses by retained ownership. Transition and global-stop apply are the vulnerable
retained-lease paths and must keep one caller-side process-control envelope that
creates one private immutable exact-object invocation-correlation token before
their nested helpers can admit. Admission must validate the token's exact
resource, PID, and epoch, reject concurrent exact-token reuse, and bind the token
through the exact handle owned by the immutable resource record in the same
condition-protected lifecycle assignment that publishes the record. No
resource-authoritative record may be visible without the exact token binding,
and no binding may appear as admission without its record. Never derive the
correlation from the returned lease, a post-return handle store, thread identity,
state guessing, or a caller Boolean. The envelope must receive compiler-cleanup,
`__exit__`, and `_close()` escapes, including the first traceable opcode of each
internal method; do not claim either internal method protects its own first
opcode. Before poison, validate only the exact token type, its direct resource-
identity slot, and the resource's direct fork-invalid owner-PID sentinel;
acquire the existing condition, directly unwrap the exact current lifecycle
state, require the exact immutable record tuple, and compare the exact token
object by identity. Do not read a lifecycle property or
call `_state_authority`, another project helper, callback, notification, policy
computation, or successor constructor. One exact current-record match must be
followed immediately by direct poison assignment. Only after poison may
`_state_authority` and direct stored token/record/resource fields validate PID,
lifecycle epoch, authority, and record consistency; inconsistency remains
poisoned and fail-closed. Then classify represented incomplete, represented
cleanup-owned, not currently represented, or invalid/wrong resource. Absence proves
neither no admission nor final assignment and must not poison. Invalid, wrong-
resource, stale-detectable, unrepresented, or another operation's token must not
select or poison unrelated work. Classification, detailed record replacement,
successor/cursor construction, and notification must occur only after poison and
cannot reset it. Controller resolution with `_CleanupRequiredAfterResolution`
is represented cleanup-owned. The poison is non-persistent and
monotonic, blocks operation and mutation admission and every admitting successor,
never resets, and allows cleanup toward X. Only then attempt detailed record
cleanup as bounded best effort. After stabilization, use a bounded cycle-aware
sanitizer whose trusted defaults use the base descriptors obtained from
`BaseException.__dict__` for traceback, cause, context, args, and the base
instance dictionary, plus the `BaseExceptionGroup.__dict__` descriptor for
children. Clear each base traceback before reading its other fields. Recursively
follow only `BaseException` values in exact built-in tuple, list, dict keys and
values, set, and frozenset containers; ordinary notes are covered only through
the base dictionary. Never invoke subclass-defined dynamic descriptors,
arbitrary subclass slots, arbitrary user-object attributes, or custom container
iteration. Preserve exact object and cause/context identity, type, args,
`SystemExit.code`, suppression, notes, group children, and ordinary dictionary
content, then bare-reraise; do not use `raise governing` or reconstruct the
exception. Bound one ordinary primary-pass failure and one ordinary replaceable
sanitizer-call failure with a fresh default-bound non-dispatching pass so neither
can replace the outward exception. Do not claim survival of repeated
asynchronous interruption or catastrophic allocation failure. Local
stabilization failure must remain secondary. Preserve wrong-PID and fork-child
non-authority. The `require_usable_for_mutation` guard is a distinct already
fail-closed ephemeral/unbound-lease use. Preserve its last-reference loss and
finalizer-driven X at the reproduced compiler boundary without requiring an
outer envelope or poison; prepare its reachable exit paths as non-admitting. The
resource lifecycle state is the sole owner of one immutable admission record per
operation. The record copies exact resource identity, operation number, PID,
owner thread, and lifecycle epoch and owns the admitted handle, lease weak
reference, finalizer identity, payload-free cleanup fence, retirement phase,
and condition-created acknowledgments. Handle-side binding fields are
compatibility observations only and must never supply authority. Read and
replace the record only under the existing lifecycle condition lock; never
reset cleanup-required or store the exception.

Phase 1 must retain the exact record, validate exact mutation release, record
one preparation acknowledgment, and make or keep the resource non-admitting.
Only plain mutation-active/closing retirement may defensively release its exact
slot; controller close-proved release ownership stays unchanged. A sole cleanup
blocker must use the existing cleanup claim and remain represented through
credential/lock cleanup. Normal retirement has exactly one owner: the live
lease already bound in the resource record. Under the resource condition, that
lease must validate the record and preparation, record local terminality, call
`detach()` on the exact admission-bound finalizer, and record
`EXPLICIT_RETIRED` only from that exact call's successful return. A merely dead
finalizer, `.alive == False`, weak-reference clearing, GC, object loss, or a
caller-built acknowledgment is never normal-retirement evidence.

Finalizer execution, direct invocation, and lease or wrapper loss before
`EXPLICIT_RETIRED` must classify orphan cleanup, keep admission frozen, and use
existing cleanup continuation toward X without restoring Active. Loss after
`EXPLICIT_RETIRED` adds no authority: only the stored phase may finish the
already-authorized publication, and current disposal still wins. Phase 2
directly rechecks the resource-owned record and performs one final lifecycle
assignment under the same condition. That assignment—not Python method return—
is operation-completion authority. Pre-assignment process control keeps the
record represented and cleanup-directed; post-assignment process control
preserves the assigned state as caller response loss. No local or resource
authority mutation may follow the final assignment on the normal path.

Do not reintroduce a broad optional lifecycle snapshot or arbitrary completed-
step set; exact closed variants and finite structural cursors own the relation.
Authority/operations, slot, resolution, custody/proof, cleanup cursor, cleanup
claim, binding/lock, and terminal state must each have one structural owner;
reject cross-wired construction. Allocate exactly one private opaque resource
identity per writer resource and bind it through authority/activity, operation,
slot/frame, controller token, connection custody/retained connection/proof,
every cleanup cursor, cleanup claim, and cleanup state. Compare it only by `is`.
Do not persist, serialize, register globally, export, log, render, or include it
in safe errors; PID/epoch equality is not resource authority.

Construct the operation completion handle, lease, finalizer, lease-loss callback,
and immutable resource record before active publication, with exact idempotent
unwind on every `BaseException`. Bind the record to the exact lease weak
reference and exact finalizer; never reconstruct completion from weak-reference
or finalizer state. Absent and never-published records must reject publication,
while post-assignment internal retry stops at record absence and leaves semantic
response-loss recovery to existing transition/global-stop replay. After exact
successful detach and resource-recorded `EXPLICIT_RETIRED`, but before final
assignment, retain the live explicit lease as a retry owner. If it disappears,
its callback may finish only from the already-stored phase. Explicit resource
close and the session finalizer remain cleanup callers, not normal-retirement
proof owners. Do not add a completion receipt, registry, scanner, or background
service. Cleanup claims use a weak reference to the exact
live `threading.Thread`, never a recyclable integer identifier. Another live
Thread or process cannot steal a claim; a dead owner requires explicit takeover
with a new token and epoch.

Keep the deterministic real-session disposal selector at the exact phase after
mutation release and before operation completion. It must make disposal current
with barriers, preserve the outstanding operation, reject new admission, and
reach X without exposing an intermediate Active state.

Safe-error privacy uses that same supported base-storage and exact-built-in-
container boundary; it does not extend to dynamic subclass descriptors,
arbitrary slots or user-object attributes, or custom iterators. Sensitive
frames return a private disposition carrying one exact content-free store error.
Through each genuine bound transition/global-stop operation guard, clear
prohibited bindings before the outer boundary catches, validates, sanitizes, and
bare-reraises that same object by identity without process-control poisoning;
reject subclassed, malformed, noted, or content-bearing candidates, and never
convert governing process control into the safe-disposition path. Transition and global-stop
privacy probes use separate real cursor-producing idempotency SELECT faults,
really close the exact built-in cursor, and cover cursor, database path and
resolved string, SQL, and parameters by identity and exact built-in value.

After a normal transaction-connection close with no pending explicit disposal
or orphan cleanup, release the mutation and operation and restore the same
wrapper to active. A later explicit transition/global-stop call must use a new
operation lease and fresh connection, applying fresh when no commit occurred or
returning exact replay after an underlying commit. Use the same explicit fresh/
replay/conflict rules for response loss after the final operation assignment.
Never retry automatically or duplicate durable effects. QU/QK retained custody, pending disposal, and
governing process-control cleanup remain non-reusable. Do not generalize
VS1B's fresh-writer recovery gate to old-session reuse or to any claim about an
old resource's terminal state. A fresh concrete writer may recover or replay
only after independent acquisition and writer fencing. In the same process,
H2 registry removal permits that acquisition before old T1; in a different
process, L1 kernel-lock release may permit it before old-process H2 or T1.
Existing transition/global-stop replay remains unchanged.

P0/C1/C2/R1/R2/R3/L1/H1/H2/T1/H3, lock release and descriptor reclamation,
transition/global-stop replay, fork non-authority, and finalizer posture remain
governed by Sections 35 and 37. VS1A is committed at
`4ffbc5f8881339dce210a50b05200e3f8e837284`; VS1B changes none of those
mechanics. Section 38 owns the private program-genesis mutation and the finite
same-/cross-process acquisition clarification. It adds no schema, migration,
public surface, worker, scheduler, service, model, Git, Bridge, ES, network, or
publication behavior.

The B3c1a contract-projection test retains its existing node ID and replaces
only the obsolete post-GC Active expectation: loss before `EXPLICIT_RETIRED` is
`ORPHANED`, non-admitting, cleanup-owned, and eventually X. The B3c1b test-file
change is explicit test-owned SQLite connection-lifetime
hygiene only. Setup and ledger ownership must close the exact connection on
every setup, expected-error, assertion, and cleanup exit. Preserve its rollback-
only result, fencing, mutation-slot, and error-precedence semantics; use no
warning suppression.

The B3c3 test-file change is only a private rollback-only regression adaptation
to the selected close-proof owner. It observes and delegates to the sealed
retained-custody proof owner, never the generic cleanup helper; preserves no
COMMIT, no commit-unknown result, ordinary rollback-only ordering, and close-
unproved custody until explicit cleanup; and adds no result, durability, public,
or authority widening.

The unchanged B2b issue remains pre-existing test-resource hygiene and is not
VS1B authority or behavior. Do not suppress its warning or change its
semantics. The committed VS1A B3c1a contract replacement and B4b
zero-Coordinator-frame privacy contract remain unchanged.

Keep production-causal runtime cases, compiled complete-module source mutants,
and secondary AST/source guards as distinct evidence classes. The shared-
foundation test is their owning surface and owns one literal tuple as the sole
focused-selector inventory. Compute report counts from those selected node IDs;
do not repeat mutable totals as architecture. Every source mutant must use an
external source copy, parse, compile, import the complete writer module, reach
the intended production path, fail causally, and leave the live repository
unchanged. Every runtime case must assert its production seam was reached; the
two direct-finalizer cases target the orphan-mark and cleanup-successor seams.
Exact commands, warning counts, overlaps, and validation-group file inventories
belong to the implementation and audit reports. Give no causal credit to a
duplicate, no-op, or unreached owning seam.

VS1B is the current committed private implementation at
`327aa4ef6f043a94f700374546fedc456027ae83` and is pushed to the directly
verified `origin/trunk_dev` ref. The exact VS1B pre-commit candidate received
externally classified, provenance-bound independent acceptance and its
post-acceptance commit gate passed. Git owns the commit/ref fact; the audit and
validation reports remain external evidence rather than Coordinator durable
authority. The C2B3C contract freeze is committed at
`5945a53685e7a5cb4edd7419bea712007fcdfcd1`. The private C2B3D author-effect
implementation was introduced and is committed at
`5e544622e5f46ddc78294322471b4fcbd2ad9172`. Git owns the committed object and
ref fact; independent acceptance, audit, validation, provenance, and report
records remain external evidence rather than Coordinator durable authority or
effect permission. C2B3D adds no worker, dispatch, credential, capsule, Git,
Bridge, ES, network, or other external effect. VS1B and C2B3D use migration
0002 and add no public API/package export, automatic retry after uncertainty,
old-resource lookup, terminal witness, or restart-safe raw-input custody.

<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_BEGIN -->
## Cognitive proposal and selection runtime

Section 41 of `.docs/c2b-durable-development-state.md` remains the sole detailed
semantic owner; Section 42 records current implementation and
repository-publication status without redefining it. C2B3D private author-effect
establishment is committed at
`5e544622e5f46ddc78294322471b4fcbd2ad9172`. Migration
`0003_cognitive_proposal_and_selection_state` and the private pre-execution
proposal-selection runtime are committed at
`394d625aa63935140eeaf88ecff6f59f0547cb7e`. Git owns committed object and ref
truth; independent acceptance, audit, validation, provenance, and report
records remain external evidence rather than Coordinator durable authority or
effect permission. The source tranche ends at typed pre-execution proposal
admission plus Coordinator selection or non-selection. It performs no
model/provider invocation, dispatch, worker contact, post-execution
validation/review execution, post-execution Coordinator semantic decision,
capsule custody, Git effect, Bridge or ES handoff, publication execution,
service, scheduler, queue, or autonomous loop. The full remote-worker phase is
not reduced to this private source tranche.
<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_END -->

<!-- RW0_C1_CURRENT_STATUS_BEGIN -->
**RW0-C1 durable evidence current status.**

RW0-C1 is now a `CURRENT IMPLEMENTED CONTRACT`. Generation 2 now terminates at
`0004_rw0_c1_durable_evidence`; migration 0004 adds exactly twenty-three STRICT
tables, forty-six immutability triggers, four explicit indexes, and zero seed
rows. The cumulative managed schema is sixty-two user tables, one hundred ten
triggers, and five explicit indexes.

The private concrete SQLite writer session now delegates phase establishment,
single-member evidence admission, and their explicit three-way recovery to the
one existing Coordinator mutation transaction controller. The fixed inventory
is fifteen evidence kinds. Replay is receipt-first after fencing; fresh writes
use full in-transaction readback, one commit attempt, and explicit
`committed_exact` / `definitely_not_committed` / `unresolved` recovery.
Historical verification uses persisted semantic time and phase-local immutable
snapshots, never the current clock or later mutable heads.

C1 adds no public `StateStore`, public `WriterSession`, or package API and owns
no completeness, C2 decision, latch, terminal outcome, source authentication,
external permission, worker/process/runtime authority, or external contact.
Any earlier unqualified statement that groups all RW0-C durable mechanics as
future is historical and superseded only for this bounded C1 boundary; later
RW0-C closure/decision work and RW0-D/E remain future.
<!-- RW0_C1_CURRENT_STATUS_END -->

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

<!-- RW0_D1_CURRENT_STATUS_BEGIN -->
RW0-D1 is a current private artificial offline process and capsule proof. The guarded Coordinator program-initialization, C2B3D author-effect, Section 41 selection, and RW0-C1 phase writers remain the sole durable owners. A separate fake planner and fake coding worker run under the bounded D1 supervisor; the parent captures one temporary candidate, builds and independently verifies a CandidateCapsuleManifestV1, removes the mutable workspace, and returns a transient typed handback with separate parent-only disposable-state custody. The preassigned fixture base_git_oid is a WorkSpec coordinate, not Git authentication. RW0-D2 validation/review/model closure is next; RW0-C2 physical decision persistence follows D2. D1 grants no live provider/credential or source authentication, ES route, Git/publication effect, terminal acceptance, public service/CLI, or RW0-E runtime authority. The detailed implementation owner is .docs/rw0-d1-offline-process-and-capsule-spine.md.
<!-- RW0_D1_CURRENT_STATUS_END -->

<!-- RW0_D2_CURRENT_STATUS_BEGIN -->
RW0-D2's bounded private offline evidence and cognitive-review implementation
was independently reviewed and introduced by commit
`59621aa041a409c6ead27b74ffe25598c159e78e`. The D1 capsule remains the
author/checking boundary. Two guarded validation/review bound effects, 14
checked C1 members, three separate fake validator/reviewer/model processes,
exact nine-role input, and one typed transient preadmission handback form this
artificial proof. The guarded Coordinator program, author-effect, Section 41
pre-execution selection, and C1 paths retain durable authority. The local
commit gate recorded no push, PR, or merge; this records that gate, not live
publication status. Git owns committed object and ref truth. Audit,
validation, provenance, and closeout records are evidence, not Coordinator
durable authority or effect permission. This successor supersedes only the D1
sentence placing D2 closure in the future. It adds no Section 41 post-execution
proposal-family writer, C1 rank-15 admission, physical C2 decision or terminal
acceptance, migration 0005, live provider/Codex invocation, ES/Bridge route,
production direct-local adapter, product Git handler, or autonomous loop.
`preadmission_ready` is not acceptance. The detailed owner is
`.docs/rw0-d2-offline-evidence-and-review.md`.
<!-- RW0_D2_CURRENT_STATUS_END -->

<!-- POST_D2_NATIVE_PROPOSAL_ADMISSION_CURRENT_SUCCESSOR_BEGIN -->
### Post-D2 native proposal admission successor

The adjacent private post-D2 offline continuation calls the original D2 run
once, records one native Section 41 post-execution proposal/context/receipt
family in transaction A, checks the committed twelve owner rows in a fresh
guarded session, then uses a distinct C1 transaction B to admit exactly one
rank-15 member. Fresh guarded readback of both families feeds unchanged pure
V22 projection. The original D2 entry and `preadmission_ready` meaning remain
as documented above. The five model recommendations remain evidence only.

The current additive production catalog now ends at
`0005_section41_post_execution_proposal_family`, still at application
generation 2 with SQLite 3.37.0 minimum. Migration 0005 adds exactly two
immutable STRICT tables, four guards, no explicit index or seed, giving 64
user tables, 114 triggers, and five explicit indexes cumulatively. Existing
0004 states require explicit administrative migration before normal writer
admission; normal validation, acquisition and mutation do not auto-migrate.
Earlier current-tip and absent-0005 statements in this file describe the
historical D2/C1 tranches and are superseded only for this additive successor.

The owning contract is `.docs/section41-post-execution-proposal-family.md`,
incorporated by Section 41 in `.docs/c2b-durable-development-state.md`.
The proof retains only a closed safe basis, uses the original process-owned
temporary state, and provides read-only three-way recovery after uncertain A
or B commits. It adds no C2 decision, acceptance, terminal outcome, executable
permission, real custody, restart/clone recovery, live provider/worker, ES or
Bridge route, Git effect, publication, service, scheduler, or autonomous loop.
This source successor is not an independent audit or deployment assertion.
<!-- POST_D2_NATIVE_PROPOSAL_ADMISSION_CURRENT_SUCCESSOR_END -->

<!-- POST_D2_UNIT2_CURRENT_SUCCESSOR_BEGIN -->
### Post-D2 Unit 2 bounded evidence successor

The current private offline D2 A path accepts exactly two Worker Wire observation
orders: `worker_started, worker_completed` and `worker_started,
candidate_captured, worker_completed`. The parent captures and verifies the
candidate capsule in either case; omission of the optional worker-authored
`candidate_captured` observation makes no claim that the parent did not capture
a candidate. `worker_completed` still carries no candidate or capsule
conditional fields. The checked C1 A families have exactly 13 or 14 members,
respectively, with rank sequences `(12, 12, 12, 13, 14, 1, 1, 5, 6, 12, 6,
12, 1)` and `(12, 12, 12, 12, 13, 14, 1, 1, 5, 6, 12, 6, 12, 1)`. One private
layout resolver anchors role positions and reached prefixes to the actual D1
Wire result. Pure V40 reviewer separation binds the parent capsule, the
rank-13 worker-result candidate, and the review observation in both layouts;
only the three-observation layout reads a `candidate_captured.candidate_ref`.

A clean, reaped validator or reviewer child whose closed checking response is
invalid stops with `validator_evidence_invalid` or
`reviewer_evidence_invalid`, respectively. The returned handback retains the
exact prior checked prefix and child outcomes without admitting the bad
observation or launching a later child. Process failure, cleanup failure, and
programming faults retain their separate handling. The native Section 41 fresh
writer derives one command and canonical safe basis from the original open D2
run and requires complete equality before route probing or target writes.
Receipt-first historical replay and checked readback use the persisted family
without rerunning children or requiring present process custody. The existing
three-observation command and safe-basis bytes remain unchanged.

This bounded implementation is pending independent review. It adds no C2
decision, acceptance, executable permission, live provider or ES route,
production worker, Git effect, publication, or autonomous loop.
<!-- POST_D2_UNIT2_CURRENT_SUCCESSOR_END -->

<!-- POST_D2_CUMULATIVE_LOCAL_COMMIT_CURRENT_SUCCESSOR_BEGIN -->
### Post-D2 cumulative local-commit status successor

The bounded post-D2 implementation in the exact sealed tree
`3965cd3d1d3e28b43c9bc3709058c2524bad369d` was independently reviewed
for a separately governed commit gate. That gate locally committed those
bytes as `66ee79132501e636d848ff8578fb674a208d6ac5`, reauthenticated all
299 committed blobs and Git modes, and recorded 9,295 collected and 9,295
passing tests, zero failures, errors, or skips, and three known Python 3.13
fork deprecation warnings. The earlier Unit 2 pending-review sentence remains
historical candidate-stage evidence and is superseded only for review and
local-commit status.

The gate performed no push, PR, merge, publication, deployment, or product
effect. This is a historical local-gate statement, not a live remote-ref or
publication claim. Git objects and refs remain authoritative for current
commit and publication truth. Audit, validation, provenance, reports, and
status text remain evidence, not Coordinator durable authority or permission
to perform effects. The artifact-only audit did not certify live Git state;
the gate proves only its prospective opening-to-commit interval. Earlier
raw-index and diagnostic-ref provenance gaps remain unresolved history. F03
remains a nonblocking private-constructor observation; F2 and qualified
F3/F6/F7 findings, cross-host clock ordering, and future live concerns are
not claimed closed.

This implementation adds no live custody, physical C2 decision or acceptance,
terminal outcome, executable permission, production provider or worker
readiness, ES or Bridge route, product Git authority, service, scheduler, or
autonomous loop. The original D2 entry and Unit 2 behavioral boundaries above
remain unchanged.
<!-- POST_D2_CUMULATIVE_LOCAL_COMMIT_CURRENT_SUCCESSOR_END -->

<!-- RW0_C2_P0_PHYSICAL_CANDIDATE_BEGIN -->
## RW0-C2 P0 physical candidate boundary

In the current uncommitted artificial-offline candidate, migration 0006 and
private P0 source record one independently verified program-independent safe
admission act/fact family under the existing guarded writer controller. P0
retains its own receipt, replay, and recovery and creates no program, C2
decision, acceptance, terminal, or executable permission. The selected P1
continuation is separate and must not rewrite P0 semantics. Fake source
evidence does not satisfy live supplier/custody gate B or close F2.
<!-- RW0_C2_P0_PHYSICAL_CANDIDATE_END -->

<!-- RW0_C2_P1_PHYSICAL_CANDIDATE_BEGIN -->
## RW0-C2 private P1 physical candidate boundary

The P0 block above is an exact historical checkpoint. The current uncommitted
artificial-offline candidate adds migration 0007 and a separate private P1
writer for five guarded progression branches, exact whole-family replay, and
three-way recovery. Replan CAS-updates both program and work heads and retains
their typed historical postimages in the v2 guarded relation; acceptance alone
records an immutable acceptance fact. P0's two private production owners and
migration 0006 remain unchanged. There is no public P1 route, live supplier,
terminal owner, worker, ES/Bridge route, product Git effect, or executable
permission. The detailed owner is
`.docs/rw0-c2-physical-p0-p1-implementation.md`.
<!-- RW0_C2_P1_PHYSICAL_CANDIDATE_END -->

<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
## RW0-C2 P0/P1 accepted local implementation status

The preceding P0 and P1 candidate blocks are exact historical checkpoints.
Independent artifact audit accepted Git-compatible tree `161ed4b544baf970cc26428b9805a106ea0f3edf`. The exact
implementation was committed locally as `8704e6c7988250598809f3a0daf88c3e11493488` with sole parent `4519630d0db967066beb21b4ace5004e76827716`
on `codex/rw0-c2-p0-p1-physical-program-v1`, without an upstream. The local
commit gate collected, executed, and recorded 9,473 passing JUnit cases in
identical order, with three known Python 3.13 multithreaded-fork
`DeprecationWarning` records and no failures, errors, or skips. No push, PR,
merge, publication, deployment, or product effect occurred. Git objects and
refs own commit and publication truth; audit, validation, and status records
are evidence only. The bounded private artificial-offline P0 and P1 source
remains separate fenced transactions: P0 records admission history without
current permission, and P1 records one five-branch decision with an acceptance
fact only on acceptance. Decision Basis v2, guarded-command-digest v2, the
historical work-head witness, universal disclosure, and acceptance-only
eligibility are current private contracts. F03 and F05 remain nonblocking
observations. No live custody supplier, terminal outcome, executable
permission, production provider/worker, ES/Bridge route, product Git effect,
service, queue, scheduler, or autonomous loop follows. The current owner is
`.docs/rw0-c2-physical-p0-p1-implementation.md`.
<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure current candidate

The uncommitted `artificial_offline_normal.v1` candidate adds a separate private Coordinator terminal writer on generation-2 migration 0008. It consumes checked P0, phase, Section 41 A, C1 rank-15/V22 and P1 evidence under one fenced transaction and records only the five normal outcomes: accept, repair, replan, terminal_reject and block. The P1 decision remains prior decision history; its acceptance fact is bound only for accept and is never mutated. Cancellation, live supplier/contact, ES routing, Git effects, publication and executable permission remain outside this candidate. See `.docs/rw0-terminal-outcome-physical-closure.md`.

The original P1 command remains a transient required operand, including private replan text. Fresh record requires current recording and disclosure; historical read/replay/recovery require disclosure only. The current catalog tip is 0008, with 78 tables, 142 triggers and five explicit indexes. Independent audit remains pending.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure local commit status

The exact cumulative independent audit accepted Git-compatible tree `4691af58ae0ee3107b4e2e9b6b1508032944e357` for an exact-byte commit gate after its current-ledger consistency repair. The private `artificial_offline_normal.v1` implementation was locally committed as `d3fd741c872b26aa2dfe927ab6dccc638cdcf356`, with sole parent `61d0330aba1160f7f5e7d9c541a325222d1c61e5`, that exact tree, and subject `feat: add RW0 normal terminal closure`. The staged-blob gate collected and passed 9,568 selector-free tests in the same order, with zero failures, errors, skips, xfails, or xpasses and only the three known Python 3.13 multithreaded-fork deprecation warnings. This is a local topic-branch commit; no push, PR, merge, publication, deployment, service/runtime contact, or product effect followed.

Migration `0008_rw0_terminal_outcome` is the current source/catalog suffix. The private fenced terminal owner records only normal `accept`, `repair`, `replan`, `terminal_reject`, and `block`. P0 scope admission, P1 progression decision with its acceptance-only fact, and terminal closure remain separate private fenced transactions and facts. P0 grants no current permission; P1 is prior decision history, not terminal truth. Normal accept binds the immutable acceptance fact without mutation or replenishment.

Common managed-store admission may shape-check the current global-stop singleton before writer fencing. After fencing and protected disclosure, receipt-present terminal read, replay, and recovery verify saved full head postimages, saved stop, and immutable P0/Section 41/C1/P1 predecessors without today's mutable-head or semantic stop checks. A fresh receipt miss retains current-head, current-stop, recording, and disclosure checks. The old whole-operation zero-current-stop-SELECT audit failure remains historical; the accepted two-layer rule supersedes only that overbroad requirement.

Git objects and refs own commit and publication truth. Audit packages, reports, validation, this status text, WA1/QtcM evidence, and provenance are evidence only. The local commit adds no executable permission, three cancel selectors, live supplier/custody gate, worker/provider or physical remote contact, ES/Bridge route, product Git-effect handler, service, queue, scheduler, deployment, or autonomous loop. Existing F03/F05 nonblocking provenance limits retain their recorded scope; this status does not claim their repair. Candidate-stage status elsewhere in this document is preserved history; this marked block is the current local status.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_POST_MERGE_STATUS_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure integrated capability status

Classification: `CURRENT INTEGRATED CAPABILITY STATUS`.

RW0 normal terminal closure was integrated into `trunk_dev` by squash commit `3be0096c163b456c9975326be3eb2c30d2b4bbd1`, with sole parent `61d0330aba1160f7f5e7d9c541a325222d1c61e5` and integrated capability tree `bc10382edd1b2c097fc729e4e168d72e710391fe`. This is the integration anchor for the accepted private `artificial_offline_normal.v1` source. The commit containing this status-only successor is intentionally not self-identified here; Git objects and refs own the current containing commit and publication truth.

The integrated capability records only normal `accept`, `repair`, `replan`, `terminal_reject`, and `block`. P0 scope admission, P1 progression decision with its acceptance-only fact, and terminal closure remain separate private fenced transactions and facts. Migration `0008_rw0_terminal_outcome` remains the source/catalog suffix. P0 grants no current permission; P1 remains prior decision history rather than terminal truth; normal accept binds the immutable acceptance fact without mutation or replenishment.

The accepted implementation staged-tree gate passed 9,568 / 9,568 tests. The accepted status staged-tree focused gate passed 5,655 / 5,655 tests. Independent artifact review accepted the exact status tree `bc10382edd1b2c097fc729e4e168d72e710391fe`. The accepted 9,597-test selector-free FULL record was carried evidence on that tree and was not rerun during integration. No tests ran during the integration operation itself. These records are evidence at their stated scopes, not current Git or runtime authority and not validation of this later status-only correction.

All earlier candidate-stage, local-commit-stage, and cross-stage status passages in this document are preserved historical evidence. Their statements that the implementation was uncommitted, only a local topic-branch commit, or followed by no push, PR, merge, or source publication are stage-local and are not current repository status after the integration anchor above.

The integrated source adds no active-cancel terminal family or executable permission; no live supplier/custody, worker/provider, or physical remote contact; no ES/Bridge route; no Coordinator-owned product Git-effect or runtime publication authority; and no service, queue, scheduler, deployment, or autonomous-runtime loop. Source publication by Git merge does not establish any of those product capabilities. Existing F03/F05 nonblocking provenance limits retain their recorded scope and are not repaired by this status correction.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_POST_MERGE_STATUS_SUCCESSOR_END -->
