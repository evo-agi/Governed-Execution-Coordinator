# Worker Execution Boundary

## Status And Purpose

Status: target contract/design record only. This document enables no runtime
implementation, no transport or process-framing implementation, no process
launch, and no dispatch. C2A freezes target-only pure semantic schemas without
creating a runtime wire protocol. This document selects target worker
source/process placement and a staged direct-local-to-ES route without
implementing either.

Contract language distinguishes `CURRENT IMPLEMENTED CONTRACT`, `CURRENT
COMPATIBILITY EDGE`, `ACCEPTED STRATEGIC TARGET`, `FUTURE IMPLEMENTATION
DETAIL`, `DEFERRED OR BLOCKED EFFECT`, and `PROCESS-ONLY GOVERNANCE`. The
authoritative C1 composition record is
`.docs/autonomous-software-development-operating-model.md`.

The Worker Execution Boundary is the reserved, transport-neutral boundary
between Coordinator-owned durable development progression and Execution
Substrate-owned execution admission and runtime lifecycle authority. This
document records strategic target direction and required invariants for future
work. It is not evidence that dispatch, worker execution, ES submission, result
ingest, or an autonomous loop exists.

This tranche selects no durable schema, table, queue, service, IPC, public API,
polling model, callback model, runtime profile, Codex protocol, package,
executable, supervisor mechanism, credential delivery, build system, deployment,
or append-only event-sourcing architecture. C2A's accepted semantic contract
does not implement a Development Program.

## Current Implementation Reality

Coordinator currently owns bounded internal durable SQLite mutation authority for
coding-work state. Current internal SQLite `WriterSession` behavior includes
durable writer issuance, fencing, transition persistence, global-stop
persistence, verification of already-persisted operator-decision receipts,
idempotency and exact replay, accepted-current CAS, rollback, one COMMIT
attempt, commit uncertainty, and explicit retry.

The public `StateStore` remains unwidened. Internal `WriterSession` mutation is
not a general public `StateStore` backend, service, API, worker loop, dispatcher,
or runtime integration.

Coordinator currently has no worker, scheduler, queue consumer, dispatcher,
reconciler, public service/API, Codex invocation, Execution Substrate handoff,
runtime-profile integration, result-ingest path, repair executor, publication
path, autonomous loop, dispatch command identity, worker attempt identity,
adapter invocation identity, ES run identity, Codex process/session identity,
outbox/inbox state, retained-result reference, or cancellation acknowledgement.

Current P1 worker, validation, audit, repair, commit, and cleanup lifecycle
names remain declared contract vocabulary with invariant `stage_not_enabled`
behavior. Those state names do not prove runtime implementation.

Execution Substrate currently owns execution admission, prepare and submit
handoff, runtime-profile compatibility, runtime identity and credential-handoff
boundaries, Nomad-backed lifecycle projection, runtime cancellation-request
boundaries, and retained execution results.

Bridge is currently a guarded adapter/evidence surface. Bridge is not the
worker owner, a direct-local trigger, durable program authority, runtime
lifecycle truth, work-selection authority, scheduling policy, retry/repair
authority, acceptance authority, or hidden Coordinator state.

Control Plane remains relevant only to current maintained MVP/demo
compatibility, migration, filming, freeze, reference, or retirement context. It
is not part of the target autonomous-development topology in this document.

## Target Topology

Classification: `ACCEPTED STRATEGIC TARGET`.

The initial bounded bootstrap/proof topology is:

```text
reasoning model
    -> Coordinator durable software-development progression
    -> transport-neutral Worker Execution Boundary
    -> bounded direct-local bootstrap/proof adapter
    -> process-separated coding worker
    -> exact immutable candidate capsule
    -> validation and independent review observations
    -> model review proposal
    -> Coordinator acceptance, repair, replan, rejection, or block
    -> at most one local feature-branch Git commit
```

The later ES-routed topology is:

```text
same Coordinator progression semantics
same worker command/observation/fence/capsule contracts
same worker artifact
    -> ES reliable-submit adapter
    -> ES admission and runtime lifecycle
    -> process-separated coding worker
    -> opaque capsule result transport or retention
```

Initial worker source and release machinery live in the Coordinator repository,
and the worker executes as a separate OS process. The authoritative Coordinator
process must not perform implementation work in-process. No seventh repository
is created now; extraction requires demonstrated independent release cadence,
ownership, multiple consumers, or materially separate dependency or security
governance.

Model reasoning owns cognitive intent, architectural judgment, semantic
judgment, planning, replanning, and evidence review proposals. Model sessions
and model responses are not durable program truth or effect authority by
themselves.

Coordinator is intended to become the durable autonomy core for software
development progression. Execution Substrate continues to own execution
admission and runtime authority. Git owns repository object and ref truth. CI or
validating runtimes own observed validation results.

Direct-local execution outside Execution Substrate is an explicitly named,
bounded bootstrap/proof edge. It is not the target production execution path,
is not implemented by this tranche, and must stop expanding after one accepted
vertical slice pending ES-migration review.

## Desired Development State Versus Observed Execution Facts

Coordinator-owned target facts are desired development facts. External facts are
observations or receipts owned by their source system. Coordinator may retain
safe references and bounded observations needed for correlation and
decision-making. Retaining a reference does not transfer ownership of the
external fact.

Coordinator-owned target facts include:

- semantic attempt identity;
- desired progression;
- durable dispatch intent;
- retry or repair decision;
- cancellation intent;
- reconciliation decision;
- evidence requirements;
- evidence bindings;
- global-stop effect planning;
- acceptance progression;
- governed advancement toward allowed Git or publication effects.
- safe candidate-capsule digest/reference binding.

Externally owned facts include:

- ES admission decision;
- ES `run_id`;
- ES/Nomad lifecycle observation;
- ES cancel-request receipt;
- terminal runtime observation;
- retained-result reference;
- adapter invocation/session reference;
- Git object/ref identity;
- validation observation.
- capsule-store retrieval observation.

External runtime identifiers may be correlation references, but they are not
semantic work identity and do not become Coordinator runtime authority.

## Transport-Neutral Command, Observation, Fence, And Capsule Contracts

A future Worker Execution Boundary requires the exact target-only semantic
fields, identities, domains, golden vectors, and finite outcomes frozen by
`.docs/c2a-first-slice-semantic-protocol-contract.md`, including mandatory
distinct `program_ref` and `program_version_ref`. Without freezing durable
tables, public endpoints, process framing, or transport wrapping, it requires:

- semantic attempt identity;
- dispatch command identity;
- canonical command digest;
- mandatory program/version and work-item/revision correlation;
- repository and base Git identity;
- policy or authorization references;
- global-stop reference;
- attempt/effect fence binding;
- evidence requirements;
- canonical candidate-capsule manifest and portable-digest contract;
- idempotent delivery acknowledgement;
- idempotent observation ingest;
- duplicate, lost, late, stale, and ambiguous outcome handling.

Transport redelivery is not a new semantic attempt. A new semantic attempt
requires a Coordinator decision.

The direct-local adapter and later ES adapter must implement the same versioned
worker command, observation, fence, and capsule contracts and pass the same
conformance contract. One-repository/one-active-invocation bounds do not make a
supervisor or adapter the scheduler, lifecycle authority, work-selection
authority, or program truth.

## Effect And Transaction Ordering

External I/O does not occur inside the SQLite mutation transaction. A
recoverable durable effect intent must exist before an external dispatch effect
is attempted.

Delivery acknowledgement is not runtime admission. An ES submit receipt is not
semantic work acceptance. An unknown dispatch outcome remains unknown until it is
reconciled. Observations cannot silently advance desired state without
Coordinator evaluation.

An outbox/inbox is a likely implementation candidate for durable effect intent
and observation ingest. This document does not freeze outbox/inbox as mandatory.
Exact persistence, table, queue, delivery, polling, callback, service, and IPC
mechanics remain open. Equivalent designs must satisfy the same recovery and
authority invariants.

## ES Submit Ambiguity

The current ES public submit contract returns an internally generated `run_id`
after successful submit. The current public contract does not expose a
caller-supplied submit idempotency key, dispatch command identity, or
query-by-dispatch-command recovery path.

An accepted submit whose response is lost can therefore be ambiguous to a
caller. Coordinator must not compensate by inventing a second ES lifecycle store,
scraping Nomad as Coordinator authority, treating trace/request IDs as recovery
authority, or storing a parallel submitted-execution lifecycle truth.

ES submit ambiguity is a blocker to reliable real dispatch. Reliable real
dispatch requires an ES-owned idempotency, correlation, or recovery decision, or
an explicitly bounded bootstrap exception. This Coordinator document does not
define that ES contract.

## Cancellation And Global Stop

Coordinator owns semantic cancellation intent and global-stop effect planning.
Execution Substrate owns the runtime cancellation-request boundary.

An ES cancel receipt proves request acceptance, not terminal stop. Terminal
cancellation is learned through ES-owned lifecycle observation.

Global stop prevents new semantic dispatch and retry/repair progression. Active
work cancellation attempts must be recorded as effects and observations without
falsely claiming runtime termination.

This tranche implements no cancellation propagation and no global-stop runtime
propagation.

## Restart And Recovery

Before real dispatch, pending dispatch intent must be discoverable after
restart. Acknowledged but uncorrelated effects must remain reconcilable.
Duplicate acknowledgement and duplicate observation must be idempotent. Late
observations must be bound to the intended semantic attempt. Stale observations
must not overwrite newer Coordinator decisions. Ambiguous outcomes must not be
converted into success or failure by inference.

This document does not choose polling versus callback, a service, local IPC, a
queue, or an exact database representation.

## Accepted Staged Placement And Credential Boundary

Classification: `ACCEPTED STRATEGIC TARGET`.

The initial bounded direct-local supervisor/adapter launches a separate OS
worker process from worker source and release machinery held in the Coordinator
repository. The authoritative Coordinator process never executes implementation
work in-process. Bridge and Bridge Core are not worker implementation owners,
adapters, or triggers for the first slice. A separate stateless gateway is not
selected.

The worker has no direct Coordinator SQLite mutation authority. The worker,
supervisor, reviewer, model adapter, capsule store, and later ES adapter must not
receive a `WriterSession`, writer proof, Coordinator database path, or
unrestricted Coordinator credentials. Each boundary receives only the least,
attempt-bound or effect-bound authority required under the verified standing
grant and Coordinator fences.

Classification: `FUTURE IMPLEMENTATION DETAIL`. Exact IPC, process launch,
supervisor lifecycle mechanics, package and executable names, build system,
credential delivery, and deployment remain open.

## Private Material And Safe Projections

Public reports must not contain raw prompts, raw Codex JSONL, raw logs,
credentials, trust material, local absolute paths, private endpoints, retained
bundles, or arbitrary runtime payloads.

The first-slice candidate capsule is private, immutable, content-addressed,
worker-side, outside the mutable worktree, and outside Coordinator SQLite. The
worker invocation authors candidate bytes. A capsule builder acting at the
worker boundary seals the canonical manifest, blobs, and portable digest. A
private immutable worker-side content-addressed store has physical custody.
Coordinator retains only a safe digest/reference and progression decisions. A
reviewer has read-only, attempt-bound, capsule-bound retrieval authority. Later
ES transport or retention is opaque. Git owns object/ref truth only after a
separately selected commit effect.

A capsule digest is not a local path, endpoint, bearer retrieval credential,
authorization proof, acceptance decision, or Git identity. The portable capsule
excludes raw prompts, model transcripts, Codex JSONL, unrestricted logs,
unrestricted command output, credentials, private endpoints, trust material,
and unrelated workspace content. Exact path, storage implementation, encryption,
garbage collection, retention duration, serialization, and wire encoding remain
future implementation details.

## Review, Handback, Repair, And Effect Boundary

Worker completion, candidate capture, validation observation, independent review
observation or proposal, model review proposal, Coordinator semantic acceptance,
repair decision, replan decision, local Git commit, PR creation, merge, and
deployment remain distinct. Neither worker exit, validator success, reviewer
output, model response, ES result, Bridge report, Git commit, nor CI result
creates semantic acceptance.

A code-changing repair normally creates a new semantic attempt, candidate
identity, portable capsule digest, and candidate-bound validation and review.
The worker must not silently commit while authoring. The first-slice local commit
is a separate effect after Coordinator acceptance; push, PR creation, merge, and
deployment are blocked.

## Explicit Non-Claims

This document and tranche add:

- no implemented worker, supervisor, process launch, or Codex invocation;
- no scheduler;
- no dispatcher or reconciler;
- no service/API/IPC;
- no schema or migration;
- no outbox/inbox implementation;
- no ES call;
- no Bridge widening;
- no Bridge or Bridge Core worker ownership;
- no gateway service;
- no connector dependency;
- no Development Program prerequisite;
- no full event-sourcing decision;
- no implemented direct-local worker route;
- no runtime-profile selection;
- no model/provider client;
- no capsule builder or store implementation;
- no subordinate-authorization runtime;
- no Git effect or publication behavior;
- no validation, review, or repair executor; and
- no autonomous loop.

## Required-Before-Execution Gates

Direct-local source work requires a separately accepted implementation contract,
standing-policy and validation contracts, versioned worker
command/observation/fence/capsule contracts, process and credential boundaries,
safe capsule custody/retrieval, cancellation and `global_stop` semantics,
adapter conformance, independent audit, and provenance.

Migration to ES additionally requires accepted ES contracts for resolved
execution-plan extraction, reliable keyed submit, caller correlation and
response-loss recovery, ES-owned ambiguous-submit reconciliation, runtime
admission and lifecycle observation, cancellation correlation, opaque capsule
result transport or retention, and Coordinator-to-ES adapter conformance.

These are owner-governed gates, not permission for Coordinator documentation to
reprioritize ES. `resolved-execution-plan-extraction-foundation` remains the next
source-bearing reliable-submit seam under ES planning authority without adoption
of the rejected archived implementation.

## Open Seams

The following implementation seams remain open:

- exact Coordinator program and semantic-attempt schema;
- mapping or migration from current finite backlog and lease compatibility;
- external issuer/verifier deployment, standing-grant encoding, signer, trust
  root, revocation transport, and credential form;
- exact outbox/inbox or equivalent design;
- polling versus callback and service/API/local IPC mechanics;
- worker package, executable, build, supervisor, and deployment mechanics;
- process framing, transport wrapping, and ES wire mapping for the C2A-frozen
  command/observation/fence/capsule semantic fields;
- Codex CLI versus App Server and model/provider protocol;
- capsule path, store technology, encryption, garbage collection, retention,
  serialization, archival, and recovery;
- Git commands, branch naming, commit-message format, credentials, and publisher;
- ES request/response, correlation, cancellation, lifecycle, retained-result,
  runtime-profile, and adapter mechanics; and
- direct-local proof/recovery policy representation.

Classification: `CURRENT COMPATIBILITY EDGE`. Current `FiniteBacklog`, standing
lease, zero-only budget, READY-only dependency, disabled stages, coding
`global_stop`, `WriterSession`, and schema 0001 remain unchanged.
Classification: `DEFERRED OR BLOCKED EFFECT`. All source/runtime work and effects
beyond one future local feature-branch commit remain blocked. Classification:
`PROCESS-ONLY GOVERNANCE`. Future audit isolation requirements live in the C1
composition record and are not worker behavior.
