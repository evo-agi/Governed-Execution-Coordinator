# Durable State Model

A2-P1/P1.1 defines state contracts. B1 adds explicit operator-local SQLite
bootstrap and migration infrastructure, but it still does not implement a
production `StateStore` mutation backend.

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

The transition evaluator is pure. It enforces allowed predecessors,
lease/global-stop prerequisites, typed authorization and dependency decisions,
attempt/repair/budget counters, evidence requirements, cleanup implications,
P1 stage availability, and terminal-state checks. It produces either an
accepted `TransitionEvent`, a domain-rejected `TransitionEvent`, or a local
pre-apply-invalid result with no event.

The evaluator does not perform writer fencing, idempotency lookup,
authoritative current-state loading, expected-version comparison, persistence,
or report projection.

P1 future worker-cycle, repair, and local-commit states are declared for
contract shape only. They are not enableable in production P1. The transition
engine returns `stage_not_enabled` for those stages without accepting a policy,
configuration, environment variable, callback, or provider that can enable
them.

## P1.1 Atomic Apply Contract

The P1.1 store surface is a protocol only. The atomic apply boundary owns:

- writer fencing;
- internal idempotency lookup;
- authoritative current-state loading;
- expected-version comparison;
- pure evaluator invocation;
- atomic state/event persistence;
- exact replay.

Expected-version mismatch is an apply conflict and creates no transition event.
Stale writers, idempotency key reuse with a different command digest, and
authoritative not-found cases are also apply conflicts with no event.

Accepted and domain-rejected transitions commit exactly one `TransitionEvent`.
The event is the receipt. There is no separate result reason or receipt object
that can disagree with the event reason.

Future production storage must provide one active authoritative writer,
ownership generation, stale-writer fencing, split-brain prevention,
transactional counters/state, crash consistency, restart reconciliation,
corruption detection, backup/restore, and persistent global stop.

B1 implements the SQLite bootstrap and forward-only migration layer for an
explicitly requested local database. B1 implements no SQLite `StateStore`, no
work-item or global-stop mutation API, no writer acquisition, no writer fencing
validation, no product read port, and no production persistence adapter.

B0 selected SQLite, one private local database, as the future first production
backend architecture. B1 adds administrative database bootstrap, connection
posture, migration-history, and schema compatibility validation. No
`StateStore` mutation backend, writer acquisition, coordinator service, or
executable A2 capability exists in B1.

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
