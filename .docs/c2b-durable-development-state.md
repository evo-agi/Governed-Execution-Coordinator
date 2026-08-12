# C2B Durable Development State

This document is the sole detailed owner of the accepted C2B durable
software-development state target. C2A remains authoritative for field-level
semantic records, identities, vectors, digests, and pure relations. C2A1
remains authoritative for the current pure Python value/API behavior. Existing
SQLite documents remain authoritative for current implemented backend,
security, writer, migration, and recovery mechanics.

## 1. Status, Classification, And Layering

Classification: `CURRENT IMPLEMENTED CONTRACT` for C2B1 migration
administration and `ACCEPTED TARGET CONTRACT` for the durable-development
representation and C2B2-C2B6 behavior below.

C2B0 was the historical documentation-and-direct-contract-test tranche. C2B1
now implements only the bounded administrative migration framework in the
existing Coordinator database. C2B durable software-development state under
the existing writer authority remains target-only. Durable development
records and behavior are absent, external effects are absent, and a C2B public
API is absent.

The contract uses these layers:

```text
CURRENT IMPLEMENTED CONTRACT
CURRENT COMPATIBILITY EDGE
ACCEPTED TARGET CONTRACT
FUTURE IMPLEMENTATION DETAIL
DEFERRED MECHANIC
```

`CURRENT IMPLEMENTED CONTRACT` remains bounded coding-work transition and
coding-global-stop SQLite mutation. `CURRENT COMPATIBILITY EDGE` preserves
schema-0001 backlog, work-item, transition, lease, and global-stop meanings.
This document is an `ACCEPTED TARGET CONTRACT`; later source and SQL mechanics
remain `FUTURE IMPLEMENTATION DETAIL`. Private WorkSpec custody, external
authority verification, worker launch, capsule storage, Git effects,
direct-local execution, and ES routing remain `DEFERRED MECHANIC` work.

The current implemented application generation remains 1. The current C2B1
migration framework is implemented, while durable development state remains
target-only. The packaged
catalog and managed database tip remain `0001_initial`, schema 0001 is
unchanged, and there is exactly one production SQL migration. C2B1 implements
exact-current ordinary open, explicit supported-prefix migration,
terminal-only compatibility, cumulative packaged-SQL schema authority,
whole-suffix single-transaction administration, and three-way migration
commit recovery. It implements no durable-development representation or
runtime authority.
The accepted C2B target reserves migrations
`0002_development_program_and_effect_state` and
`0003_development_observation_and_progression_state`; their exact target
responsibilities and inventories are frozen below. No 0002/0003 SQL, catalog
entry, schema object, installed migration, application-generation change, C2B
durable record, product reader, product writer, product mutation transaction,
ingest or progression recovery path, worker, process,
model integration, capsule store, Git effect, adapter, ES route, service,
scheduler, queue, or autonomous loop currently exists.
No target C2B reader, writer, mutation, transaction, ingest, or durable runtime
exists; C2B1 migration administration does not satisfy any of those roles.

## 2. One Database, One Writer, And Fact Ownership

C2B must reuse exactly:

```text
one existing Coordinator SQLite database
one existing writer issuance and fencing authority
one existing operation guard
one existing mutation slot
one existing transaction controller
```

It must add no second database, writer, session authority, transaction
controller, generic mutation dispatcher, public `StateStore` method, or public
`WriterSession` method.

Coordinator may author and record its own durable progression, effect-intent,
ingest-disposition, decision, eligibility, and latch facts. Coordinator does
not author standing grants, external source invocations, source observations,
candidate bytes, capsule bytes, validation or independent-review observations,
Git objects or refs, or ES admission/runtime facts. Persistence of a reference
or digest never transfers authorship, custody, authorization, or source truth.

## 3. Identity Non-Collapse

The following remain distinct durable or externally bound identities:

```text
program
program version
accepted-intent revision
work item
work-item revision
semantic attempt
effect intent
effect fence
delivery attempt
source invocation
source observation
observation ingest disposition
candidate
capsule manifest
portable capsule digest
Coordinator decision
publication eligibility
Git-effect intent
Git commit
publication state
mutation receipt
```

Current schema-0001 backlog, admitted-backlog, work-item, transition-event,
attempt-count, repair-count, lease, and idempotency identities cannot substitute
for any target identity. Reports and projections cannot substitute for durable
truth.

## 4. Hybrid Durable Representation

The selected representation combines mutable CAS-protected current heads,
immutable role-specific records, and immutable mutation receipts.

The exact mutable target records are:

```text
development_program_heads
development_work_item_heads
development_effect_heads
development_delivery_heads
development_observation_ref_heads
development_first_slice_latch
```

The latch is mutable only through its one-way `available` to `consumed`
transition. Every other proposed semantic or evidence record is immutable.
Immutable tables receive no-update and no-delete guards; the latch receives a
no-delete guard and one-way update guard.

C2B rejects one mutable aggregate JSON row, fully mutable normalized history,
one generic event ledger, reuse of `work_items` or `transition_events` as target
truth, and projection tables as authority.

## 5. Program Genesis

Program genesis requires a real immutable `initialize` decision.

```text
program_version_number: 1
program_version_kind: initial
creating_decision_ref: required and non-null
initial program head revision: 0
preassigned semantic attempt: required
preassigned candidate: required
```

The initialization transaction atomically creates:

```text
program head
program version 1
accepted-intent safe revision binding
initial work-item heads
initial work-item revisions
program-version membership
WorkSpec safe bindings
initialize decision
mutation receipt
```

It creates no semantic-attempt row, effect, command, delivery, observation,
capsule, Git fact, or external request.

The genesis relationships are:

```text
program head <-> current version
program version <-> creating decision
initialize decision <-> resulting version
work head <-> initial work revision
```

Those foreign-key cycles use `DEFERRABLE INITIALLY DEFERRED`. Foreign keys are
never disabled.

## 6. Exact Decision-Kind Inventory

The exact ordered, case-sensitive first-slice decision kinds are:

```text
initialize
accept
repair
replan
terminal_reject
block
redeliver
cancel
```

No alias, extension bag, unknown kind, or implicit decision is permitted.

Version effects are exact:

```text
initialize: creates version 1
accept: appends an accepted program version
repair: appends a program version and preassigns a successor attempt/candidate
replan: appends accepted-intent/work revision and program-version state
terminal_reject: appends a terminal-rejected version
block: appends a blocked version
redeliver: no program-version advance
cancel: no program-version advance
```

No decision performs an external effect.

## 7. Distinct Cancel Decision

`cancel` is a real immutable Coordinator decision. It is not coding global
stop, `block`, `terminal_reject`, a cancellation effect, delivery,
acknowledgement, termination observation, semantic abandonment, or runtime
termination.

The closed cancel-command semantic fields are:

```text
schema_id
mutation_ref
decision_ref
decision_kind
program_ref
program_version_ref
program_version_number
expected_program_head_revision
semantic_attempt_ref
candidate_ref
attempt_fence_ref
attempt_fence_digest
target_effect_intent_ref
target_effect_class
target_effect_fence_ref
target_effect_fence_digest
expected_target_effect_head_revision
originating_command_ref
originating_command_digest
target_capsule_manifest_ref
target_portable_capsule_digest
coding_global_stop_ref
coding_global_stop_version
source_directive_ref
source_directive_digest
source_evidence_ref
source_evidence_digest
preassigned_cancel_effect_intent_ref
preassigned_cancel_effect_fence_ref
preassigned_first_cancel_delivery_attempt_ref
```

Target classes are exactly:

```text
author_candidate
validate_candidate
review_candidate
```

Targets of class `cancel_effect` or `local_git_commit` are rejected. An author
target forbids the paired capsule fields. A validation or review target
requires the exact paired capsule-manifest ref and portable digest.

The cancel-decision transaction creates only one immutable decision, its
closed-role decision-evidence bindings, and one mutation receipt. It creates no
version, attempt, candidate, command, effect, delivery, observation,
acknowledgement, abandonment, or external request. Program-head and target-head
revisions are fresh-operation checks; cancellation-effect establishment owns
the target-head CAS.

## 8. Decision-To-Effect Basis

Every durable effect intent requires this exact immediate foreign key:

```sql
basis_decision_ref TEXT NOT NULL
  REFERENCES development_decisions(decision_ref)
  ON UPDATE RESTRICT
  ON DELETE RESTRICT
```

Basis relations are exact:

```text
author_candidate:
  exact initialize, repair, or attempt-selecting replan decision that
  preassigned the attempt and candidate

validate_candidate:
  exact selection decision already bound to the existing attempt

review_candidate:
  exact selection decision already bound to the existing attempt

cancel_effect:
  exact cancel decision that preassigned the cancellation effect, fence, and
  first delivery and named the exact target
```

Nullable, unrelated, cross-program, cross-version, cross-attempt, or
cross-candidate bases are rejected. `block` and `terminal_reject` cannot be a
cancellation basis. `accept` and `redeliver` cannot be an author basis.

## 9. Originating Author-Command Cardinality

One candidate has exactly one originating `WorkerCommandV1`. One originating
command has exactly one `author_candidate` effect. That same command may be
referenced by author, validation, review, and cancellation effects in the same
attempt/candidate lineage. Every effect references exactly one originating
command.

Target constraints are:

```text
development_author_commands.command_ref: primary key
development_author_commands.author_effect_intent_ref: unique
development_author_commands.candidate_ref: unique
development_effect_intents.command_ref: non-unique foreign key
development_effect_intents: one author_candidate effect per command
```

The exact partial unique index is
`uq_development_effect_intents_author_command`, defined as
`UNIQUE(command_ref) WHERE effect_class='author_candidate'`.

Positive relation:

```text
attempt A1
candidate K1
originating command C1
author effect -> C1
validation effect -> C1
review effect -> C1
cancellation effect -> C1
```

A second command for A1/K1, two author effects under C1, or two originating
commands for K1 is rejected.

## 10. Author-Effect Establishment

The private target roles are `_initialize_development_program` and
`_establish_development_author_effect_intent`. Author-effect establishment
consumes an already committed `initialize`, `repair`, or attempt-selecting
`replan` decision and the exact attempt/candidate refs it preassigned.

It atomically creates:

```text
semantic attempt
candidate identity through the attempt graph
AttemptFence binding
author effect intent
author EffectFence
one originating WorkerCommandV1
authority evaluation
initial author delivery
effect head
delivery head
mutation receipt
```

It creates no validation, review, cancellation, source observation, capsule
bytes, Git fact, external process, or external I/O.

## 11. Bound-Effect Establishment

The distinct private target role is
`_establish_development_bound_effect_intent`. Its closed binding variants are
validation, review, and cancellation.

Every variant reuses:

```text
existing semantic attempt
existing candidate
existing AttemptFence
existing originating command
existing post-bound author EffectFence
```

Every variant creates only:

```text
new current effect intent
new current EffectFence
new authority evaluation
new initial delivery
new effect head
new delivery head
mutation receipt
```

It creates no new semantic attempt, candidate, `WorkerCommandV1`, author
effect, program version, or source observation.

Validation requires the exact candidate capsule and validation requirement.
Review requires the exact candidate capsule and review requirement.
Cancellation requires the exact cancel decision, target effect/fence/head, and
target capsule when the target consumes one. Cancellation CAS-updates the
target effect knowledge to `cancellation_effect_established`. That state is
Coordinator knowledge only; it does not imply an external request,
acknowledgement, termination, or abandonment.

## 12. Complete Target Mutation Families

The complete target mutation-family inventory is:

```text
_initialize_development_program
_establish_development_author_effect_intent
_establish_development_bound_effect_intent
_ingest_development_source_observation
_record_development_progression_decision
```

The corresponding recovery-family inventory is:

```text
_resolve_development_program_initialization_commit_outcome
_resolve_development_author_effect_establishment_commit_outcome
_resolve_development_bound_effect_establishment_commit_outcome
_resolve_development_source_observation_ingest_commit_outcome
_resolve_development_progression_decision_commit_outcome
```

These names describe target internal roles, not public package APIs or stable
external methods. C2B0 implements none of them.

## 13. Source Invocation, Observation, And Ingest

A delivery attempt is a Coordinator-planned identity. A source invocation is a
source-authored external identity. A source observation is a source-authored
record and digest. An ingest disposition is a Coordinator-authored
classification. A progression decision is a separate Coordinator-authored
semantic judgment.

Source-observation identity is `(observation_ref, observation_digest)`.
Same-ref/different-digest claims may both be retained for conflict handling.

The exact ingest order is:

```text
1. C2A1 record-local validation
2. actual durable graph validation
3. preserve source-authored claim
4. compare prior observation identity/digest
5. classify source-owner relation
6. append Coordinator ingest disposition
7. evaluate semantic progression separately
```

The exact disposition vocabulary and precedence is:

```text
duplicate_exact
conflict_quarantined
ambiguous_quarantined
stale_retained
late_retained
recorded
```

A malformed observation creates no claim, disposition, receipt, or head
change. No observation or disposition directly authorizes acceptance, repair,
replan, redelivery, publication, or program completion.

## 14. Unknown Outcome And Redelivery

Unknown source observation, source-native rejection or nonacceptance, ingest
disposition, Coordinator redeliver decision, successor delivery attempt, and
actual redelivery remain distinct. The C2A five-condition rule remains
governing.

C2B may later record a redeliver decision and successor delivery. C2B does not
perform redelivery. It must not introduce a generic reconciled Boolean,
timeout-as-failure, blind redelivery, Nomad scraping, Bridge recovery
authority, or trace/request-ID authority.

## 15. Coding Global-Stop Matrix

This is a new C2B target decision, not an inherited C1 invariant. For a fresh
operation while coding `global_stop` is active:

```text
initialize program: block
establish author effect: block
establish validation effect: block
establish review effect: block
create productive initial delivery: block
redeliver productive effect: block
accept: block
repair: block
productive replan: block
publication eligibility: block
consume first-slice latch: block
local Git eligibility or effect: block
record source invocation for an existing delivery: permit
ingest source observation: permit
retain duplicate/conflict/ambiguous/stale/late evidence: permit
record terminal reject: permit
record block: permit
record cancel decision: permit
establish cancellation effect and initial cancellation delivery: permit
redeliver an existing cancellation effect: permit
ingest cancellation acknowledgement or termination evidence: permit as source evidence
perform external cancellation: not implemented
```

Cancellation planning is also permitted under a clear stop, subject to the
same exact version and target checks.

A fresh blocked operation returns `coding_global_stop_active` and creates no
receipt. Stop-version disagreement returns `global_stop_version_conflict` and
creates no receipt. Exact replay of an already committed operation precedes
fresh stop/head checks and returns the original result.

Stop clearance changes the stop version. A recorded but unestablished cancel
decision bound to an older version remains immutable history but cannot
establish its effect; a new current-version decision is required. A target
that becomes terminal or changes from the decision-bound head revision also
prevents effect establishment.

## 16. Private WorkSpec Custody

The semantic author is the accepted-intent/work-specification authority. C2B
records safe bindings only. The physical custodian is explicitly deferred.
Coordinator SQLite is a safe-reference holder, not a private-material store.
Retrieval authorization requires a separately accepted future contract.

C2B may retain:

```text
work_spec_ref
source WorkSpec digest
safe program/work/repository/base/path bindings
validation/review requirement bindings
privacy classification
distinct C2B safe-projection digest
```

C2B must not retain:

```text
objective text
requirements
exclusions
raw prompts
model responses
transcripts
candidate bytes
capsule entries
workspace paths
credentials
private endpoints
bearer retrieval material
```

A safe ref is not retrieval authority. A digest is not the private WorkSpec.
SQLite cannot reconstruct the private WorkSpec. Chat, model-session memory,
reports, connectors, and Bridge ledgers cannot become hidden custody.

C2B3 may later receive a complete validated WorkSpec transiently but may
persist only its safe projection. Restart-safe author establishment and worker
launch remain blocked until a separately accepted custody, retention,
authorization, and attempt-bound retrieval contract exists. C2B0 selects no
custodian or storage technology.

## 17. C2A Value Persistence Matrix

The target privacy matrix is:

```text
WorkSpecV1:
  safe projection only; exclude objective, requirements, exclusions
CeilingsV1:
  all fifteen integers where embedded; no standalone authority row
AttemptFenceV1:
  complete canonical mapping and digest
EffectFenceV1:
  complete canonical mapping and digest
WorkerCommandV1:
  complete canonical mapping and digest
DeliveryEnvelopeV1:
  complete canonical mapping and digest before future external I/O
WorkerObservationV1:
  complete validated canonical mapping and digest
CandidateCapsuleManifestV1:
  safe projection excluding entries; safe bindings, portable digest, and a distinct projection digest
CapsuleEntryV1:
  persist nothing
```

Candidate and capsule bytes, capsule entries, paths, modes, file digests,
lengths, and real workspace material remain outside Coordinator SQLite.

## 18. Authority Evaluation

Only safe authority bindings may be persisted. Target authority-evaluation
states are:

```text
pending
verified
blocked
stale
revoked
expired
```

A separately accepted external verifier must supply `verified`; C2B does not
implement that verifier. A reference, digest, record, relation, caller Boolean,
or Coordinator decision is not executable authorization. Without a verified
current authority result, an effect is not eligible for future dispatch.
Eligibility remains distinct from ES admission and actual execution.

## 19. First-Slice One-Shot Latch

The latch contract is:

```text
latch_ref: direct_local_first_productive_acceptance
scope: global Coordinator bootstrap
initial state: available
initial version: 0
final state: consumed
final version: 1
reset: forbidden
delete: forbidden
reuse: forbidden
```

Consumption is atomic with the first accepted productive direct-local
decision. It binds `decision_ref`, `program_version_ref`, `candidate_ref`,
`capsule_manifest_ref`, `portable_capsule_digest`, and the transaction
timestamp. Missing, duplicate, malformed, ambiguous, or already consumed state
fails closed. The consumed latch blocks a second productive acceptance.

The latch is not a scheduler, queue, backlog, lease, or general program truth.
Retirement or expansion requires a separately reviewed future migration.

## 20. Migration-Framework Strategy

Migration `0001_initial` retains immutable bytes, checksum, history, and
meanings. Every installed migration row remains immutable and is the persisted
projection of one packaged definition. The persisted projection contains
sequence, migration ID, checksum, `applied_at`, and compatibility bounds.
`applied_at` is validated persisted row data, not packaged catalog metadata and
not definition identity. Exact sequence, migration ID, checksum, and bounds
resolve one definition; that definition supplies the catalog-only
`destructive` value. `schema_migrations` has no `destructive` column.
Compatibility bounds describe the application
generations allowed to own a database when that migration is the installed
terminal tip; they do not require every historical row to include the running
application generation. Historical `0001_initial` therefore remains `[1,1]`,
while migrations 0002 and 0003 are each `[2,2]`. No immutable history row,
including migration 0001, is rewritten.

Ordinary product or writer open requires all of the following:

```text
exact complete catalog history
exact current terminal sequence and migration ID
terminal migration compatibility containing the current application generation
complete final-schema verification
```

Ordinary open never silently migrates and never accepts an older prefix. An
explicit migration preflight may recognize one exact non-empty supported older
catalog prefix only when every installed row has exact packaged checksum and
metadata, there are no gaps, unknown rows, partial rows, divergent bounds, or
ambiguous catalog resolution, and one exact contiguous packaged suffix leads to the current terminal
tip. A supported older prefix is migration-eligible only; it is not ordinarily
product-openable before migration.

C2B1 is a framework-only source/test reset: it adds no SQL or database change
and is now the current migration-administration implementation. The implemented
application generation remains 1, and the current
catalog and terminal tip remain exactly `0001_initial`. It privately
distinguishes absent, empty, current, supported older prefix, unsupported older,
newer unsupported, corrupt history, partial migration, and non-empty unmanaged
state while preserving the public absent/empty/managed/unknown classification.
Any selected destructive definition is rejected before common-lock acquisition,
writable open, `BEGIN IMMEDIATE`, or database mutation.

C2B2 advances the implemented application generation from 1 to 2 when it adds
migration 0002, and its catalog terminal tip becomes 0002. C2B3 remains
application generation 2 with terminal migration 0002. C2B4 adds migration 0003
while retaining application generation 2, and its terminal tip becomes 0003.
C2B5 and C2B6 remain application generation 2 with terminal migration 0003.

Fresh installation and upgrade always apply the complete missing cumulative
catalog suffix:

```text
C2B2 fresh installation: 0001 -> 0002
C2B4-or-later fresh installation: 0001 -> 0002 -> 0003
C2B2 upgrade from exact 0001: apply only 0002
C2B4-or-later upgrade from exact 0001: apply 0002 then 0003
C2B4-or-later upgrade from exact 0002: apply only 0003
```

For every path above, the complete intended packaged suffix is one
administrative transaction:

```text
C2B2 fresh installation transaction: [0001, 0002]
C2B4-or-later fresh installation transaction: [0001, 0002, 0003]
C2B2 upgrade from exact 0001 transaction: [0002]
C2B4-or-later upgrade from exact 0001 transaction: [0002, 0003]
C2B4-or-later upgrade from exact 0002 transaction: [0003]
```

Every migration selected for that suffix contributes all of the following to
the same administrative transaction:

```text
DDL
managed invariant changes
matching migration-history insertion
```

No suffix migration may commit before a later migration in the same selected
suffix is attempted. A history row without its schema effects, schema effects
without the matching history row, and a partially installed suffix are all
forbidden. Failure before commit restores the complete exact prior supported
prefix with no partial DDL, invariant change, or history row and never rewrites
0001. Ordinary product or writer open never performs migration.

If an administrative commit attempt raises, migration recovery must:

```text
close the uncertain connection
reopen through the migration recovery path
reread the complete exact migration history
reread the complete live-schema invariants
compare both the exact prior supported prefix and exact intended completed suffix tip
```

The evidence classifications are exact:

```text
COMMITTED_EXACT
history equals the prior prefix plus the complete intended suffix
every suffix row's persisted projection resolves exactly to one packaged non-destructive definition
live schema equals the complete intended terminal-tip schema
the prior prefix remains unchanged
no partial, extra, unknown, or divergent object exists
```

```text
DEFINITELY_NOT_COMMITTED
history equals the exact prior supported prefix
live schema equals the exact prior supported-prefix schema
no intended suffix history row exists
no intended suffix schema object or invariant exists
no partial or unexpected object exists
```

```text
UNRESOLVED
history and schema disagree
only part of the intended suffix is present
history-only suffix evidence exists
schema-only suffix evidence exists
an unknown or divergent history row exists
an unexpected schema object exists
either exact verification cannot be completed
```

An `unresolved` result forbids automatic rerun and automatic append of a
missing remainder. This is the `UNRESOLVED` evidence outcome and raises only
`migration_outcome_unresolved`. An operator or separately accepted recovery must complete
before another migration attempt. This migration-specific rule is distinct
from the semantic progression-mutation retry contract.

A generation-1 binary rejects migration sequence 2 or 3 as newer and
unsupported. A generation-2 binary whose terminal catalog is 0002 ordinarily
opens exact 0002 and rejects 0003 as newer. A generation-2 binary whose terminal
catalog is 0003 ordinarily opens exact 0003 and treats exact 0001 or 0002 only
as explicitly migratable supported prefixes. Final schema authority is the
cumulative packaged migration sequence; no cumulative schema snapshot is
introduced.

## 21. Migration 0002

The target migration is `0002_development_program_and_effect_state`, with
application compatibility bounds `[2,2]`, `destructive: no`, nineteen new
tables, and no seeded C2B rows.

The exact table inventory is:

```text
development_program_heads
development_program_versions
development_accepted_intent_revisions
development_work_item_heads
development_work_item_revisions
development_program_version_work_items
development_revision_edges
development_work_spec_bindings
development_semantic_attempts
development_attempt_fences
development_authority_evaluations
development_effect_intents
development_effect_fences
development_author_commands
development_effect_heads
development_delivery_attempts
development_delivery_heads
development_decisions
development_mutation_receipts
```

`development_decisions` supports the base decision envelope and the
`initialize` decision representation. C2B2 owns and lands both the base
decision envelope and initialize-decision row treatment, without adding a
mutation API. C2B3 later uses that representation for program initialization.
C2B4 adds only non-initialize, evidence-bearing decision contracts; it neither
owns initialize representation nor is the first point at which a durable
decision row is representable. `development_decisions` is a closed
kind-specific contract, not a generic decision metadata bag.

## 22. Migration 0003

The target migration is `0003_development_observation_and_progression_state`,
with application compatibility bounds `[2,2]`, `destructive: no`, and nine new
tables.

The exact table inventory is:

```text
development_source_invocations
development_candidate_capsule_bindings
development_source_observation_claims
development_observation_ref_heads
development_observation_ingests
development_observation_quarantines
development_decision_evidence_bindings
development_publication_eligibility
development_first_slice_latch
```

`development_decision_evidence_bindings` is a closed role-specific relation,
not a metadata bag. Cancellation roles are:

```text
cancel_target_effect
cancel_target_effect_fence
cancel_target_capsule
cancel_source_directive
cancel_source_evidence
```

The capsule role is required only when the target consumes a capsule.

Migration 0003 seeds only:

```text
latch_ref: direct_local_first_productive_acceptance
state: available
version: 0
consumed bindings: null
```

## 23. Exact Schema Totals

The exact target totals are:

```text
schema 0001: 11 user tables, 0 explicit application indexes, 16 triggers
schema tip 0002: 30 user tables, 1 explicit application index, 46 triggers
schema tip 0003: 39 user tables, 2 explicit application indexes, 62 triggers
```

C2B adds exactly twenty-eight tables, forty-six triggers, and two explicit
indexes. The migration split is:

```text
0002: 19 tables, 30 triggers, 1 explicit index
0003: 9 tables, 16 triggers, 1 explicit index
```

Trigger arithmetic is exact:

```text
0002: 15 immutable tables * no-update/no-delete = 30
0003: 7 immutable tables * no-update/no-delete = 14
0003: latch no-delete = 1
0003: latch one-way update guard = 1
```

Migration 0003 seeds exactly the one available latch row described above; all
other new C2B tables begin empty.

## 24. Exact Explicit Indexes

The exact explicit index inventory is:

```text
uq_development_effect_intents_author_command
idx_development_source_observation_claims_digest
```

`uq_development_effect_intents_author_command` is
`UNIQUE(command_ref) WHERE effect_class='author_candidate'`.
`idx_development_source_observation_claims_digest` supports bounded
different-ref/same-digest ambiguity lookup.

No index is added for dashboard browsing, lineage exploration, hypothetical
analytics, or future convenience. SQLite-managed primary-key and unique
autoindexes are excluded from explicit-index totals.

## 25. Transaction And Replay Algebra

Every future mutation follows this exact order:

```text
1. exact command-local preflight
2. session operation guard
3. shared mutation slot
4. resource-bound connection
5. BEGIN IMMEDIATE
6. managed-schema and resource revalidation
7. durable writer fencing
8. mutation-receipt lookup
9. exact replay or same-key conflict
10. fresh program, stop, decision, and effect graph reads
11. CAS and knowledge checks
12. one transaction UTC timestamp
13. one immutable role-specific write plan
14. capability invalidation
15. exactly one commit attempt
16. cleanup while retaining the shared slot
```

Exact replay precedes current-state checks. The outcome algebra is:

```text
same mutation_ref + same canonical digest: exact replay
same mutation_ref + different digest: mutation_ref_reuse_conflict
same semantic ref + different graph/digest: semantic identity conflict
stale program head: program_head_conflict
stale cancellation target: target_effect_state_conflict
fresh productive operation under active stop: coding_global_stop_active
commit attempt raises: commit_outcome_unknown
resolver proves complete receipt/graph: committed_exact
resolver proves absence: definitely_not_committed
resolver cannot classify: unresolved
```

No mutation automatically retries after an unknown commit outcome. A
cancellation effect cannot be established while the cancel-decision commit is
unresolved. No external I/O occurs inside the transaction or in any C2B
implementation tranche.

## 26. Exact Target Tranche Sequence

The exact sequence is:

```text
C2B0: historical documentation and direct documentation-contract tests only
C2B1: current application generation 1; terminal tip 0001; migration-framework reset only; no SQL or schema change; no durable development state
C2B2: application generation advances to 2; terminal tip 0002; migration 0002; core records, base decision envelope, initialize-decision representation, private readers; no mutation API
C2B3: application generation 2; terminal tip 0002; program initialization, author-effect establishment, private delegation and recovery; no external I/O
C2B4: application generation 2; terminal tip 0003; migration 0003; observation/evidence/non-initialize-decision/eligibility/latch contracts and readers; initialize representation remains C2B2-owned; no new mutation API
C2B5: application generation 2; terminal tip 0003; source-observation ingest, cancel and redeliver decisions, bound validation/review/cancellation effects, knowledge and recovery; no external I/O
C2B6: application generation 2; terminal tip 0003; accept, repair, replan, terminal_reject, block, publication eligibility, latch, version/head recovery; no external I/O
```

Redelivery belongs in C2B5 because it creates a successor delivery under an
existing effect and depends on observation/disposition knowledge. Productive
redelivery is blocked by active stop; cancellation redelivery remains
risk-reducing and permitted.

Later source filenames and allowlists are implementation-planning records, not
public API or immutable semantic identity. Every later tranche must re-ground
its exact path set before mutation.

## 27. Explicit Nonimplementation

C2B0 creates no source module, SQL, schema object, migration, database row,
writer method, transaction, reader, observation ingest, decision runtime,
authority verifier, worker, process, capsule store, Git effect, direct-local
adapter, ES client, service, API, IPC, scheduler, queue, or publication
mechanism.

C2B0 adds no dependency, package-root export, public DTO, public `StateStore`
method, or public `WriterSession` method. It performs no Bridge or ES change and
makes no effect dispatch-eligible.
