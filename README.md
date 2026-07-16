# NWP Coordinator

Current repository name: Governed Execution Coordinator.

This operational repository name is provisional and may change without changing
schema, authority, or durable identifiers. The canonical component name is
NWP Coordinator.

This repository contains the A2-P1/P1.1 skeleton for the future local
coding-work coordinator. P1/P1.1 provides offline contract primitives and B1
SQLite bootstrap/migration infrastructure only:

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
- explicit operator-local SQLite database bootstrap, connection posture,
  migration catalog, migration-history validation, and schema compatibility
  checks.

P1.1 models expected-version mismatch, stale writer tokens, idempotency key
reuse, and authoritative not-found cases as apply conflicts with no event.
Domain rejections, such as invalid predecessors, global stop, budget failure,
missing evidence, and invariant P1 `stage_not_enabled`, commit exactly one
event. The event is the receipt.

P1/B1 does not execute workers, invoke Bridge or Codex, start a scheduler, run
a daemon, consume a queue, create worktrees, implement `StateStore` mutations,
acquire a Coordinator writer, authorize executable work, run validation
sandboxes, repair, commit, publish, push, open pull requests, or contact live
product routes.

The P1 runtime has no supported policy, configuration, callback, or environment
path that enables future worker, repair, or local-commit stages.

B0 selected SQLite, one private local database, as the future first production
state backend architecture. B1 implements secure local database bootstrap and
forward-only migrations for explicitly requested operator-local administration.
B1 still provides no `StateStore` mutation backend, writer acquisition,
coordinator service, worker, scheduler, authorization path, or executable A2
capability.

See `.docs/` for the authority boundary and A2-P1 contract.
