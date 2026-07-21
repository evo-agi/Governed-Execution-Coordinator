# Durable State Model

A2-P1/P1.1 defines state contracts. B1/B1.1 adds explicit operator-local
SQLite bootstrap, observational validation, live-schema integrity checks, and
migration infrastructure. B2a corrects the writer-session authority contract.
B2b adds the common state-authority lock for initialize/migrate administration.
B2c adds durable writer issuance and an internal concrete SQLite
`WriterSession`. B3a adds canonical persistence and provenance contracts only.
B3b2a adds private capability-protocol and query-contract prerequisites.
B3b2b adds private SELECT readers over those specs with no production
integration. B3c0a adds contract/static pins for future transition authority,
ordering, fencing, and failure precedence only. B3c0b adds pure/static
transition-event row, replay, event-owned idempotency, and sequence contracts
only. B3c1 adds contract/static pins for the production-unintegrated
rollback-only controller posture plus B3c1a private mutation slot,
operation-lease authority checks, durable-issuance verification, writer
fencing result vocabulary, nominal capability epoch, cleanup precedence, and
B3c1a/B3c1b split only.
B3c2 adds private transaction-internal transition-event SELECT readers and
shared private SELECT lifecycle support only; it remains production-unintegrated
and mutates no durable state.
B3c3 adds only a private rollback-only dry run. It implements
result/preflight/binding/timestamp/cleanup boundaries, idempotency and context
reader ordering, expected-version checks, lease-runtime/context construction,
and exactly one pure evaluator invocation, but it does not persist evaluator
output, mutate durable state, commit, or add migration 0002.
The code still does not implement a production `StateStore` mutation backend.

The work-item state schema id is:

`governed-execution.nwp-work-item-state.v1`

Normal states:

- `proposed`
- `lease_admitted`
- `ready`
- `cycle_starting`
- `worker_running`
- `validating`
- `auditing`
- `commit_eligible`
- `local_commit_completed`

Alternate or terminal states:

- `repair_admitted`
- `repair_running`
- `blocked`
- `failed`
- `exhausted`
- `lease_expired`
- `canceled_revoked`
- `cleanup_pending`
- `cleanup_completed`

The transition evaluator is pure. It enforces target-state support, invariant
P1 stage availability, typed lease runtime status, global-stop prerequisites,
terminal and predecessor rules, typed authorization and dependency decisions,
evidence requirements, safe-failure-class requirements, and
attempt/repair/budget counters. It produces either an
accepted `TransitionEvent`, a domain-rejected `TransitionEvent`, or a local
pre-apply-invalid result with no event.

The evaluator does not perform writer fencing, idempotency lookup,
authoritative current-state loading, expected-version comparison, persistence,
or report projection.

P1 future worker-cycle, repair, and local-commit states are declared for
contract shape only. They are not enableable in production P1. The transition
engine returns `stage_not_enabled` for those stages without accepting a policy,
configuration, environment variable, callback, or provider that can enable
them. Pre-apply binding failures still win before domain evaluation, but for a
valid bound command targeting a P1-disabled state, `stage_not_enabled` precedes
lease runtime, global stop, authorization, dependency, evidence, predecessor,
terminal, budget, attempt, and repair-limit reasons. The resulting
domain-rejected event still records the complete reconstructed context
provenance, including `LeaseRuntimeDecision`.

## P1.1 Atomic Apply Contract

The P1.1/B2a store and writer-session surfaces are protocols only. Future
mutation authority is session-bound. The atomic apply boundary owns:

- writer fencing;
- internal idempotency lookup;
- authoritative current-state loading;
- expected-version comparison;
- authoritative context reconstruction from persisted rows;
- lease runtime derivation from one transaction UTC timestamp;
- pure evaluator invocation;
- atomic state/event persistence;
- exact replay.

Expected-version mismatch is an apply conflict and creates no transition event.
Stale writer sessions, idempotency key reuse with a different command digest,
transactional validation failures, and authoritative not-found cases are also
apply conflicts with no event.
Closed writer sessions and writer-session process mismatches are session-local
failures before the atomic store boundary, not apply conflicts.
`validation_failed` is reserved for a future fenced SQLite transaction that has
accepted locally valid typed inputs but discovers their persisted decision,
global-stop, dependency, current-record, or addressing bindings do not match
authoritative records. Parser failures, closed sessions, forked sessions, and
B2c mutation-unavailable failures are local/pre-store invalid outcomes.

B3a corrects the transition writer protocol to `apply_transition(command)`.
The caller supplies only `TransitionCommand`; future B3 reconstructs
`TransitionContext` internally. `TransitionContext` contains
`LeaseIdentityValidation`, `AuthorizationDecision`, `DependencyDecision`,
`GlobalStopState`, and `LeaseRuntimeDecision`. It no longer carries raw
`lease_expired` or `lease_revoked` booleans.

B3b prerequisite contracts are source-of-truth in
`.docs/b3b-reader-prerequisite-contract.md`. They do not implement typed SQLite
readers or production fixtures. They pin future current-state reconstruction for the first
bounded persisted slice: admitted backlog is mandatory read-time authority;
work-item attempt and repair limits are exact copies of the standing lease;
`WorkItemRecord.budget_consumed` and `WorkItemRecord.budget_limit` must both be
zero; future B3c accepts only zero `TransitionCommand.budget_cost` in that
slice; dependency receipts apply only to READY transitions; row timestamps may
be carried only in internal envelopes; and schema 0001 is sufficient without
migration 0002.

B3b1 implements only the pure row-contract portion of that model. Already
fetched explicit row mappings for lease identity, authorization, dependency,
work items, admitted backlogs, and global-stop current state can now be
validated into internal timestamped envelopes. The operational `created_at`,
`admitted_at`, and `updated_at` fields are retained as internal metadata only
and do not alter the semantic identity or canonical digest of the reconstructed
model values. B3b1 does not add SQLite readers, cardinality/not-found behavior,
fixture insertion, transition context assembly, idempotency/replay, event
sequencing, expected-version checks, or mutation storage.

B3b2a implements the private capability-protocol and query-contract portion of
the future typed-reader boundary. Ordered row-column tuples are now the source
of truth for schema-0001 row shapes, and six immutable explicit-column
parameterized SELECT specs exist as data.

B3b2b implements six private SELECT readers over those specs. They validate
lookup refs before borrowing, borrow only through `_TransitionReadCapability`,
bind the lookup as one parameter, call `fetchmany(2)`, classify row cardinality,
require exact built-in tuple rows, map tuples to private dictionaries, delegate
to B3b1 row adapters, classify SQLite SELECT failures safely, sanitize unknown
capability borrow exceptions, and close cursors without closing the connection.
Optional readers return `None` on absence; the mandatory `global_stop_current`
singleton raises `database_integrity_failure` when absent. Tests execute the
readers through a tests-only capability and in-memory tables.

B3b2b does not provide a concrete production capability, accept raw SQLite
connections as authority, own or close the connection, begin or end a
transaction, assemble `TransitionContext`, inspect idempotency/replay/event
state, classify optional missing rows into apply conflicts, or mutate durable
state. `connection.in_transaction` is not transaction identity. Future B3c must
own one opaque epoch per `BEGIN IMMEDIATE` transaction, invalidate it before
commit or rollback, reject old epochs after transaction end or restart on the
same connection, and own writer fencing, idempotency/replay, expected-version,
reader ordering, cross-record assembly, evaluation, and mutation.

B3c0a is the source of truth for future transition authority and ordering. It
pins nominal capability ownership, operation-guard lifetime, the private
credential boundary, operation-lease acquisition as the externally atomic
lifecycle/process and retained-lock gate, one shared transition/global-stop
mutation slot per `WriterSession`, the pre-SQLite mutation prefix, writer
fencing before idempotency, current-state and expected-version checks before
context rows, context row order, timestamp capture after authoritative binding,
capability invalidation before commit or rollback, rollback/commit/close
precedence, and event-ref/sequence collision posture.
B3c0a implements none of those runtime steps.

B3c1 prerequisites are source-of-truth in
`.docs/b3c1-prerequisite-contract.md`. They reconcile the B3c0a capability
wording by requiring a single private rollback-only controller construction path
while keeping future production invocation limited to
`_SQLiteWriterSession.apply_transition()`. During B3c1b, that controller has no
production caller; coherent tests may invoke the same private controller
directly through private imports; public transition and global-stop mutation
methods remain `writer_session_mutation_unavailable` and open no SQLite
database. B3c1a implements only private WriterSession authority plumbing.
B3c1b implements only private rollback-only writer fencing/capability
mechanics, with no B3b2 reader integration, context assembly, evaluator
invocation, event/state mutation, public mutation-method behavior change,
commit, or migration 0002.

B3c0b implements the already-fetched `transition_events` row contract and pure
idempotency match. `TransitionEventRecordEnvelope` reconstructs the stored
event and replay `WorkItemRecord`, hides both from repr, validates exact
canonical event/replay JSON and digests, checks all indexed event columns,
requires `transition_events.created_at` to equal the event's
`LeaseRuntimeDecision.evaluated_at`, and enforces the bounded zero-budget
replay slice. `match_transition_event_idempotency(...)` returns `None` for an
absent row, exact replay for matching work item/key/digest, an
`idempotency_key_reuse_conflict` for a digest mismatch, and
`database_integrity_failure` for wrong-address rows. It does not read SQLite,
generate timestamps, invoke the evaluator, allocate sequences, or mutate state.

B3c0b also defines immutable data-only query specs for future
`transition_events` idempotency lookup and maximum sequence inspection. Those
specs are now consumed only by B3c2 private transaction-internal readers. The
idempotency reader returns only `None` or an exact hidden
`TransitionEventRecordEnvelope`; exact replay and idempotency-key conflict
are now consumed by the private B3c3 rollback-only dry-run runtime through the
pure matcher. The maximum-sequence reader returns only `None` or an exact
observed non-negative integer maximum; sequence allocation remains future B3c4
behavior through the pure allocator.

B3 tests-only coherent fixtures now live under `tests/` only. They use a
temporary managed schema-0001 database, directly seed synthetic authoritative
rows through a test-setup transaction, reconstruct through existing B3b1/B3b2b
and B3c0b contracts, and acquire real internal writer issuance as temporary
test evidence. Unsupported authorization remains production/default, optional
persisted events are domain-rejected, and no accepted executable transition is
proved. The fixtures do not add production admission, authorization, product
state initialization, runtime authority, a concrete capability, fencing, context
assembly, mutation, or migration 0002.

Committed accepted and domain-rejected transitions commit exactly one
`TransitionEvent`. The event is the receipt. B3c3 rollback-only fresh
evaluation output is explicitly non-durable and non-receipt until B3c4 inserts
and commits the event. A committed event carries the complete
`LeaseRuntimeDecision` mapping, so the transaction timestamp and runtime lease
status used by the evaluator are covered by event identity and digest. There is
no separate result
reason or receipt object that can disagree with the event reason.

Future production storage must provide one active authoritative writer session,
ownership generation, stale-writer fencing, split-brain prevention,
transactional counters/state, crash consistency, restart reconciliation,
corruption detection, backup/restore, and persistent global stop.

B1/B1.1 implements the SQLite bootstrap and forward-only migration layer for an
explicitly requested local database plus observational existing-database
inspection/validation. B1.1 managed validation checks migration-history/catalog
equality, live-schema manifest equality, exactly one global-stop current
singleton, and zero-or-one writer ownership row semantics. A missing writer row
is valid before first acquisition; a present writer row must have generation at
least `1`. B2a adds safe writer
metadata and an opaque `WriterSession` protocol. B2b adds shared
state-authority lock integration for initialize/migrate. B2c adds internal
writer acquisition, proof generation/verification, durable generation
issuance, a private full-operation guard for future apply transactions, and
session-local mutation-unavailable failures. The guard uses private operation
identities and a lifecycle epoch, makes copied child leases no-op safely,
rejects same-thread close with `writer_session_close_during_operation`, lets
cross-thread close wait for active operations, retains the concrete session
wrapper through each lease, and distinguishes closing from cleaning so exactly
one cleanup owner releases proof/lock resources before closed is published.
Nonblocking finalizer cleanup may defer proof/lock release until the last
operation exits, and concurrent explicit close callers wait for closed before
returning. It implements no SQLite `StateStore`, no work-item or global-stop
mutation API, no transition or global-stop event persistence, no product read
port, and no production persistence adapter.

B0 selected SQLite, one private local database, as the future first production
backend architecture. B1/B1.1 adds administrative database bootstrap,
observational connection posture, migration-history/catalog equality,
live-schema manifest checks, and schema compatibility validation. B2a adds
writer-session contract hardening, B2b adds the common administrative lock,
B2c adds internal writer acquisition, B3a adds non-mutating canonical
contracts, B3b prerequisite contracts add pure/model reader prerequisites, and
B3b1 adds pure internal row-to-envelope adapters only. B3b2a adds private
capability-protocol and query-spec contracts. B3b2b adds private SELECT readers
that are not called by production source. B3c0a adds contract/static pins only.
B3c0b adds pure/static transition-event envelope, idempotency match, and
sequence/query-spec contracts only. B3 tests-only coherent fixtures add
temporary managed graphs under `tests/` only. No `StateStore` mutation backend,
integrated production typed SQLite reader, production fixture insertion helper,
coordinator service, or executable A2 capability exists in this slice. B3c1a
adds only private WriterSession authority plumbing, and B3c1b adds only private
rollback-only writer fencing/capability mechanics; neither changes that runtime
boundary. B3c2 adds private event/idempotency and observed maximum-sequence
readers with no production caller and no mutation.

The future SQLite backend must preserve the P1.1 command/event/apply-conflict
algebra. Event rows own idempotency and exact replay snapshots. Current-state
tables own current state. Replay snapshots are authoritative only for exact
replay of the original command, never for later current-state truth.

The first journal posture is rollback journal DELETE mode with
`synchronous=FULL` and explicit transactions. Future mutation transactions use
`BEGIN IMMEDIATE`; B1 migration transactions also begin explicitly. WAL remains
a future option only after a focused operations/recovery audit.

## Global Stop

Global stop is operator-owned. The Coordinator observes and enforces it. The
Coordinator cannot clear, weaken, replace, or reinterpret it.

Global-stop updates use the same command/event/apply-conflict/outcome algebra
as work-item transitions. A typed operator decision is an input to the pure
global-stop evaluator; it is not minted by the Coordinator.

An active global stop blocks lease admission, ready, cycle start,
retry-equivalent progression, worker-cycle progression, repair,
commit eligibility, and local-commit completion. Report failure cannot disable
enforcement.

P1 does not terminate processes or cancel workers because P1 starts no worker.
