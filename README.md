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
  with private in-memory proof material and no mutation storage.

P1.1 models expected-version mismatch, stale writer sessions, idempotency key
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
state backend architecture. B1/B1.1 implements secure local database bootstrap,
non-mutating inspection/validation for existing databases, live-schema
integrity checks, and forward-only migrations for explicitly requested
operator-local administration. B2a corrects the writer-session contract, and
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
and retains the common lock for the session lifetime. The runtime still
provides no `StateStore` mutation backend, transition/global-stop persistence,
coordinator service, worker, scheduler, authorization path, or executable A2
capability. B2c mutation methods fail locally with
`writer_session_mutation_unavailable`.

See `.docs/` for the authority boundary and A2-P1 contract.
