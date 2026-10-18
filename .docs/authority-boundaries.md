# Authority Boundaries

## C1 Classification Key

Authority statements distinguish `CURRENT IMPLEMENTED CONTRACT`, `CURRENT
COMPATIBILITY EDGE`, `ACCEPTED STRATEGIC TARGET`, `FUTURE IMPLEMENTATION
DETAIL`, `DEFERRED OR BLOCKED EFFECT`, and `PROCESS-ONLY GOVERNANCE`. The
authoritative C1 composition record is
`.docs/autonomous-software-development-operating-model.md`.

## Current Authority

The NWP Coordinator cannot self-authorize. A valid lease digest proves only
schema validity, canonical form, digest match, time-window shape, bounded field
shape, and finite-backlog binding shape. It does not prove authorization or
executability.

The production/default authorization provider is unsupported and fail-closed.
It returns `authorized=false`, `executable=false`, and
`unsupported_authorization_model`. Typed authorization decisions may represent
external operator/repo policy truth, but P1/P1.1 implements no executable
authorization provider and no trusted-local bypass.

B3a does not add authorization verification. It aligns
`AuthorizationDecision` with schema 0001 by binding it to
`lease_identity_decision_ref`, keeps `unsupported` as the only current
production posture, requires internally coherent authorization flags and
reasons, and classifies `operator_policy` as unsupported by the accepted
runtime architecture until a separate authorization contract exists.

Bridge remains the current guarded adapter/evidence surface. It is not the
worker owner or a direct-local trigger. Bridge ledgers and reports are
evidence/projection and never become Coordinator durable state, lifecycle truth,
retry/repair authority, scheduling policy, acceptance, or hidden program state.

Control Plane remains relevant only to current maintained MVP/demo
compatibility, migration, filming, freeze, reference, or retirement context. CP
does not become A2 coding-work state owner and is not part of the target
autonomous-development topology.

Execution Substrate remains execution admission/runtime authority and does not
delegate ES route, TLS, lifecycle, runtime-profile compatibility, runtime
identity, credential-handoff boundaries, runtime cancellation request, retained
results, or runtime truth to the Coordinator.

Maintenance Agent currently retains only its bounded current-contract scan,
proposal, approval-record, route-matrix/eligibility handling, and bounded
foreground invocation behavior. MA is not selected as the general authorization
issuer, renewal authority, deployment authority, runtime/lifecycle authority, or
durable operational-progression owner. Maintenance leases and coding leases are
separate namespaces and are not interchangeable.

Infrastructure Manager outputs remain readiness evidence, bootstrap provenance,
diagnostics, and profile/support evidence. IM is not durable progression,
operational acceptance, owner-route, orchestration, or runtime authority. Its
outputs are not Coordinator state truth. MA/IM survival, migration, or retirement
remains open.

Reports, ChatGPT state, connector state, API sessions, Symphony, and adapter
evidence do not create durable A2 state, lease authority, execution authority,
acceptance, commit authority, or publication authority. A report or adapter
projection does not create durable A2 state.

## Strategic Target Fact Ownership

Coordinator may later become the component-level durable progression owner for
governed programs admitted to its target operating model through conceptual
shared owner-neutral progression mechanics and separately versioned
software-development and bounded operational-change domain contracts. Current
implementation remains coding-work-specific bounded durable SQLite mutation
authority only. The target does not select one universal queue, backlog, lease,
work-item/state grammar, state machine, retry or repair counter, dependency
receipt model, global stop, acceptance grammar, effect vocabulary, schema,
service, module, scheduler, or reconciler. C1 does select a coding-specific
staged worker source/process route without implementing it: initial source and
release machinery in the Coordinator repository, a separate OS worker process,
a bounded direct-local bootstrap/proof adapter, and later ES routing through the
same versioned contracts.

The target-only operational authority split is:

- Git and owning repository retain desired bytes and owner action definitions;
- owning route/component repository retains action meaning, route eligibility,
  preconditions, privilege and runtime-profile requirements,
  identity/signing/secret custody, idempotency and re-entry, post-check meaning,
  rollback, compensation, containment, and redaction;
- external owner/policy authority retains grant issuance and effect ceilings;
- target Coordinator may safely verify and bind allowlisted immutable authority
  references and own durable progression decisions;
- Execution Substrate retains authentication, reliable keyed submit when that
  future contract is implemented, admission, runtime handoff, lifecycle
  projection, cancellation-request, and retained-result boundaries;
- runtime/provider/host source retains observed runtime facts;
- Maintenance Agent retains bounded current scans, proposals, approval records,
  route eligibility handling, and foreground invocation only;
- Infrastructure Manager retains evidence, provenance, diagnostics, and
  profile/support evidence only;
- Control Plane retains current MVP/demo workflow and exact-scope controls only;
- Bridge/connector retains transport, session, and report evidence only;
- CI/probes/owner systems retain validation observations;
- Git retains object and ref truth.

Coordinator may verify and bind allowlisted immutable authority references. It
may not mint, renew, widen, translate, reinterpret, or self-supersede operational
authority. A digest proves byte identity only. Owner-blocked routes remain
blocked.

Execution Substrate continues to own execution admission, runtime-profile
compatibility, prepare and submit handoff, runtime identity and
credential-handoff boundaries, submitted execution lifecycle projection, runtime
cancellation request boundaries, and retained execution results. Git owns
repository object and ref truth. CI or validating runtimes own observed
validation results.

The Worker Execution Boundary is the reserved transport-neutral boundary between
Coordinator-owned durable development progression and ES-owned runtime
authority. The bounded direct-local supervisor/adapter and later ES adapter may
own only bounded process and transport protocol mechanics, ephemeral
invocation/session correlation, and bounded redaction/evidence shaping. They
must not own durable work selection, scheduling policy, semantic retry or repair
authority, acceptance, ES admission, runtime lifecycle truth, Git truth,
validation truth, or hidden program state. Bridge and Bridge Core are not
worker owners.

Model reasoning owns cognitive intent and architectural or semantic judgment.
Model sessions and model responses are not durable program truth by themselves.
The user steers major direction, priorities, and risk posture and is not a
routine synchronous per-attempt approval service. Connector availability and a
first-class Development Program are not prerequisites for the Worker Execution
Boundary. Full append-only event sourcing is not selected or required by this
tranche. CP WebAuthn and MA biometric/lease designs are not adopted as the
general operational authorization model.

## External Standing Authority And Target Subordinate Records

Classification: `CURRENT IMPLEMENTED CONTRACT`. Current executable
authorization is unsupported and fail-closed. Current coding `global_stop`
behavior is unchanged; global-stop and transition commands remain caller
inputs, and accepted or domain-rejected events persist only through the guarded
Coordinator `WriterSession` paths. Coordinator cannot self-authorize, and a
digest proves byte identity only, not permission.

Classification: `ACCEPTED STRATEGIC TARGET`. Authority authorship and durable
recording remain distinct:

- external standing-policy authority authors immutable standing grants, grant
  revocation or expiry, applicable global-stop directives, and effect, risk,
  cost, time, repository, path, and publication ceilings;
- Coordinator verifies and durably binds a safe standing-authority reference
  and its own progression facts; and
- Coordinator may derive narrower subordinate attempt/effect authorization
  records and issue attempt/effect fences only within that verified grant.

The external standing-policy authority does not write Coordinator SQLite
directly. Coordinator may never exceed, extend, renew, reinterpret, or outlive
the parent grant and may never convert its own durable record into independent
external authority. Subordinate authorization is target-only and is not
implemented by the current repository.

Every subordinate record or fence binds the parent standing-grant identity and
the exact program version, work item, semantic attempt, and effect. It remains
within scope, ceiling, expiry, revocation, and `global_stop`; fails closed when
the parent grant is absent, stale, expired, revoked, ambiguous, or insufficient;
does not make Coordinator a new grant issuer; and is not transferable to another
effect or attempt unless the parent grant expressly permits bounded reuse.

Classification: `FUTURE IMPLEMENTATION DETAIL`. The external issuer, verifier
deployment, encoding, signer, trust root, revocation transport, credential form,
and grant wire protocol remain open.

## Target Writer, Source, Custodian, And Projection Matrix

Classification: `ACCEPTED STRATEGIC TARGET`, except where a row is explicitly
current.

The matrix distinguishes semantic source or authority, durable recorder,
physical custodian, safe-reference holder, and projection. Storing a reference
does not collapse those roles.

| Fact or material | Semantic source or authority | Durable recorder | Physical custodian or safe-reference holder | Projection treatment |
| --- | --- | --- | --- | --- |
| External standing grant | External standing-policy authority | External authority system; Coordinator records only a verified safe binding | External authority system; Coordinator holds a safe reference | Reports may project bounded status only |
| External revocation, expiry, or applicable global-stop directive | External standing-policy authority | External authority system; Coordinator records its verified binding and resulting progression facts | External authority system; Coordinator holds a safe reference | Reports do not author or clear the directive |
| Program identity, revisions, work items, semantic attempts, progression decisions, effect intents, subordinate attempt/effect records, fences, cancellation intents, semantic acceptance, repair/replan decisions, and publication eligibility | Coordinator under the admitted domain and parent grant | Coordinator | Coordinator durable state, using only safe material | Reports are non-authoritative projections |
| Current transition and `global_stop` mutation | Current guarded Coordinator `WriterSession` contract | Guarded Coordinator `WriterSession` | Coordinator SQLite under current custody rules | Reports remain projections |
| Bootstrap worker invocation fact | Direct-local supervisor as source | Future Coordinator observation binding only | Supervisor owns process-local fact; Coordinator may hold a safe reference | Supervisor output is evidence, not acceptance |
| Later runtime admission, profile handoff, identity, lifecycle, cancellation request, and result fact | Execution Substrate | ES | ES; Coordinator may hold safe references | ES observations remain source-attributed |
| Candidate bytes and implementation activity | Worker invocation | Not Coordinator program truth | Mutable worker workspace until sealed | Worker completion is not acceptance |
| Canonical capsule manifest, blobs, and portable digest | Capsule builder acting at the worker boundary | Immutable capsule store for the sealed artifact; Coordinator records only a safe digest/reference | First-slice private immutable worker-side content-addressed store | A digest is not authority or acceptance |
| Validation result | Executing validator or CI source | Validator/CI source; Coordinator may bind an observation | Validator/CI evidence system | Success is not semantic acceptance |
| Model planning or review proposal | Model invocation as non-authoritative source evidence | Coordinator may bind only the safe proposal/decision relationship required by a future contract | Model/provider under its own custody contract | Model output is a proposal only |
| Git object and local ref | Git | Git object database and refs | Git | A commit is neither acceptance nor publication permission |
| PR or remote publication state | Git forge, when a future tranche permits it | Git forge | Git forge | Blocked in the first slice |
| Workspace teardown | Worker supervisor | Supervisor operational record, if a future contract requires one | Worker supervisor | Teardown does not decide acceptance |
| Public report | No semantic authority | No authoritative fact writer | Projection output only | Projection only |

The worker, supervisor, reviewer, model adapter, capsule store, and ES adapter
must not receive a `WriterSession`, writer proof, Coordinator database path, or
unrestricted Coordinator credentials. The first-slice capsule is private,
immutable, content-addressed, worker-side, outside the mutable worktree, and
outside Coordinator SQLite. A reviewer receives only read-only, attempt-bound,
capsule-bound retrieval authority. Later ES transport or retention is opaque and
does not make ES the semantic author or acceptance authority.

Classification: `DEFERRED OR BLOCKED EFFECT`. Push, PR creation, remote-ref
mutation, merge, deployment, and production autonomy are outside the first
slice. Classification: `PROCESS-ONLY GOVERNANCE`. Audit-fixture isolation rules
are recorded only in the C1 composition record and create no product authority.

## Evidence And References Versus Authority

For first-slice source observations, four additional roles are exact and do
not collapse:

- the **underlying fact owner** owns the external or source-native fact;
- the **canonical observation author** constructs and authors the closed
  `WorkerObservationV1` record;
- the **adapter/carrier** transports a command, delivery envelope,
  observation, or opaque result; and
- the **Coordinator recorder** records only the safe observation and its
  ingest disposition through a future guarded writer boundary.

### First-slice observation fact-owner and authorship matrix

| Observation family | Underlying fact owner | Canonical observation author | Permitted carrier |
| --- | --- | --- | --- |
| delivery acknowledged/rejected/unknown | direct-local delivery supervisor or ES submit/recovery owner | `direct_local_adapter` or `es_adapter` | the selected route only |
| worker started/completed and candidate captured | worker process | `worker` | direct-local or ES route |
| capsule sealed/seal failed | capsule builder | `capsule_builder` | direct-local or ES route |
| validation completed | validator/test runtime | `validator` | direct-local or ES route |
| independent review completed | independent reviewer | `independent_reviewer` | direct-local or ES route |
| cancellation acknowledged/rejected | direct-local supervisor or ES cancellation/lifecycle owner | `direct_local_adapter` or `es_adapter` | selected route |
| process exit/deadline | OS/supervisor for direct-local or ES lifecycle owner | `direct_local_adapter` or `es_adapter` | selected route |
| workspace teardown | workspace custodian | `workspace_custodian` | selected route |
| capsule retrieval | capsule store | `capsule_store` | selected route |

`source_kind` identifies the canonical observation-author kind. `source_ref`
is that author's stable safe record reference. The existing v1
`evidence_refs` field has the `safe_evidence_refs` role and may safely bind a
native fact of the underlying owner. Carrier identity is route metadata outside
the semantic observation identity. Recording or carrying a fact transfers
neither authorship nor authority. ES remains the fact owner for ES
admission/runtime/lifecycle facts even when `es_adapter` authors the canonical
Coordinator observation. A direct-local adapter does not become the OS-process
fact owner merely because it authors an observation, and Coordinator does not
become the fact owner merely because it records that observation.

Under the accepted C2A semantic contract and current C2A1 pure value layer,
schema validity, canonical digest validity, safe-reference possession,
capsule-digest possession, object equality, and successful pure relation
validation do not confer authority or acceptance. A future verifier must
establish the whole parent grant, subordinate authorization, fence,
expiry/revocation, repository/base/path, and current-global-stop relation. The
governing field contract is
`.docs/c2a-first-slice-semantic-protocol-contract.md`, while
`.docs/c2a1-pure-semantic-values.md` governs the internal no-I/O implementation;
neither alters the source, recorder, or custodian roles above or implements an
authority verifier.

Coordinator may retain safe opaque references and bounded observations needed
for correlation and decision-making. Retaining an ES `run_id`, adapter
invocation reference, Git ref, validation reference, or retained-result
reference does not transfer ownership of the external fact to Coordinator.
Persistence does not make evidence true. Raw credentials, keys, biometric
material, TLS/SPIFFE/Vault/WebAuthn/Codex/OpenAI/API-key material, private
environment files, unrestricted logs, support-bundle bodies, and private
paths/endpoints remain outside Coordinator durable/public state.

The current ES submit contract exposes an internally generated `run_id` after a
successful submit but does not expose caller-supplied submit idempotency or a
query-by-dispatch-command recovery contract. Reliable real dispatch requires an
ES-owned idempotency, correlation, or recovery decision, or an explicitly
bounded bootstrap exception. Coordinator must not compensate by inventing a
second ES lifecycle store, scraping Nomad as its own authority, or treating
trace/request IDs as recovery authority.

External I/O must not occur inside the SQLite mutation transaction boundary. A
recoverable durable effect intent must exist before an external dispatch effect
is attempted. Delivery acknowledgement is not runtime admission. An ES submit
receipt is not semantic work acceptance. Transport redelivery is not a new
semantic attempt; a new semantic attempt requires a Coordinator decision.

Writer-session authority is mutation fencing contract shape plus B2c internal
SQLite acquisition. B2a removes standalone reconstructable public-token
mutation authority: mutation authority belongs to an opaque backend-created
`WriterSession`, not to safe writer metadata or a durable SQLite row. B2c
acquires an internal session for a managed database. B3c4c makes public
`WriterSession.apply_transition(command)` delegate through the existing
operation guard to the B3c4b private atomic transition entry. The public wrapper
does not own SQL, transaction control, event or current-state writes, sequence
allocation, context assembly, evaluator invocation, capability construction, or
mutation-slot acquisition. B4c guarded public global-stop delegation exists:
public `apply_global_stop_update()` enters the same operation guard, performs
bounded function-local loading, maps the exact private global-stop preflight
vocabulary to the public vocabulary, and delegates once to B4b private atomic
global-stop persistence. B4a defines
receipt/read/event/replay/sequence/write contracts, and B4b implements private
atomic global-stop persistence without provisioning operator-decision receipts.
B4c adds no SQL, receipt verification, evaluator, sequence, write, rollback, or
commit ownership to `WriterSession`. Receipt provisioning remains a
separately governed operator/repo-policy integration seam, and no public,
orchestration, worker, service, connector, CLI, or cross-repository authority is
added. Stale
writer conflicts are private apply-boundary failures and never disclose
idempotency status or return transition events. Closed-session and
process-mismatch failures are session-local failures before the apply boundary;
they are not durable apply conflicts.

B3a changes the transition method shape to `apply_transition(command)` and
requires future transition context to be reconstructed inside the fenced store
boundary. It adds canonical event/replay contracts, including integrity-bound
lease-runtime status and evaluation time in `TransitionEvent`, and safe
mutation-store error classes only. It does not create admission, executable
authorization, SQLite transition mutation, global-stop mutation, service,
worker, repair, commit, publication, or related-repo authority.

Transition events are durable receipts for accepted or domain-rejected commands
only after B3c4b private atomic commit succeeds. Apply conflicts are not
receipts and do not provide acceptance,
authorization, publication, or product truth.

B1 SQLite bootstrap and migration operations are operator-local administrative
schema operations. They do not create work-item authority, global-stop update
authority, authorization receipts, executable permission, acceptance, commit,
publication, or product truth.

B2b's state-authority lock is live-process exclusion for initialize/migrate and
B2c writer acquisition. It is not writer authority by itself, not a credential,
not durable state, and not a substitute for private-proof writer fencing.

B2a/B2c writer-session contract objects do not create work-item authority,
global-stop update authority, executable authorization, acceptance, commit,
publication, product truth, or process liveness truth. Safe writer metadata is
diagnostics/evidence only and cannot reconstruct a private writer credential.

Coordinator P1 reports are closed typed public projections. They cannot widen
authority, cannot mutate state, and cannot carry raw private content,
endpoints, local paths, platform identifiers, credentials, trust material, or
execution claims.

## C2B0 Target Authority, Source, And Custody Closure

Status: `ACCEPTED TARGET CONTRACT`; no runtime authority is added.

Coordinator may later author and durably record its own program progression,
effect-intent, ingest-disposition, decision, eligibility, and immutable acceptance facts
through the existing writer authority. The external source still authors each
source invocation and observation. A Coordinator ingest disposition is not a
source observation, and neither is a Coordinator progression decision.
Decision, effect intent, delivery, acknowledgement, runtime termination, and
semantic abandonment remain distinct facts.

The accepted-intent/work-specification authority semantically authors private
WorkSpec material. Coordinator SQLite may retain only safe bindings and is a
safe-reference holder, not the physical custodian. The custodian and
attempt-bound retrieval authorization remain deferred; a safe ref or digest is
not retrieval authority. Chat, model sessions, reports, connectors, and Bridge
ledgers cannot become hidden custody.

An external authority system remains the author of executable standing
authority. C2B records at most safe bindings and a future verifier-authored
status. No verifier exists. Persistence, a digest, a relation, a Coordinator
decision, or a caller Boolean never becomes executable authorization.

<!-- C2B3_NARROWED_AUTHORITY_BEGIN -->
## Vertical-slice governing authority boundary

The narrowed vertical-slice target does not change authority ownership.
Coordinator owns durable progression, never the parent standing grant and
never authors `verified`. An external authority source owns the parent grant;
an external verifier supplies current verification immediately before the
future effect. Persisted evidence is not automatically fresh permission, and
the user is not a routine per-effect approver.

The worker has no Coordinator SQLite or writer access. Git owns object and ref
truth. Validators and reviewers own their evidence. Reports, model output,
Bridge records, topology/profile observations, and transport receipts remain
evidence only. Raw WorkSpec and retrieval bearer authority never enter
Coordinator SQLite; a safe ref or digest is identity evidence, not retrieval
authority.

The first bounded direct/non-ES delivery may yield at most one productive
acceptance. A separate local-Git effect may later yield at most one isolated
feature-branch commit, with zero publication effects and no blind retry after
an ambiguous outcome. Exact durable authority/evidence representations remain
required just-in-time questions rather than selected schemas.
<!-- C2B3_NARROWED_AUTHORITY_END -->

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
implemented separately under the D1 owner. RW0-D2 evidence/review/model
closure, RW0-C2 physical decision persistence, live provider/credential/custody,
and RW0-E runtime mechanics remain future.
Execution Substrate retains admission and runtime authority.
<!-- RW0_B2_CAPABILITY_CURRENT_STATUS_END -->

<!-- COORDINATOR_RW0_PHASE_ENTRY_CROSS_REFERENCE_END -->
