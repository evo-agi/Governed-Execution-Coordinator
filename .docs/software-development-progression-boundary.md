# Software-Development Progression Boundary

This document records the C0 software-development progression boundary for the
Coordinator repository. It is a documentation and contract-test tranche for the
accepted strategic target only. Current owning-repository contracts remain
present reality where they describe implemented behavior.

C1 supplements rather than replaces this exact C0-SD-001 through C0-SD-015
inventory. The authoritative staged operating-model composition is
`.docs/autonomous-software-development-operating-model.md`. Across C0 and C1,
statements distinguish `CURRENT IMPLEMENTED CONTRACT`, `CURRENT COMPATIBILITY
EDGE`, `ACCEPTED STRATEGIC TARGET`, `FUTURE IMPLEMENTATION DETAIL`, `DEFERRED OR
BLOCKED EFFECT`, and `PROCESS-ONLY GOVERNANCE`.

## Status And Current Reality

### C0-SD-001 - Tranche Boundary

Classification: CURRENT CONTRACT / INVARIANT for C0.

C0 changes documentation and contract tests only. It MUST NOT add or change
source behavior, schema or migration, dependencies, package exports, entry
points, services, APIs, IPC, queues, workers, schedulers, adapters, ES or Bridge
integration, Codex or model invocation, Git or CI integration, publication
behavior, executable-authority issuance, or autonomous progression.

C0 does not report a durable development-program model, worker, dispatcher,
observation ingest, publication path, repair executor, or autonomous loop as
implemented.

### C0-SD-002 - Target Status

Classification: STRATEGIC TARGET with CURRENT CONTRACT / INVARIANT limits.

The strategic target is a program-native software-development progression
domain owned durably by Coordinator. This is target-only. Current Coordinator
remains the bounded durable coding-work SQLite authority described by current
contracts, including internal writer issuance, fenced transition and
`global_stop` mutation, idempotency, CAS, exact replay, commit uncertainty, and
explicit retry semantics.

Reports, traces, generated artifacts, model sessions, model responses, and chat
remain non-authoritative. C0 references already-frozen owner-neutral
progression rules instead of restating them as a second generic kernel.

## Relationship To Owner-Neutral And Adjacent Boundaries

The adjacent documents
[.docs/worker-execution-boundary.md](worker-execution-boundary.md) and
[.docs/operational-progression-boundary.md](operational-progression-boundary.md)
remain governing context for already-frozen owner-neutral mechanics such as
durable intent before external I/O, source-attributed observations, explicit
unknown or ambiguous outcomes, and transport-neutral worker contracts. C1
closes the coding-specific staged source/process placement while operational
progression remains separate and unchanged.

C0 MUST NOT create or imply one universal queue, backlog, lease,
work-item/state grammar, state machine, retry or repair counter, dependency
receipt model, global stop, acceptance grammar, effect vocabulary, schema,
service, module, worker, scheduler, or reconciler. Software-development target
semantics are separately versioned from bounded operational-change semantics.

## Software-Development Scope And FiniteBacklog Compatibility

### C0-SD-003 - Identity Non-Collapse

Classification: STRATEGIC TARGET.

The target semantics MUST keep these concepts distinct, even when a later design
correlates them:

- development program;
- `program_version` or equivalent expected revision;
- accepted-intent revision;
- objective revision;
- work-graph revision;
- work unit and work-unit revision;
- future execution-batch identity, if used;
- semantic attempt;
- progression decision;
- effect intent;
- delivery or dispatch attempt;
- external invocation or source reference;
- source observation;
- semantic acceptance or another semantic decision;
- publication eligibility;
- publication intent;
- publication effect;
- publication observation.

`program_version` is a Coordinator concurrency coordinate. It MUST NOT collapse
into accepted-intent revision, objective revision, work-graph revision, Git
revision, ES lifecycle revision, or source-observation revision. Objective
revision is semantically distinct from accepted-intent revision, but C0 does not
require a separate storage aggregate, API, or table.

### C0-SD-004 - Current FiniteBacklog Compatibility

Classification: COMPATIBILITY EDGE and BOUNDED IMPLEMENTED PROOF.

`FiniteBacklog` v1 remains unchanged as the current immutable, closed-world,
digest-bound coding-work compatibility contract. It is not target program
truth, accepted-intent truth, objective truth, work-graph truth,
semantic-attempt truth, effect truth, semantic-acceptance truth, publication
truth, or the enduring target execution-batch model.

C0 leaves open whether a later versioned compatibility layer maps
`FiniteBacklog` v1 to a future execution-batch concept, adapts it into
program-native work, replaces it with a versioned successor, or retires it
through an explicit migration.

## Identity, Revision, Supersession, And Proposal Containment

### C0-SD-005 - Immutable Revision History And Explicit Supersession

Classification: STRATEGIC TARGET.

Accepted-intent, objective, work-graph, and work-unit revisions MUST append
immutably rather than rewrite prior durable truth. A Coordinator progression
decision MUST explicitly identify what is selected, preserved, amended,
superseded, split, merged, abandoned, or cancelled.

Supersession MAY be partial. Split and merge operations preserve explicit
lineage. Previously accepted results MAY remain usable when an explicit
progression decision preserves their semantic relevance. C0 does not select a
graph schema, dependency grammar, or persistence layout.

### C0-SD-006 - Stale Proposal Containment

Classification: STRATEGIC TARGET.

A model proposal or ingress command capable of changing durable progression MUST
bind the Coordinator `program_version` or equivalent expected revision on which
it was based. A stale proposal remains evidence only. It cannot mutate current
progression without explicit re-evaluation, rejection, rebasing, or another new
Coordinator decision.

Model sessions and model responses are not durable program truth.

## Attempts, Effects, Delivery, And Invocation

### C0-SD-007 - Attempt, Effect, Delivery, And Invocation Separation

Classification: STRATEGIC TARGET.

For productive work, the target semantics distinguish:

```text
productive semantic attempt
  -> one or more durable implementation, validation, or review effect intents
      -> zero or more delivery or dispatch attempts
          -> zero or more source-owned invocation or run references
```

A new semantic attempt requires an explicit Coordinator progression decision.
Re-delivering or reconciling one durable effect does not itself create a new
semantic attempt. A repair is normally a new semantic attempt.

Cancellation and publication may reuse generic effect/delivery mechanics, but
they are not automatically children of the productive semantic attempt:

```text
cancellation progression decision
  -> cancellation effect intent
      -> delivery attempts
          -> cancellation receipt and later source observation

publication progression decision
  -> publication effect intent
      -> delivery attempts
          -> Git or owner-source publication observations
```

C0 does not select worker commands, transport DTOs, retry budgets, or dispatch
protocols.

## Observations, Ambiguity, And Reconciliation

### C0-SD-008 - Ambiguity And Safe Reconciliation

Classification: STRATEGIC TARGET.

A lost acknowledgement preserves the original durable effect intent and creates
an ambiguous external outcome. Reconciliation, query, waiting, containment, or a
later delivery attempt remains associated with that same effect intent.

A later delivery attempt is allowed only when the owning action or transport
contract establishes that re-delivery is safe. Ambiguity alone never authorizes
blind retry, never proves admission, and never proves non-admission. C0 MUST NOT
assume or specify the in-flight ES reliable-submit or Nomad-reconciliation
algorithm.

### C0-SD-009 - Observations Are Not Semantic Decisions

Classification: STRATEGIC TARGET.

External observations are source-attributed facts or evidence. Coordinator may
durably bind them and make progression decisions over them, but an observation
MUST NOT directly advance desired state or become semantic acceptance, repair,
replan, publication, or program completion.

The target freezes these non-equivalences:

- source observation != semantic acceptance;
- successful process exit != accepted change;
- ES terminal state != accepted work;
- validation success != publication;
- Git commit or ref != program completion;
- cancellation receipt != termination proof;
- source termination observation != successful cancellation semantics.

Acceptance, retry, repair, replan, block, supersession, abandonment, and
publication progression are explicit Coordinator decisions.

## Stop, Cancellation, Publication, Authority, And Custody

### C0-SD-010 - Stop And Cancellation Compatibility

Classification: COMPATIBILITY EDGE and CURRENT CONTRACT / INVARIANT.

Current coding `global_stop` remains unchanged. It remains the strongest current
coding-effect authority gate under present contracts. C0 MUST NOT weaken,
reinterpret, clear, replace, or generalize its current authority.

A stop directive, cancellation intent, cancellation receipt, source termination
observation, and semantic abandonment or acceptance remain distinct. Future
program-, work-, attempt-, effect-, or invocation-scoped stops are additive
target concepts. Their hierarchy, precedence, authorization, and exact
permissions remain open. This clause does not define evaluator ordering,
returned-reason priority, or interaction with `stage_not_enabled`.

### C0-SD-011 - Publication Separation

Classification: STRATEGIC TARGET.

Semantic acceptance creates publication eligibility at most. The target MUST
keep semantic acceptance, publication eligibility, publication progression
decision, publication intent, publication effect, Git object/ref/push/PR truth,
publication observation, and publication acceptance or completion decision
distinct.

Coordinator may own publication intent and progression decisions. Git and owner
repositories retain object/ref and action truth. C0 does not select Git
credentials, Git commands, branch policy, PR policy, publication transport, or
publisher placement.

C1 closes the first-slice maximum effect at one local feature-branch Git commit
after Coordinator semantic acceptance and a separately selected Git
effect. The worker must not silently commit during authoring. Push, remote-ref
mutation, PR creation, merge, and deployment are blocked first-slice effects,
not implied consequences of acceptance or a local commit.

### C0-SD-012 - Private-Material And Evidence Custody

Classification: STRATEGIC TARGET with CURRENT REPORT PRIVACY INVARIANT.

Durable Coordinator program truth may contain only the minimal normalized
intent, objective or work descriptions, classifications, decisions, hashes, and
safe opaque references required for progression. Durable does not mean public;
normalized state may itself be access-controlled.

Raw prompts, model transcripts, Codex JSONL, unrestricted logs, command output,
workspaces, raw diffs, raw retained-result bodies, credentials, endpoints,
local paths, and trust material remain separate evidence or custody material.
Retention in a future private evidence store would not make those bytes program
authority or semantic-acceptance truth. Coordinator may bind safe references and
relevant verification results. Public reports and projections remain more
restrictive and must preserve current report privacy contracts.

C1 closes the first-slice candidate-custody split conceptually. The worker
invocation authors candidate bytes; a capsule builder acting at the worker
boundary seals a canonical manifest, blobs, and portable digest; and a private,
immutable, content-addressed worker-side store outside the mutable worktree and
Coordinator SQLite has physical custody. Coordinator may retain only a safe
capsule digest/reference and progression decisions. Reviewer retrieval is
read-only, attempt-bound, and capsule-bound; later ES transport or retention is
opaque; and Git becomes object/ref truth only after a separate commit effect.
A capsule digest is not a path, endpoint, bearer retrieval credential,
authorization proof, acceptance decision, or Git identity. Exact path, storage
technology, encryption, garbage collection, retention, serialization, and wire
encoding remain future implementation details.

### C0-SD-013 - Executable Authority Binding

Classification: STRATEGIC TARGET.

Planning, proposal formation, and non-effectful reasoning may exist without
executable authority. Before an execution-producing effect becomes eligible for
dispatch, and before any execution-producing external I/O, its durable effect
intent MUST bind an immutable, externally issued, scope-compatible standing
authority reference or verified decision.

External standing-policy authority authors the immutable grant, revocation or
expiry, applicable global-stop directives, and effect ceilings. Coordinator
MUST NOT mint, renew, widen, reinterpret, or silently reuse that external
standing authority. Under C1's accepted target only, Coordinator may derive a
narrower subordinate attempt/effect authorization record and issue a fence
within the verified parent grant. The subordinate record binds the parent grant
and exact program version, work item, semantic attempt, and effect; cannot
exceed or outlive the parent; fails closed on absence, staleness, expiry,
revocation, ambiguity, or insufficiency; and is not a new grant issuer.

A parent grant may cover more than one effect or attempt only when its immutable
scope and ceilings expressly permit bounded reuse, and each subordinate binding
is explicit. The external authority does not write Coordinator SQLite directly,
and Coordinator's durable record does not become independent external
authority. Current subordinate-authorization runtime behavior remains absent.

C0 does not select issuer, verifier deployment, encoding, signer, trust root,
revocation transport, or wire protocol.

## Required Gates, Explicit Non-Claims, And Open Decisions

### C0-SD-014 - Ambiguity Vocabulary Is Not A Universal State Machine

Classification: STRATEGIC TARGET and IMPLEMENTATION DETAIL LEFT OPEN.

The target may distinguish semantic facts such as intended, durably recorded,
eligible, delivery attempted, acknowledged, externally admitted, observed,
terminal observed, semantically accepted, stale, conflicting, blocked,
superseded, abandoned, and ambiguous or unknown.

These are semantic distinctions. They are not a mandatory enum, a universal
linear lifecycle, or a shared cross-domain state machine. Different effects and
source contracts may expose different subsets.

An ambiguous effect outcome means an external effect may or may not have crossed
its boundary. An unknown or inconclusive observation means available evidence
cannot establish the relevant source fact. C0 MUST NOT collapse those cases.

### C0-SD-015 - Implementation And Cross-Repository Choices Remain Open

Classification: `ACCEPTED STRATEGIC TARGET` for choices superseded by C1,
`FUTURE IMPLEMENTATION DETAIL` for the remaining open mechanics, and
`REPORT-ONLY UNCERTAINTY` where owning-repository evidence is absent.

C1 supersedes C0's open alternatives for the first software-development slice:
worker source and initial release machinery live in the Coordinator repository;
the worker runs as a separate OS process; a bounded direct-local
bootstrap/proof route precedes later ES routing through the same versioned
contracts; Bridge and Bridge Core are not worker owners; the first private
immutable content-addressed capsule has worker-side custody; external standing
authority and subordinate Coordinator records are distinct; and the maximum
effect is one local feature-branch Git commit after acceptance.

The remaining implementation details are exact schema and migration design;
current-state tables versus event sourcing; outbox/inbox design;
service/API/IPC/queue/scheduler mechanics; worker package, executable, build,
supervisor, credential, and IPC mechanics; process framing, transport wrapping,
and ES wire mapping for the C2A-frozen worker
command/observation/fence/capsule semantic fields;
ES request/response/correlation/query/cancellation/result-ingest wire contracts;
model provider, model protocol, and
prompt transport; authority issuer/verifier deployment, encoding, signer,
trust root, revocation transport, and credential form; Git commands, branch
naming, commit-message format, credentials, CI transport, and publisher
implementation; capsule path, storage technology, encryption, garbage
collection, retention, serialization, and recovery; CP/IM/MA migration,
retirement, or integration; stop precedence; and final program-completion
semantics when intent can continue evolving.

C0 and a later strictly pure, transport-neutral Coordinator domain model do not
require an ES repository change. Concrete ES-backed dispatch, reconciliation,
cancellation, runtime observation, result ingest, and unattended execution
require separately accepted ES and cross-repository contracts.

The pure semantic-contract prerequisite is now satisfied by the accepted C2A
document and the current C2A1 internal no-I/O values and six pure coherence
validators. Durable schema, authority verification, process launch, worker
execution, observation ingest, acceptance runtime, and Git effect remain
unsatisfied required-before-runtime gates. A separately accepted implementation
contract must still freeze the applicable runtime, direct-local or ES adapter,
transport, and persistence mechanics before schema, service, worker, adapter,
Git/CI, or runtime execution work.

## C2B1/C2B2 Current Migration And Pure-Value Boundary

Status: `CURRENT IMPLEMENTED CONTRACT` for explicit SQLite administration and
private pure no-I/O row/value validation only. C2B0 remains the historical
accepted-target contract tranche.

C2B1 implements exact-current ordinary open and explicit supported-prefix
migration in `sqlite_migration.py`. Complete-catalog initialization and
complete contiguous suffix migration use one administrative transaction and
three-way commit readback under the retained common lock. Migration eligibility,
history, schema evidence, and recovery evidence are administrative facts only;
they are not development-program admission, selection, attempt, observation,
decision, acceptance, effect, publication, or completion truth.

C2B2 Slice 1 uses this administrative boundary at application generation 2 and
terminal migration `0002_development_program_and_effect_state`. It implements
only physical representability for the frozen nineteen-table core. Slice 2
adds private pure row/value source for those nineteen tables, with no SQLite,
SQL, capability use, database reader, or production caller. No C2B product
mutation, complete family graph verification, family replay or recovery, or
C2B3 behavior is added.

Durable development progression, source-observation ingest, semantic decisions,
effect establishment or execution, WorkSpec custody, worker/process behavior,
capsule storage, Git effects, direct-local execution, ES routing, and autonomous
runtime remain unimplemented. C2B1 adds no product progression transaction,
reader, writer, public API, service, scheduler, queue, or publication authority.

## C2B0 Accepted Durable Progression Closure

Status: `ACCEPTED TARGET CONTRACT`; the C0 historical statements above remain
historical and durable C2B progression remains unimplemented.

The exact ordered decision kinds are `initialize`, `accept`, `repair`,
`replan`, `terminal_reject`, `block`, `redeliver`, and `cancel`. `initialize`
creates program version 1 of kind `initial` and preassigns the first semantic
attempt and candidate. `cancel` is a distinct immutable decision, advances no
program version, preassigns a cancellation effect/fence/first delivery, and is
not global stop, block, terminal rejection, acknowledgement, termination, or
abandonment.

Every durable effect has a non-null immediate `basis_decision_ref`. An author
effect uses the exact `initialize`, `repair`, or attempt-selecting `replan`
decision that preassigned its attempt/candidate. Validation and review reuse
the selection decision bound to the existing attempt. Cancellation uses the
exact cancel decision and target. `block` and `terminal_reject` cannot
substitute as cancellation bases.

Author-effect establishment creates the semantic attempt, candidate identity,
AttemptFence, author effect/fence, sole originating `WorkerCommandV1`, initial
delivery, heads, and receipt. Bound validation, review, and cancellation
effects reuse that attempt, candidate, AttemptFence, originating command, and
post-bound author EffectFence. They create no attempt, candidate, second
command, author effect, or program version. A new semantic attempt remains
possible only after an explicit attempt-selecting Coordinator decision.
