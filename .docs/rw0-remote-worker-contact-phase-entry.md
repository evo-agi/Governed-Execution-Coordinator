# RW0 Remote-Contact Phase-Entry Operating Model

<!-- COORDINATOR_RW0_PHASE_ENTRY_CONTRACT_BEGIN -->

## Current-contract registry

Only the bounded registry below is machine-authoritative for the facts that it
owns. Projection rows consume their named owner and create no second authority.

<!-- COORDINATOR_RW0_CURRENT_CONTRACT_REGISTRY_BEGIN -->
Registry version: 1

| Component | Lifecycle status | Contract class | Authority owner | Detail contract | Authority posture | Implementation posture | Explicit nonclaims |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW0-B1 | current_implemented | private_pure_no_io_semantics | RW0-B1 | .docs/rw0-b1-pure-phase-values.md | no_executable_authority | implemented_in_this_repository | source_authentication,executable_permission,persistence,semantic_acceptance,acceptance_latch,es_runtime_fact |
| RW0-B2-Wire | current_implemented | private_pure_no_io_semantics | RW0-B2-Wire | .docs/rw0-b2-wire-protocol.md | no_executable_authority | implemented_in_this_repository | physical_transport,stream_process_plumbing,source_authentication,executable_permission,persistence,semantic_acceptance,es_runtime_fact |
| RW0-B2-Capability | current_implemented | private_pure_no_io_semantics | RW0-B2-Capability | .docs/rw0-b2-capability.md | no_executable_authority | implemented_in_this_repository | source_authentication,physical_process_behavior,executable_permission,semantic_acceptance,persistence,provider_runtime_selection,es_runtime_fact |
| RW0-C | current_partial | c1_durable_evidence_c2_future | RW0-C | .docs/rw0-c1-durable-evidence.md | guarded_private_evidence_only | c1_implemented_c2_not_implemented | completeness,external_standing_authority,executable_permission,physical_process,es_runtime_fact |
| RW0-D | future | physical_custody_transport_process_provider_cancellation_mechanics | RW0-D | this_document | source_owned_physical_facts_no_semantic_progression | not_implemented | executable_authority,semantic_acceptance,es_runtime_fact,live_credentials,network |
| RW0-E | future | separately_authorized_live_proof | RW0-E | this_document | external_standing_authority_required_no_independent_authority | not_implemented | independent_standing_authority,semantic_progression,git,publication,es_runtime_fact |
| Execution Substrate | current_external_owner | route_admission_reliable_submit_runtime | Execution Substrate | external_contract | admission_and_runtime_authority_only | external_contract_not_implemented_here | coordinator_semantic_progression,semantic_acceptance,publication_authority,external_standing_authority |
<!-- COORDINATOR_RW0_CURRENT_CONTRACT_REGISTRY_END -->

## Status, scope, and nonimplementation

Accepted target reset: `.docs/rw0-c2-durable-progression-decision-semantic-contract.md`
owns five-branch reduction, exact replay, and one whole-family recovery classifier.
`.docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md` solely owns immutable
scope admission and acceptance-fact semantics. One scope belongs to an explicitly
standing-policy-admitted Coordinator authority lineage. Across all participating
direct-local programs at most one distinct productive acceptance may commit.
Machine/database replacement, restore, rollback, clone, passive backup, relocation,
a new grant or policy epoch never replenishes it. Later ES operation is separately
governed and non-replenishing. Mutable-latch target requirements are explicitly
superseded. Guard values, physical storage, migration treatment, provisioner,
reader, writer, public export, and runtime remain future; none is implemented.

Classification: `CURRENT IMPLEMENTED CONTRACT` for bounded RW0-C1 private
durable evidence; `ACCEPTED STRATEGIC TARGET` for RW0-C2/D/E and the complete
remote-contact operating model.

RW0-A is a docs-and-contract-tests-only freeze. It defines the bounded target
operating model for one future author-worker contact through one future
Coordinator-owned durable RW0 terminal-outcome fact. It adds no product behavior, authority,
database representation, transport, process, or external effect.

Current executable authorization remains unsupported and fail-closed.

RW0-B1 now implements only the private pure semantic values and relations governed by `.docs/rw0-b1-pure-phase-values.md`; it does not itself persist phase entry. RW0-C1 separately implements private immutable phase establishment and one-member supplied-evidence admission. Neither tranche implements verifier authenticity, physical custody, transport, process, worker, terminal-outcome runtime, latch, Git, ES route, service, scheduler, queue, or autonomous loop.

No phase-entry external effect, verifier, custody, adapter, supervisor, worker, Codex invocation, capsule store, validation or review executor, model invocation, post-execution decision or terminal-outcome runtime, acceptance latch, Git effect, ES route, service, queue, scheduler, or autonomous loop is implemented.

The bounded post-execution pure-owner tranche implements only private, pure,
no-I/O values, projections, evaluators, and helpers. It has no production
caller; performs no runtime or I/O; makes and writes no durable post-execution
decision; adds no migration or SQLite widening; creates no public export; and
acquires no external authority or custody. It implements no C2B progression,
terminal outcome, RW0-D/E, or Execution Substrate work. RW0-C2 durable
decision writing and runtime remain future.

The RW0-C2 durable progression-decision semantic target is now frozen, but not
implemented, in
`.docs/rw0-c2-durable-progression-decision-semantic-contract.md`, its sole
semantic owner. It selects the no-write/block/recovery-unresolved distinction,
finite branch reducer, migration-0002 branch mapping, model non-authority, and
immutable bootstrap-guard dependency. It selects no physical representation or
terminal-outcome design and creates no RW0-D/E or Execution Substrate behavior.

Reports, model output, topology and readiness profiles, transport receipts, and artifacts remain evidence only. They are not identity, executable authority,
acceptance, progression, runtime truth, or publication truth. Current private
RW0-B1 pure semantics and RW0-C1 private durable evidence mechanics are implemented. C2B3D and Section 41 remain the complete executable implemented boundary relevant to this target; RW0-C1 adds no executable authority.

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

## Current entry lineage

VS1B route-neutral genesis commits nine physical rows and eight graph entries.
It establishes the program/version, accepted-intent, work/revision, initialize
decision, membership, privacy-safe WorkSpec binding, preassigned attempt and
candidate, current heads, and receipt without external I/O.

C2B3D author-effect establishment commits ten physical rows and nine graph entries, including one pending authority evaluation and one inert planned initial delivery. It establishes the existing semantic attempt, attempt fence,
author-effect intent, effect fence, sole author command, effect head, initial
delivery attempt, delivery head, and receipt. The pending evaluation and
planned delivery are durable intent and bounds, never executable permission or
evidence that delivery occurred.

Section 41 selection is causally later than C2B3D and does not advance the effect or delivery heads. It reconstructs that exact lineage and records a typed
proposal, Coordinator disposition, and separate selection head. Section 41
remains the sole detailed pre-execution selection semantic owner.

K8 field inventory, in order: program_ref, semantic_attempt_ref, candidate_ref, effect_intent_ref, author_command_ref, attempt_fence_ref, effect_fence_ref, delivery_attempt_ref.

The unchanged Section 41 source remains the sole exact L34 inventory authority.
K8 plus the exact current L34 and selection-head postimage is necessary, but it is not launch authority. The required postimage includes the exact current
proposal, disposition, disposition value, head revision, and head digest.

selected_for_dispatch_gates is planning state, not executable permission. RW0
must consume the existing attempt, candidate, effect, command, fences, and
initial delivery; it must not create competing C2A identities or a second
initial author-effect family merely to launch the selected work.

## Bounded RW0 scenario class

The target scenario is one owner-qualified repository bound to one exact
repository identity, one exact base identity, one exact authorized path set,
and the current WorkSpec and fences. The first productive proof is a docs/docs-contract-only change with a maximum three-path ceiling. It changes no target
runtime, admission, reliable-submit, privileged-operation, deployment, or
publication behavior.

Base or path drift requires replan and a new WorkSpec; it is never absorbed.
The exact repository, base, and paths are selected and verified immediately
before RW0-E rather than embedded as enduring Coordinator architecture.

RW0 retains exactly the existing C2B3D semantic attempt, author effect intent, author command, author candidate, and initial author delivery identity.
No replacement or second semantic attempt occurs in RW0.
No replacement or second author effect occurs in RW0.
No replacement or second author command occurs in RW0.
No replacement or second author candidate occurs in RW0.
No second candidate-authoring worker or source invocation occurs in RW0.
No author relaunch or author redelivery occurs in RW0.
The existing author-candidate delivery identity permits exactly one actual author-candidate delivery in RW0. RW0 permits no author redelivery, author
relaunch, second author effect, replacement author attempt, or second
candidate-authoring invocation. It permits one author-worker invocation, one
candidate and immutable capsule, bounded validation, one independent review,
one typed model proposal, and exactly one durable RW0 terminal-outcome fact.
Validation, independent review, and cancellation each require a distinct current effect intent, current effect fence, and initial delivery under the same originating semantic attempt and author-command lineage.
At most one actual validation-effect delivery, one actual review-effect delivery, and one actual cancellation-effect delivery for the exact currently targeted effect may occur if those effects are reached.
Every reached effect has zero redelivery or retry in RW0; an ambiguous delivery stops and reconciles.
The model-review proposal is a separate source invocation and not a DeliveryEnvelopeV1 effect class.
At most one productive direct-local acceptance is permitted.

The exact C2B decision-kind inventory remains initialize, accept, repair, replan, terminal_reject, block, redeliver, cancel; RW0-A does not add or reinterpret a C2B decision kind.
The future guarded Coordinator writer commits exactly one durable RW0 terminal-outcome fact per run after outcome-specific evidence and current-head checks; it is not a development_decision, effect basis, executable permission, source observation, report, or projection.
The terminal-outcome fact has the finite values accept, repair, replan, terminal_reject, block, cancel; it creates no program version or effect authority by itself.
On a non-cancel branch, exactly one corresponding immutable C2B development_decision of the same kind commits first, and the terminal-outcome fact binds its exact ref and digest without contradicting kind or lineage.
The immutable C2B accept decision creates the bootstrap-acceptance fact atomically in the same guarded Coordinator writer transaction; no terminal-outcome fact is a prerequisite for that fact creation.
The later terminal-outcome accept binds the exact accepted decision ref and digest and the immutable bootstrap-acceptance fact identity and digest from that decision transaction; it never creates, updates, deletes, resets, renews, repairs, or replenishes guard truth.
If the accepted decision committed while the terminal-outcome commit is uncertain, the acceptance fact remains permanent; exact guarded-writer readback precedes any new effect or successor, and recovery creates neither a second accept decision nor a second acceptance fact.
Repair, replan, terminal_reject, ordinary block, and cancel decisions create no bootstrap-acceptance fact and never reset, renew, or replenish guard truth.
On the active-cancel branch, exactly one pre-effect C2B cancel decision bases the cancel effect; terminal-outcome cancel binds that decision and complete post-teardown reconciliation without a second cancel decision.
If active-cancel reconciliation is incomplete, contradictory, stale, or ambiguous, terminal-outcome block binds the same pre-effect cancel decision and unresolved evidence without a C2B block decision.
After exact cancel-decision commit readback and before cancel-effect establishment, the guarded Coordinator writer and current verifier recheck the decision ref/digest, current program/version/attempt/target head, stop version/state, parent grant, subordinate authorization, attempt/effect fences and authorization bases, expiry, revocation, repository, base, path, audience, and preassigned effect/fence/first delivery/target.
If that pre-effect cancel basis is stale, superseded, incompatible, missing, or ambiguous, RW0 establishes no cancel effect, fence, delivery, request, or signal and creates no replacement cancel or block decision, semantic attempt, or author lineage.
The pre_effect_cancel_basis_unusable sub-branch commits one RW0 terminal-outcome block bound to the unusable cancel decision and exact current-head, stop, and verification mismatch evidence, without a C2B block decision, successor, Git effect, or publication.
This pre-effect terminal block can close RW0 before a cancellation effect or teardown; it is distinct from the post-teardown reconciliation block.
If the pre-effect cancel basis remains current and valid, RW0 follows the existing cancel effect, request, acknowledgement, signal, exit, teardown, reconciliation, and terminal-outcome sequence.
No additional cancellation-control decision exists on a non-cancel branch, and no other Coordinator progression decision is created on the active-cancel branch.

Terminal outcomes: accept, repair, replan, terminal_reject, block, cancel.
Every listed terminal outcome ends RW0, launches no successor in RW0, and permits no Git or publication effect.
Every terminal outcome ends RW0, and repair or replan never launches a successor in RW0. A repair or replan decision may describe later successor work,
but that work requires a separately governed phase and does not execute here.

RW0 performs no Git effect and no publication. Commit, push, remote-ref
mutation, PR, merge, deployment, release, and publication counts are all zero.

## Authority model

The external standing-policy authority authors the immutable parent grant, revocation and expiry directives, applicable global-stop directives, and effect ceilings. The existing author attempt fence and author effect fence are inert persisted bounds and are reused exactly; they are not executable permission.
Each persisted author fence retains its exact externally authored authorization-basis reference and digest; those immutable basis bindings are inert lineage and ceiling bounds, not permission.
Before WorkSpec retrieval, author launch, and every later effect, a current verifier proves the complete grant, subordinate authorization, applicable attempt and current effect fences, expiry, revocation, repository, base, path, and current global stop relation. Audience and effect ceilings must also be current and complete.

Coordinator derives narrower subordinate authorization bound to the exact existing author attempt and effect fences only after fresh parent verification; it does not issue replacement author fences. The subordinate record is a strict
subset of the parent authority and retains its exact parent, expiry,
revocation, audience, repository, base, path, and effect-ceiling bindings.
The future Coordinator-derived subordinate authorization is a separate record with its own identity and digest; it neither replaces nor rewrites either existing author fence.
For each existing author fence, the subordinate record binds that fence's persisted authorization-basis reference and digest byte-for-byte and binds the exact existing fence reference and digest.
The current external verifier proves that the parent grant authorizes the immutable fence-bound basis family and that the attempt-fence and author-effect-fence basis bindings are jointly compatible with the same parent-grant family and exact K8/L34 lineage.
The two fence-bound authorization-basis pairs need not equal each other; each must equal its corresponding subordinate-record binding under a freshly verified common parent-grant-family relation.
The verifier also proves the parent grant valid, unexpired, unrevoked, and compatible with the exact audience, repository, base, path, effect class, and ceilings. The subordinate record strictly narrows that verified parent/basis relation and binds the exact persisted attempt-fence and author-effect-fence refs and digests; an independently valid digest proves only identity.
If any basis equality, ancestry, family, scope, freshness, revocation, expiry, repository, base, path, or global-stop relation is false, missing, stale, or ambiguous, no subordinate record is established, no retrieval, contact, author delivery, or launch occurs, no replacement author lineage is minted, and a C2B block decision precedes matching RW0 terminal-outcome block.
A later successor outside RW0 may replan and establish a different semantic attempt/effect lineage under a separately governed phase; RW0 never absorbs an incompatible authorization family or replaces the persisted author fences to make one appear compatible.
Coordinator may establish distinct current effect intents and fences for validation, review, or cancellation within freshly verified parent authority.
Those later current-effect fences do not replace the author effect fence; the
originating attempt fence and author-command lineage remain exact.
Later validation, review, and active-cancellation effects each bind their own current effect fence and subordinate authorization to the same verified parent-grant family and exact originating attempt-fence lineage; none reuses the author effect fence.

Coordinator never mints, renews, widens, reinterprets, or outlives the parent grant and never becomes an independent grant issuer. It cannot author the
verifier's current observation or convert an expired, revoked, ambiguous, or
unavailable verification into permission. The user remains the source of major
direction and risk posture, not a routine per-effect approval service.

A schema, digest, ref, report, readiness result, or model output is never execution permission. Current code implements neither the external verifier nor
executable subordinate authorization or permission. Their exact
schemas, cryptographic encoding, trust root, deployment, and revocation
transport remain later decisions.

## WorkSpec and selected-plan custody

Raw WorkSpec and selected-plan bytes never enter Coordinator SQLite, reports, argv, environment, logs, capsules, or public errors. Coordinator may retain only
the already permitted privacy-safe semantic bindings and future bounded safe
custody observations.

A safe ref or digest is not retrieval permission. Retrieval is one-use, expiring, revocable, out of band, and bound to the exact attempt, effect, and audience. The retrieval authority must also be bound to the exact repository,
base, path ceiling, worker role, and verified parent-authority interval.

Crash or restart discards the bearer and never reuses it. Restart first
reconciles the durable phase-entry state and the custodian-authored consumption,
expiry, revocation, or unknown result. A fresh bearer, if later permitted,
requires fresh current gates and cannot imply that an earlier launch was not
accepted.

The exact custodian, broker, backend, capability issuer, bearer transport, and credential mechanism remain deferred. The target freezes privacy, binding,
freshness, one-use behavior, source ownership, observation, and restart rules;
it does not select a physical implementation.

Standing operator provisioning is only a bounded proof candidate; the user is not a synchronous per-attempt approver and this candidate is not enduring architecture. No chat, model session, report, connector, Bridge ledger, or
Coordinator database becomes hidden physical custody.

## Host, transport, and process boundary

The target uses one owner-neutrally qualified remote Linux host. Qualification
requires current, authenticated, source-attributed evidence for operating
system, architecture, exact worker artifact and protocol support, dedicated
execution identity, isolated workspace, resource and cancellation profile,
credential handoff, capsule-store profile, validation/review tools, capacity,
cleanup posture, observation time, and expiry. Readiness is evidence, not
identity or executable authority.

There is no Mac, Coordinator-host, or alternate-host fallback and no third adapter kind. direct_local_bootstrap remains only the compatibility route token.
It denotes one bounded non-ES delivery route and does not designate a concrete
transport protocol or physical host.

The author-candidate route requires one authenticated bounded contact and one
actual author-candidate delivery. Any reached validation, review, or
cancellation effect uses its own authenticated bounded current-effect delivery
on the same qualified host, never the author delivery.
A host-key-pinned SSH forced command is only a preferred future proof candidate; it is not governing architecture in RW0-A.
RW0-B2-Wire now fixes NWPF representational framing, the closed worker-result grammar, and process/result classification.
Physical transport and stream/process plumbing, authentication
mechanism, direct-local and ES route wrappers, terminal runtime reconciliation,
and process byte/resource ceilings remain open for RW0-C/D/E and ES as
applicable.

The roles are separate: an ephemeral direct-local adapter handles transport; a
remote supervisor owns process lifecycle, deadlines, cancellation requests,
stdout/stderr capture, and cleanup; the author worker owns candidate production;
the capsule builder and store own sealing and custody; the validator owns the
validation observation; the independent reviewer owns its review observation;
the model adapter owns source invocation and typed proposal production; and
Coordinator alone owns semantic progression.

No adapter, supervisor, worker, builder, store, validator, reviewer, or model adapter receives Coordinator SQLite or writer authority. The author process uses
a dedicated unprivileged identity, attempt-scoped isolated workspace, closed
unrelated descriptors and environment, bounded wall/CPU/memory/disk/output
resources, one process group, explicit cancellation and reap behavior, and no
sudo, Docker socket, Coordinator state, unrelated repository, or capsule-store
write access. Exact sandbox technology remains deferred.

Protocol stdout is bounded evidence only. Stderr is private, capped, redacted,
and prohibited from Coordinator state, reports, and the capsule. Exit zero,
valid-looking output, transport acknowledgement, or process disappearance is
never semantic acceptance.

## Identity and fact ownership

Every row below retains one authoritative author, recorder, or physical
custodian. A safe Coordinator projection never takes over source truth.

| Fact or material | Authoritative writer/source/custodian | Safe Coordinator role | Non-collapse rule |
| --- | --- | --- | --- |
| program/work | Existing Coordinator progression writer | Reconstruct exact current VS1B program/work lineage | Program/work is not attempt, effect, delivery, or permission. |
| semantic attempt/candidate | Existing Coordinator C2B3D writer; worker later authors candidate bytes | Bind existing refs/digests | Launch does not mint a replacement attempt or candidate identity. |
| author effect intent/command/fences | Existing C2B3D intent, command, and inert attempt/effect fences with their exact externally authored per-fence authorization-basis refs/digests; future Coordinator-derived narrower authorization is a separate record | Verify each immutable basis pair byte-for-byte against its corresponding subordinate binding, both existing fence refs/digests, the common parent-grant family, current heads, and ceilings | Existing author fences are not newly issued at phase entry or executable permission; incompatibility blocks without replacement. |
| existing author delivery attempt | Existing C2B3D initial author delivery identity | Advance only through future guarded mutations | Author delivery is not validation, review, cancellation, invocation, acknowledgement, result, or decision. |
| later current effects and deliveries | Guarded Coordinator writer establishes distinct validation, review, or cancellation intents, current fences, subordinate bindings, and initial deliveries within verified parent authority | Bind each reached effect to the originating attempt, applicable attempt fence, author-command lineage, and same verified parent-grant family | A later effect neither reuses the author effect fence nor the author delivery and is never blindly redelivered. |
| Section 41 proposal/disposition/head | Proposal source and Coordinator disposition writer | Require exact current K8, L34, and head postimage | Proposal is not disposition; selection is not launch authority. |
| phase-entry/contact claim | Future guarded Coordinator writer | Commit a receipt-backed no-contact claim before external contact | Claim is not authority, retrieval, or delivery. |
| authority/host/custody gates | External verifier, host-owning source, and physical custodian | Record only bounded current evaluations/observations | Gate evidence does not collapse into permission or identity. |
| process launch and control | Direct-local supervisor owns process-launch attempt, process-group control, deadline, signal, and route-local supervision; OS/supervisor owns exit and deadline facts | Record bounded source evidence only | Process launch does not prove worker start, completion, or candidate capture. |
| worker start/completion/candidate capture | Worker process is the underlying fact owner and canonical author of `worker_started`, `worker_completed`, and `candidate_captured` | Ingest the worker-authored observation through the selected carrier | Adapter or supervisor carriage does not transfer worker authorship. |
| source invocation and observation | Exact external source kind and invocation | Apply the closed ingest disposition algebra | Invocation, observation, ingest, and desired state remain distinct. |
| capsule manifest/portable digest/custody | Capsule builder and private immutable store | Retain safe manifest/portable/custody bindings | Portable identity excludes storage path, host, bearer, and backend metadata. |
| validation/review | Validator and independent reviewer | Retain bounded exact-capsule observations | Successful evidence is not acceptance. |
| model proposal | Model adapter and configured model invocation | Retain typed proposal and safe evidence bindings | Proposal, provider response, and Coordinator decision are distinct. |
| C2B development decision | Guarded Coordinator writer | Bind one same-kind pre-outcome decision on a non-cancel branch, or the exact pre-effect `cancel` decision on active cancellation; an accepted direct-local decision atomically creates the immutable acceptance fact | A pre-effect cancel decision bases its effect only while current and compatible; neither a stale cancel decision nor a later outcome can create an acceptance fact. |
| RW0 terminal outcome and immutable bootstrap acceptance guard | Future guarded Coordinator writer | Commit one separate durable terminal-outcome fact bound to current lineage, decision, evidence, and heads; terminal `accept` binds the exact committed acceptance-fact identity/digest | Outcome is not a development decision, effect basis, or guard mutation; no external source creates acceptance truth or decides progression. |

Delivery, source invocation, observation, candidate, capsule, validation, review, model proposal, C2B decision, RW0 terminal outcome, and Git effect remain distinct facts.
Validator and reviewer evidence, model output, reports, IM evidence, and transport receipts are non-authoritative evidence.

## Target fact timeline

This is a target causal timeline, not an implemented schema or process:

1. **pre-contact reconstruction** — a guarded Coordinator operation reconstructs the current VS1B, C2B3D, and Section 41 K8/L34/head lineage, current effect and delivery heads, applicable global stop, and exact repository/base/path bounds.
2. **phase-entry claim** — Coordinator commits a receipt-backed, no-contact claim with current-head CAS semantics before verifier, host, or custodian contact.
3. **fresh authority, host, and custody gates** — outside the transaction, the owning sources produce current bounded facts; Coordinator later records only safe bindings after rereading the claim and current state.
4. **one-use retrieval** — the physical custodian redeems the exact attempt/effect/audience-bound authority and authors consumption, failure, revocation, expiry, or unknown truth.
5. **pre-send claim** — Coordinator commits the exact existing author delivery's current pre-send transition before transport I/O.
6. **one actual author-candidate delivery** — the ephemeral adapter makes one bounded author contact using that existing delivery identity, with no redelivery or relaunch.
7. **process launch and worker start observations** — the supervisor owns the process-launch attempt, process-group control, deadline, signals, exit, and route-local reconciliation. The worker process owns and canonically authors worker_started, worker_completed, and candidate_captured observations. The adapter or supervisor may carry them but does not become their author. Supervisor process launch does not prove worker_started; worker_started does not prove completion or candidate capture.
8. **candidate capture and capsule seal** — the worker produces candidate bytes; the separate builder/store create and retain the immutable capsule.
9. **validation observation** — if reached, a distinct `validate_candidate` intent, current fence, and initial delivery precede the validator invocation on an exact-base-plus-capsule reconstruction. The validator authors its observation.
10. **independent review observation** — if reached, a distinct `review_candidate` intent, current fence, and initial delivery precede a reviewer invocation that reads the immutable reconstruction without author write authority.
11. **typed model proposal** — a separate source invocation receives bounded safe context and emits one non-authoritative typed proposal, not a DeliveryEnvelopeV1 current-effect delivery.
12. **Coordinator semantic decision and possible acceptance-fact creation** — on the normal branch, the guarded writer rereads current evidence, authority, global stop, fences, and heads and commits exactly one C2B accept, repair, replan, terminal_reject, or block decision of the eventual outcome's kind. The productive-direct-local `accept` decision atomically creates the immutable acceptance fact in that decision family; every nonaccept decision creates no fact.
13. **RW0 terminal outcome** — only after that decision commits does the future guarded writer commit the separate matching terminal-outcome fact. Terminal `accept` binds the exact decision ref/digest and acceptance-fact identity/digest without guard mutation. Until the outcome commits or exact readback resolves uncertainty, RW0 is not terminally closed and permits no new effect or successor.
14. **teardown and custody terminal facts** — the supervisor and custodians author process reap, workspace teardown, retained-capsule, and unresolved-cleanup facts without erasing the normal-branch terminal outcome.

On the normal branch, Coordinator commits one C2B accept, repair, replan, terminal_reject, or block decision after validation, review, and model proposal complete or become conclusively unavailable. The accepted direct-local decision alone atomically creates the immutable acceptance fact; nonaccept decisions create none. The matching RW0 terminal-outcome fact follows the decision and binds its exact ref, digest, kind, lineage, and the immutable acceptance-fact identity/digest when accepting, without mutating guard truth. Cleanup and custody facts follow without changing the terminal outcome.
No successor launches, and no Git or publication effect follows.

The active-cancellation branch is separate from that normal sequence. The existing immutable C2B cancel decision commits before the cancellation effect, preassigns its effect intent, fence, first delivery, and exact target, and is the cancellation effect's exact basis_decision_ref.
Commit uncertainty for that pre-effect decision is resolved by exact guarded-writer readback before currentness verification or effect establishment. The guarded writer and current verifier then recheck the exact decision, target head, stop version/state, parent/basis/fence family, authority freshness, and preassigned effect/fence/first delivery/target. A stale, changed, missing, incompatible, or ambiguous basis enters `pre_effect_cancel_basis_unusable`: no cancel effect, fence, delivery, request, or signal is established or emitted, and no replacement cancel or block C2B decision is made. The guarded writer commits one terminal-outcome `block` bound to that unusable decision and exact mismatch evidence, even before teardown; source-owned supervision and cleanup facts may continue, but the outcome never asserts process exit or semantic cancellation. No successor, Git effect, or publication follows.
Only a current compatible basis permits this path. Coordinator establishes the distinct `cancel_effect` intent, current effect fence, subordinate authorization binding, and initial cancellation delivery before an external request. It creates no second cancel decision after the effect. The pre-effect decision does not terminate RW0 or create a bootstrap-acceptance fact.
The C2B cancel decision is neither a cancellation request, acknowledgement, signal, process exit, workspace teardown, source reconciliation, semantic abandonment, semantic cancellation, nor RW0 terminal closure.
Request, acknowledgement, signal delivery, process exit, and mutable workspace teardown remain distinct source facts in that order; each may be absent or unknown and none implies the next.
Post-teardown source-native reconciliation covers process-group and descendant state, worker observations, request, acknowledgement, signal, exit, workspace cleanup, capsule custody, and applicable delivery and source receipts.
Only after that source-native reconciliation proves every required terminal relation complete and non-ambiguous may the guarded writer commit the one RW0 terminal-outcome fact with value `cancel`. If reconciliation is incomplete, contradictory, stale, or ambiguous, it commits terminal-outcome value `block` bound to the same pre-effect cancel decision and unresolved evidence, without a C2B block decision. This post-teardown branch is distinct from the unusable pre-effect basis branch.
No other Coordinator progression decision is created on the active-cancel branch.
The pre-effect C2B cancel decision does not prove terminal cancellation or block, and the later terminal-outcome fact cannot basis its already-established cancel effect.
Source reconciliation alone does not establish terminal outcome; only the guarded Coordinator writer commits the fact after rereading current evidence and heads.
Neither request, acknowledgement, signal, exit, teardown, nor reconciliation alone establishes terminal closure. No successor launches, and no Git or publication effect follows.

No external I/O occurs inside a Coordinator transaction. Each external phase is
separated by a durable intent/claim and later source-observation ingest. No
report, in-memory flag, filesystem marker, or adapter log is hidden progression
state.

## Failure, ambiguity, cancellation, and recovery

| Failure or unknown | Fact owner and safe observation | Coordinator response and retry rule | Global stop, restart, and possible artifact |
| --- | --- | --- | --- |
| phase-entry commit uncertainty | Coordinator SQLite and exact recovery probe | No contact; resolve as committed exact, definitely absent, or unresolved. Unresolved stops. | Restart performs fresh-writer readback. No candidate or capsule exists. |
| stale, missing, or ambiguous authority or host gate | External verifier or host-owning source | Record blocked/unknown; do not retrieve or launch. A later check is a fresh observation, not reinterpretation. | Global stop blocks. No candidate or capsule exists. |
| incompatible or ambiguous immutable authorization-basis family | External verifier proves the current parent, each persisted per-fence basis pair, and common family relation | Do not establish the subordinate record, retrieve, contact, deliver, or launch; do not replace author lineage. Commit the non-cancel C2B `block` decision, then its matching RW0 terminal-outcome `block`. | A later separately governed successor may replan; this RW0 run never absorbs the mismatch. |
| retrieval failure or unknown consumption | Physical custodian | Record/reconcile consumption truth; never reuse the bearer and never infer no launch. | Stop closes/revokes the capability. Candidate exists only if launch separately occurred. |
| delivery rejection or unknown acceptance | Transport/supervisor source-native record for the exact current effect | Record exact observation and stop RW0; the same effect is never redelivered. | Restart reconciles source truth, never adapter memory. Candidate or capsule may exist after unknown author acceptance. |
| process start, exit, or deadline ambiguity | Supervisor and OS evidence | Ingest bounded observations; never equate exit with rejection, completion, cancellation, or absence. No relaunch. | Commit and resolve the pre-effect C2B `cancel` decision before its cancel effect and request. Candidate may exist. |
| candidate capture or capsule seal ambiguity | Worker, builder, and store | Keep capture and seal facts distinct; reconcile store before assuming absence; block later progression. | Stop prevents new phases. Candidate and/or capsule may exist. |
| validation, review, or model inconclusive outcome | Validator, reviewer, or model adapter | No accept and no blind reinvocation; reconcile the source or commit a nonaccepting decision. | Stop prevents the next phase. Capsule remains retained. |
| C2B decision commit uncertainty | Coordinator SQLite and exact recovery probe | Resolve the pre-effect `cancel` decision before cancel-effect establishment, or resolve a non-cancel same-kind decision before its terminal-outcome fact. Never fabricate a second cancel or block decision. | Fresh-writer readback only; unresolved C2B decision blocks further contact. |
| pre-effect cancel basis unusable after decision readback | Guarded writer and current verifier compare the exact decision, current target head and stop version/state, parent/basis/fence relation, and preassigned effect/fence/delivery/target | Establish no cancel effect, delivery, request, or signal; create no replacement C2B cancel/block decision or author lineage. Commit one `pre_effect_cancel_basis_unusable` RW0 terminal-outcome `block` bound to the unusable decision and exact mismatch evidence, even before teardown. | Source-owned supervision and cleanup may continue without implying cancellation. RW0 launches no successor and performs no Git or publication effect. |
| accepted decision committed, terminal outcome uncertain | Coordinator SQLite and exact guarded-writer readback | The accept decision and its atomic acceptance fact remain committed. Resolve the separate terminal-outcome fact without another accept decision or acceptance fact. | Until exact outcome resolution, no new effect, successor, Git, or publication occurs. |
| RW0 terminal-outcome commit uncertainty | Future guarded Coordinator writer and exact recovery probe | Resolve the exact terminal-outcome fact through guarded-writer readback; do not emit a second fact, decision, effect, or acceptance-fact creation speculatively. | Unresolved terminal outcome permits no new effect or successor; committed accept is not erased. |
| cleanup or custody ambiguity | Supervisor, workspace custodian, and capsule store | Perform only source-owned idempotent cleanup/reconciliation; never infer semantic cancellation. Unresolved process or workspace cleanup blocks terminal-outcome `cancel`. | Restart reconciles processes and custody. Candidate/capsule may persist. |
| post-teardown source reconciliation incomplete or contradictory | Supervisor/OS, worker, workspace and capsule custodians, and delivery sources retain their own facts | After teardown, reconcile descendants, worker observations, request/ack/signal/exit, workspace cleanup, custody, and receipts. Commit terminal-outcome `cancel` only when all required terminal relations are complete and unambiguous; otherwise commit terminal-outcome `block` without a second C2B decision. | No source fact or reconciliation alone commits an outcome; no successor, Git, or publication follows. |

Global stop prevents every not-yet-started productive phase. If productive
work is already active, Coordinator commits exactly one immutable pre-effect C2B
`cancel` decision and resolves its commit outcome before a fresh currentness
check. If stop-version, target-head, or authority relations have drifted, the
unusable pre-effect basis terminally blocks RW0 without establishing an effect
or emitting a request. Only when that exact decision remains current and
compatible does Coordinator establish the distinct cancellation
effect/fence/subordinate binding/delivery before any external request. That
decision is the effect basis, not RW0 terminal closure.
Already-authored evidence is retained and ingested without promoting it.

For a current compatible cancel basis, cancellation facts remain ordered and non-collapsible:

pre-effect C2B cancel decision → cancellation effect/fence/subordinate binding/delivery → request → acknowledgement → signal → process exit → workspace teardown → source-native reconciliation → RW0 terminal-outcome cancel or block

Acknowledgement does not prove signal delivery; signal does not prove exit;
exit does not prove teardown, candidate absence, abandonment, or semantic
cancellation; teardown does not prove reconciliation; reconciliation does not
itself commit a terminal-outcome fact. Restart uses only durable Coordinator facts plus
authoritative source reconciliation after teardown. Contradiction becomes
conflict or ambiguity and terminal-outcome `block`, never inferred success or permission
to retry.

## Capsule, validation, review, model, and decision

The builder seals a canonical immutable manifest for only the authorized paths
and every referenced before/after blob, length, digest, operation, and mode.
Validation and review materialize the exact authorized base plus that capsule
in new read-only or separately isolated workspaces. They never examine the
author's mutable workspace as the acceptance object.

The capsule excludes WorkSpec, selected plan, prompts, transcripts, provider
JSONL, stdout/stderr, credentials, endpoints, trust material, retrieval
authority, physical store paths, unrelated files, and arbitrary workspace
metadata. Its portable identity excludes backend, encryption, host, retention,
and retrieval details. A store ref or digest grants no retrieval authority.

The validator owns finite `passed`, `failed`, `inconclusive`, or `not_run`
evidence. The independent reviewer owns finite `passed`, `failed`, or
`inconclusive` evidence under a distinct role/invocation, exact-capsule binding,
read-only access, and no author or Coordinator-writer authority. Neither result
is acceptance.

The model adapter records a separate invocation and a typed proposal bound to
the capsule, worker evidence, validation, review, standing policy, current
authority, global stop, risk lane, and effect ceiling. Raw prompts, responses,
reasoning, sessions, credentials, and provider metadata remain private and are
not durable program truth.

Coordinator alone commits the applicable C2B decision and the distinct future
RW0 terminal-outcome fact through guarded writer authority. The former obeys
the unchanged C2B decision grammar; the latter is durable RW0 terminal closure,
not a `development_decision`, an effect basis, permission, or a source fact.
The terminal-outcome fact binds the exact phase-entry identity, C2B3D and Section 41 lineage, applicable decision refs and digests, effect/delivery/source evidence, reached capsule/validation/review/model evidence, current global-stop and head state, and any immutable bootstrap-acceptance fact identity and digest.
The terminal-outcome semantic role is frozen here, while its identity, digest, row, receipt, graph, table, migration, application generation, and public API representation remain deferred.
Terminal outcomes: accept, repair, replan, terminal_reject, block, cancel.
Every listed terminal outcome ends RW0, launches no successor in RW0, and permits no Git or publication effect.
The normal branch commits one same-kind C2B non-cancel decision before its
matching terminal-outcome fact. The active-cancel branch commits one pre-effect
C2B `cancel` decision as the cancel-effect basis, then one terminal-outcome
`cancel` after complete post-teardown reconciliation or one terminal-outcome
`block` when reconciliation is unresolved; it creates neither a second cancel
decision nor a C2B block decision. The pre-effect cancel decision alone proves
neither terminal value. A stale or incompatible pre-effect cancel basis instead
commits one terminal-outcome `block` before effect establishment, with no
replacement C2B decision or cancellation request. Only the committed
productive-direct-local `accept` decision creates the immutable acceptance fact,
atomically with that decision family; the matching terminal-outcome fact binds
the exact decision and acceptance-fact identity/digest without guard mutation.
No terminal-outcome value permits a successor, Git effect, or publication inside RW0.
Terminal-outcome commit uncertainty requires exact guarded-writer readback; unresolved outcome prevents new effect or successor and recovery never fabricates another accept, cancel, or block decision or acceptance fact. A committed accept decision retains its permanent acceptance fact during unresolved outcome recovery.
Commit uncertainty must be resolved before any later contact. No Git effect
follows the RW0 terminal outcome.

The minimum capsule is retained through validation, review, proposal, decision, and terminal outcome,
and every unresolved recovery or cancellation case, and remains available for
a separately governed later Git handoff. Acceptance alone is not a garbage-
collection signal. Exact backend, encryption, retention duration, quota,
archival, recovery, and garbage collection remain deferred.

## ES and IM ownership

Execution Substrate owns ES-route admission, reliable submit, runtime lifecycle, cancellation, runtime identity and credential handoff, route correlations, and retained results. It also retains resolved effective-plan and runtime-profile
compatibility authority for its route. The direct-local supervisor owns only route-local process control, cancellation-request delivery, route receipts, and source-native reconciliation facts. The direct-local adapter transports those
bounded facts; Coordinator owns semantic progression, safe observation ingest,
and the separate RW0 terminal outcome, never route lifecycle. Direct-local never claims ES-route facts or creates a parallel ES lifecycle store. It cannot scrape Nomad.

Later conformance must run the same worker artifact/version and the same C2A
semantic command, fence, observation, capsule, replay/conflict, ambiguity,
cancellation, and privacy rules through both routes. Only transport wrappers,
source attribution, and route-owned correlations may differ. Current ES
unkeyed submit is not a reliable fallback, and ES implementation sequencing
requires a separate owner-repository decision.

Infrastructure Manager output may corroborate environment profile, copied
provenance, diagnostics, or readiness observations. It cannot author the
parent grant, host identity, execution permission, WorkSpec custody, runtime
truth, semantic acceptance, or progression. Coordinator must consume
owner-neutral evidence without importing IM as a mandatory runtime dependency.

Neither Execution Substrate nor Infrastructure Manager is modified, adopted as
an enduring Coordinator implementation dependency, or allowed to define this
target through uncommitted local overlays.

## Tranche map and open decisions

The bounded sequence is:

1. **RW0-A — phase-entry contract freeze** — docs and direct contract tests only; no source, schema, I/O, runtime, worker, or external contact.
2. **RW0-B — current private pure protocol, value, Wire, and Capability contracts** — B1, NWPF representational framing, worker-result grammar, process/result classification, and Capability composition are current; no SQLite, filesystem, process, network, or model effect.
3. **RW0-C — durable phase-entry and observation state** — future RW0-C2
   durable progression decision, immutable bootstrap guard, terminal outcome, and any
   later physical suffix remain separate from current RW0-C1 private durable
   phase establishment and one-member supplied-evidence admission; no external
   contact.
4. **RW0-D — offline worker, supervisor, and capsule proof** — D1 now implements the bounded artificial fake-planner/fake-worker process and capsule spine; D2 evidence/review/model closure remains future, with no network or live credentials.
5. **RW0-E — one live qualified-host proof** — one future externally authorized bounded author-candidate contact with separately bounded later current-effect deliveries if reached, through exactly one separate durable RW0 terminal-outcome fact and stop; the active-cancel branch first commits the existing C2B `cancel` decision as its cancel-effect basis, never a second cancel or block decision; no Git or publication.

The authority-authorship decision is resolved: external standing policy owns
the immutable parent grant and directives; Coordinator target derives only
narrower parent-bound subordinate authorization records and, for later distinct
current effects, their applicable fences. The existing C2B3D author fences and
their external authorization-basis bindings remain immutable. Coordinator never
becomes independent external authority.

The following architecture-defining decisions remain open and block only the
named future owner tranche or ES phase:

| Deferred decision | Earliest blocked tranche |
| --- | --- |
| authority verifier deployment, trust roots, grant encoding, and revocation transport | RW0-C / RW0-E |
| C2 current-posture verification and guard physical integration | RW0-C / RW0-E |
| offline process/custody mechanics and fake capability behavior | RW0-D |
| first-live independent enrollment supplier, continuous original process/storage custody, and complete fencing conformance | RW0-E |
| phase-entry claim, retrieval-event, host-observation, terminal-outcome, guard physical representation and decision-family receipt/idempotency design | RW0-C |
| supervisor/process-group strategy, fake CLI transcript protocol, and capsule/tool implementation | RW0-D |
| live credential/account selection and qualified-host evidence | RW0-E |
| ES route implementation, reliable-submit, runtime, cancel, and result APIs | ES phase |
| direct-local/ES wrapper choice | RW0-D / RW0-E / ES phase |

Migration 0004, its phase/evidence tables and receipts, and its generation-2
catalog treatment are implemented by RW0-C1. Terminal-outcome and
immutable bootstrap-guard representation remain future RW0-C2 work and are not
implemented by RW0-A or RW0-B.
The separate RW0-C2 semantic contract resolves the progression-decision branch
algebra only. A later bounded-hybrid physical freeze still owns the migration-
0005 question, and the accepted bootstrap guard owner now freezes lineage/admission/acceptance
semantics. Physical representation, provisioning, safe values, and mutation
integration remain mandatory future freezes before any accept writer is callable.
No open decision blocks RW0-A.
RW0-B is current and implemented; no unresolved decision blocks it. Each later tranche requires its own bounded
reconnaissance before source work when its governing decisions remain open.
The `rw0-c2-single-realization-proof-v1` target in
`.docs/rw0-c2-first-live-proof-posture.md` selects the first RW0-E support
conditions only. RW0-D uses artificial source observations and disposable
state without a production continuity supplier, while still requiring its
own offline process/custody implementation. RW0-E requires a concrete
independent enrollment and privileged custody supplier to prove launch
uniqueness, nontransferability, original-storage isolation, denied
restore/clone/restart paths, complete fencing, and supervisor fail closure.
Full-custodian and acceptance-focused checkpoint protocols are unselected
successor options, not first-live entry requirements.

## Non-authoritative initial proof fixture candidate

The earlier reconnaissance recorded one possible first-proof fixture: Execution
Substrate commit `b92bd9884106154d25342e1573dcc4c312311436` and candidate paths
`PLANS.md`, `.docs/system_overview/hybrid_integration_architecture_adr.md`, and
`docs_contract_test.go`.

This is stale-able evidence only. It is not a durable Coordinator contract, not execution permission, and not a required future base or path set. It carries no
authority merely because the commit or paths appear here. Immediately before RW0-E, the exact base and paths must be selected and verified again. Any drift
requires replan and a new WorkSpec under the scenario-class ceiling.

<!-- RW0_D1_CURRENT_STATUS_BEGIN -->
RW0-D1 is a current private artificial offline process and capsule proof. The guarded Coordinator program-initialization, C2B3D author-effect, Section 41 selection, and RW0-C1 phase writers remain the sole durable owners. A separate fake planner and fake coding worker run under the bounded D1 supervisor; the parent captures one temporary candidate, builds and independently verifies a CandidateCapsuleManifestV1, removes the mutable workspace, and returns a transient typed handback with separate parent-only disposable-state custody. The preassigned fixture base_git_oid is a WorkSpec coordinate, not Git authentication. RW0-D2 validation/review/model closure is next; RW0-C2 physical decision persistence follows D2. D1 grants no live provider/credential or source authentication, ES route, Git/publication effect, terminal acceptance, public service/CLI, or RW0-E runtime authority. The detailed implementation owner is .docs/rw0-d1-offline-process-and-capsule-spine.md.
<!-- RW0_D1_CURRENT_STATUS_END -->

<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
**Current C2 phase-entry status successor.**

The earlier phase maps, B2 Capability projection, and D1 block remain exact
stage snapshots. A separate C2 owner now implements and locally commits
private artificial-offline P0/P1 representation, safe values, writers,
replay/readback, and recovery. This does not make a live accept writer callable.
Terminal-outcome persistence, real supplier/custody, physical worker contact,
RW0-E, provider, credentials, ES routing, and runtime remain future.

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

<!-- COORDINATOR_RW0_PHASE_ENTRY_CONTRACT_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_BEGIN -->
**RW0 normal terminal closure current candidate.**

The uncommitted `artificial_offline_normal.v1` candidate adds a separate private Coordinator terminal writer on generation-2 migration 0008. It consumes checked P0, phase, Section 41 A, C1 rank-15/V22 and P1 evidence under one fenced transaction and records only the five normal outcomes: accept, repair, replan, terminal_reject and block. The P1 decision remains prior decision history; its acceptance fact is bound only for accept and is never mutated. Cancellation, live supplier/contact, ES routing, Git effects, publication and executable permission remain outside this candidate. See `.docs/rw0-terminal-outcome-physical-closure.md`.

This satisfies the normal persistence portion of RW0-C only in the private artificial-offline profile. All three cancel-shaped paths remain unimplemented. First-live RW0-E still requires gate-B supplier qualification.
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
