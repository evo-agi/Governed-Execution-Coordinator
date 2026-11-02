# RW0-C2 durable progression-decision semantic contract

## Status and authority

Classification: `ACCEPTED STRATEGIC TARGET` and
`DEFERRED OR BLOCKED EFFECT`.

This document is the single semantic owner for the future RW0-C2 durable
post-execution progression-decision owner. This tranche writes only the target
semantic contract and its finite documentation-contract oracle. It does not
implement a command, reducer, durable writer, result, receipt, replay path,
recovery path, acceptance latch, terminal-outcome owner, migration, reader,
transaction integration, production caller, public export, or runtime behavior.

Git owns commit, tree, object, and ref facts. `AGENTS.md` routes repository
composition and contract authority; `.docs/` owns current and target contract
semantics within each document's declared scope; and
`.docs/autonomous-software-development-operating-model.md` remains the
authoritative composition and current-status record. Source and migrations
implement current behavior and durable representation without becoming the
sole repository contract authority. Tests and reports remain evidence only.

The existing post-execution modules remain private, pure, no-I/O values,
projections, evaluators, and bounded helpers with no production caller. RW0-C1
remains the implemented durable phase and supplied-evidence boundary. Migration
0002 remains the canonical generic development decision/version/head/receipt
representation, migrations 0001 through 0004 remain byte- and meaning-exact,
application generation remains 2, and migration 0005 does not exist.

This contract owns future Coordinator progression semantics only. It does not
authenticate evidence, issue standing authority, grant execution permission,
own physical process or transport truth, or displace Execution Substrate
admission/runtime authority. A model supplies proposal evidence only. The
caller supplies a bounded command only. Neither may author durable truth.

## Governing distinctions

The future owner must preserve three disjoint outcomes:

| Outcome | Meaning | Durable effects |
| --- | --- | --- |
| command rejection / no durable write | The command or basis cannot be admitted as one complete, nonconflicting mutation | no decision, version, head mutation, receipt, acceptance fact, or terminal fact |
| durable progression decision | Exactly one of the five closed branches is derived from an admitted basis | one version-advancing migration-0002 decision family, subject to future atomic-writer and recovery contracts |
| committed-recovery `unresolved` | A commit was attempted and guarded readback cannot prove either the exact committed family or definite absence | no new or fabricated decision, result, receipt, acceptance fact, or terminal fact |

`post_execution_program_block` is a real durable decision. It is never a
synonym for command rejection. Recovery `unresolved` is neither a branch nor a
rejection; it can occur only after commit uncertainty.

## Basis-admission no-write gate

The closed rejection classes are:

| Rejection class | Covered condition |
| --- | --- |
| `required_fact_invalid` | malformed, missing, duplicate, partial, foreign, or contradictory required fact |
| `basis_identity_lineage_profile_provenance_conflict` | owner, identity, lineage, profile, provenance, validation/review-basis, or decision-time-currentness conflict |
| `stale_caller_expectation` | stale caller program head, version, revision, or other caller expectation |
| `mutation_ref_reuse_conflict` | one `mutation_ref` is reused with a different canonical command digest |
| `preassigned_identity_or_family_route_collision` | a preassigned identity or family-route locator collides |
| `matrix_conflict` | an applicable selected matrix entry reports `conflict` or its owner/profile binding conflicts |
| `expected_branch_mismatch` | the optional caller assertion differs from the branch derived by the Coordinator |
| `halt_only_matrix_contract_conflict` | any matrix does not return its exact profile-owned `permit` for the selected halt-only branch |
| `bootstrap_acceptance_guard_conflict` | applicable command lacks exact admitted-lineage posture or derived acceptance lacks exhaustive unclaimed-scope proof |

These classes are operation results, not durable branch reasons. Every
rejection returns before a durable mutation. Later-discovered rejection
conditions, including expected-branch mismatch and bootstrap-guard conflict,
still prohibit the entire write; they do not convert to a durable block.

## Decision-time currentness

| Currentness conclusion | Reducer effect |
| --- | --- |
| `conflict` | no write: `basis_identity_lineage_profile_provenance_conflict` |
| `stale` | add durable block reason `decision_basis_not_current` |
| `unknown` | add durable block reason `decision_basis_not_current` |
| `current` | continue |

A stale caller expectation is independently a no-write conflict. A complete,
current observation which proves that the evidence basis itself is stale or
unknown is instead sufficient evidence for a version-advancing block.

## Exact V14 and V15 input projection

The reducer consumes already validated current V14 and V15 semantic values. It
does not consume raw source observations directly, reinterpret a partial tuple,
or invent a compound alias. The complete projection below is normative and is
bound by documentation-contract tests to the current source tuple owners.

### Validation accepted rows

<!-- RW0_C2_VALIDATION_PROJECTION_BEGIN -->
| `source_outcome` | `result` | `repairability` | `reason` | Normalized class |
| --- | --- | --- | --- | --- |
| `passed` | `passed` | `not_applicable` | `validation_passed` | `accept` |
| `failed` | `repairable_failure` | `repairable` | `validation_failed_repairable` | `repair` |
| `failed` | `replan_required` | `same_attempt_insufficient` | `validation_failed_replan_required` | `replan` |
| `failed` | `terminal_failure` | `nonrepairable` | `validation_failed_terminal` | `terminal` |
| `failed` | `unknown` | `unknown` | `validation_failed_unclassified` | `nonconclusive` |
| `inconclusive` | `unknown` | `unknown` | `validation_inconclusive` | `nonconclusive` |
| `not_run` | `not_run` | `not_applicable` | `validation_not_run` | `nonconclusive` |
<!-- RW0_C2_VALIDATION_PROJECTION_END -->

### Validation conflict projection

<!-- RW0_C2_VALIDATION_CONFLICT_BEGIN -->
| `source_outcome` | `result` | `repairability` | `reason` | Normalized class |
| --- | --- | --- | --- | --- |
| `any_v14_allowed_source_outcome` | `basis_conflict` | `conflict` | `source_observation_mismatch` | `conflict` |
<!-- RW0_C2_VALIDATION_CONFLICT_END -->

### Review accepted rows

<!-- RW0_C2_REVIEW_PROJECTION_BEGIN -->
| `separation_status` | `source_outcome` | `result` | `reason` | Normalized class |
| --- | --- | --- | --- | --- |
| `separate` | `passed` | `passed` | `review_passed` | `accept` |
| `separate` | `failed` | `repair_required` | `review_failed_repair_required` | `repair` |
| `separate` | `failed` | `replan_required` | `review_failed_replan_required` | `replan` |
| `separate` | `failed` | `terminal_reject` | `review_failed_terminal_reject` | `terminal` |
| `separate` | `failed` | `unknown` | `review_failed_unclassified` | `nonconclusive` |
| `separate` | `inconclusive` | `unknown` | `review_inconclusive` | `nonconclusive` |
<!-- RW0_C2_REVIEW_PROJECTION_END -->

### Review separation-status overrides

<!-- RW0_C2_REVIEW_OVERRIDE_BEGIN -->
| `separation_status` | `source_outcome` | `result` | `reason` | Normalized class |
| --- | --- | --- | --- | --- |
| `not_separate` | `any_v15_allowed_source_outcome` | `basis_conflict` | `review_not_operationally_separate` | `conflict` |
| `unknown` | `any_v15_allowed_source_outcome` | `unknown` | `reviewer_separation_unknown` | `nonconclusive` |
| `conflict` | `any_v15_allowed_source_outcome` | `basis_conflict` | `reviewer_separation_conflict` | `conflict` |
<!-- RW0_C2_REVIEW_OVERRIDE_END -->

Any other V14 or V15 field combination is an invalid or contradictory required
fact and yields no durable write with `required_fact_invalid`. No compound
conflict alias is admitted; the exact current fields above are authoritative.

After projection, conflict is resolved before any durable branch.
Nonconclusive evidence is resolved before candidate-quality severity. When both
inputs are conclusive, the maximum severity is
`terminal > replan > repair > accept`; input order is irrelevant and no tuple
order is a semantic tie-break.

The closed candidate evidence reason classes are:

- `candidate_evidence_conclusively_accepted`
- `candidate_evidence_requires_repair`
- `candidate_evidence_requires_replan`
- `candidate_evidence_terminally_rejected`
- `candidate_evidence_nonconclusive`

## Matrix eligibility and active stop

For the provisional candidate branch, the reducer consumes the exact selected
entry from this closed, ordered owner inventory. Missing, additional,
duplicated, or reordered owners make the basis invalid and cause no write.

<!-- RW0_C2_MATRIX_OWNER_PROFILES_BEGIN -->
| Order | Owner | Productive permit reason | Halt-only permit reason |
| ---: | --- | --- | --- |
| 1 | `standing_policy` | `policy_permits` | `halt_only_policy_not_applicable` |
| 2 | `risk_lane` | `risk_lane_permits` | `halt_only_risk_not_applicable` |
| 3 | `decision_time_authority` | `authority_verified_current` | `halt_only_authority_not_applicable` |
| 4 | `global_stop` | `global_stop_clear` | `halt_only_stop_checked` |
| 5 | `source_effect_ceiling` | `source_effect_within_current_ceilings` | `halt_only_ceiling_not_applicable` |
<!-- RW0_C2_MATRIX_OWNER_PROFILES_END -->

The accepted reducer input grammar contains exactly the 44 pairs currently
emittable through valid production construction, evaluator control flow, and
the required accepted relation/action boundary:

<!-- RW0_C2_MATRIX_OWNER_RESULT_REASON_PAIRS_BEGIN -->
| Owner | Result | Reason |
| --- | --- | --- |
| `standing_policy` | `permit` | `halt_only_policy_not_applicable` |
| `standing_policy` | `deny` | `policy_revoked` |
| `standing_policy` | `deny` | `branch_not_allowed` |
| `standing_policy` | `deny` | `risk_lane_not_allowed` |
| `standing_policy` | `deny` | `effect_class_not_allowed` |
| `standing_policy` | `unknown` | `policy_status_unknown` |
| `standing_policy` | `unknown` | `policy_currentness_unknown` |
| `standing_policy` | `permit` | `policy_permits` |
| `risk_lane` | `permit` | `halt_only_risk_not_applicable` |
| `risk_lane` | `deny` | `policy_revoked` |
| `risk_lane` | `deny` | `required_lane_mismatch` |
| `risk_lane` | `unknown` | `policy_status_unknown` |
| `risk_lane` | `permit` | `risk_lane_permits` |
| `decision_time_authority` | `conflict` | `snapshot_or_phase_mismatch` |
| `decision_time_authority` | `conflict` | `parent_or_fence_identity_mismatch` |
| `decision_time_authority` | `conflict` | `support_conflict` |
| `decision_time_authority` | `permit` | `halt_only_authority_not_applicable` |
| `decision_time_authority` | `deny` | `authority_denied` |
| `decision_time_authority` | `deny` | `authority_revoked` |
| `decision_time_authority` | `deny` | `attempt_fence_expired` |
| `decision_time_authority` | `deny` | `effect_fence_expired` |
| `decision_time_authority` | `deny` | `authority_grant_expired` |
| `decision_time_authority` | `deny` | `authority_observation_expired` |
| `decision_time_authority` | `deny` | `effect_class_not_allowed` |
| `decision_time_authority` | `unknown` | `authority_status_unknown` |
| `decision_time_authority` | `unknown` | `family_status_unknown` |
| `decision_time_authority` | `unknown` | `revocation_status_unknown` |
| `decision_time_authority` | `permit` | `authority_verified_current` |
| `global_stop` | `permit` | `halt_only_stop_checked` |
| `global_stop` | `deny` | `global_stop_active` |
| `global_stop` | `permit` | `global_stop_clear` |
| `source_effect_ceiling` | `conflict` | `snapshot_lineage_or_fence_mismatch` |
| `source_effect_ceiling` | `conflict` | `proposal_evidence_conflict` |
| `source_effect_ceiling` | `permit` | `halt_only_ceiling_not_applicable` |
| `source_effect_ceiling` | `deny` | `proposal_evidence_noncompliant` |
| `source_effect_ceiling` | `deny` | `attempt_fence_expired` |
| `source_effect_ceiling` | `deny` | `effect_fence_expired` |
| `source_effect_ceiling` | `deny` | `authority_grant_expired` |
| `source_effect_ceiling` | `deny` | `authority_observation_expired` |
| `source_effect_ceiling` | `deny` | `effect_class_not_allowed` |
| `source_effect_ceiling` | `deny` | `source_effect_exceeds_current_attempt` |
| `source_effect_ceiling` | `deny` | `source_effect_exceeds_current_authority` |
| `source_effect_ceiling` | `unknown` | `current_authority_unknown` |
| `source_effect_ceiling` | `permit` | `source_effect_within_current_ceilings` |
<!-- RW0_C2_MATRIX_OWNER_RESULT_REASON_PAIRS_END -->

The source metadata also declares exactly these 24 pairs, but they are not
accepted outputs of the current complete construction/evaluator/relation call
graph and therefore are not reducer inputs:

<!-- RW0_C2_MATRIX_METADATA_UNREACHABLE_PAIRS_BEGIN -->
| Owner | Result | Reason | Reachability classification |
| --- | --- | --- | --- |
| `standing_policy` | `conflict` | `policy_identity_conflict` | `no_evaluator_branch` |
| `standing_policy` | `conflict` | `evaluator_profile_mismatch` | `no_evaluator_branch` |
| `standing_policy` | `conflict` | `support_conflict` | `no_evaluator_branch` |
| `standing_policy` | `deny` | `policy_not_yet_valid` | `accepted_relation_precludes` |
| `standing_policy` | `deny` | `policy_expired` | `valid_construction_precludes` |
| `standing_policy` | `deny` | `audience_mismatch` | `no_evaluator_branch` |
| `standing_policy` | `deny` | `repository_mismatch` | `no_evaluator_branch` |
| `standing_policy` | `deny` | `path_scope_mismatch` | `no_evaluator_branch` |
| `standing_policy` | `deny` | `ceilings_exceeded` | `no_evaluator_branch` |
| `risk_lane` | `conflict` | `risk_source_conflict` | `no_evaluator_branch` |
| `risk_lane` | `conflict` | `policy_identity_conflict` | `no_evaluator_branch` |
| `risk_lane` | `conflict` | `evaluator_profile_mismatch` | `no_evaluator_branch` |
| `risk_lane` | `conflict` | `support_conflict` | `no_evaluator_branch` |
| `risk_lane` | `deny` | `policy_not_yet_valid` | `accepted_relation_precludes` |
| `risk_lane` | `deny` | `policy_expired` | `valid_construction_precludes` |
| `risk_lane` | `deny` | `risk_lane_not_allowed` | `accepted_relation_precludes` |
| `decision_time_authority` | `conflict` | `profile_mismatch` | `no_evaluator_branch` |
| `global_stop` | `conflict` | `snapshot_or_stop_identity_mismatch` | `valid_construction_precludes` |
| `global_stop` | `conflict` | `profile_mismatch` | `no_evaluator_branch` |
| `global_stop` | `unknown` | `global_stop_unknown` | `valid_construction_precludes` |
| `source_effect_ceiling` | `conflict` | `profile_mismatch` | `no_evaluator_branch` |
| `source_effect_ceiling` | `conflict` | `support_conflict` | `valid_construction_precludes` |
| `source_effect_ceiling` | `unknown` | `proposal_evidence_unknown` | `valid_construction_precludes` |
| `source_effect_ceiling` | `deny` | `source_effect_exceeds_current_effect` | `accepted_relation_precludes` |
<!-- RW0_C2_MATRIX_METADATA_UNREACHABLE_PAIRS_END -->

The accepted and metadata-only inventories are disjoint and their union is the
exact 68-pair source metadata declaration. A supplied or forged metadata-only
pair is `matrix_conflict` and no-write. Any later change that makes such a pair
emittable requires a deliberately authorized source-and-contract tranche; this
contract does not adapt automatically.

The absent pair `risk_lane` / `unknown` / `policy_currentness_unknown` is
forbidden; `risk_lane` unknown is exactly `policy_status_unknown`.

Every entry must retain the exact branch, exact owner, one pair from that
owner's table, and the canonical branch profile. Productive entries use
`governed` / `author_candidate`; terminal-reject and block entries use
`halt_only` / null effect class. A productive wrong applicability, effect
class, owner/profile binding, foreign pair, or non-profile-owned permit is
`matrix_conflict`. An exact owner conflict pair is `matrix_conflict` on either
profile. A final halt-only deny, unknown, foreign or malformed pair, wrong
applicability, wrong effect class, or non-profile-owned permit is
`halt_only_matrix_contract_conflict`.
That includes the same owner's otherwise valid productive permit: a productive
permit reason substituted on any final halt-only entry is always
`halt_only_matrix_contract_conflict` on direct terminal, stale-currentness,
unknown-currentness, validation-nonconclusive, review-nonconclusive,
productive-deny conversion, and productive-unknown conversion routes.

Each selected entry has exactly one result from `permit`, `deny`, `unknown`, or
`conflict`. For the productive branches `candidate_acceptance`,
`candidate_repair`, and `attempt_selecting_replan`, any `conflict` is no-write,
all five `permit` results retain the candidate, and any `deny` or `unknown`
adds durable block reason `productive_branch_not_permitted`.

For a final `program_terminal_reject` or `post_execution_program_block`, each
matrix must select that branch's profile-owned `halt_only` entry and return the
exact result `permit` with the owner-specific halt-only permit reason above. An
exact owner conflict pair is `matrix_conflict`; every other non-permit or
invalid halt-only entry is `halt_only_matrix_contract_conflict`. Each produces
no write.

The productive-to-block path is necessarily two-stage. The reducer first
evaluates and retains all five productive entries. A deny or unknown converts
the provisional result to block. The reducer then evaluates all five distinct
block/halt-only entries. Only five exact block permits produce a durable block;
skipping this second stage is a contract violation.

Consequently, with an active global stop, terminal evidence still selects
`program_terminal_reject`, while acceptance, repair, or replan evidence is
converted to `post_execution_program_block`. The global-stop matrix is an
input to the same reducer; it does not own a competing branch.

All selected matrix results, owner/profile bindings, and bounded reasons are
retained in the immutable decision basis. The summary reason never erases
lower-level evidence.

## Block reason precedence

Only after every applicable no-write gate passes, when several durable block
conditions are present, the one summary reason is the first applicable value
in this exact order:

1. `decision_basis_not_current`
2. `candidate_evidence_nonconclusive`
3. `productive_branch_not_permitted`

Currentness, normalized dispositions, provisional candidate evidence, and all
matrix entries remain retained even when a higher-precedence reason supplies
the summary.

## Closed branch mapping

<!-- RW0_C2_BRANCH_MAPPING_BEGIN -->
| Authoritative branch | Migration-0002 decision kind | Migration-0002 decision variant | Version advancing |
| --- | --- | --- | --- |
| `candidate_acceptance` | `accept` | `candidate_acceptance` | yes |
| `candidate_repair` | `repair` | `candidate_repair` | yes |
| `attempt_selecting_replan` | `replan` | `attempt_selecting_replan` | yes |
| `program_terminal_reject` | `terminal_reject` | `program_terminal_reject` | yes |
| `post_execution_program_block` | `block` | `program_block` | yes |
<!-- RW0_C2_BRANCH_MAPPING_END -->

The RW0-C2 reducer emits exactly these five branches. It emits neither
`redeliver` nor `cancel`; their pre-existing migration-0002 grammar remains
outside this reducer and is not changed by this contract. Existing
migration-0002 nullability and branch constraints remain authoritative.

## Deterministic reducer pipeline

The future owner must perform one deterministic reduction while retaining the
complete admitted basis:

1. Reconstruct all required facts, including the every-command admitted-lineage
   relation and universal authority posture, and reject malformed, incomplete,
   foreign, contradictory, stale-caller, replay-conflicting, or colliding input.
2. Validate the exact five-owner inventory, every canonical branch profile,
   and every owner-specific result/reason pair. Owner, profile, pair, and exact
   conflict failures are no-write before any block reason can control output.
3. Evaluate decision-time currentness: conflict is no-write; stale or unknown
   records the highest-precedence block condition. Then normalize validation
   and review. Any conflict is no-write. Record whether evidence is
   nonconclusive; otherwise derive the maximum-severity provisional candidate.
4. For every conclusive productive candidate, evaluate and retain all five
   productive matrix entries even when currentness already supplied a block
   reason. Conflict is no-write; deny or unknown records the productive-
   eligibility block condition.
5. Select the first applicable block reason, otherwise retain the conclusive
   candidate. For every final terminal-reject or block branch, separately
   evaluate all five exact final-branch halt-only entries. This stage is
   mandatory for direct terminal, native block, and converted block paths.
6. Compare the optional expected-branch assertion to that authoritative final
   branch. Mismatch is no-write.
7. Retain the exact admitted-lineage relation and universal posture already
   established in the command/writer admission prefix. If and only if acceptance
   was derived, prove the scope exhaustively unclaimed.
   Failure is no-write; success creates one immutable acceptance-fact member
   of the future atomic decision family.
8. Only after all authoritative no-write gates, including the bootstrap guard,
   evaluate model-recommendation consistency. Retain that evidence without
   changing the branch. This is always the last evaluation stage while the
   basis remains valid.
9. Build exactly one result/receipt family for the one final branch, then use
   the separately frozen writer/replay/recovery contract. No other final branch
   or fallback mutation is permitted.

All no-write conditions have precedence over durable output even when their
check necessarily follows provisional branch calculation. Calculating a
provisional branch is not creating durable truth.

The contract-test interpreter retains this ordered internal audit trace as the
applicable stages are reached: `basis_validated`,
`matrix_grammar_validated`, `currentness_reduced`,
`validation_review_reduced`, `productive_matrix_evaluated`,
`branch_selected`, `halt_only_matrix_evaluated`,
`bootstrap_acceptance_guard_checked`, and `model_consistency_evaluated`. Productive
evaluation records the provisional productive branch plus all five canonical
owner entries and their exact result/reason pairs. It is performed after a
stale or unknown currentness block has been recorded whenever V14/V15 still
produces a conclusive productive candidate. The block-summary precedence
chooses only the summary reason; it never suppresses evidence evaluation.
Matrix conflict remains global no-write. Model consistency is always the last
trace stage while the basis remains valid, and it is absent when an earlier
gate, including the bootstrap-guard gate, rejects the operation.

## Command and model non-authority

The future command may carry an optional expected-branch assertion. It is only
an optimistic conflict assertion and is covered by the canonical command
digest. It does not request or select that branch.

The command must not carry a caller-authored authoritative branch,
decision-time currentness conclusion, matrix conclusion, durable decision,
durable result, receipt, admission fact, acceptance fact, terminal outcome, or commit/recovery
classification. The model likewise cannot author any of those values. Model
recommendation consistency is evaluated only after reduction and is retained
as non-authoritative evidence. A recognized recommendation that maps to the
authoritative branch records `consistent` /
`mapped_branch_equals_authoritative_branch`; a recognized recommendation that
maps elsewhere records `inconsistent` /
`mapped_branch_differs_from_authoritative_branch`; and an unrecognized string
records `inconsistent` / `model_recommendation_unrecognized`. An isolated
unrecognized recommendation cannot create no-write, block, terminal reject,
another durable branch, matrix conflict, or currentness conflict. A missing or
malformed complete proposal family remains invalid basis independently of this
non-authoritative token.

## Abstract result, receipt, replay, and recovery responsibilities

A later physical contract must bind one canonical command digest, one
`mutation_ref`, all preassigned family identities, the complete immutable
decision basis, exactly one mapped migration-0002 decision/version/head family,
one result projection, and one receipt. It must preserve one guarded writer,
writer fencing, expected-head checks, atomic CAS, exactly one commit attempt,
and readback-only resolution of commit uncertainty.

Same-`mutation_ref`, same-command replay returns the exact committed decision,
result, receipt, version/head postimages, and, for acceptance, the committed
immutable bootstrap-acceptance fact without another mutation. Same-`mutation_ref` with a different
command digest is `mutation_ref_reuse_conflict`. A fresh command colliding with
any preassigned identity or family route is
`preassigned_identity_or_family_route_collision`.

After a commit-attempt exception, recovery must use a command-covered selector
and classify only:

- `committed_exact` when the whole expected family is present and exact;
- `definitely_not_committed` when the original command's newly created family is exhaustively absent,
  without fragments, aliases, collisions, or read faults; fresh retry eligibility
  is a separate question; or
- `unresolved` when neither proposition can be proved.

Recovery never completes a partial family, invents a result or receipt,
re-evaluates the reducer, changes a branch, or retries automatically after
`unresolved`.

## Bootstrap acceptance-guard dependency

The sole admitted-lineage, admission, eligibility, and acceptance-fact owner is
`.docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md`. This explicitly
supersedes the former mutable-latch target; `acceptance_latch_precondition_conflict`
is superseded terminology, not another active rejection owner.

Every applicable direct-local command binds canonical admitted lineage and scope expectations.
The non-authoritative relation is command-digest and recovery-selector covered,
selects no scope or branch, requests no acceptance, and cannot admit, mint,
renew, or replenish a scope. Admission, positive continuity, sole-active
posture, and absence of foreign/conflicting lineage claims must be exact for
every command. Acceptance alone additionally requires exhaustive unclaimed-scope
proof under the guard owner. Unknown or explicitly claimed status may permit a nonaccept
branch only when derivation makes no unclaimed assertion and all other
preconditions are exact. Failure is `bootstrap_acceptance_guard_conflict`,
never fallback block. This owner projects the guard interface, not guard tables.

For the bounded private offline P1 implementation, the current source's
universal check validates exact types, time, positive and basis-bound
continuity and sole-active posture, no foreign claim, and the relevant
disclosure or recording permission. Current claimed status is type-checked
but is not universal posture or protected-result disclosure authority. After
a receipt miss, recording posture, route/current checks, and authoritative
branch derivation, only candidate acceptance checks that both the immutable
basis assertion and current source say exhaustively unclaimed. `False` or
`None` rejects fresh acceptance with the existing guard conflict; either
value alone cannot veto a nonaccept branch. Receipt-present exact replay
requires fresh universal disclosure but never reevaluates current acceptance
eligibility. Receipt-absent recovery with explicit current `False` and no
complete local acceptance winner is `unresolved`; a complete competing winner
may prove original-command noncommit without disclosing that winner or
granting retry. This separation changes no basis, command, result, receipt,
or branch grammar and adds no live authority.

Acceptance creates exactly one immutable fact in the same decision/version/head/
result/receipt family; the four nonaccept branches create none. Receipt-first
replay/collision checks precede fresh eligibility. Exact replay returns the
original complete family and fact without reevaluation, new timestamp, or
historical mutable-head freshness. There is one whole-family recovery classifier:
all expected immutable members exact means `committed_exact`; exhaustive original-
family absence means `definitely_not_committed`; any partial family or unprovable
proposition means `unresolved`. A competing complete winner may prove original-
family absence while independently prohibiting fresh retry in that claimed scope.
Decision without fact or fact without decision is unresolved; no fragment repair
is permitted. Physical guard values, provisioning, storage, and transaction
integration remain future and no accept writer is callable.

The accepted-target private value/versioning and receipt-graph profile owner is
`.docs/rw0-c2-private-value-versioning.md`. Its supplemental guarded relation,
result composite, and required-role profile preserve the generic migration-0002
v1 decision/version/head/result/receipt meanings. This decision owner retains
the reducer, five branches, one result/receipt, exact replay, collisions, and
one whole-family recovery classifier. The private profile chooses no physical
layout or transaction mechanics; those remain later bounded-hybrid freezes.

## Terminal outcome and RW0-D/E separation

The later terminal-outcome fact binds the exact committed decision, result,
and receipt. On acceptance it also binds the immutable bootstrap-acceptance fact identity/digest.
It never creates, updates, deletes, resets, renews, repairs, or replenishes guard truth and is neither a development decision
nor an effect basis. Existing pure terminal-binding validation does not create
a terminal-outcome durable owner.

This contract selects no terminal table, storage, receipt, writer, or recovery
shape. It adds no worker, process, transport, cancellation, Git, Execution
Substrate, publication, RW0-D, or RW0-E semantics.

## Physical-persistence handoff

Migration 0002 decision/version/head/receipt facts remain canonical. A later
bounded-hybrid physical freeze must decide whether supplemental immutable
basis, currentness, graph, result, or recovery relations require migration
0005. Nothing here freezes SQL, a table, column, key, trigger, index, checksum,
reader, writer, migration, catalog entry, or application-generation change.

Migrations 0001 through 0004 must remain unchanged. Migration 0005 must not be
created by this tranche.

## Implementation and audit stop conditions

Implementation must stop and obtain a separately authorized contract before
any of the following: source or SQL creation; migration 0005; a durable writer;
a callable accept path; guard or terminal storage; transaction/controller,
reader, replay, or recovery integration; public/API/package widening; worker,
process, transport, cancellation, Git, ES, publication, RW0-D, or RW0-E work.

A later source tranche is blocked until it freezes exact guard safe values and provisioning,
the bounded-hybrid physical family, exact safe command/result/receipt/recovery
values, mutation-authority integration, and causal implementation tests. If
those owners cannot preserve the three-way no-write/block/unresolved
distinction or the reducer below, the conflict must be surfaced rather than
worked around.

Audit of this tranche must prove that only documentation and documentation-
contract tests changed, the finite reducer is causally exercised without
importing future source, migrations 0001 through 0004 remain exact, migration
0005 is absent, and no source, public, database, runtime, or external-system
effect was introduced.

The contract test therefore carries a temporary source-nonimplementation
guard for this exact documentation/test tranche. It recursively inventories
all non-cache files below `src/ge_nwp_coordinator`, rejects symlinks and
unsupported file types, and binds the current 66 regular files to canonical
manifest payload size 10,877 bytes and SHA-256
`f069130c33d68ebf4d83a2d4d3a3f6aca7d1f1b583decc6138c772bd4ddd721d`.
It is the authoritative source-byte nonimplementation gate for this exact
contract-only tranche and is deliberately superseded by a future authorized
source tranche; it is not an enduring prohibition on Coordinator development.
Supplementary semantic AST checks protect the named authority, import/call,
re-export, package-export, public store/session, owner-module, migration, and
runtime boundaries. They do not claim to detect every conceivable future
neutral-named implementation after the complete manifest barrier is
superseded. Fixed normalized evaluator/helper AST fingerprints are likewise a
temporary control-flow guard supersedable by that later authorized source
tranche.

## Normative finite contract representations

The marked table is the complete human-readable finite representation. Each
value is JSON so nested order and null/boolean types remain exact. The marked
JSON block is the machine-readable representation. This document owns both;
neither is a second semantic owner. Tests parse both, require exact equality,
bind the expanded projection/matrix/branch tables above, and compare the result
with one independent fixed expectation, static source-metadata extraction,
actual production constructor/evaluator/relation witnesses, exact
unreachability-boundary proofs, and current-source AST evidence.

<!-- RW0_C2_DURABLE_DECISION_HUMAN_CONTRACT_BEGIN -->
| Field | JSON value |
| --- | --- |
| `contract_id` | `"rw0-c2-durable-progression-decision-semantic-contract-v2"` |
| `status` | `"accepted_strategic_target_not_implemented"` |
| `outcome_classes` | `["no_write","durable_decision","recovery_unresolved"]` |
| `rejection_classes` | `["required_fact_invalid","basis_identity_lineage_profile_provenance_conflict","stale_caller_expectation","mutation_ref_reuse_conflict","preassigned_identity_or_family_route_collision","matrix_conflict","expected_branch_mismatch","halt_only_matrix_contract_conflict","bootstrap_acceptance_guard_conflict"]` |
| `admission_fault_to_rejection` | `{"malformed_required_fact":"required_fact_invalid","missing_required_fact":"required_fact_invalid","duplicate_required_fact":"required_fact_invalid","partial_required_fact":"required_fact_invalid","foreign_required_fact":"required_fact_invalid","contradictory_required_fact":"required_fact_invalid","owner_conflict":"basis_identity_lineage_profile_provenance_conflict","identity_conflict":"basis_identity_lineage_profile_provenance_conflict","lineage_conflict":"basis_identity_lineage_profile_provenance_conflict","profile_conflict":"basis_identity_lineage_profile_provenance_conflict","provenance_conflict":"basis_identity_lineage_profile_provenance_conflict","stale_caller_head":"stale_caller_expectation","stale_caller_expectation":"stale_caller_expectation","mutation_ref_reused_with_different_digest":"mutation_ref_reuse_conflict","preassigned_identity_collision":"preassigned_identity_or_family_route_collision","family_route_collision":"preassigned_identity_or_family_route_collision"}` |
| `validation_projection` | `[{"source_outcome":"passed","result":"passed","repairability":"not_applicable","reason":"validation_passed","normalized_class":"accept"},{"source_outcome":"failed","result":"repairable_failure","repairability":"repairable","reason":"validation_failed_repairable","normalized_class":"repair"},{"source_outcome":"failed","result":"replan_required","repairability":"same_attempt_insufficient","reason":"validation_failed_replan_required","normalized_class":"replan"},{"source_outcome":"failed","result":"terminal_failure","repairability":"nonrepairable","reason":"validation_failed_terminal","normalized_class":"terminal"},{"source_outcome":"failed","result":"unknown","repairability":"unknown","reason":"validation_failed_unclassified","normalized_class":"nonconclusive"},{"source_outcome":"inconclusive","result":"unknown","repairability":"unknown","reason":"validation_inconclusive","normalized_class":"nonconclusive"},{"source_outcome":"not_run","result":"not_run","repairability":"not_applicable","reason":"validation_not_run","normalized_class":"nonconclusive"}]` |
| `validation_conflict_projection` | `{"source_outcome":"any_v14_allowed_source_outcome","result":"basis_conflict","repairability":"conflict","reason":"source_observation_mismatch","normalized_class":"conflict"}` |
| `review_projection` | `[{"separation_status":"separate","source_outcome":"passed","result":"passed","reason":"review_passed","normalized_class":"accept"},{"separation_status":"separate","source_outcome":"failed","result":"repair_required","reason":"review_failed_repair_required","normalized_class":"repair"},{"separation_status":"separate","source_outcome":"failed","result":"replan_required","reason":"review_failed_replan_required","normalized_class":"replan"},{"separation_status":"separate","source_outcome":"failed","result":"terminal_reject","reason":"review_failed_terminal_reject","normalized_class":"terminal"},{"separation_status":"separate","source_outcome":"failed","result":"unknown","reason":"review_failed_unclassified","normalized_class":"nonconclusive"},{"separation_status":"separate","source_outcome":"inconclusive","result":"unknown","reason":"review_inconclusive","normalized_class":"nonconclusive"}]` |
| `review_override_projection` | `[{"separation_status":"not_separate","source_outcome":"any_v15_allowed_source_outcome","result":"basis_conflict","reason":"review_not_operationally_separate","normalized_class":"conflict"},{"separation_status":"unknown","source_outcome":"any_v15_allowed_source_outcome","result":"unknown","reason":"reviewer_separation_unknown","normalized_class":"nonconclusive"},{"separation_status":"conflict","source_outcome":"any_v15_allowed_source_outcome","result":"basis_conflict","reason":"reviewer_separation_conflict","normalized_class":"conflict"}]` |
| `invalid_projection_rejection` | `"required_fact_invalid"` |
| `normalized_classes` | `["accept","repair","replan","terminal","nonconclusive","conflict"]` |
| `conclusive_severity_low_to_high` | `["accept","repair","replan","terminal"]` |
| `normalized_candidate_branch` | `{"accept":"candidate_acceptance","repair":"candidate_repair","replan":"attempt_selecting_replan","terminal":"program_terminal_reject","nonconclusive":"post_execution_program_block"}` |
| `candidate_reason_by_normalized_class` | `{"accept":"candidate_evidence_conclusively_accepted","repair":"candidate_evidence_requires_repair","replan":"candidate_evidence_requires_replan","terminal":"candidate_evidence_terminally_rejected","nonconclusive":"candidate_evidence_nonconclusive"}` |
| `currentness` | `{"conflict":"no_write","stale":"decision_basis_not_current","unknown":"decision_basis_not_current","current":"continue"}` |
| `matrix` | `{"owners":["standing_policy","risk_lane","decision_time_authority","global_stop","source_effect_ceiling"],"results":["permit","deny","unknown","conflict"],"productive_branches":["candidate_acceptance","candidate_repair","attempt_selecting_replan"],"halt_only_branches":["program_terminal_reject","post_execution_program_block"],"branch_profiles":{"candidate_acceptance":{"applicability":"governed","governed_effect_class":"author_candidate"},"candidate_repair":{"applicability":"governed","governed_effect_class":"author_candidate"},"attempt_selecting_replan":{"applicability":"governed","governed_effect_class":"author_candidate"},"program_terminal_reject":{"applicability":"halt_only","governed_effect_class":null},"post_execution_program_block":{"applicability":"halt_only","governed_effect_class":null}},"permit_reasons":{"standing_policy":{"productive":"policy_permits","halt_only":"halt_only_policy_not_applicable"},"risk_lane":{"productive":"risk_lane_permits","halt_only":"halt_only_risk_not_applicable"},"decision_time_authority":{"productive":"authority_verified_current","halt_only":"halt_only_authority_not_applicable"},"global_stop":{"productive":"global_stop_clear","halt_only":"halt_only_stop_checked"},"source_effect_ceiling":{"productive":"source_effect_within_current_ceilings","halt_only":"halt_only_ceiling_not_applicable"}},"productive_all_permit":"retain_candidate","productive_deny_or_unknown":"convert_to_post_execution_program_block","productive_conflict":"matrix_conflict","halt_only_required_branches":["program_terminal_reject","post_execution_program_block"],"halt_only_required_result":"permit","productive_profile_or_pair_rejection":"matrix_conflict","halt_only_profile_or_pair_rejection":"halt_only_matrix_contract_conflict","exact_conflict_pair_rejection":"matrix_conflict","metadata_unreachable_rejection":"matrix_conflict","malformed_inventory_rejection":"required_fact_invalid"}` |
| `accepted_emittable_pairs` | `{"standing_policy":[{"result":"permit","reason":"halt_only_policy_not_applicable"},{"result":"deny","reason":"policy_revoked"},{"result":"deny","reason":"branch_not_allowed"},{"result":"deny","reason":"risk_lane_not_allowed"},{"result":"deny","reason":"effect_class_not_allowed"},{"result":"unknown","reason":"policy_status_unknown"},{"result":"unknown","reason":"policy_currentness_unknown"},{"result":"permit","reason":"policy_permits"}],"risk_lane":[{"result":"permit","reason":"halt_only_risk_not_applicable"},{"result":"deny","reason":"policy_revoked"},{"result":"deny","reason":"required_lane_mismatch"},{"result":"unknown","reason":"policy_status_unknown"},{"result":"permit","reason":"risk_lane_permits"}],"decision_time_authority":[{"result":"conflict","reason":"snapshot_or_phase_mismatch"},{"result":"conflict","reason":"parent_or_fence_identity_mismatch"},{"result":"conflict","reason":"support_conflict"},{"result":"permit","reason":"halt_only_authority_not_applicable"},{"result":"deny","reason":"authority_denied"},{"result":"deny","reason":"authority_revoked"},{"result":"deny","reason":"attempt_fence_expired"},{"result":"deny","reason":"effect_fence_expired"},{"result":"deny","reason":"authority_grant_expired"},{"result":"deny","reason":"authority_observation_expired"},{"result":"deny","reason":"effect_class_not_allowed"},{"result":"unknown","reason":"authority_status_unknown"},{"result":"unknown","reason":"family_status_unknown"},{"result":"unknown","reason":"revocation_status_unknown"},{"result":"permit","reason":"authority_verified_current"}],"global_stop":[{"result":"permit","reason":"halt_only_stop_checked"},{"result":"deny","reason":"global_stop_active"},{"result":"permit","reason":"global_stop_clear"}],"source_effect_ceiling":[{"result":"conflict","reason":"snapshot_lineage_or_fence_mismatch"},{"result":"conflict","reason":"proposal_evidence_conflict"},{"result":"permit","reason":"halt_only_ceiling_not_applicable"},{"result":"deny","reason":"proposal_evidence_noncompliant"},{"result":"deny","reason":"attempt_fence_expired"},{"result":"deny","reason":"effect_fence_expired"},{"result":"deny","reason":"authority_grant_expired"},{"result":"deny","reason":"authority_observation_expired"},{"result":"deny","reason":"effect_class_not_allowed"},{"result":"deny","reason":"source_effect_exceeds_current_attempt"},{"result":"deny","reason":"source_effect_exceeds_current_authority"},{"result":"unknown","reason":"current_authority_unknown"},{"result":"permit","reason":"source_effect_within_current_ceilings"}]}` |
| `metadata_only_unreachable_pairs` | `{"standing_policy":[{"result":"conflict","reason":"policy_identity_conflict","classification":"no_evaluator_branch"},{"result":"conflict","reason":"evaluator_profile_mismatch","classification":"no_evaluator_branch"},{"result":"conflict","reason":"support_conflict","classification":"no_evaluator_branch"},{"result":"deny","reason":"policy_not_yet_valid","classification":"accepted_relation_precludes"},{"result":"deny","reason":"policy_expired","classification":"valid_construction_precludes"},{"result":"deny","reason":"audience_mismatch","classification":"no_evaluator_branch"},{"result":"deny","reason":"repository_mismatch","classification":"no_evaluator_branch"},{"result":"deny","reason":"path_scope_mismatch","classification":"no_evaluator_branch"},{"result":"deny","reason":"ceilings_exceeded","classification":"no_evaluator_branch"}],"risk_lane":[{"result":"conflict","reason":"risk_source_conflict","classification":"no_evaluator_branch"},{"result":"conflict","reason":"policy_identity_conflict","classification":"no_evaluator_branch"},{"result":"conflict","reason":"evaluator_profile_mismatch","classification":"no_evaluator_branch"},{"result":"conflict","reason":"support_conflict","classification":"no_evaluator_branch"},{"result":"deny","reason":"policy_not_yet_valid","classification":"accepted_relation_precludes"},{"result":"deny","reason":"policy_expired","classification":"valid_construction_precludes"},{"result":"deny","reason":"risk_lane_not_allowed","classification":"accepted_relation_precludes"}],"decision_time_authority":[{"result":"conflict","reason":"profile_mismatch","classification":"no_evaluator_branch"}],"global_stop":[{"result":"conflict","reason":"snapshot_or_stop_identity_mismatch","classification":"valid_construction_precludes"},{"result":"conflict","reason":"profile_mismatch","classification":"no_evaluator_branch"},{"result":"unknown","reason":"global_stop_unknown","classification":"valid_construction_precludes"}],"source_effect_ceiling":[{"result":"conflict","reason":"profile_mismatch","classification":"no_evaluator_branch"},{"result":"conflict","reason":"support_conflict","classification":"valid_construction_precludes"},{"result":"unknown","reason":"proposal_evidence_unknown","classification":"valid_construction_precludes"},{"result":"deny","reason":"source_effect_exceeds_current_effect","classification":"accepted_relation_precludes"}]}` |
| `block_reason_precedence` | `["decision_basis_not_current","candidate_evidence_nonconclusive","productive_branch_not_permitted"]` |
| `branch_mapping` | `{"candidate_acceptance":{"decision_kind":"accept","decision_variant":"candidate_acceptance","version_advancing":true},"candidate_repair":{"decision_kind":"repair","decision_variant":"candidate_repair","version_advancing":true},"attempt_selecting_replan":{"decision_kind":"replan","decision_variant":"attempt_selecting_replan","version_advancing":true},"program_terminal_reject":{"decision_kind":"terminal_reject","decision_variant":"program_terminal_reject","version_advancing":true},"post_execution_program_block":{"decision_kind":"block","decision_variant":"program_block","version_advancing":true}}` |
| `excluded_reducer_decision_kinds` | `["cancel","redeliver"]` |
| `expected_branch` | `{"role":"conflict_assertion_only","mismatch":"expected_branch_mismatch"}` |
| `model` | `{"recommendation_to_branch":{"accept_candidate":"candidate_acceptance","repair_candidate":"candidate_repair","replan":"attempt_selecting_replan","terminal_reject":"program_terminal_reject","block":"post_execution_program_block"},"evaluation_order":"after_bootstrap_guard_gate","may_change_branch":false,"retention":"non_authoritative_evidence","recognized_equal":{"status":"consistent","reason":"mapped_branch_equals_authoritative_branch"},"recognized_unequal":{"status":"inconsistent","reason":"mapped_branch_differs_from_authoritative_branch"},"unrecognized":{"status":"inconsistent","reason":"model_recommendation_unrecognized"}}` |
| `evaluation_trace` | `{"ordered_stages":["basis_validated","matrix_grammar_validated","currentness_reduced","validation_review_reduced","productive_matrix_evaluated","branch_selected","halt_only_matrix_evaluated","bootstrap_acceptance_guard_checked","model_consistency_evaluated"],"productive_matrix_evidence_fields":["provisional_productive_branch","owner_entries"],"model_last":true}` |
| `guard` | `{"owner":".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md","relation_in_command_digest":true,"relation_in_recovery_selector":true,"relation_grants_authority":false,"relation_requests_acceptance":false,"relation_required_every_applicable_command":true,"universal_exact_roles":["lineage","scope","admission","continuity","sole_active","no_foreign_claim"],"accept_required_evidence":"exhaustively_unclaimed","accept_invalid_states":["mismatch","missing","duplicate","malformed","ambiguous","claimed"],"accept_invalid_result":"bootstrap_acceptance_guard_conflict","accept_effect":"create_one_immutable_acceptance_fact","nonaccept_effect":"none","replay_mutates":false,"recovery_family":"complete_decision_family_including_acceptance_fact","accept_writer_callable_before_physical_freeze":false}` |
| `recovery` | `{"requires_commit_attempt_uncertainty":true,"readback":{"exact_family":"committed_exact","provably_absent":"definitely_not_committed","ambiguous":"unresolved"},"unresolved_creates_decision":false,"unresolved_is_branch":false,"automatic_retry_after_unresolved":false}` |
| `terminal` | `{"later_immutable_fact":true,"binds_committed_decision_result_receipt":true,"acceptance_binds_immutable_bootstrap_acceptance_fact":true,"mutates_guard":false,"is_development_decision":false,"is_effect_basis":false}` |
| `physical` | `{"application_generation":2,"current_terminal_migration":"0004_rw0_c1_durable_evidence","canonical_decision_representation_migration":"0002_development_program_and_effect_state","migration_0005_exists":false,"migration_0005_selected":false,"later_freeze":"bounded_hybrid_physical_contract"}` |
| `excluded_effect_domains` | `["worker","process","transport","cancellation","git","execution_substrate","publication","rw0_d","rw0_e"]` |
| `implementation` | `{"durable_decision_writer":false,"bootstrap_acceptance_guard":false,"terminal_outcome_owner":false,"production_caller":false,"public_export":false,"runtime_active":false,"rw0_d":false,"rw0_e":false,"execution_substrate_change":false}` |
| `temporary_source_nonimplementation_guard` | `{"source_root":"src/ge_nwp_coordinator","complete_tree_manifest_status":"superseded_by_authorized_rw0_d1_source_tranche","bounded_scope":"rw0_c2_physical_decision_acceptance_terminal_runtime_only","forbidden_modules_calls_exports_enforced":true,"migration_0005_exists":false,"production_caller_exists":false,"public_export_exists":false,"runtime_active":false}` |
<!-- RW0_C2_DURABLE_DECISION_HUMAN_CONTRACT_END -->

<!-- RW0_C2_P1_COMMAND_DIGEST_V2_DISCLOSURE_SUCCESSOR_BEGIN -->
### RW0-C2 private physical P1 command identity and disclosure successor

The historical semantic `expected_branch` role remains
`conflict_assertion_only`: it cannot select a branch or authorize a decision.
The current private P1 physical mutation binds that assertion in the exact
guarded-command-digest v2 after the six branch-neutral preassignments. Its
domain is
`governed-execution.nwp-rw0-c2-guarded-command-digest.v2.identity`; the
preimage is the historical 30 ordered relation pairs followed by
`expected_branch` as JSON null or an exact finite branch string. The six
preassignments exclude it, while exact replay identity includes it. Reusing
one mutation ref with a different valid assertion is a changed-command
conflict, never historical replay. The command schema remains v1 and the
migration-0002 receipt meaning remains exact.

Protected P1 readback, record-mode exact replay, and recovery require fresh
current positive disclosure posture before returning a committed family.
Receipt-free record mode requires current recording posture before route
probing or writes. Receipt-free read and recovery require disclosure posture
before absence can be reported; recovery additionally requires old-execution
exclusion and complete route-absence proof. Denied or unverifiable disclosure
returns `unresolved` from recovery and no committed result from read or
record. Internal competing-winner completeness verification uses the exact
persisted command digest and does not expose the competing result.
<!-- RW0_C2_P1_COMMAND_DIGEST_V2_DISCLOSURE_SUCCESSOR_END -->

<!-- RW0_C2_DURABLE_DECISION_FINITE_ORACLE_BEGIN -->
```json
{
  "contract_id": "rw0-c2-durable-progression-decision-semantic-contract-v2",
  "status": "accepted_strategic_target_not_implemented",
  "outcome_classes": [
    "no_write",
    "durable_decision",
    "recovery_unresolved"
  ],
  "rejection_classes": [
    "required_fact_invalid",
    "basis_identity_lineage_profile_provenance_conflict",
    "stale_caller_expectation",
    "mutation_ref_reuse_conflict",
    "preassigned_identity_or_family_route_collision",
    "matrix_conflict",
    "expected_branch_mismatch",
    "halt_only_matrix_contract_conflict",
    "bootstrap_acceptance_guard_conflict"
  ],
  "admission_fault_to_rejection": {
    "malformed_required_fact": "required_fact_invalid",
    "missing_required_fact": "required_fact_invalid",
    "duplicate_required_fact": "required_fact_invalid",
    "partial_required_fact": "required_fact_invalid",
    "foreign_required_fact": "required_fact_invalid",
    "contradictory_required_fact": "required_fact_invalid",
    "owner_conflict": "basis_identity_lineage_profile_provenance_conflict",
    "identity_conflict": "basis_identity_lineage_profile_provenance_conflict",
    "lineage_conflict": "basis_identity_lineage_profile_provenance_conflict",
    "profile_conflict": "basis_identity_lineage_profile_provenance_conflict",
    "provenance_conflict": "basis_identity_lineage_profile_provenance_conflict",
    "stale_caller_head": "stale_caller_expectation",
    "stale_caller_expectation": "stale_caller_expectation",
    "mutation_ref_reused_with_different_digest": "mutation_ref_reuse_conflict",
    "preassigned_identity_collision": "preassigned_identity_or_family_route_collision",
    "family_route_collision": "preassigned_identity_or_family_route_collision"
  },
  "validation_projection": [
    {
      "source_outcome": "passed",
      "result": "passed",
      "repairability": "not_applicable",
      "reason": "validation_passed",
      "normalized_class": "accept"
    },
    {
      "source_outcome": "failed",
      "result": "repairable_failure",
      "repairability": "repairable",
      "reason": "validation_failed_repairable",
      "normalized_class": "repair"
    },
    {
      "source_outcome": "failed",
      "result": "replan_required",
      "repairability": "same_attempt_insufficient",
      "reason": "validation_failed_replan_required",
      "normalized_class": "replan"
    },
    {
      "source_outcome": "failed",
      "result": "terminal_failure",
      "repairability": "nonrepairable",
      "reason": "validation_failed_terminal",
      "normalized_class": "terminal"
    },
    {
      "source_outcome": "failed",
      "result": "unknown",
      "repairability": "unknown",
      "reason": "validation_failed_unclassified",
      "normalized_class": "nonconclusive"
    },
    {
      "source_outcome": "inconclusive",
      "result": "unknown",
      "repairability": "unknown",
      "reason": "validation_inconclusive",
      "normalized_class": "nonconclusive"
    },
    {
      "source_outcome": "not_run",
      "result": "not_run",
      "repairability": "not_applicable",
      "reason": "validation_not_run",
      "normalized_class": "nonconclusive"
    }
  ],
  "validation_conflict_projection": {
    "source_outcome": "any_v14_allowed_source_outcome",
    "result": "basis_conflict",
    "repairability": "conflict",
    "reason": "source_observation_mismatch",
    "normalized_class": "conflict"
  },
  "review_projection": [
    {
      "separation_status": "separate",
      "source_outcome": "passed",
      "result": "passed",
      "reason": "review_passed",
      "normalized_class": "accept"
    },
    {
      "separation_status": "separate",
      "source_outcome": "failed",
      "result": "repair_required",
      "reason": "review_failed_repair_required",
      "normalized_class": "repair"
    },
    {
      "separation_status": "separate",
      "source_outcome": "failed",
      "result": "replan_required",
      "reason": "review_failed_replan_required",
      "normalized_class": "replan"
    },
    {
      "separation_status": "separate",
      "source_outcome": "failed",
      "result": "terminal_reject",
      "reason": "review_failed_terminal_reject",
      "normalized_class": "terminal"
    },
    {
      "separation_status": "separate",
      "source_outcome": "failed",
      "result": "unknown",
      "reason": "review_failed_unclassified",
      "normalized_class": "nonconclusive"
    },
    {
      "separation_status": "separate",
      "source_outcome": "inconclusive",
      "result": "unknown",
      "reason": "review_inconclusive",
      "normalized_class": "nonconclusive"
    }
  ],
  "review_override_projection": [
    {
      "separation_status": "not_separate",
      "source_outcome": "any_v15_allowed_source_outcome",
      "result": "basis_conflict",
      "reason": "review_not_operationally_separate",
      "normalized_class": "conflict"
    },
    {
      "separation_status": "unknown",
      "source_outcome": "any_v15_allowed_source_outcome",
      "result": "unknown",
      "reason": "reviewer_separation_unknown",
      "normalized_class": "nonconclusive"
    },
    {
      "separation_status": "conflict",
      "source_outcome": "any_v15_allowed_source_outcome",
      "result": "basis_conflict",
      "reason": "reviewer_separation_conflict",
      "normalized_class": "conflict"
    }
  ],
  "invalid_projection_rejection": "required_fact_invalid",
  "normalized_classes": [
    "accept",
    "repair",
    "replan",
    "terminal",
    "nonconclusive",
    "conflict"
  ],
  "conclusive_severity_low_to_high": [
    "accept",
    "repair",
    "replan",
    "terminal"
  ],
  "normalized_candidate_branch": {
    "accept": "candidate_acceptance",
    "repair": "candidate_repair",
    "replan": "attempt_selecting_replan",
    "terminal": "program_terminal_reject",
    "nonconclusive": "post_execution_program_block"
  },
  "candidate_reason_by_normalized_class": {
    "accept": "candidate_evidence_conclusively_accepted",
    "repair": "candidate_evidence_requires_repair",
    "replan": "candidate_evidence_requires_replan",
    "terminal": "candidate_evidence_terminally_rejected",
    "nonconclusive": "candidate_evidence_nonconclusive"
  },
  "currentness": {
    "conflict": "no_write",
    "stale": "decision_basis_not_current",
    "unknown": "decision_basis_not_current",
    "current": "continue"
  },
  "matrix": {
    "owners": [
      "standing_policy",
      "risk_lane",
      "decision_time_authority",
      "global_stop",
      "source_effect_ceiling"
    ],
    "results": [
      "permit",
      "deny",
      "unknown",
      "conflict"
    ],
    "productive_branches": [
      "candidate_acceptance",
      "candidate_repair",
      "attempt_selecting_replan"
    ],
    "halt_only_branches": [
      "program_terminal_reject",
      "post_execution_program_block"
    ],
    "branch_profiles": {
      "candidate_acceptance": {
        "applicability": "governed",
        "governed_effect_class": "author_candidate"
      },
      "candidate_repair": {
        "applicability": "governed",
        "governed_effect_class": "author_candidate"
      },
      "attempt_selecting_replan": {
        "applicability": "governed",
        "governed_effect_class": "author_candidate"
      },
      "program_terminal_reject": {
        "applicability": "halt_only",
        "governed_effect_class": null
      },
      "post_execution_program_block": {
        "applicability": "halt_only",
        "governed_effect_class": null
      }
    },
    "permit_reasons": {
      "standing_policy": {
        "productive": "policy_permits",
        "halt_only": "halt_only_policy_not_applicable"
      },
      "risk_lane": {
        "productive": "risk_lane_permits",
        "halt_only": "halt_only_risk_not_applicable"
      },
      "decision_time_authority": {
        "productive": "authority_verified_current",
        "halt_only": "halt_only_authority_not_applicable"
      },
      "global_stop": {
        "productive": "global_stop_clear",
        "halt_only": "halt_only_stop_checked"
      },
      "source_effect_ceiling": {
        "productive": "source_effect_within_current_ceilings",
        "halt_only": "halt_only_ceiling_not_applicable"
      }
    },
    "productive_all_permit": "retain_candidate",
    "productive_deny_or_unknown": "convert_to_post_execution_program_block",
    "productive_conflict": "matrix_conflict",
    "halt_only_required_branches": [
      "program_terminal_reject",
      "post_execution_program_block"
    ],
    "halt_only_required_result": "permit",
    "productive_profile_or_pair_rejection": "matrix_conflict",
    "halt_only_profile_or_pair_rejection": "halt_only_matrix_contract_conflict",
    "exact_conflict_pair_rejection": "matrix_conflict",
    "metadata_unreachable_rejection": "matrix_conflict",
    "malformed_inventory_rejection": "required_fact_invalid"
  },
  "accepted_emittable_pairs": {
    "standing_policy": [
      {
        "result": "permit",
        "reason": "halt_only_policy_not_applicable"
      },
      {
        "result": "deny",
        "reason": "policy_revoked"
      },
      {
        "result": "deny",
        "reason": "branch_not_allowed"
      },
      {
        "result": "deny",
        "reason": "risk_lane_not_allowed"
      },
      {
        "result": "deny",
        "reason": "effect_class_not_allowed"
      },
      {
        "result": "unknown",
        "reason": "policy_status_unknown"
      },
      {
        "result": "unknown",
        "reason": "policy_currentness_unknown"
      },
      {
        "result": "permit",
        "reason": "policy_permits"
      }
    ],
    "risk_lane": [
      {
        "result": "permit",
        "reason": "halt_only_risk_not_applicable"
      },
      {
        "result": "deny",
        "reason": "policy_revoked"
      },
      {
        "result": "deny",
        "reason": "required_lane_mismatch"
      },
      {
        "result": "unknown",
        "reason": "policy_status_unknown"
      },
      {
        "result": "permit",
        "reason": "risk_lane_permits"
      }
    ],
    "decision_time_authority": [
      {
        "result": "conflict",
        "reason": "snapshot_or_phase_mismatch"
      },
      {
        "result": "conflict",
        "reason": "parent_or_fence_identity_mismatch"
      },
      {
        "result": "conflict",
        "reason": "support_conflict"
      },
      {
        "result": "permit",
        "reason": "halt_only_authority_not_applicable"
      },
      {
        "result": "deny",
        "reason": "authority_denied"
      },
      {
        "result": "deny",
        "reason": "authority_revoked"
      },
      {
        "result": "deny",
        "reason": "attempt_fence_expired"
      },
      {
        "result": "deny",
        "reason": "effect_fence_expired"
      },
      {
        "result": "deny",
        "reason": "authority_grant_expired"
      },
      {
        "result": "deny",
        "reason": "authority_observation_expired"
      },
      {
        "result": "deny",
        "reason": "effect_class_not_allowed"
      },
      {
        "result": "unknown",
        "reason": "authority_status_unknown"
      },
      {
        "result": "unknown",
        "reason": "family_status_unknown"
      },
      {
        "result": "unknown",
        "reason": "revocation_status_unknown"
      },
      {
        "result": "permit",
        "reason": "authority_verified_current"
      }
    ],
    "global_stop": [
      {
        "result": "permit",
        "reason": "halt_only_stop_checked"
      },
      {
        "result": "deny",
        "reason": "global_stop_active"
      },
      {
        "result": "permit",
        "reason": "global_stop_clear"
      }
    ],
    "source_effect_ceiling": [
      {
        "result": "conflict",
        "reason": "snapshot_lineage_or_fence_mismatch"
      },
      {
        "result": "conflict",
        "reason": "proposal_evidence_conflict"
      },
      {
        "result": "permit",
        "reason": "halt_only_ceiling_not_applicable"
      },
      {
        "result": "deny",
        "reason": "proposal_evidence_noncompliant"
      },
      {
        "result": "deny",
        "reason": "attempt_fence_expired"
      },
      {
        "result": "deny",
        "reason": "effect_fence_expired"
      },
      {
        "result": "deny",
        "reason": "authority_grant_expired"
      },
      {
        "result": "deny",
        "reason": "authority_observation_expired"
      },
      {
        "result": "deny",
        "reason": "effect_class_not_allowed"
      },
      {
        "result": "deny",
        "reason": "source_effect_exceeds_current_attempt"
      },
      {
        "result": "deny",
        "reason": "source_effect_exceeds_current_authority"
      },
      {
        "result": "unknown",
        "reason": "current_authority_unknown"
      },
      {
        "result": "permit",
        "reason": "source_effect_within_current_ceilings"
      }
    ]
  },
  "metadata_only_unreachable_pairs": {
    "standing_policy": [
      {
        "result": "conflict",
        "reason": "policy_identity_conflict",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "conflict",
        "reason": "evaluator_profile_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "conflict",
        "reason": "support_conflict",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "deny",
        "reason": "policy_not_yet_valid",
        "classification": "accepted_relation_precludes"
      },
      {
        "result": "deny",
        "reason": "policy_expired",
        "classification": "valid_construction_precludes"
      },
      {
        "result": "deny",
        "reason": "audience_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "deny",
        "reason": "repository_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "deny",
        "reason": "path_scope_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "deny",
        "reason": "ceilings_exceeded",
        "classification": "no_evaluator_branch"
      }
    ],
    "risk_lane": [
      {
        "result": "conflict",
        "reason": "risk_source_conflict",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "conflict",
        "reason": "policy_identity_conflict",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "conflict",
        "reason": "evaluator_profile_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "conflict",
        "reason": "support_conflict",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "deny",
        "reason": "policy_not_yet_valid",
        "classification": "accepted_relation_precludes"
      },
      {
        "result": "deny",
        "reason": "policy_expired",
        "classification": "valid_construction_precludes"
      },
      {
        "result": "deny",
        "reason": "risk_lane_not_allowed",
        "classification": "accepted_relation_precludes"
      }
    ],
    "decision_time_authority": [
      {
        "result": "conflict",
        "reason": "profile_mismatch",
        "classification": "no_evaluator_branch"
      }
    ],
    "global_stop": [
      {
        "result": "conflict",
        "reason": "snapshot_or_stop_identity_mismatch",
        "classification": "valid_construction_precludes"
      },
      {
        "result": "conflict",
        "reason": "profile_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "unknown",
        "reason": "global_stop_unknown",
        "classification": "valid_construction_precludes"
      }
    ],
    "source_effect_ceiling": [
      {
        "result": "conflict",
        "reason": "profile_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "conflict",
        "reason": "support_conflict",
        "classification": "valid_construction_precludes"
      },
      {
        "result": "unknown",
        "reason": "proposal_evidence_unknown",
        "classification": "valid_construction_precludes"
      },
      {
        "result": "deny",
        "reason": "source_effect_exceeds_current_effect",
        "classification": "accepted_relation_precludes"
      }
    ]
  },
  "block_reason_precedence": [
    "decision_basis_not_current",
    "candidate_evidence_nonconclusive",
    "productive_branch_not_permitted"
  ],
  "branch_mapping": {
    "candidate_acceptance": {
      "decision_kind": "accept",
      "decision_variant": "candidate_acceptance",
      "version_advancing": true
    },
    "candidate_repair": {
      "decision_kind": "repair",
      "decision_variant": "candidate_repair",
      "version_advancing": true
    },
    "attempt_selecting_replan": {
      "decision_kind": "replan",
      "decision_variant": "attempt_selecting_replan",
      "version_advancing": true
    },
    "program_terminal_reject": {
      "decision_kind": "terminal_reject",
      "decision_variant": "program_terminal_reject",
      "version_advancing": true
    },
    "post_execution_program_block": {
      "decision_kind": "block",
      "decision_variant": "program_block",
      "version_advancing": true
    }
  },
  "excluded_reducer_decision_kinds": [
    "cancel",
    "redeliver"
  ],
  "expected_branch": {
    "role": "conflict_assertion_only",
    "mismatch": "expected_branch_mismatch"
  },
  "model": {
    "recommendation_to_branch": {
      "accept_candidate": "candidate_acceptance",
      "repair_candidate": "candidate_repair",
      "replan": "attempt_selecting_replan",
      "terminal_reject": "program_terminal_reject",
      "block": "post_execution_program_block"
    },
    "evaluation_order": "after_bootstrap_guard_gate",
    "may_change_branch": false,
    "retention": "non_authoritative_evidence",
    "recognized_equal": {
      "status": "consistent",
      "reason": "mapped_branch_equals_authoritative_branch"
    },
    "recognized_unequal": {
      "status": "inconsistent",
      "reason": "mapped_branch_differs_from_authoritative_branch"
    },
    "unrecognized": {
      "status": "inconsistent",
      "reason": "model_recommendation_unrecognized"
    }
  },
  "evaluation_trace": {
    "ordered_stages": [
      "basis_validated",
      "matrix_grammar_validated",
      "currentness_reduced",
      "validation_review_reduced",
      "productive_matrix_evaluated",
      "branch_selected",
      "halt_only_matrix_evaluated",
      "bootstrap_acceptance_guard_checked",
      "model_consistency_evaluated"
    ],
    "productive_matrix_evidence_fields": [
      "provisional_productive_branch",
      "owner_entries"
    ],
    "model_last": true
  },
  "guard": {
    "owner": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
    "relation_in_command_digest": true,
    "relation_in_recovery_selector": true,
    "relation_grants_authority": false,
    "relation_requests_acceptance": false,
    "relation_required_every_applicable_command": true,
    "universal_exact_roles": [
      "lineage",
      "scope",
      "admission",
      "continuity",
      "sole_active",
      "no_foreign_claim"
    ],
    "accept_required_evidence": "exhaustively_unclaimed",
    "accept_invalid_states": [
      "mismatch",
      "missing",
      "duplicate",
      "malformed",
      "ambiguous",
      "claimed"
    ],
    "accept_invalid_result": "bootstrap_acceptance_guard_conflict",
    "accept_effect": "create_one_immutable_acceptance_fact",
    "nonaccept_effect": "none",
    "replay_mutates": false,
    "recovery_family": "complete_decision_family_including_acceptance_fact",
    "accept_writer_callable_before_physical_freeze": false
  },
  "recovery": {
    "requires_commit_attempt_uncertainty": true,
    "readback": {
      "exact_family": "committed_exact",
      "provably_absent": "definitely_not_committed",
      "ambiguous": "unresolved"
    },
    "unresolved_creates_decision": false,
    "unresolved_is_branch": false,
    "automatic_retry_after_unresolved": false
  },
  "terminal": {
    "later_immutable_fact": true,
    "binds_committed_decision_result_receipt": true,
    "acceptance_binds_immutable_bootstrap_acceptance_fact": true,
    "mutates_guard": false,
    "is_development_decision": false,
    "is_effect_basis": false
  },
  "physical": {
    "application_generation": 2,
    "current_terminal_migration": "0004_rw0_c1_durable_evidence",
    "canonical_decision_representation_migration": "0002_development_program_and_effect_state",
    "migration_0005_exists": false,
    "migration_0005_selected": false,
    "later_freeze": "bounded_hybrid_physical_contract"
  },
  "excluded_effect_domains": [
    "worker",
    "process",
    "transport",
    "cancellation",
    "git",
    "execution_substrate",
    "publication",
    "rw0_d",
    "rw0_e"
  ],
  "implementation": {
    "durable_decision_writer": false,
    "bootstrap_acceptance_guard": false,
    "terminal_outcome_owner": false,
    "production_caller": false,
    "public_export": false,
    "runtime_active": false,
    "rw0_d": false,
    "rw0_e": false,
    "execution_substrate_change": false
  },
  "temporary_source_nonimplementation_guard": {
    "source_root": "src/ge_nwp_coordinator",
    "complete_tree_manifest_status": "superseded_by_authorized_rw0_d1_source_tranche",
    "bounded_scope": "rw0_c2_physical_decision_acceptance_terminal_runtime_only",
    "forbidden_modules_calls_exports_enforced": true,
    "migration_0005_exists": false,
    "production_caller_exists": false,
    "public_export_exists": false,
    "runtime_active": false
  }
}
```
<!-- RW0_C2_DURABLE_DECISION_FINITE_ORACLE_END -->

RW0-D1 now implements only the separately owned artificial offline process/capsule spine. The boolean `rw0_d = false` above continues to mean that complete RW0-D and D2 closure are not implemented. The temporary complete-tree source manifest is superseded by the scoped C2 nonimplementation guard; C2 branch, recovery, immutable scope admission, and acceptance semantics remain unchanged.

### Physical suffix succession after native Section 41 admission

The additive Section 41 post-execution proposal-family migration 0005 now exists in the current generation-2 catalog. This does not implement this C2 decision reducer. Earlier references reserving 0005 for possible C2 physical decision relations are historical prospective allocations; any separately authorized C2 additive suffix is now later, currently expected no earlier than 0006, with schema and authority still unselected. A checked Section 41 proposal and C1 rank-15 membership are input evidence, never a C2 decision, block, acceptance or terminal fact.

### P1 physical relation/profile successor in the cumulative program

The uncommitted P0/P1 implementation candidate selects migration 0007 for the
five-branch decision family. The versioned relation/result/profile successor is
owned in `.docs/rw0-c2-private-value-versioning.md`; it adds a replan-only
historical work-item-head postimage and exact graph role. This successor
preserves this owner's reducer, no-write conflicts, version advancement,
single generic receipt, exact whole-family replay, and three-way recovery.
The old finite oracle's absence of migration 0005 and physical C2 source is
historical context, not current 0007 catalog truth. The successor is not an
implementation-complete claim until its fenced writer, readback, connected
five-branch proof, and final validation finish.

### Decision-basis v2 physical repair after independent audit

The independently audited uncommitted 21-field basis candidate is a blocked
predecessor. Its stale-currentness block could commit a final
`decision_basis_not_current` reason while omitting the exact typed validation
and independent-review dispositions that selected the distinct candidate
reason. The current physical P1 candidate introduces decision-basis v2 with
those two closed safe typed mappings inside the existing canonical basis BLOB.
The basis digest and dependent identity chain are recomputed. The pure
candidate-reason classifier is shared by fresh reduction and historical
reconstruction; replay verifies both the derived candidate reason and its
finite relationship to the persisted branch/final reason before checking the
whole family. No result-only reason column, new table, branch rule, effect
authority, or target finite-oracle rewrite follows. The exact grammar is owned
by `.docs/rw0-c2-private-value-versioning.md`, and the uncommitted physical
implementation by `.docs/rw0-c2-physical-p0-p1-implementation.md`. Independent
acceptance, publication, and live authority remain separate gates.

<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
### Accepted local P0/P1 physical decision status

The 21-field blocked basis, earlier incomplete P1, and basis-v2 repair
paragraphs above retain their historical wording. Independent artifact audit
accepted tree `161ed4b544baf970cc26428b9805a106ea0f3edf`, and local commit `8704e6c7988250598809f3a0daf88c3e11493488` records the bounded private
artificial-offline implementation. P0 admission is a separate historical
recording transaction and grants no current authority. P1 is one fenced
five-branch decision transaction, with acceptance fact only for acceptance;
that fact is not a terminal result. Decision Basis v2, guarded-command-digest
v2, exact historical work-head witness, universal disclosure, and
acceptance-only current eligibility are implemented private contracts. The
pure decision grammar and owner split above remain unchanged. No live source,
executable permission, product Git effect, ES/Bridge route, service, queue,
scheduler, deployment, autonomy, or publication follows.
<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure current candidate

The uncommitted `artificial_offline_normal.v1` candidate adds a separate private Coordinator terminal writer on generation-2 migration 0008. It consumes checked P0, phase, Section 41 A, C1 rank-15/V22 and P1 evidence under one fenced transaction and records only the five normal outcomes: accept, repair, replan, terminal_reject and block. The P1 decision remains prior decision history; its acceptance fact is bound only for accept and is never mutated. Cancellation, live supplier/contact, ES routing, Git effects, publication and executable permission remain outside this candidate. See `.docs/rw0-terminal-outcome-physical-closure.md`.

P1's five branches, acceptance-only fact, Decision Basis v2 and guarded command digest v2 remain unchanged. The terminal reader verifies complete P1 history from the exact original transient command, including private replan material.
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
