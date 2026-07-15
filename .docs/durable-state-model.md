# Durable State Model

A2-P1 defines state contracts but does not persist them in production.

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

The transition engine is pure. It enforces allowed predecessors,
expected-version checks, idempotency-key handling, lease/global-stop
prerequisites, attempt/repair/budget counters, evidence requirements, cleanup
implications, and terminal-state checks.

The state-store surface is a protocol only. Future production storage must
provide one active authoritative writer, ownership generation, stale-writer
fencing, split-brain prevention, transactional counters/state, crash
consistency, migrations, restart reconciliation, corruption detection,
backup/restore, and persistent global stop.

P1 selects no production state backend. It implements no SQLite store, no
filesystem journal, no database, and no production persistence adapter.

## Global Stop

Global stop is operator-owned. The Coordinator observes and enforces it. The
Coordinator cannot clear, weaken, replace, or reinterpret it.

An active global stop blocks lease admission, ready, cycle start, retry,
repair, and commit eligibility. Report failure cannot disable enforcement.

P1 does not terminate processes or cancel workers because P1 starts no worker.
