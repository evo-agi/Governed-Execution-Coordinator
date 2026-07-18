# Durable State Model

A2-P1/P1.1 defines state contracts. B1/B1.1 adds explicit operator-local
SQLite bootstrap, observational validation, live-schema integrity checks, and
migration infrastructure. B2a corrects the writer-session authority contract.
B2b adds the common state-authority lock for initialize/migrate administration.
B2c adds durable writer issuance and an internal concrete SQLite
`WriterSession`. B3a adds canonical persistence and provenance contracts only.
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
readers or fixtures. They pin future current-state reconstruction for the first
bounded persisted slice: admitted backlog is mandatory read-time authority;
work-item attempt and repair limits are exact copies of the standing lease;
`WorkItemRecord.budget_consumed` and `WorkItemRecord.budget_limit` must both be
zero; future B3c accepts only zero `TransitionCommand.budget_cost` in that
slice; dependency receipts apply only to READY transitions; row timestamps may
be carried only in internal envelopes; and schema 0001 is sufficient without
migration 0002.

Accepted and domain-rejected transitions commit exactly one `TransitionEvent`.
The event is the receipt. It carries the complete `LeaseRuntimeDecision`
mapping, so the transaction timestamp and runtime lease status used by the
evaluator are covered by event identity and digest. There is no separate result
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
contracts, and B3b prerequisite contracts add pure/model reader prerequisites
only. No `StateStore` mutation backend, typed SQLite reader, test database
fixture insertion helper, coordinator service, or executable A2 capability
exists in this slice.

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
