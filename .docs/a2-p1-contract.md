# A2-P1 Contract

A2-P1 is the Coordinator skeleton tranche.

It implements:

- `governed-execution.nwp-standing-lease.v1` identity parsing,
  canonicalization, and digest validation;
- a distinct authorization-provider boundary whose production/default provider
  always blocks with `unsupported_authorization_model`;
- finite backlog parsing and canonical identity;
- immutable work-item records and a pure state transition engine;
- a state-store protocol only;
- global-stop models and pure enforcement checks;
- safe report projections.

It does not implement worker execution or any of the following:
- Bridge invocation;
- Codex invocation;
- subprocess or shell execution;
- network clients;
- scheduler, daemon, queue consumer, or background loop;
- production storage, SQLite, filesystem journal, or database;
- executable lease authorization;
- signing, keys, certificates, trust roots, or custody;
- validation sandboxing;
- retry execution;
- repair;
- local commit behavior;
- push, pull request, merge, publication, or deployment.

## P1 State Gating

The state vocabulary includes future executable stages so that the contract can
be validated, but the default P1 policy gates those stages. Transitions into
worker, repair, or commit stages return `stage_not_enabled` unless a test-only
fixture policy is used.

No publication state exists in P1.
