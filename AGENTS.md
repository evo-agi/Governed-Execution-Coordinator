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

This repository currently implements no direct-local adapter, worker
supervisor, worker process, dispatcher, reconciler, service/API/IPC, ES call,
Bridge widening, Codex invocation, model/provider client, capsule builder or
store, validation/review/repair executor, Git effect handler, runtime-profile
integration, outbox/inbox, schema or migration for dispatch, connector
dependency, or autonomous loop. Future adapter and supervisor mechanics may own
only bounded protocol, process, ephemeral correlation, redaction, and evidence
shaping. They must not own durable work selection, scheduling policy, semantic
retry or repair authority, acceptance, ES admission, runtime lifecycle truth,
Git truth, validation truth, or hidden program state.

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

C2B2 Slice 1 implements only physical durable schema representability: nineteen
STRICT tables, thirty immutable guards, one partial unique index, generation-2
fresh initialization, exact 0001-to-0002 explicit migration, SQLite 3.37.0
runtime preflight, sequence-scoped zero-seed verification, and cumulative
schema verification through 0002. It adds no C2B2 pure row/value module,
private reader, mutation API, family graph locator, exact family replay,
commit-outcome recovery, public surface, or C2B3 behavior. The historical B3/B4
coherent fixture retains schema-0001 graph meanings inside a current physical
generation-2 temporary database and leaves all nineteen C2B tables empty.

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
0002 through production initialization, but directly seed only the historical
schema-0001 B3/B4 graph and leave all nineteen C2B tables empty. The exact
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
`block`, `redeliver`, and `cancel`. Author-effect establishment and bound
validation/review/cancellation-effect establishment are separate future private
transaction roles. Private WorkSpec custody and restart-safe retrieval remain
deferred. C2B0 added documentation and direct contract tests only. C2B1 now
implements only the administrative migration framework described above. C2B2
Slice 1 now implements the generation-2 physical schema, and
`0002_development_program_and_effect_state` is the implemented current physical
terminal migration. Migration 0003 remains unimplemented and deferred. C2B2
pure row/value source and private readers, C2B mutation, replay, and recovery,
observation ingest, decisions, latch behavior, authority verification,
worker/process execution, Git effects, direct-local behavior, and ES routing
remain unimplemented. C2B3 has not started.

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
