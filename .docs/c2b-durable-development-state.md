# C2B Durable Development State

This document is the sole detailed owner of the accepted C2B durable
software-development state target. C2A remains authoritative for field-level
semantic records, identities, vectors, digests, and pure relations. C2A1
remains authoritative for the current pure Python value/API behavior. Existing
SQLite documents remain authoritative for current implemented backend,
security, writer, migration, and recovery mechanics.

## 1. Status, Classification, And Layering

Classification: `CURRENT IMPLEMENTED CONTRACT` for C2B1 migration
administration, C2B2 Slice 1 physical schema representability, and C2B2 Slice
2 pure private row/value behavior; `ACCEPTED TARGET CONTRACT` covers C2B2
private readers and later integration plus C2B3-C2B6 behavior below.

C2B0 was the historical documentation-and-direct-contract-test tranche. C2B1
implements the bounded administrative migration framework in the existing
Coordinator database. C2B2 Slice 1 implements migration 0002 and physical
representability for the frozen nineteen-table core. C2B2 Slice 2 implements
four pure private row/value modules without implementing a private reader,
mutation, replay, recovery, product runtime caller, or C2B3 behavior. External
effects and a C2B public API remain absent.

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

The current implemented application generation is 2. C2B1 migration mechanics
remain implemented, and C2B2 Slice 1 extends the packaged catalog and managed
database tip through `0002_development_program_and_effect_state` without
changing schema-0001 migration bytes or meanings. There are exactly two
production SQL migrations. The migration framework implements
exact-current ordinary open, explicit supported-prefix migration,
terminal-only compatibility, cumulative packaged-SQL schema authority,
whole-suffix single-transaction administration, and three-way migration
commit recovery. Migration 0002 implements the frozen physical core schema but
does not make its tables populated product truth or runtime authority.
Migration `0003_development_observation_and_progression_state` remains reserved;
the exact responsibilities and inventories are frozen below. No 0003 SQL,
C2B2 private reader, product writer, product mutation transaction, ingest or
progression recovery path, worker, process,
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
development_author_commands.effect_intent_ref: unique
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

C2B1 is the framework-only source/test reset that added no SQL or database
change. C2B2 Slice 1 now uses that framework at implemented application
generation 2 with current catalog and terminal tip
`0002_development_program_and_effect_state`. The framework privately
distinguishes absent, empty, current, supported older prefix, unsupported older,
newer unsupported, corrupt history, partial migration, and non-empty unmanaged
state while preserving the public absent/empty/managed/unknown classification.
Any selected destructive definition is rejected before common-lock acquisition,
writable open, `BEGIN IMMEDIATE`, or database mutation.

C2B2 Slice 1 advances the implemented application generation from 1 to 2,
adds migration 0002, and makes its catalog terminal tip 0002. C2B3 remains
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

The implemented literal migration is
`0002_development_program_and_effect_state`, with
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
C2B1: historical application generation 1 / terminal tip 0001 migration-framework reset; no SQL or schema change; no durable development state
C2B2: application generation advances to 2; terminal tip 0002; migration 0002; core records, base decision envelope, initialize-decision representation, and pure private row/value source; private readers remain later C2B2 work; no mutation API
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

## 28. C2B2 Field-Level Freeze Classification

This section and Sections 29–34 are the repository-owned C2B2 field-level
freeze. C2B2 Slice 1 implements its physical SQL representation and Slice 2
implements the row/value contract; private readers and later integration remain
accepted targets.

```text
CURRENT IMPLEMENTED CONTRACT: C2B2 Slice 1 migration administration and physical representation at generation 2 / tip 0002_development_program_and_effect_state plus Slice 2 pure private row/value source
ACCEPTED C2B2 FIELD-LEVEL TARGET CONTRACT: private readers and later integration over the migration-0002 core
LATER-TRANCHE TARGET CONTRACT: family-specific mutation, exact replay, recovery, and complete graph verification
ABSENT: C2B2 private readers, C2B mutations, exact replay, recovery, and C2B product runtime caller
```

The proposal supplied authoring evidence. It is not runtime input, an installed
migration, or repository contract authority. The structured literal below is
the sole detailed semantic owner for this freeze.

## 29. C2B2 Field-Level Structured Contract Ledger

The following closed JSON ledger freezes migration 0002's exact SQL core,
nineteen ordered table schemas, columns, declarations, logical types,
nullability, checks, keys, UNIQUE constraints, eighty-seven foreign keys and
their actions/deferrability, row schema and digest contracts, timestamps,
privacy, mutability, thirty immutable triggers, the sole explicit index, C2A
mapping, decisions, receipts, common graph primitive, and private readers.

<!-- C2B2_FIELD_LEVEL_CONTRACT_JSON_BEGIN -->

```json
{
  "c2a_persistence": {
    "cross_row_invariants": [
      {
        "aggregate_reader_enforcement": "The paged aggregate consumes all pages in one capability epoch and proves start=0, unit increments, no duplicates, and nonempty initial versions.",
        "authority_effect": "Integrity validation only; no execution or external authority is created.",
        "exact_pass_condition": "For one program/version aggregate with n members, sorted (membership_ordinal, work_item_ref) rows have ordinals exactly 0..n-1; an initial version has n>=1.",
        "future_mutation_preflight_enforcement": "Initialization and replan write plans precompute dense ordinals and reject duplicates or gaps before write.",
        "input_tables_and_fields": [
          "development_program_version_work_items.program_ref",
          "development_program_version_work_items.program_version_ref",
          "development_program_version_work_items.membership_ordinal",
          "development_program_version_work_items.work_item_ref"
        ],
        "invariant_id": "membership_ordinals_contiguous",
        "owning_tranche": "C2B2 reader contract; C2B3 initialization and C2B6 replan mutation preflight.",
        "privacy_effect": "Only safe refs, ordinals, and digests participate.",
        "private_adapter_enforcement": "Each row adapter validates exact scalar types and row digest.",
        "safe_failure": "database_integrity_failure for persisted gaps/duplicates/empty initial aggregate; domain rejection before write for an invalid proposed aggregate.",
        "sql_enforced_portion": "UNIQUE(program_ref, program_version_ref, membership_ordinal) rejects duplicate ordinals; SQL does not prove gaps or completeness."
      },
      {
        "aggregate_reader_enforcement": "Program/version/decision aggregates prove basis identity, exact arithmetic, and current-head correspondence.",
        "authority_effect": "Durable progression integrity only; not external standing authority.",
        "exact_pass_condition": "Genesis is version 1 with null basis; each version-advancing non-genesis decision binds the authoritative basis and resulting_program_version_number=basis_program_version_number+1; non-version-advancing decisions have no resulting version fields.",
        "future_mutation_preflight_enforcement": "Current head is read inside the transaction; preflight computes exactly the next version and CAS basis.",
        "input_tables_and_fields": [
          "development_program_heads.current_program_version_ref",
          "development_program_heads.current_program_version_number",
          "development_program_versions.program_version_number",
          "development_decisions.basis_program_version_ref",
          "development_decisions.basis_program_version_number",
          "development_decisions.resulting_program_version_ref",
          "development_decisions.resulting_program_version_number"
        ],
        "invariant_id": "version_number_advancement",
        "owning_tranche": "C2B2 reader contract; C2B3 genesis and C2B6 progression mutation preflight.",
        "privacy_effect": "No private payload participates.",
        "private_adapter_enforcement": "Adapters validate positive integers and ref/number group completeness.",
        "safe_failure": "program_head_conflict for stale caller expectation; database_integrity_failure for an impossible persisted graph.",
        "sql_enforced_portion": "Positive integer predicates, unique program/version number, and the closed decision nullability algebra; arithmetic across rows is not SQL-enforced."
      },
      {
        "aggregate_reader_enforcement": "Aggregate readers verify current record/head identity and reject incoherent revision evidence.",
        "authority_effect": "Conflict fencing only; no authorization issuance.",
        "exact_pass_condition": "Each mutable-head update compares the caller-bound expected revision and advances the stored head revision by exactly one; genesis program/work heads begin at revision 0.",
        "future_mutation_preflight_enforcement": "One CAS predicate and rowcount=1 are required for every mutable-head update.",
        "input_tables_and_fields": [
          "development_program_heads.head_revision",
          "development_work_item_heads.head_revision",
          "development_effect_heads.head_revision",
          "development_delivery_heads.head_revision",
          "development_decisions.expected_program_head_revision",
          "development_decisions.expected_target_effect_head_revision"
        ],
        "invariant_id": "head_revision_advancement",
        "owning_tranche": "C2B3/C2B5/C2B6 mutation runtime with C2B2 private-reader prerequisites.",
        "privacy_effect": "Counters only.",
        "private_adapter_enforcement": "Adapters require exact built-in nonnegative integers.",
        "safe_failure": "program_head_conflict or target_effect_state_conflict for stale expectations; database_integrity_failure for malformed persisted state.",
        "sql_enforced_portion": "Nonnegative integer checks only; exact CAS arithmetic belongs to the transaction mutation."
      },
      {
        "aggregate_reader_enforcement": "Reject any ref/digest mismatch before returning an aggregate or replay.",
        "authority_effect": "A valid digest proves identity only, never execution permission.",
        "exact_pass_condition": "Every digest paired with a reference equals the recomputed digest of the exact referenced canonical record; paired fields are both absent or both present where nullable.",
        "future_mutation_preflight_enforcement": "Write plans derive digests from canonical records and never accept caller-computed durable digests as authority.",
        "input_tables_and_fields": [
          "all persisted ref/digest pairs",
          "decision selected/target/originating ref-digest fields",
          "receipt graph record_ref/record_digest entries"
        ],
        "invariant_id": "ref_digest_equality",
        "owning_tranche": "C2B2 adapters/readers; later C2B mutation tranches.",
        "privacy_effect": "Digest validation does not reveal source bytes or secrets.",
        "private_adapter_enforcement": "Recompute every row, C2A, projection, nested-envelope, decision, and graph digest.",
        "safe_failure": "database_integrity_failure for persisted mismatch; domain rejection before write for incoherent proposed records.",
        "sql_enforced_portion": "Scalar digest predicates, nullable group CHECKs, and FKs for local refs; digest equality is not SQL-enforced."
      },
      {
        "aggregate_reader_enforcement": "Read the exact cancellation decision, cancellation intent/fence, target intent/fence, and capsule binding; prove the class-conditioned null/equality algebra before returning.",
        "authority_effect": "Binding evidence only; no effect authorization is minted.",
        "exact_pass_condition": "For cancel_effect targeting author_candidate, the cancellation effect intent portable_capsule_digest, cancellation effect fence portable_capsule_digest, decision target_capsule_manifest_ref, and decision target_portable_capsule_digest are all null. For cancel_effect targeting validate_candidate or review_candidate, the intent digest is non-null and equals both the target/cancellation fence portable digest and decision.target_portable_capsule_digest; the cancellation effect fence carries that same digest and its target-fence ref/digest identifies the exact target.",
        "future_mutation_preflight_enforcement": "Cancellation preflight rejects a missing, extra, stale, or mismatched capsule binding before any write.",
        "input_tables_and_fields": [
          "development_decisions.target_effect_class",
          "development_decisions.target_capsule_manifest_ref",
          "development_decisions.target_portable_capsule_digest",
          "development_decisions.target_effect_fence_ref",
          "development_effect_intents.effect_class",
          "development_effect_intents.cancellation_target_effect_intent_ref",
          "development_effect_intents.portable_capsule_digest",
          "development_effect_fences.effect_intent_ref",
          "development_effect_fences.portable_capsule_digest",
          "development_effect_fences.cancellation_target_effect_fence_ref",
          "development_effect_fences.cancellation_target_effect_fence_digest"
        ],
        "invariant_id": "cancellation_capsule_target_binding",
        "negative_cases": [
          "extra capsule on author target",
          "missing capsule on validation target",
          "missing capsule on review target",
          "sibling capsule digest",
          "arbitrary unrelated digest",
          "decision/intent/fence disagreement"
        ],
        "owning_tranche": "C2B2 reader contract; C2B5 cancellation mutation.",
        "privacy_effect": "Only safe capsule refs and portable digests persist; capsule bytes never persist in 0002.",
        "private_adapter_enforcement": "Reconstruct C2A values and invoke cancellation/effect coherence validation.",
        "safe_failure": "domain rejection before write; database_integrity_failure if persisted evidence is incoherent.",
        "sql_enforced_portion": "Closed decision and effect-fence nullable-group CHECKs; cross-row equality is not SQL-enforced."
      },
      {
        "aggregate_reader_enforcement": "Attempt/fence aggregates repeat reconstruction before return.",
        "authority_effect": "Effect ceiling representation only; the mask is not permission.",
        "exact_pass_condition": "The integer mask is 1..31, has no unknown bits, and reconstructs exactly the canonical C2A ordered unique effect-class list using bit order author_candidate,cancel_effect,local_git_commit,review_candidate,validate_candidate.",
        "future_mutation_preflight_enforcement": "Encode only a validated nonempty C2A closed list; reject duplicates, unknown classes, or noncanonical ordering.",
        "input_tables_and_fields": [
          "development_attempt_fences.allowed_effect_class_mask"
        ],
        "invariant_id": "c2a_effect_class_mask_reconstruction",
        "owning_tranche": "C2B2 C2A adapter/reader contract; C2B3 author establishment.",
        "privacy_effect": "Closed class bits only.",
        "private_adapter_enforcement": "Decode bits to the exact canonical list, reconstruct AttemptFenceV1, and verify its digest/coherence.",
        "safe_failure": "database_integrity_failure for malformed persisted mask; domain rejection before write for invalid proposal.",
        "sql_enforced_portion": "Exact integer storage and BETWEEN 1 AND 31."
      },
      {
        "aggregate_reader_enforcement": "Transaction aggregate reads and compares the authoritative singleton before returning a mutation context.",
        "authority_effect": "Preserves external stop authority; Coordinator cannot reinterpret or mint it.",
        "exact_pass_condition": "Every mutation binds the exact authoritative schema-0001 coding global-stop ref/version observed inside the same transaction; productive operations fail when stop is active and risk-reducing cancellation remains governed by its exact later contract.",
        "future_mutation_preflight_enforcement": "Fresh path binds the observed pair and applies the stop policy before write.",
        "input_tables_and_fields": [
          "development_decisions.coding_global_stop_ref",
          "development_decisions.coding_global_stop_version",
          "development_attempt_fences.global_stop_ref",
          "development_attempt_fences.global_stop_version",
          "development_effect_fences.global_stop_ref",
          "development_effect_fences.global_stop_version",
          "development_author_commands.global_stop_ref",
          "development_author_commands.global_stop_version",
          "schema-0001 global_stop_current"
        ],
        "invariant_id": "global_stop_binding",
        "owning_tranche": "C2B3/C2B5/C2B6 mutation transactions using existing schema-0001 global-stop authority.",
        "privacy_effect": "Safe ref and version only.",
        "private_adapter_enforcement": "Adapters validate ref/version shape without treating it as caller authority.",
        "safe_failure": "coding_global_stop_active or apply conflict for current state; database_integrity_failure for persisted mismatch.",
        "sql_enforced_portion": "Scalar/ref-version checks only; migration 0002 intentionally has no FK to the schema-0001 singleton."
      },
      {
        "aggregate_reader_enforcement": "After 0003 the observation resolver must prove exact-one complete result graph before replay.",
        "authority_effect": "Observation existence is knowledge evidence, not execution authorization.",
        "exact_pass_condition": "An observation-ingest receipt has exactly one result_observation_ref resolving to the complete migration-0003 observation graph; all other receipt families have it null.",
        "future_mutation_preflight_enforcement": "C2B5 observation ingest writes the result and receipt atomically under the shared transaction.",
        "input_tables_and_fields": [
          "development_mutation_receipts.result_observation_ref",
          "migration-0003 observation tables"
        ],
        "invariant_id": "observation_result_existence_after_0003",
        "owning_tranche": "C2B4 migration-0003 resolver contract and C2B5 observation ingest.",
        "privacy_effect": "The 0002 receipt contains only a safe observation ref and digests; source bytes remain excluded.",
        "private_adapter_enforcement": "The 0002 receipt adapter preserves the safe ref but does not claim existence before 0003.",
        "safe_failure": "database_integrity_failure for missing, duplicate, or incomplete persisted observation result.",
        "sql_enforced_portion": "The migration-0002 closed receipt union controls nullability; no 0002 FK targets future tables."
      }
    ],
    "delivery_wrapper_digest_contract": {
      "c2b_delivery_attempt_wrapper": {
        "basis_decision_treatment": "basis_decision_ref is required and participates in wrapper identity.",
        "database_column_for_literal_schema_id": null,
        "delivery_lineage_fields": [
          "delivery_kind",
          "delivery_number",
          "predecessor_delivery_attempt_ref"
        ],
        "digest_domain": "governed-execution.nwp-development-delivery-attempt.v1.identity",
        "identity_value_sources": {
          "basis_decision_ref": "persisted",
          "delivery_envelope_digest": "recomputed nested C2A digest",
          "delivery_kind": "persisted",
          "delivery_number": "persisted",
          "predecessor_delivery_attempt_ref": "persisted nullable lineage",
          "recorded_at": "persisted whole-second UTC",
          "schema_id": "literal governed-execution.nwp-development-delivery-attempt.v1"
        },
        "literal_schema_canonical_key": "schema_id",
        "literal_schema_derivation": "The adapter supplies the fixed wrapper schema literal; it is not caller input and adding a twentieth SQL column is neither necessary nor authorized.",
        "literal_wrapper_schema_id": "governed-execution.nwp-development-delivery-attempt.v1",
        "nested_delivery_envelope_digest_treatment": "Included as one exact digest identity input; nested envelope fields are not duplicated into the wrapper identity.",
        "operational_fields_excluded": [],
        "ordered_identity_keys": [
          "schema_id",
          "delivery_envelope_digest",
          "delivery_kind",
          "delivery_number",
          "predecessor_delivery_attempt_ref",
          "basis_decision_ref",
          "recorded_at"
        ],
        "recorded_at_participation": true,
        "self_digest_exclusion": "delivery_attempt_digest"
      },
      "counterfactuals": [
        "nested_delivery_envelope_substitution changes or invalidates delivery_envelope_digest",
        "wrapper_schema_substitution changes or invalidates delivery_attempt_digest"
      ],
      "nested_delivery_envelope": {
        "digest_domain": "governed-execution.nwp-delivery-envelope.v1.identity",
        "ordered_identity_keys": [
          "schema_id",
          "delivery_attempt_ref",
          "program_ref",
          "program_version_ref",
          "command_ref",
          "command_digest",
          "semantic_attempt_ref",
          "effect_intent_ref",
          "attempt_fence_ref",
          "attempt_fence_digest",
          "effect_fence_ref",
          "effect_fence_digest",
          "adapter_kind",
          "adapter_safe_correlation_ref"
        ],
        "schema_id": "governed-execution.nwp-delivery-envelope.v1",
        "self_digest_exclusion": "delivery_envelope_digest"
      }
    },
    "field_mapping_ledger": [
      {
        "c2a_field": "schema_id",
        "input_b_durable_column": "schema_id",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[schema_id]",
        "repaired_sql_column": "schema_id",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "attempt_fence_ref",
        "input_b_durable_column": "attempt_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[attempt_fence_ref]",
        "repaired_sql_column": "attempt_fence_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "parent_standing_grant_ref",
        "input_b_durable_column": "parent_standing_grant_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[parent_standing_grant_ref]",
        "repaired_sql_column": "parent_standing_grant_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "parent_standing_grant_digest",
        "input_b_durable_column": "parent_standing_grant_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[parent_standing_grant_digest]",
        "repaired_sql_column": "parent_standing_grant_digest",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "attempt_authorization_ref",
        "input_b_durable_column": "attempt_authorization_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[attempt_authorization_ref]",
        "repaired_sql_column": "attempt_authorization_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "attempt_authorization_digest",
        "input_b_durable_column": "attempt_authorization_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[attempt_authorization_digest]",
        "repaired_sql_column": "attempt_authorization_digest",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "program_ref",
        "input_b_durable_column": "program_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[program_ref]",
        "repaired_sql_column": "program_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "program_version_ref",
        "input_b_durable_column": "program_version_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[program_version_ref]",
        "repaired_sql_column": "program_version_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "accepted_intent_revision_ref",
        "input_b_durable_column": "accepted_intent_revision_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[accepted_intent_revision_ref]",
        "repaired_sql_column": "accepted_intent_revision_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "work_item_ref",
        "input_b_durable_column": "work_item_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[work_item_ref]",
        "repaired_sql_column": "work_item_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "work_item_revision_ref",
        "input_b_durable_column": "work_item_revision_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[work_item_revision_ref]",
        "repaired_sql_column": "work_item_revision_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "semantic_attempt_ref",
        "input_b_durable_column": "semantic_attempt_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[semantic_attempt_ref]",
        "repaired_sql_column": "semantic_attempt_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "repository_ref",
        "input_b_durable_column": "repository_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[repository_ref]",
        "repaired_sql_column": "repository_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "base_git_object_format",
        "input_b_durable_column": "base_git_object_format",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[base_git_object_format]",
        "repaired_sql_column": "base_git_object_format",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "base_git_oid",
        "input_b_durable_column": "base_git_oid",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[base_git_oid]",
        "repaired_sql_column": "base_git_oid",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "path_ceiling",
        "input_b_durable_column": "path_ceiling_json",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[path_ceiling_json]",
        "repaired_sql_column": "path_ceiling_json",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "allowed_effect_classes",
        "input_b_durable_column": "allowed_effect_class_mask",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[allowed_effect_class_mask]",
        "repaired_sql_column": "allowed_effect_class_mask",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_active_invocations",
        "input_b_durable_column": "aggregate_max_active_invocations",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_active_invocations]",
        "repaired_sql_column": "aggregate_max_active_invocations",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_candidate_bytes",
        "input_b_durable_column": "aggregate_max_candidate_bytes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_candidate_bytes]",
        "repaired_sql_column": "aggregate_max_candidate_bytes",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_changed_files",
        "input_b_durable_column": "aggregate_max_changed_files",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_changed_files]",
        "repaired_sql_column": "aggregate_max_changed_files",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_cost_microusd",
        "input_b_durable_column": "aggregate_max_cost_microusd",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_cost_microusd]",
        "repaired_sql_column": "aggregate_max_cost_microusd",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_cpu_seconds",
        "input_b_durable_column": "aggregate_max_cpu_seconds",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_cpu_seconds]",
        "repaired_sql_column": "aggregate_max_cpu_seconds",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_deliveries",
        "input_b_durable_column": "aggregate_max_deliveries",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_deliveries]",
        "repaired_sql_column": "aggregate_max_deliveries",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_deployments",
        "input_b_durable_column": "aggregate_max_deployments",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_deployments]",
        "repaired_sql_column": "aggregate_max_deployments",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_local_commits",
        "input_b_durable_column": "aggregate_max_local_commits",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_local_commits]",
        "repaired_sql_column": "aggregate_max_local_commits",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_memory_bytes",
        "input_b_durable_column": "aggregate_max_memory_bytes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_memory_bytes]",
        "repaired_sql_column": "aggregate_max_memory_bytes",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_merges",
        "input_b_durable_column": "aggregate_max_merges",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_merges]",
        "repaired_sql_column": "aggregate_max_merges",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_model_input_tokens",
        "input_b_durable_column": "aggregate_max_model_input_tokens",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_model_input_tokens]",
        "repaired_sql_column": "aggregate_max_model_input_tokens",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_model_output_tokens",
        "input_b_durable_column": "aggregate_max_model_output_tokens",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_model_output_tokens]",
        "repaired_sql_column": "aggregate_max_model_output_tokens",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_pull_requests",
        "input_b_durable_column": "aggregate_max_pull_requests",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_pull_requests]",
        "repaired_sql_column": "aggregate_max_pull_requests",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_pushes",
        "input_b_durable_column": "aggregate_max_pushes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_pushes]",
        "repaired_sql_column": "aggregate_max_pushes",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_wall_seconds",
        "input_b_durable_column": "aggregate_max_wall_seconds",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_wall_seconds]",
        "repaired_sql_column": "aggregate_max_wall_seconds",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "expires_at",
        "input_b_durable_column": "expires_at",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[expires_at]",
        "repaired_sql_column": "expires_at",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "global_stop_ref",
        "input_b_durable_column": "global_stop_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[global_stop_ref]",
        "repaired_sql_column": "global_stop_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "global_stop_version",
        "input_b_durable_column": "global_stop_version",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[global_stop_version]",
        "repaired_sql_column": "global_stop_version",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "attempt_fence_digest",
        "input_b_durable_column": "attempt_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[attempt_fence_digest]",
        "repaired_sql_column": "attempt_fence_digest",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "schema_id",
        "input_b_durable_column": "schema_id",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[schema_id]",
        "repaired_sql_column": "schema_id",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_fence_ref",
        "input_b_durable_column": "effect_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_fence_ref]",
        "repaired_sql_column": "effect_fence_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "parent_standing_grant_ref",
        "input_b_durable_column": "parent_standing_grant_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[parent_standing_grant_ref]",
        "repaired_sql_column": "parent_standing_grant_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "parent_standing_grant_digest",
        "input_b_durable_column": "parent_standing_grant_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[parent_standing_grant_digest]",
        "repaired_sql_column": "parent_standing_grant_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_authorization_ref",
        "input_b_durable_column": "effect_authorization_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_authorization_ref]",
        "repaired_sql_column": "effect_authorization_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_authorization_digest",
        "input_b_durable_column": "effect_authorization_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_authorization_digest]",
        "repaired_sql_column": "effect_authorization_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "attempt_fence_ref",
        "input_b_durable_column": "attempt_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[attempt_fence_ref]",
        "repaired_sql_column": "attempt_fence_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "attempt_fence_digest",
        "input_b_durable_column": "attempt_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[attempt_fence_digest]",
        "repaired_sql_column": "attempt_fence_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "program_ref",
        "input_b_durable_column": "program_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[program_ref]",
        "repaired_sql_column": "program_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "program_version_ref",
        "input_b_durable_column": "program_version_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[program_version_ref]",
        "repaired_sql_column": "program_version_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "accepted_intent_revision_ref",
        "input_b_durable_column": "accepted_intent_revision_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[accepted_intent_revision_ref]",
        "repaired_sql_column": "accepted_intent_revision_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "work_item_ref",
        "input_b_durable_column": "work_item_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[work_item_ref]",
        "repaired_sql_column": "work_item_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "work_item_revision_ref",
        "input_b_durable_column": "work_item_revision_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[work_item_revision_ref]",
        "repaired_sql_column": "work_item_revision_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "semantic_attempt_ref",
        "input_b_durable_column": "semantic_attempt_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[semantic_attempt_ref]",
        "repaired_sql_column": "semantic_attempt_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_intent_ref",
        "input_b_durable_column": "effect_intent_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_intent_ref]",
        "repaired_sql_column": "effect_intent_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_class",
        "input_b_durable_column": "effect_class",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_class]",
        "repaired_sql_column": "effect_class",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "command_ref",
        "input_b_durable_column": "command_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[command_ref]",
        "repaired_sql_column": "command_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "command_digest",
        "input_b_durable_column": "command_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[command_digest]",
        "repaired_sql_column": "command_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "candidate_ref",
        "input_b_durable_column": "candidate_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[candidate_ref]",
        "repaired_sql_column": "candidate_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "repository_ref",
        "input_b_durable_column": "repository_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[repository_ref]",
        "repaired_sql_column": "repository_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "base_git_object_format",
        "input_b_durable_column": "base_git_object_format",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[base_git_object_format]",
        "repaired_sql_column": "base_git_object_format",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "base_git_oid",
        "input_b_durable_column": "base_git_oid",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[base_git_oid]",
        "repaired_sql_column": "base_git_oid",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "path_ceiling",
        "input_b_durable_column": "path_ceiling_json",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[path_ceiling_json]",
        "repaired_sql_column": "path_ceiling_json",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_active_invocations",
        "input_b_durable_column": "effect_max_active_invocations",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_active_invocations]",
        "repaired_sql_column": "effect_max_active_invocations",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_candidate_bytes",
        "input_b_durable_column": "effect_max_candidate_bytes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_candidate_bytes]",
        "repaired_sql_column": "effect_max_candidate_bytes",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_changed_files",
        "input_b_durable_column": "effect_max_changed_files",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_changed_files]",
        "repaired_sql_column": "effect_max_changed_files",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_cost_microusd",
        "input_b_durable_column": "effect_max_cost_microusd",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_cost_microusd]",
        "repaired_sql_column": "effect_max_cost_microusd",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_cpu_seconds",
        "input_b_durable_column": "effect_max_cpu_seconds",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_cpu_seconds]",
        "repaired_sql_column": "effect_max_cpu_seconds",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_deliveries",
        "input_b_durable_column": "effect_max_deliveries",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_deliveries]",
        "repaired_sql_column": "effect_max_deliveries",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_deployments",
        "input_b_durable_column": "effect_max_deployments",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_deployments]",
        "repaired_sql_column": "effect_max_deployments",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_local_commits",
        "input_b_durable_column": "effect_max_local_commits",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_local_commits]",
        "repaired_sql_column": "effect_max_local_commits",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_memory_bytes",
        "input_b_durable_column": "effect_max_memory_bytes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_memory_bytes]",
        "repaired_sql_column": "effect_max_memory_bytes",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_merges",
        "input_b_durable_column": "effect_max_merges",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_merges]",
        "repaired_sql_column": "effect_max_merges",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_model_input_tokens",
        "input_b_durable_column": "effect_max_model_input_tokens",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_model_input_tokens]",
        "repaired_sql_column": "effect_max_model_input_tokens",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_model_output_tokens",
        "input_b_durable_column": "effect_max_model_output_tokens",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_model_output_tokens]",
        "repaired_sql_column": "effect_max_model_output_tokens",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_pull_requests",
        "input_b_durable_column": "effect_max_pull_requests",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_pull_requests]",
        "repaired_sql_column": "effect_max_pull_requests",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_pushes",
        "input_b_durable_column": "effect_max_pushes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_pushes]",
        "repaired_sql_column": "effect_max_pushes",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_wall_seconds",
        "input_b_durable_column": "effect_max_wall_seconds",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_wall_seconds]",
        "repaired_sql_column": "effect_max_wall_seconds",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "expires_at",
        "input_b_durable_column": "expires_at",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[expires_at]",
        "repaired_sql_column": "expires_at",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "global_stop_ref",
        "input_b_durable_column": "global_stop_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[global_stop_ref]",
        "repaired_sql_column": "global_stop_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "global_stop_version",
        "input_b_durable_column": "global_stop_version",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[global_stop_version]",
        "repaired_sql_column": "global_stop_version",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "portable_capsule_digest",
        "input_b_durable_column": "portable_capsule_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[portable_capsule_digest]",
        "repaired_sql_column": "portable_capsule_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "cancellation_target_effect_intent_ref",
        "input_b_durable_column": "cancellation_target_effect_intent_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[cancellation_target_effect_intent_ref]",
        "repaired_sql_column": "cancellation_target_effect_intent_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "cancellation_target_effect_fence_ref",
        "input_b_durable_column": "cancellation_target_effect_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[cancellation_target_effect_fence_ref]",
        "repaired_sql_column": "cancellation_target_effect_fence_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "cancellation_target_effect_fence_digest",
        "input_b_durable_column": "cancellation_target_effect_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[cancellation_target_effect_fence_digest]",
        "repaired_sql_column": "cancellation_target_effect_fence_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_fence_digest",
        "input_b_durable_column": "effect_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_fence_digest]",
        "repaired_sql_column": "effect_fence_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "schema_id",
        "input_b_durable_column": "schema_id",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[schema_id]",
        "repaired_sql_column": "schema_id",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "command_ref",
        "input_b_durable_column": "command_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[command_ref]",
        "repaired_sql_column": "command_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "program_ref",
        "input_b_durable_column": "program_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[program_ref]",
        "repaired_sql_column": "program_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "program_version_ref",
        "input_b_durable_column": "program_version_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[program_version_ref]",
        "repaired_sql_column": "program_version_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "accepted_intent_revision_ref",
        "input_b_durable_column": "accepted_intent_revision_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[accepted_intent_revision_ref]",
        "repaired_sql_column": "accepted_intent_revision_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "work_item_ref",
        "input_b_durable_column": "work_item_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[work_item_ref]",
        "repaired_sql_column": "work_item_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "work_item_revision_ref",
        "input_b_durable_column": "work_item_revision_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[work_item_revision_ref]",
        "repaired_sql_column": "work_item_revision_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "semantic_attempt_ref",
        "input_b_durable_column": "semantic_attempt_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[semantic_attempt_ref]",
        "repaired_sql_column": "semantic_attempt_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_intent_ref",
        "input_b_durable_column": "effect_intent_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_intent_ref]",
        "repaired_sql_column": "effect_intent_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_class",
        "input_b_durable_column": "effect_class",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_class]",
        "repaired_sql_column": "effect_class",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "candidate_ref",
        "input_b_durable_column": "candidate_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[candidate_ref]",
        "repaired_sql_column": "candidate_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "repository_ref",
        "input_b_durable_column": "repository_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[repository_ref]",
        "repaired_sql_column": "repository_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "base_git_object_format",
        "input_b_durable_column": "base_git_object_format",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[base_git_object_format]",
        "repaired_sql_column": "base_git_object_format",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "base_git_oid",
        "input_b_durable_column": "base_git_oid",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[base_git_oid]",
        "repaired_sql_column": "base_git_oid",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "path_ceiling",
        "input_b_durable_column": "path_ceiling_json",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[path_ceiling_json]",
        "repaired_sql_column": "path_ceiling_json",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "work_spec_ref",
        "input_b_durable_column": "work_spec_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[work_spec_ref]",
        "repaired_sql_column": "work_spec_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "work_spec_digest",
        "input_b_durable_column": "work_spec_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[work_spec_digest]",
        "repaired_sql_column": "work_spec_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "standing_grant_ref",
        "input_b_durable_column": "standing_grant_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[standing_grant_ref]",
        "repaired_sql_column": "standing_grant_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "standing_grant_digest",
        "input_b_durable_column": "standing_grant_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[standing_grant_digest]",
        "repaired_sql_column": "standing_grant_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "attempt_authorization_ref",
        "input_b_durable_column": "attempt_authorization_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[attempt_authorization_ref]",
        "repaired_sql_column": "attempt_authorization_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "attempt_authorization_digest",
        "input_b_durable_column": "attempt_authorization_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[attempt_authorization_digest]",
        "repaired_sql_column": "attempt_authorization_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_authorization_ref",
        "input_b_durable_column": "effect_authorization_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_authorization_ref]",
        "repaired_sql_column": "effect_authorization_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_authorization_digest",
        "input_b_durable_column": "effect_authorization_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_authorization_digest]",
        "repaired_sql_column": "effect_authorization_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "attempt_fence_ref",
        "input_b_durable_column": "attempt_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[attempt_fence_ref]",
        "repaired_sql_column": "attempt_fence_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "attempt_fence_digest",
        "input_b_durable_column": "attempt_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[attempt_fence_digest]",
        "repaired_sql_column": "attempt_fence_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_fence_ref",
        "input_b_durable_column": "effect_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_fence_ref]",
        "repaired_sql_column": "effect_fence_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_fence_digest",
        "input_b_durable_column": "effect_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_fence_digest]",
        "repaired_sql_column": "effect_fence_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "global_stop_ref",
        "input_b_durable_column": "global_stop_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[global_stop_ref]",
        "repaired_sql_column": "global_stop_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "global_stop_version",
        "input_b_durable_column": "global_stop_version",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[global_stop_version]",
        "repaired_sql_column": "global_stop_version",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "validation_requirement_ref",
        "input_b_durable_column": "validation_requirement_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[validation_requirement_ref]",
        "repaired_sql_column": "validation_requirement_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "validation_requirement_digest",
        "input_b_durable_column": "validation_requirement_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[validation_requirement_digest]",
        "repaired_sql_column": "validation_requirement_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "review_requirement_ref",
        "input_b_durable_column": "review_requirement_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[review_requirement_ref]",
        "repaired_sql_column": "review_requirement_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "review_requirement_digest",
        "input_b_durable_column": "review_requirement_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[review_requirement_digest]",
        "repaired_sql_column": "review_requirement_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "capsule_schema_id",
        "input_b_durable_column": "capsule_schema_id",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[capsule_schema_id]",
        "repaired_sql_column": "capsule_schema_id",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "capsule_profile_ref",
        "input_b_durable_column": "capsule_profile_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[capsule_profile_ref]",
        "repaired_sql_column": "capsule_profile_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_active_invocations",
        "input_b_durable_column": "effect_max_active_invocations",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_active_invocations]",
        "repaired_sql_column": "effect_max_active_invocations",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_candidate_bytes",
        "input_b_durable_column": "effect_max_candidate_bytes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_candidate_bytes]",
        "repaired_sql_column": "effect_max_candidate_bytes",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_changed_files",
        "input_b_durable_column": "effect_max_changed_files",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_changed_files]",
        "repaired_sql_column": "effect_max_changed_files",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_cost_microusd",
        "input_b_durable_column": "effect_max_cost_microusd",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_cost_microusd]",
        "repaired_sql_column": "effect_max_cost_microusd",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_cpu_seconds",
        "input_b_durable_column": "effect_max_cpu_seconds",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_cpu_seconds]",
        "repaired_sql_column": "effect_max_cpu_seconds",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_deliveries",
        "input_b_durable_column": "effect_max_deliveries",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_deliveries]",
        "repaired_sql_column": "effect_max_deliveries",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_deployments",
        "input_b_durable_column": "effect_max_deployments",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_deployments]",
        "repaired_sql_column": "effect_max_deployments",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_local_commits",
        "input_b_durable_column": "effect_max_local_commits",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_local_commits]",
        "repaired_sql_column": "effect_max_local_commits",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_memory_bytes",
        "input_b_durable_column": "effect_max_memory_bytes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_memory_bytes]",
        "repaired_sql_column": "effect_max_memory_bytes",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_merges",
        "input_b_durable_column": "effect_max_merges",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_merges]",
        "repaired_sql_column": "effect_max_merges",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_model_input_tokens",
        "input_b_durable_column": "effect_max_model_input_tokens",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_model_input_tokens]",
        "repaired_sql_column": "effect_max_model_input_tokens",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_model_output_tokens",
        "input_b_durable_column": "effect_max_model_output_tokens",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_model_output_tokens]",
        "repaired_sql_column": "effect_max_model_output_tokens",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_pull_requests",
        "input_b_durable_column": "effect_max_pull_requests",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_pull_requests]",
        "repaired_sql_column": "effect_max_pull_requests",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_pushes",
        "input_b_durable_column": "effect_max_pushes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_pushes]",
        "repaired_sql_column": "effect_max_pushes",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_wall_seconds",
        "input_b_durable_column": "effect_max_wall_seconds",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_wall_seconds]",
        "repaired_sql_column": "effect_max_wall_seconds",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "privacy_classification",
        "input_b_durable_column": "privacy_classification",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[privacy_classification]",
        "repaired_sql_column": "privacy_classification",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "redaction_profile_ref",
        "input_b_durable_column": "redaction_profile_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[redaction_profile_ref]",
        "repaired_sql_column": "redaction_profile_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "command_digest",
        "input_b_durable_column": "command_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[command_digest]",
        "repaired_sql_column": "command_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "schema_id",
        "input_b_durable_column": "schema_id",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[schema_id]",
        "repaired_sql_column": "schema_id",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "delivery_attempt_ref",
        "input_b_durable_column": "delivery_attempt_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[delivery_attempt_ref]",
        "repaired_sql_column": "delivery_attempt_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "program_ref",
        "input_b_durable_column": "program_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[program_ref]",
        "repaired_sql_column": "program_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "program_version_ref",
        "input_b_durable_column": "program_version_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[program_version_ref]",
        "repaired_sql_column": "program_version_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "command_ref",
        "input_b_durable_column": "command_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[command_ref]",
        "repaired_sql_column": "command_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "command_digest",
        "input_b_durable_column": "command_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[command_digest]",
        "repaired_sql_column": "command_digest",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "semantic_attempt_ref",
        "input_b_durable_column": "semantic_attempt_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[semantic_attempt_ref]",
        "repaired_sql_column": "semantic_attempt_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "effect_intent_ref",
        "input_b_durable_column": "effect_intent_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[effect_intent_ref]",
        "repaired_sql_column": "effect_intent_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "attempt_fence_ref",
        "input_b_durable_column": "attempt_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[attempt_fence_ref]",
        "repaired_sql_column": "attempt_fence_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "attempt_fence_digest",
        "input_b_durable_column": "attempt_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[attempt_fence_digest]",
        "repaired_sql_column": "attempt_fence_digest",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "effect_fence_ref",
        "input_b_durable_column": "effect_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[effect_fence_ref]",
        "repaired_sql_column": "effect_fence_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "effect_fence_digest",
        "input_b_durable_column": "effect_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[effect_fence_digest]",
        "repaired_sql_column": "effect_fence_digest",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "adapter_kind",
        "input_b_durable_column": "adapter_kind",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[adapter_kind]",
        "repaired_sql_column": "adapter_kind",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "adapter_safe_correlation_ref",
        "input_b_durable_column": "adapter_safe_correlation_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[adapter_safe_correlation_ref]",
        "repaired_sql_column": "adapter_safe_correlation_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "delivery_envelope_digest",
        "input_b_durable_column": "delivery_envelope_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[delivery_envelope_digest]",
        "repaired_sql_column": "delivery_envelope_digest",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      }
    ],
    "summary_mappings": {
      "AttemptFenceV1": {
        "allowed_effect_classes_encoding": {
          "bit_order": [
            "author_candidate",
            "cancel_effect",
            "local_git_commit",
            "review_candidate",
            "validate_candidate"
          ],
          "column": "allowed_effect_class_mask",
          "valid_mask_range": [
            1,
            31
          ]
        },
        "operational_fields_excluded": [
          "recorded_at"
        ],
        "path_ceiling_encoding": {
          "canonical_value": [
            ".docs/system_overview/hybrid_integration_architecture_adr.md",
            "PLANS.md",
            "docs_contract_test.go"
          ],
          "column": "path_ceiling_json"
        },
        "table": "development_attempt_fences"
      },
      "CandidateCapsuleManifestV1": "migration_0003_safe_evidence_binding_only",
      "CapsuleEntryV1": "never_persisted",
      "CeilingsV1": {
        "fields": [
          "max_active_invocations",
          "max_candidate_bytes",
          "max_changed_files",
          "max_cost_microusd",
          "max_cpu_seconds",
          "max_deliveries",
          "max_deployments",
          "max_local_commits",
          "max_memory_bytes",
          "max_merges",
          "max_model_input_tokens",
          "max_model_output_tokens",
          "max_pull_requests",
          "max_pushes",
          "max_wall_seconds"
        ],
        "mapping": "flattened"
      },
      "DeliveryEnvelopeV1": {
        "nested_envelope_digest": "delivery_envelope_digest",
        "table": "development_delivery_attempts",
        "wrapper_digest": "delivery_attempt_digest"
      },
      "EffectFenceV1": {
        "operational_fields_excluded": [
          "recorded_at"
        ],
        "path_ceiling_encoding": {
          "canonical_value": [
            ".docs/system_overview/hybrid_integration_architecture_adr.md",
            "PLANS.md",
            "docs_contract_test.go"
          ],
          "column": "path_ceiling_json"
        },
        "table": "development_effect_fences"
      },
      "WorkerCommandV1": {
        "identity_excludes": [
          "effect_fence_digest",
          "command_digest",
          "recorded_at"
        ],
        "path_ceiling_encoding": {
          "canonical_value": [
            ".docs/system_overview/hybrid_integration_architecture_adr.md",
            "PLANS.md",
            "docs_contract_test.go"
          ],
          "column": "path_ceiling_json"
        },
        "table": "development_author_commands"
      },
      "WorkerObservationV1": "migration_0003_only"
    }
  },
  "classification": {
    "absent": [
      "C2B2 private readers",
      "C2B mutations and exact replay or recovery",
      "C2B product runtime caller"
    ],
    "accepted_c2b2_field_level_target_contract": "private readers and later integration over the migration-0002 core",
    "current_implemented_contract": "C2B2 Slice 1 migration administration and physical representation at application generation 2 and terminal tip 0002_development_program_and_effect_state plus Slice 2 pure private row/value source",
    "later_tranche_target_contract": "family-specific mutation, exact replay, recovery, and complete graph verification"
  },
  "common_graph_digest_primitive": {
    "array_order_significant": true,
    "closed_envelope": true,
    "closed_graph_entry": true,
    "domain": "governed-execution.nwp-development-mutation-receipt.v1.identity",
    "domain_separator_hex": "00",
    "duplicate_role_ordinal": "reject",
    "duplicate_role_record_ref": "reject",
    "encoding": "compact_sorted_key_utf8_json",
    "formula": "SHA-256(UTF8(domain) || 0x00 || compact sorted-key UTF-8 JSON(identity))",
    "graph_entry_ordered_keys": [
      "role",
      "ordinal",
      "record_ref",
      "record_digest"
    ],
    "identity_additional_field": "graph_entries",
    "identity_envelope_fields": [
      "schema_id",
      "mutation_ref",
      "mutation_family",
      "command_schema_id",
      "command_digest",
      "program_ref",
      "decision_ref",
      "result_program_version_ref",
      "result_semantic_attempt_ref",
      "result_effect_intent_ref",
      "result_effect_fence_ref",
      "result_delivery_attempt_ref",
      "result_observation_ref",
      "result_decision_ref",
      "result_class",
      "result_projection_digest",
      "outcome",
      "committed_at"
    ],
    "role_string_owner": "owning_family_contract",
    "same_record_ref_in_distinct_roles": "permitted",
    "self_digest_exclusion": "mutation_graph_digest"
  },
  "contract_id": "governed-execution.coordinator.c2b2-field-level-contract-freeze.v1",
  "decision_envelope": {
    "column_count": 43,
    "decision_kinds": [
      "initialize",
      "accept",
      "repair",
      "replan",
      "terminal_reject",
      "block",
      "redeliver",
      "cancel"
    ],
    "decision_variants": [
      "program_genesis",
      "candidate_acceptance",
      "candidate_repair",
      "program_replan",
      "attempt_selecting_replan",
      "program_terminal_reject",
      "program_block",
      "productive_redelivery",
      "cancellation_redelivery",
      "effect_cancellation"
    ],
    "digest_contract": {
      "domain": "governed-execution.nwp-development-decision.v1.identity",
      "identity_fields": [
        "schema_id",
        "mutation_ref",
        "decision_ref",
        "program_ref",
        "decision_kind",
        "decision_variant",
        "basis_decision_ref",
        "basis_program_version_ref",
        "basis_program_version_number",
        "expected_program_head_revision",
        "resulting_program_version_ref",
        "resulting_program_version_number",
        "selected_semantic_attempt_ref",
        "selected_candidate_ref",
        "selected_attempt_fence_ref",
        "selected_attempt_fence_digest",
        "target_effect_intent_ref",
        "target_effect_class",
        "target_effect_fence_ref",
        "target_effect_fence_digest",
        "expected_target_effect_head_revision",
        "target_delivery_attempt_ref",
        "originating_command_ref",
        "originating_command_digest",
        "target_capsule_manifest_ref",
        "target_portable_capsule_digest",
        "coding_global_stop_ref",
        "coding_global_stop_version",
        "source_directive_ref",
        "source_directive_digest",
        "source_evidence_ref",
        "source_evidence_digest",
        "preassigned_semantic_attempt_ref",
        "preassigned_candidate_ref",
        "preassigned_effect_intent_ref",
        "preassigned_effect_fence_ref",
        "preassigned_delivery_attempt_ref",
        "resulting_accepted_intent_revision_ref",
        "resulting_work_item_ref",
        "resulting_work_item_revision_ref",
        "reason_code",
        "decided_at"
      ],
      "schema_id": "governed-execution.nwp-development-decision.v1",
      "self_digest_excluded": true,
      "timestamp_included": true
    },
    "mutation_implemented": false,
    "non_version_advancing_kinds": [
      "redeliver",
      "cancel"
    ],
    "ordered_columns": [
      "schema_id",
      "mutation_ref",
      "decision_ref",
      "program_ref",
      "decision_kind",
      "decision_variant",
      "basis_decision_ref",
      "basis_program_version_ref",
      "basis_program_version_number",
      "expected_program_head_revision",
      "resulting_program_version_ref",
      "resulting_program_version_number",
      "selected_semantic_attempt_ref",
      "selected_candidate_ref",
      "selected_attempt_fence_ref",
      "selected_attempt_fence_digest",
      "target_effect_intent_ref",
      "target_effect_class",
      "target_effect_fence_ref",
      "target_effect_fence_digest",
      "expected_target_effect_head_revision",
      "target_delivery_attempt_ref",
      "originating_command_ref",
      "originating_command_digest",
      "target_capsule_manifest_ref",
      "target_portable_capsule_digest",
      "coding_global_stop_ref",
      "coding_global_stop_version",
      "source_directive_ref",
      "source_directive_digest",
      "source_evidence_ref",
      "source_evidence_digest",
      "preassigned_semantic_attempt_ref",
      "preassigned_candidate_ref",
      "preassigned_effect_intent_ref",
      "preassigned_effect_fence_ref",
      "preassigned_delivery_attempt_ref",
      "resulting_accepted_intent_revision_ref",
      "resulting_work_item_ref",
      "resulting_work_item_revision_ref",
      "reason_code",
      "decided_at",
      "decision_digest"
    ],
    "representation_owner": "C2B2",
    "variant_matrix": [
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_initialize_development_program",
        "kind": "initialize",
        "required_groups": [
          "result_version",
          "preassigned_attempt"
        ],
        "required_non_null_fields": [
          "preassigned_candidate_ref",
          "preassigned_semantic_attempt_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref"
        ],
        "required_null_groups": [
          "basis",
          "selection",
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_effect",
          "preassigned_delivery",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='initialize' AND decision_variant='program_genesis' AND basis_decision_ref IS NULL AND basis_program_version_ref IS NULL AND basis_program_version_number IS NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND resulting_program_version_number=1 AND expected_program_head_revision=0)",
        "variant": "program_genesis",
        "version_advancing": true
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "accept",
        "required_groups": [
          "basis",
          "result_version",
          "selection"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref",
          "selected_semantic_attempt_ref"
        ],
        "required_null_groups": [
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_attempt",
          "preassigned_effect",
          "preassigned_delivery",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='accept' AND decision_variant='candidate_acceptance' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL)",
        "variant": "candidate_acceptance",
        "version_advancing": true
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "repair",
        "required_groups": [
          "basis",
          "result_version",
          "selection",
          "preassigned_attempt"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "preassigned_candidate_ref",
          "preassigned_semantic_attempt_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref",
          "selected_semantic_attempt_ref"
        ],
        "required_null_groups": [
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_effect",
          "preassigned_delivery",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='repair' AND decision_variant='candidate_repair' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL)",
        "variant": "candidate_repair",
        "version_advancing": true
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "replan",
        "required_groups": [
          "basis",
          "result_version",
          "result_intent"
        ],
        "required_non_null_fields": [
          "basis_decision_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "resulting_accepted_intent_revision_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref"
        ],
        "required_null_groups": [
          "selection",
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_attempt",
          "preassigned_effect",
          "preassigned_delivery",
          "result_work"
        ],
        "sql_branch": "(decision_kind='replan' AND decision_variant='program_replan' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NOT NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL)",
        "variant": "program_replan",
        "version_advancing": true
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "replan",
        "required_groups": [
          "basis",
          "result_version",
          "selection",
          "preassigned_attempt",
          "result_intent",
          "result_work"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "preassigned_candidate_ref",
          "preassigned_semantic_attempt_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "resulting_accepted_intent_revision_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref",
          "resulting_work_item_ref",
          "resulting_work_item_revision_ref",
          "selected_semantic_attempt_ref"
        ],
        "required_null_groups": [
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_effect",
          "preassigned_delivery"
        ],
        "sql_branch": "(decision_kind='replan' AND decision_variant='attempt_selecting_replan' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NOT NULL AND resulting_work_item_ref IS NOT NULL AND resulting_work_item_revision_ref IS NOT NULL)",
        "variant": "attempt_selecting_replan",
        "version_advancing": true
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "terminal_reject",
        "required_groups": [
          "basis",
          "result_version",
          "selection"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref",
          "selected_semantic_attempt_ref"
        ],
        "required_null_groups": [
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_attempt",
          "preassigned_effect",
          "preassigned_delivery",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='terminal_reject' AND decision_variant='program_terminal_reject' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL)",
        "variant": "program_terminal_reject",
        "version_advancing": true
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "block",
        "required_groups": [
          "basis",
          "result_version"
        ],
        "required_non_null_fields": [
          "basis_decision_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref"
        ],
        "required_null_groups": [
          "selection",
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_attempt",
          "preassigned_effect",
          "preassigned_delivery",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='block' AND decision_variant='program_block' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL)",
        "variant": "program_block",
        "version_advancing": true
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "redeliver",
        "required_groups": [
          "basis",
          "selection",
          "target_effect",
          "target_delivery",
          "originating_command",
          "preassigned_delivery"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "expected_target_effect_head_revision",
          "originating_command_digest",
          "originating_command_ref",
          "preassigned_delivery_attempt_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "selected_semantic_attempt_ref",
          "target_delivery_attempt_ref",
          "target_effect_class",
          "target_effect_fence_digest",
          "target_effect_fence_ref",
          "target_effect_intent_ref"
        ],
        "required_null_groups": [
          "result_version",
          "capsule",
          "source",
          "preassigned_attempt",
          "preassigned_effect",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='redeliver' AND decision_variant='productive_redelivery' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NOT NULL AND originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND target_effect_class IN ('author_candidate','validate_candidate','review_candidate'))",
        "variant": "productive_redelivery",
        "version_advancing": false
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "redeliver",
        "required_groups": [
          "basis",
          "selection",
          "target_effect",
          "target_delivery",
          "originating_command",
          "preassigned_delivery"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "expected_target_effect_head_revision",
          "originating_command_digest",
          "originating_command_ref",
          "preassigned_delivery_attempt_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "selected_semantic_attempt_ref",
          "target_delivery_attempt_ref",
          "target_effect_class",
          "target_effect_fence_digest",
          "target_effect_fence_ref",
          "target_effect_intent_ref"
        ],
        "required_null_groups": [
          "result_version",
          "capsule",
          "source",
          "preassigned_attempt",
          "preassigned_effect",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='redeliver' AND decision_variant='cancellation_redelivery' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NOT NULL AND originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND target_effect_class='cancel_effect')",
        "variant": "cancellation_redelivery",
        "version_advancing": false
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "cancel",
        "required_groups": [
          "basis",
          "selection",
          "target_effect",
          "originating_command",
          "source",
          "preassigned_effect",
          "preassigned_delivery"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "expected_target_effect_head_revision",
          "originating_command_digest",
          "originating_command_ref",
          "preassigned_delivery_attempt_ref",
          "preassigned_effect_fence_ref",
          "preassigned_effect_intent_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "selected_semantic_attempt_ref",
          "source_directive_digest",
          "source_directive_ref",
          "source_evidence_digest",
          "source_evidence_ref",
          "target_effect_class",
          "target_effect_fence_digest",
          "target_effect_fence_ref",
          "target_effect_intent_ref"
        ],
        "required_null_groups": [
          "result_version",
          "target_delivery",
          "preassigned_attempt",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='cancel' AND decision_variant='effect_cancellation' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND ((target_effect_class='author_candidate' AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL) OR (target_effect_class IN ('validate_candidate','review_candidate') AND target_capsule_manifest_ref IS NOT NULL AND target_portable_capsule_digest IS NOT NULL)) AND source_directive_ref IS NOT NULL AND source_directive_digest IS NOT NULL AND source_evidence_ref IS NOT NULL AND source_evidence_digest IS NOT NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NOT NULL AND preassigned_effect_fence_ref IS NOT NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND target_effect_class IN ('author_candidate','validate_candidate','review_candidate'))",
        "variant": "effect_cancellation",
        "version_advancing": false
      }
    ],
    "version_advancing_kinds": [
      "initialize",
      "accept",
      "repair",
      "replan",
      "terminal_reject",
      "block"
    ]
  },
  "explicit_indexes": [
    {
      "columns": [
        "command_ref"
      ],
      "name": "uq_development_effect_intents_author_command",
      "sql": "CREATE UNIQUE INDEX uq_development_effect_intents_author_command\nON development_effect_intents(command_ref)\nWHERE effect_class = 'author_candidate';",
      "table": "development_effect_intents",
      "where": "effect_class = 'author_candidate'"
    }
  ],
  "family_replay_boundary": {
    "c2b2_does_not_freeze_or_implement": [
      "complete mutation-family replay graphs",
      "complete family graph verifier",
      "historical mutable-head replay",
      "family graph locators",
      "mutation",
      "recovery"
    ],
    "ownership": {
      "C2B3": [
        "initialize graph/replay",
        "author-effect graph/replay"
      ],
      "C2B4": [
        "migration-0003 row contracts/readers only"
      ],
      "C2B5": [
        "observation ingest graph/replay",
        "bound validation/review/cancellation effect graph/replay",
        "cancel graph/replay",
        "redeliver graph/replay"
      ],
      "C2B6": [
        "accept graph/replay",
        "repair graph/replay",
        "replan graph/replay",
        "terminal_reject graph/replay",
        "block graph/replay",
        "eligibility/latch/version/head replay"
      ]
    },
    "proposal_replay_material_classification": "reviewed later-tranche proposal evidence; not current C2B2 contract authority",
    "required_before_first_family_writer": [
      "closed role inventory",
      "role ranks",
      "ordinal sources",
      "record-ref derivations",
      "graph member locators",
      "historical mutable-head postimages",
      "family golden vectors",
      "complete exact replay",
      "commit-outcome recovery"
    ]
  },
  "foreign_keys": [
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "current_program_version_ref"
      ],
      "child_table": "development_program_heads",
      "deferrability": "DEFERRABLE INITIALLY DEFERRED",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "program_head_current_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_program_versions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "program_version_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_program_versions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "program_version_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "creating_decision_ref"
      ],
      "child_table": "development_program_versions",
      "deferrability": "DEFERRABLE INITIALLY DEFERRED",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "program_version_creating_decision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_accepted_intent_revisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "accepted_intent_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "prior_accepted_intent_revision_ref"
      ],
      "child_table": "development_accepted_intent_revisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "accepted_intent_prior_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_work_item_heads",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "work_item_head_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "current_work_item_revision_ref"
      ],
      "child_table": "development_work_item_heads",
      "deferrability": "DEFERRABLE INITIALLY DEFERRED",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "work_item_head_current_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref"
      ],
      "child_table": "development_work_item_revisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref"
      ],
      "parent_table": "development_work_item_heads",
      "role": "work_item_revision_head"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "prior_work_item_revision_ref"
      ],
      "child_table": "development_work_item_revisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "work_item_revision_prior"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_work_item_revisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "work_item_revision_accepted_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_program_version_work_items",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "membership_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "child_table": "development_program_version_work_items",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "membership_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_revision_edges",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "revision_edge_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "from_accepted_intent_revision_ref"
      ],
      "child_table": "development_revision_edges",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "revision_edge_from_accepted_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "to_accepted_intent_revision_ref"
      ],
      "child_table": "development_revision_edges",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "revision_edge_to_accepted_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "from_work_item_revision_ref"
      ],
      "child_table": "development_revision_edges",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "revision_edge_from_work_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "to_work_item_revision_ref"
      ],
      "child_table": "development_revision_edges",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "revision_edge_to_work_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_work_spec_bindings",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "work_spec_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_work_spec_bindings",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "work_spec_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "child_table": "development_work_spec_bindings",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "work_spec_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_semantic_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "semantic_attempt_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_semantic_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "semantic_attempt_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "child_table": "development_semantic_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "semantic_attempt_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "selection_decision_ref"
      ],
      "child_table": "development_semantic_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "semantic_attempt_selection_decision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_attempt_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "attempt_fence_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_attempt_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "attempt_fence_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "child_table": "development_attempt_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "attempt_fence_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "child_table": "development_attempt_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "attempt_fence_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_authority_evaluations",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "authority_evaluation_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "child_table": "development_authority_evaluations",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "authority_evaluation_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "child_table": "development_authority_evaluations",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "authority_evaluation_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_effect_intents",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "effect_intent_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "child_table": "development_effect_intents",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "effect_intent_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Require equal program_ref, exact basis decision identity/digest, and basis-kind coherence; mismatch is database_integrity_failure.",
      "child_columns": [
        "basis_decision_ref"
      ],
      "child_table": "development_effect_intents",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "effect_intent_basis_decision_owner_exception"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "command_ref"
      ],
      "child_table": "development_effect_intents",
      "deferrability": "DEFERRABLE INITIALLY DEFERRED",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "command_ref"
      ],
      "parent_table": "development_author_commands",
      "role": "author_effect_intent_command"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "cancellation_target_effect_intent_ref"
      ],
      "child_table": "development_effect_intents",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "cancellation_target_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "effect_fence_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "effect_fence_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "effect_fence_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "effect_fence_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "effect_fence_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "parent_table": "development_attempt_fences",
      "role": "effect_fence_attempt_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "command_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "DEFERRABLE INITIALLY DEFERRED",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "command_ref"
      ],
      "parent_table": "development_author_commands",
      "role": "author_effect_fence_command"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "cancellation_target_effect_intent_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "effect_fence_cancellation_target_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "cancellation_target_effect_fence_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "parent_table": "development_effect_fences",
      "role": "effect_fence_cancellation_target_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "author_command_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "author_command_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "author_command_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "author_command_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "author_command_author_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "parent_table": "development_attempt_fences",
      "role": "author_command_attempt_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "parent_table": "development_effect_fences",
      "role": "author_command_effect_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "work_spec_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "work_spec_ref"
      ],
      "parent_table": "development_work_spec_bindings",
      "role": "author_command_work_spec_binding"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "child_table": "development_effect_heads",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "effect_head_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "current_effect_fence_ref"
      ],
      "child_table": "development_effect_heads",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "parent_table": "development_effect_fences",
      "role": "effect_head_current_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "cancellation_effect_intent_ref"
      ],
      "child_table": "development_effect_heads",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "effect_head_cancellation_effect"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "delivery_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "command_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "command_ref"
      ],
      "parent_table": "development_author_commands",
      "role": "delivery_originating_command"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "delivery_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "delivery_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "parent_table": "development_attempt_fences",
      "role": "delivery_attempt_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "parent_table": "development_effect_fences",
      "role": "delivery_effect_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "predecessor_delivery_attempt_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "delivery_attempt_ref"
      ],
      "parent_table": "development_delivery_attempts",
      "role": "delivery_predecessor"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "basis_decision_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "delivery_basis_decision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "child_table": "development_delivery_heads",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "delivery_head_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "current_delivery_attempt_ref"
      ],
      "child_table": "development_delivery_heads",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "delivery_attempt_ref"
      ],
      "parent_table": "development_delivery_attempts",
      "role": "delivery_head_current_delivery_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "decision_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "basis_decision_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "decision_basis_decision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "basis_program_version_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "decision_basis_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "resulting_program_version_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "DEFERRABLE INITIALLY DEFERRED",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "initialize_decision_resulting_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "selected_semantic_attempt_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "decision_selected_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "selected_attempt_fence_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "parent_table": "development_attempt_fences",
      "role": "decision_selected_attempt_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "target_effect_intent_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "decision_target_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "target_effect_fence_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "parent_table": "development_effect_fences",
      "role": "decision_target_effect_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "target_delivery_attempt_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "delivery_attempt_ref"
      ],
      "parent_table": "development_delivery_attempts",
      "role": "decision_target_delivery_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "originating_command_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "command_ref"
      ],
      "parent_table": "development_author_commands",
      "role": "decision_originating_command"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "resulting_accepted_intent_revision_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "decision_resulting_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "resulting_work_item_ref",
        "resulting_work_item_revision_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "decision_resulting_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "receipt_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "decision_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "receipt_decision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "result_program_version_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "receipt_result_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "result_semantic_attempt_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "receipt_result_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "result_effect_intent_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "receipt_result_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "result_effect_fence_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "parent_table": "development_effect_fences",
      "role": "receipt_result_effect_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "result_delivery_attempt_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "delivery_attempt_ref"
      ],
      "parent_table": "development_delivery_attempts",
      "role": "receipt_result_delivery_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "result_decision_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "receipt_result_decision"
    }
  ],
  "nonimplementation": {
    "complete_family_replay": false,
    "database_mutation": false,
    "dependency": false,
    "migration_0002_repository_sql": false,
    "migration_0003_pulled_forward": false,
    "mutation_or_recovery_api": false,
    "package_root_export": false,
    "production_source": false,
    "public_reader": false,
    "runtime_authority": false,
    "state_store_method": false,
    "writer_session_method": false
  },
  "oracle_architecture": {
    "allowed_literal_nodes": [
      "dict",
      "list",
      "tuple",
      "str",
      "int",
      "bool",
      "None"
    ],
    "allowed_repository_reads": [
      ".docs/c2b-durable-development-state.md"
    ],
    "architecture_self_check_additional_read": "tests/test_c2b2_field_level_contract.py",
    "dynamic_dispatch": "forbidden",
    "expected_contract_assignment_count": 1,
    "expected_contract_rhs": "directly literal Python expression",
    "forbidden_imports": [
      "another collected test",
      "ge_nwp_coordinator production source",
      "sqlite3",
      "importlib or dynamic import"
    ],
    "forbidden_input_reads": [
      "external SQL",
      "external proposal JSON",
      "production source",
      "Downloads or proposal-artifact path"
    ],
    "forbidden_literal_nodes": [
      "nonconstant Name",
      "Call",
      "Attribute",
      "Subscript",
      "comprehension",
      "generator",
      "lambda",
      "formatted string"
    ],
    "forbidden_runtime_selection": [
      "eval",
      "exec",
      "built-in compile",
      "__import__",
      "getattr-based callable selection",
      "globals-based callable selection",
      "locals-based callable selection",
      "call through Subscript",
      "callable registry",
      "validator registry",
      "generic dispatch table"
    ],
    "permitted_semantic_sha256_call_sites": [
      {
        "enclosing_function": "_graph_digest_from_identity",
        "purpose": "produce the domain-separated semantic mutation-graph digest"
      },
      {
        "enclosing_function": "test_c2b2_common_graph_digest_primitive_is_closed_and_order_sensitive",
        "purpose": "independently verify the semantic mutation-graph golden formula"
      }
    ],
    "runtime_literal_equality": "ast.literal_eval(assignment value) equals runtime EXPECTED_CONTRACT",
    "source_or_file_hash_authority": "forbidden; diagnostic hashes cannot substitute for semantic equality"
  },
  "privacy_contract": {
    "forbidden_persistent_material": [
      "WorkSpec objective",
      "requirements",
      "exclusions",
      "credentials",
      "private endpoints",
      "bearer retrieval material",
      "private prompts or responses",
      "transcripts",
      "source bytes",
      "candidate bytes",
      "capsule bytes or entries",
      "physical workspace paths",
      "TLS/SPIFFE/Vault/Codex/OpenAI material"
    ],
    "persisted_classes": [
      "safe references",
      "digests",
      "fixed states",
      "integer counters and ceilings",
      "whole-second UTC timestamps",
      "exact current repository-relative C2A path arrays"
    ],
    "privacy_vocabularies": {
      "work_spec": "private_work_spec",
      "worker_command": "private_source_change"
    },
    "safe_failure": "privacy-safe closed error vocabulary; no exception string or diagnostic includes persisted private material"
  },
  "private_readers": [
    {
      "absence_result": null,
      "bounded_aggregate_verification": "permitted",
      "cardinality": "singleton",
      "complete_mutation_family_replay_verification": false,
      "decoded_private_value": "private_closed_mutation_receipt_envelope",
      "duplicate_result": "database_integrity_failure",
      "fetch_bound": 2,
      "future_caller": [
        "C2B3",
        "C2B5",
        "C2B6"
      ],
      "limit": 2,
      "lookup_identity": [
        "mutation_ref"
      ],
      "malformed_row_result": "database_integrity_failure",
      "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
      "ordering": null,
      "role": "mutation_receipt_by_mutation_ref",
      "row_digest_verification": "required_before_return",
      "safe_error": "mutation_failed_or_database_integrity_failure",
      "selects": [
        {
          "fields": [
            "schema_id",
            "mutation_ref",
            "mutation_family",
            "command_schema_id",
            "command_digest",
            "program_ref",
            "decision_ref",
            "result_program_version_ref",
            "result_semantic_attempt_ref",
            "result_effect_intent_ref",
            "result_effect_fence_ref",
            "result_delivery_attempt_ref",
            "result_observation_ref",
            "result_decision_ref",
            "result_class",
            "result_projection_digest",
            "mutation_graph_digest",
            "outcome",
            "committed_at"
          ],
          "table": "development_mutation_receipts"
        }
      ]
    },
    {
      "absence_result": null,
      "bounded_aggregate_verification": "permitted",
      "cardinality": "singleton",
      "complete_mutation_family_replay_verification": false,
      "decoded_private_value": "private_closed_development_decision_envelope",
      "duplicate_result": "database_integrity_failure",
      "fetch_bound": 2,
      "future_caller": [
        "C2B3",
        "C2B5",
        "C2B6"
      ],
      "limit": 2,
      "lookup_identity": [
        "decision_ref"
      ],
      "malformed_row_result": "database_integrity_failure",
      "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
      "ordering": null,
      "role": "decision_by_decision_ref",
      "row_digest_verification": "required_before_return",
      "safe_error": "mutation_failed_or_database_integrity_failure",
      "selects": [
        {
          "fields": [
            "schema_id",
            "mutation_ref",
            "decision_ref",
            "program_ref",
            "decision_kind",
            "decision_variant",
            "basis_decision_ref",
            "basis_program_version_ref",
            "basis_program_version_number",
            "expected_program_head_revision",
            "resulting_program_version_ref",
            "resulting_program_version_number",
            "selected_semantic_attempt_ref",
            "selected_candidate_ref",
            "selected_attempt_fence_ref",
            "selected_attempt_fence_digest",
            "target_effect_intent_ref",
            "target_effect_class",
            "target_effect_fence_ref",
            "target_effect_fence_digest",
            "expected_target_effect_head_revision",
            "target_delivery_attempt_ref",
            "originating_command_ref",
            "originating_command_digest",
            "target_capsule_manifest_ref",
            "target_portable_capsule_digest",
            "coding_global_stop_ref",
            "coding_global_stop_version",
            "source_directive_ref",
            "source_directive_digest",
            "source_evidence_ref",
            "source_evidence_digest",
            "preassigned_semantic_attempt_ref",
            "preassigned_candidate_ref",
            "preassigned_effect_intent_ref",
            "preassigned_effect_fence_ref",
            "preassigned_delivery_attempt_ref",
            "resulting_accepted_intent_revision_ref",
            "resulting_work_item_ref",
            "resulting_work_item_revision_ref",
            "reason_code",
            "decided_at",
            "decision_digest"
          ],
          "table": "development_decisions"
        }
      ]
    },
    {
      "absence_result": null,
      "bounded_aggregate_verification": "permitted",
      "cardinality": "two_singletons",
      "complete_mutation_family_replay_verification": false,
      "decoded_private_value": "private_program_head_current_version_aggregate",
      "duplicate_result": "database_integrity_failure",
      "fetch_bound": 2,
      "future_caller": [
        "C2B3",
        "C2B6"
      ],
      "limit": 2,
      "lookup_identity": [
        "program_ref"
      ],
      "malformed_row_result": "database_integrity_failure",
      "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
      "ordering": null,
      "role": "program_head_and_current_version",
      "row_digest_verification": "required_before_return",
      "safe_error": "mutation_failed_or_database_integrity_failure",
      "selects": [
        {
          "fields": [
            "schema_id",
            "program_ref",
            "current_program_version_ref",
            "current_program_version_number",
            "head_revision",
            "program_state",
            "updated_at",
            "head_digest"
          ],
          "table": "development_program_heads"
        },
        {
          "fields": [
            "schema_id",
            "program_version_ref",
            "program_ref",
            "program_version_number",
            "program_version_kind",
            "creating_decision_ref",
            "accepted_intent_revision_ref",
            "created_at",
            "program_version_digest"
          ],
          "table": "development_program_versions"
        }
      ]
    },
    {
      "absence_result": null,
      "bounded_aggregate_verification": "permitted",
      "cardinality": "two_singletons",
      "complete_mutation_family_replay_verification": false,
      "decoded_private_value": "private_initialize_decision_result_aggregate",
      "duplicate_result": "database_integrity_failure",
      "fetch_bound": 2,
      "future_caller": [
        "C2B3"
      ],
      "limit": 2,
      "lookup_identity": [
        "program_ref",
        "decision_ref"
      ],
      "malformed_row_result": "database_integrity_failure",
      "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
      "ordering": null,
      "role": "initialize_decision_and_resulting_version",
      "row_digest_verification": "required_before_return",
      "safe_error": "mutation_failed_or_database_integrity_failure",
      "selects": [
        {
          "fields": [
            "schema_id",
            "mutation_ref",
            "decision_ref",
            "program_ref",
            "decision_kind",
            "decision_variant",
            "basis_decision_ref",
            "basis_program_version_ref",
            "basis_program_version_number",
            "expected_program_head_revision",
            "resulting_program_version_ref",
            "resulting_program_version_number",
            "selected_semantic_attempt_ref",
            "selected_candidate_ref",
            "selected_attempt_fence_ref",
            "selected_attempt_fence_digest",
            "target_effect_intent_ref",
            "target_effect_class",
            "target_effect_fence_ref",
            "target_effect_fence_digest",
            "expected_target_effect_head_revision",
            "target_delivery_attempt_ref",
            "originating_command_ref",
            "originating_command_digest",
            "target_capsule_manifest_ref",
            "target_portable_capsule_digest",
            "coding_global_stop_ref",
            "coding_global_stop_version",
            "source_directive_ref",
            "source_directive_digest",
            "source_evidence_ref",
            "source_evidence_digest",
            "preassigned_semantic_attempt_ref",
            "preassigned_candidate_ref",
            "preassigned_effect_intent_ref",
            "preassigned_effect_fence_ref",
            "preassigned_delivery_attempt_ref",
            "resulting_accepted_intent_revision_ref",
            "resulting_work_item_ref",
            "resulting_work_item_revision_ref",
            "reason_code",
            "decided_at",
            "decision_digest"
          ],
          "table": "development_decisions"
        },
        {
          "fields": [
            "schema_id",
            "program_version_ref",
            "program_ref",
            "program_version_number",
            "program_version_kind",
            "creating_decision_ref",
            "accepted_intent_revision_ref",
            "created_at",
            "program_version_digest"
          ],
          "table": "development_program_versions"
        }
      ]
    },
    {
      "absence_result": null,
      "bounded_aggregate_verification": "permitted",
      "cardinality": "singleton",
      "complete_mutation_family_replay_verification": false,
      "decoded_private_value": "private_verified_accepted_intent_revision",
      "duplicate_result": "database_integrity_failure",
      "fetch_bound": 2,
      "future_caller": [
        "C2B3",
        "C2B6"
      ],
      "limit": 2,
      "lookup_identity": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "malformed_row_result": "database_integrity_failure",
      "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
      "ordering": null,
      "role": "accepted_intent_revision_by_exact_ref",
      "row_digest_verification": "required_before_return",
      "safe_error": "mutation_failed_or_database_integrity_failure",
      "selects": [
        {
          "fetch": "fetchmany(2)",
          "fields": [
            "schema_id",
            "accepted_intent_revision_ref",
            "program_ref",
            "accepted_intent_revision_number",
            "prior_accepted_intent_revision_ref",
            "source_intent_ref",
            "source_intent_digest",
            "safe_projection_digest",
            "created_at",
            "accepted_intent_revision_digest"
          ],
          "limit": 2,
          "lookup_key": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "ordering": null,
          "parameter_order": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "query_sql": "SELECT schema_id, accepted_intent_revision_ref, program_ref, accepted_intent_revision_number, prior_accepted_intent_revision_ref, source_intent_ref, source_intent_digest, safe_projection_digest, created_at, accepted_intent_revision_digest FROM development_accepted_intent_revisions WHERE program_ref = ? AND accepted_intent_revision_ref = ? LIMIT 2",
          "table": "development_accepted_intent_revisions"
        }
      ]
    },
    {
      "absence_result": null,
      "bounded_aggregate_verification": "permitted",
      "cardinality": "bounded_singleton_graph",
      "complete_mutation_family_replay_verification": false,
      "decoded_private_value": "private_verified_work_item_head_and_revision",
      "duplicate_result": "database_integrity_failure",
      "fetch_bound": 2,
      "future_caller": [
        "C2B3",
        "C2B5",
        "C2B6"
      ],
      "limit": 2,
      "lookup_identity": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "malformed_row_result": "database_integrity_failure",
      "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
      "ordering": null,
      "role": "work_item_head_and_revision_by_exact_ref",
      "row_digest_verification": "required_before_return",
      "safe_error": "mutation_failed_or_database_integrity_failure",
      "selects": [
        {
          "fields": [
            "schema_id",
            "work_item_ref",
            "program_ref",
            "current_work_item_revision_ref",
            "current_work_item_revision_number",
            "head_revision",
            "work_state",
            "updated_at",
            "head_digest"
          ],
          "table": "development_work_item_heads"
        },
        {
          "fields": [
            "schema_id",
            "work_item_revision_ref",
            "program_ref",
            "work_item_ref",
            "work_item_revision_number",
            "work_item_revision_kind",
            "prior_work_item_revision_ref",
            "accepted_intent_revision_ref",
            "created_at",
            "work_item_revision_digest"
          ],
          "table": "development_work_item_revisions"
        }
      ]
    },
    {
      "absence_result": "database_integrity_failure for an initial version; [] only for a non-initial version whose controlling contract permits empty membership",
      "all_pages_same_capability_epoch": true,
      "bounded_aggregate_verification": "permitted",
      "cardinality": "paged_collection",
      "complete_mutation_family_replay_verification": false,
      "continuation_pair_rule": "after_membership_ordinal and after_work_item_ref are both null or both present",
      "decoded_private_value": "private_ordered_program_work_membership",
      "duplicate_result": "database_integrity_failure",
      "fetch_bound": 257,
      "future_caller": [
        "C2B3",
        "C2B6"
      ],
      "has_more_rule": "The 257th row proves has_more only and is not returned.",
      "limit": 257,
      "lookup_identity": [
        "program_ref",
        "program_version_ref",
        "after_membership_ordinal",
        "after_work_item_ref"
      ],
      "malformed_row_result": "database_integrity_failure",
      "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
      "ordering": [
        "membership_ordinal ASC",
        "work_item_ref ASC"
      ],
      "return_bound": 256,
      "role": "paged_program_version_membership",
      "row_digest_verification": "required_before_return",
      "safe_error": "mutation_failed_or_database_integrity_failure",
      "selects": [
        {
          "fields": [
            "schema_id",
            "program_ref",
            "program_version_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "membership_ordinal",
            "created_at",
            "membership_digest"
          ],
          "table": "development_program_version_work_items"
        },
        {
          "fields": [
            "schema_id",
            "work_item_revision_ref",
            "program_ref",
            "work_item_ref",
            "work_item_revision_number",
            "work_item_revision_kind",
            "prior_work_item_revision_ref",
            "accepted_intent_revision_ref",
            "created_at",
            "work_item_revision_digest"
          ],
          "table": "development_work_item_revisions"
        }
      ]
    },
    {
      "absence_result": null,
      "bounded_aggregate_verification": "permitted",
      "cardinality": "singleton",
      "complete_mutation_family_replay_verification": false,
      "decoded_private_value": "private_safe_work_spec_projection_binding",
      "duplicate_result": "database_integrity_failure",
      "fetch_bound": 2,
      "future_caller": [
        "C2B3",
        "C2B5",
        "C2B6"
      ],
      "limit": 2,
      "lookup_identity": [
        "program_ref",
        "program_version_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "malformed_row_result": "database_integrity_failure",
      "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
      "ordering": null,
      "role": "work_spec_safe_binding",
      "row_digest_verification": "required_before_return",
      "safe_error": "mutation_failed_or_database_integrity_failure",
      "selects": [
        {
          "fields": [
            "schema_id",
            "work_spec_ref",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "repository_ref",
            "base_git_object_format",
            "base_git_oid",
            "authorized_paths_json",
            "validation_requirement_ref",
            "review_requirement_ref",
            "privacy_classification",
            "work_spec_digest",
            "safe_projection_digest",
            "recorded_at",
            "work_spec_binding_digest"
          ],
          "table": "development_work_spec_bindings"
        }
      ]
    },
    {
      "absence_result": null,
      "bounded_aggregate_verification": "permitted",
      "cardinality": "bounded_singleton_graph",
      "complete_mutation_family_replay_verification": false,
      "decoded_private_value": "private_verified_attempt_fence_command_effect_graph",
      "duplicate_result": "database_integrity_failure",
      "fetch_bound": 2,
      "future_caller": [
        "C2B3",
        "C2B5",
        "C2B6"
      ],
      "limit": 2,
      "lookup_identity": [
        "program_ref",
        "semantic_attempt_ref",
        "effect_intent_ref"
      ],
      "malformed_row_result": "database_integrity_failure",
      "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
      "ordering": null,
      "role": "attempt_fence_command_effect_aggregate",
      "row_digest_verification": "required_before_return",
      "safe_error": "mutation_failed_or_database_integrity_failure",
      "selects": [
        {
          "fields": [
            "schema_id",
            "semantic_attempt_ref",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "attempt_number",
            "candidate_ref",
            "attempt_phase",
            "selection_decision_ref",
            "created_at",
            "semantic_attempt_digest"
          ],
          "table": "development_semantic_attempts"
        },
        {
          "fields": [
            "schema_id",
            "attempt_fence_ref",
            "parent_standing_grant_ref",
            "parent_standing_grant_digest",
            "attempt_authorization_ref",
            "attempt_authorization_digest",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "semantic_attempt_ref",
            "repository_ref",
            "base_git_object_format",
            "base_git_oid",
            "path_ceiling_json",
            "allowed_effect_class_mask",
            "aggregate_max_active_invocations",
            "aggregate_max_candidate_bytes",
            "aggregate_max_changed_files",
            "aggregate_max_cost_microusd",
            "aggregate_max_cpu_seconds",
            "aggregate_max_deliveries",
            "aggregate_max_deployments",
            "aggregate_max_local_commits",
            "aggregate_max_memory_bytes",
            "aggregate_max_merges",
            "aggregate_max_model_input_tokens",
            "aggregate_max_model_output_tokens",
            "aggregate_max_pull_requests",
            "aggregate_max_pushes",
            "aggregate_max_wall_seconds",
            "expires_at",
            "global_stop_ref",
            "global_stop_version",
            "attempt_fence_digest",
            "recorded_at"
          ],
          "table": "development_attempt_fences"
        },
        {
          "fields": [
            "schema_id",
            "command_ref",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "semantic_attempt_ref",
            "effect_intent_ref",
            "effect_class",
            "candidate_ref",
            "repository_ref",
            "base_git_object_format",
            "base_git_oid",
            "path_ceiling_json",
            "work_spec_ref",
            "work_spec_digest",
            "standing_grant_ref",
            "standing_grant_digest",
            "attempt_authorization_ref",
            "attempt_authorization_digest",
            "effect_authorization_ref",
            "effect_authorization_digest",
            "attempt_fence_ref",
            "attempt_fence_digest",
            "effect_fence_ref",
            "effect_fence_digest",
            "global_stop_ref",
            "global_stop_version",
            "validation_requirement_ref",
            "validation_requirement_digest",
            "review_requirement_ref",
            "review_requirement_digest",
            "capsule_schema_id",
            "capsule_profile_ref",
            "effect_max_active_invocations",
            "effect_max_candidate_bytes",
            "effect_max_changed_files",
            "effect_max_cost_microusd",
            "effect_max_cpu_seconds",
            "effect_max_deliveries",
            "effect_max_deployments",
            "effect_max_local_commits",
            "effect_max_memory_bytes",
            "effect_max_merges",
            "effect_max_model_input_tokens",
            "effect_max_model_output_tokens",
            "effect_max_pull_requests",
            "effect_max_pushes",
            "effect_max_wall_seconds",
            "privacy_classification",
            "redaction_profile_ref",
            "command_digest",
            "recorded_at"
          ],
          "table": "development_author_commands"
        },
        {
          "fields": [
            "schema_id",
            "effect_intent_ref",
            "program_ref",
            "program_version_ref",
            "semantic_attempt_ref",
            "effect_class",
            "candidate_ref",
            "command_ref",
            "basis_decision_ref",
            "cancellation_target_effect_intent_ref",
            "expected_target_effect_head_revision",
            "portable_capsule_digest",
            "created_at",
            "effect_intent_digest"
          ],
          "table": "development_effect_intents"
        },
        {
          "fields": [
            "schema_id",
            "effect_fence_ref",
            "parent_standing_grant_ref",
            "parent_standing_grant_digest",
            "effect_authorization_ref",
            "effect_authorization_digest",
            "attempt_fence_ref",
            "attempt_fence_digest",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "semantic_attempt_ref",
            "effect_intent_ref",
            "effect_class",
            "command_ref",
            "command_digest",
            "candidate_ref",
            "repository_ref",
            "base_git_object_format",
            "base_git_oid",
            "path_ceiling_json",
            "effect_max_active_invocations",
            "effect_max_candidate_bytes",
            "effect_max_changed_files",
            "effect_max_cost_microusd",
            "effect_max_cpu_seconds",
            "effect_max_deliveries",
            "effect_max_deployments",
            "effect_max_local_commits",
            "effect_max_memory_bytes",
            "effect_max_merges",
            "effect_max_model_input_tokens",
            "effect_max_model_output_tokens",
            "effect_max_pull_requests",
            "effect_max_pushes",
            "effect_max_wall_seconds",
            "expires_at",
            "global_stop_ref",
            "global_stop_version",
            "portable_capsule_digest",
            "cancellation_target_effect_intent_ref",
            "cancellation_target_effect_fence_ref",
            "cancellation_target_effect_fence_digest",
            "effect_fence_digest",
            "recorded_at"
          ],
          "table": "development_effect_fences"
        },
        {
          "fields": [
            "schema_id",
            "authority_evaluation_ref",
            "program_ref",
            "evaluation_scope",
            "evaluation_subject_ref",
            "semantic_attempt_ref",
            "effect_intent_ref",
            "authority_ref",
            "authority_digest",
            "authority_state",
            "reason_code",
            "expires_at",
            "evaluated_at",
            "authority_evaluation_digest"
          ],
          "table": "development_authority_evaluations"
        }
      ]
    },
    {
      "absence_result": null,
      "bounded_aggregate_verification": "permitted",
      "cardinality": "singleton",
      "complete_mutation_family_replay_verification": false,
      "decoded_private_value": "private_verified_authority_evaluation",
      "duplicate_result": "database_integrity_failure",
      "fetch_bound": 2,
      "future_caller": [
        "C2B3",
        "C2B5"
      ],
      "limit": 2,
      "lookup_identity": [
        "program_ref",
        "authority_evaluation_ref"
      ],
      "malformed_row_result": "database_integrity_failure",
      "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
      "ordering": null,
      "role": "authority_evaluation_by_exact_ref",
      "row_digest_verification": "required_before_return",
      "safe_error": "mutation_failed_or_database_integrity_failure",
      "selects": [
        {
          "fetch": "fetchmany(2)",
          "fields": [
            "schema_id",
            "authority_evaluation_ref",
            "program_ref",
            "evaluation_scope",
            "evaluation_subject_ref",
            "semantic_attempt_ref",
            "effect_intent_ref",
            "authority_ref",
            "authority_digest",
            "authority_state",
            "reason_code",
            "expires_at",
            "evaluated_at",
            "authority_evaluation_digest"
          ],
          "limit": 2,
          "lookup_key": [
            "program_ref",
            "authority_evaluation_ref"
          ],
          "ordering": null,
          "parameter_order": [
            "program_ref",
            "authority_evaluation_ref"
          ],
          "query_sql": "SELECT schema_id, authority_evaluation_ref, program_ref, evaluation_scope, evaluation_subject_ref, semantic_attempt_ref, effect_intent_ref, authority_ref, authority_digest, authority_state, reason_code, expires_at, evaluated_at, authority_evaluation_digest FROM development_authority_evaluations WHERE program_ref = ? AND authority_evaluation_ref = ? LIMIT 2",
          "table": "development_authority_evaluations"
        }
      ]
    },
    {
      "absence_result": null,
      "bounded_aggregate_verification": "permitted",
      "cardinality": "singleton",
      "complete_mutation_family_replay_verification": false,
      "decoded_private_value": "private_effect_head",
      "duplicate_result": "database_integrity_failure",
      "fetch_bound": 2,
      "future_caller": [
        "C2B3",
        "C2B5"
      ],
      "limit": 2,
      "lookup_identity": [
        "program_ref",
        "effect_intent_ref"
      ],
      "malformed_row_result": "database_integrity_failure",
      "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
      "ordering": null,
      "role": "effect_head",
      "row_digest_verification": "required_before_return",
      "safe_error": "mutation_failed_or_database_integrity_failure",
      "selects": [
        {
          "fields": [
            "schema_id",
            "effect_intent_ref",
            "program_ref",
            "current_effect_fence_ref",
            "head_revision",
            "effect_state",
            "cancellation_effect_intent_ref",
            "updated_at",
            "head_digest"
          ],
          "table": "development_effect_heads"
        }
      ]
    },
    {
      "absence_result": null,
      "bounded_aggregate_verification": "permitted",
      "cardinality": "two_singletons",
      "complete_mutation_family_replay_verification": false,
      "decoded_private_value": "private_delivery_head_current_attempt_aggregate",
      "duplicate_result": "database_integrity_failure",
      "fetch_bound": 2,
      "future_caller": [
        "C2B3",
        "C2B5"
      ],
      "limit": 2,
      "lookup_identity": [
        "program_ref",
        "effect_intent_ref"
      ],
      "malformed_row_result": "database_integrity_failure",
      "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
      "ordering": null,
      "role": "delivery_head",
      "row_digest_verification": "required_before_return",
      "safe_error": "mutation_failed_or_database_integrity_failure",
      "selects": [
        {
          "fields": [
            "schema_id",
            "effect_intent_ref",
            "program_ref",
            "current_delivery_attempt_ref",
            "head_revision",
            "delivery_state",
            "updated_at",
            "head_digest"
          ],
          "table": "development_delivery_heads"
        },
        {
          "fields": [
            "schema_id",
            "delivery_attempt_ref",
            "program_ref",
            "program_version_ref",
            "command_ref",
            "command_digest",
            "semantic_attempt_ref",
            "effect_intent_ref",
            "attempt_fence_ref",
            "attempt_fence_digest",
            "effect_fence_ref",
            "effect_fence_digest",
            "adapter_kind",
            "adapter_safe_correlation_ref",
            "delivery_envelope_digest",
            "delivery_kind",
            "delivery_number",
            "predecessor_delivery_attempt_ref",
            "basis_decision_ref",
            "recorded_at",
            "delivery_attempt_digest"
          ],
          "table": "development_delivery_attempts"
        }
      ]
    }
  ],
  "receipt_envelope": {
    "column_count": 19,
    "common_required_fields": [
      "schema_id",
      "mutation_ref",
      "mutation_family",
      "command_schema_id",
      "command_digest",
      "program_ref",
      "result_class",
      "result_projection_digest",
      "mutation_graph_digest",
      "outcome",
      "committed_at"
    ],
    "family_matrix": [
      {
        "command_schema_id": "governed-execution.nwp-initialize-development-program-command.v1",
        "family": "initialize_development_program",
        "required_non_null_result_fields": [
          "decision_ref",
          "result_program_version_ref",
          "result_decision_ref"
        ],
        "required_null_result_fields": [
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref",
          "result_observation_ref"
        ],
        "result_class": "development_program_initialized",
        "result_identity_keys": [
          "schema_id",
          "program_ref",
          "decision_ref",
          "result_program_version_ref",
          "result_decision_ref"
        ],
        "result_projection_digest_domain": "governed-execution.nwp-initialize-development-program-result.v1.identity",
        "result_projection_schema_id": "governed-execution.nwp-initialize-development-program-result.v1",
        "sql_branch": "(mutation_family='initialize_development_program' AND command_schema_id='governed-execution.nwp-initialize-development-program-command.v1' AND result_class='development_program_initialized' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NULL AND result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND result_delivery_attempt_ref IS NULL AND result_observation_ref IS NULL AND result_decision_ref IS NOT NULL AND result_decision_ref=decision_ref)"
      },
      {
        "command_schema_id": "governed-execution.nwp-establish-development-author-effect-intent-command.v1",
        "family": "establish_development_author_effect_intent",
        "required_non_null_result_fields": [
          "decision_ref",
          "result_program_version_ref",
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref"
        ],
        "required_null_result_fields": [
          "result_observation_ref",
          "result_decision_ref"
        ],
        "result_class": "development_author_effect_intent_established",
        "result_identity_keys": [
          "schema_id",
          "program_ref",
          "decision_ref",
          "result_program_version_ref",
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref"
        ],
        "result_projection_digest_domain": "governed-execution.nwp-establish-development-author-effect-intent-result.v1.identity",
        "result_projection_schema_id": "governed-execution.nwp-establish-development-author-effect-intent-result.v1",
        "sql_branch": "(mutation_family='establish_development_author_effect_intent' AND command_schema_id='governed-execution.nwp-establish-development-author-effect-intent-command.v1' AND result_class='development_author_effect_intent_established' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NOT NULL AND result_effect_intent_ref IS NOT NULL AND result_effect_fence_ref IS NOT NULL AND result_delivery_attempt_ref IS NOT NULL AND result_observation_ref IS NULL AND result_decision_ref IS NULL)"
      },
      {
        "command_schema_id": "governed-execution.nwp-establish-development-bound-effect-intent-command.v1",
        "family": "establish_development_bound_effect_intent",
        "required_non_null_result_fields": [
          "decision_ref",
          "result_program_version_ref",
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref"
        ],
        "required_null_result_fields": [
          "result_observation_ref",
          "result_decision_ref"
        ],
        "result_class": "development_bound_effect_intent_established",
        "result_identity_keys": [
          "schema_id",
          "program_ref",
          "decision_ref",
          "result_program_version_ref",
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref"
        ],
        "result_projection_digest_domain": "governed-execution.nwp-establish-development-bound-effect-intent-result.v1.identity",
        "result_projection_schema_id": "governed-execution.nwp-establish-development-bound-effect-intent-result.v1",
        "sql_branch": "(mutation_family='establish_development_bound_effect_intent' AND command_schema_id='governed-execution.nwp-establish-development-bound-effect-intent-command.v1' AND result_class='development_bound_effect_intent_established' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NOT NULL AND result_effect_intent_ref IS NOT NULL AND result_effect_fence_ref IS NOT NULL AND result_delivery_attempt_ref IS NOT NULL AND result_observation_ref IS NULL AND result_decision_ref IS NULL)"
      },
      {
        "command_schema_id": "governed-execution.nwp-ingest-development-source-observation-command.v1",
        "family": "ingest_development_source_observation",
        "required_non_null_result_fields": [
          "result_observation_ref"
        ],
        "required_null_result_fields": [
          "decision_ref",
          "result_program_version_ref",
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref",
          "result_decision_ref"
        ],
        "result_class": "development_source_observation_ingested",
        "result_identity_keys": [
          "schema_id",
          "program_ref",
          "result_observation_ref"
        ],
        "result_projection_digest_domain": "governed-execution.nwp-ingest-development-source-observation-result.v1.identity",
        "result_projection_schema_id": "governed-execution.nwp-ingest-development-source-observation-result.v1",
        "sql_branch": "(mutation_family='ingest_development_source_observation' AND command_schema_id='governed-execution.nwp-ingest-development-source-observation-command.v1' AND result_class='development_source_observation_ingested' AND decision_ref IS NULL AND result_program_version_ref IS NULL AND result_semantic_attempt_ref IS NULL AND result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND result_delivery_attempt_ref IS NULL AND result_observation_ref IS NOT NULL AND result_decision_ref IS NULL)"
      },
      {
        "command_schema_id": "governed-execution.nwp-record-development-progression-decision-command.v1",
        "family": "record_development_progression_decision",
        "required_non_null_result_fields": [
          "decision_ref",
          "result_program_version_ref",
          "result_decision_ref"
        ],
        "required_null_result_fields": [
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref",
          "result_observation_ref"
        ],
        "result_class": "development_progression_decision_recorded",
        "result_identity_keys": [
          "schema_id",
          "program_ref",
          "decision_ref",
          "result_program_version_ref",
          "result_decision_ref"
        ],
        "result_projection_digest_domain": "governed-execution.nwp-record-development-progression-decision-result.v1.identity",
        "result_projection_schema_id": "governed-execution.nwp-record-development-progression-decision-result.v1",
        "sql_branch": "(mutation_family='record_development_progression_decision' AND command_schema_id='governed-execution.nwp-record-development-progression-decision-command.v1' AND result_class='development_progression_decision_recorded' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NULL AND result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND result_delivery_attempt_ref IS NULL AND result_observation_ref IS NULL AND result_decision_ref IS NOT NULL AND result_decision_ref=decision_ref)"
      }
    ],
    "ordered_columns": [
      "schema_id",
      "mutation_ref",
      "mutation_family",
      "command_schema_id",
      "command_digest",
      "program_ref",
      "decision_ref",
      "result_program_version_ref",
      "result_semantic_attempt_ref",
      "result_effect_intent_ref",
      "result_effect_fence_ref",
      "result_delivery_attempt_ref",
      "result_observation_ref",
      "result_decision_ref",
      "result_class",
      "result_projection_digest",
      "mutation_graph_digest",
      "outcome",
      "committed_at"
    ],
    "outcomes": [
      "committed"
    ],
    "safe_contradiction_result": "database_integrity_failure"
  },
  "receipt_scalar_coherence": {
    "establish_development_author_effect_intent": {
      "decision_ref": "exact_basis_decision",
      "result_decision_ref": "null",
      "result_delivery_attempt_ref": "exact_created_initial_delivery",
      "result_effect_fence_ref": "exact_created_author_effect_fence",
      "result_effect_intent_ref": "exact_created_author_effect_intent",
      "result_observation_ref": "null",
      "result_program_version_ref": "equals_effect_intent.program_version_ref_and_exact_basis_decision_bound_program_version_ref",
      "result_semantic_attempt_ref": "exact_created_attempt"
    },
    "establish_development_bound_effect_intent": {
      "decision_ref": "exact_basis_decision",
      "result_decision_ref": "null",
      "result_delivery_attempt_ref": "exact_created_initial_delivery",
      "result_effect_fence_ref": "exact_created_bound_effect_fence",
      "result_effect_intent_ref": "exact_created_bound_effect_intent",
      "result_observation_ref": "null",
      "result_program_version_ref": "equals_effect_intent.program_version_ref_and_exact_basis_decision_bound_program_version_ref",
      "result_semantic_attempt_ref": "exact_existing_attempt"
    },
    "every_family": {
      "contradiction_result": "database_integrity_failure",
      "projection_schema_domain_identity_from_receipt_family_matrix": true,
      "row_to_result_equality": "exact",
      "self_digest_exclusions": [
        "result_projection_digest"
      ]
    },
    "ingest_development_source_observation": {
      "all_decision_version_attempt_effect_fence_delivery_result_refs": "null",
      "observation_parent_graph_owner": "migration_0003",
      "result_observation_ref": "exact_safe_observation_result_ref"
    },
    "initialize_development_program": {
      "all_effect_attempt_delivery_observation_result_refs": "null",
      "decision_ref": "exact_initialize_decision",
      "result_decision_ref": "equals_decision_ref",
      "result_program_version_ref": "equals_decision.resulting_program_version_ref_and_created_program_version_ref"
    },
    "record_development_progression_decision": {
      "advancing_kinds_use_new_resulting_version": [
        "accept",
        "repair",
        "replan",
        "terminal_reject",
        "block"
      ],
      "all_attempt_effect_fence_delivery_observation_result_refs": "null",
      "decision_ref": "exact_committed_decision",
      "non_advancing_kinds_use_unchanged_basis_version": [
        "redeliver",
        "cancel"
      ],
      "result_decision_ref": "equals_decision_ref",
      "result_program_version_ref": "decision.resulting_program_version_ref_when_non_null_else_decision.basis_program_version_ref"
    }
  },
  "scalar_and_compound_contracts": {
    "closed_state_vocabularies": {
      "adapter_kind": [
        "direct_local_bootstrap",
        "execution_substrate"
      ],
      "attempt_phase": [
        "established"
      ],
      "authority_state": [
        "pending",
        "verified",
        "blocked",
        "stale",
        "revoked",
        "expired"
      ],
      "command_schema_id": [
        "governed-execution.nwp-initialize-development-program-command.v1",
        "governed-execution.nwp-establish-development-author-effect-intent-command.v1",
        "governed-execution.nwp-establish-development-bound-effect-intent-command.v1",
        "governed-execution.nwp-ingest-development-source-observation-command.v1",
        "governed-execution.nwp-record-development-progression-decision-command.v1"
      ],
      "decision_kind": [
        "initialize",
        "accept",
        "repair",
        "replan",
        "terminal_reject",
        "block",
        "redeliver",
        "cancel"
      ],
      "decision_variant": [
        "program_genesis",
        "candidate_acceptance",
        "candidate_repair",
        "program_replan",
        "attempt_selecting_replan",
        "program_terminal_reject",
        "program_block",
        "productive_redelivery",
        "cancellation_redelivery",
        "effect_cancellation"
      ],
      "delivery_kind": [
        "initial",
        "redelivery"
      ],
      "delivery_state": [
        "planned",
        "submitted",
        "outcome_unknown",
        "acknowledged",
        "rejected",
        "completed"
      ],
      "effect_class": [
        "author_candidate",
        "cancel_effect",
        "local_git_commit",
        "review_candidate",
        "validate_candidate"
      ],
      "effect_state": [
        "ready_for_delivery",
        "delivery_pending",
        "delivery_outcome_unknown",
        "observed",
        "cancellation_effect_established",
        "terminal"
      ],
      "evaluation_scope": [
        "attempt",
        "effect"
      ],
      "mutation_family": [
        "initialize_development_program",
        "establish_development_author_effect_intent",
        "establish_development_bound_effect_intent",
        "ingest_development_source_observation",
        "record_development_progression_decision"
      ],
      "program_state": [
        "active",
        "accepted",
        "terminal_rejected",
        "blocked"
      ],
      "program_version_kind": [
        "initial",
        "accepted",
        "repair",
        "replan",
        "terminal_rejected",
        "blocked"
      ],
      "receipt_outcome": [
        "committed"
      ],
      "result_class": [
        "development_program_initialized",
        "development_author_effect_intent_established",
        "development_bound_effect_intent_established",
        "development_source_observation_ingested",
        "development_progression_decision_recorded"
      ],
      "revision_edge_kind": [
        "accepted_intent_supersedes",
        "work_item_supersedes",
        "work_item_split",
        "work_item_merge"
      ],
      "target_effect_class": [
        "author_candidate",
        "cancel_effect",
        "local_git_commit",
        "review_candidate",
        "validate_candidate"
      ],
      "work_revision_kind": [
        "initial",
        "replan"
      ],
      "work_spec_privacy_classification": [
        "private_work_spec"
      ],
      "work_state": [
        "planned",
        "active",
        "accepted",
        "repair_required",
        "terminal_rejected",
        "blocked"
      ],
      "worker_command_privacy_classification": [
        "private_source_change"
      ]
    },
    "compound_value_encodings": {
      "CeilingsV1": {
        "encoding": "fifteen flattened nonnegative ANY/integer columns",
        "fields": [
          "max_active_invocations",
          "max_candidate_bytes",
          "max_changed_files",
          "max_cost_microusd",
          "max_cpu_seconds",
          "max_deliveries",
          "max_deployments",
          "max_local_commits",
          "max_memory_bytes",
          "max_merges",
          "max_model_input_tokens",
          "max_model_output_tokens",
          "max_pull_requests",
          "max_pushes",
          "max_wall_seconds"
        ]
      },
      "allowed_effect_classes": {
        "bit_order": [
          "author_candidate",
          "cancel_effect",
          "local_git_commit",
          "review_candidate",
          "validate_candidate"
        ],
        "encoding": "closed five-bit integer mask"
      },
      "path_ceiling": {
        "encoding": "exact canonical JSON text",
        "paths": [
          ".docs/system_overview/hybrid_integration_architecture_adr.md",
          "PLANS.md",
          "docs_contract_test.go"
        ],
        "value": "[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]"
      }
    },
    "digest_predicates": {
      "git_sha1_oid": "typeof(x)='text' AND length(x)=40 AND x=lower(x) AND x NOT GLOB '*[^0-9a-f]*'",
      "sha256": "typeof(x)='text' AND length(x)=64 AND x=lower(x) AND x NOT GLOB '*[^0-9a-f]*'"
    },
    "nullable_pair_conventions": {
      "enforcement": "column checks plus named bidirectional table checks",
      "rule": "every declared ref/digest or ref/version group is both-null or both-present"
    },
    "reason_code_predicate": "typeof(x)='text' AND length(x) BETWEEN 1 AND 96 AND substr(x,1,1) GLOB '[a-z]' AND x NOT GLOB '*[^a-z0-9_.-]*'",
    "safe_ref_predicate": "typeof(x)='text' AND length(x) BETWEEN 1 AND 96 AND substr(x,1,1) GLOB '[0-9A-Za-z]' AND x NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(x,1,instr(x,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
    "scalar_conventions": {
      "empty_string_required_fields": "rejected",
      "git_sha1_oid_predicate": "typeof(x)='text' AND length(x)=40 AND x=lower(x) AND x NOT GLOB '*[^0-9a-f]*'",
      "maximum_safe_ref_length": 96,
      "nonnegative_integer_predicate": "typeof(x)='integer' AND x>=0",
      "positive_integer_predicate": "typeof(x)='integer' AND x>=1",
      "python_boundary": "exact built-in types; bool rejected when int required",
      "reason_code_predicate": "typeof(x)='text' AND length(x) BETWEEN 1 AND 96 AND substr(x,1,1) GLOB '[a-z]' AND x NOT GLOB '*[^a-z0-9_.-]*'",
      "safe_ref_predicate": "typeof(x)='text' AND length(x) BETWEEN 1 AND 96 AND substr(x,1,1) GLOB '[0-9A-Za-z]' AND x NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(x,1,instr(x,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
      "sha256_predicate": "typeof(x)='text' AND length(x)=64 AND x=lower(x) AND x NOT GLOB '*[^0-9a-f]*'",
      "sqlite_declaration_type": "ANY",
      "tables_strict": true,
      "timestamp_predicate": "typeof(x)='text' AND length(x)=20 AND x GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(x,1,4) BETWEEN '0001' AND '9999' AND substr(x,6,2) BETWEEN '01' AND '12' AND substr(x,9,2) BETWEEN '01' AND '31' AND substr(x,12,2) BETWEEN '00' AND '23' AND substr(x,15,2) BETWEEN '00' AND '59' AND substr(x,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',x) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',x)=x"
    },
    "timestamp_predicate": "typeof(x)='text' AND length(x)=20 AND x GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(x,1,4) BETWEEN '0001' AND '9999' AND substr(x,6,2) BETWEEN '01' AND '12' AND substr(x,9,2) BETWEEN '01' AND '31' AND substr(x,12,2) BETWEEN '00' AND '23' AND substr(x,15,2) BETWEEN '00' AND '59' AND substr(x,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',x) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',x)=x"
  },
  "sql_core": {
    "application_generation": 2,
    "compatibility": [
      2,
      2
    ],
    "current_migration_0001_changed": false,
    "deferred_foreign_key_count": 6,
    "destructive": false,
    "explicit_index_count": 1,
    "foreign_key_count": 87,
    "immutable_table_count": 15,
    "immutable_table_names": [
      "development_program_versions",
      "development_accepted_intent_revisions",
      "development_work_item_revisions",
      "development_program_version_work_items",
      "development_revision_edges",
      "development_work_spec_bindings",
      "development_semantic_attempts",
      "development_attempt_fences",
      "development_authority_evaluations",
      "development_effect_intents",
      "development_effect_fences",
      "development_author_commands",
      "development_delivery_attempts",
      "development_decisions",
      "development_mutation_receipts"
    ],
    "immutable_trigger_count": 30,
    "migration_0003_present": false,
    "migration_catalog_target": [
      {
        "changed": false,
        "compatibility": [
          1,
          1
        ],
        "migration_id": "0001_initial",
        "sequence": 1
      },
      {
        "compatibility": [
          2,
          2
        ],
        "destructive": false,
        "migration_id": "0002_development_program_and_effect_state",
        "sequence": 2
      }
    ],
    "migration_id": "0002_development_program_and_effect_state",
    "mutable_table_count": 4,
    "mutable_table_names": [
      "development_program_heads",
      "development_work_item_heads",
      "development_effect_heads",
      "development_delivery_heads"
    ],
    "seed_c2b_rows": 0,
    "sequence": 2,
    "sql_rendering_contract": {
      "final_newline": true,
      "indentation": "two spaces for table members and trigger SELECT",
      "index_position": "after all tables and before triggers",
      "statement_separator": "two LF bytes",
      "table_statement_order": [
        "development_program_heads",
        "development_program_versions",
        "development_accepted_intent_revisions",
        "development_work_item_heads",
        "development_work_item_revisions",
        "development_program_version_work_items",
        "development_revision_edges",
        "development_work_spec_bindings",
        "development_semantic_attempts",
        "development_attempt_fences",
        "development_authority_evaluations",
        "development_effect_intents",
        "development_effect_fences",
        "development_author_commands",
        "development_effect_heads",
        "development_delivery_attempts",
        "development_delivery_heads",
        "development_decisions",
        "development_mutation_receipts"
      ],
      "trigger_order": "immutable table order; UPDATE then DELETE"
    },
    "strict_tables": true,
    "table_count": 19,
    "table_names_in_order": [
      "development_program_heads",
      "development_program_versions",
      "development_accepted_intent_revisions",
      "development_work_item_heads",
      "development_work_item_revisions",
      "development_program_version_work_items",
      "development_revision_edges",
      "development_work_spec_bindings",
      "development_semantic_attempts",
      "development_attempt_fences",
      "development_authority_evaluations",
      "development_effect_intents",
      "development_effect_fences",
      "development_author_commands",
      "development_effect_heads",
      "development_delivery_attempts",
      "development_delivery_heads",
      "development_decisions",
      "development_mutation_receipts"
    ],
    "view_count": 0
  },
  "tables": [
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-program-head.v1'",
          "constant": "governed-execution.nwp-development-program-head.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(current_program_version_ref)='text' AND length(current_program_version_ref) BETWEEN 1 AND 96 AND substr(current_program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND current_program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(current_program_version_ref,1,instr(current_program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "current_program_version_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(current_program_version_number)='integer' AND current_program_version_number>=1",
          "constant": null,
          "enum_values": null,
          "logical_type": "positive_integer",
          "name": "current_program_version_number",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(head_revision)='integer' AND head_revision>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "head_revision",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_state)='text' AND program_state IN ('active','accepted','terminal_rejected','blocked')",
          "constant": null,
          "enum_values": [
            "active",
            "accepted",
            "terminal_rejected",
            "blocked"
          ],
          "logical_type": "closed_enum",
          "name": "program_state",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(updated_at)='text' AND length(updated_at)=20 AND updated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(updated_at,1,4) BETWEEN '0001' AND '9999' AND substr(updated_at,6,2) BETWEEN '01' AND '12' AND substr(updated_at,9,2) BETWEEN '01' AND '31' AND substr(updated_at,12,2) BETWEEN '00' AND '23' AND substr(updated_at,15,2) BETWEEN '00' AND '59' AND substr(updated_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at)=updated_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "updated_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(head_digest)='text' AND length(head_digest)=64 AND head_digest=lower(head_digest) AND head_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "head_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "head_digest",
      "digest_domain": "governed-execution.nwp-development-program-head.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "program_ref",
        "current_program_version_ref",
        "current_program_version_number",
        "head_revision",
        "program_state",
        "updated_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "current_program_version_ref"
          ],
          "deferrability": "DEFERRABLE INITIALLY DEFERRED",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "program_head_current_program_version"
        }
      ],
      "future_mutation_owner": "program_progression_CAS",
      "immutable_triggers": [],
      "mutable": true,
      "name": "development_program_heads",
      "primary_key": [
        "program_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "program_head_and_current_version"
      ],
      "record_schema_id": "governed-execution.nwp-development-program-head.v1",
      "role": "program_progression_head",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [],
      "timestamp_participation": {
        "updated_at": true
      },
      "unique_constraints": []
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-program-version.v1'",
          "constant": "governed-execution.nwp-development-program-version.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_version_number)='integer' AND program_version_number>=1",
          "constant": null,
          "enum_values": null,
          "logical_type": "positive_integer",
          "name": "program_version_number",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_version_kind)='text' AND program_version_kind IN ('initial','accepted','repair','replan','terminal_rejected','blocked')",
          "constant": null,
          "enum_values": [
            "initial",
            "accepted",
            "repair",
            "replan",
            "terminal_rejected",
            "blocked"
          ],
          "logical_type": "closed_enum",
          "name": "program_version_kind",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(creating_decision_ref)='text' AND length(creating_decision_ref) BETWEEN 1 AND 96 AND substr(creating_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND creating_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(creating_decision_ref,1,instr(creating_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "creating_decision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_version_digest)='text' AND length(program_version_digest)=64 AND program_version_digest=lower(program_version_digest) AND program_version_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "program_version_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "program_version_digest",
      "digest_domain": "governed-execution.nwp-development-program-version.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "program_version_ref",
        "program_ref",
        "program_version_number",
        "program_version_kind",
        "creating_decision_ref",
        "accepted_intent_revision_ref",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "program_version_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "program_version_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "creating_decision_ref"
          ],
          "deferrability": "DEFERRABLE INITIALLY DEFERRED",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "program_version_creating_decision"
        }
      ],
      "future_mutation_owner": "_initialize_development_program_or_progression_decision",
      "immutable_triggers": [
        "development_program_versions_no_update",
        "development_program_versions_no_delete"
      ],
      "mutable": false,
      "name": "development_program_versions",
      "primary_key": [
        "program_version_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "program_head_and_current_version",
        "initialize_decision_and_resulting_version"
      ],
      "record_schema_id": "governed-execution.nwp-development-program-version.v1",
      "role": "program_version_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [
        {
          "name": "initial_program_version_number",
          "sql": "((program_version_kind='initial' AND program_version_number=1) OR (program_version_kind<>'initial' AND program_version_number>=2))"
        }
      ],
      "timestamp_participation": {
        "created_at": true
      },
      "unique_constraints": [
        [
          "program_ref",
          "program_version_ref"
        ],
        [
          "program_ref",
          "program_version_number"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-accepted-intent-revision.v1'",
          "constant": "governed-execution.nwp-development-accepted-intent-revision.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(accepted_intent_revision_number)='integer' AND accepted_intent_revision_number>=1",
          "constant": null,
          "enum_values": null,
          "logical_type": "positive_integer",
          "name": "accepted_intent_revision_number",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "prior_accepted_intent_revision_ref IS NULL OR (typeof(prior_accepted_intent_revision_ref)='text' AND length(prior_accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(prior_accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND prior_accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(prior_accepted_intent_revision_ref,1,instr(prior_accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "prior_accepted_intent_revision_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(source_intent_ref)='text' AND length(source_intent_ref) BETWEEN 1 AND 96 AND substr(source_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND source_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(source_intent_ref,1,instr(source_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "source_intent_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(source_intent_digest)='text' AND length(source_intent_digest)=64 AND source_intent_digest=lower(source_intent_digest) AND source_intent_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "source_intent_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(safe_projection_digest)='text' AND length(safe_projection_digest)=64 AND safe_projection_digest=lower(safe_projection_digest) AND safe_projection_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "safe_projection_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(accepted_intent_revision_digest)='text' AND length(accepted_intent_revision_digest)=64 AND accepted_intent_revision_digest=lower(accepted_intent_revision_digest) AND accepted_intent_revision_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "accepted_intent_revision_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "accepted_intent_revision_digest",
      "digest_domain": "governed-execution.nwp-development-accepted-intent-revision.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "accepted_intent_revision_ref",
        "program_ref",
        "accepted_intent_revision_number",
        "prior_accepted_intent_revision_ref",
        "source_intent_ref",
        "source_intent_digest",
        "safe_projection_digest",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "accepted_intent_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "prior_accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "accepted_intent_prior_revision"
        }
      ],
      "future_mutation_owner": "_initialize_development_program_or_replan",
      "immutable_triggers": [
        "development_accepted_intent_revisions_no_update",
        "development_accepted_intent_revisions_no_delete"
      ],
      "mutable": false,
      "name": "development_accepted_intent_revisions",
      "primary_key": [
        "accepted_intent_revision_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "accepted_intent_revision_by_exact_ref"
      ],
      "record_schema_id": "governed-execution.nwp-development-accepted-intent-revision.v1",
      "role": "accepted_intent_revision_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [
        {
          "name": "accepted_intent_prior_bidirectional",
          "sql": "((accepted_intent_revision_number=1 AND prior_accepted_intent_revision_ref IS NULL) OR (accepted_intent_revision_number>=2 AND prior_accepted_intent_revision_ref IS NOT NULL))"
        }
      ],
      "timestamp_participation": {
        "created_at": true
      },
      "unique_constraints": [
        [
          "program_ref",
          "accepted_intent_revision_ref"
        ],
        [
          "program_ref",
          "accepted_intent_revision_number"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-work-item-head.v1'",
          "constant": "governed-execution.nwp-development-work-item-head.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(current_work_item_revision_ref)='text' AND length(current_work_item_revision_ref) BETWEEN 1 AND 96 AND substr(current_work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND current_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(current_work_item_revision_ref,1,instr(current_work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "current_work_item_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(current_work_item_revision_number)='integer' AND current_work_item_revision_number>=1",
          "constant": null,
          "enum_values": null,
          "logical_type": "positive_integer",
          "name": "current_work_item_revision_number",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(head_revision)='integer' AND head_revision>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "head_revision",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_state)='text' AND work_state IN ('planned','active','accepted','repair_required','terminal_rejected','blocked')",
          "constant": null,
          "enum_values": [
            "planned",
            "active",
            "accepted",
            "repair_required",
            "terminal_rejected",
            "blocked"
          ],
          "logical_type": "closed_enum",
          "name": "work_state",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(updated_at)='text' AND length(updated_at)=20 AND updated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(updated_at,1,4) BETWEEN '0001' AND '9999' AND substr(updated_at,6,2) BETWEEN '01' AND '12' AND substr(updated_at,9,2) BETWEEN '01' AND '31' AND substr(updated_at,12,2) BETWEEN '00' AND '23' AND substr(updated_at,15,2) BETWEEN '00' AND '59' AND substr(updated_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at)=updated_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "updated_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(head_digest)='text' AND length(head_digest)=64 AND head_digest=lower(head_digest) AND head_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "head_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "head_digest",
      "digest_domain": "governed-execution.nwp-development-work-item-head.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "work_item_ref",
        "program_ref",
        "current_work_item_revision_ref",
        "current_work_item_revision_number",
        "head_revision",
        "work_state",
        "updated_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "work_item_head_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "current_work_item_revision_ref"
          ],
          "deferrability": "DEFERRABLE INITIALLY DEFERRED",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "work_item_head_current_revision"
        }
      ],
      "future_mutation_owner": "program_work_item_CAS",
      "immutable_triggers": [],
      "mutable": true,
      "name": "development_work_item_heads",
      "primary_key": [
        "work_item_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "work_item_head_and_revision_by_exact_ref"
      ],
      "record_schema_id": "governed-execution.nwp-development-work-item-head.v1",
      "role": "work_item_progression_head",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [],
      "timestamp_participation": {
        "updated_at": true
      },
      "unique_constraints": [
        [
          "program_ref",
          "work_item_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-work-item-revision.v1'",
          "constant": "governed-execution.nwp-development-work-item-revision.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_revision_number)='integer' AND work_item_revision_number>=1",
          "constant": null,
          "enum_values": null,
          "logical_type": "positive_integer",
          "name": "work_item_revision_number",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_revision_kind)='text' AND work_item_revision_kind IN ('initial','replan')",
          "constant": null,
          "enum_values": [
            "initial",
            "replan"
          ],
          "logical_type": "closed_enum",
          "name": "work_item_revision_kind",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "prior_work_item_revision_ref IS NULL OR (typeof(prior_work_item_revision_ref)='text' AND length(prior_work_item_revision_ref) BETWEEN 1 AND 96 AND substr(prior_work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND prior_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(prior_work_item_revision_ref,1,instr(prior_work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "prior_work_item_revision_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_revision_digest)='text' AND length(work_item_revision_digest)=64 AND work_item_revision_digest=lower(work_item_revision_digest) AND work_item_revision_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "work_item_revision_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "work_item_revision_digest",
      "digest_domain": "governed-execution.nwp-development-work-item-revision.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "work_item_revision_ref",
        "program_ref",
        "work_item_ref",
        "work_item_revision_number",
        "work_item_revision_kind",
        "prior_work_item_revision_ref",
        "accepted_intent_revision_ref",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref"
          ],
          "parent_table": "development_work_item_heads",
          "role": "work_item_revision_head"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "prior_work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "work_item_revision_prior"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "work_item_revision_accepted_intent"
        }
      ],
      "future_mutation_owner": "_initialize_development_program_or_replan",
      "immutable_triggers": [
        "development_work_item_revisions_no_update",
        "development_work_item_revisions_no_delete"
      ],
      "mutable": false,
      "name": "development_work_item_revisions",
      "primary_key": [
        "work_item_revision_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "work_item_head_and_revision_by_exact_ref"
      ],
      "record_schema_id": "governed-execution.nwp-development-work-item-revision.v1",
      "role": "work_item_revision_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [
        {
          "name": "work_revision_prior_bidirectional",
          "sql": "((work_item_revision_kind='initial' AND work_item_revision_number=1 AND prior_work_item_revision_ref IS NULL) OR (work_item_revision_kind='replan' AND work_item_revision_number>=2 AND prior_work_item_revision_ref IS NOT NULL))"
        }
      ],
      "timestamp_participation": {
        "created_at": true
      },
      "unique_constraints": [
        [
          "program_ref",
          "work_item_ref",
          "work_item_revision_ref"
        ],
        [
          "program_ref",
          "work_item_revision_ref"
        ],
        [
          "program_ref",
          "work_item_ref",
          "work_item_revision_number"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-program-version-work-item.v1'",
          "constant": "governed-execution.nwp-development-program-version-work-item.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": false,
          "pk_ordinal": 2,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": false,
          "pk_ordinal": 3,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(membership_ordinal)='integer' AND membership_ordinal>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "membership_ordinal",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(membership_digest)='text' AND length(membership_digest)=64 AND membership_digest=lower(membership_digest) AND membership_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "membership_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "membership_digest",
      "digest_domain": "governed-execution.nwp-development-program-version-work-item.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "program_ref",
        "program_version_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "membership_ordinal",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "membership_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "membership_work_item_revision"
        }
      ],
      "future_mutation_owner": "_initialize_development_program_or_replan",
      "immutable_triggers": [
        "development_program_version_work_items_no_update",
        "development_program_version_work_items_no_delete"
      ],
      "mutable": false,
      "name": "development_program_version_work_items",
      "primary_key": [
        "program_ref",
        "program_version_ref",
        "work_item_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "paged_program_version_membership"
      ],
      "record_schema_id": "governed-execution.nwp-development-program-version-work-item.v1",
      "role": "program_version_membership_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [],
      "timestamp_participation": {
        "created_at": true
      },
      "unique_constraints": [
        [
          "program_ref",
          "program_version_ref",
          "membership_ordinal"
        ]
      ]
    },
    {
      "c2b2_reader_treatment": "durable row representation only",
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-revision-edge.v1'",
          "constant": "governed-execution.nwp-development-revision-edge.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(revision_edge_ref)='text' AND length(revision_edge_ref) BETWEEN 1 AND 96 AND substr(revision_edge_ref,1,1) GLOB '[0-9A-Za-z]' AND revision_edge_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(revision_edge_ref,1,instr(revision_edge_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "revision_edge_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(relation_key_digest)='text' AND length(relation_key_digest)=64 AND relation_key_digest=lower(relation_key_digest) AND relation_key_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "relation_key_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(revision_edge_kind)='text' AND revision_edge_kind IN ('accepted_intent_supersedes','work_item_supersedes','work_item_split','work_item_merge')",
          "constant": null,
          "enum_values": [
            "accepted_intent_supersedes",
            "work_item_supersedes",
            "work_item_split",
            "work_item_merge"
          ],
          "logical_type": "closed_enum",
          "name": "revision_edge_kind",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "from_accepted_intent_revision_ref IS NULL OR (typeof(from_accepted_intent_revision_ref)='text' AND length(from_accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(from_accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND from_accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(from_accepted_intent_revision_ref,1,instr(from_accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "from_accepted_intent_revision_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "to_accepted_intent_revision_ref IS NULL OR (typeof(to_accepted_intent_revision_ref)='text' AND length(to_accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(to_accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND to_accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(to_accepted_intent_revision_ref,1,instr(to_accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "to_accepted_intent_revision_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "from_work_item_revision_ref IS NULL OR (typeof(from_work_item_revision_ref)='text' AND length(from_work_item_revision_ref) BETWEEN 1 AND 96 AND substr(from_work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND from_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(from_work_item_revision_ref,1,instr(from_work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "from_work_item_revision_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "to_work_item_revision_ref IS NULL OR (typeof(to_work_item_revision_ref)='text' AND length(to_work_item_revision_ref) BETWEEN 1 AND 96 AND substr(to_work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND to_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(to_work_item_revision_ref,1,instr(to_work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "to_work_item_revision_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(revision_edge_digest)='text' AND length(revision_edge_digest)=64 AND revision_edge_digest=lower(revision_edge_digest) AND revision_edge_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "revision_edge_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "revision_edge_digest",
      "digest_domain": "governed-execution.nwp-development-revision-edge.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "revision_edge_ref",
        "relation_key_digest",
        "program_ref",
        "revision_edge_kind",
        "from_accepted_intent_revision_ref",
        "to_accepted_intent_revision_ref",
        "from_work_item_revision_ref",
        "to_work_item_revision_ref",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "revision_edge_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "from_accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "revision_edge_from_accepted_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "to_accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "revision_edge_to_accepted_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "from_work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "revision_edge_from_work_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "to_work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "revision_edge_to_work_revision"
        }
      ],
      "future_mutation_owner": "_record_development_progression_decision",
      "future_reader_owner": "C2B6",
      "future_reader_owner_reason": "exact revision-edge selection is progression-family-specific and belongs to the C2B6 graph-locator/replay contract before C2B6 writers",
      "immutable_triggers": [
        "development_revision_edges_no_update",
        "development_revision_edges_no_delete"
      ],
      "mutable": false,
      "name": "development_revision_edges",
      "primary_key": [
        "revision_edge_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [],
      "record_schema_id": "governed-execution.nwp-development-revision-edge.v1",
      "role": "revision_edge_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [
        {
          "name": "revision_edge_endpoint_algebra",
          "sql": "((revision_edge_kind='accepted_intent_supersedes' AND from_accepted_intent_revision_ref IS NOT NULL AND to_accepted_intent_revision_ref IS NOT NULL AND from_work_item_revision_ref IS NULL AND to_work_item_revision_ref IS NULL) OR (revision_edge_kind IN ('work_item_supersedes','work_item_split','work_item_merge') AND from_accepted_intent_revision_ref IS NULL AND to_accepted_intent_revision_ref IS NULL AND from_work_item_revision_ref IS NOT NULL AND to_work_item_revision_ref IS NOT NULL))"
        }
      ],
      "timestamp_participation": {
        "created_at": true
      },
      "unique_constraints": [
        [
          "relation_key_digest"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-work-spec-binding.v1'",
          "constant": "governed-execution.nwp-development-work-spec-binding.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_spec_ref)='text' AND length(work_spec_ref) BETWEEN 1 AND 96 AND substr(work_spec_ref,1,1) GLOB '[0-9A-Za-z]' AND work_spec_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_spec_ref,1,instr(work_spec_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_spec_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(repository_ref)='text' AND length(repository_ref) BETWEEN 1 AND 96 AND substr(repository_ref,1,1) GLOB '[0-9A-Za-z]' AND repository_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(repository_ref,1,instr(repository_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "repository_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(base_git_object_format)='text' AND base_git_object_format='sha1'",
          "constant": "sha1",
          "enum_values": null,
          "logical_type": "constant_text",
          "name": "base_git_object_format",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(base_git_oid)='text' AND length(base_git_oid)=40 AND base_git_oid=lower(base_git_oid) AND base_git_oid NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "git_sha1_oid",
          "name": "base_git_oid",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": "[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]",
          "check_sql": "typeof(authorized_paths_json)='text' AND authorized_paths_json='[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]'",
          "constant": null,
          "enum_values": null,
          "logical_type": "canonical_json",
          "name": "authorized_paths_json",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(validation_requirement_ref)='text' AND length(validation_requirement_ref) BETWEEN 1 AND 96 AND substr(validation_requirement_ref,1,1) GLOB '[0-9A-Za-z]' AND validation_requirement_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(validation_requirement_ref,1,instr(validation_requirement_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "validation_requirement_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(review_requirement_ref)='text' AND length(review_requirement_ref) BETWEEN 1 AND 96 AND substr(review_requirement_ref,1,1) GLOB '[0-9A-Za-z]' AND review_requirement_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(review_requirement_ref,1,instr(review_requirement_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "review_requirement_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(privacy_classification)='text' AND privacy_classification='private_work_spec'",
          "constant": "private_work_spec",
          "enum_values": null,
          "logical_type": "constant_text",
          "name": "privacy_classification",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_spec_digest)='text' AND length(work_spec_digest)=64 AND work_spec_digest=lower(work_spec_digest) AND work_spec_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "work_spec_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(safe_projection_digest)='text' AND length(safe_projection_digest)=64 AND safe_projection_digest=lower(safe_projection_digest) AND safe_projection_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "safe_projection_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "recorded_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_spec_binding_digest)='text' AND length(work_spec_binding_digest)=64 AND work_spec_binding_digest=lower(work_spec_binding_digest) AND work_spec_binding_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "work_spec_binding_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "work_spec_binding_digest",
      "digest_domain": "governed-execution.nwp-development-work-spec-binding.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "work_spec_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "authorized_paths_json",
        "validation_requirement_ref",
        "review_requirement_ref",
        "privacy_classification",
        "work_spec_digest",
        "safe_projection_digest",
        "recorded_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "work_spec_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "work_spec_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "work_spec_work_item_revision"
        }
      ],
      "future_mutation_owner": "_initialize_development_program_or_replan",
      "immutable_triggers": [
        "development_work_spec_bindings_no_update",
        "development_work_spec_bindings_no_delete"
      ],
      "mutable": false,
      "name": "development_work_spec_bindings",
      "primary_key": [
        "work_spec_ref"
      ],
      "privacy_class": "safe_private_work_spec_projection",
      "reader_roles": [
        "work_spec_safe_binding"
      ],
      "record_schema_id": "governed-execution.nwp-development-work-spec-binding.v1",
      "role": "work_spec_binding_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [],
      "timestamp_participation": {
        "recorded_at": true,
        "safe_projection_digest": false
      },
      "unique_constraints": [
        [
          "program_ref",
          "program_version_ref",
          "work_item_ref",
          "work_item_revision_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-semantic-attempt.v1'",
          "constant": "governed-execution.nwp-development-semantic-attempt.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_number)='integer' AND attempt_number>=1",
          "constant": null,
          "enum_values": null,
          "logical_type": "positive_integer",
          "name": "attempt_number",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(candidate_ref)='text' AND length(candidate_ref) BETWEEN 1 AND 96 AND substr(candidate_ref,1,1) GLOB '[0-9A-Za-z]' AND candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(candidate_ref,1,instr(candidate_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "candidate_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_phase)='text' AND attempt_phase IN ('established')",
          "constant": null,
          "enum_values": [
            "established"
          ],
          "logical_type": "closed_enum",
          "name": "attempt_phase",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(selection_decision_ref)='text' AND length(selection_decision_ref) BETWEEN 1 AND 96 AND substr(selection_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND selection_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(selection_decision_ref,1,instr(selection_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "selection_decision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(semantic_attempt_digest)='text' AND length(semantic_attempt_digest)=64 AND semantic_attempt_digest=lower(semantic_attempt_digest) AND semantic_attempt_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "semantic_attempt_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "semantic_attempt_digest",
      "digest_domain": "governed-execution.nwp-development-semantic-attempt.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "semantic_attempt_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "attempt_number",
        "candidate_ref",
        "attempt_phase",
        "selection_decision_ref",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "semantic_attempt_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "semantic_attempt_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "semantic_attempt_work_item_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "selection_decision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "semantic_attempt_selection_decision"
        }
      ],
      "future_mutation_owner": "_establish_development_author_effect_intent",
      "immutable_triggers": [
        "development_semantic_attempts_no_update",
        "development_semantic_attempts_no_delete"
      ],
      "mutable": false,
      "name": "development_semantic_attempts",
      "primary_key": [
        "semantic_attempt_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "attempt_fence_command_effect_aggregate"
      ],
      "record_schema_id": "governed-execution.nwp-development-semantic-attempt.v1",
      "role": "semantic_attempt_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [],
      "timestamp_participation": {
        "created_at": true
      },
      "unique_constraints": [
        [
          "program_ref",
          "semantic_attempt_ref"
        ],
        [
          "program_ref",
          "candidate_ref"
        ],
        [
          "program_ref",
          "work_item_ref",
          "attempt_number"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-attempt-fence.v1'",
          "constant": "governed-execution.nwp-attempt-fence.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_fence_ref)='text' AND length(attempt_fence_ref) BETWEEN 1 AND 96 AND substr(attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(attempt_fence_ref,1,instr(attempt_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "attempt_fence_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(parent_standing_grant_ref)='text' AND length(parent_standing_grant_ref) BETWEEN 1 AND 96 AND substr(parent_standing_grant_ref,1,1) GLOB '[0-9A-Za-z]' AND parent_standing_grant_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(parent_standing_grant_ref,1,instr(parent_standing_grant_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "parent_standing_grant_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(parent_standing_grant_digest)='text' AND length(parent_standing_grant_digest)=64 AND parent_standing_grant_digest=lower(parent_standing_grant_digest) AND parent_standing_grant_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "parent_standing_grant_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_authorization_ref)='text' AND length(attempt_authorization_ref) BETWEEN 1 AND 96 AND substr(attempt_authorization_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_authorization_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(attempt_authorization_ref,1,instr(attempt_authorization_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "attempt_authorization_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_authorization_digest)='text' AND length(attempt_authorization_digest)=64 AND attempt_authorization_digest=lower(attempt_authorization_digest) AND attempt_authorization_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "attempt_authorization_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(repository_ref)='text' AND length(repository_ref) BETWEEN 1 AND 96 AND substr(repository_ref,1,1) GLOB '[0-9A-Za-z]' AND repository_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(repository_ref,1,instr(repository_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "repository_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(base_git_object_format)='text' AND base_git_object_format='sha1'",
          "constant": "sha1",
          "enum_values": null,
          "logical_type": "constant_text",
          "name": "base_git_object_format",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(base_git_oid)='text' AND length(base_git_oid)=40 AND base_git_oid=lower(base_git_oid) AND base_git_oid NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "git_sha1_oid",
          "name": "base_git_oid",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": "[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]",
          "check_sql": "typeof(path_ceiling_json)='text' AND path_ceiling_json='[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]'",
          "constant": null,
          "enum_values": null,
          "logical_type": "canonical_json",
          "name": "path_ceiling_json",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(allowed_effect_class_mask)='integer' AND allowed_effect_class_mask BETWEEN 1 AND 31",
          "constant": null,
          "enum_values": null,
          "logical_type": "effect_class_mask",
          "name": "allowed_effect_class_mask",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_active_invocations)='integer' AND aggregate_max_active_invocations>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_active_invocations",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_candidate_bytes)='integer' AND aggregate_max_candidate_bytes>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_candidate_bytes",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_changed_files)='integer' AND aggregate_max_changed_files>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_changed_files",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_cost_microusd)='integer' AND aggregate_max_cost_microusd>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_cost_microusd",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_cpu_seconds)='integer' AND aggregate_max_cpu_seconds>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_cpu_seconds",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_deliveries)='integer' AND aggregate_max_deliveries>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_deliveries",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_deployments)='integer' AND aggregate_max_deployments>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_deployments",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_local_commits)='integer' AND aggregate_max_local_commits>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_local_commits",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_memory_bytes)='integer' AND aggregate_max_memory_bytes>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_memory_bytes",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_merges)='integer' AND aggregate_max_merges>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_merges",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_model_input_tokens)='integer' AND aggregate_max_model_input_tokens>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_model_input_tokens",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_model_output_tokens)='integer' AND aggregate_max_model_output_tokens>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_model_output_tokens",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_pull_requests)='integer' AND aggregate_max_pull_requests>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_pull_requests",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_pushes)='integer' AND aggregate_max_pushes>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_pushes",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(aggregate_max_wall_seconds)='integer' AND aggregate_max_wall_seconds>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_wall_seconds",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(expires_at)='text' AND length(expires_at)=20 AND expires_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(expires_at,1,4) BETWEEN '0001' AND '9999' AND substr(expires_at,6,2) BETWEEN '01' AND '12' AND substr(expires_at,9,2) BETWEEN '01' AND '31' AND substr(expires_at,12,2) BETWEEN '00' AND '23' AND substr(expires_at,15,2) BETWEEN '00' AND '59' AND substr(expires_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',expires_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',expires_at)=expires_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "expires_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(global_stop_ref)='text' AND length(global_stop_ref) BETWEEN 1 AND 96 AND substr(global_stop_ref,1,1) GLOB '[0-9A-Za-z]' AND global_stop_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(global_stop_ref,1,instr(global_stop_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "global_stop_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(global_stop_version)='integer' AND global_stop_version>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "global_stop_version",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_fence_digest)='text' AND length(attempt_fence_digest)=64 AND attempt_fence_digest=lower(attempt_fence_digest) AND attempt_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "attempt_fence_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "recorded_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "attempt_fence_digest",
      "digest_domain": "governed-execution.nwp-attempt-fence.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "attempt_fence_ref",
        "parent_standing_grant_ref",
        "parent_standing_grant_digest",
        "attempt_authorization_ref",
        "attempt_authorization_digest",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "path_ceiling_json",
        "allowed_effect_class_mask",
        "aggregate_max_active_invocations",
        "aggregate_max_candidate_bytes",
        "aggregate_max_changed_files",
        "aggregate_max_cost_microusd",
        "aggregate_max_cpu_seconds",
        "aggregate_max_deliveries",
        "aggregate_max_deployments",
        "aggregate_max_local_commits",
        "aggregate_max_memory_bytes",
        "aggregate_max_merges",
        "aggregate_max_model_input_tokens",
        "aggregate_max_model_output_tokens",
        "aggregate_max_pull_requests",
        "aggregate_max_pushes",
        "aggregate_max_wall_seconds",
        "expires_at",
        "global_stop_ref",
        "global_stop_version"
      ],
      "excluded_operational_fields": [
        "recorded_at"
      ],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "attempt_fence_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "attempt_fence_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "attempt_fence_work_item_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "attempt_fence_semantic_attempt"
        }
      ],
      "future_mutation_owner": "_establish_development_author_effect_intent",
      "immutable_triggers": [
        "development_attempt_fences_no_update",
        "development_attempt_fences_no_delete"
      ],
      "mutable": false,
      "name": "development_attempt_fences",
      "primary_key": [
        "attempt_fence_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "attempt_fence_command_effect_aggregate"
      ],
      "record_schema_id": "governed-execution.nwp-attempt-fence.v1",
      "role": "attempt_fence_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [],
      "timestamp_participation": {
        "expires_at": true,
        "recorded_at": false
      },
      "unique_constraints": [
        [
          "program_ref",
          "attempt_fence_ref"
        ],
        [
          "program_ref",
          "semantic_attempt_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-authority-evaluation.v1'",
          "constant": "governed-execution.nwp-development-authority-evaluation.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(authority_evaluation_ref)='text' AND length(authority_evaluation_ref) BETWEEN 1 AND 96 AND substr(authority_evaluation_ref,1,1) GLOB '[0-9A-Za-z]' AND authority_evaluation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(authority_evaluation_ref,1,instr(authority_evaluation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "authority_evaluation_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(evaluation_scope)='text' AND evaluation_scope IN ('attempt','effect')",
          "constant": null,
          "enum_values": [
            "attempt",
            "effect"
          ],
          "logical_type": "closed_enum",
          "name": "evaluation_scope",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(evaluation_subject_ref)='text' AND length(evaluation_subject_ref) BETWEEN 1 AND 96 AND substr(evaluation_subject_ref,1,1) GLOB '[0-9A-Za-z]' AND evaluation_subject_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(evaluation_subject_ref,1,instr(evaluation_subject_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "evaluation_subject_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "semantic_attempt_ref IS NULL OR (typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "effect_intent_ref IS NULL OR (typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(authority_ref)='text' AND length(authority_ref) BETWEEN 1 AND 96 AND substr(authority_ref,1,1) GLOB '[0-9A-Za-z]' AND authority_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(authority_ref,1,instr(authority_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "authority_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(authority_digest)='text' AND length(authority_digest)=64 AND authority_digest=lower(authority_digest) AND authority_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "authority_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(authority_state)='text' AND authority_state IN ('pending','verified','blocked','stale','revoked','expired')",
          "constant": null,
          "enum_values": [
            "pending",
            "verified",
            "blocked",
            "stale",
            "revoked",
            "expired"
          ],
          "logical_type": "closed_enum",
          "name": "authority_state",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(reason_code)='text' AND length(reason_code) BETWEEN 1 AND 96 AND substr(reason_code,1,1) GLOB '[a-z]' AND reason_code NOT GLOB '*[^a-z0-9_.-]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "reason_code",
          "name": "reason_code",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "expires_at IS NULL OR (typeof(expires_at)='text' AND length(expires_at)=20 AND expires_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(expires_at,1,4) BETWEEN '0001' AND '9999' AND substr(expires_at,6,2) BETWEEN '01' AND '12' AND substr(expires_at,9,2) BETWEEN '01' AND '31' AND substr(expires_at,12,2) BETWEEN '00' AND '23' AND substr(expires_at,15,2) BETWEEN '00' AND '59' AND substr(expires_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',expires_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',expires_at)=expires_at)",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "expires_at",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(evaluated_at)='text' AND length(evaluated_at)=20 AND evaluated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(evaluated_at,1,4) BETWEEN '0001' AND '9999' AND substr(evaluated_at,6,2) BETWEEN '01' AND '12' AND substr(evaluated_at,9,2) BETWEEN '01' AND '31' AND substr(evaluated_at,12,2) BETWEEN '00' AND '23' AND substr(evaluated_at,15,2) BETWEEN '00' AND '59' AND substr(evaluated_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',evaluated_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',evaluated_at)=evaluated_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "evaluated_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(authority_evaluation_digest)='text' AND length(authority_evaluation_digest)=64 AND authority_evaluation_digest=lower(authority_evaluation_digest) AND authority_evaluation_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "authority_evaluation_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "authority_evaluation_digest",
      "digest_domain": "governed-execution.nwp-development-authority-evaluation.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "authority_evaluation_ref",
        "program_ref",
        "evaluation_scope",
        "evaluation_subject_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "authority_ref",
        "authority_digest",
        "authority_state",
        "reason_code",
        "expires_at",
        "evaluated_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "authority_evaluation_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "authority_evaluation_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "authority_evaluation_effect_intent"
        }
      ],
      "future_mutation_owner": "effect_establishment_authority_binding",
      "immutable_triggers": [
        "development_authority_evaluations_no_update",
        "development_authority_evaluations_no_delete"
      ],
      "mutable": false,
      "name": "development_authority_evaluations",
      "primary_key": [
        "authority_evaluation_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "authority_evaluation_by_exact_ref"
      ],
      "record_schema_id": "governed-execution.nwp-development-authority-evaluation.v1",
      "role": "authority_evaluation_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [
        {
          "name": "authority_scope_subject_algebra",
          "sql": "((evaluation_scope='attempt' AND semantic_attempt_ref IS NOT NULL AND effect_intent_ref IS NULL AND evaluation_subject_ref=semantic_attempt_ref) OR (evaluation_scope='effect' AND semantic_attempt_ref IS NULL AND effect_intent_ref IS NOT NULL AND evaluation_subject_ref=effect_intent_ref))"
        },
        {
          "name": "authority_expiry_algebra",
          "sql": "((authority_state IN ('verified','expired') AND expires_at IS NOT NULL) OR (authority_state IN ('pending','blocked','stale','revoked') AND expires_at IS NULL))"
        }
      ],
      "timestamp_participation": {
        "evaluated_at": true,
        "expires_at": true
      },
      "unique_constraints": [
        [
          "program_ref",
          "authority_evaluation_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-effect-intent.v1'",
          "constant": "governed-execution.nwp-development-effect-intent.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_class)='text' AND effect_class IN ('author_candidate','cancel_effect','local_git_commit','review_candidate','validate_candidate')",
          "constant": null,
          "enum_values": [
            "author_candidate",
            "cancel_effect",
            "local_git_commit",
            "review_candidate",
            "validate_candidate"
          ],
          "logical_type": "closed_enum",
          "name": "effect_class",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(candidate_ref)='text' AND length(candidate_ref) BETWEEN 1 AND 96 AND substr(candidate_ref,1,1) GLOB '[0-9A-Za-z]' AND candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(candidate_ref,1,instr(candidate_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "candidate_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(command_ref)='text' AND length(command_ref) BETWEEN 1 AND 96 AND substr(command_ref,1,1) GLOB '[0-9A-Za-z]' AND command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(command_ref,1,instr(command_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "command_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(basis_decision_ref)='text' AND length(basis_decision_ref) BETWEEN 1 AND 96 AND substr(basis_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND basis_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(basis_decision_ref,1,instr(basis_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "basis_decision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "cancellation_target_effect_intent_ref IS NULL OR (typeof(cancellation_target_effect_intent_ref)='text' AND length(cancellation_target_effect_intent_ref) BETWEEN 1 AND 96 AND substr(cancellation_target_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND cancellation_target_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(cancellation_target_effect_intent_ref,1,instr(cancellation_target_effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "cancellation_target_effect_intent_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "expected_target_effect_head_revision IS NULL OR (typeof(expected_target_effect_head_revision)='integer' AND expected_target_effect_head_revision>=0)",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "expected_target_effect_head_revision",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "portable_capsule_digest IS NULL OR (typeof(portable_capsule_digest)='text' AND length(portable_capsule_digest)=64 AND portable_capsule_digest=lower(portable_capsule_digest) AND portable_capsule_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "portable_capsule_digest",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_intent_digest)='text' AND length(effect_intent_digest)=64 AND effect_intent_digest=lower(effect_intent_digest) AND effect_intent_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "effect_intent_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "effect_intent_digest",
      "digest_domain": "governed-execution.nwp-development-effect-intent.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "effect_intent_ref",
        "program_ref",
        "program_version_ref",
        "semantic_attempt_ref",
        "effect_class",
        "candidate_ref",
        "command_ref",
        "basis_decision_ref",
        "cancellation_target_effect_intent_ref",
        "expected_target_effect_head_revision",
        "portable_capsule_digest",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [
        "uq_development_effect_intents_author_command"
      ],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "effect_intent_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "effect_intent_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Require equal program_ref, exact basis decision identity/digest, and basis-kind coherence; mismatch is database_integrity_failure.",
          "child_columns": [
            "basis_decision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "effect_intent_basis_decision_owner_exception"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "command_ref"
          ],
          "deferrability": "DEFERRABLE INITIALLY DEFERRED",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "command_ref"
          ],
          "parent_table": "development_author_commands",
          "role": "author_effect_intent_command"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "cancellation_target_effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "cancellation_target_effect_intent"
        }
      ],
      "future_mutation_owner": "effect_establishment",
      "immutable_triggers": [
        "development_effect_intents_no_update",
        "development_effect_intents_no_delete"
      ],
      "mutable": false,
      "name": "development_effect_intents",
      "primary_key": [
        "effect_intent_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "attempt_fence_command_effect_aggregate"
      ],
      "record_schema_id": "governed-execution.nwp-development-effect-intent.v1",
      "role": "effect_intent_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [
        {
          "name": "effect_intent_cancellation_algebra",
          "sql": "((effect_class='cancel_effect' AND cancellation_target_effect_intent_ref IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL) OR (effect_class<>'cancel_effect' AND cancellation_target_effect_intent_ref IS NULL AND expected_target_effect_head_revision IS NULL))"
        },
        {
          "name": "effect_intent_capsule_algebra",
          "sql": "((effect_class='author_candidate' AND portable_capsule_digest IS NULL) OR (effect_class IN ('validate_candidate','review_candidate','local_git_commit') AND portable_capsule_digest IS NOT NULL) OR effect_class='cancel_effect')"
        }
      ],
      "timestamp_participation": {
        "created_at": true
      },
      "unique_constraints": [
        [
          "program_ref",
          "effect_intent_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-effect-fence.v1'",
          "constant": "governed-execution.nwp-effect-fence.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_fence_ref)='text' AND length(effect_fence_ref) BETWEEN 1 AND 96 AND substr(effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_fence_ref,1,instr(effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "effect_fence_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(parent_standing_grant_ref)='text' AND length(parent_standing_grant_ref) BETWEEN 1 AND 96 AND substr(parent_standing_grant_ref,1,1) GLOB '[0-9A-Za-z]' AND parent_standing_grant_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(parent_standing_grant_ref,1,instr(parent_standing_grant_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "parent_standing_grant_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(parent_standing_grant_digest)='text' AND length(parent_standing_grant_digest)=64 AND parent_standing_grant_digest=lower(parent_standing_grant_digest) AND parent_standing_grant_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "parent_standing_grant_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_authorization_ref)='text' AND length(effect_authorization_ref) BETWEEN 1 AND 96 AND substr(effect_authorization_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_authorization_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_authorization_ref,1,instr(effect_authorization_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "effect_authorization_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_authorization_digest)='text' AND length(effect_authorization_digest)=64 AND effect_authorization_digest=lower(effect_authorization_digest) AND effect_authorization_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "effect_authorization_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_fence_ref)='text' AND length(attempt_fence_ref) BETWEEN 1 AND 96 AND substr(attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(attempt_fence_ref,1,instr(attempt_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "attempt_fence_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_fence_digest)='text' AND length(attempt_fence_digest)=64 AND attempt_fence_digest=lower(attempt_fence_digest) AND attempt_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "attempt_fence_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_class)='text' AND effect_class IN ('author_candidate','cancel_effect','local_git_commit','review_candidate','validate_candidate')",
          "constant": null,
          "enum_values": [
            "author_candidate",
            "cancel_effect",
            "local_git_commit",
            "review_candidate",
            "validate_candidate"
          ],
          "logical_type": "closed_enum",
          "name": "effect_class",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(command_ref)='text' AND length(command_ref) BETWEEN 1 AND 96 AND substr(command_ref,1,1) GLOB '[0-9A-Za-z]' AND command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(command_ref,1,instr(command_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "command_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(command_digest)='text' AND length(command_digest)=64 AND command_digest=lower(command_digest) AND command_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "command_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(candidate_ref)='text' AND length(candidate_ref) BETWEEN 1 AND 96 AND substr(candidate_ref,1,1) GLOB '[0-9A-Za-z]' AND candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(candidate_ref,1,instr(candidate_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "candidate_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(repository_ref)='text' AND length(repository_ref) BETWEEN 1 AND 96 AND substr(repository_ref,1,1) GLOB '[0-9A-Za-z]' AND repository_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(repository_ref,1,instr(repository_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "repository_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(base_git_object_format)='text' AND base_git_object_format='sha1'",
          "constant": "sha1",
          "enum_values": null,
          "logical_type": "constant_text",
          "name": "base_git_object_format",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(base_git_oid)='text' AND length(base_git_oid)=40 AND base_git_oid=lower(base_git_oid) AND base_git_oid NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "git_sha1_oid",
          "name": "base_git_oid",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": "[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]",
          "check_sql": "typeof(path_ceiling_json)='text' AND path_ceiling_json='[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]'",
          "constant": null,
          "enum_values": null,
          "logical_type": "canonical_json",
          "name": "path_ceiling_json",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_active_invocations)='integer' AND effect_max_active_invocations>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_active_invocations",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_candidate_bytes)='integer' AND effect_max_candidate_bytes>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_candidate_bytes",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_changed_files)='integer' AND effect_max_changed_files>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_changed_files",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_cost_microusd)='integer' AND effect_max_cost_microusd>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_cost_microusd",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_cpu_seconds)='integer' AND effect_max_cpu_seconds>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_cpu_seconds",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_deliveries)='integer' AND effect_max_deliveries>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_deliveries",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_deployments)='integer' AND effect_max_deployments>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_deployments",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_local_commits)='integer' AND effect_max_local_commits>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_local_commits",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_memory_bytes)='integer' AND effect_max_memory_bytes>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_memory_bytes",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_merges)='integer' AND effect_max_merges>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_merges",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_model_input_tokens)='integer' AND effect_max_model_input_tokens>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_model_input_tokens",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_model_output_tokens)='integer' AND effect_max_model_output_tokens>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_model_output_tokens",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_pull_requests)='integer' AND effect_max_pull_requests>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_pull_requests",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_pushes)='integer' AND effect_max_pushes>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_pushes",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_wall_seconds)='integer' AND effect_max_wall_seconds>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_wall_seconds",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(expires_at)='text' AND length(expires_at)=20 AND expires_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(expires_at,1,4) BETWEEN '0001' AND '9999' AND substr(expires_at,6,2) BETWEEN '01' AND '12' AND substr(expires_at,9,2) BETWEEN '01' AND '31' AND substr(expires_at,12,2) BETWEEN '00' AND '23' AND substr(expires_at,15,2) BETWEEN '00' AND '59' AND substr(expires_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',expires_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',expires_at)=expires_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "expires_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(global_stop_ref)='text' AND length(global_stop_ref) BETWEEN 1 AND 96 AND substr(global_stop_ref,1,1) GLOB '[0-9A-Za-z]' AND global_stop_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(global_stop_ref,1,instr(global_stop_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "global_stop_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(global_stop_version)='integer' AND global_stop_version>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "global_stop_version",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "portable_capsule_digest IS NULL OR (typeof(portable_capsule_digest)='text' AND length(portable_capsule_digest)=64 AND portable_capsule_digest=lower(portable_capsule_digest) AND portable_capsule_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "portable_capsule_digest",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "cancellation_target_effect_intent_ref IS NULL OR (typeof(cancellation_target_effect_intent_ref)='text' AND length(cancellation_target_effect_intent_ref) BETWEEN 1 AND 96 AND substr(cancellation_target_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND cancellation_target_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(cancellation_target_effect_intent_ref,1,instr(cancellation_target_effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "cancellation_target_effect_intent_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "cancellation_target_effect_fence_ref IS NULL OR (typeof(cancellation_target_effect_fence_ref)='text' AND length(cancellation_target_effect_fence_ref) BETWEEN 1 AND 96 AND substr(cancellation_target_effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND cancellation_target_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(cancellation_target_effect_fence_ref,1,instr(cancellation_target_effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "cancellation_target_effect_fence_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "cancellation_target_effect_fence_digest IS NULL OR (typeof(cancellation_target_effect_fence_digest)='text' AND length(cancellation_target_effect_fence_digest)=64 AND cancellation_target_effect_fence_digest=lower(cancellation_target_effect_fence_digest) AND cancellation_target_effect_fence_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "cancellation_target_effect_fence_digest",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_fence_digest)='text' AND length(effect_fence_digest)=64 AND effect_fence_digest=lower(effect_fence_digest) AND effect_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "effect_fence_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "recorded_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "effect_fence_digest",
      "digest_domain": "governed-execution.nwp-effect-fence.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "effect_fence_ref",
        "parent_standing_grant_ref",
        "parent_standing_grant_digest",
        "effect_authorization_ref",
        "effect_authorization_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "effect_class",
        "command_ref",
        "command_digest",
        "candidate_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "path_ceiling_json",
        "effect_max_active_invocations",
        "effect_max_candidate_bytes",
        "effect_max_changed_files",
        "effect_max_cost_microusd",
        "effect_max_cpu_seconds",
        "effect_max_deliveries",
        "effect_max_deployments",
        "effect_max_local_commits",
        "effect_max_memory_bytes",
        "effect_max_merges",
        "effect_max_model_input_tokens",
        "effect_max_model_output_tokens",
        "effect_max_pull_requests",
        "effect_max_pushes",
        "effect_max_wall_seconds",
        "expires_at",
        "global_stop_ref",
        "global_stop_version",
        "portable_capsule_digest",
        "cancellation_target_effect_intent_ref",
        "cancellation_target_effect_fence_ref",
        "cancellation_target_effect_fence_digest"
      ],
      "excluded_operational_fields": [
        "recorded_at"
      ],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "effect_fence_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "effect_fence_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "effect_fence_work_item_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "effect_fence_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "effect_fence_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "parent_table": "development_attempt_fences",
          "role": "effect_fence_attempt_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "command_ref"
          ],
          "deferrability": "DEFERRABLE INITIALLY DEFERRED",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "command_ref"
          ],
          "parent_table": "development_author_commands",
          "role": "author_effect_fence_command"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "cancellation_target_effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "effect_fence_cancellation_target_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "cancellation_target_effect_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "parent_table": "development_effect_fences",
          "role": "effect_fence_cancellation_target_fence"
        }
      ],
      "future_mutation_owner": "effect_establishment",
      "immutable_triggers": [
        "development_effect_fences_no_update",
        "development_effect_fences_no_delete"
      ],
      "mutable": false,
      "name": "development_effect_fences",
      "primary_key": [
        "effect_fence_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "attempt_fence_command_effect_aggregate"
      ],
      "record_schema_id": "governed-execution.nwp-effect-fence.v1",
      "role": "effect_fence_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [
        {
          "name": "effect_fence_cancellation_algebra",
          "sql": "((effect_class='cancel_effect' AND cancellation_target_effect_intent_ref IS NOT NULL AND cancellation_target_effect_fence_ref IS NOT NULL AND cancellation_target_effect_fence_digest IS NOT NULL) OR (effect_class<>'cancel_effect' AND cancellation_target_effect_intent_ref IS NULL AND cancellation_target_effect_fence_ref IS NULL AND cancellation_target_effect_fence_digest IS NULL))"
        },
        {
          "name": "effect_fence_capsule_algebra",
          "sql": "((effect_class='author_candidate' AND portable_capsule_digest IS NULL) OR (effect_class IN ('validate_candidate','review_candidate','local_git_commit') AND portable_capsule_digest IS NOT NULL) OR effect_class='cancel_effect')"
        }
      ],
      "timestamp_participation": {
        "expires_at": true,
        "recorded_at": false
      },
      "unique_constraints": [
        [
          "program_ref",
          "effect_fence_ref"
        ],
        [
          "program_ref",
          "effect_intent_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-worker-command.v1'",
          "constant": "governed-execution.nwp-worker-command.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(command_ref)='text' AND length(command_ref) BETWEEN 1 AND 96 AND substr(command_ref,1,1) GLOB '[0-9A-Za-z]' AND command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(command_ref,1,instr(command_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "command_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_class)='text' AND effect_class='author_candidate'",
          "constant": "author_candidate",
          "enum_values": null,
          "logical_type": "constant_text",
          "name": "effect_class",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(candidate_ref)='text' AND length(candidate_ref) BETWEEN 1 AND 96 AND substr(candidate_ref,1,1) GLOB '[0-9A-Za-z]' AND candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(candidate_ref,1,instr(candidate_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "candidate_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(repository_ref)='text' AND length(repository_ref) BETWEEN 1 AND 96 AND substr(repository_ref,1,1) GLOB '[0-9A-Za-z]' AND repository_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(repository_ref,1,instr(repository_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "repository_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(base_git_object_format)='text' AND base_git_object_format='sha1'",
          "constant": "sha1",
          "enum_values": null,
          "logical_type": "constant_text",
          "name": "base_git_object_format",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(base_git_oid)='text' AND length(base_git_oid)=40 AND base_git_oid=lower(base_git_oid) AND base_git_oid NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "git_sha1_oid",
          "name": "base_git_oid",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": "[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]",
          "check_sql": "typeof(path_ceiling_json)='text' AND path_ceiling_json='[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]'",
          "constant": null,
          "enum_values": null,
          "logical_type": "canonical_json",
          "name": "path_ceiling_json",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_spec_ref)='text' AND length(work_spec_ref) BETWEEN 1 AND 96 AND substr(work_spec_ref,1,1) GLOB '[0-9A-Za-z]' AND work_spec_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_spec_ref,1,instr(work_spec_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "work_spec_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(work_spec_digest)='text' AND length(work_spec_digest)=64 AND work_spec_digest=lower(work_spec_digest) AND work_spec_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "work_spec_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(standing_grant_ref)='text' AND length(standing_grant_ref) BETWEEN 1 AND 96 AND substr(standing_grant_ref,1,1) GLOB '[0-9A-Za-z]' AND standing_grant_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(standing_grant_ref,1,instr(standing_grant_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "standing_grant_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(standing_grant_digest)='text' AND length(standing_grant_digest)=64 AND standing_grant_digest=lower(standing_grant_digest) AND standing_grant_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "standing_grant_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_authorization_ref)='text' AND length(attempt_authorization_ref) BETWEEN 1 AND 96 AND substr(attempt_authorization_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_authorization_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(attempt_authorization_ref,1,instr(attempt_authorization_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "attempt_authorization_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_authorization_digest)='text' AND length(attempt_authorization_digest)=64 AND attempt_authorization_digest=lower(attempt_authorization_digest) AND attempt_authorization_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "attempt_authorization_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_authorization_ref)='text' AND length(effect_authorization_ref) BETWEEN 1 AND 96 AND substr(effect_authorization_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_authorization_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_authorization_ref,1,instr(effect_authorization_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "effect_authorization_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_authorization_digest)='text' AND length(effect_authorization_digest)=64 AND effect_authorization_digest=lower(effect_authorization_digest) AND effect_authorization_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "effect_authorization_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_fence_ref)='text' AND length(attempt_fence_ref) BETWEEN 1 AND 96 AND substr(attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(attempt_fence_ref,1,instr(attempt_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "attempt_fence_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_fence_digest)='text' AND length(attempt_fence_digest)=64 AND attempt_fence_digest=lower(attempt_fence_digest) AND attempt_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "attempt_fence_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_fence_ref)='text' AND length(effect_fence_ref) BETWEEN 1 AND 96 AND substr(effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_fence_ref,1,instr(effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "effect_fence_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_fence_digest)='text' AND length(effect_fence_digest)=64 AND effect_fence_digest=lower(effect_fence_digest) AND effect_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "effect_fence_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(global_stop_ref)='text' AND length(global_stop_ref) BETWEEN 1 AND 96 AND substr(global_stop_ref,1,1) GLOB '[0-9A-Za-z]' AND global_stop_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(global_stop_ref,1,instr(global_stop_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "global_stop_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(global_stop_version)='integer' AND global_stop_version>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "global_stop_version",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(validation_requirement_ref)='text' AND length(validation_requirement_ref) BETWEEN 1 AND 96 AND substr(validation_requirement_ref,1,1) GLOB '[0-9A-Za-z]' AND validation_requirement_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(validation_requirement_ref,1,instr(validation_requirement_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "validation_requirement_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(validation_requirement_digest)='text' AND length(validation_requirement_digest)=64 AND validation_requirement_digest=lower(validation_requirement_digest) AND validation_requirement_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "validation_requirement_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(review_requirement_ref)='text' AND length(review_requirement_ref) BETWEEN 1 AND 96 AND substr(review_requirement_ref,1,1) GLOB '[0-9A-Za-z]' AND review_requirement_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(review_requirement_ref,1,instr(review_requirement_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "review_requirement_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(review_requirement_digest)='text' AND length(review_requirement_digest)=64 AND review_requirement_digest=lower(review_requirement_digest) AND review_requirement_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "review_requirement_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(capsule_schema_id)='text' AND capsule_schema_id='governed-execution.nwp-candidate-capsule-manifest.v1'",
          "constant": "governed-execution.nwp-candidate-capsule-manifest.v1",
          "enum_values": null,
          "logical_type": "constant_text",
          "name": "capsule_schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(capsule_profile_ref)='text' AND length(capsule_profile_ref) BETWEEN 1 AND 96 AND substr(capsule_profile_ref,1,1) GLOB '[0-9A-Za-z]' AND capsule_profile_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(capsule_profile_ref,1,instr(capsule_profile_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "capsule_profile_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_active_invocations)='integer' AND effect_max_active_invocations>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_active_invocations",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_candidate_bytes)='integer' AND effect_max_candidate_bytes>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_candidate_bytes",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_changed_files)='integer' AND effect_max_changed_files>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_changed_files",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_cost_microusd)='integer' AND effect_max_cost_microusd>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_cost_microusd",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_cpu_seconds)='integer' AND effect_max_cpu_seconds>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_cpu_seconds",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_deliveries)='integer' AND effect_max_deliveries>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_deliveries",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_deployments)='integer' AND effect_max_deployments>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_deployments",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_local_commits)='integer' AND effect_max_local_commits>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_local_commits",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_memory_bytes)='integer' AND effect_max_memory_bytes>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_memory_bytes",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_merges)='integer' AND effect_max_merges>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_merges",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_model_input_tokens)='integer' AND effect_max_model_input_tokens>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_model_input_tokens",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_model_output_tokens)='integer' AND effect_max_model_output_tokens>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_model_output_tokens",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_pull_requests)='integer' AND effect_max_pull_requests>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_pull_requests",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_pushes)='integer' AND effect_max_pushes>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_pushes",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_max_wall_seconds)='integer' AND effect_max_wall_seconds>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_wall_seconds",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(privacy_classification)='text' AND privacy_classification='private_source_change'",
          "constant": "private_source_change",
          "enum_values": null,
          "logical_type": "constant_text",
          "name": "privacy_classification",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(redaction_profile_ref)='text' AND length(redaction_profile_ref) BETWEEN 1 AND 96 AND substr(redaction_profile_ref,1,1) GLOB '[0-9A-Za-z]' AND redaction_profile_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(redaction_profile_ref,1,instr(redaction_profile_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "redaction_profile_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(command_digest)='text' AND length(command_digest)=64 AND command_digest=lower(command_digest) AND command_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "command_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "recorded_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "command_digest",
      "digest_domain": "governed-execution.nwp-worker-command.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "command_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "effect_class",
        "candidate_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "path_ceiling_json",
        "work_spec_ref",
        "work_spec_digest",
        "standing_grant_ref",
        "standing_grant_digest",
        "attempt_authorization_ref",
        "attempt_authorization_digest",
        "effect_authorization_ref",
        "effect_authorization_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "global_stop_ref",
        "global_stop_version",
        "validation_requirement_ref",
        "validation_requirement_digest",
        "review_requirement_ref",
        "review_requirement_digest",
        "capsule_schema_id",
        "capsule_profile_ref",
        "effect_max_active_invocations",
        "effect_max_candidate_bytes",
        "effect_max_changed_files",
        "effect_max_cost_microusd",
        "effect_max_cpu_seconds",
        "effect_max_deliveries",
        "effect_max_deployments",
        "effect_max_local_commits",
        "effect_max_memory_bytes",
        "effect_max_merges",
        "effect_max_model_input_tokens",
        "effect_max_model_output_tokens",
        "effect_max_pull_requests",
        "effect_max_pushes",
        "effect_max_wall_seconds",
        "privacy_classification",
        "redaction_profile_ref"
      ],
      "excluded_operational_fields": [
        "effect_fence_digest",
        "recorded_at"
      ],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "author_command_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "author_command_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "author_command_work_item_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "author_command_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "author_command_author_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "parent_table": "development_attempt_fences",
          "role": "author_command_attempt_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "parent_table": "development_effect_fences",
          "role": "author_command_effect_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "work_spec_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "work_spec_ref"
          ],
          "parent_table": "development_work_spec_bindings",
          "role": "author_command_work_spec_binding"
        }
      ],
      "future_mutation_owner": "_establish_development_author_effect_intent",
      "immutable_triggers": [
        "development_author_commands_no_update",
        "development_author_commands_no_delete"
      ],
      "mutable": false,
      "name": "development_author_commands",
      "primary_key": [
        "command_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "attempt_fence_command_effect_aggregate"
      ],
      "record_schema_id": "governed-execution.nwp-worker-command.v1",
      "role": "author_command_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [],
      "timestamp_participation": {
        "recorded_at": false
      },
      "unique_constraints": [
        [
          "program_ref",
          "command_ref"
        ],
        [
          "effect_intent_ref"
        ],
        [
          "candidate_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-effect-head.v1'",
          "constant": "governed-execution.nwp-development-effect-head.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(current_effect_fence_ref)='text' AND length(current_effect_fence_ref) BETWEEN 1 AND 96 AND substr(current_effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND current_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(current_effect_fence_ref,1,instr(current_effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "current_effect_fence_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(head_revision)='integer' AND head_revision>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "head_revision",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_state)='text' AND effect_state IN ('ready_for_delivery','delivery_pending','delivery_outcome_unknown','observed','cancellation_effect_established','terminal')",
          "constant": null,
          "enum_values": [
            "ready_for_delivery",
            "delivery_pending",
            "delivery_outcome_unknown",
            "observed",
            "cancellation_effect_established",
            "terminal"
          ],
          "logical_type": "closed_enum",
          "name": "effect_state",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "cancellation_effect_intent_ref IS NULL OR (typeof(cancellation_effect_intent_ref)='text' AND length(cancellation_effect_intent_ref) BETWEEN 1 AND 96 AND substr(cancellation_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND cancellation_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(cancellation_effect_intent_ref,1,instr(cancellation_effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "cancellation_effect_intent_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(updated_at)='text' AND length(updated_at)=20 AND updated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(updated_at,1,4) BETWEEN '0001' AND '9999' AND substr(updated_at,6,2) BETWEEN '01' AND '12' AND substr(updated_at,9,2) BETWEEN '01' AND '31' AND substr(updated_at,12,2) BETWEEN '00' AND '23' AND substr(updated_at,15,2) BETWEEN '00' AND '59' AND substr(updated_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at)=updated_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "updated_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(head_digest)='text' AND length(head_digest)=64 AND head_digest=lower(head_digest) AND head_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "head_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "head_digest",
      "digest_domain": "governed-execution.nwp-development-effect-head.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "effect_intent_ref",
        "program_ref",
        "current_effect_fence_ref",
        "head_revision",
        "effect_state",
        "cancellation_effect_intent_ref",
        "updated_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "effect_head_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "current_effect_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "parent_table": "development_effect_fences",
          "role": "effect_head_current_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "cancellation_effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "effect_head_cancellation_effect"
        }
      ],
      "future_mutation_owner": "effect_head_CAS",
      "immutable_triggers": [],
      "mutable": true,
      "name": "development_effect_heads",
      "primary_key": [
        "effect_intent_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "effect_head"
      ],
      "record_schema_id": "governed-execution.nwp-development-effect-head.v1",
      "role": "effect_progression_head",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [
        {
          "name": "effect_head_cancellation_algebra",
          "sql": "((effect_state='cancellation_effect_established' AND cancellation_effect_intent_ref IS NOT NULL) OR (effect_state<>'cancellation_effect_established' AND cancellation_effect_intent_ref IS NULL))"
        }
      ],
      "timestamp_participation": {
        "updated_at": true
      },
      "unique_constraints": [
        [
          "program_ref",
          "effect_intent_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-delivery-envelope.v1'",
          "constant": "governed-execution.nwp-delivery-envelope.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(delivery_attempt_ref)='text' AND length(delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(delivery_attempt_ref,1,instr(delivery_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "delivery_attempt_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(command_ref)='text' AND length(command_ref) BETWEEN 1 AND 96 AND substr(command_ref,1,1) GLOB '[0-9A-Za-z]' AND command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(command_ref,1,instr(command_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "command_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(command_digest)='text' AND length(command_digest)=64 AND command_digest=lower(command_digest) AND command_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "command_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_fence_ref)='text' AND length(attempt_fence_ref) BETWEEN 1 AND 96 AND substr(attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(attempt_fence_ref,1,instr(attempt_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "attempt_fence_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(attempt_fence_digest)='text' AND length(attempt_fence_digest)=64 AND attempt_fence_digest=lower(attempt_fence_digest) AND attempt_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "attempt_fence_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_fence_ref)='text' AND length(effect_fence_ref) BETWEEN 1 AND 96 AND substr(effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_fence_ref,1,instr(effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "effect_fence_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_fence_digest)='text' AND length(effect_fence_digest)=64 AND effect_fence_digest=lower(effect_fence_digest) AND effect_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "effect_fence_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(adapter_kind)='text' AND adapter_kind IN ('direct_local_bootstrap','execution_substrate')",
          "constant": null,
          "enum_values": [
            "direct_local_bootstrap",
            "execution_substrate"
          ],
          "logical_type": "closed_enum",
          "name": "adapter_kind",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(adapter_safe_correlation_ref)='text' AND length(adapter_safe_correlation_ref) BETWEEN 1 AND 96 AND substr(adapter_safe_correlation_ref,1,1) GLOB '[0-9A-Za-z]' AND adapter_safe_correlation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(adapter_safe_correlation_ref,1,instr(adapter_safe_correlation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "adapter_safe_correlation_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(delivery_envelope_digest)='text' AND length(delivery_envelope_digest)=64 AND delivery_envelope_digest=lower(delivery_envelope_digest) AND delivery_envelope_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "delivery_envelope_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(delivery_kind)='text' AND delivery_kind IN ('initial','redelivery')",
          "constant": null,
          "enum_values": [
            "initial",
            "redelivery"
          ],
          "logical_type": "closed_enum",
          "name": "delivery_kind",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(delivery_number)='integer' AND delivery_number>=1",
          "constant": null,
          "enum_values": null,
          "logical_type": "positive_integer",
          "name": "delivery_number",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "predecessor_delivery_attempt_ref IS NULL OR (typeof(predecessor_delivery_attempt_ref)='text' AND length(predecessor_delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(predecessor_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND predecessor_delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(predecessor_delivery_attempt_ref,1,instr(predecessor_delivery_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "predecessor_delivery_attempt_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(basis_decision_ref)='text' AND length(basis_decision_ref) BETWEEN 1 AND 96 AND substr(basis_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND basis_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(basis_decision_ref,1,instr(basis_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "basis_decision_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "recorded_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(delivery_attempt_digest)='text' AND length(delivery_attempt_digest)=64 AND delivery_attempt_digest=lower(delivery_attempt_digest) AND delivery_attempt_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "delivery_attempt_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "derived_literal_identity_fields": {
        "schema_id": "governed-execution.nwp-development-delivery-attempt.v1"
      },
      "digest_column": "delivery_attempt_digest",
      "digest_domain": "governed-execution.nwp-development-delivery-attempt.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "delivery_envelope_digest",
        "delivery_kind",
        "delivery_number",
        "predecessor_delivery_attempt_ref",
        "basis_decision_ref",
        "recorded_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "delivery_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "command_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "command_ref"
          ],
          "parent_table": "development_author_commands",
          "role": "delivery_originating_command"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "delivery_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "delivery_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "parent_table": "development_attempt_fences",
          "role": "delivery_attempt_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "parent_table": "development_effect_fences",
          "role": "delivery_effect_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "predecessor_delivery_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "delivery_attempt_ref"
          ],
          "parent_table": "development_delivery_attempts",
          "role": "delivery_predecessor"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "basis_decision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "delivery_basis_decision"
        }
      ],
      "future_mutation_owner": "effect_establishment_or_redelivery_decision",
      "immutable_triggers": [
        "development_delivery_attempts_no_update",
        "development_delivery_attempts_no_delete"
      ],
      "mutable": false,
      "name": "development_delivery_attempts",
      "nested_digest_contracts": [
        {
          "digest_column": "delivery_envelope_digest",
          "domain": "governed-execution.nwp-delivery-envelope.v1.identity",
          "identity_fields": [
            "schema_id",
            "delivery_attempt_ref",
            "program_ref",
            "program_version_ref",
            "command_ref",
            "command_digest",
            "semantic_attempt_ref",
            "effect_intent_ref",
            "attempt_fence_ref",
            "attempt_fence_digest",
            "effect_fence_ref",
            "effect_fence_digest",
            "adapter_kind",
            "adapter_safe_correlation_ref"
          ],
          "schema_id": "governed-execution.nwp-delivery-envelope.v1",
          "self_digest_excluded": true
        }
      ],
      "primary_key": [
        "delivery_attempt_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "delivery_head"
      ],
      "record_schema_id": "governed-execution.nwp-development-delivery-attempt.v1",
      "role": "delivery_attempt_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [
        {
          "name": "delivery_predecessor_algebra",
          "sql": "((delivery_kind='initial' AND delivery_number=1 AND predecessor_delivery_attempt_ref IS NULL) OR (delivery_kind='redelivery' AND delivery_number>=2 AND predecessor_delivery_attempt_ref IS NOT NULL))"
        }
      ],
      "timestamp_participation": {
        "recorded_at": true
      },
      "unique_constraints": [
        [
          "program_ref",
          "delivery_attempt_ref"
        ],
        [
          "program_ref",
          "effect_intent_ref",
          "delivery_number"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-delivery-head.v1'",
          "constant": "governed-execution.nwp-development-delivery-head.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(current_delivery_attempt_ref)='text' AND length(current_delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(current_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND current_delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(current_delivery_attempt_ref,1,instr(current_delivery_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "current_delivery_attempt_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(head_revision)='integer' AND head_revision>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "head_revision",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(delivery_state)='text' AND delivery_state IN ('planned','submitted','outcome_unknown','acknowledged','rejected','completed')",
          "constant": null,
          "enum_values": [
            "planned",
            "submitted",
            "outcome_unknown",
            "acknowledged",
            "rejected",
            "completed"
          ],
          "logical_type": "closed_enum",
          "name": "delivery_state",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(updated_at)='text' AND length(updated_at)=20 AND updated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(updated_at,1,4) BETWEEN '0001' AND '9999' AND substr(updated_at,6,2) BETWEEN '01' AND '12' AND substr(updated_at,9,2) BETWEEN '01' AND '31' AND substr(updated_at,12,2) BETWEEN '00' AND '23' AND substr(updated_at,15,2) BETWEEN '00' AND '59' AND substr(updated_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at)=updated_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "updated_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(head_digest)='text' AND length(head_digest)=64 AND head_digest=lower(head_digest) AND head_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "head_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "head_digest",
      "digest_domain": "governed-execution.nwp-development-delivery-head.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "effect_intent_ref",
        "program_ref",
        "current_delivery_attempt_ref",
        "head_revision",
        "delivery_state",
        "updated_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "delivery_head_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "current_delivery_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "delivery_attempt_ref"
          ],
          "parent_table": "development_delivery_attempts",
          "role": "delivery_head_current_delivery_attempt"
        }
      ],
      "future_mutation_owner": "delivery_head_CAS",
      "immutable_triggers": [],
      "mutable": true,
      "name": "development_delivery_heads",
      "primary_key": [
        "effect_intent_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "delivery_head"
      ],
      "record_schema_id": "governed-execution.nwp-development-delivery-head.v1",
      "role": "delivery_progression_head",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [],
      "timestamp_participation": {
        "updated_at": true
      },
      "unique_constraints": [
        [
          "program_ref",
          "effect_intent_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-decision.v1'",
          "constant": "governed-execution.nwp-development-decision.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(mutation_ref)='text' AND length(mutation_ref) BETWEEN 1 AND 96 AND substr(mutation_ref,1,1) GLOB '[0-9A-Za-z]' AND mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(mutation_ref,1,instr(mutation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "mutation_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(decision_ref)='text' AND length(decision_ref) BETWEEN 1 AND 96 AND substr(decision_ref,1,1) GLOB '[0-9A-Za-z]' AND decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(decision_ref,1,instr(decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "decision_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(decision_kind)='text' AND decision_kind IN ('initialize','accept','repair','replan','terminal_reject','block','redeliver','cancel')",
          "constant": null,
          "enum_values": [
            "initialize",
            "accept",
            "repair",
            "replan",
            "terminal_reject",
            "block",
            "redeliver",
            "cancel"
          ],
          "logical_type": "closed_enum",
          "name": "decision_kind",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(decision_variant)='text' AND decision_variant IN ('program_genesis','candidate_acceptance','candidate_repair','program_replan','attempt_selecting_replan','program_terminal_reject','program_block','productive_redelivery','cancellation_redelivery','effect_cancellation')",
          "constant": null,
          "enum_values": [
            "program_genesis",
            "candidate_acceptance",
            "candidate_repair",
            "program_replan",
            "attempt_selecting_replan",
            "program_terminal_reject",
            "program_block",
            "productive_redelivery",
            "cancellation_redelivery",
            "effect_cancellation"
          ],
          "logical_type": "closed_enum",
          "name": "decision_variant",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "basis_decision_ref IS NULL OR (typeof(basis_decision_ref)='text' AND length(basis_decision_ref) BETWEEN 1 AND 96 AND substr(basis_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND basis_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(basis_decision_ref,1,instr(basis_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "basis_decision_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "basis_program_version_ref IS NULL OR (typeof(basis_program_version_ref)='text' AND length(basis_program_version_ref) BETWEEN 1 AND 96 AND substr(basis_program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND basis_program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(basis_program_version_ref,1,instr(basis_program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "basis_program_version_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "basis_program_version_number IS NULL OR (typeof(basis_program_version_number)='integer' AND basis_program_version_number>=1)",
          "constant": null,
          "enum_values": null,
          "logical_type": "positive_integer",
          "name": "basis_program_version_number",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(expected_program_head_revision)='integer' AND expected_program_head_revision>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "expected_program_head_revision",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "resulting_program_version_ref IS NULL OR (typeof(resulting_program_version_ref)='text' AND length(resulting_program_version_ref) BETWEEN 1 AND 96 AND substr(resulting_program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND resulting_program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(resulting_program_version_ref,1,instr(resulting_program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "resulting_program_version_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "resulting_program_version_number IS NULL OR (typeof(resulting_program_version_number)='integer' AND resulting_program_version_number>=1)",
          "constant": null,
          "enum_values": null,
          "logical_type": "positive_integer",
          "name": "resulting_program_version_number",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "selected_semantic_attempt_ref IS NULL OR (typeof(selected_semantic_attempt_ref)='text' AND length(selected_semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(selected_semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND selected_semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(selected_semantic_attempt_ref,1,instr(selected_semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "selected_semantic_attempt_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "selected_candidate_ref IS NULL OR (typeof(selected_candidate_ref)='text' AND length(selected_candidate_ref) BETWEEN 1 AND 96 AND substr(selected_candidate_ref,1,1) GLOB '[0-9A-Za-z]' AND selected_candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(selected_candidate_ref,1,instr(selected_candidate_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "selected_candidate_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "selected_attempt_fence_ref IS NULL OR (typeof(selected_attempt_fence_ref)='text' AND length(selected_attempt_fence_ref) BETWEEN 1 AND 96 AND substr(selected_attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND selected_attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(selected_attempt_fence_ref,1,instr(selected_attempt_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "selected_attempt_fence_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "selected_attempt_fence_digest IS NULL OR (typeof(selected_attempt_fence_digest)='text' AND length(selected_attempt_fence_digest)=64 AND selected_attempt_fence_digest=lower(selected_attempt_fence_digest) AND selected_attempt_fence_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "selected_attempt_fence_digest",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "target_effect_intent_ref IS NULL OR (typeof(target_effect_intent_ref)='text' AND length(target_effect_intent_ref) BETWEEN 1 AND 96 AND substr(target_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND target_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(target_effect_intent_ref,1,instr(target_effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "target_effect_intent_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "target_effect_class IS NULL OR (typeof(target_effect_class)='text' AND target_effect_class IN ('author_candidate','cancel_effect','local_git_commit','review_candidate','validate_candidate'))",
          "constant": null,
          "enum_values": [
            "author_candidate",
            "cancel_effect",
            "local_git_commit",
            "review_candidate",
            "validate_candidate"
          ],
          "logical_type": "closed_enum",
          "name": "target_effect_class",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "target_effect_fence_ref IS NULL OR (typeof(target_effect_fence_ref)='text' AND length(target_effect_fence_ref) BETWEEN 1 AND 96 AND substr(target_effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND target_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(target_effect_fence_ref,1,instr(target_effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "target_effect_fence_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "target_effect_fence_digest IS NULL OR (typeof(target_effect_fence_digest)='text' AND length(target_effect_fence_digest)=64 AND target_effect_fence_digest=lower(target_effect_fence_digest) AND target_effect_fence_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "target_effect_fence_digest",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "expected_target_effect_head_revision IS NULL OR (typeof(expected_target_effect_head_revision)='integer' AND expected_target_effect_head_revision>=0)",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "expected_target_effect_head_revision",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "target_delivery_attempt_ref IS NULL OR (typeof(target_delivery_attempt_ref)='text' AND length(target_delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(target_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND target_delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(target_delivery_attempt_ref,1,instr(target_delivery_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "target_delivery_attempt_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "originating_command_ref IS NULL OR (typeof(originating_command_ref)='text' AND length(originating_command_ref) BETWEEN 1 AND 96 AND substr(originating_command_ref,1,1) GLOB '[0-9A-Za-z]' AND originating_command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(originating_command_ref,1,instr(originating_command_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "originating_command_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "originating_command_digest IS NULL OR (typeof(originating_command_digest)='text' AND length(originating_command_digest)=64 AND originating_command_digest=lower(originating_command_digest) AND originating_command_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "originating_command_digest",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "target_capsule_manifest_ref IS NULL OR (typeof(target_capsule_manifest_ref)='text' AND length(target_capsule_manifest_ref) BETWEEN 1 AND 96 AND substr(target_capsule_manifest_ref,1,1) GLOB '[0-9A-Za-z]' AND target_capsule_manifest_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(target_capsule_manifest_ref,1,instr(target_capsule_manifest_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "target_capsule_manifest_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "target_portable_capsule_digest IS NULL OR (typeof(target_portable_capsule_digest)='text' AND length(target_portable_capsule_digest)=64 AND target_portable_capsule_digest=lower(target_portable_capsule_digest) AND target_portable_capsule_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "target_portable_capsule_digest",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(coding_global_stop_ref)='text' AND length(coding_global_stop_ref) BETWEEN 1 AND 96 AND substr(coding_global_stop_ref,1,1) GLOB '[0-9A-Za-z]' AND coding_global_stop_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(coding_global_stop_ref,1,instr(coding_global_stop_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "coding_global_stop_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(coding_global_stop_version)='integer' AND coding_global_stop_version>=0",
          "constant": null,
          "enum_values": null,
          "logical_type": "nonnegative_integer",
          "name": "coding_global_stop_version",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "source_directive_ref IS NULL OR (typeof(source_directive_ref)='text' AND length(source_directive_ref) BETWEEN 1 AND 96 AND substr(source_directive_ref,1,1) GLOB '[0-9A-Za-z]' AND source_directive_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(source_directive_ref,1,instr(source_directive_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "source_directive_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "source_directive_digest IS NULL OR (typeof(source_directive_digest)='text' AND length(source_directive_digest)=64 AND source_directive_digest=lower(source_directive_digest) AND source_directive_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "source_directive_digest",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "source_evidence_ref IS NULL OR (typeof(source_evidence_ref)='text' AND length(source_evidence_ref) BETWEEN 1 AND 96 AND substr(source_evidence_ref,1,1) GLOB '[0-9A-Za-z]' AND source_evidence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(source_evidence_ref,1,instr(source_evidence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "source_evidence_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "source_evidence_digest IS NULL OR (typeof(source_evidence_digest)='text' AND length(source_evidence_digest)=64 AND source_evidence_digest=lower(source_evidence_digest) AND source_evidence_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "source_evidence_digest",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "preassigned_semantic_attempt_ref IS NULL OR (typeof(preassigned_semantic_attempt_ref)='text' AND length(preassigned_semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(preassigned_semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND preassigned_semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(preassigned_semantic_attempt_ref,1,instr(preassigned_semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "preassigned_semantic_attempt_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "preassigned_candidate_ref IS NULL OR (typeof(preassigned_candidate_ref)='text' AND length(preassigned_candidate_ref) BETWEEN 1 AND 96 AND substr(preassigned_candidate_ref,1,1) GLOB '[0-9A-Za-z]' AND preassigned_candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(preassigned_candidate_ref,1,instr(preassigned_candidate_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "preassigned_candidate_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "preassigned_effect_intent_ref IS NULL OR (typeof(preassigned_effect_intent_ref)='text' AND length(preassigned_effect_intent_ref) BETWEEN 1 AND 96 AND substr(preassigned_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND preassigned_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(preassigned_effect_intent_ref,1,instr(preassigned_effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "preassigned_effect_intent_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "preassigned_effect_fence_ref IS NULL OR (typeof(preassigned_effect_fence_ref)='text' AND length(preassigned_effect_fence_ref) BETWEEN 1 AND 96 AND substr(preassigned_effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND preassigned_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(preassigned_effect_fence_ref,1,instr(preassigned_effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "preassigned_effect_fence_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "preassigned_delivery_attempt_ref IS NULL OR (typeof(preassigned_delivery_attempt_ref)='text' AND length(preassigned_delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(preassigned_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND preassigned_delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(preassigned_delivery_attempt_ref,1,instr(preassigned_delivery_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "preassigned_delivery_attempt_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "resulting_accepted_intent_revision_ref IS NULL OR (typeof(resulting_accepted_intent_revision_ref)='text' AND length(resulting_accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(resulting_accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND resulting_accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(resulting_accepted_intent_revision_ref,1,instr(resulting_accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "resulting_accepted_intent_revision_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "resulting_work_item_ref IS NULL OR (typeof(resulting_work_item_ref)='text' AND length(resulting_work_item_ref) BETWEEN 1 AND 96 AND substr(resulting_work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND resulting_work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(resulting_work_item_ref,1,instr(resulting_work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "resulting_work_item_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "resulting_work_item_revision_ref IS NULL OR (typeof(resulting_work_item_revision_ref)='text' AND length(resulting_work_item_revision_ref) BETWEEN 1 AND 96 AND substr(resulting_work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND resulting_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(resulting_work_item_revision_ref,1,instr(resulting_work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "resulting_work_item_revision_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(reason_code)='text' AND length(reason_code) BETWEEN 1 AND 96 AND substr(reason_code,1,1) GLOB '[a-z]' AND reason_code NOT GLOB '*[^a-z0-9_.-]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "reason_code",
          "name": "reason_code",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(decided_at)='text' AND length(decided_at)=20 AND decided_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(decided_at,1,4) BETWEEN '0001' AND '9999' AND substr(decided_at,6,2) BETWEEN '01' AND '12' AND substr(decided_at,9,2) BETWEEN '01' AND '31' AND substr(decided_at,12,2) BETWEEN '00' AND '23' AND substr(decided_at,15,2) BETWEEN '00' AND '59' AND substr(decided_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',decided_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',decided_at)=decided_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "decided_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(decision_digest)='text' AND length(decision_digest)=64 AND decision_digest=lower(decision_digest) AND decision_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "decision_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "decision_digest",
      "digest_domain": "governed-execution.nwp-development-decision.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "mutation_ref",
        "decision_ref",
        "program_ref",
        "decision_kind",
        "decision_variant",
        "basis_decision_ref",
        "basis_program_version_ref",
        "basis_program_version_number",
        "expected_program_head_revision",
        "resulting_program_version_ref",
        "resulting_program_version_number",
        "selected_semantic_attempt_ref",
        "selected_candidate_ref",
        "selected_attempt_fence_ref",
        "selected_attempt_fence_digest",
        "target_effect_intent_ref",
        "target_effect_class",
        "target_effect_fence_ref",
        "target_effect_fence_digest",
        "expected_target_effect_head_revision",
        "target_delivery_attempt_ref",
        "originating_command_ref",
        "originating_command_digest",
        "target_capsule_manifest_ref",
        "target_portable_capsule_digest",
        "coding_global_stop_ref",
        "coding_global_stop_version",
        "source_directive_ref",
        "source_directive_digest",
        "source_evidence_ref",
        "source_evidence_digest",
        "preassigned_semantic_attempt_ref",
        "preassigned_candidate_ref",
        "preassigned_effect_intent_ref",
        "preassigned_effect_fence_ref",
        "preassigned_delivery_attempt_ref",
        "resulting_accepted_intent_revision_ref",
        "resulting_work_item_ref",
        "resulting_work_item_revision_ref",
        "reason_code",
        "decided_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "decision_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "basis_decision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "decision_basis_decision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "basis_program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "decision_basis_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "resulting_program_version_ref"
          ],
          "deferrability": "DEFERRABLE INITIALLY DEFERRED",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "initialize_decision_resulting_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "selected_semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "decision_selected_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "selected_attempt_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "parent_table": "development_attempt_fences",
          "role": "decision_selected_attempt_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "target_effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "decision_target_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "target_effect_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "parent_table": "development_effect_fences",
          "role": "decision_target_effect_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "target_delivery_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "delivery_attempt_ref"
          ],
          "parent_table": "development_delivery_attempts",
          "role": "decision_target_delivery_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "originating_command_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "command_ref"
          ],
          "parent_table": "development_author_commands",
          "role": "decision_originating_command"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "resulting_accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "decision_resulting_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "resulting_work_item_ref",
            "resulting_work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "decision_resulting_work_item_revision"
        }
      ],
      "future_mutation_owner": "_initialize_development_program_or_record_progression_decision",
      "immutable_triggers": [
        "development_decisions_no_update",
        "development_decisions_no_delete"
      ],
      "mutable": false,
      "name": "development_decisions",
      "primary_key": [
        "decision_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "decision_by_decision_ref",
        "initialize_decision_and_resulting_version"
      ],
      "record_schema_id": "governed-execution.nwp-development-decision.v1",
      "role": "development_decision_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [
        {
          "name": "decision_closed_variant_algebra",
          "sql": "((decision_kind='initialize' AND decision_variant='program_genesis' AND basis_decision_ref IS NULL AND basis_program_version_ref IS NULL AND basis_program_version_number IS NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND resulting_program_version_number=1 AND expected_program_head_revision=0) OR (decision_kind='accept' AND decision_variant='candidate_acceptance' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL) OR (decision_kind='repair' AND decision_variant='candidate_repair' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL) OR (decision_kind='replan' AND decision_variant='program_replan' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NOT NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL) OR (decision_kind='replan' AND decision_variant='attempt_selecting_replan' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NOT NULL AND resulting_work_item_ref IS NOT NULL AND resulting_work_item_revision_ref IS NOT NULL) OR (decision_kind='terminal_reject' AND decision_variant='program_terminal_reject' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL) OR (decision_kind='block' AND decision_variant='program_block' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL) OR (decision_kind='redeliver' AND decision_variant='productive_redelivery' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NOT NULL AND originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND target_effect_class IN ('author_candidate','validate_candidate','review_candidate')) OR (decision_kind='redeliver' AND decision_variant='cancellation_redelivery' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NOT NULL AND originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND target_effect_class='cancel_effect') OR (decision_kind='cancel' AND decision_variant='effect_cancellation' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND ((target_effect_class='author_candidate' AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL) OR (target_effect_class IN ('validate_candidate','review_candidate') AND target_capsule_manifest_ref IS NOT NULL AND target_portable_capsule_digest IS NOT NULL)) AND source_directive_ref IS NOT NULL AND source_directive_digest IS NOT NULL AND source_evidence_ref IS NOT NULL AND source_evidence_digest IS NOT NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NOT NULL AND preassigned_effect_fence_ref IS NOT NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND target_effect_class IN ('author_candidate','validate_candidate','review_candidate')))"
        }
      ],
      "timestamp_participation": {
        "decided_at": true
      },
      "unique_constraints": [
        [
          "program_ref",
          "decision_ref"
        ],
        [
          "mutation_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": null,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-mutation-receipt.v1'",
          "constant": "governed-execution.nwp-development-mutation-receipt.v1",
          "enum_values": null,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(mutation_ref)='text' AND length(mutation_ref) BETWEEN 1 AND 96 AND substr(mutation_ref,1,1) GLOB '[0-9A-Za-z]' AND mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(mutation_ref,1,instr(mutation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "mutation_ref",
          "nullable": false,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(mutation_family)='text' AND mutation_family IN ('initialize_development_program','establish_development_author_effect_intent','establish_development_bound_effect_intent','ingest_development_source_observation','record_development_progression_decision')",
          "constant": null,
          "enum_values": [
            "initialize_development_program",
            "establish_development_author_effect_intent",
            "establish_development_bound_effect_intent",
            "ingest_development_source_observation",
            "record_development_progression_decision"
          ],
          "logical_type": "closed_enum",
          "name": "mutation_family",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(command_schema_id)='text' AND command_schema_id IN ('governed-execution.nwp-initialize-development-program-command.v1','governed-execution.nwp-establish-development-author-effect-intent-command.v1','governed-execution.nwp-establish-development-bound-effect-intent-command.v1','governed-execution.nwp-ingest-development-source-observation-command.v1','governed-execution.nwp-record-development-progression-decision-command.v1')",
          "constant": null,
          "enum_values": [
            "governed-execution.nwp-initialize-development-program-command.v1",
            "governed-execution.nwp-establish-development-author-effect-intent-command.v1",
            "governed-execution.nwp-establish-development-bound-effect-intent-command.v1",
            "governed-execution.nwp-ingest-development-source-observation-command.v1",
            "governed-execution.nwp-record-development-progression-decision-command.v1"
          ],
          "logical_type": "closed_enum",
          "name": "command_schema_id",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(command_digest)='text' AND length(command_digest)=64 AND command_digest=lower(command_digest) AND command_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "command_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "decision_ref IS NULL OR (typeof(decision_ref)='text' AND length(decision_ref) BETWEEN 1 AND 96 AND substr(decision_ref,1,1) GLOB '[0-9A-Za-z]' AND decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(decision_ref,1,instr(decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "decision_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "result_program_version_ref IS NULL OR (typeof(result_program_version_ref)='text' AND length(result_program_version_ref) BETWEEN 1 AND 96 AND substr(result_program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND result_program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_program_version_ref,1,instr(result_program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "result_program_version_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "result_semantic_attempt_ref IS NULL OR (typeof(result_semantic_attempt_ref)='text' AND length(result_semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(result_semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND result_semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_semantic_attempt_ref,1,instr(result_semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "result_semantic_attempt_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "result_effect_intent_ref IS NULL OR (typeof(result_effect_intent_ref)='text' AND length(result_effect_intent_ref) BETWEEN 1 AND 96 AND substr(result_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND result_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_effect_intent_ref,1,instr(result_effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "result_effect_intent_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "result_effect_fence_ref IS NULL OR (typeof(result_effect_fence_ref)='text' AND length(result_effect_fence_ref) BETWEEN 1 AND 96 AND substr(result_effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND result_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_effect_fence_ref,1,instr(result_effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "result_effect_fence_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "result_delivery_attempt_ref IS NULL OR (typeof(result_delivery_attempt_ref)='text' AND length(result_delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(result_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND result_delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_delivery_attempt_ref,1,instr(result_delivery_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "result_delivery_attempt_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "result_observation_ref IS NULL OR (typeof(result_observation_ref)='text' AND length(result_observation_ref) BETWEEN 1 AND 96 AND substr(result_observation_ref,1,1) GLOB '[0-9A-Za-z]' AND result_observation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_observation_ref,1,instr(result_observation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "result_observation_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "result_decision_ref IS NULL OR (typeof(result_decision_ref)='text' AND length(result_decision_ref) BETWEEN 1 AND 96 AND substr(result_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND result_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_decision_ref,1,instr(result_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": null,
          "enum_values": null,
          "logical_type": "safe_ref",
          "name": "result_decision_ref",
          "nullable": true,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(result_class)='text' AND result_class IN ('development_program_initialized','development_author_effect_intent_established','development_bound_effect_intent_established','development_source_observation_ingested','development_progression_decision_recorded')",
          "constant": null,
          "enum_values": [
            "development_program_initialized",
            "development_author_effect_intent_established",
            "development_bound_effect_intent_established",
            "development_source_observation_ingested",
            "development_progression_decision_recorded"
          ],
          "logical_type": "closed_enum",
          "name": "result_class",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(result_projection_digest)='text' AND length(result_projection_digest)=64 AND result_projection_digest=lower(result_projection_digest) AND result_projection_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "result_projection_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(mutation_graph_digest)='text' AND length(mutation_graph_digest)=64 AND mutation_graph_digest=lower(mutation_graph_digest) AND mutation_graph_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": null,
          "enum_values": null,
          "logical_type": "sha256",
          "name": "mutation_graph_digest",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(outcome)='text' AND outcome='committed'",
          "constant": "committed",
          "enum_values": null,
          "logical_type": "constant_text",
          "name": "outcome",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": null,
          "check_sql": "typeof(committed_at)='text' AND length(committed_at)=20 AND committed_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(committed_at,1,4) BETWEEN '0001' AND '9999' AND substr(committed_at,6,2) BETWEEN '01' AND '12' AND substr(committed_at,9,2) BETWEEN '01' AND '31' AND substr(committed_at,12,2) BETWEEN '00' AND '23' AND substr(committed_at,15,2) BETWEEN '00' AND '59' AND substr(committed_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',committed_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',committed_at)=committed_at",
          "constant": null,
          "enum_values": null,
          "logical_type": "timestamp",
          "name": "committed_at",
          "nullable": false,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": null,
      "digest_domain": "governed-execution.nwp-development-mutation-receipt.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "mutation_ref",
        "mutation_family",
        "command_schema_id",
        "command_digest",
        "program_ref",
        "decision_ref",
        "result_program_version_ref",
        "result_semantic_attempt_ref",
        "result_effect_intent_ref",
        "result_effect_fence_ref",
        "result_delivery_attempt_ref",
        "result_observation_ref",
        "result_decision_ref",
        "result_class",
        "result_projection_digest",
        "outcome",
        "committed_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "receipt_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "decision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "receipt_decision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "result_program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "receipt_result_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "result_semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "receipt_result_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "result_effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "receipt_result_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "result_effect_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "parent_table": "development_effect_fences",
          "role": "receipt_result_effect_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "result_delivery_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "delivery_attempt_ref"
          ],
          "parent_table": "development_delivery_attempts",
          "role": "receipt_result_delivery_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "result_decision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "receipt_result_decision"
        }
      ],
      "future_mutation_owner": "all_five_C2B_mutation_families",
      "immutable_triggers": [
        "development_mutation_receipts_no_update",
        "development_mutation_receipts_no_delete"
      ],
      "mutable": false,
      "name": "development_mutation_receipts",
      "primary_key": [
        "mutation_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "mutation_receipt_by_mutation_ref"
      ],
      "record_schema_id": "governed-execution.nwp-development-mutation-receipt.v1",
      "role": "development_mutation_receipt_record",
      "seed_rows": [],
      "self_digest_excluded": true,
      "strict": true,
      "table_checks": [
        {
          "name": "receipt_closed_family_algebra",
          "sql": "((mutation_family='initialize_development_program' AND command_schema_id='governed-execution.nwp-initialize-development-program-command.v1' AND result_class='development_program_initialized' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NULL AND result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND result_delivery_attempt_ref IS NULL AND result_observation_ref IS NULL AND result_decision_ref IS NOT NULL AND result_decision_ref=decision_ref) OR (mutation_family='establish_development_author_effect_intent' AND command_schema_id='governed-execution.nwp-establish-development-author-effect-intent-command.v1' AND result_class='development_author_effect_intent_established' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NOT NULL AND result_effect_intent_ref IS NOT NULL AND result_effect_fence_ref IS NOT NULL AND result_delivery_attempt_ref IS NOT NULL AND result_observation_ref IS NULL AND result_decision_ref IS NULL) OR (mutation_family='establish_development_bound_effect_intent' AND command_schema_id='governed-execution.nwp-establish-development-bound-effect-intent-command.v1' AND result_class='development_bound_effect_intent_established' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NOT NULL AND result_effect_intent_ref IS NOT NULL AND result_effect_fence_ref IS NOT NULL AND result_delivery_attempt_ref IS NOT NULL AND result_observation_ref IS NULL AND result_decision_ref IS NULL) OR (mutation_family='ingest_development_source_observation' AND command_schema_id='governed-execution.nwp-ingest-development-source-observation-command.v1' AND result_class='development_source_observation_ingested' AND decision_ref IS NULL AND result_program_version_ref IS NULL AND result_semantic_attempt_ref IS NULL AND result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND result_delivery_attempt_ref IS NULL AND result_observation_ref IS NOT NULL AND result_decision_ref IS NULL) OR (mutation_family='record_development_progression_decision' AND command_schema_id='governed-execution.nwp-record-development-progression-decision-command.v1' AND result_class='development_progression_decision_recorded' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NULL AND result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND result_delivery_attempt_ref IS NULL AND result_observation_ref IS NULL AND result_decision_ref IS NOT NULL AND result_decision_ref=decision_ref))"
        }
      ],
      "timestamp_participation": {
        "committed_at": true
      },
      "unique_constraints": []
    }
  ],
  "triggers": [
    {
      "body_sql": "CREATE TRIGGER development_program_versions_no_update\nBEFORE UPDATE ON development_program_versions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_program_versions');\nEND;",
      "diagnostic": "append_only_development_program_versions",
      "name": "development_program_versions_no_update",
      "operation": "UPDATE",
      "table": "development_program_versions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_program_versions_no_delete\nBEFORE DELETE ON development_program_versions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_program_versions');\nEND;",
      "diagnostic": "append_only_development_program_versions",
      "name": "development_program_versions_no_delete",
      "operation": "DELETE",
      "table": "development_program_versions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_accepted_intent_revisions_no_update\nBEFORE UPDATE ON development_accepted_intent_revisions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_accepted_intent_revisions');\nEND;",
      "diagnostic": "append_only_development_accepted_intent_revisions",
      "name": "development_accepted_intent_revisions_no_update",
      "operation": "UPDATE",
      "table": "development_accepted_intent_revisions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_accepted_intent_revisions_no_delete\nBEFORE DELETE ON development_accepted_intent_revisions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_accepted_intent_revisions');\nEND;",
      "diagnostic": "append_only_development_accepted_intent_revisions",
      "name": "development_accepted_intent_revisions_no_delete",
      "operation": "DELETE",
      "table": "development_accepted_intent_revisions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_work_item_revisions_no_update\nBEFORE UPDATE ON development_work_item_revisions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_work_item_revisions');\nEND;",
      "diagnostic": "append_only_development_work_item_revisions",
      "name": "development_work_item_revisions_no_update",
      "operation": "UPDATE",
      "table": "development_work_item_revisions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_work_item_revisions_no_delete\nBEFORE DELETE ON development_work_item_revisions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_work_item_revisions');\nEND;",
      "diagnostic": "append_only_development_work_item_revisions",
      "name": "development_work_item_revisions_no_delete",
      "operation": "DELETE",
      "table": "development_work_item_revisions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_program_version_work_items_no_update\nBEFORE UPDATE ON development_program_version_work_items\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_program_version_work_items');\nEND;",
      "diagnostic": "append_only_development_program_version_work_items",
      "name": "development_program_version_work_items_no_update",
      "operation": "UPDATE",
      "table": "development_program_version_work_items",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_program_version_work_items_no_delete\nBEFORE DELETE ON development_program_version_work_items\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_program_version_work_items');\nEND;",
      "diagnostic": "append_only_development_program_version_work_items",
      "name": "development_program_version_work_items_no_delete",
      "operation": "DELETE",
      "table": "development_program_version_work_items",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_revision_edges_no_update\nBEFORE UPDATE ON development_revision_edges\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_revision_edges');\nEND;",
      "diagnostic": "append_only_development_revision_edges",
      "name": "development_revision_edges_no_update",
      "operation": "UPDATE",
      "table": "development_revision_edges",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_revision_edges_no_delete\nBEFORE DELETE ON development_revision_edges\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_revision_edges');\nEND;",
      "diagnostic": "append_only_development_revision_edges",
      "name": "development_revision_edges_no_delete",
      "operation": "DELETE",
      "table": "development_revision_edges",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_work_spec_bindings_no_update\nBEFORE UPDATE ON development_work_spec_bindings\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_work_spec_bindings');\nEND;",
      "diagnostic": "append_only_development_work_spec_bindings",
      "name": "development_work_spec_bindings_no_update",
      "operation": "UPDATE",
      "table": "development_work_spec_bindings",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_work_spec_bindings_no_delete\nBEFORE DELETE ON development_work_spec_bindings\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_work_spec_bindings');\nEND;",
      "diagnostic": "append_only_development_work_spec_bindings",
      "name": "development_work_spec_bindings_no_delete",
      "operation": "DELETE",
      "table": "development_work_spec_bindings",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_semantic_attempts_no_update\nBEFORE UPDATE ON development_semantic_attempts\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_semantic_attempts');\nEND;",
      "diagnostic": "append_only_development_semantic_attempts",
      "name": "development_semantic_attempts_no_update",
      "operation": "UPDATE",
      "table": "development_semantic_attempts",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_semantic_attempts_no_delete\nBEFORE DELETE ON development_semantic_attempts\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_semantic_attempts');\nEND;",
      "diagnostic": "append_only_development_semantic_attempts",
      "name": "development_semantic_attempts_no_delete",
      "operation": "DELETE",
      "table": "development_semantic_attempts",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_attempt_fences_no_update\nBEFORE UPDATE ON development_attempt_fences\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_attempt_fences');\nEND;",
      "diagnostic": "append_only_development_attempt_fences",
      "name": "development_attempt_fences_no_update",
      "operation": "UPDATE",
      "table": "development_attempt_fences",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_attempt_fences_no_delete\nBEFORE DELETE ON development_attempt_fences\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_attempt_fences');\nEND;",
      "diagnostic": "append_only_development_attempt_fences",
      "name": "development_attempt_fences_no_delete",
      "operation": "DELETE",
      "table": "development_attempt_fences",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_authority_evaluations_no_update\nBEFORE UPDATE ON development_authority_evaluations\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_authority_evaluations');\nEND;",
      "diagnostic": "append_only_development_authority_evaluations",
      "name": "development_authority_evaluations_no_update",
      "operation": "UPDATE",
      "table": "development_authority_evaluations",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_authority_evaluations_no_delete\nBEFORE DELETE ON development_authority_evaluations\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_authority_evaluations');\nEND;",
      "diagnostic": "append_only_development_authority_evaluations",
      "name": "development_authority_evaluations_no_delete",
      "operation": "DELETE",
      "table": "development_authority_evaluations",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_effect_intents_no_update\nBEFORE UPDATE ON development_effect_intents\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_effect_intents');\nEND;",
      "diagnostic": "append_only_development_effect_intents",
      "name": "development_effect_intents_no_update",
      "operation": "UPDATE",
      "table": "development_effect_intents",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_effect_intents_no_delete\nBEFORE DELETE ON development_effect_intents\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_effect_intents');\nEND;",
      "diagnostic": "append_only_development_effect_intents",
      "name": "development_effect_intents_no_delete",
      "operation": "DELETE",
      "table": "development_effect_intents",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_effect_fences_no_update\nBEFORE UPDATE ON development_effect_fences\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_effect_fences');\nEND;",
      "diagnostic": "append_only_development_effect_fences",
      "name": "development_effect_fences_no_update",
      "operation": "UPDATE",
      "table": "development_effect_fences",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_effect_fences_no_delete\nBEFORE DELETE ON development_effect_fences\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_effect_fences');\nEND;",
      "diagnostic": "append_only_development_effect_fences",
      "name": "development_effect_fences_no_delete",
      "operation": "DELETE",
      "table": "development_effect_fences",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_author_commands_no_update\nBEFORE UPDATE ON development_author_commands\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_author_commands');\nEND;",
      "diagnostic": "append_only_development_author_commands",
      "name": "development_author_commands_no_update",
      "operation": "UPDATE",
      "table": "development_author_commands",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_author_commands_no_delete\nBEFORE DELETE ON development_author_commands\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_author_commands');\nEND;",
      "diagnostic": "append_only_development_author_commands",
      "name": "development_author_commands_no_delete",
      "operation": "DELETE",
      "table": "development_author_commands",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_delivery_attempts_no_update\nBEFORE UPDATE ON development_delivery_attempts\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_delivery_attempts');\nEND;",
      "diagnostic": "append_only_development_delivery_attempts",
      "name": "development_delivery_attempts_no_update",
      "operation": "UPDATE",
      "table": "development_delivery_attempts",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_delivery_attempts_no_delete\nBEFORE DELETE ON development_delivery_attempts\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_delivery_attempts');\nEND;",
      "diagnostic": "append_only_development_delivery_attempts",
      "name": "development_delivery_attempts_no_delete",
      "operation": "DELETE",
      "table": "development_delivery_attempts",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_decisions_no_update\nBEFORE UPDATE ON development_decisions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_decisions');\nEND;",
      "diagnostic": "append_only_development_decisions",
      "name": "development_decisions_no_update",
      "operation": "UPDATE",
      "table": "development_decisions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_decisions_no_delete\nBEFORE DELETE ON development_decisions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_decisions');\nEND;",
      "diagnostic": "append_only_development_decisions",
      "name": "development_decisions_no_delete",
      "operation": "DELETE",
      "table": "development_decisions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_mutation_receipts_no_update\nBEFORE UPDATE ON development_mutation_receipts\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_mutation_receipts');\nEND;",
      "diagnostic": "append_only_development_mutation_receipts",
      "name": "development_mutation_receipts_no_update",
      "operation": "UPDATE",
      "table": "development_mutation_receipts",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_mutation_receipts_no_delete\nBEFORE DELETE ON development_mutation_receipts\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_mutation_receipts');\nEND;",
      "diagnostic": "append_only_development_mutation_receipts",
      "name": "development_mutation_receipts_no_delete",
      "operation": "DELETE",
      "table": "development_mutation_receipts",
      "timing": "BEFORE"
    }
  ],
  "work_spec_safe_projection": {
    "digest_domain": "governed-execution.nwp-development-work-spec-safe-projection.v1.identity",
    "ordered_keys": [
      "schema_id",
      "work_spec_ref",
      "program_ref",
      "program_version_ref",
      "accepted_intent_revision_ref",
      "work_item_ref",
      "work_item_revision_ref",
      "repository_ref",
      "base_git_object_format",
      "base_git_oid",
      "authorized_paths",
      "validation_requirement_ref",
      "review_requirement_ref",
      "privacy_classification",
      "work_spec_digest"
    ],
    "projection_is_complete_WorkSpecV1": false,
    "recorded_at_participates_in_projection_digest": false,
    "schema_id": "governed-execution.nwp-development-work-spec-safe-projection.v1",
    "source_field_treatment": {
      "authorized_paths": "stored as exact safe derived three-path canonical JSON",
      "credentials, endpoints, and retrieval material": "forbidden",
      "exclusions": "forbidden",
      "objective": "forbidden",
      "physical workspace path": "forbidden",
      "requirements": "forbidden",
      "safe references and source digest": "stored unchanged"
    }
  }
}
```
<!-- C2B2_FIELD_LEVEL_CONTRACT_JSON_END -->

The ledger is closed-world: missing, extra, reordered, or altered structural
material is not a compatible C2B2 target. It seeds no C2B row and introduces no
generic payload, metadata, extension, or opaque semantic bag.

## 30. Receipt Scalar Result And Persisted Graph Coherence

The nineteen-column receipt is structural, but its scalar result references
must also equal the persisted rows they summarize. Initialization binds its
initialize decision, the same `result_decision_ref`, and the decision's newly
created resulting version. Author-effect establishment binds the exact basis
decision and basis-bound program version plus the exact new attempt, author
intent, fence, and initial delivery. Bound-effect establishment applies the
same version rule while binding its existing attempt and exact new bound
intent, fence, and delivery. Observation ingest exposes only its exact safe
observation result reference; its parent graph remains migration-0003-owned.

Progression always binds `result_decision_ref` equal to `decision_ref`.
`accept`, `repair`, `replan`, `terminal_reject`, and `block` bind the newly
resulting version. `redeliver` and `cancel` do not advance a version and bind
the unchanged basis version. Any row/projection/graph contradiction fails as
`database_integrity_failure`; a digest never overrides scalar inequality.

## 31. Common Mutation-Graph Digest Primitive

C2B2 freezes only the common domain-separated receipt identity function. Its
identity is the eighteen receipt fields other than `mutation_graph_digest`
plus ordered `graph_entries`; each entry has exactly `role`, `ordinal`,
`record_ref`, and `record_digest`. Envelope and entry keys are closed, array
order is significant, the digest excludes itself, duplicate `(role, ordinal)`
and `(role, record_ref)` pairs are rejected, and one record ref may appear in
distinct roles. Each owning family contract supplies its closed role strings.

This primitive does not make C2B2 the owner of a family graph inventory,
locator, replay verifier, historical head postimage, writer, or resolver.

## 32. C2B2 Private Reader Boundary

C2B2 owns exactly the twelve role contracts in the structured ledger. Each
reader has one exact ordered nonempty `future_caller` list drawn only from
`C2B3`, `C2B5`, and `C2B6`; C2B2 has no reader implementation/caller and C2B4
owns only migration-0003 rows/readers. The mapping is:

```text
mutation_receipt_by_mutation_ref: [C2B3, C2B5, C2B6]
decision_by_decision_ref: [C2B3, C2B5, C2B6]
program_head_and_current_version: [C2B3, C2B6]
initialize_decision_and_resulting_version: [C2B3]
accepted_intent_revision_by_exact_ref: [C2B3, C2B6]
work_item_head_and_revision_by_exact_ref: [C2B3, C2B5, C2B6]
paged_program_version_membership: [C2B3, C2B6]
work_spec_safe_binding: [C2B3, C2B5, C2B6]
attempt_fence_command_effect_aggregate: [C2B3, C2B5, C2B6]
authority_evaluation_by_exact_ref: [C2B3, C2B5]
effect_head: [C2B3, C2B5]
delivery_head: [C2B3, C2B5]
```

For table metadata, `tables[].role` is only a table-semantic grouping label;
it is never a reader identity. `tables[].reader_roles` is the sole ordered
table-to-reader mapping, every member belongs to the exact twelve-role
inventory, and the ambiguous singular `tables[].reader_role` field is
forbidden. `development_revision_edges.reader_roles` is exactly empty: C2B2
freezes its durable row representation only. Exact revision-edge selection is
progression-family-specific and remains C2B6-owned as part of its future graph
locator/replay contract before C2B6 writers; C2B2 does not add a thirteenth
reader or freeze a revision-edge query, locator, replay graph, or historical
postimage.

Before borrow or SQL, every reader requires
`type(capability) is _SQLiteMutationReadCapability`. A structural protocol
stand-in and a raw `sqlite3.Connection` are not authority. Readers use explicit
ordered columns, bounded fetches, deterministic ordering where applicable,
closed private decoders, digest verification, and safe error classification.
They may verify exact bounded aggregates but may not claim complete
mutation-family replay. No public reader, public export, `StateStore` method,
or `WriterSession` method is added.

## 33. Family Replay Deferral And Tranche Ownership

C2B2 does not freeze or implement complete mutation-family replay graphs, a
complete family graph verifier, historical mutable-head replay, family graph
locators, mutation, or recovery. Before its first writer, each family-owning
tranche must freeze its closed roles/ranks/ordinals, record-ref derivations,
member locators, historical mutable-head postimages, golden vectors, exact
replay, and commit-outcome recovery.

```text
C2B3: initialize and author-effect graph/replay
C2B4: migration-0003 row contracts/readers only; not a mutation tranche
C2B5: observation ingest, bound validation/review/cancellation effects, cancel, and redeliver graph/replay
C2B6: accept, repair, replan, terminal_reject, block, and eligibility/latch/version/head replay
```

The proposal's forty-role ledger, locators, historical postimages, and replay
vectors are reviewed later-tranche proposal evidence, not current C2B2
contract authority.

## 34. C2B2 Freeze Nonimplementation

The field-level freeze tranche created documentation and contract tests only.
C2B2 Slice 1 implements its literal migration-0002 SQL and physical schema
representation, and Slice 2 implements pure private row/value source without
changing the physical schema. Neither slice creates migration-0003 material,
database rows, a product reader, mutation or recovery API, public API,
`StateStore` or `WriterSession` widening, package-root export, dependency,
worker, provider, capsule, Git, direct-local, ES, Bridge, service, IPC, queue,
scheduler, reconciler, or autonomous loop. The implemented migration contract
is generation 2 at tip `0002_development_program_and_effect_state`.

### Dedicated C2B2 Oracle Architecture And Audit-Repair Closure

`tests/test_c2b2_field_level_contract.py` owns exactly one module-level
`EXPECTED_CONTRACT` assignment. Its right-hand side is a direct Python literal
made only from dictionaries, lists, tuples, strings, integers, booleans, and
`None`; no call, attribute, subscript, comprehension, generator, lambda,
formatted string, or nonconstant name may occur below that assignment.
`ast.literal_eval` of the assignment must equal the runtime value.

The semantic oracle reads only this owner document. Its bounded architecture
self-check may additionally read its own test source. It may not import another
collected test, Coordinator production source, `sqlite3`, or `importlib`; read
external SQL, proposal JSON, production source, Downloads, or proposal
artifacts; or use dynamic import. It rejects `eval`, `exec`, built-in
`compile`, `__import__`, callable selection through `getattr`, `globals`, or
`locals`, calls through subscripts, callable/validator registries, and generic
dispatch tables. Literal data mappings remain permitted only when they do not
select executable behavior.

The owner payload is compared directly with `EXPECTED_CONTRACT` and validated
semantically. A source/file digest cannot substitute for that equality. The
only semantic SHA-256 call sites are `_graph_digest_from_identity`, which
produces the domain-separated mutation-graph digest, and
`test_c2b2_common_graph_digest_primitive_is_closed_and_order_sensitive`, which
independently checks that semantic formula. Any unclassified SHA-256 call site
or source-hash-only acceptance fails closed.

Direct contract negatives require the exact `_ContractViolation` class and one
exact identifier from a closed safe vocabulary. Reader caller failures use
`C2B2_READER_FUTURE_CALLER_MISSING` or
`C2B2_READER_FUTURE_CALLER_INVALID`; table mapping failures use
`C2B2_TABLE_READER_ROLE_UNKNOWN`, `C2B2_TABLE_READER_ROLE_MISMATCH`, or
`C2B2_REVISION_EDGE_READER_OWNERSHIP`; oracle architecture failures use
`C2B2_ORACLE_EXPECTED_NOT_LITERAL`, `C2B2_ORACLE_FORBIDDEN_INPUT`,
`C2B2_ORACLE_DYNAMIC_DISPATCH`, or `C2B2_ORACLE_SOURCE_HASH_AUTHORITY`.
Empty, wrong, substring-only, path-bearing, candidate-bearing, or private-input
diagnostics are not accepted.
