# NWP Coordinator Agent Rules

If `.docs/` exists, always treat `.docs/` as the source of truth.

## Ownership

This repository owns the future A2 coding-work durable state contract only.
Current P1/P1.1 code has no production durable store and no active durable
writer.

Bridge remains the guarded worker/evidence adapter. Control Plane remains
product workflow authority. Execution Substrate remains product admission and
runtime authority. Maintenance Agent remains maintenance authority.
Infrastructure Manager remains readiness, provenance, and diagnostics
authority.

Operator/repo policy owns lease issuance and global stop. The coordinator
cannot self-authorize, cannot mint authorization, and cannot treat a valid
digest as execution permission.

Transition commands, transition events, writer-session contracts,
global-stop commands, and global-stop events are contract objects only until a
future backend tranche. Reports are projections only. They are not durable
state, authorization, acceptance, publication, or product truth.

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
`_TransitionReadCapability` protocol for future B3c-managed active
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
the private `_TransitionReadCapability` protocol, execute parameterized
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
The readers accept only `_TransitionReadCapability`, reuse the immutable B3c0b
query specs, delegate event/replay integrity to
`transition_event_record_envelope_from_row(...)`, return only `None` or an
exact hidden envelope for idempotency lookup and `None` or an exact observed
non-negative integer maximum for sequence inspection, and are test-executed
through both fault-injected private capabilities and the real B3c1b nominal
capability seam. The B3c2 idempotency reader locally requires exact built-in
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
planned write plan, commit-resolution state vocabulary, SQLite
classification matrix, retry-after-uncertainty contract, proof matrix, and
B3c4c public-integration boundary. It adds no SQLite mutation execution, no
controller integration, no maximum-sequence read or allocation integration, no
COMMIT, no public `WriterSession.apply_transition()` behavior change, no
package-root export, no `StateStore` widening, no global-stop mutation, no
schema-ID bump, and no migration 0002. B3c4a fresh planned outcomes are
private grammar only and are not durable receipts unless the B3c4b private
atomic runtime successfully commits the frozen plan.

B3c4b contracts are pinned in
`.docs/b3c4b-private-atomic-transition-persistence.md`. B3c4b implements only
private atomic transition persistence through the existing single transaction
controller and nominal-capability path. It shares the B3c3 read/evaluate
sequence, reads observed maximum event sequence only for fresh evaluations,
allocates the next sequence through the pure allocator, consumes the frozen
B3c4a write plan, inserts one transition event, CAS-updates the current work
item only for accepted transitions, invalidates the capability before commit,
attempts exactly one commit, returns fresh committed outcomes only after
successful commit and cleanup, and returns `commit_outcome_unknown` after any
commit-attempt exception. Replay and conflicts roll back and perform no write.
B3c4b remains private and production-unintegrated: public
`_SQLiteWriterSession.apply_transition()` still raises
`writer_session_mutation_unavailable`; there is no public API/export,
`StateStore` widening, global-stop mutation, schema-ID bump, migration 0002,
worker, service, CLI, MCP, connector, repair, publication, or related-repo
consumer. B3c4c remains future for public transition delegation. B4 remains
future for persistent global-stop updates.

B3 tests-only coherent fixtures are implemented only under `tests/`. They
create temporary managed schema-0001 SQLite databases through production
initialization, directly seed synthetic authoritative rows through a test setup
transaction, validate rows through existing pure contracts, acquire real
internal writer issuance as temporary test evidence, and may persist only a
domain-rejected event/replay row produced by the pure evaluator. They are not
production admission, not authorization, not runtime authority, not product
state initialization, not accepted operator-policy authority, not an executable
transition proof, and not migration 0002.

Global-stop updates use the same command/event/apply-conflict/outcome algebra.
The Coordinator cannot manufacture operator authorization and cannot clear,
weaken, or replace global stop without a typed operator decision.

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
