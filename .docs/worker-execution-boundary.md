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
A private no-I/O RW0-B1 semantic value and relation layer is now implemented. RW0-C1 now adds private immutable phase establishment and one-member-at-a-time supplied-evidence admission through the existing mutation controller. No verifier authenticity, custody, transport, process, worker, terminal-outcome runtime, latch, Git, ES route, service, scheduler, queue, or autonomous loop is implemented. C1 records durable evidence only; the executable boundary remains private C2B3D planned author delivery plus Section 41 pre-execution selection.
RW0 target begins with a receipt-backed no-contact phase-entry fact and fresh authority, host, and custody gates.
External standing-policy authority owns the parent grant; Coordinator target derives a separate narrower subordinate authorization record only inside that freshly verified grant.
Existing author attempt/effect fences retain exact externally authored per-fence authorization-basis refs/digests; the future subordinate record binds each corresponding basis pair and both exact fence identities byte-for-byte without replacement.
A current external verifier proves parent/basis ancestry, joint common-family compatibility, scope, expiry, revocation, global stop, and current heads; incompatibility or ambiguity blocks RW0 before retrieval, contact, delivery, or launch.
The two per-fence authorization-basis pairs need not equal each other; neither existing fence nor its digest is executable permission.
Direct-local permits one qualified remote Linux host, exactly the existing author attempt, effect, command, candidate, and initial delivery, with at most one author invocation and actual author delivery; reached validation, review, and cancellation use distinct current effects and deliveries.
No replacement author attempt, effect, command, candidate, or candidate-authoring invocation occurs; no author relaunch or redelivery, fallback, or third adapter is permitted.
The existing C2B `cancel` decision commits before the cancellation effect, preassigns its effect, fence, first delivery, and target, and is that effect's exact basis_decision_ref.
A separate future Coordinator-owned durable RW0 terminal-outcome fact closes each run; it is not a development_decision, effect basis, or second C2B cancel or block decision.
Non-cancel terminal outcomes bind one earlier same-kind C2B decision. The accepted direct-local C2B decision alone atomically creates the immutable bootstrap-acceptance fact in its guarded writer transaction; the later terminal-outcome `accept` binds that exact decision ref/digest and acceptance-fact identity/digest without mutating guard truth.
The bootstrap guard owner `.docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md` binds one permanently non-replenishable scope to an explicitly standing-policy-admitted Coordinator authority lineage, requires positive continuity and sole-active authority, and supersedes mutable-latch target requirements. Local absence, replacement, restore, cloning, grants, and later ES routing create no allowance.
After exact cancel-decision commit readback and current-head, stop-version, and authority verification, an unusable pre-effect cancel basis establishes no effect, fence, delivery, request, or signal and commits terminal-outcome `block` bound to the exact unusable decision and mismatch evidence, without another C2B decision.
A current compatible cancel basis follows distinct request, acknowledgement, signal, exit, teardown, and source reconciliation facts, yielding terminal-outcome `cancel` only when complete and unambiguous or terminal-outcome `block` otherwise without another C2B decision.
No current custody, adapter, supervisor, worker, capsule, validation, review, model, post-execution decision, terminal-outcome, latch, Git, or publication runtime exists.
Direct-local route-local process and cancellation ownership does not absorb ES-route authority; no successor, Git, or publication effect follows RW0.
Exact custodian, physical transport framing, stream/process plumbing, Codex seam, schema, terminal-outcome representation, guard values, storage, provisioning, readers, writers, migration treatment, and runtime remain deferred.
<!-- RW0_D1_CURRENT_STATUS_BEGIN -->
RW0-D1 is a current private artificial offline process and capsule proof. The guarded Coordinator program-initialization, C2B3D author-effect, Section 41 selection, and RW0-C1 phase writers remain the sole durable owners. A separate fake planner and fake coding worker run under the bounded D1 supervisor; the parent captures one temporary candidate, builds and independently verifies a CandidateCapsuleManifestV1, removes the mutable workspace, and returns a transient typed handback with separate parent-only disposable-state custody. The preassigned fixture base_git_oid is a WorkSpec coordinate, not Git authentication. RW0-D2 validation/review/model closure is next; RW0-C2 physical decision persistence follows D2. D1 grants no live provider/credential or source authentication, ES route, Git/publication effect, terminal acceptance, public service/CLI, or RW0-E runtime authority. The detailed implementation owner is .docs/rw0-d1-offline-process-and-capsule-spine.md.
<!-- RW0_D1_CURRENT_STATUS_END -->

RW0-C1 uses the fixed fifteen-kind inventory, same-phase membership operands, receipt-first replay, one commit attempt, guarded readback, and explicit three-way recovery. It claims no completeness, acceptance, C2 decision, current authority, source authenticity, permission, runtime truth, or external contact; RW0-C2 closure/decision and RW0-D/E remain future.
<!-- RW0_B2_WIRE_CURRENT_STATUS_BEGIN -->
RW0-B2-Wire now implements private, pure, no-I/O NWPF v1 representational framing, canonical command/result codecs, closed worker-result grammar, safe supplied cancellation-request and process source-claim values, and pure process/result classification. It also implements the separate private, pure, no-I/O cancellation-control evidence profile `rw0-wire-cancellation-control-v1` with digest `4d6f84552b852a4c4073b4238591afd271072f648424eca9e744def436165288`, exact-current author/validation/review cancellation-control relations, and pure `invalid`/`incomplete`/`finite` supplied-control-evidence classification. The additive cancellation-control profile does not replace or enter the fixed NWPF v1 frames, Capability continues to bind only `rw0-wire-nwpf-v1`, and the profile remains distinct from B1 physical host cancellation-mechanism evidence. Physical transport framing and stream/process plumbing remain deferred, as do pre-read allocation, supervisor/worker implementation, cancellation delivery, concrete direct-local or ES wrapper/correlation mechanics, persistence, source authentication, process proof, CLI/App Server integration, credentials, provider/session behavior, and live execution. The fixed protocol profile is `rw0-wire-nwpf-v1` with digest `470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454`; `.docs/rw0-b2-wire-protocol.md` is the detailed owner. RW0-B2-Wire does not own or alter RW0-B1 or C2A schema, canonical-identity, semantic-outcome, or authority contracts; their protected owner reconstruction and occurrence-work accounting are hardened separately for fail-closed Capability composition. No worker, process, contact, persistence, authority, acceptance, or Codex mechanism is implemented. Capability is implemented separately as private, pure, no-I/O semantics owned by `.docs/rw0-b2-capability.md` and does not widen Wire ownership. RW0-B1, RW0-B2-Wire, and RW0-B2-Capability private semantics are current implemented contracts; RW0-C/D/E durable, transport, process, provider, credential, live-proof, and runtime mechanics remain future, and Execution Substrate retains admission and runtime ownership.
<!-- RW0_B2_WIRE_CURRENT_STATUS_END -->

<!-- RW0_B2_CAPABILITY_CURRENT_STATUS_BEGIN -->
RW0-B2-Capability implements private, pure, no-I/O worker-mechanism capability
declaration, independently authored supplied observation, and Coordinator
qualification values plus one pure qualification relation. It binds the fixed
RW0-B2-Wire profile `rw0-wire-nwpf-v1` with digest
`470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454`
and consumes one private B1 host-validation snapshot seam after B1 reconstructs
the complete applicable B1, C2A, and lineage graph through protected owners.
It authenticates no source, proves no physical process
behavior, grants no permission or semantic acceptance, persists no fact,
contacts no worker/provider/host, and selects no CLI, App Server, credential,
provider-session, transport, or runtime mechanism. `.docs/rw0-b2-capability.md`
is the sole detailed Capability owner. RW0-B1, RW0-B2-Wire, and
RW0-B2-Capability private semantics are current implemented contracts. RW0-C1
durable phase/evidence mechanics are implemented separately behind private
mutation authority; RW0-D1 artificial offline planner/worker process and capsule mechanics are
implemented separately under the D1 owner. RW0-D2 now has a bounded private
offline source candidate: two guarded validation/review bound effects, checked
C1 evidence, separate fake validator/reviewer/model processes, nine-role input,
and a typed transient preadmission handback. External-copy validation and
independent audit are separate gates; this status grants neither. RW0-C2 physical decision persistence,
live provider/credential/custody, and RW0-E runtime mechanics remain future.
Execution Substrate retains admission and runtime authority.
<!-- RW0_B2_CAPABILITY_CURRENT_STATUS_END -->

<!-- COORDINATOR_RW0_PHASE_ENTRY_CROSS_REFERENCE_END -->

<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
**Current C2 boundary status successor.**

The preceding B1, Wire, Capability, D1, and D2 cross-stage status passages are
preserved stage snapshots. Their present-tense C2-future wording is superseded
for private physical P0/P1 persistence only. This Worker Execution Boundary
still owns neither P0/P1 persistence nor live runtime. The separate Coordinator
C2 owner now has locally committed private physical P0/P1 persistence.
Physical worker transport, live process control, terminal outcome, provider,
credential handling, ES routing, and runtime remain deferred.

The independently accepted, bounded private artificial-offline P0→P1 source is
Git tree `161ed4b544baf970cc26428b9805a106ea0f3edf`, locally committed as
`8704e6c7988250598809f3a0daf88c3e11493488` with sole parent
`4519630d0db967066beb21b4ace5004e76827716`. Its exact-byte local gate
recorded 9,473 collected/executed/JUnit/passed, zero failures, errors, and
skips, and three known Python 3.13 multithreaded-fork `DeprecationWarning`s.
That gate performed no push, upstream creation, PR, merge, publication,
deployment, or product effect. Git objects and refs remain commit and
publication truth; audit, validation, provenance, reports, and status prose
are evidence only.

The separate current C2 implementation records P0 immutable admission history,
never current permission. P1 persists one of five durable decision branches and
creates an acceptance fact only on `candidate_acceptance`; the fact is not
terminal truth, executable permission, live custody, runtime admission, or
deployment authority. Decision Basis v2, guarded-command-digest v2, the
historical work-head witness, universal disclosure posture, and acceptance-only
eligibility are current private mechanics. F03 and F05 remain open nonblocking
observations. There is no live enrollment/custody supplier, terminal outcome,
production provider/worker, ES/Bridge route, product Git effect, public service,
queue, scheduler, deployment, or autonomous loop.
<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure current candidate

The uncommitted `artificial_offline_normal.v1` candidate adds a separate private Coordinator terminal writer on generation-2 migration 0008. It consumes checked P0, phase, Section 41 A, C1 rank-15/V22 and P1 evidence under one fenced transaction and records only the five normal outcomes: accept, repair, replan, terminal_reject and block. The P1 decision remains prior decision history; its acceptance fact is bound only for accept and is never mutated. Cancellation, live supplier/contact, ES routing, Git effects, publication and executable permission remain outside this candidate. See `.docs/rw0-terminal-outcome-physical-closure.md`.

The connected proof uses fake D1/D2 processes in task-owned state. It adds no live worker, transport, ES submit, cancellation acknowledgement or result ingest.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure local commit status

The exact cumulative independent audit accepted Git-compatible tree `4691af58ae0ee3107b4e2e9b6b1508032944e357` for an exact-byte commit gate after its current-ledger consistency repair. The private `artificial_offline_normal.v1` implementation was locally committed as `d3fd741c872b26aa2dfe927ab6dccc638cdcf356`, with sole parent `61d0330aba1160f7f5e7d9c541a325222d1c61e5`, that exact tree, and subject `feat: add RW0 normal terminal closure`. The staged-blob gate collected and passed 9,568 selector-free tests in the same order, with zero failures, errors, skips, xfails, or xpasses and only the three known Python 3.13 multithreaded-fork deprecation warnings. This is a local topic-branch commit; no push, PR, merge, publication, deployment, service/runtime contact, or product effect followed.

Migration `0008_rw0_terminal_outcome` is the current source/catalog suffix. The private fenced terminal owner records only normal `accept`, `repair`, `replan`, `terminal_reject`, and `block`. P0 scope admission, P1 progression decision with its acceptance-only fact, and terminal closure remain separate private fenced transactions and facts. P0 grants no current permission; P1 is prior decision history, not terminal truth. Normal accept binds the immutable acceptance fact without mutation or replenishment.

Common managed-store admission may shape-check the current global-stop singleton before writer fencing. After fencing and protected disclosure, receipt-present terminal read, replay, and recovery verify saved full head postimages, saved stop, and immutable P0/Section 41/C1/P1 predecessors without today's mutable-head or semantic stop checks. A fresh receipt miss retains current-head, current-stop, recording, and disclosure checks. The old whole-operation zero-current-stop-SELECT audit failure remains historical; the accepted two-layer rule supersedes only that overbroad requirement.

Git objects and refs own commit and publication truth. Audit packages, reports, validation, this status text, WA1/QtcM evidence, and provenance are evidence only. The local commit adds no executable permission, three cancel selectors, live supplier/custody gate, worker/provider or physical remote contact, ES/Bridge route, product Git-effect handler, service, queue, scheduler, deployment, or autonomous loop. Existing F03/F05 nonblocking provenance limits retain their recorded scope; this status does not claim their repair. Candidate-stage status elsewhere in this document is preserved history; this marked block is the current local status.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_POST_MERGE_STATUS_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure integrated capability status

Classification: `CURRENT INTEGRATED CAPABILITY STATUS`.

RW0 normal terminal closure was integrated into `trunk_dev` by squash commit `3be0096c163b456c9975326be3eb2c30d2b4bbd1`, with sole parent `61d0330aba1160f7f5e7d9c541a325222d1c61e5` and integrated capability tree `bc10382edd1b2c097fc729e4e168d72e710391fe`. This is the integration anchor for the accepted private `artificial_offline_normal.v1` source. The commit containing this status-only successor is intentionally not self-identified here; Git objects and refs own the current containing commit and publication truth.

The integrated capability records only normal `accept`, `repair`, `replan`, `terminal_reject`, and `block`. P0 scope admission, P1 progression decision with its acceptance-only fact, and terminal closure remain separate private fenced transactions and facts. Migration `0008_rw0_terminal_outcome` remains the source/catalog suffix. P0 grants no current permission; P1 remains prior decision history rather than terminal truth; normal accept binds the immutable acceptance fact without mutation or replenishment.

The accepted implementation staged-tree gate passed 9,568 / 9,568 tests. The accepted status staged-tree focused gate passed 5,655 / 5,655 tests. Independent artifact review accepted the exact status tree `bc10382edd1b2c097fc729e4e168d72e710391fe`. The accepted 9,597-test selector-free FULL record was carried evidence on that tree and was not rerun during integration. No tests ran during the integration operation itself. These records are evidence at their stated scopes, not current Git or runtime authority and not validation of this later status-only correction.

All earlier candidate-stage, local-commit-stage, and cross-stage status passages in this document are preserved historical evidence. Their statements that the implementation was uncommitted, only a local topic-branch commit, or followed by no push, PR, merge, or source publication are stage-local and are not current repository status after the integration anchor above.

The integrated source adds no active-cancel terminal family or executable permission; no live supplier/custody, worker/provider, or physical remote contact; no ES/Bridge route; no Coordinator-owned product Git-effect or runtime publication authority; and no service, queue, scheduler, deployment, or autonomous-runtime loop. Source publication by Git merge does not establish any of those product capabilities. Existing F03/F05 nonblocking provenance limits retain their recorded scope and are not repaired by this status correction.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_POST_MERGE_STATUS_SUCCESSOR_END -->

<!-- RW0_TERMINAL_ANCHOR_0009_STATUS_SUCCESSOR_BEGIN -->
## RW0 terminal anchor registry implementation status

Classification: `CURRENT UNCOMMITTED IMPLEMENTATION CANDIDATE`.

Migration `0009_rw0_terminal_anchor_registry` is the current source/catalog suffix at application schema generation 2. The integrated migration-0008 normal closure status above remains historical. Its four branch-family rows and normal semantic payload are unchanged. Explicit 0008-prefix migration registers each complete existing normal family without rewriting its rows; fresh normal receipts register an immutable anchor in the same transaction. The `rw0_terminal_anchors` phase key is the sole cross-profile route, while the selected checked branch family retains terminal semantic meaning. The registry is no independent outcome, progression decision, authorization, effect basis, or cryptographic replacement.

Migration 0009 admits only `artificial_offline_normal.v1`. Any later branch profile requires a separate explicit migration evolving the family-validation trigger; it must use the same phase-unique registry and cannot introduce a second phase-unique terminal store. This candidate adds no physical cancel capability, cancellation decision or outcome, cancellation effect or request, process observation, external source reconciliation, qualified supplier or custody, successor launch, live execution, Git effect, publication, or deployment. Git objects and refs remain publication truth; this uncommitted source status and validation are evidence only.
<!-- RW0_TERMINAL_ANCHOR_0009_STATUS_SUCCESSOR_END -->

<!-- RW0_TERMINAL_ANCHOR_EVOLUTION_POST_MERGE_STATUS_SUCCESSOR_BEGIN -->
## RW0 terminal anchor evolution integrated capability status

Classification: `CURRENT INTEGRATED CAPABILITY STATUS`.

RW0 terminal-anchor evolution was integrated into `trunk_dev` by squash commit `856c5ac7efd268f70512169c127c91cf097bd200`, with sole parent `69fc836dbaa0e2124b427bc9611de2e0fba77040` and integrated capability tree `575a8da09b4da2539e8e8d6c1deb475a71627d03`. PR #20 and source topic commit `5961cf6bb1dd810eb5260e11b9f9f9054dd41d7d` are source-publication provenance. The commit containing this status-only successor is intentionally not self-identified as the permanent current HEAD; Git objects and refs own current commit and publication truth.

Migration `0009_rw0_terminal_anchor_registry` is the current integrated catalog suffix. Migrations 0001-0008 and existing normal-family rows remain preserved. The `rw0_terminal_anchors` registry owns the sole cross-profile phase route. The selected complete branch family retains terminal outcome, graph, result, receipt, and semantic meaning. The registry is no outcome, progression decision, effect basis, authorization, or independent terminal fact. Migration 0009 admits only `artificial_offline_normal.v1`. A later terminal family requires a separate explicit migration evolving family admission while preserving the same phase-unique registry.

Active cancellation is an authorized subsequent Coordinator capability, but this integrated source implements no cancel decision, cancel effect, request, source observation, reconciliation, or terminal cancel family. Progression pause/resume remains a separate nonterminal lifecycle concern; it is not represented by the terminal registry and is not implemented here. T2-R1 remains optional fixture hardening and is not implemented by this status correction.

The accepted source validation passed 12 / 12, 421 / 421, 194 / 194, 68 / 68, 791 / 791, and a full suite of 9,648 / 9,648 tests, with only the three expected Python 3.13 fork deprecation warnings. All 68 source paths passed staged and committed blob/mode/size equality. No tests ran in the merge gate itself. These records are evidence for the integrated source tree, not validation of this later status-only correction.

Earlier candidate, repair, audit, local-commit, and publication passages in this document remain preserved historical evidence; their uncommitted or unmerged statements are stage-local rather than current repository status. The integrated source adds no live supplier/custody, worker/provider, ES, CP, Bridge, or Temporal route; no Coordinator-owned product Git effect, scheduler, queue, service, successor launch, deployment, or autonomous runtime loop. Source publication does not itself establish product runtime authority.
<!-- RW0_TERMINAL_ANCHOR_EVOLUTION_POST_MERGE_STATUS_SUCCESSOR_END -->

<!-- RW0_ACTIVE_CANCEL_PRE_EFFECT_SAFETY_CLOSURE_STATUS_SUCCESSOR_BEGIN -->
## RW0 active-cancel pre-effect safety closure candidate

Classification: `CURRENT UNCOMMITTED IMPLEMENTATION CANDIDATE`.

Migration `0010_rw0_active_cancel_pre_effect_safety_closure` is a candidate suffix to the exact `trunk_dev` baseline commit `6931ae92126abaf89a75dcf0eb3781f23b4a9363` and tree `1aea0d26cdb578267eed2c0d850c3beef40f81e1`. The prior integrated migration-0009 status remains historical and current predecessor evidence. Migration 0008 and 0009 SQL bytes are unchanged. The candidate production catalog is [0001_initial, 0002_development_program_and_effect_state, 0003_cognitive_proposal_and_selection_state, 0004_rw0_c1_durable_evidence, 0005_section41_post_execution_proposal_family, 0006_rw0_c2_scope_admission, 0007_rw0_c2_progression_decision, 0008_rw0_terminal_outcome, 0009_rw0_terminal_anchor_registry, 0010_rw0_active_cancel_pre_effect_safety_closure], with short sequence catalog [0001, 0002, 0003, 0004, 0005, 0006, 0007, 0008, 0009, 0010]; the current production SQL resource count is `10`.

The private artificial-offline candidate records one immutable generic `cancel/effect_cancellation` decision with a distinct exact receipt and closed safe evidence bindings. Receipt-first same-command replay, changed-command conflict, and exact three-way commit recovery are candidate behavior. A separate fenced verifier rereads Coordinator-owned facts. Exact proven Coordinator-owned mismatch may close one cancel-bound `pre_effect_cancel_basis_unusable` terminal `block`, after the same mismatch is proven again in the terminal transaction. There is no replacement C2B block decision. The `rw0_terminal_anchors` registry remains the sole phase route; the selected complete family owns terminal meaning.

No authenticated current external source authority exists in this candidate. Supplied source evidence is a safe binding, not permission. Missing or unavailable external source evidence is unresolved. Exact local equality returns `locally_current_source_unverified`, never effect eligibility. A missing immutable predecessor is corruption; a complete competing terminal family occupies the phase.

This candidate performs no cancellation effect, fence creation, delivery, request, signal, process control, teardown, terminal cancel, live source contact, ES, CP, Bridge, Temporal, product Git effect, publication, deployment, or pause/resume. It adds no public StateStore route. Independent read-only audit remains required before any integration claim.
<!-- RW0_ACTIVE_CANCEL_PRE_EFFECT_SAFETY_CLOSURE_STATUS_SUCCESSOR_END -->
