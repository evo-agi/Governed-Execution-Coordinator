# A2-P1 Contract

A2-P1 is the Coordinator skeleton tranche.

It implements:

- `governed-execution.nwp-standing-lease.v1` identity parsing,
  canonicalization, and digest validation;
- closed-world parsing for versioned v1 inputs, including recursive
  allowed-key checks and duplicate JSON object key rejection before
  canonicalization;
- a distinct authorization-provider boundary whose production/default provider
  always blocks with `unsupported_authorization_model`;
- finite backlog parsing and canonical identity;
- immutable work-item records and a pure state transition engine;
- a state-store protocol only;
- global-stop models and pure enforcement checks;
- closed typed report projections.

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
be validated, but P1 gates those stages invariantly. Transitions into worker
cycle, repair, or local-commit stages return `stage_not_enabled` under the
committed P1 runtime.

P1 exposes no production API, policy object, constructor argument,
configuration, environment variable, callback, or provider that enables those
future stages. Future tranches must explicitly change or version the contract
rather than flip a hidden P1 switch.

No publication state exists in P1.

## Public Projections

Reports are closed typed projections. They are constructed from explicit safe
refs, enums, bounded counters, global-stop status, and the fixed
non-authority notice. They are not arbitrary mappings passed through a generic
sanitizer.

Public projections expose no private brief, prompt, instruction, raw log,
raw payload, credential, endpoint, local path, platform identifier, trust
material, signer, key, certificate, or custody material.
