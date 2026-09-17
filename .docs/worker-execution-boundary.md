# Worker Execution Boundary

## Status And Purpose

Status: target runtime contract/design record with a current C2A1 pure-value
prerequisite. This document enables no runtime implementation, no transport or
process-framing implementation, no process launch, and no dispatch. C2A freezes
the pure semantic schemas without creating a runtime wire protocol, and C2A1
implements only the internal immutable values and six named pure coherence
validators. This document selects target worker source/process placement and a
staged direct-local-to-ES route without implementing either.

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

Separately, C2A1 currently provides one internal standard-library-only no-I/O
module for nine immutable semantic values and six pure graph-coherence
validators. It does not verify standing authority, ingest observations, acquire
time or external facts, launch a worker, own capsule bytes, execute validation
or review, perform Git effects, or implement either delivery route.

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

A future Worker Execution Boundary consumes the exact semantic fields,
identities, domains, golden vectors, and finite outcomes frozen by
`.docs/c2a-first-slice-semantic-protocol-contract.md`, including mandatory
distinct `program_ref` and `program_version_ref`. C2A1 supplies only their pure
internal value and coherence layer. Without freezing durable tables, public
endpoints, process framing, or transport wrapping, the future boundary requires:

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

## C2B0 Durable Intent And Restart Overlay

Status: `ACCEPTED TARGET CONTRACT`; no worker or process implementation.

Future author, validation, review, and cancellation external I/O requires its
exact durable effect intent and initial delivery to commit first. A cancel
decision must commit before the cancellation effect, and the cancellation
effect must commit before any future external cancellation request. A durable
decision or effect is not delivery acknowledgement, ES admission, runtime
termination, semantic abandonment, or acceptance.

The C2B target retains only a privacy-safe WorkSpec projection. SQLite cannot
reconstruct the private WorkSpec, and a safe ref or digest cannot authorize
retrieval. Restart-safe author establishment and worker launch remain blocked
until a separately accepted physical-custody, retention, authorization, and
attempt-bound retrieval contract exists.

C2B0 adds no worker, supervisor, process launch, source invocation, external
cancellation, capsule store, model/provider client, direct-local adapter, ES
adapter, Git effect, service/API/IPC, queue, scheduler, or runtime behavior.

<!-- C2B3_NARROWED_WORKER_BOUNDARY_BEGIN -->
## Narrowed first-route worker boundary

The first author-effect delivery uses the existing `direct_local_bootstrap`
compatibility token as a bounded direct/non-ES route to one qualified remote
Linux host. The token does not imply the user's Mac, Coordinator-host
execution, physical colocation, or a third adapter kind. Initialization remains
route-neutral, and topology/profile/transport observations are operational
evidence only.

The worker receives neither Coordinator SQLite nor writer authority. Raw
WorkSpec and retrieval bearer authority never enter Coordinator SQLite, and a
ref/digest cannot authorize retrieval. External standing authority and current
verification remain external. The
`qualified_remote_host_readiness_evidence_gate` must be satisfied by accepted
owning-process evidence that one remote Linux host is qualified before real
retrieval, process-separated worker or Codex invocation, validation, review, or
Git execution. That operational evidence is not identity or authority, and its
failure or absence permits neither Mac nor Coordinator-host fallback.

The route may yield at most one productive acceptance. A second productive
bootstrap slice is blocked until accepted ES reliable-submit and adapter-
conformance gates. Exact custody, retrieval, invocation, capsule, evidence,
protocol, supervision, transport, and conformance mechanics remain just-in-
time design questions and no runtime/source is authorized.
<!-- C2B3_NARROWED_WORKER_BOUNDARY_END -->

<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_BEGIN -->
## Cognitive proposal and selection runtime

Section 41 of `.docs/c2b-durable-development-state.md` remains the sole detailed
semantic owner; Section 42 records current implementation and
repository-publication status without redefining it. C2B3D private author-effect
establishment is committed at
`5e544622e5f46ddc78294322471b4fcbd2ad9172`. Migration
`0003_cognitive_proposal_and_selection_state` and the private pre-execution
proposal-selection runtime are committed at
`394d625aa63935140eeaf88ecff6f59f0547cb7e`. Git owns committed object and ref
truth; independent acceptance, audit, validation, provenance, and report
records remain external evidence rather than Coordinator durable authority or
effect permission. The source tranche ends at typed pre-execution proposal
admission plus Coordinator selection or non-selection. It performs no
model/provider invocation, dispatch, worker contact, post-execution
validation/review execution, post-execution Coordinator semantic decision,
capsule custody, Git effect, Bridge or ES handoff, publication execution,
service, scheduler, queue, or autonomous loop. The full remote-worker phase is
not reduced to this private source tranche.
<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_END -->


<!-- COORDINATOR_RW0_PHASE_ENTRY_CROSS_REFERENCE_BEGIN -->
### RW0 remote-contact phase-entry target cross-reference

.docs/rw0-remote-worker-contact-phase-entry.md is the sole detailed owner.
Current implementation stops at private C2B3D planned author delivery plus Section 41 pre-execution selection; executable contact and terminal-outcome runtime remain unsupported and fail-closed.
RW0 target begins with a receipt-backed no-contact phase-entry fact and fresh authority, host, and custody gates.
External standing-policy authority owns the parent grant; Coordinator target derives a separate narrower subordinate authorization record only inside that freshly verified grant.
Existing author attempt/effect fences retain exact externally authored per-fence authorization-basis refs/digests; the future subordinate record binds each corresponding basis pair and both exact fence identities byte-for-byte without replacement.
A current external verifier proves parent/basis ancestry, joint common-family compatibility, scope, expiry, revocation, global stop, and current heads; incompatibility or ambiguity blocks RW0 before retrieval, contact, delivery, or launch.
The two per-fence authorization-basis pairs need not equal each other; neither existing fence nor its digest is executable permission.
Direct-local permits one qualified remote Linux host, exactly the existing author attempt, effect, command, candidate, and initial delivery, with at most one author invocation and actual author delivery; reached validation, review, and cancellation use distinct current effects and deliveries.
No replacement author attempt, effect, command, candidate, or candidate-authoring invocation occurs; no author relaunch or redelivery, fallback, or third adapter is permitted.
The existing C2B `cancel` decision commits before the cancellation effect, preassigns its effect, fence, first delivery, and target, and is that effect's exact basis_decision_ref.
A separate future Coordinator-owned durable RW0 terminal-outcome fact closes each run; it is not a development_decision, effect basis, or second C2B cancel or block decision.
Non-cancel terminal outcomes bind one earlier same-kind C2B decision. The accepted direct-local C2B decision alone atomically consumes the one-way latch in its guarded writer transaction; the later terminal-outcome `accept` binds that exact decision ref/digest and committed latch postimage without another latch mutation.
After exact cancel-decision commit readback and current-head, stop-version, and authority verification, an unusable pre-effect cancel basis establishes no effect, fence, delivery, request, or signal and commits terminal-outcome `block` bound to the exact unusable decision and mismatch evidence, without another C2B decision.
A current compatible cancel basis follows distinct request, acknowledgement, signal, exit, teardown, and source reconciliation facts, yielding terminal-outcome `cancel` only when complete and unambiguous or terminal-outcome `block` otherwise without another C2B decision.
No current custody, adapter, supervisor, worker, capsule, validation, review, model, post-execution decision, terminal-outcome, latch, Git, or publication runtime exists.
Direct-local route-local process and cancellation ownership does not absorb ES-route authority; no successor, Git, or publication effect follows RW0.
Exact custodian, transport, framing, Codex seam, schema, terminal-outcome representation, latch, and physical backends remain deferred.
<!-- COORDINATOR_RW0_PHASE_ENTRY_CROSS_REFERENCE_END -->
