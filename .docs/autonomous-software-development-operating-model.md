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
VS1B route-neutral program-initialization caller, and the later Section 41
runtime composes with a bounded seven-role subset without widening that query
contract. C2B2 did not implement or acquire ownership of migration 0003 or
Section 41; reader reports and projections remain neither durable program truth nor
effect authority. C2B3 implements the receipt-first route-neutral genesis and
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
generation 2 and now applies the complete three-entry catalog
`[0001, 0002, 0003]`, whose current packaged tip is migration 0003. Migration
0002 remains the unchanged historical prefix introduced by C2B2 Slice 1, and
migration 0001 retains its preserved identity.

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
the current generation-2 migration-0003 physical tip, and
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
tip is `0003_cognitive_proposal_and_selection_state`, with three production SQL
resources.
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
remains generation 2 and now terminates at migration 0003. It comprises C2A1,
C2B2 private values/readers, existing bounded writer/transaction authority, the
private VS1B genesis family, the private C2B3D author-effect family, and the
private non-executable pre-execution proposal-selection family. All worker,
dispatch, Git, Bridge, ES, and other external execution remains absent.
<!-- C2B3_NARROWED_OPERATING_MODEL_END -->

<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_BEGIN -->
## Cognitive proposal and selection runtime

Section 41 of `.docs/c2b-durable-development-state.md` is the sole detailed semantic owner
for this bounded contract; Section 42 records implementation status without redefining it.
C2B3D remains current and unchanged. Migration 0003 and the private pre-execution
proposal-selection runtime are now implemented in the uncommitted candidate pending
fresh independent audit. The source tranche ends at typed pre-execution proposal
admission plus Coordinator selection or non-selection; it performs no model invocation
or dispatch. Model invocation, dispatch, worker contact, post-execution review,
post-execution semantic decision, Git, and publication remain blocked. The full
remote-worker phase is not reduced to this private source tranche.
<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_END -->
