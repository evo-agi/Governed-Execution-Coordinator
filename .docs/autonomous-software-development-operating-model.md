# C1 Autonomous Software-Development Operating Model

C2A composes below this unchanged thirteen-clause C1 inventory. The accepted
field and semantic authority is
`.docs/c2a-first-slice-semantic-protocol-contract.md`; it makes `program_ref`
and `program_version_ref` mandatory distinct identities for every productive
first-slice semantic record. C2A1 implements only the internal no-I/O values and
six named pure coherence validators governed by
`.docs/c2a1-pure-semantic-values.md`; this does not change C1 topology, add
durable state, or authorize any effect, and preserves the one-local-commit
maximum.

## C1-AOM-001 — Status And Classification Ledger

This document is the authoritative composition record for the accepted C1
software-development operating model. It composes, without replacing, the
specialized contracts in:

- `.docs/authority-boundaries.md` for authority and one-writer detail;
- `.docs/software-development-progression-boundary.md` for
  attempt/effect/review/acceptance/repair/publication semantics;
- `.docs/worker-execution-boundary.md` for process, transport, credential,
  fence, and capsule boundary detail;
- `.docs/durable-state-model.md` for current SQLite implementation reality.
- `.docs/c2a1-pure-semantic-values.md` for the current internal no-I/O value and
  pure coherence layer.

The status classifications used by C1 are:

- `CURRENT IMPLEMENTED CONTRACT` — behavior implemented in the current
  Coordinator repository;
- `CURRENT COMPATIBILITY EDGE` — behavior retained for present compatibility
  without making it enduring target truth;
- `ACCEPTED STRATEGIC TARGET` — an accepted architecture decision that remains
  unimplemented until a separately authorized source tranche;
- `FUTURE IMPLEMENTATION DETAIL` — a decision intentionally left to a later
  implementation contract;
- `DEFERRED OR BLOCKED EFFECT` — behavior that is not permitted by this tranche
  or remains gated on another owner contract; and
- `PROCESS-ONLY GOVERNANCE` — repository-work or audit discipline that is not
  product runtime architecture or durable state.

Classification: `CURRENT IMPLEMENTED CONTRACT`. Coordinator currently provides
bounded durable SQLite mutation authority for the existing coding-work
transition and `global_stop` contracts, plus a separate internal C2A1 pure
semantic-value and coherence layer and private pure C2B2 row/value source for
all nineteen migration-0002 tables. The C2B2 reader layer remains exactly
twelve private roles and twenty-four bounded query contracts with no public API
or reader-created durable authority. All twelve roles have the bounded private
C2B3D author-effect caller, the mutation-receipt role also retains the private
VS1B route-neutral program-initialization caller, and the later Section 41 and
RW0-C1 runtimes compose with a bounded seven-role subset without widening that
query contract. C2B2 did not implement or acquire ownership of migrations
0003/0004, Section 41, or RW0-C1; reader reports and projections remain neither
durable program truth nor effect authority. C2B3 implements the receipt-first route-neutral genesis and
author-effect families with readback-only uncertainty resolution, and Section
41 implements private pre-execution proposal selection. Coordinator still has
no bound-effect or post-execution progression-decision runtime, dispatcher,
scheduler, queue consumer,
worker, worker supervisor, subprocess launcher, model/provider client, ES
client, capsule builder or store, observation-ingest loop, validation executor,
review executor, repair executor, Git effect handler, publisher,
service/API/IPC surface, autonomous loop, or subordinate-authorization runtime.

Classification: `CURRENT COMPATIBILITY EDGE`. `FiniteBacklog`, current standing
lease, zero-only budget, READY-only dependency, disabled-stage, coding
`global_stop`, current `WriterSession`, schema-0001 compatibility meanings, and
`control-plane-normal-shell/v1` compatibility remain unchanged within their
owning contracts. The physical Coordinator schema remains at application
generation 2 and now applies the complete four-entry catalog
`[0001, 0002, 0003, 0004]`, whose current packaged tip is migration 0004.
Migrations 0002 and 0003 remain unchanged historical prefixes, and migration
0001 retains its preserved identity.

Classification: `ACCEPTED STRATEGIC TARGET`. This record is authoritative for
the selected staged model, first exact scenario, first effect ceiling, ten
direct-local stop conditions, parallel ES lanes, ES-migration gate, first-slice
dependency exclusions, and process-only audit-isolation governance.

Classification: `FUTURE IMPLEMENTATION DETAIL`. Exact source APIs, protocols,
storage technologies, credentials, process mechanics, and wire formats remain
open as stated in C1-AOM-013.

Classification: `DEFERRED OR BLOCKED EFFECT`. This tranche authorizes no
autonomous execution, worker invocation, Git mutation, publication, ES
integration, or operational progression.

Classification: `PROCESS-ONLY GOVERNANCE`. C1-AOM-012 governs future synthetic
audit fixtures only and is not a product contract.

## C1-AOM-002 — Accepted Staged Topology

Classification: `ACCEPTED STRATEGIC TARGET`.

The first-stage topology is ordered as follows:

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

The later ES-routed topology preserves the same semantic and transport-neutral
contracts:

```text
same Coordinator progression semantics
same worker command/observation/fence/capsule contracts
same worker artifact
    -> ES reliable-submit adapter
    -> ES admission and runtime lifecycle
    -> process-separated coding worker
    -> opaque capsule result transport or retention
```

Direct-local is a bounded bootstrap/proof route, not the target production
execution path. Neither route is implemented by this tranche. The
transport-neutral boundary does not transfer Coordinator durable progression,
ES admission/runtime authority, Git truth, validation truth, or semantic
acceptance to an adapter or worker.

## C1-AOM-003 — Worker Source, Release, Process, And Credential Boundary

Classification: `ACCEPTED STRATEGIC TARGET`.

Initial worker source and release machinery live in the Coordinator repository,
and the worker executes as a separate OS process. The authoritative Coordinator
process must not execute implementation work in-process. The worker has no
direct Coordinator SQLite mutation authority.

The worker, supervisor, reviewer, model adapter, and capsule store must not
receive a `WriterSession`, writer proof, Coordinator database path, or
unrestricted Coordinator credentials. They may receive only the least authority
required for their exact attempt-bound, effect-bound role under the governing
standing grant and fences.

No seventh repository is created now. Worker extraction into a separate
repository requires demonstrated independent release cadence, independent
ownership, multiple consumers, or materially separate dependency or security
governance.

Classification: `FUTURE IMPLEMENTATION DETAIL`. Exact package names,
executable names, IPC, supervisor mechanics, build system, credential delivery,
and deployment remain open. Bridge and Bridge Core are not worker
implementation owners.

## C1-AOM-004 — First Autonomous Slice And Effect Ceiling

Classification: `ACCEPTED STRATEGIC TARGET`.

The first autonomous vertical slice preserves this ordering:

```text
worker completion
    -> candidate capture
    -> validation observation
    -> independent review observation or proposal
    -> model review proposal
    -> Coordinator semantic decision
    -> at most one separately selected local feature-branch Git commit effect
```

The maximum effect is one local feature-branch Git commit after Coordinator
semantic acceptance and a separate effect decision. Worker authoring must not
silently create that commit.

Classification: `DEFERRED OR BLOCKED EFFECT`. Push, remote-ref mutation, PR
creation, merge, deployment, and any production-autonomy claim are excluded.
The effect ceiling is not permission; every effect remains subject to standing
authority, subordinate fences, current `global_stop`, validation, and the
applicable attempt decision.

## C1-AOM-005 — Candidate Capsule And Custody

Classification: `ACCEPTED STRATEGIC TARGET`.

The first-slice carrier is private, immutable, content-addressed, worker-side,
outside the mutable worktree, and outside Coordinator SQLite. Roles remain
separate:

- the worker invocation is the source of candidate bytes and implementation
  activity;
- a capsule builder acting at the worker boundary seals the canonical manifest,
  blobs, and portable digest;
- a private immutable worker-side content-addressed store has first-slice
  physical custody;
- Coordinator holds only a safe digest/reference and progression decisions;
- a reviewer receives read-only, attempt-bound, capsule-bound retrieval
  authority;
- ES may later transport or retain the exported capsule opaquely; and
- Git becomes object and ref truth only after a separately selected commit
  effect.

A capsule digest is not a local path, endpoint, bearer retrieval credential,
authorization proof, acceptance decision, or Git identity. Mutable workspace
state and the sealed capsule are distinct. A code-changing repair normally
creates a new semantic attempt, new candidate identity, new portable capsule
digest, and new candidate-bound validation and review.

The portable capsule excludes raw prompts, model transcripts, Codex JSONL,
unrestricted logs, unrestricted command output, credentials, private endpoints,
trust material, and unrelated workspace content.

Classification: `FUTURE IMPLEMENTATION DETAIL`. Exact path, storage
implementation, encryption, garbage collection, retention duration,
serialization, and wire encoding remain open.

## C1-AOM-006 — Standing Authority, Subordinate Authorization, Model, And User Role

Classification: `CURRENT IMPLEMENTED CONTRACT`. Current executable
authorization remains unsupported and fail-closed. Current coding
`global_stop`, caller-supplied transition and global-stop commands, and guarded
`WriterSession` persistence remain unchanged. Coordinator cannot self-authorize,
and a digest proves identity only, not permission.

Classification: `ACCEPTED STRATEGIC TARGET`. External standing-policy authority
authors immutable standing grants, grant revocation or expiry, applicable
global-stop directives, and effect, risk, cost, time, repository, path, and
publication ceilings. It does not write Coordinator SQLite directly.

Coordinator may verify and durably bind a safe standing-authority reference and
its own progression facts. Within that verified parent grant, it may derive
narrower subordinate attempt/effect authorization records and issue
attempt/effect fences. A subordinate record or fence:

- binds the parent standing-grant identity;
- binds the exact program version, work item, semantic attempt, and effect;
- remains within scope, ceiling, expiry, revocation, and global stop;
- fails closed when the parent grant is absent, stale, expired, revoked,
  ambiguous, or insufficient;
- is not a new grant issuer; and
- is not transferable to another effect or attempt unless the external grant
  expressly permits bounded reuse.

Coordinator may never exceed, extend, renew, reinterpret, or outlive the
external grant, and it may never convert its own durable record into independent
external authority. This subordinate-authorization behavior is not currently
implemented.

Model reasoning creates cognitive planning, implementation, and review
proposals. A model invocation is non-authoritative source evidence; a model
session or response is not a durable decision or effect authority. The user
steers major direction, priorities, and risk posture and is not a routine
synchronous per-attempt approver.

Detailed authority and writer/source/custodian treatment is authoritative in
`.docs/authority-boundaries.md`.

## C1-AOM-007 — Review, Acceptance, Repair, And Publication Separation

Classification: `ACCEPTED STRATEGIC TARGET`.

The operating model keeps each of these distinct:

1. worker completion;
2. candidate capture;
3. validation observation;
4. independent review observation or proposal;
5. model review proposal;
6. Coordinator semantic acceptance;
7. Coordinator repair decision;
8. Coordinator replan decision;
9. local Git commit;
10. PR creation;
11. merge; and
12. deployment.

Neither worker exit, validator success, reviewer output, model response, ES
result, Bridge report, Git commit, nor CI result directly creates semantic
acceptance. Coordinator is the target semantic decision source for acceptance,
repair, replan, rejection, or block, but external fact sources retain their own
facts.

A code-changing repair normally creates a new semantic attempt, candidate
identity, portable capsule digest, and candidate-bound validation and review.
The first-slice local commit is a separate effect after acceptance. PR creation,
merge, and deployment remain separately governed publication effects and are
blocked in the first slice.

## C1-AOM-008 — Direct-Local Bootstrap/Proof Contract

Classification: `ACCEPTED STRATEGIC TARGET` with `DEFERRED OR BLOCKED EFFECT`
limits.

1. The direct-local route implements the same versioned worker command,
   observation, fence, and capsule contracts intended for ES routing.
2. It is named explicitly as bootstrap/proof.
3. It initially permits one repository and one active invocation.
4. It has no connector or Bridge trigger.
5. It cannot push, create a PR, merge, or deploy.
6. It cannot write Coordinator SQLite directly.
7. It cannot create semantic attempts, accept candidates, or decide repairs.
8. Expansion stops after one accepted vertical slice pending an ES-migration
   review.
9. The later ES adapter must pass the same conformance contract.
10. After ES routing is accepted, direct-local becomes disabled by default and
    survives only under a distinct proof/recovery policy.

The one-repository and one-active-invocation bounds are effect ceilings for the
bootstrap route. They do not make the adapter, supervisor, or worker a hidden
scheduler, lifecycle authority, work-selection authority, or durable program
truth.

## C1-AOM-009 — First Recorded ES Scenario

Classification: `ACCEPTED STRATEGIC TARGET`, not an executed scenario.

The first recorded worker scenario is eventually allowed to change exactly:

```text
Execution Substrate/PLANS.md
Execution Substrate/.docs/system_overview/hybrid_integration_architecture_adr.md
Execution Substrate/docs_contract_test.go
```

Its purpose is to classify direct-local worker execution as a bounded
bootstrap/proof edge, record mandatory migration stop conditions, preserve ES
reliable-submit dependencies, preserve the current ES P0, and create no ES
runtime change. Its maximum effect is one local feature-branch Git commit; push,
remote-ref mutation, PR creation, merge, deployment, and a production-autonomy
claim are excluded.

Classification: `DEFERRED OR BLOCKED EFFECT`. The scenario may occur only after
the Coordinator C1 contract reset is accepted, the Bridge documentation/test
reset is accepted, a separately authorized direct-local bootstrap
implementation is accepted, and first-slice standing-policy and validation
contracts exist. This tranche does not execute it and does not modify ES.

## C1-AOM-010 — Parallel ES Lanes And Migration Gate

Classification: `CURRENT COMPATIBILITY EDGE` and `ACCEPTED STRATEGIC TARGET`.

The owner-governed lanes may progress in parallel:

```text
Lane 1:
  current ES P0 Remote Alpha operator-helper consolidation

Lane 2:
  Coordinator C1 contract reset and bounded autonomy bootstrap

Lane 3:
  ES reliable-submit, correlation, and reconciliation under ES planning authority
```

Coordinator documentation does not reprioritize ES. Migration from direct-local
to ES is blocked until accepted ES contracts cover at least:

1. resolved execution-plan extraction;
2. reliable keyed submit;
3. caller correlation and response-loss recovery;
4. ES-owned ambiguous-submit reconciliation;
5. runtime admission and lifecycle observation;
6. cancellation correlation;
7. opaque capsule result transport or retention; and
8. Coordinator-to-ES adapter conformance.

`resolved-execution-plan-extraction-foundation` remains the next source-bearing
reliable-submit seam under ES planning authority. C1 does not import, revive, or
adopt the rejected archived implementation.

## C1-AOM-011 — Compatibility, Deferred Components, And Cross-Repository Drift

Classification: `CURRENT COMPATIBILITY EDGE`.

C1 preserves `FiniteBacklog`, current standing-lease behavior, current zero-only
budget behavior, current READY-only dependency behavior, current disabled-stage
behavior, current coding `global_stop`, current `WriterSession` authority, the
schema-0001 compatibility meanings and unchanged `0001_initial.sql` identity,
the current generation-2 migration-0004 physical tip, and
`control-plane-normal-shell/v1` as an ES/CP compatibility edge. Coding and
operational progression remain separately versioned domains; operational
progression is excluded from the first software-development slice.

Classification: `DEFERRED OR BLOCKED EFFECT`. First-slice runtime dependencies
explicitly exclude:

- Governed Execution OpenAI Bridge;
- Governed Execution Bridge Core;
- Control Plane;
- Infrastructure Manager;
- Governed Execution Maintenance Agent;
- Host Lens; and
- Symphony.

Bridge remains a guarded adapter/evidence surface, not the worker owner or a
direct-local trigger. Bridge's stale CP-enduring-target and
Bridge-worker-placement records require a later Bridge-only documentation and
contract-test tranche. Bridge Core adoption is deferred. CP, IM, and MA
migration, survival, or retirement outcomes remain outside C1.

The ES hybrid integration ADR remains current cross-repository status and
migration authority. It is not the complete Coordinator target operating model
and does not transfer Coordinator architecture ownership to ES.

## C1-AOM-012 — Audit-Isolation Process Governance

Classification: `PROCESS-ONLY GOVERNANCE`.

This clause is `NOT PRODUCT RUNTIME ARCHITECTURE`, `NOT COORDINATOR DURABLE
STATE`, and `NOT WORKER BEHAVIOR`.

Any future mutation-capable synthetic Git fixture must:

1. clear ambient Git variables;
2. initialize an explicit audit-owned `.git`;
3. verify the physical Git top-level is beneath the audit root;
4. never use a copied pathname as isolation proof; and
5. recheck the real repository HEAD, index, local configuration, and status
   after each mutation-capable probe group.

This tranche implements no fixture or helper.

## C1-AOM-013 — Future Details And Non-Implementation Contract

Classification: `FUTURE IMPLEMENTATION DETAIL`.

C1 leaves open exact IPC and supervisor mechanics; package, module, executable,
and build-system names; process framing, transport wrapping, and ES wire mapping
for the C2A-frozen command/observation/fence/capsule semantic fields;
capsule path, store technology, encryption, garbage collection, retention,
serialization, archival, and recovery; external issuer and verifier deployment,
signer, trust root, revocation transport, credential form, and grant encoding;
Git commands, branch naming, commit-message format, credentials, and publisher;
model provider, protocol, prompt transport, and deployment; Coordinator program
schema, migrations, outbox/inbox, service/API/IPC, scheduler, and reconciler;
later ES request/response/correlation/recovery/cancellation/result and runtime
profile mechanics; direct-local proof/recovery policy representation; stop
precedence and final program-completion semantics; operational-change topology;
CP/IM/MA migration or retirement; and Bridge Core adoption.

Classification: `DEFERRED OR BLOCKED EFFECT`.

C2A1 adds only one internal pure no-I/O production source module for immutable
semantic values and six named coherence validators. It adds no schema,
migration, dependency, package export, entry point, script, worker, subprocess
call, network client, filesystem capsule implementation, model/provider
implementation, ES client, Bridge integration, Git mutation implementation,
runtime subordinate-authority implementation, runtime enablement flag,
software-development runtime, semantic-attempt runtime, observation ingest,
validation/review/repair executor, publisher, service/API/IPC, or autonomous
loop.

The direct-local bootstrap, worker, capsule custody implementation, first
scenario, local commit effect, ES migration, and every publication effect each
require a separately accepted implementation or owner-repository tranche.

## C2B0 Accepted Durable-State Composition Overlay

Classification: `ACCEPTED TARGET CONTRACT`.

C2B0 closes only the target durable-state seams governed in
`.docs/c2b-durable-development-state.md`; the historical C1 ledger above
remains unchanged. Target program genesis uses an immutable `initialize`
decision. The exact decision domain also includes the distinct risk-reducing
`cancel` decision. Author-effect establishment is separate from bound
validation, review, and cancellation-effect establishment, and none performs
external I/O.

For the C2B target, active coding global stop blocks initialization,
author/validation/review effects, productive delivery or redelivery,
acceptance, repair, productive replan, publication eligibility, latch
consumption, and Git eligibility. It permits source evidence retention,
terminal reject/block decisions, a cancel decision, cancellation-effect
planning and cancellation delivery, and cancellation evidence ingest. This is
a C2B target selection, not a retroactive C1 invariant.

C2B5 owns source-observation ingest, cancel/redeliver decisions, and bound
validation/review/cancellation effects. C2B6 owns remaining program
progression, publication eligibility, and the first-slice latch. C2B0
implements neither tranche and adds no schema, migration, runtime, worker,
Bridge change, or ES change.

## C2B1/C2B2 Current Administrative, Pure-Value, And Private-Reader Composition

Classification: `CURRENT IMPLEMENTED CONTRACT` for migration administration,
private pure no-I/O row/value validation, private reader behavior, and the
bounded private C2B3 route-neutral genesis and author-effect families plus the
Section 41 pre-execution proposal-selection family. C2B0
remains the historical contract-freeze tranche for the target composition
above.

C2B1 implements exact-current ordinary SQLite open, explicit supported-prefix
migration, terminal-only application-generation compatibility, cumulative
packaged-SQL schema authority, complete-catalog initialization, complete-suffix
single-transaction migration, and three-way migration commit readback while
retaining the common state-authority lock and filesystem binding. C2B2 Slice 1
introduced application generation 2 and catalog entry
`0002_development_program_and_effect_state`. The current generation-2 catalog
tip is `0004_rw0_c1_durable_evidence`, with four production SQL resources;
migrations 0003 and 0004 retain their separate Section 41 and RW0-C1 owners.
Slice 1 adds physical schema representability only. This administrative
evidence is not program, progression, decision, effect, acceptance,
publication, or runtime truth.

C2B2 Slice 2 implements four private pure row/value modules: exact ordered
tuple boundaries for the nineteen tables, immutable validated values, eighteen
row self-digest checks, five receipt result projections, bounded C2A
reconstruction, WorkSpec safe projection, and the common supplied-entry graph
digest primitive. It adds no SQL, reader capability, database reader, or
independent product writer. By itself it adds no migration, observation ingest,
semantic decision, authority verification, WorkSpec custody, worker/process
execution, capsule
storage, Git effect, direct-local route, ES route, service, scheduler, queue,
publication, or autonomous loop. C2B2 Slice 3 separately implements exactly
twelve private reader roles and twenty-four literal SELECT specifications
through the existing nominal capability seam. All twelve roles have the
bounded private C2B3D author-effect caller; the mutation-receipt role also
retains the VS1B caller. This adds no public API or external effect. C2B3 now
implements route-neutral program genesis and private author-effect
establishment, with exact replay and readback-only uncertainty recovery for
both families. Section 41 separately implements private non-executable
pre-execution selection with receipt-first replay and fresh-writer read-only
recovery. Bound effect, observation ingest, post-execution progression
decisions, and remaining C2B4-C2B6 behavior remain target-only.

<!-- C2B3_NARROWED_OPERATING_MODEL_BEGIN -->
## Narrowed first vertical-slice operating order

The horizontal C2B3-C2B6 sequence is no longer operative implementation order.
The only frozen dependency order is:

1. pre-I/O Coordinator progression;
2. remote worker contact through semantic decision;
3. a separate local-Git effect and stop;
4. migration to ES before another productive bootstrap slice.

This is not a mandatory program or tranche count. Future prompts may divide or
combine internal checkpoints while preserving authority, validation, and
provenance boundaries.

Each phase must resolve only the questions it needs. VS1B resolved the pre-I/O
route-neutral initialization, minimum durable graph, migration-0002 sufficiency,
and replay/recovery questions without external I/O. C2B3D now resolves only the
private author-effect command, ten-row/nine-entry durable family, replay,
recovery, and bounded current-head questions. Its planned delivery remains
inert. Remote contact owns minimum custody/retrieval, fresh verifier,
invocation, capsule, evidence, and executable-path migration questions. Local
Git owns command/delivery/observation,
reconciliation, authority, outcome evidence, and no-blind-retry questions. ES
migration owns reliable keyed submit, response-loss and Nomad ambiguity,
retained results/capsules, conformance, and bootstrap disablement.

These are required questions, not selected future schemas. Current capability
remains generation 2 and now terminates at migration 0004. It comprises C2A1,
C2B2 private values/readers, existing bounded writer/transaction authority, the
private VS1B genesis family, the private C2B3D author-effect family, the private
non-executable pre-execution proposal-selection family, and RW0-C1 private
immutable phase/evidence persistence. All worker, dispatch, Git, Bridge, ES,
and other external execution remains absent.
<!-- C2B3_NARROWED_OPERATING_MODEL_END -->

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
Non-cancel terminal outcomes bind one earlier same-kind C2B decision. The accepted direct-local C2B decision alone atomically consumes the one-way latch in its guarded writer transaction; the later terminal-outcome `accept` binds that exact decision ref/digest and committed latch postimage without another latch mutation.
After exact cancel-decision commit readback and current-head, stop-version, and authority verification, an unusable pre-effect cancel basis establishes no effect, fence, delivery, request, or signal and commits terminal-outcome `block` bound to the exact unusable decision and mismatch evidence, without another C2B decision.
A current compatible cancel basis follows distinct request, acknowledgement, signal, exit, teardown, and source reconciliation facts, yielding terminal-outcome `cancel` only when complete and unambiguous or terminal-outcome `block` otherwise without another C2B decision.
No current custody, adapter, supervisor, worker, capsule, validation, review, model, post-execution decision, terminal-outcome, latch, Git, or publication runtime exists.
Direct-local route-local process and cancellation ownership does not absorb ES-route authority; no successor, Git, or publication effect follows RW0.
Exact custodian, physical transport framing, stream/process plumbing, Codex seam, schema, terminal-outcome representation, latch, and physical backends remain deferred.
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
mutation authority; RW0-C2 closure/decision and RW0-D/E transport, process,
provider, credential, live-proof, and runtime mechanics remain future.
Execution Substrate retains admission and runtime authority.
<!-- RW0_B2_CAPABILITY_CURRENT_STATUS_END -->
<!-- COORDINATOR_RW0_PHASE_ENTRY_CROSS_REFERENCE_END -->
