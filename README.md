# NWP Coordinator

Current repository name: Governed Execution Coordinator.

This operational repository name is provisional and may change without changing
schema, authority, or durable identifiers. The canonical component name is
NWP Coordinator.

This repository contains the A2-P1 skeleton for the future local coding-work
coordinator. P1 provides offline contract primitives only:

- standing lease identity parsing, deterministic canonicalization, and digest
  validation for `governed-execution.nwp-standing-lease.v1`;
- closed-world v1 input parsing that rejects unknown and duplicate fields
  before canonicalization;
- a fail-closed unsupported authorization provider;
- finite backlog parsing and canonical identity;
- a pure work-item state transition engine;
- a state-store protocol with no production backend;
- operator-owned global-stop models and enforcement checks;
- closed, typed, non-authoritative report projections.

P1 does not execute workers, invoke Bridge or Codex, start a scheduler, run a
daemon, consume a queue, create worktrees, select a production state backend,
authorize executable work, run validation sandboxes, repair, commit, publish,
push, open pull requests, or contact live product routes.

The P1 runtime has no supported policy, configuration, callback, or environment
path that enables future worker, repair, or local-commit stages.

See `.docs/` for the authority boundary and A2-P1 contract.
