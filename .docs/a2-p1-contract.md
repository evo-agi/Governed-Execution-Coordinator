# A2-P1 Contract

A2-P1/P1.1 is the Coordinator skeleton tranche.

It implements:

- `governed-execution.nwp-standing-lease.v1` identity parsing,
  canonicalization, and digest validation;
- closed-world parsing for versioned v1 inputs, including recursive
  allowed-key checks and duplicate JSON object key rejection before
  canonicalization;
- exact-shape, non-coercing collection parsing before normalization and digest
  verification;
- a distinct authorization-provider boundary whose production/default provider
  always blocks with `unsupported_authorization_model`;
- finite backlog parsing and canonical identity;
- immutable work-item records and a pure state transition evaluator;
- a state-store protocol only for read-side P1.1 storage shape;
- P1.1 transition commands, transition events, apply conflicts, committed
  outcomes, read-side state-store protocol, and writer-session protocol only;
- global-stop command/event models and pure enforcement checks;
- closed typed report projections.

It does not implement worker execution or any of the following:
- Bridge invocation;
- Codex invocation;
- subprocess or shell execution;
- network clients;
- scheduler, daemon, queue consumer, or background loop;
- `StateStore` mutation storage, filesystem journal, in-memory production
  store, product database reads, or product database writes;
- executable lease authorization;
- signing, keys, certificates, trust roots, or custody;
- validation sandboxing;
- retry execution;
- repair;
- local commit behavior;
- push, pull request, merge, publication, or deployment.

B0 added architecture documents, a non-production SQLite schema fixture, and
static/in-memory schema tests for a future first backend. B1/B1.1 adds explicit
operator-local SQLite bootstrap, observational inspection/validation,
connection posture, packaged migrations, migration-history/catalog equality,
live-schema manifest verification, and schema compatibility validation. B2a
corrects writer authority to an opaque future `WriterSession` plus safe
non-authoritative metadata. B2a does not change the P1/P1.1 runtime
prohibition above: there is still no production SQLite `StateStore`, no writer
acquisition, no coordinator service, and no executable A2 capability.

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

## P1.1 Transition Persistence Contract

`TransitionCommand` carries caller intent and safe decision references.
`TransitionEvent` is the only durable transition receipt. Caller code never
provides proposed state, proposed events, or receipts.

The pure evaluator owns domain rules and constructs accepted or
domain-rejected events. Expected-version comparison, writer fencing,
idempotency lookup, authoritative state loading, atomic state/event persistence,
and exact replay belong to the atomic store boundary.

Apply conflicts have no event. They include stale writer session, idempotency
key reuse with a different command digest, expected-version conflict, and
authoritative work-item not found. Exact replay returns the original committed
state/event with `replayed=true` and creates no new event or counter effect.

Global-stop updates use the same command/event/apply-conflict/outcome algebra.
The Coordinator cannot manufacture operator authorization.

## Public Projections

Reports are closed typed projections. They are constructed from explicit safe
refs, enums, bounded counters, global-stop status, and the fixed
non-authority notice. They are not arbitrary mappings passed through a generic
sanitizer.

Public projections expose no private brief, prompt, instruction, raw log,
raw payload, credential, endpoint, local path, platform identifier, trust
material, signer, key, certificate, or custody material.
