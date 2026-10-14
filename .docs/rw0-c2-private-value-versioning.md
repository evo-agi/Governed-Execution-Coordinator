# RW0-C2 Private Value Versioning and Receipt-Graph Profile

## Status and ownership

Classification: `ACCEPTED TARGET CONTRACT`; none of the private values or
profiles defined here is implemented. This document is the sole owner of the
private RW0-C2 value/versioning and receipt-graph profile seam. The bootstrap
guard owner `.docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md`
owns lineage, scope, admission, continuity, sole-active posture, one-shot
eligibility, permanence, terminal, and ES semantics. The durable-decision owner
`.docs/rw0-c2-durable-progression-decision-semantic-contract.md` retains the
reducer, five branches, decision/version/head, result/receipt, exact replay,
collision taxonomy, and one whole-family recovery classifier. Current source
and migrations alone own implemented v1 bytes and physical storage. The
operating model owns composition and current-status classification. These
private schemas are neither public protocol nor an independent reducer,
provisioner, writer, replay owner, or recovery owner.

An externally authenticated standing-policy admission act is external evidence,
not Coordinator durable authority or execution permission. A later separate
provisioner records an immutable admitted-lineage/scope fact after
verification. The guarded decision writer reads a previously provisioned admission fact;
the separate provisioner owns exact authorized recording and owner-governed
readback/recovery, with no replacement, renewal, orphan repair, or implicit
retry. Positive lineage continuity and one
active authority remain fresh external/current evidence composed with local
writer/session fencing. A local row, its absence, a supplied digest, lock,
writer row, database, machine, or process is insufficient evidence of either
external condition or an unclaimed scope. Retained historical continuity and
sole-active bases record past checks; fresh external verification supplies
current standing permission. Historical
evidence in a committed family records what was checked; protected replay and
recovery use positive current external continuity and sole-active posture
under their owners.

The first-live support profile
`.docs/rw0-c2-first-live-proof-posture.md` selects one non-reissuable
incarnation and continuous original process/storage custody for its initial
RW0-E proof. It does not change this owner's eleven schemas, closed fields,
canonical bytes, digest domains, or graph meanings. A later proof-source
envelope requires separate versioning.

## Closed private value family

The eleven logical schemas and their exact IDs, digest domains, fields, forms,
and authority matrix appear in the single closed block below. Python class
names are deliberately unfrozen. A verified admission-act safe evidence value
projects the authenticated act reference and digest, policy-authored lineage,
scope, guard profile, direct-local applicability, and bounded provenance. The
immutable scope-admission fact binds that verified act and nonrenewable one-shot
ceiling; its identity is independent of machine, process, database, program,
attempt, candidate, command, grant renewal, restore, and relocation identity.
The command relation is an expectation, never admission authority. Its lineage and scope are compared with the existing admission fact; the
caller supplies an expectation. It binds every preassigned decision-family identity and
route needed before reduction.
The continuity and sole-active bases retain exact source identity/digest,
lineage/scope, authority epoch, currentness coordinates, and provenance; a
sole-active basis also identifies the asserted sole authority. Their safe
projection digests do not turn them into standing local facts.

The derived `candidate_acceptance` branch has one immutable acceptance fact
in the same atomic decision/version/head/result/receipt family. It binds the
admitted scope, consuming mutation and command digest, exact decision and
version, historical head postimage, selected attempt/candidate, immutable
basis, family route, and one transaction timestamp. It has no available or
consumed state, revision, reset, renewal, terminal state, or separate receipt.
The four nonaccept branches have no acceptance fact. Every command contains
the mandatory prospective acceptance-fact coordinate and its collision route.
An occupied reserved identity is a collision on every branch. The supplemental
guarded family relation is immutable and binds exact historical head postimage
evidence as the complete verified v1 head identity/postimage tuple, not a
second current-head row; the mutable current head need not retain that
historical value. Relation head ref/revision/digest must equal the nested
postimage program ref/revision/digest, and the nested current-version ref must
equal the resulting version. On acceptance, the fact's head coordinates must
equal those relation coordinates. On acceptance, both relation
`acceptance_fact_ref` and `acceptance_fact_digest` are exact non-null strings:
the former equals the command's reserved prospective ref and the latter equals
the verified digest of the single actual immutable fact. The receipt graph
contains the acceptance role exactly once. On each of the four nonaccept
branches, both relation fields are exactly JSON null/Python `None`, the fact
and its receipt role are absent, and the command and selector retain the
reserved ref and its mandatory collision probe. Null relation fields never
prove an unclaimed scope. A non-null or dangling nonaccept fact claim is
invalid; a durable record at the reserved identity is a collision or
unresolved input under the decision owner's taxonomy. The
guarded result is a versioned composite of this relation and the unchanged
generic v1 result. Its canonical `receipt_graph_profile_id` selects the exact
static role-verification profile and is covered by its self-digest. The
guarded-result member's unchanged generic v1 graph entry consequently binds
that selection. The profile is versioned contract metadata, not a per-family
value, durable row, graph entry, self-digest, or second graph root. The generic
v1 graph digest remains the source-exact digest of the unchanged receipt
preimage and ten common entries, plus `acceptance_fact` only on acceptance.
Neither composite nor profile creates a second durable result or receipt.
The recovery selector and result are
transient query/projection values, never durable authority.

Logical `command_relation` and `guarded_result` are relations or composites
rather than mandatory standalone rows. Their schema IDs and domains identify
canonical private projections, not a selected table or new v1 receipt field.
`receipt_graph_profile` is a static definition selected by its schema ID and
version; it has no per-instance digest domain. A profile-version change needs
a new ID/version and a successor guarded-result contract. A future physical
contract is the seam for supplemental representation under these exact
semantics.

## Prospective acceptance-fact identity

Every guarded command has a mandatory, non-null, exact-string
`preassigned_acceptance_fact_ref`, including all four nonaccept branches. This
is a prospective reserved identity and an expected-coordinate assertion only;
it is neither a fact claim nor permission to create one. The Coordinator
independently derives it before branch reduction. Its presence or absence
has no branch-selection effect; absence or JSON null is invalid command
grammar before reduction. The reference is always covered by
the command digest and recovery selector, and its identity is collision-probed
on every branch. A wrong derived reference is invalid even when the eventual
branch is nonaccept. The nonaccept family and receipt graph have no fact
member at that reference; the reserved coordinate remains a collision probe.

The exact prospective-ref preimage is the same branch-neutral
`guarded_family_preassignment_basis_v1` transcript used by all six sibling
preassignments below. Its ordered primitive pairs, types, origins, domains,
and fixed vectors are frozen in the machine block. It contains no other
preassigned ref or route. Serialize the ordered `[name, value]` pairs as UTF-8
JSON with `ensure_ascii=False`, `allow_nan=False`, compact separators, and no
coercion. Compute lowercase SHA-256 over the exact prospective-ref domain,
one NUL byte, and those JSON bytes. The command assertion must equal the
Coordinator-derived reference byte-for-byte. This prospective-ref domain is
separate from the acceptance-fact row's identity/digest domain and does not
alter that row's immutable content.

The decision owner's authoritative derived branch determines membership:
`candidate_acceptance` has exactly one immutable fact at the reserved
reference; each other branch has none in the family or receipt graph. Nonaccept fact absence is not evidence of an unclaimed scope. A caller-provided coordinate has no branch effect.

## Branch-neutral preassignment and canonical identity

`guarded_family_preassignment_basis_v1` is an exact derivation transcript
inside the admitted-command relation, not a twelfth logical value, durable
authority, or public DTO. Its 24 ordered primitive coordinates are the full
command-digest inclusion inventory before the six preassignments.
`command_profile` is the literal `command_relation.schema_id`; it adds no
field to that logical schema. The command relation carries the four exact
`continuity_source_ref`, `continuity_source_digest`, `sole_active_source_ref`,
and `sole_active_source_digest` fields at their preassignment positions. They
bind independently verified external basis values and remain historical
expectations. The transcript is built from this closed relation and verified
external values, never extra flat fixture keys. Lineage,
scope, admission act/fact, guard profile, and applicability are checked against
independent verified admission evidence. Safe continuity and sole-active
basis/source expectations are checked against current external evidence; a
historical projection alone supplies no current permission. Mutation identity,
program identity, decision basis, and current-head expectations are checked
against their respective decision-owner state and mutation rules. Each
primitive is available before branch reduction and independent of the command
digest, sibling preassignments, branch, result, receipt, transaction time,
terminal outcome, postcommit state, and raw credentials or attestations.

The six preassigned decision, resulting-version, guarded-relation,
guarded-result, family-route, and prospective-fact identities are **siblings**.
Each hashes exactly the same compact UTF-8 ordered primitive-pair transcript
under its own frozen UTF-8 domain plus one NUL byte. Each output is exactly
64 lowercase SHA-256 hex characters. No sibling reads another sibling or the
command digest. The command digest is derived only after independent
validation of all six and covers the 24 primitives and all six assignments.
Its complete grammar remains with the decision owner. The canonical decision,
version, and historical head then use the reserved refs after the authoritative
branch is derived. Acceptance yields one fact at the reserved ref.
Branch-specific canonical digests precede the single generic receipt graph;
replay and recovery are projections afterward.

The guarded relation contains the canonical command digest and full current-v1 historical-head postimage. Its field-to-node map declares every one of the 26 raw preimage owners. The complete supplied relation is checked field by field against independently verified admission, the closed command and digest, the actual C2 branch, canonical current-v1 decision/version/head/result values, and target guarded members. Its self-digest and all downstream guarded, graph, and receipt digests may be recomputed without changing those source equalities. Omitted, duplicate, extra, reordered, null-for-required, and Boolean-as-integer fields fail closed. Acceptance fact value and digest enter only the acceptance expansion. The machine-readable `dependency_registry` contains 86 closed nodes and 266
common edges partitioned into `fresh_write_construction_v1`,
`exact_replay_readback_v1`, and `uncertain_commit_recovery_v1`. The five fresh
branch expansions contain 70 nodes and 221 edges on acceptance and 68 nodes
and 205 edges on each nonaccept branch. The exact replay graph contains seven
nodes and eight edges; the uncertain-commit recovery graph contains 56 nodes
and 157 edges. Every node declares exact lifecycle membership, and each
partition is topologically sorted independently. There is no cross-partition
execution order. Acceptance-only nodes and edges are absent from every
nonaccept fresh graph. Recovery observations and both projections are absent
from fresh construction. A post-read stage label is descriptive only and does
not establish order against fresh construction. The static receipt-profile
definition is outside every per-family runtime graph; a contract literal
supplies its ID to the guarded result. One
`transaction_timestamp` is assigned after branch derivation. It feeds the
unchanged v1 decision `decided_at`, resulting version `created_at`, historical
head postimage `updated_at`, and receipt/graph-preimage `committed_at` before
the corresponding digests. It feeds no preassignment, command digest, branch,
admission fact, or precommit recovery selector. The source-exact receipt
preimage and ten-or-eleven exact entries precede graph hashing; the final v1
receipt row follows that digest and has no invented self-digest. Every node states stage,
closed origin class, exact dependencies, and prohibited dependencies. Stage
order constrains fresh construction only; exact dependency closure and a
complete topological sort constrain each lifecycle. An aggregate digest may
not conceal a reverse edge. Conditional acceptance nodes are present in the
registry but materialize only on the acceptance branch. No post-branch value
feeds a preassignment.

Each new private identity uses its listed v1 schema ID and digest domain. Its
closed field set has exact built-in types: safe refs and enum strings are
strings, counters are integers but never booleans, optional references use
actual JSON null, and digests are lowercase 64-character SHA-256 hex. Reject
unknown fields, duplicate JSON keys at every depth, non-finite numbers, and
implicit coercion before digest comparison. The self-digest field named last
in a schema is excluded from its own identity. Identity bytes are UTF-8 JSON
with `ensure_ascii=False`, `allow_nan=False`, sorted keys, and separators
`(',', ':')`; the digest is lowercase SHA-256 of the UTF-8 domain, one NUL
byte, and those identity bytes. Array order is significant. These rules
version only the new private family and do not alter existing v1 domains or
serialization. External source digests remain externally authenticated
claims, not recomputed Coordinator identity claims.

The acceptance-fact content digest excludes result and receipt; admission is
independent of decision, result, receipt, and terminal fact.
Relation/result preassigned refs never depend on their content digests or the
final receipt digest. The selector contains no transaction timestamp or
postcommit-only digest.

`guarded_command_digest_v1` hashes the exact ordered 30 name/value pairs in
`command_digest.ordered_preimage` using compact UTF-8 JSON and the domain
`governed-execution.nwp-rw0-c2-guarded-command-digest.v1.identity`, followed
by one NUL byte. The fixed command vector digest is
`a392abcc3f0981b4ac2aeab5d3869aea9f24ba7305b242563e3a41f402b716b1`.
It is a derived command identity, not a standing grant or another logical
schema. Its six sibling values are independently derived from the 24 primitive
coordinates before command digest formation. The future guarded command digest semantically covers the closed inclusion
inventory below: admitted lineage/scope, admission fact and act expectations,
guard profile/applicability, safe continuity and sole-active source/basis
expectations, mutation and every preassigned decision/version/prospective
acceptance-fact/relation/result identity, deterministic route, and the decision owner's exact
basis and current-head expectation. It excludes caller-authored branch or
acceptance conclusion, transaction timestamp, resulting row digests, receipt
graph digest, terminal outcome, raw credentials, and raw attestations. The
decision owner remains responsible for its complete command grammar; this
profile fixes only the added guarded semantic coverage.

## Branch graph and replay/recovery

Fresh construction first verifies the admission act and immutable fact, the
explicit current continuity and sole-active postures, and the current
decision basis, head, and program identity. It closes the command relation and
24-coordinate transcript, derives six sibling preassignments, and computes
the canonical command digest. The required
`validated_admission_command_and_current_posture` node then binds the verified
admission values, closed command relation, command digest, all six validated
sibling expectations, both fresh current posture observations, and the local
writer/session fence. That fence is only a future transaction-owner
prerequisite; it does not issue lineage authority. An invalid or missing
admission or current posture leaves the authoritative branch unmaterialized.
The authoritative branch also consumes the exact C2 decision basis and
currentness inputs. One transaction timestamp follows the branch. The branch
then determines canonical current-v1 members, optional acceptance fact,
guarded relation and result, exact entries and receipt preimage, graph digest,
and final generic v1 receipt row.

Exact replay is a separate post-read graph. Receipt-first mutation lookup,
the exact canonical command digest, fresh current posture for protected
disclosure, and the complete already-persisted family feed only
`replay_projection`. It returns the original committed timestamp and family.
It creates no branch, timestamp, fact, relation, result, graph entry, receipt,
admission, or scope state. Uncertain-commit recovery is another post-read
graph: canonical command and complete-family selector, fresh current posture,
and eight actual typed route observations form the complete observation set
before the decision owner's recovery projection. Its route observations do
not construct or mutate any durable family member. Shared identity and
posture nodes declare each lifecycle in which their value is used; neither
post-read projection can feed the fresh authoritative branch or durable family.

The machine block's graph roles are logical required members. The receipt is
the root and is not an entry in its own graph. Each common role occurs once
with exact role, ordinal, reference, digest source, and verified member
semantics as frozen in `graph.role_bindings`;
`acceptance_fact` is an additional required role exactly once for
`candidate_acceptance` and forbidden for every nonaccept branch. A historical
head role binds the committed postimage recorded by the relation, not a claim
that the mutable head still has that value. The admission act and currentness
bases are retained safe evidence roles; they never replace fresh external
verification. The static profile has no graph role or per-instance digest.
The future writer forms the unchanged generic v1 receipt fields except
`mutation_graph_digest`, including the single `committed_at`, and the exact
ordered graph entries. Current v1 `_receipt_graph_identity` hashes those
receipt fields and entries under its existing domain. The final v1 receipt
row adds only that computed graph digest. The guarded-result member contains
the selected profile ID; its exact member ref/digest is in the existing common
role inventory. Completeness verification reconstructs the current v1 graph
digest, verifies every exact member, checks the guarded-result profile and
branch, then checks static profile roles and cardinality. The supplied v1
graph primitive hashes supplied entries, but the profile separately proves
required-role completeness, no extra/duplicate roles, exact member
reconstruction, correct branch, and receipt binding. A
matching graph digest alone proves none of those propositions. Nonaccept
absence is a branch grammar rule, not a caller-controlled null or evidence
that scope remains unclaimed.

Exact replay is owned by the decision owner. Its projection contains the original decision,
version, historical head postimage, optional original acceptance fact, guarded
relation/result, one receipt, and original transaction timestamp. Its projection
has no newly created or reconstructed fact, branch or eligibility reevaluation,
new transaction timestamp, current-head alteration, or scope renewal. The
complete-family selector covers
the command-bound lineage/scope/admission expectation, mutation, decision,
version, mandatory prospective fact identity, route, and the closed collision
routes below. The recovery projection consumes the exact `complete_family_recovery_observation_set_v1`
post-read derivation: one typed observation for every mandatory route,
canonical lineage and scope, and separate fresh current continuity and
sole-active posture refs and digests. Each route observation has exactly
`route_role`, `route_key`, `status`, `read_attempted`, `readable`,
`evidence_ref`, `evidence_digest`, and `total_absence_proved` in that order.
A route key is an exact ordered array of nonempty strings. Evidence ref is
either a nonempty string or null; evidence digest is either lowercase
64-character hex over safe observation evidence or null. The transient digest
is SHA-256 of the UTF-8 domain
`governed-execution.nwp-rw0-c2-route-observation-evidence.v1`, one NUL byte,
and the UTF-8 evidence ref. Neither coordinate is durable family authority.
The closed statuses are `unchecked`,
`exact_complete_family`, `absent`, `partial`, `duplicate`, `foreign`,
`malformed`, `unreadable`, `route_identity_conflict`, and
`competing_complete_scope_winner`. `unchecked` has no attempted or readable
read, no evidence pair, and no absence proof. `unreadable` has an attempted
but unreadable read, no evidence pair, and no absence proof. `absent` has an
attempted readable read, no evidence pair, and proved total absence. Every
other status has an attempted readable read, a nonempty evidence ref, a valid
evidence digest, and no absence proof. Missing observations never become
absence. Recovery classifies this observation set; it cannot infer missing
rows from local absence elsewhere.
The selector is a precommit query plan and uses no transaction timestamp. Local absence alone supplies no unclaimed-scope inference. One recovery result is exactly
`committed_exact`, `definitely_not_committed`, or `unresolved` under the
decision owner's existing three-way classifier. Same mutation and same digest
with an exact complete family replays; same mutation and different digest
conflicts. Preassigned identity/route collision, a different complete winner,
partial/orphan/duplicate/malformed/foreign/unreadable family, or restore/clone
without proved continuity remain unresolved for exact replay or fresh
permission. The original-family `definitely_not_committed` total-absence classification
has positive current continuity, sole-active posture, and exhaustive absence
across every mandatory collision route as prerequisites; fresh retry
eligibility is a separate decision. Local absence without that current
posture is `unresolved`.
The transient private `validated_current_recovery_posture_v1` is the safe
value-level result of fresh external-current verification for one exact
lineage and scope. It is not one of the eleven logical schemas, a durable row,
or a public protocol. Its ordered fields are `lineage_ref`, `scope_ref`,
`current_continuity_posture_ref`, `current_continuity_posture_digest`,
`continuity_state`, `current_sole_active_posture_ref`,
`current_sole_active_posture_digest`, and `sole_active_state`. Every field is an
exact built-in string; refs are nonempty and digests are lowercase 64-character
hexadecimal strings. The closed continuity states are
`positively_established`, `missing`, `stale`, `unknown`, `conflicting`, and
`negative`. The closed sole-active states are
`exactly_one_active_authority`, `missing`, `stale`, `unknown`, `conflicting`,
and `not_exactly_one`. Only the first state in each list is positive. Literal
ref/digest identity does not define positivity. The record must bind the
selector's lineage and scope and the fresh observation's posture coordinates
and states. Retained historical bases cannot construct it.

The transient `complete-family-recovery-result-v1` has exactly seven
semantic payload fields in this order: `classification`, `lineage_ref`,
`scope_ref`, `current_continuity_posture_ref`,
`current_continuity_posture_digest`, `current_sole_active_posture_ref`,
and `current_sole_active_posture_digest`. The uniform logical-schema
`schema_id` precedes those fields as a type identifier; there is no
result self-digest or composite external-posture coordinate. The projector
copies lineage, scope, and both current posture pairs from that validated
current record after exact selector and observation binding. The closed
projector inputs are the validated observation set, canonical command/branch/
family/selector binding, and validated current record. It computes
classification from the complete bound route observations and current states;
callers cannot supply a classification. With positive current states, a
complete original family is
`committed_exact`; proved absence on all eight routes with positive current
posture is `definitely_not_committed`; a different complete scope winner
also proves original-command noncommit but grants no fresh eligibility.
Every other observation is `unresolved`. A well-formed nonpositive current
record always returns `unresolved`, including when route observations appear
complete or absent; it does not raise merely for a missing, stale, unknown,
conflicting, negative, or not-exactly-one state. Malformed fields or a
lineage/scope mismatch fail value validation before projection.

| Position | Recovery-result semantic field | Validated source |
|---:|---|---|
| 1 | `classification` | complete observation classifier |
| 2 | `lineage_ref` | canonical selector and bound observation |
| 3 | `scope_ref` | canonical selector and bound observation |
| 4 | `current_continuity_posture_ref` | fresh current continuity observation |
| 5 | `current_continuity_posture_digest` | fresh current continuity observation |
| 6 | `current_sole_active_posture_ref` | fresh current sole-active observation |
| 7 | `current_sole_active_posture_digest` | fresh current sole-active observation |

The static `rw0-c2-private-value-contract-v1` vocabulary profile freezes the
three lifecycle IDs, ten route-observation statuses, and seven recovery-result
payload fields. Changing any of these requires a successor profile and
contract ID; no V1 consumer silently reinterprets them.

Recovery's result binds its classification to the observation set's canonical
lineage and scope and copies both validated fresh current posture ref/digest
pairs exactly. The two state fields remain classification inputs and never
enter the result payload. Historical basis rows cannot fill either current
pair. The result
never confers fresh retry or acceptance eligibility. Recovery performs no
fragment repair, branch reevaluation, new timestamp,
automatic retry, scope renewal, or second classification.

## Closed recovery collision routes

`collision_route_templates` is closed contract metadata with exactly eight
ordered elements, each containing `role`, `kind`, `key_sources`, and
`expected_schema_id`. A concrete selector's `required_collision_routes` is
an eight-element query-plan value with exactly `role`, `kind`, `key`, and
`expected_schema_id` per element. The concrete `key` is always an ordered
array of exact nonempty strings, including one-element arrays for single-key
routes. For each template, it is exactly the ordered values of the selector's
top-level fields named by `key_sources`. No concrete route contains
`key_sources`; no template contains `key`. Every selector, for every branch,
carries each role below exactly once in this order. A schema ID is an exact
versioned string where one record type is addressed, and JSON null is allowed
only for the two routes that do not address one record type. Null is never
allowed in a key. The closed route grammar rejects additional, omitted,
duplicate, reordered, or substituted routes and keys. These routes are read-only
query-plan coordinates, not durable authority or another collision/recovery
owner.

1. `mutation_receipt_route`: `receipt_replay`, key `mutation_ref`, generic v1
   receipt schema; reaches the receipt and replay route.
2. `decision_identity_route`: `preassigned_identity`, key `decision_ref`,
   generic v1 decision schema.
3. `resulting_version_identity_route`: `preassigned_identity`, key
   `version_ref`, generic v1 program-version schema.
4. `acceptance_fact_identity_route`: `preassigned_identity`, key
   `acceptance_fact_ref`, acceptance-fact schema; mandatory even for nonaccept.
5. `guarded_family_relation_identity_route`: `preassigned_identity`, key
   `relation_ref`, guarded-family-relation schema.
6. `guarded_progression_result_identity_route`: `preassigned_identity`, key
   `guarded_result_ref`, guarded-result schema.
7. `deterministic_family_route`: `deterministic_family`, key `family_route`,
   with no single-record schema.
8. `admitted_scope_winner_route`: `scope_complete_winner`, ordered key
   `lineage_ref`, `scope_ref`, `admission_fact_ref`, `admission_fact_digest`,
   with no single-record schema; observes a different complete winner.

The following prose table independently states the exact route inventory.
Source coordinates are ordered selector fields.

| Role | Kind | Ordered source coordinates | Expected schema |
|---|---|---|---|
| `mutation_receipt_route` | `receipt_replay` | `mutation_ref` | `governed-execution.nwp-development-mutation-receipt.v1` |
| `decision_identity_route` | `preassigned_identity` | `decision_ref` | `governed-execution.nwp-development-decision.v1` |
| `resulting_version_identity_route` | `preassigned_identity` | `version_ref` | `governed-execution.nwp-development-program-version.v1` |
| `acceptance_fact_identity_route` | `preassigned_identity` | `acceptance_fact_ref` | `governed-execution.nwp-rw0-c2-bootstrap-acceptance-fact.v1` |
| `guarded_family_relation_identity_route` | `preassigned_identity` | `relation_ref` | `governed-execution.nwp-rw0-c2-guarded-family-relation.v1` |
| `guarded_progression_result_identity_route` | `preassigned_identity` | `guarded_result_ref` | `governed-execution.nwp-rw0-c2-guarded-progression-result.v1` |
| `deterministic_family_route` | `deterministic_family` | `family_route` | `null` |
| `admitted_scope_winner_route` | `scope_complete_winner` | `lineage_ref`, `scope_ref`, `admission_fact_ref`, `admission_fact_digest` | `null` |

No route key or expected schema depends on transaction timestamp or a final
receipt/result digest. Original-family noncommit by total absence has three prerequisites: all
eight routes checked, exhaustive absence, and positive current external
continuity plus sole-active posture. Missing,
duplicate, malformed, foreign, unreadable, or unchecked routes, partial/orphan
members, and local absence without positive current posture are `unresolved`.
A different complete winner under the admitted scope is evidence of original
command noncommit under the decision owner's classifier and makes fresh acceptance ineligible; it grants no
retry permission. Exact complete-family replay projects the original fact, if any, and the
original timestamp. Recovery neither repairs fragments nor
reevaluates the branch, renews scope, or retries automatically.

## Normative semantic boundaries

The following tagged clauses are the exact target-only value boundaries.
They state requirements of the existing guard and decision owners. Tagged
registered clauses are the only authority-sensitive normative prose outside
the machine block. Other prose is explanatory and nonnormative; it contains
no closed subject-plus-modal authority construction. The machine registry
and these tagged statements are independently authored and checked for agreement.

NORMATIVE historical_basis_non_authority [historical_basis_not_current_permission]: Retained historical continuity and sole-active bases never become current standing permission.

NORMATIVE current_external_posture [fresh_posture_required_for_protected_disclosure]: Protected replay and recovery require positive current external continuity and sole-active posture.

NORMATIVE mandatory_prospective_fact_coordinate [derived_nonnull_coordinate_required]: Every guarded command requires a non-null Coordinator-derived prospective acceptance-fact ref before branch reduction.

NORMATIVE branch_nonselection [coordinate_cannot_force_or_veto_branch]: Supplying or withholding the prospective fact coordinate cannot force or veto the authoritative branch.

NORMATIVE nonaccept_fact_collision [nonaccept_fact_absent_but_collision_probed]: Every nonaccept branch forbids fact membership while retaining and collision-probing the reserved fact identity.

NORMATIVE closed_collision_routes [eight_exact_routes_required]: Every branch requires the exact ordered eight-route collision inventory with no omissions or extensions.

NORMATIVE total_absence_currentness [local_absence_cannot_prove_noncommit]: Local absence without positive current continuity and sole-active posture is unresolved, never definitely_not_committed.

NORMATIVE replay_original_fact_timestamp [replay_creates_no_fact_or_timestamp]: Exact replay returns the original fact if present and the original transaction timestamp; it creates neither a new fact nor a new timestamp.

NORMATIVE admitted_scope_only [command_relation_cannot_admit_scope]: A command relation must match an already admitted lineage and scope and cannot select an unadmitted scope.

NORMATIVE separate_admission_decision_writers [decision_writer_cannot_provision_admission]: The guarded decision writer cannot provision or repair an admission fact; only the separate admission provisioner may record it.

NORMATIVE single_result_receipt_replay_recovery [one_decision_owned_result_receipt_replay_recovery]: The guarded family retains one logical result, one receipt, one replay owner, and one recovery classifier under the decision owner.

NORMATIVE terminal_nonreplenishment [terminal_cannot_replenish_acceptance]: A terminal outcome cannot replenish acceptance.

NORMATIVE es_nonreplenishment [es_cannot_replenish_direct_local_allowance]: ES routing cannot replenish the direct-local allowance.

The machine block's closed `normative_clause_registry` contains thirteen
clause records. Each declares one unchanged owner document and marker, a
nonempty ordered list of exact pointer/comparison/expected-value assertions,
and one named private structural consequence. Pointer comparisons read only
the unchanged owner value; they never derive an action or polarity. Every
consequence names a private grammar invariant checked separately, and each
visible `NORMATIVE` tag carries both the clause and consequence ID.
The private `rw0-c2-private-owner-assertions-v1` profile fixes their exact
order and 37 assertions. Its digest is SHA-256 of the UTF-8 domain
`governed-execution.nwp-rw0-c2-private-owner-assertions.v1`, one NUL byte,
and compact sorted-key JSON of the ordered registry without a trailing
newline. Repository tests detect one-sided drift; only a fresh independent
audit can authenticate coordinated edits to the private contract and verifier.
The bounded visible-text parser checks headings, paragraphs, quotes, lists,
continuations, table cells, and link labels outside fenced code. It segments
sentences, contrastive clauses, and comma-separated clauses beginning with a
recognized modal before evaluating protected actions, and
carries an immediately preceding protected subject into a modal or action-led
contrastive clause within the same visible block. Each action has its own
polarity, so a prohibition on one action cannot cancel permission for another.
Exact neutral noun phrases such as `replay glossary`, `replay diagram`,
`replay example`, and `replay documentation` remain explanatory even when
they quote protected action wording; `receipt documentation` and
`timestamp terminology` likewise do not name protected authority subjects.
Immediate `it` inherits a protected subject only within the same visible
Markdown block. The parser is closed grammar, not unrestricted language
inference. Owner markers are stable identifiers, not line numbers.

## Current v1 and B1 boundaries

Migration-0002 `development_decisions`, `development_program_versions`,
`development_program_heads`, generic progression result projection, generic
`development_mutation_receipts`, and the supplied mutation-graph digest
primitive keep their current v1 field order, canonical bytes, schema IDs,
domains, and meanings. No v1 canonical value gains a field or silently gains
lineage, scope, admission, acceptance, or recovery authority. The new guarded
relation, result composite, and receipt profile supplement those v1 records;
the generic receipt remains one logical receipt. The machine block records the
relevant current v1 inventory for source-derived verification.

The B1 `latch_postimage_ref` / `latch_postimage_digest` pair keeps its exact
names, order, nullability, bytes, domain, and budgets. It proves supplied
representation and pair coherence only. The guarded decision writer has no
B1-pair read or consumption path. The pair is neither admission, acceptance, uniqueness,
family membership, continuity, replay, nor recovery proof. A later terminal
consumer requires its own separately accepted safe-value
compatibility/versioning contract; no B1 successor is defined here. A
terminal fact has no acceptance-creation, reset, repair, renewal, or
replenishment effect.
Later ES routing has no direct-local-allowance replenishment effect.

## Future handoff

A later bounded-hybrid physical contract is the seam for these logical values
through an additive migration `0005` while preserving migrations 0001–0004.
This document does not choose any SQL table, column, index, trigger, row,
reader, query, transaction, collision query, writer entry signature, or
recovery implementation. Admission provisioning and continuity issuer,
transport, transfer, and currentness protocols require their own contracts.
No migration `0005`, source module, reader, writer, provisioner, production
caller, package export, public method, runtime, RW0-D/E, or ES behavior is
implemented by this tranche.

## Closed machine-readable contract

This one block is a finite target-value registry and profile, not a physical
schema or an executable reducer. The prose above and the independent contract
test constrain its meaning.

<!-- RW0_C2_PRIVATE_VALUES_MACHINE_BEGIN -->
```json
{
  "contract_id": "rw0-c2-private-value-versioning-v1",
  "status": "accepted_target_not_implemented",
  "owners": {
    "guard": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
    "decision": ".docs/rw0-c2-durable-progression-decision-semantic-contract.md",
    "values": ".docs/rw0-c2-private-value-versioning.md",
    "composition": ".docs/autonomous-software-development-operating-model.md",
    "implemented_v1": "current_source_and_migrations"
  },
  "canonicalization": {
    "json": "utf8_ensure_ascii_false_allow_nan_false_sort_keys_compact",
    "digest": "sha256(domain_utf8+nul+identity_json_utf8)",
    "self_digest": "excluded",
    "unknown_fields": "reject",
    "duplicate_keys_recursive": "reject",
    "types": "exact_builtin_no_bool_as_int",
    "array_order": "significant"
  },
  "schemas": [
    [
      "admission_act",
      "governed-execution.nwp-rw0-c2-verified-admission-act.v1",
      "governed-execution.nwp-rw0-c2-verified-admission-act.v1.identity",
      "external_safe_evidence",
      [
        "schema_id",
        "act_ref",
        "act_digest",
        "lineage_ref",
        "scope_ref",
        "guard_profile",
        "applicability",
        "provenance_ref",
        "provenance_digest",
        "projection_digest"
      ]
    ],
    [
      "scope_admission_fact",
      "governed-execution.nwp-rw0-c2-scope-admission-fact.v1",
      "governed-execution.nwp-rw0-c2-scope-admission-fact.v1.identity",
      "immutable_durable_fact",
      [
        "schema_id",
        "admission_fact_ref",
        "act_ref",
        "act_digest",
        "lineage_ref",
        "scope_ref",
        "guard_profile",
        "applicability",
        "provenance_ref",
        "provenance_digest",
        "one_shot_ceiling",
        "admission_fact_digest"
      ]
    ],
    [
      "command_relation",
      "governed-execution.nwp-rw0-c2-admitted-command-relation.v1",
      "governed-execution.nwp-rw0-c2-admitted-command-relation.v1.identity",
      "transient_command_relation",
      [
        "schema_id",
        "lineage_ref",
        "scope_ref",
        "admission_fact_ref",
        "admission_fact_digest",
        "guard_profile",
        "applicability",
        "admission_act_ref",
        "admission_act_digest",
        "continuity_basis_ref",
        "continuity_basis_digest",
        "continuity_source_ref",
        "continuity_source_digest",
        "sole_active_basis_ref",
        "sole_active_basis_digest",
        "sole_active_source_ref",
        "sole_active_source_digest",
        "mutation_ref",
        "program_ref",
        "decision_basis_ref",
        "decision_basis_digest",
        "expected_head_ref",
        "expected_head_revision",
        "expected_head_digest",
        "preassigned_decision_ref",
        "preassigned_version_ref",
        "preassigned_acceptance_fact_ref",
        "preassigned_relation_ref",
        "preassigned_guarded_result_ref",
        "family_route",
        "relation_digest"
      ]
    ],
    [
      "continuity_basis",
      "governed-execution.nwp-rw0-c2-verified-lineage-continuity.v1",
      "governed-execution.nwp-rw0-c2-verified-lineage-continuity.v1.identity",
      "external_current_safe_evidence",
      [
        "schema_id",
        "basis_ref",
        "source_ref",
        "source_digest",
        "lineage_ref",
        "scope_ref",
        "authority_epoch_ref",
        "currentness_ref",
        "currentness_digest",
        "provenance_ref",
        "provenance_digest",
        "projection_digest"
      ]
    ],
    [
      "sole_active_basis",
      "governed-execution.nwp-rw0-c2-verified-sole-active.v1",
      "governed-execution.nwp-rw0-c2-verified-sole-active.v1.identity",
      "external_current_safe_evidence",
      [
        "schema_id",
        "basis_ref",
        "source_ref",
        "source_digest",
        "lineage_ref",
        "scope_ref",
        "authority_epoch_ref",
        "currentness_ref",
        "currentness_digest",
        "active_authority_ref",
        "sole_active_assertion_ref",
        "sole_active_assertion_digest",
        "provenance_ref",
        "provenance_digest",
        "projection_digest"
      ]
    ],
    [
      "acceptance_fact",
      "governed-execution.nwp-rw0-c2-bootstrap-acceptance-fact.v1",
      "governed-execution.nwp-rw0-c2-bootstrap-acceptance-fact.v1.identity",
      "immutable_durable_fact",
      [
        "schema_id",
        "acceptance_fact_ref",
        "lineage_ref",
        "scope_ref",
        "admission_fact_ref",
        "admission_fact_digest",
        "mutation_ref",
        "command_digest",
        "decision_ref",
        "decision_digest",
        "version_ref",
        "version_digest",
        "historical_head_ref",
        "historical_head_revision",
        "historical_head_digest",
        "selected_attempt_ref",
        "selected_candidate_ref",
        "basis_ref",
        "basis_digest",
        "family_route",
        "accepted_at",
        "acceptance_fact_digest"
      ]
    ],
    [
      "family_relation",
      "governed-execution.nwp-rw0-c2-guarded-family-relation.v1",
      "governed-execution.nwp-rw0-c2-guarded-family-relation.v1.identity",
      "immutable_supplemental_relation",
      [
        "schema_id",
        "relation_ref",
        "branch",
        "lineage_ref",
        "scope_ref",
        "command_digest",
        "admission_act_ref",
        "admission_act_digest",
        "admission_fact_ref",
        "admission_fact_digest",
        "continuity_basis_ref",
        "continuity_basis_digest",
        "sole_active_basis_ref",
        "sole_active_basis_digest",
        "decision_ref",
        "decision_digest",
        "version_ref",
        "version_digest",
        "historical_head_ref",
        "historical_head_revision",
        "historical_head_digest",
        "historical_head_postimage",
        "acceptance_fact_ref",
        "acceptance_fact_digest",
        "generic_result_projection_digest",
        "family_route",
        "relation_digest"
      ]
    ],
    [
      "guarded_result",
      "governed-execution.nwp-rw0-c2-guarded-progression-result.v1",
      "governed-execution.nwp-rw0-c2-guarded-progression-result.v1.identity",
      "derived_result_composite",
      [
        "schema_id",
        "guarded_result_ref",
        "branch",
        "generic_v1_result_schema_id",
        "generic_v1_result_digest",
        "family_relation_ref",
        "family_relation_digest",
        "receipt_graph_profile_id",
        "guarded_result_digest"
      ]
    ],
    [
      "receipt_graph_profile",
      "governed-execution.nwp-rw0-c2-receipt-graph-profile.v1",
      null,
      "static_contract_metadata",
      [
        "schema_id",
        "version",
        "authoritative_branches",
        "common_roles",
        "acceptance_only_role",
        "role_bindings",
        "ordinal_per_role",
        "role_entry_fields",
        "exact_member_verification",
        "extra_or_duplicate_roles",
        "supersession_rule"
      ]
    ],
    [
      "recovery_selector",
      "governed-execution.nwp-rw0-c2-complete-family-selector.v1",
      "governed-execution.nwp-rw0-c2-complete-family-selector.v1.identity",
      "transient_query_value",
      [
        "schema_id",
        "lineage_ref",
        "scope_ref",
        "admission_fact_ref",
        "admission_fact_digest",
        "mutation_ref",
        "command_digest",
        "decision_ref",
        "version_ref",
        "acceptance_fact_ref",
        "relation_ref",
        "guarded_result_ref",
        "family_route",
        "required_collision_routes",
        "selector_digest"
      ]
    ],
    [
      "recovery_result",
      "governed-execution.nwp-rw0-c2-complete-family-recovery-result.v1",
      "governed-execution.nwp-rw0-c2-complete-family-recovery-result.v1.identity",
      "transient_read_projection",
      [
        "schema_id",
        "classification",
        "lineage_ref",
        "scope_ref",
        "current_continuity_posture_ref",
        "current_continuity_posture_digest",
        "current_sole_active_posture_ref",
        "current_sole_active_posture_digest"
      ]
    ]
  ],
  "authority": {
    "admission_act": [
      "external_standing_policy",
      "external_standing_policy",
      "external_current_verifier",
      "external_safe_evidence",
      "act_expectation",
      "verified_evidence_role",
      "act_via_admission",
      "decision_owner",
      "decision_owner",
      [
        "caller",
        "model",
        "local_digest"
      ]
    ],
    "scope_admission_fact": [
      "guard_owner",
      "future_separate_admission_provisioner",
      "guarded_decision_verifier",
      "immutable_durable",
      "ref_and_digest",
      "required_role",
      "ref_and_digest",
      "decision_owner",
      "decision_owner",
      [
        "decision_writer",
        "local_absence",
        "database"
      ]
    ],
    "command_relation": [
      "guard_and_decision_owners",
      "none",
      "guarded_decision_verifier",
      "transient",
      "all_expectations",
      "via_command_digest",
      "exact_expectations",
      "decision_owner",
      "decision_owner",
      [
        "caller_admission",
        "model_branch"
      ]
    ],
    "continuity_basis": [
      "guard_owner_external_currentness",
      "none",
      "external_current_verifier",
      "external_current_safe_evidence",
      "basis_and_source",
      "historical_evidence_role",
      "basis_and_source",
      "decision_owner",
      "decision_owner",
      [
        "stored_snapshot",
        "machine",
        "database",
        "process"
      ]
    ],
    "sole_active_basis": [
      "guard_owner_external_currentness",
      "none",
      "external_current_verifier",
      "external_current_safe_evidence",
      "basis_and_source",
      "historical_evidence_role",
      "basis_and_source",
      "decision_owner",
      "decision_owner",
      [
        "local_lock",
        "writer_row",
        "machine"
      ]
    ],
    "acceptance_fact": [
      "guard_owner",
      "future_guarded_decision_writer",
      "whole_family_verifier",
      "immutable_durable",
      "preassigned_ref_only",
      "acceptance_only_role",
      "preassigned_ref",
      "decision_owner",
      "decision_owner",
      [
        "terminal",
        "grant",
        "replay"
      ]
    ],
    "family_relation": [
      "decision_owner",
      "future_guarded_decision_writer",
      "whole_family_verifier",
      "immutable_supplemental",
      "preassigned_ref_only",
      "required_role",
      "preassigned_ref",
      "decision_owner",
      "decision_owner",
      [
        "receipt_digest_only",
        "mutable_head_currentness"
      ]
    ],
    "guarded_result": [
      "decision_owner",
      "none",
      "whole_family_verifier",
      "derived_composite",
      "preassigned_ref_only",
      "required_role",
      "preassigned_ref",
      "decision_owner",
      "decision_owner",
      [
        "generic_v1_reinterpretation"
      ]
    ],
    "receipt_graph_profile": [
      "decision_owner",
      "none",
      "whole_family_verifier",
      "static_contract_metadata",
      "excluded",
      "transitive_via_guarded_result",
      "excluded",
      "decision_owner",
      "decision_owner",
      [
        "graph_digest_only",
        "second_receipt",
        "durable_profile_row"
      ]
    ],
    "recovery_selector": [
      "decision_owner",
      "none",
      "whole_family_verifier",
      "transient",
      "excluded",
      "excluded",
      "self",
      "decision_owner",
      "decision_owner",
      [
        "local_absence",
        "timestamp",
        "postcommit_digest"
      ]
    ],
    "recovery_result": [
      "decision_owner",
      "none",
      "whole_family_verifier",
      "transient",
      "excluded",
      "excluded",
      "excluded",
      "decision_owner",
      "decision_owner",
      [
        "automatic_retry",
        "fragment_repair",
        "stale_posture"
      ]
    ]
  },
  "preassignment_basis": {
    "name": "guarded_family_preassignment_basis_v1",
    "logical_schema": false,
    "durable_authority": false,
    "public_dto": false,
    "ordered_primitive_fields": [
      {
        "name": "command_profile",
        "type": "nonempty_exact_str",
        "origin_class": "contract_literal",
        "source_node": "contract_literal"
      },
      {
        "name": "lineage_ref",
        "type": "nonempty_exact_str",
        "origin_class": "current_owner_durable_current_value",
        "source_node": "verified_scope_admission_fact"
      },
      {
        "name": "scope_ref",
        "type": "nonempty_exact_str",
        "origin_class": "current_owner_durable_current_value",
        "source_node": "verified_scope_admission_fact"
      },
      {
        "name": "admission_fact_ref",
        "type": "nonempty_exact_str",
        "origin_class": "current_owner_durable_current_value",
        "source_node": "verified_scope_admission_fact"
      },
      {
        "name": "admission_fact_digest",
        "type": "lowercase_sha256_hex_64",
        "origin_class": "current_owner_durable_current_value",
        "source_node": "verified_scope_admission_fact"
      },
      {
        "name": "admission_act_ref",
        "type": "nonempty_exact_str",
        "origin_class": "externally_verified",
        "source_node": "verified_admission_act"
      },
      {
        "name": "admission_act_digest",
        "type": "lowercase_sha256_hex_64",
        "origin_class": "externally_verified",
        "source_node": "verified_admission_act"
      },
      {
        "name": "guard_profile",
        "type": "nonempty_exact_str",
        "origin_class": "current_owner_durable_current_value",
        "source_node": "verified_scope_admission_fact"
      },
      {
        "name": "applicability",
        "type": "nonempty_exact_str",
        "origin_class": "current_owner_durable_current_value",
        "source_node": "verified_scope_admission_fact"
      },
      {
        "name": "continuity_basis_ref",
        "type": "nonempty_exact_str",
        "origin_class": "externally_verified",
        "source_node": "verified_continuity_basis"
      },
      {
        "name": "continuity_basis_digest",
        "type": "lowercase_sha256_hex_64",
        "origin_class": "externally_verified",
        "source_node": "verified_continuity_basis"
      },
      {
        "name": "continuity_source_ref",
        "type": "nonempty_exact_str",
        "origin_class": "externally_verified",
        "source_node": "verified_continuity_basis"
      },
      {
        "name": "continuity_source_digest",
        "type": "lowercase_sha256_hex_64",
        "origin_class": "externally_verified",
        "source_node": "verified_continuity_basis"
      },
      {
        "name": "sole_active_basis_ref",
        "type": "nonempty_exact_str",
        "origin_class": "externally_verified",
        "source_node": "verified_sole_active_basis"
      },
      {
        "name": "sole_active_basis_digest",
        "type": "lowercase_sha256_hex_64",
        "origin_class": "externally_verified",
        "source_node": "verified_sole_active_basis"
      },
      {
        "name": "sole_active_source_ref",
        "type": "nonempty_exact_str",
        "origin_class": "externally_verified",
        "source_node": "verified_sole_active_basis"
      },
      {
        "name": "sole_active_source_digest",
        "type": "lowercase_sha256_hex_64",
        "origin_class": "externally_verified",
        "source_node": "verified_sole_active_basis"
      },
      {
        "name": "mutation_ref",
        "type": "nonempty_exact_str",
        "origin_class": "caller_expectation_independently_verified",
        "source_node": "verified_mutation_identity"
      },
      {
        "name": "program_ref",
        "type": "nonempty_exact_str",
        "origin_class": "current_owner_durable_current_value",
        "source_node": "current_program_identity"
      },
      {
        "name": "decision_basis_ref",
        "type": "nonempty_exact_str",
        "origin_class": "caller_expectation_independently_verified",
        "source_node": "current_decision_basis"
      },
      {
        "name": "decision_basis_digest",
        "type": "lowercase_sha256_hex_64",
        "origin_class": "caller_expectation_independently_verified",
        "source_node": "current_decision_basis"
      },
      {
        "name": "expected_head_ref",
        "type": "nonempty_exact_str",
        "origin_class": "caller_expectation_independently_verified",
        "source_node": "current_head"
      },
      {
        "name": "expected_head_revision",
        "type": "nonnegative_exact_int_not_bool",
        "origin_class": "caller_expectation_independently_verified",
        "source_node": "current_head"
      },
      {
        "name": "expected_head_digest",
        "type": "lowercase_sha256_hex_64",
        "origin_class": "caller_expectation_independently_verified",
        "source_node": "current_head"
      }
    ],
    "serialization": "ordered_name_value_pairs_utf8_json_ensure_ascii_false_allow_nan_false_compact",
    "excluded_sources": [
      "command_digest",
      "preassigned_sibling",
      "authoritative_branch",
      "result",
      "receipt",
      "transaction_timestamp",
      "terminal_outcome",
      "postcommit_head",
      "raw_external_credential",
      "raw_external_attestation"
    ],
    "profile_source": "command_relation.schema_id"
  },
  "preassignment_siblings": [
    {
      "name": "preassigned_decision_ref",
      "command_field": "preassigned_decision_ref",
      "domain": "governed-execution.nwp-rw0-c2-preassigned-decision-ref.v1",
      "input": "guarded_family_preassignment_basis_v1",
      "output_grammar": "lowercase_sha256_hex_64",
      "fixed_vector": "400960b261c148544c0d0c29d2c65bf7b6b85b679d18c52d2ab4ec793198f208"
    },
    {
      "name": "preassigned_resulting_program_version_ref",
      "command_field": "preassigned_version_ref",
      "domain": "governed-execution.nwp-rw0-c2-preassigned-resulting-version-ref.v1",
      "input": "guarded_family_preassignment_basis_v1",
      "output_grammar": "lowercase_sha256_hex_64",
      "fixed_vector": "1d930498247537c7934366c77a35a3a7c0614402ceefa87b49d713143220f237"
    },
    {
      "name": "preassigned_guarded_family_relation_ref",
      "command_field": "preassigned_relation_ref",
      "domain": "governed-execution.nwp-rw0-c2-preassigned-guarded-relation-ref.v1",
      "input": "guarded_family_preassignment_basis_v1",
      "output_grammar": "lowercase_sha256_hex_64",
      "fixed_vector": "0fbf19ecc76ca0a2c6ffba5c8c4b07157cdb1645a722b0df130ed5c30b832f77"
    },
    {
      "name": "preassigned_guarded_progression_result_ref",
      "command_field": "preassigned_guarded_result_ref",
      "domain": "governed-execution.nwp-rw0-c2-preassigned-guarded-result-ref.v1",
      "input": "guarded_family_preassignment_basis_v1",
      "output_grammar": "lowercase_sha256_hex_64",
      "fixed_vector": "28719afd5182e5a76ea2d17502d70b62cc2e1817f4b82e460d8a1f2225700254"
    },
    {
      "name": "deterministic_family_route",
      "command_field": "family_route",
      "domain": "governed-execution.nwp-rw0-c2-deterministic-family-route.v1",
      "input": "guarded_family_preassignment_basis_v1",
      "output_grammar": "lowercase_sha256_hex_64",
      "fixed_vector": "4f13fe4404b53c9d521eac90a64d87352d1077e307be5a33a8dd9c27c33079b9"
    },
    {
      "name": "preassigned_acceptance_fact_ref",
      "command_field": "preassigned_acceptance_fact_ref",
      "domain": "governed-execution.nwp-rw0-c2-bootstrap-acceptance-fact.v1.prospective-ref",
      "input": "guarded_family_preassignment_basis_v1",
      "output_grammar": "lowercase_sha256_hex_64",
      "fixed_vector": "e45e55113d63769b1a4a157aa5a0d8a1621516ba5b81155535f1116af66e8f17"
    }
  ],
  "dependency_registry": {
    "origin_classes": [
      "externally_verified",
      "current_owner_durable_current_value",
      "caller_expectation_independently_verified",
      "contract_literal",
      "primitive_derivation_transcript",
      "sibling_domain_separated_derivation",
      "post_preassignment_command_digest",
      "authoritative_branch_output",
      "post_branch_canonical_value_digest",
      "receipt_graph",
      "replay_recovery_projection",
      "future_transaction_owner_prerequisite",
      "validated_prebranch_admission_posture",
      "postread_verified_input"
    ],
    "nodes": [
      {
        "node": "receipt_profile_id_literal",
        "stage": 0,
        "origin_class": "contract_literal",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "family_relation_schema_literal",
        "stage": 0,
        "origin_class": "contract_literal",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "verified_admission_act",
        "stage": 0,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "verified_scope_admission_fact",
        "stage": 1,
        "origin_class": "current_owner_durable_current_value",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_admission_act"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "verified_continuity_basis",
        "stage": 0,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "verified_sole_active_basis",
        "stage": 0,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "verified_mutation_identity",
        "stage": 0,
        "origin_class": "caller_expectation_independently_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "current_program_identity",
        "stage": 0,
        "origin_class": "current_owner_durable_current_value",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "current_decision_basis",
        "stage": 0,
        "origin_class": "current_owner_durable_current_value",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "current_head",
        "stage": 0,
        "origin_class": "current_owner_durable_current_value",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "fresh_current_continuity_posture",
        "stage": 0,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "exact_replay_readback_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "fresh_current_sole_active_posture",
        "stage": 0,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "exact_replay_readback_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "local_writer_session_fence",
        "stage": 0,
        "origin_class": "future_transaction_owner_prerequisite",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "fresh_external_posture",
        "stage": 1,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "fresh_current_continuity_posture",
          "fresh_current_sole_active_posture"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "exact_replay_readback_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:command_profile",
        "stage": 2,
        "origin_class": "contract_literal",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:lineage_ref",
        "stage": 2,
        "origin_class": "current_owner_durable_current_value",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_scope_admission_fact"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:scope_ref",
        "stage": 2,
        "origin_class": "current_owner_durable_current_value",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_scope_admission_fact"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:admission_fact_ref",
        "stage": 2,
        "origin_class": "current_owner_durable_current_value",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_scope_admission_fact"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:admission_fact_digest",
        "stage": 2,
        "origin_class": "current_owner_durable_current_value",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_scope_admission_fact"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:admission_act_ref",
        "stage": 2,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_admission_act"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:admission_act_digest",
        "stage": 2,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_admission_act"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:guard_profile",
        "stage": 2,
        "origin_class": "current_owner_durable_current_value",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_scope_admission_fact"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:applicability",
        "stage": 2,
        "origin_class": "current_owner_durable_current_value",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_scope_admission_fact"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:continuity_basis_ref",
        "stage": 2,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_continuity_basis"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:continuity_basis_digest",
        "stage": 2,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_continuity_basis"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:continuity_source_ref",
        "stage": 2,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_continuity_basis"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:continuity_source_digest",
        "stage": 2,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_continuity_basis"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:sole_active_basis_ref",
        "stage": 2,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_sole_active_basis"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:sole_active_basis_digest",
        "stage": 2,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_sole_active_basis"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:sole_active_source_ref",
        "stage": 2,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_sole_active_basis"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:sole_active_source_digest",
        "stage": 2,
        "origin_class": "externally_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_sole_active_basis"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:mutation_ref",
        "stage": 2,
        "origin_class": "caller_expectation_independently_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_mutation_identity"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:program_ref",
        "stage": 2,
        "origin_class": "current_owner_durable_current_value",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "current_program_identity"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:decision_basis_ref",
        "stage": 2,
        "origin_class": "caller_expectation_independently_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "current_decision_basis"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:decision_basis_digest",
        "stage": 2,
        "origin_class": "caller_expectation_independently_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "current_decision_basis"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:expected_head_ref",
        "stage": 2,
        "origin_class": "caller_expectation_independently_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "current_head"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:expected_head_revision",
        "stage": 2,
        "origin_class": "caller_expectation_independently_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "current_head"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "primitive:expected_head_digest",
        "stage": 2,
        "origin_class": "caller_expectation_independently_verified",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "current_head"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "closed_command_relation_value",
        "stage": 3,
        "origin_class": "primitive_derivation_transcript",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "primitive:command_profile",
          "primitive:lineage_ref",
          "primitive:scope_ref",
          "primitive:admission_fact_ref",
          "primitive:admission_fact_digest",
          "primitive:admission_act_ref",
          "primitive:admission_act_digest",
          "primitive:guard_profile",
          "primitive:applicability",
          "primitive:continuity_basis_ref",
          "primitive:continuity_basis_digest",
          "primitive:continuity_source_ref",
          "primitive:continuity_source_digest",
          "primitive:sole_active_basis_ref",
          "primitive:sole_active_basis_digest",
          "primitive:sole_active_source_ref",
          "primitive:sole_active_source_digest",
          "primitive:mutation_ref",
          "primitive:program_ref",
          "primitive:decision_basis_ref",
          "primitive:decision_basis_digest",
          "primitive:expected_head_ref",
          "primitive:expected_head_revision",
          "primitive:expected_head_digest",
          "verified_admission_act",
          "verified_scope_admission_fact"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "guarded_family_preassignment_basis_v1",
        "stage": 4,
        "origin_class": "primitive_derivation_transcript",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "closed_command_relation_value",
          "primitive:command_profile",
          "primitive:lineage_ref",
          "primitive:scope_ref",
          "primitive:admission_fact_ref",
          "primitive:admission_fact_digest",
          "primitive:admission_act_ref",
          "primitive:admission_act_digest",
          "primitive:guard_profile",
          "primitive:applicability",
          "primitive:continuity_basis_ref",
          "primitive:continuity_basis_digest",
          "primitive:continuity_source_ref",
          "primitive:continuity_source_digest",
          "primitive:sole_active_basis_ref",
          "primitive:sole_active_basis_digest",
          "primitive:sole_active_source_ref",
          "primitive:sole_active_source_digest",
          "primitive:mutation_ref",
          "primitive:program_ref",
          "primitive:decision_basis_ref",
          "primitive:decision_basis_digest",
          "primitive:expected_head_ref",
          "primitive:expected_head_revision",
          "primitive:expected_head_digest"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "sibling:preassigned_decision_ref",
        "stage": 5,
        "origin_class": "sibling_domain_separated_derivation",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "guarded_family_preassignment_basis_v1"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "sibling:preassigned_resulting_program_version_ref",
        "stage": 5,
        "origin_class": "sibling_domain_separated_derivation",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "guarded_family_preassignment_basis_v1"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "sibling:preassigned_guarded_family_relation_ref",
        "stage": 5,
        "origin_class": "sibling_domain_separated_derivation",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "guarded_family_preassignment_basis_v1"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "sibling:preassigned_guarded_progression_result_ref",
        "stage": 5,
        "origin_class": "sibling_domain_separated_derivation",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "guarded_family_preassignment_basis_v1"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "sibling:deterministic_family_route",
        "stage": 5,
        "origin_class": "sibling_domain_separated_derivation",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "guarded_family_preassignment_basis_v1"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "sibling:preassigned_acceptance_fact_ref",
        "stage": 5,
        "origin_class": "sibling_domain_separated_derivation",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "guarded_family_preassignment_basis_v1"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "command_digest",
        "stage": 6,
        "origin_class": "post_preassignment_command_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "closed_command_relation_value",
          "primitive:command_profile",
          "primitive:lineage_ref",
          "primitive:scope_ref",
          "primitive:admission_fact_ref",
          "primitive:admission_fact_digest",
          "primitive:admission_act_ref",
          "primitive:admission_act_digest",
          "primitive:guard_profile",
          "primitive:applicability",
          "primitive:continuity_basis_ref",
          "primitive:continuity_basis_digest",
          "primitive:continuity_source_ref",
          "primitive:continuity_source_digest",
          "primitive:sole_active_basis_ref",
          "primitive:sole_active_basis_digest",
          "primitive:sole_active_source_ref",
          "primitive:sole_active_source_digest",
          "primitive:mutation_ref",
          "primitive:program_ref",
          "primitive:decision_basis_ref",
          "primitive:decision_basis_digest",
          "primitive:expected_head_ref",
          "primitive:expected_head_revision",
          "primitive:expected_head_digest",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1",
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "guarded_result_identity_expectation",
        "stage": 6,
        "origin_class": "post_preassignment_command_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "sibling:preassigned_guarded_progression_result_ref"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [
          "command_digest",
          "authoritative_branch",
          "transaction_timestamp",
          "acceptance_fact_digest",
          "family_relation_digest",
          "guarded_result_digest",
          "generic_receipt_graph_digest",
          "generic_receipt_row_value",
          "recovery_projection",
          "terminal_outcome",
          "postcommit_head",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "validated_admission_command_and_current_posture",
        "stage": 7,
        "origin_class": "validated_prebranch_admission_posture",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_admission_act",
          "verified_scope_admission_fact",
          "closed_command_relation_value",
          "command_digest",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref",
          "fresh_current_continuity_posture",
          "fresh_current_sole_active_posture",
          "local_writer_session_fence"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "authoritative_branch",
        "stage": 8,
        "origin_class": "authoritative_branch_output",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "validated_admission_command_and_current_posture",
          "current_decision_basis",
          "current_head"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "recovery_selector_value",
        "stage": 6,
        "origin_class": "replay_recovery_projection",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "command_digest",
          "sibling:preassigned_decision_ref",
          "sibling:preassigned_resulting_program_version_ref",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:preassigned_guarded_progression_result_ref",
          "sibling:deterministic_family_route",
          "sibling:preassigned_acceptance_fact_ref",
          "primitive:lineage_ref",
          "primitive:scope_ref",
          "primitive:admission_fact_ref",
          "primitive:admission_fact_digest",
          "primitive:mutation_ref"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "transaction_timestamp",
        "stage": 9,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "authoritative_branch"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "recovery_selector_digest",
        "stage": 7,
        "origin_class": "replay_recovery_projection",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "recovery_selector_value"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "recovery_route_observation:mutation_receipt_route",
        "stage": 8,
        "origin_class": "replay_recovery_projection",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "recovery_selector_value",
          "fresh_external_posture"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "recovery_route_observation:decision_identity_route",
        "stage": 8,
        "origin_class": "replay_recovery_projection",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "recovery_selector_value",
          "fresh_external_posture"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "recovery_route_observation:resulting_version_identity_route",
        "stage": 8,
        "origin_class": "replay_recovery_projection",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "recovery_selector_value",
          "fresh_external_posture"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "recovery_route_observation:acceptance_fact_identity_route",
        "stage": 8,
        "origin_class": "replay_recovery_projection",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "recovery_selector_value",
          "fresh_external_posture"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "recovery_route_observation:guarded_family_relation_identity_route",
        "stage": 8,
        "origin_class": "replay_recovery_projection",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "recovery_selector_value",
          "fresh_external_posture"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "recovery_route_observation:guarded_progression_result_identity_route",
        "stage": 8,
        "origin_class": "replay_recovery_projection",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "recovery_selector_value",
          "fresh_external_posture"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "recovery_route_observation:deterministic_family_route",
        "stage": 8,
        "origin_class": "replay_recovery_projection",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "recovery_selector_value",
          "fresh_external_posture"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "recovery_route_observation:admitted_scope_winner_route",
        "stage": 8,
        "origin_class": "replay_recovery_projection",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "recovery_selector_value",
          "fresh_external_posture"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "complete_family_recovery_observation_set_v1",
        "stage": 9,
        "origin_class": "replay_recovery_projection",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "recovery_selector_digest",
          "fresh_external_posture",
          "recovery_route_observation:mutation_receipt_route",
          "recovery_route_observation:decision_identity_route",
          "recovery_route_observation:resulting_version_identity_route",
          "recovery_route_observation:acceptance_fact_identity_route",
          "recovery_route_observation:guarded_family_relation_identity_route",
          "recovery_route_observation:guarded_progression_result_identity_route",
          "recovery_route_observation:deterministic_family_route",
          "recovery_route_observation:admitted_scope_winner_route"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "uncertain_commit_recovery_v1"
        ]
      },
      {
        "node": "canonical_decision_value",
        "stage": 10,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "authoritative_branch",
          "command_digest",
          "sibling:preassigned_decision_ref",
          "transaction_timestamp"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "canonical_decision_digest",
        "stage": 11,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "canonical_decision_value"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "canonical_version_value",
        "stage": 12,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "canonical_decision_digest",
          "sibling:preassigned_resulting_program_version_ref",
          "transaction_timestamp"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "canonical_version_digest",
        "stage": 13,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "canonical_version_value"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "historical_head_postimage_value",
        "stage": 14,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "canonical_version_digest",
          "current_head",
          "transaction_timestamp"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "historical_head_postimage_digest",
        "stage": 15,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "historical_head_postimage_value"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "generic_result_projection_value",
        "stage": 16,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "canonical_decision_digest",
          "canonical_version_digest",
          "historical_head_postimage_digest"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "generic_result_projection_digest",
        "stage": 17,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "generic_result_projection_value"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "acceptance_fact_value",
        "stage": 18,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": [
          "candidate_acceptance"
        ],
        "common_dependencies": [
          "authoritative_branch",
          "command_digest",
          "canonical_decision_value",
          "canonical_decision_digest",
          "canonical_version_value",
          "canonical_version_digest",
          "historical_head_postimage_value",
          "historical_head_postimage_digest",
          "transaction_timestamp",
          "sibling:preassigned_acceptance_fact_ref",
          "sibling:deterministic_family_route"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "acceptance_fact_digest",
        "stage": 19,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": [
          "candidate_acceptance"
        ],
        "common_dependencies": [
          "acceptance_fact_value"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "family_relation_value",
        "stage": 20,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "authoritative_branch",
          "command_digest",
          "historical_head_postimage_value",
          "historical_head_postimage_digest",
          "canonical_decision_value",
          "canonical_decision_digest",
          "canonical_version_value",
          "canonical_version_digest",
          "generic_result_projection_value",
          "generic_result_projection_digest",
          "guarded_result_identity_expectation",
          "sibling:preassigned_guarded_family_relation_ref",
          "sibling:deterministic_family_route",
          "verified_scope_admission_fact",
          "verified_admission_act",
          "verified_continuity_basis",
          "verified_sole_active_basis",
          "family_relation_schema_literal",
          "primitive:lineage_ref",
          "primitive:scope_ref"
        ],
        "dependencies_by_branch": {
          "candidate_acceptance": [
            "acceptance_fact_value",
            "acceptance_fact_digest"
          ]
        },
        "prohibited_dependencies": [
          "acceptance_fact_value",
          "acceptance_fact_digest"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "family_relation_digest",
        "stage": 21,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "family_relation_value"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "guarded_result_value",
        "stage": 22,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "family_relation_digest",
          "generic_result_projection_digest",
          "sibling:preassigned_guarded_progression_result_ref",
          "authoritative_branch",
          "receipt_profile_id_literal"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "guarded_result_digest",
        "stage": 23,
        "origin_class": "post_branch_canonical_value_digest",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "guarded_result_value"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "generic_receipt_preimage_value",
        "stage": 24,
        "origin_class": "receipt_graph",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "command_digest",
          "canonical_decision_value",
          "canonical_decision_digest",
          "canonical_version_value",
          "canonical_version_digest",
          "generic_result_projection_value",
          "generic_result_projection_digest",
          "transaction_timestamp"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "generic_receipt_graph_entries_value",
        "stage": 24,
        "origin_class": "receipt_graph",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "verified_admission_act",
          "verified_scope_admission_fact",
          "verified_continuity_basis",
          "verified_sole_active_basis",
          "canonical_decision_value",
          "canonical_decision_digest",
          "canonical_version_value",
          "canonical_version_digest",
          "historical_head_postimage_value",
          "historical_head_postimage_digest",
          "generic_result_projection_value",
          "generic_result_projection_digest",
          "family_relation_value",
          "family_relation_digest",
          "guarded_result_value",
          "guarded_result_digest"
        ],
        "dependencies_by_branch": {
          "candidate_acceptance": [
            "acceptance_fact_value",
            "acceptance_fact_digest"
          ]
        },
        "prohibited_dependencies": [
          "acceptance_fact_value",
          "acceptance_fact_digest"
        ],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "generic_receipt_graph_identity_value",
        "stage": 25,
        "origin_class": "receipt_graph",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "generic_receipt_preimage_value",
          "generic_receipt_graph_entries_value"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "generic_receipt_graph_digest",
        "stage": 26,
        "origin_class": "receipt_graph",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "generic_receipt_graph_identity_value"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "generic_receipt_row_value",
        "stage": 27,
        "origin_class": "receipt_graph",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "generic_receipt_preimage_value",
          "generic_receipt_graph_digest"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "fresh_write_construction_v1"
        ]
      },
      {
        "node": "replay_canonical_command_digest_observation",
        "stage": 0,
        "origin_class": "postread_verified_input",
        "materializes_on": "all_branches",
        "common_dependencies": [],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "exact_replay_readback_v1"
        ]
      },
      {
        "node": "replay_receipt_first_mutation_lookup",
        "stage": 1,
        "origin_class": "postread_verified_input",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "replay_canonical_command_digest_observation"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "exact_replay_readback_v1"
        ]
      },
      {
        "node": "replay_exact_persisted_family",
        "stage": 2,
        "origin_class": "postread_verified_input",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "replay_receipt_first_mutation_lookup"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "exact_replay_readback_v1"
        ]
      },
      {
        "node": "replay_projection",
        "stage": 28,
        "origin_class": "replay_recovery_projection",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "replay_canonical_command_digest_observation",
          "replay_receipt_first_mutation_lookup",
          "replay_exact_persisted_family",
          "fresh_external_posture"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "exact_replay_readback_v1"
        ]
      },
      {
        "node": "recovery_projection",
        "stage": 28,
        "origin_class": "replay_recovery_projection",
        "materializes_on": "all_branches",
        "common_dependencies": [
          "recovery_selector_value",
          "recovery_selector_digest",
          "complete_family_recovery_observation_set_v1",
          "fresh_external_posture"
        ],
        "dependencies_by_branch": {},
        "prohibited_dependencies": [],
        "lifecycle_memberships": [
          "uncertain_commit_recovery_v1"
        ]
      }
    ],
    "conditional_nodes": [
      "acceptance_fact_value",
      "acceptance_fact_digest"
    ],
    "dependency_rule": "exact_branch_expansion_no_implicit_aggregate_inputs",
    "stage_rule": "fresh_write_dependencies_strictly_increase_only",
    "topological_rule": "complete_unique_topological_sort_per_lifecycle_partition",
    "node_count": 86,
    "common_edge_count": 266,
    "expanded_counts": {
      "candidate_acceptance": {
        "nodes": 70,
        "edges": 221
      },
      "candidate_repair": {
        "nodes": 68,
        "edges": 205
      },
      "attempt_selecting_replan": {
        "nodes": 68,
        "edges": 205
      },
      "program_terminal_reject": {
        "nodes": 68,
        "edges": 205
      },
      "post_execution_program_block": {
        "nodes": 68,
        "edges": 205
      }
    },
    "recovery_observation_nodes": [
      "recovery_route_observation:mutation_receipt_route",
      "recovery_route_observation:decision_identity_route",
      "recovery_route_observation:resulting_version_identity_route",
      "recovery_route_observation:acceptance_fact_identity_route",
      "recovery_route_observation:guarded_family_relation_identity_route",
      "recovery_route_observation:guarded_progression_result_identity_route",
      "recovery_route_observation:deterministic_family_route",
      "recovery_route_observation:admitted_scope_winner_route"
    ],
    "relation_field_dependencies": {
      "schema_id": "family_relation_schema_literal",
      "relation_ref": "sibling:preassigned_guarded_family_relation_ref",
      "branch": "authoritative_branch",
      "lineage_ref": "primitive:lineage_ref",
      "scope_ref": "primitive:scope_ref",
      "command_digest": "command_digest",
      "admission_act_ref": "verified_admission_act",
      "admission_act_digest": "verified_admission_act",
      "admission_fact_ref": "verified_scope_admission_fact",
      "admission_fact_digest": "verified_scope_admission_fact",
      "continuity_basis_ref": "verified_continuity_basis",
      "continuity_basis_digest": "verified_continuity_basis",
      "sole_active_basis_ref": "verified_sole_active_basis",
      "sole_active_basis_digest": "verified_sole_active_basis",
      "decision_ref": "canonical_decision_value",
      "decision_digest": "canonical_decision_digest",
      "version_ref": "canonical_version_value",
      "version_digest": "canonical_version_digest",
      "historical_head_ref": "historical_head_postimage_value",
      "historical_head_revision": "historical_head_postimage_value",
      "historical_head_digest": "historical_head_postimage_digest",
      "historical_head_postimage": "historical_head_postimage_value",
      "acceptance_fact_ref": "acceptance_fact_value",
      "acceptance_fact_digest": "acceptance_fact_digest",
      "generic_result_projection_digest": "generic_result_projection_digest",
      "family_route": "sibling:deterministic_family_route"
    },
    "lifecycle_partitions": {
      "fresh_write_construction_v1": {
        "phase": "fresh_write_construction",
        "branch_dags": {
          "candidate_acceptance": {
            "nodes": [
              "receipt_profile_id_literal",
              "family_relation_schema_literal",
              "verified_admission_act",
              "verified_scope_admission_fact",
              "verified_continuity_basis",
              "verified_sole_active_basis",
              "verified_mutation_identity",
              "current_program_identity",
              "current_decision_basis",
              "current_head",
              "fresh_current_continuity_posture",
              "fresh_current_sole_active_posture",
              "local_writer_session_fence",
              "fresh_external_posture",
              "primitive:command_profile",
              "primitive:lineage_ref",
              "primitive:scope_ref",
              "primitive:admission_fact_ref",
              "primitive:admission_fact_digest",
              "primitive:admission_act_ref",
              "primitive:admission_act_digest",
              "primitive:guard_profile",
              "primitive:applicability",
              "primitive:continuity_basis_ref",
              "primitive:continuity_basis_digest",
              "primitive:continuity_source_ref",
              "primitive:continuity_source_digest",
              "primitive:sole_active_basis_ref",
              "primitive:sole_active_basis_digest",
              "primitive:sole_active_source_ref",
              "primitive:sole_active_source_digest",
              "primitive:mutation_ref",
              "primitive:program_ref",
              "primitive:decision_basis_ref",
              "primitive:decision_basis_digest",
              "primitive:expected_head_ref",
              "primitive:expected_head_revision",
              "primitive:expected_head_digest",
              "closed_command_relation_value",
              "guarded_family_preassignment_basis_v1",
              "sibling:preassigned_decision_ref",
              "sibling:preassigned_resulting_program_version_ref",
              "sibling:preassigned_guarded_family_relation_ref",
              "sibling:preassigned_guarded_progression_result_ref",
              "sibling:deterministic_family_route",
              "sibling:preassigned_acceptance_fact_ref",
              "command_digest",
              "guarded_result_identity_expectation",
              "validated_admission_command_and_current_posture",
              "authoritative_branch",
              "transaction_timestamp",
              "canonical_decision_value",
              "canonical_decision_digest",
              "canonical_version_value",
              "canonical_version_digest",
              "historical_head_postimage_value",
              "historical_head_postimage_digest",
              "generic_result_projection_value",
              "generic_result_projection_digest",
              "acceptance_fact_value",
              "acceptance_fact_digest",
              "family_relation_value",
              "family_relation_digest",
              "guarded_result_value",
              "guarded_result_digest",
              "generic_receipt_preimage_value",
              "generic_receipt_graph_entries_value",
              "generic_receipt_graph_identity_value",
              "generic_receipt_graph_digest",
              "generic_receipt_row_value"
            ],
            "node_count": 70,
            "edge_count": 221
          },
          "candidate_repair": {
            "nodes": [
              "receipt_profile_id_literal",
              "family_relation_schema_literal",
              "verified_admission_act",
              "verified_scope_admission_fact",
              "verified_continuity_basis",
              "verified_sole_active_basis",
              "verified_mutation_identity",
              "current_program_identity",
              "current_decision_basis",
              "current_head",
              "fresh_current_continuity_posture",
              "fresh_current_sole_active_posture",
              "local_writer_session_fence",
              "fresh_external_posture",
              "primitive:command_profile",
              "primitive:lineage_ref",
              "primitive:scope_ref",
              "primitive:admission_fact_ref",
              "primitive:admission_fact_digest",
              "primitive:admission_act_ref",
              "primitive:admission_act_digest",
              "primitive:guard_profile",
              "primitive:applicability",
              "primitive:continuity_basis_ref",
              "primitive:continuity_basis_digest",
              "primitive:continuity_source_ref",
              "primitive:continuity_source_digest",
              "primitive:sole_active_basis_ref",
              "primitive:sole_active_basis_digest",
              "primitive:sole_active_source_ref",
              "primitive:sole_active_source_digest",
              "primitive:mutation_ref",
              "primitive:program_ref",
              "primitive:decision_basis_ref",
              "primitive:decision_basis_digest",
              "primitive:expected_head_ref",
              "primitive:expected_head_revision",
              "primitive:expected_head_digest",
              "closed_command_relation_value",
              "guarded_family_preassignment_basis_v1",
              "sibling:preassigned_decision_ref",
              "sibling:preassigned_resulting_program_version_ref",
              "sibling:preassigned_guarded_family_relation_ref",
              "sibling:preassigned_guarded_progression_result_ref",
              "sibling:deterministic_family_route",
              "sibling:preassigned_acceptance_fact_ref",
              "command_digest",
              "guarded_result_identity_expectation",
              "validated_admission_command_and_current_posture",
              "authoritative_branch",
              "transaction_timestamp",
              "canonical_decision_value",
              "canonical_decision_digest",
              "canonical_version_value",
              "canonical_version_digest",
              "historical_head_postimage_value",
              "historical_head_postimage_digest",
              "generic_result_projection_value",
              "generic_result_projection_digest",
              "family_relation_value",
              "family_relation_digest",
              "guarded_result_value",
              "guarded_result_digest",
              "generic_receipt_preimage_value",
              "generic_receipt_graph_entries_value",
              "generic_receipt_graph_identity_value",
              "generic_receipt_graph_digest",
              "generic_receipt_row_value"
            ],
            "node_count": 68,
            "edge_count": 205
          },
          "attempt_selecting_replan": {
            "nodes": [
              "receipt_profile_id_literal",
              "family_relation_schema_literal",
              "verified_admission_act",
              "verified_scope_admission_fact",
              "verified_continuity_basis",
              "verified_sole_active_basis",
              "verified_mutation_identity",
              "current_program_identity",
              "current_decision_basis",
              "current_head",
              "fresh_current_continuity_posture",
              "fresh_current_sole_active_posture",
              "local_writer_session_fence",
              "fresh_external_posture",
              "primitive:command_profile",
              "primitive:lineage_ref",
              "primitive:scope_ref",
              "primitive:admission_fact_ref",
              "primitive:admission_fact_digest",
              "primitive:admission_act_ref",
              "primitive:admission_act_digest",
              "primitive:guard_profile",
              "primitive:applicability",
              "primitive:continuity_basis_ref",
              "primitive:continuity_basis_digest",
              "primitive:continuity_source_ref",
              "primitive:continuity_source_digest",
              "primitive:sole_active_basis_ref",
              "primitive:sole_active_basis_digest",
              "primitive:sole_active_source_ref",
              "primitive:sole_active_source_digest",
              "primitive:mutation_ref",
              "primitive:program_ref",
              "primitive:decision_basis_ref",
              "primitive:decision_basis_digest",
              "primitive:expected_head_ref",
              "primitive:expected_head_revision",
              "primitive:expected_head_digest",
              "closed_command_relation_value",
              "guarded_family_preassignment_basis_v1",
              "sibling:preassigned_decision_ref",
              "sibling:preassigned_resulting_program_version_ref",
              "sibling:preassigned_guarded_family_relation_ref",
              "sibling:preassigned_guarded_progression_result_ref",
              "sibling:deterministic_family_route",
              "sibling:preassigned_acceptance_fact_ref",
              "command_digest",
              "guarded_result_identity_expectation",
              "validated_admission_command_and_current_posture",
              "authoritative_branch",
              "transaction_timestamp",
              "canonical_decision_value",
              "canonical_decision_digest",
              "canonical_version_value",
              "canonical_version_digest",
              "historical_head_postimage_value",
              "historical_head_postimage_digest",
              "generic_result_projection_value",
              "generic_result_projection_digest",
              "family_relation_value",
              "family_relation_digest",
              "guarded_result_value",
              "guarded_result_digest",
              "generic_receipt_preimage_value",
              "generic_receipt_graph_entries_value",
              "generic_receipt_graph_identity_value",
              "generic_receipt_graph_digest",
              "generic_receipt_row_value"
            ],
            "node_count": 68,
            "edge_count": 205
          },
          "program_terminal_reject": {
            "nodes": [
              "receipt_profile_id_literal",
              "family_relation_schema_literal",
              "verified_admission_act",
              "verified_scope_admission_fact",
              "verified_continuity_basis",
              "verified_sole_active_basis",
              "verified_mutation_identity",
              "current_program_identity",
              "current_decision_basis",
              "current_head",
              "fresh_current_continuity_posture",
              "fresh_current_sole_active_posture",
              "local_writer_session_fence",
              "fresh_external_posture",
              "primitive:command_profile",
              "primitive:lineage_ref",
              "primitive:scope_ref",
              "primitive:admission_fact_ref",
              "primitive:admission_fact_digest",
              "primitive:admission_act_ref",
              "primitive:admission_act_digest",
              "primitive:guard_profile",
              "primitive:applicability",
              "primitive:continuity_basis_ref",
              "primitive:continuity_basis_digest",
              "primitive:continuity_source_ref",
              "primitive:continuity_source_digest",
              "primitive:sole_active_basis_ref",
              "primitive:sole_active_basis_digest",
              "primitive:sole_active_source_ref",
              "primitive:sole_active_source_digest",
              "primitive:mutation_ref",
              "primitive:program_ref",
              "primitive:decision_basis_ref",
              "primitive:decision_basis_digest",
              "primitive:expected_head_ref",
              "primitive:expected_head_revision",
              "primitive:expected_head_digest",
              "closed_command_relation_value",
              "guarded_family_preassignment_basis_v1",
              "sibling:preassigned_decision_ref",
              "sibling:preassigned_resulting_program_version_ref",
              "sibling:preassigned_guarded_family_relation_ref",
              "sibling:preassigned_guarded_progression_result_ref",
              "sibling:deterministic_family_route",
              "sibling:preassigned_acceptance_fact_ref",
              "command_digest",
              "guarded_result_identity_expectation",
              "validated_admission_command_and_current_posture",
              "authoritative_branch",
              "transaction_timestamp",
              "canonical_decision_value",
              "canonical_decision_digest",
              "canonical_version_value",
              "canonical_version_digest",
              "historical_head_postimage_value",
              "historical_head_postimage_digest",
              "generic_result_projection_value",
              "generic_result_projection_digest",
              "family_relation_value",
              "family_relation_digest",
              "guarded_result_value",
              "guarded_result_digest",
              "generic_receipt_preimage_value",
              "generic_receipt_graph_entries_value",
              "generic_receipt_graph_identity_value",
              "generic_receipt_graph_digest",
              "generic_receipt_row_value"
            ],
            "node_count": 68,
            "edge_count": 205
          },
          "post_execution_program_block": {
            "nodes": [
              "receipt_profile_id_literal",
              "family_relation_schema_literal",
              "verified_admission_act",
              "verified_scope_admission_fact",
              "verified_continuity_basis",
              "verified_sole_active_basis",
              "verified_mutation_identity",
              "current_program_identity",
              "current_decision_basis",
              "current_head",
              "fresh_current_continuity_posture",
              "fresh_current_sole_active_posture",
              "local_writer_session_fence",
              "fresh_external_posture",
              "primitive:command_profile",
              "primitive:lineage_ref",
              "primitive:scope_ref",
              "primitive:admission_fact_ref",
              "primitive:admission_fact_digest",
              "primitive:admission_act_ref",
              "primitive:admission_act_digest",
              "primitive:guard_profile",
              "primitive:applicability",
              "primitive:continuity_basis_ref",
              "primitive:continuity_basis_digest",
              "primitive:continuity_source_ref",
              "primitive:continuity_source_digest",
              "primitive:sole_active_basis_ref",
              "primitive:sole_active_basis_digest",
              "primitive:sole_active_source_ref",
              "primitive:sole_active_source_digest",
              "primitive:mutation_ref",
              "primitive:program_ref",
              "primitive:decision_basis_ref",
              "primitive:decision_basis_digest",
              "primitive:expected_head_ref",
              "primitive:expected_head_revision",
              "primitive:expected_head_digest",
              "closed_command_relation_value",
              "guarded_family_preassignment_basis_v1",
              "sibling:preassigned_decision_ref",
              "sibling:preassigned_resulting_program_version_ref",
              "sibling:preassigned_guarded_family_relation_ref",
              "sibling:preassigned_guarded_progression_result_ref",
              "sibling:deterministic_family_route",
              "sibling:preassigned_acceptance_fact_ref",
              "command_digest",
              "guarded_result_identity_expectation",
              "validated_admission_command_and_current_posture",
              "authoritative_branch",
              "transaction_timestamp",
              "canonical_decision_value",
              "canonical_decision_digest",
              "canonical_version_value",
              "canonical_version_digest",
              "historical_head_postimage_value",
              "historical_head_postimage_digest",
              "generic_result_projection_value",
              "generic_result_projection_digest",
              "family_relation_value",
              "family_relation_digest",
              "guarded_result_value",
              "guarded_result_digest",
              "generic_receipt_preimage_value",
              "generic_receipt_graph_entries_value",
              "generic_receipt_graph_identity_value",
              "generic_receipt_graph_digest",
              "generic_receipt_row_value"
            ],
            "node_count": 68,
            "edge_count": 205
          }
        }
      },
      "exact_replay_readback_v1": {
        "phase": "postread_exact_replay",
        "dag": {
          "nodes": [
            "fresh_current_continuity_posture",
            "fresh_current_sole_active_posture",
            "fresh_external_posture",
            "replay_canonical_command_digest_observation",
            "replay_receipt_first_mutation_lookup",
            "replay_exact_persisted_family",
            "replay_projection"
          ],
          "node_count": 7,
          "edge_count": 8
        }
      },
      "uncertain_commit_recovery_v1": {
        "phase": "postread_uncertain_commit_recovery",
        "dag": {
          "nodes": [
            "verified_admission_act",
            "verified_scope_admission_fact",
            "verified_continuity_basis",
            "verified_sole_active_basis",
            "verified_mutation_identity",
            "current_program_identity",
            "current_decision_basis",
            "current_head",
            "fresh_current_continuity_posture",
            "fresh_current_sole_active_posture",
            "fresh_external_posture",
            "primitive:command_profile",
            "primitive:lineage_ref",
            "primitive:scope_ref",
            "primitive:admission_fact_ref",
            "primitive:admission_fact_digest",
            "primitive:admission_act_ref",
            "primitive:admission_act_digest",
            "primitive:guard_profile",
            "primitive:applicability",
            "primitive:continuity_basis_ref",
            "primitive:continuity_basis_digest",
            "primitive:continuity_source_ref",
            "primitive:continuity_source_digest",
            "primitive:sole_active_basis_ref",
            "primitive:sole_active_basis_digest",
            "primitive:sole_active_source_ref",
            "primitive:sole_active_source_digest",
            "primitive:mutation_ref",
            "primitive:program_ref",
            "primitive:decision_basis_ref",
            "primitive:decision_basis_digest",
            "primitive:expected_head_ref",
            "primitive:expected_head_revision",
            "primitive:expected_head_digest",
            "closed_command_relation_value",
            "guarded_family_preassignment_basis_v1",
            "sibling:preassigned_decision_ref",
            "sibling:preassigned_resulting_program_version_ref",
            "sibling:preassigned_guarded_family_relation_ref",
            "sibling:preassigned_guarded_progression_result_ref",
            "sibling:deterministic_family_route",
            "sibling:preassigned_acceptance_fact_ref",
            "command_digest",
            "recovery_selector_value",
            "recovery_selector_digest",
            "recovery_route_observation:mutation_receipt_route",
            "recovery_route_observation:decision_identity_route",
            "recovery_route_observation:resulting_version_identity_route",
            "recovery_route_observation:acceptance_fact_identity_route",
            "recovery_route_observation:guarded_family_relation_identity_route",
            "recovery_route_observation:guarded_progression_result_identity_route",
            "recovery_route_observation:deterministic_family_route",
            "recovery_route_observation:admitted_scope_winner_route",
            "complete_family_recovery_observation_set_v1",
            "recovery_projection"
          ],
          "node_count": 56,
          "edge_count": 157
        }
      }
    },
    "private_contract_vocabulary_id": "rw0-c2-private-value-contract-v1"
  },
  "command_digest": {
    "includes": [
      "command_profile",
      "lineage_ref",
      "scope_ref",
      "admission_fact_ref",
      "admission_fact_digest",
      "admission_act_ref",
      "admission_act_digest",
      "guard_profile",
      "applicability",
      "continuity_basis_ref",
      "continuity_basis_digest",
      "continuity_source_ref",
      "continuity_source_digest",
      "sole_active_basis_ref",
      "sole_active_basis_digest",
      "sole_active_source_ref",
      "sole_active_source_digest",
      "mutation_ref",
      "program_ref",
      "decision_basis_ref",
      "decision_basis_digest",
      "expected_head_ref",
      "expected_head_revision",
      "expected_head_digest",
      "preassigned_decision_ref",
      "preassigned_version_ref",
      "preassigned_acceptance_fact_ref",
      "preassigned_relation_ref",
      "preassigned_guarded_result_ref",
      "family_route"
    ],
    "excludes": [
      "caller_branch",
      "caller_acceptance_conclusion",
      "transaction_timestamp",
      "resulting_row_digests",
      "receipt_graph_digest",
      "terminal_outcome",
      "raw_credentials",
      "raw_external_attestations"
    ],
    "admitted_scope_match_required": true,
    "caller_can_select_unadmitted_scope": false,
    "derivation_order": "after_six_independent_siblings",
    "name": "guarded_command_digest_v1",
    "domain": "governed-execution.nwp-rw0-c2-guarded-command-digest.v1.identity",
    "ordered_preimage": [
      [
        "command_profile",
        "command_relation.schema_id",
        "nonempty_exact_str"
      ],
      [
        "lineage_ref",
        "command_relation.lineage_ref",
        "nonempty_exact_str"
      ],
      [
        "scope_ref",
        "command_relation.scope_ref",
        "nonempty_exact_str"
      ],
      [
        "admission_fact_ref",
        "command_relation.admission_fact_ref",
        "nonempty_exact_str"
      ],
      [
        "admission_fact_digest",
        "command_relation.admission_fact_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "admission_act_ref",
        "command_relation.admission_act_ref",
        "nonempty_exact_str"
      ],
      [
        "admission_act_digest",
        "command_relation.admission_act_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "guard_profile",
        "command_relation.guard_profile",
        "nonempty_exact_str"
      ],
      [
        "applicability",
        "command_relation.applicability",
        "nonempty_exact_str"
      ],
      [
        "continuity_basis_ref",
        "command_relation.continuity_basis_ref",
        "nonempty_exact_str"
      ],
      [
        "continuity_basis_digest",
        "command_relation.continuity_basis_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "continuity_source_ref",
        "command_relation.continuity_source_ref",
        "nonempty_exact_str"
      ],
      [
        "continuity_source_digest",
        "command_relation.continuity_source_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "sole_active_basis_ref",
        "command_relation.sole_active_basis_ref",
        "nonempty_exact_str"
      ],
      [
        "sole_active_basis_digest",
        "command_relation.sole_active_basis_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "sole_active_source_ref",
        "command_relation.sole_active_source_ref",
        "nonempty_exact_str"
      ],
      [
        "sole_active_source_digest",
        "command_relation.sole_active_source_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "mutation_ref",
        "command_relation.mutation_ref",
        "nonempty_exact_str"
      ],
      [
        "program_ref",
        "command_relation.program_ref",
        "nonempty_exact_str"
      ],
      [
        "decision_basis_ref",
        "command_relation.decision_basis_ref",
        "nonempty_exact_str"
      ],
      [
        "decision_basis_digest",
        "command_relation.decision_basis_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "expected_head_ref",
        "command_relation.expected_head_ref",
        "nonempty_exact_str"
      ],
      [
        "expected_head_revision",
        "command_relation.expected_head_revision",
        "nonnegative_exact_int_not_bool"
      ],
      [
        "expected_head_digest",
        "command_relation.expected_head_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "preassigned_decision_ref",
        "command_relation.preassigned_decision_ref",
        "lowercase_sha256_hex_64"
      ],
      [
        "preassigned_version_ref",
        "command_relation.preassigned_version_ref",
        "lowercase_sha256_hex_64"
      ],
      [
        "preassigned_acceptance_fact_ref",
        "command_relation.preassigned_acceptance_fact_ref",
        "lowercase_sha256_hex_64"
      ],
      [
        "preassigned_relation_ref",
        "command_relation.preassigned_relation_ref",
        "lowercase_sha256_hex_64"
      ],
      [
        "preassigned_guarded_result_ref",
        "command_relation.preassigned_guarded_result_ref",
        "lowercase_sha256_hex_64"
      ],
      [
        "family_route",
        "command_relation.family_route",
        "lowercase_sha256_hex_64"
      ]
    ],
    "serialization": "ordered_name_value_pairs_utf8_json_ensure_ascii_false_allow_nan_false_compact",
    "digest": "sha256(domain_utf8+nul+preimage_json_utf8)",
    "fixed_vector_digest": "a392abcc3f0981b4ac2aeab5d3869aea9f24ba7305b242563e3a41f402b716b1"
  },
  "prospective_fact_identity": {
    "command_field": "preassigned_acceptance_fact_ref",
    "required_all_branches": true,
    "nullable": false,
    "assertion_only": true,
    "coordinator_derived": true,
    "caller_selects_branch": false,
    "wrong_ref_invalid": true,
    "domain": "governed-execution.nwp-rw0-c2-bootstrap-acceptance-fact.v1.prospective-ref",
    "ordered_preimage": [
      [
        "command_profile",
        "preassignment_basis.command_profile",
        "nonempty_exact_str"
      ],
      [
        "lineage_ref",
        "preassignment_basis.lineage_ref",
        "nonempty_exact_str"
      ],
      [
        "scope_ref",
        "preassignment_basis.scope_ref",
        "nonempty_exact_str"
      ],
      [
        "admission_fact_ref",
        "preassignment_basis.admission_fact_ref",
        "nonempty_exact_str"
      ],
      [
        "admission_fact_digest",
        "preassignment_basis.admission_fact_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "admission_act_ref",
        "preassignment_basis.admission_act_ref",
        "nonempty_exact_str"
      ],
      [
        "admission_act_digest",
        "preassignment_basis.admission_act_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "guard_profile",
        "preassignment_basis.guard_profile",
        "nonempty_exact_str"
      ],
      [
        "applicability",
        "preassignment_basis.applicability",
        "nonempty_exact_str"
      ],
      [
        "continuity_basis_ref",
        "preassignment_basis.continuity_basis_ref",
        "nonempty_exact_str"
      ],
      [
        "continuity_basis_digest",
        "preassignment_basis.continuity_basis_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "continuity_source_ref",
        "preassignment_basis.continuity_source_ref",
        "nonempty_exact_str"
      ],
      [
        "continuity_source_digest",
        "preassignment_basis.continuity_source_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "sole_active_basis_ref",
        "preassignment_basis.sole_active_basis_ref",
        "nonempty_exact_str"
      ],
      [
        "sole_active_basis_digest",
        "preassignment_basis.sole_active_basis_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "sole_active_source_ref",
        "preassignment_basis.sole_active_source_ref",
        "nonempty_exact_str"
      ],
      [
        "sole_active_source_digest",
        "preassignment_basis.sole_active_source_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "mutation_ref",
        "preassignment_basis.mutation_ref",
        "nonempty_exact_str"
      ],
      [
        "program_ref",
        "preassignment_basis.program_ref",
        "nonempty_exact_str"
      ],
      [
        "decision_basis_ref",
        "preassignment_basis.decision_basis_ref",
        "nonempty_exact_str"
      ],
      [
        "decision_basis_digest",
        "preassignment_basis.decision_basis_digest",
        "lowercase_sha256_hex_64"
      ],
      [
        "expected_head_ref",
        "preassignment_basis.expected_head_ref",
        "nonempty_exact_str"
      ],
      [
        "expected_head_revision",
        "preassignment_basis.expected_head_revision",
        "nonnegative_exact_int_not_bool"
      ],
      [
        "expected_head_digest",
        "preassignment_basis.expected_head_digest",
        "lowercase_sha256_hex_64"
      ]
    ],
    "serialization": "ordered_name_value_pairs_utf8_json_ensure_ascii_false_allow_nan_false_compact",
    "digest": "sha256(domain_utf8+nul+preimage_json_utf8)",
    "ref_encoding": "lowercase_sha256_hex_64",
    "preimage_excludes": [
      "authoritative_branch",
      "expected_branch",
      "result",
      "guarded_relation_digest",
      "guarded_result_digest",
      "receipt_ref",
      "receipt_digest",
      "transaction_timestamp",
      "terminal_outcome",
      "current_head_after_commit",
      "raw_external_attestations"
    ],
    "command_digest_covered": true,
    "selector_covered": true,
    "collision_probe_all_branches": true,
    "acceptance_fact_count": 1,
    "nonaccept_fact_count": 0,
    "nonaccept_absence_proves_unclaimed": false,
    "derivation_basis": "guarded_family_preassignment_basis_v1",
    "sibling_independent": true
  },
  "admission_binding": {
    "verified_act_fields": [
      "schema_id",
      "act_ref",
      "act_digest",
      "lineage_ref",
      "scope_ref",
      "guard_profile",
      "applicability",
      "provenance_ref",
      "provenance_digest",
      "projection_digest"
    ],
    "immutable_fact_fields": [
      "schema_id",
      "admission_fact_ref",
      "act_ref",
      "act_digest",
      "lineage_ref",
      "scope_ref",
      "guard_profile",
      "applicability",
      "provenance_ref",
      "provenance_digest",
      "one_shot_ceiling",
      "admission_fact_digest"
    ],
    "command_equalities": [
      "lineage_ref",
      "scope_ref",
      "admission_fact_ref",
      "admission_fact_digest",
      "admission_act_ref",
      "admission_act_digest",
      "guard_profile",
      "applicability"
    ],
    "must_validate_before_branch": true,
    "command_may_admit_or_select_scope": false
  },
  "family_relation_fact_fields": {
    "fields": [
      "acceptance_fact_ref",
      "acceptance_fact_digest"
    ],
    "acceptance": {
      "ref": "reserved_command_preassigned_acceptance_fact_ref",
      "digest": "verified_actual_immutable_fact_digest",
      "fact_count": 1,
      "receipt_role_count": 1
    },
    "nonaccept": {
      "ref": null,
      "digest": null,
      "fact_count": 0,
      "receipt_role_count": 0,
      "reserved_ref_in_command_and_selector": true,
      "reserved_route_required": true,
      "null_proves_unclaimed": false,
      "occupied_reserved_identity": "collision_or_unresolved"
    }
  },
  "graph": {
    "root": "generic_v1_mutation_receipt",
    "root_fields": [
      "mutation_ref",
      "command_digest",
      "result_projection_digest",
      "mutation_graph_digest",
      "committed_at"
    ],
    "common_roles": [
      "verified_admission_act",
      "scope_admission_fact",
      "historical_continuity_basis",
      "historical_sole_active_basis",
      "decision",
      "program_version",
      "historical_head_postimage",
      "generic_v1_result_projection",
      "guarded_family_relation",
      "guarded_result_composite"
    ],
    "acceptance_only_role": "acceptance_fact",
    "historical_head_fields": [
      "schema_id",
      "program_ref",
      "current_program_version_ref",
      "current_program_version_number",
      "head_revision",
      "program_state",
      "updated_at",
      "head_digest"
    ],
    "historical_head_equalities": [
      "family_relation.historical_head_ref=historical_head_postimage.program_ref",
      "family_relation.historical_head_revision=historical_head_postimage.head_revision",
      "family_relation.historical_head_digest=historical_head_postimage.head_digest",
      "historical_head_postimage.current_program_version_ref=family_relation.version_ref",
      "acceptance_fact.historical_head_ref=family_relation.historical_head_ref",
      "acceptance_fact.historical_head_revision=family_relation.historical_head_revision",
      "acceptance_fact.historical_head_digest=family_relation.historical_head_digest"
    ],
    "role_bindings": {
      "verified_admission_act": [
        "admission_act.act_ref",
        "admission_act.act_digest",
        "authenticated_external_act"
      ],
      "scope_admission_fact": [
        "scope_admission_fact.admission_fact_ref",
        "scope_admission_fact.admission_fact_digest",
        "verified_provisioner_fact"
      ],
      "historical_continuity_basis": [
        "continuity_basis.basis_ref",
        "continuity_basis.projection_digest",
        "verified_historical_external_evidence"
      ],
      "historical_sole_active_basis": [
        "sole_active_basis.basis_ref",
        "sole_active_basis.projection_digest",
        "verified_historical_external_evidence"
      ],
      "decision": [
        "v1_decision.decision_ref",
        "v1_decision.decision_digest",
        "v1_decision_reconstruction"
      ],
      "program_version": [
        "v1_program_version.program_version_ref",
        "v1_program_version.program_version_digest",
        "v1_version_reconstruction"
      ],
      "historical_head_postimage": [
        "family_relation.historical_head_postimage.program_ref",
        "family_relation.historical_head_postimage.head_digest",
        "v1_head_reconstruction_from_complete_snapshot"
      ],
      "generic_v1_result_projection": [
        "v1_decision.decision_ref",
        "generic_result_projection.result_projection_digest",
        "v1_result_reconstruction"
      ],
      "guarded_family_relation": [
        "family_relation.relation_ref",
        "family_relation.relation_digest",
        "guarded_relation_reconstruction"
      ],
      "guarded_result_composite": [
        "guarded_result.guarded_result_ref",
        "guarded_result.guarded_result_digest",
        "guarded_result_reconstruction"
      ],
      "acceptance_fact": [
        "acceptance_fact.acceptance_fact_ref",
        "acceptance_fact.acceptance_fact_digest",
        "verified_acceptance_only_fact"
      ]
    },
    "ordinal_per_role": 0,
    "exact_member_verification": true,
    "digest_alone_proves_members": false,
    "extra_or_duplicate_roles": "reject",
    "guarded_result_profile_selector": "receipt_graph_profile_id",
    "profile_graph_role": false,
    "profile_instance_digest": false,
    "generic_receipt_self_digest": false,
    "source_exact_digest": "current_v1_receipt_preimage_plus_exact_ordered_graph_entries",
    "source_exact_receipt_preimage_fields": [
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
    "profile_completeness_rule": "reconstruct_graph_and_exact_members_then_validate_guarded_result_profile_and_branch"
  },
  "receipt_graph_profile_definition": {
    "schema_id": "governed-execution.nwp-rw0-c2-receipt-graph-profile.v1",
    "version": 1,
    "authoritative_branches": [
      "candidate_acceptance",
      "candidate_repair",
      "attempt_selecting_replan",
      "program_terminal_reject",
      "post_execution_program_block"
    ],
    "common_roles": [
      "verified_admission_act",
      "scope_admission_fact",
      "historical_continuity_basis",
      "historical_sole_active_basis",
      "decision",
      "program_version",
      "historical_head_postimage",
      "generic_v1_result_projection",
      "guarded_family_relation",
      "guarded_result_composite"
    ],
    "acceptance_only_role": "acceptance_fact",
    "role_bindings": {
      "verified_admission_act": [
        "admission_act.act_ref",
        "admission_act.act_digest",
        "authenticated_external_act"
      ],
      "scope_admission_fact": [
        "scope_admission_fact.admission_fact_ref",
        "scope_admission_fact.admission_fact_digest",
        "verified_provisioner_fact"
      ],
      "historical_continuity_basis": [
        "continuity_basis.basis_ref",
        "continuity_basis.projection_digest",
        "verified_historical_external_evidence"
      ],
      "historical_sole_active_basis": [
        "sole_active_basis.basis_ref",
        "sole_active_basis.projection_digest",
        "verified_historical_external_evidence"
      ],
      "decision": [
        "v1_decision.decision_ref",
        "v1_decision.decision_digest",
        "v1_decision_reconstruction"
      ],
      "program_version": [
        "v1_program_version.program_version_ref",
        "v1_program_version.program_version_digest",
        "v1_version_reconstruction"
      ],
      "historical_head_postimage": [
        "family_relation.historical_head_postimage.program_ref",
        "family_relation.historical_head_postimage.head_digest",
        "v1_head_reconstruction_from_complete_snapshot"
      ],
      "generic_v1_result_projection": [
        "v1_decision.decision_ref",
        "generic_result_projection.result_projection_digest",
        "v1_result_reconstruction"
      ],
      "guarded_family_relation": [
        "family_relation.relation_ref",
        "family_relation.relation_digest",
        "guarded_relation_reconstruction"
      ],
      "guarded_result_composite": [
        "guarded_result.guarded_result_ref",
        "guarded_result.guarded_result_digest",
        "guarded_result_reconstruction"
      ],
      "acceptance_fact": [
        "acceptance_fact.acceptance_fact_ref",
        "acceptance_fact.acceptance_fact_digest",
        "verified_acceptance_only_fact"
      ]
    },
    "ordinal_per_role": 0,
    "role_entry_fields": [
      "role",
      "ordinal",
      "record_ref",
      "record_digest"
    ],
    "exact_member_verification": true,
    "extra_or_duplicate_roles": "reject",
    "supersession_rule": "new_profile_id_version_and_successor_guarded_result_contract"
  },
  "branches": {
    "candidate_acceptance": [
      "accept",
      "candidate_acceptance",
      1,
      "required"
    ],
    "candidate_repair": [
      "repair",
      "candidate_repair",
      0,
      "forbidden"
    ],
    "attempt_selecting_replan": [
      "replan",
      "attempt_selecting_replan",
      0,
      "forbidden"
    ],
    "program_terminal_reject": [
      "terminal_reject",
      "program_terminal_reject",
      0,
      "forbidden"
    ],
    "post_execution_program_block": [
      "block",
      "program_block",
      0,
      "forbidden"
    ]
  },
  "collision_route_templates": [
    {
      "role": "mutation_receipt_route",
      "kind": "receipt_replay",
      "key_sources": [
        "mutation_ref"
      ],
      "expected_schema_id": "governed-execution.nwp-development-mutation-receipt.v1"
    },
    {
      "role": "decision_identity_route",
      "kind": "preassigned_identity",
      "key_sources": [
        "decision_ref"
      ],
      "expected_schema_id": "governed-execution.nwp-development-decision.v1"
    },
    {
      "role": "resulting_version_identity_route",
      "kind": "preassigned_identity",
      "key_sources": [
        "version_ref"
      ],
      "expected_schema_id": "governed-execution.nwp-development-program-version.v1"
    },
    {
      "role": "acceptance_fact_identity_route",
      "kind": "preassigned_identity",
      "key_sources": [
        "acceptance_fact_ref"
      ],
      "expected_schema_id": "governed-execution.nwp-rw0-c2-bootstrap-acceptance-fact.v1"
    },
    {
      "role": "guarded_family_relation_identity_route",
      "kind": "preassigned_identity",
      "key_sources": [
        "relation_ref"
      ],
      "expected_schema_id": "governed-execution.nwp-rw0-c2-guarded-family-relation.v1"
    },
    {
      "role": "guarded_progression_result_identity_route",
      "kind": "preassigned_identity",
      "key_sources": [
        "guarded_result_ref"
      ],
      "expected_schema_id": "governed-execution.nwp-rw0-c2-guarded-progression-result.v1"
    },
    {
      "role": "deterministic_family_route",
      "kind": "deterministic_family",
      "key_sources": [
        "family_route"
      ],
      "expected_schema_id": null
    },
    {
      "role": "admitted_scope_winner_route",
      "kind": "scope_complete_winner",
      "key_sources": [
        "lineage_ref",
        "scope_ref",
        "admission_fact_ref",
        "admission_fact_digest"
      ],
      "expected_schema_id": null
    }
  ],
  "selector": {
    "includes": [
      "lineage_ref",
      "scope_ref",
      "admission_fact_ref",
      "admission_fact_digest",
      "mutation_ref",
      "command_digest",
      "decision_ref",
      "version_ref",
      "acceptance_fact_ref",
      "relation_ref",
      "guarded_result_ref",
      "family_route",
      "required_collision_routes"
    ],
    "excludes": [
      "transaction_timestamp",
      "receipt_digest",
      "receipt_graph_digest",
      "resulting_row_digests"
    ],
    "route_element_fields": [
      "role",
      "kind",
      "key",
      "expected_schema_id"
    ],
    "route_element_types": {
      "role": "closed_enum_str",
      "kind": "closed_enum_str",
      "key": "ordered_nonnull_exact_string_array",
      "expected_schema_id": "exact_versioned_str_or_null"
    },
    "exact_route_count": 8,
    "exact_order": true,
    "role_once": true,
    "no_extensions": true,
    "key_equals_selector_top_level": true,
    "all_branches": true,
    "no_timestamp_or_postcommit_digest_dependency": true,
    "local_absence_proves_unclaimed": false,
    "route_instantiation": "ordered_selector_top_level_values_for_template_key_sources",
    "concrete_route_element_fields": [
      "role",
      "kind",
      "key",
      "expected_schema_id"
    ],
    "concrete_key_type": "ordered_nonnull_exact_string_array",
    "concrete_routes_all_branches": true
  },
  "replay": {
    "returns": [
      "original_decision",
      "original_version",
      "historical_head_postimage",
      "original_optional_acceptance_fact",
      "original_guarded_relation",
      "original_guarded_result",
      "original_generic_v1_receipt",
      "original_transaction_timestamp"
    ],
    "reevaluate_branch": false,
    "new_fact": false,
    "new_timestamp": false,
    "change_current_head": false,
    "renew_scope": false,
    "fresh_external_posture_required": true,
    "historical_basis_is_current_permission": false
  },
  "recovery": {
    "classes": [
      "committed_exact",
      "definitely_not_committed",
      "unresolved"
    ],
    "cases": [
      "same_mutation_same_command_complete_exact",
      "same_mutation_different_command_conflict",
      "preassigned_identity_or_route_collision",
      "different_complete_winner_same_scope",
      "exact_total_original_family_absence",
      "partial_orphan_duplicate_malformed_foreign_unreadable",
      "restore_or_clone_continuity_unproved"
    ],
    "exact_complete_original_class": "committed_exact",
    "same_mutation_different_digest_reason": "mutation_ref_reuse_conflict",
    "identity_or_family_route_collision_reason": "preassigned_identity_or_family_route_collision",
    "total_absence_class": "definitely_not_committed",
    "total_absence_requires_all_routes_checked": true,
    "total_absence_requires_positive_current_continuity": true,
    "total_absence_requires_positive_current_sole_active": true,
    "local_absence_without_current_posture_class": "unresolved",
    "missing_malformed_unreadable_foreign_duplicate_unchecked_route_class": "unresolved",
    "partial_or_orphan_fact_class": "unresolved",
    "different_complete_winner_can_prove_original_noncommit": true,
    "different_complete_winner_fresh_acceptance_eligible": false,
    "fresh_retry_eligibility_separate": true,
    "fresh_external_posture_required": true,
    "fragment_repair": false,
    "branch_reevaluation": false,
    "new_timestamp": false,
    "automatic_retry": false,
    "scope_renewal": false
  },
  "owner_assertion_profile": {
    "profile_id": "rw0-c2-private-owner-assertions-v1",
    "digest_domain": "governed-execution.nwp-rw0-c2-private-owner-assertions.v1",
    "digest_preimage": "ordered_registry_compact_sorted_key_json_utf8_no_newline",
    "digest_rule": "sha256(domain_utf8+nul+preimage_utf8)",
    "registry_digest": "93b76bb45f90e44c999366462adc466db21970bdfbeae51246cba616ba19edb0",
    "clause_count": 13,
    "assertion_count": 37,
    "first_clause_vector": {
      "clause_id": "historical_basis_non_authority",
      "preimage_bytes": 492,
      "digest": "a1b7dc2ec2c5576f68d47a6da3046513410d8f95cc277bbb51920d1942e14d7a"
    }
  },
  "normative_clause_registry": [
    {
      "clause_id": "historical_basis_non_authority",
      "owner_document": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
      "owner_machine_marker": "RW0_C2_BOOTSTRAP_GUARD_MACHINE_BEGIN",
      "owner_assertions": [
        {
          "json_pointer": "/scope/continuity",
          "comparison": "equals",
          "expected_value": "positively_established"
        },
        {
          "json_pointer": "/family/replay_historical_head_freshness",
          "comparison": "equals",
          "expected_value": false
        }
      ],
      "private_structural_consequence": "historical_basis_not_current_permission"
    },
    {
      "clause_id": "current_external_posture",
      "owner_document": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
      "owner_machine_marker": "RW0_C2_BOOTSTRAP_GUARD_MACHINE_BEGIN",
      "owner_assertions": [
        {
          "json_pointer": "/scope/continuity",
          "comparison": "equals",
          "expected_value": "positively_established"
        },
        {
          "json_pointer": "/scope/active_authorities",
          "comparison": "equals",
          "expected_value": 1
        }
      ],
      "private_structural_consequence": "fresh_posture_required_for_protected_disclosure"
    },
    {
      "clause_id": "mandatory_prospective_fact_coordinate",
      "owner_document": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
      "owner_machine_marker": "RW0_C2_BOOTSTRAP_GUARD_MACHINE_BEGIN",
      "owner_assertions": [
        {
          "json_pointer": "/relation/every_applicable_command",
          "comparison": "equals",
          "expected_value": true
        },
        {
          "json_pointer": "/acceptance_roles",
          "comparison": "contains",
          "expected_value": "acceptance_fact_identity"
        }
      ],
      "private_structural_consequence": "derived_nonnull_coordinate_required"
    },
    {
      "clause_id": "branch_nonselection",
      "owner_document": ".docs/rw0-c2-durable-progression-decision-semantic-contract.md",
      "owner_machine_marker": "RW0_C2_DURABLE_DECISION_FINITE_ORACLE_BEGIN",
      "owner_assertions": [
        {
          "json_pointer": "/expected_branch/role",
          "comparison": "equals",
          "expected_value": "conflict_assertion_only"
        },
        {
          "json_pointer": "/model/may_change_branch",
          "comparison": "equals",
          "expected_value": false
        },
        {
          "json_pointer": "/guard/relation_grants_authority",
          "comparison": "equals",
          "expected_value": false
        },
        {
          "json_pointer": "/guard/relation_requests_acceptance",
          "comparison": "equals",
          "expected_value": false
        }
      ],
      "private_structural_consequence": "coordinate_cannot_force_or_veto_branch"
    },
    {
      "clause_id": "nonaccept_fact_collision",
      "owner_document": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
      "owner_machine_marker": "RW0_C2_BOOTSTRAP_GUARD_MACHINE_BEGIN",
      "owner_assertions": [
        {
          "json_pointer": "/branch_effects/candidate_repair",
          "comparison": "equals",
          "expected_value": 0
        },
        {
          "json_pointer": "/taxonomy/fact_identity_collision",
          "comparison": "equals",
          "expected_value": "preassigned_identity_or_family_route_collision"
        }
      ],
      "private_structural_consequence": "nonaccept_fact_absent_but_collision_probed"
    },
    {
      "clause_id": "closed_collision_routes",
      "owner_document": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
      "owner_machine_marker": "RW0_C2_BOOTSTRAP_GUARD_MACHINE_BEGIN",
      "owner_assertions": [
        {
          "json_pointer": "/taxonomy/family_route_collision",
          "comparison": "equals",
          "expected_value": "preassigned_identity_or_family_route_collision"
        },
        {
          "json_pointer": "/eligibility/acceptance_only",
          "comparison": "contains",
          "expected_value": "exact_command_family_route"
        },
        {
          "json_pointer": "/relation/recovery_selector_covered",
          "comparison": "equals",
          "expected_value": true
        }
      ],
      "private_structural_consequence": "eight_exact_routes_required"
    },
    {
      "clause_id": "total_absence_currentness",
      "owner_document": ".docs/rw0-c2-durable-progression-decision-semantic-contract.md",
      "owner_machine_marker": "RW0_C2_DURABLE_DECISION_FINITE_ORACLE_BEGIN",
      "owner_assertions": [
        {
          "json_pointer": "/recovery/unresolved_creates_decision",
          "comparison": "equals",
          "expected_value": false
        },
        {
          "json_pointer": "/recovery/automatic_retry_after_unresolved",
          "comparison": "equals",
          "expected_value": false
        },
        {
          "json_pointer": "/recovery/readback/ambiguous",
          "comparison": "equals",
          "expected_value": "unresolved"
        }
      ],
      "private_structural_consequence": "local_absence_cannot_prove_noncommit"
    },
    {
      "clause_id": "replay_original_fact_timestamp",
      "owner_document": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
      "owner_machine_marker": "RW0_C2_BOOTSTRAP_GUARD_MACHINE_BEGIN",
      "owner_assertions": [
        {
          "json_pointer": "/family/replay_new_fact",
          "comparison": "equals",
          "expected_value": false
        },
        {
          "json_pointer": "/family/replay_new_timestamp",
          "comparison": "equals",
          "expected_value": false
        }
      ],
      "private_structural_consequence": "replay_creates_no_fact_or_timestamp"
    },
    {
      "clause_id": "admitted_scope_only",
      "owner_document": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
      "owner_machine_marker": "RW0_C2_BOOTSTRAP_GUARD_MACHINE_BEGIN",
      "owner_assertions": [
        {
          "json_pointer": "/relation/authority",
          "comparison": "equals",
          "expected_value": false
        },
        {
          "json_pointer": "/relation/requests_acceptance",
          "comparison": "equals",
          "expected_value": false
        },
        {
          "json_pointer": "/relation/roles",
          "comparison": "contains",
          "expected_value": "canonical_scope_expectation"
        },
        {
          "json_pointer": "/scope/local_absence_is_proof",
          "comparison": "equals",
          "expected_value": false
        }
      ],
      "private_structural_consequence": "command_relation_cannot_admit_scope"
    },
    {
      "clause_id": "separate_admission_decision_writers",
      "owner_document": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
      "owner_machine_marker": "RW0_C2_BOOTSTRAP_GUARD_MACHINE_BEGIN",
      "owner_assertions": [
        {
          "json_pointer": "/authority/admission",
          "comparison": "equals",
          "expected_value": "external_standing_policy"
        },
        {
          "json_pointer": "/authority/writer",
          "comparison": "equals",
          "expected_value": "future_guarded_decision_transaction"
        },
        {
          "json_pointer": "/relation/prohibited",
          "comparison": "contains",
          "expected_value": "caller_admission"
        }
      ],
      "private_structural_consequence": "decision_writer_cannot_provision_admission"
    },
    {
      "clause_id": "single_result_receipt_replay_recovery",
      "owner_document": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
      "owner_machine_marker": "RW0_C2_BOOTSTRAP_GUARD_MACHINE_BEGIN",
      "owner_assertions": [
        {
          "json_pointer": "/family/separate_receipt",
          "comparison": "equals",
          "expected_value": false
        },
        {
          "json_pointer": "/family/separate_replay",
          "comparison": "equals",
          "expected_value": false
        },
        {
          "json_pointer": "/family/separate_recovery",
          "comparison": "equals",
          "expected_value": false
        },
        {
          "json_pointer": "/authority/replay",
          "comparison": "equals",
          "expected_value": "decision_owner"
        },
        {
          "json_pointer": "/authority/recovery",
          "comparison": "equals",
          "expected_value": "decision_owner"
        }
      ],
      "private_structural_consequence": "one_decision_owned_result_receipt_replay_recovery"
    },
    {
      "clause_id": "terminal_nonreplenishment",
      "owner_document": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
      "owner_machine_marker": "RW0_C2_BOOTSTRAP_GUARD_MACHINE_BEGIN",
      "owner_assertions": [
        {
          "json_pointer": "/terminal/mutates_guard",
          "comparison": "equals",
          "expected_value": false
        },
        {
          "json_pointer": "/scope/forbidden_changes",
          "comparison": "contains",
          "expected_value": "replenish"
        }
      ],
      "private_structural_consequence": "terminal_cannot_replenish_acceptance"
    },
    {
      "clause_id": "es_nonreplenishment",
      "owner_document": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
      "owner_machine_marker": "RW0_C2_BOOTSTRAP_GUARD_MACHINE_BEGIN",
      "owner_assertions": [
        {
          "json_pointer": "/es/replenishes",
          "comparison": "equals",
          "expected_value": false
        },
        {
          "json_pointer": "/es/new_grant_or_policy_epoch_replenishes",
          "comparison": "equals",
          "expected_value": false
        },
        {
          "json_pointer": "/es/separately_governed",
          "comparison": "equals",
          "expected_value": true
        }
      ],
      "private_structural_consequence": "es_cannot_replenish_direct_local_allowance"
    }
  ],
  "v1": {
    "decision": [
      "governed-execution.nwp-development-decision.v1",
      "governed-execution.nwp-development-decision.v1.identity"
    ],
    "program_version": [
      "governed-execution.nwp-development-program-version.v1",
      "governed-execution.nwp-development-program-version.v1.identity"
    ],
    "program_head": [
      "governed-execution.nwp-development-program-head.v1",
      "governed-execution.nwp-development-program-head.v1.identity"
    ],
    "generic_result": [
      "governed-execution.nwp-record-development-progression-decision-result.v1",
      "governed-execution.nwp-record-development-progression-decision-result.v1.identity",
      [
        "schema_id",
        "program_ref",
        "decision_ref",
        "result_program_version_ref",
        "result_decision_ref"
      ]
    ],
    "generic_receipt": [
      "governed-execution.nwp-development-mutation-receipt.v1",
      "governed-execution.nwp-development-mutation-receipt.v1.identity"
    ],
    "graph_entry_fields": [
      "role",
      "ordinal",
      "record_ref",
      "record_digest"
    ],
    "migration_catalog": [
      "0001_initial.sql",
      "0002_development_program_and_effect_state.sql",
      "0003_cognitive_proposal_and_selection_state.sql",
      "0004_rw0_c1_durable_evidence.sql"
    ],
    "preserve_bytes": true,
    "append_existing_v1_field": false,
    "new_v1_authority": false
  },
  "b1": {
    "pair": [
      "latch_postimage_ref",
      "latch_postimage_digest"
    ],
    "guarded_writer_consumes_pair": false,
    "pair_proves": "supplied_representation_and_pair_coherence_only",
    "durable_guard_authority": false,
    "terminal_consumer": "separately_accepted_safe_value_compatibility_versioning_contract",
    "successor_defined": false
  },
  "boundaries": {
    "admission_writer": "future_separate_admission_provisioner_only",
    "acceptance_writer": "future_guarded_decision_writer_acceptance_only",
    "receipts": 1,
    "replay_owners": 1,
    "recovery_classifiers": 1,
    "local_absence_admits_or_unclaims": false,
    "operational_identity_is_lineage": false,
    "external_currentness_is_local_durable_fact": false,
    "mutable_latch_state": false,
    "terminal_creates_or_replenishes_acceptance": false,
    "es_replenishes_direct_local": false,
    "migration_0005_implemented": false,
    "provisioner_implemented": false,
    "writer_implemented": false,
    "reader_implemented": false,
    "recovery_implemented": false,
    "production_caller_implemented": false,
    "public_export_implemented": false,
    "runtime_implemented": false
  },
  "recovery_observation_set": {
    "name": "complete_family_recovery_observation_set_v1",
    "kind": "non_durable_postread_derivation_not_logical_schema",
    "owner": "decision_owner_existing_whole_family_recovery",
    "posture_fields": [
      "lineage_ref",
      "scope_ref",
      "fresh_current_continuity",
      "fresh_current_sole_active"
    ],
    "posture_value_fields": [
      "status",
      "posture_ref",
      "posture_digest"
    ],
    "posture_statuses": [
      "positive",
      "missing",
      "stale",
      "unknown",
      "conflicting",
      "negative"
    ],
    "route_observation_fields": [
      "route_role",
      "route_key",
      "status",
      "read_attempted",
      "readable",
      "evidence_ref",
      "evidence_digest",
      "total_absence_proved"
    ],
    "route_statuses": [
      "unchecked",
      "exact_complete_family",
      "absent",
      "partial",
      "duplicate",
      "foreign",
      "malformed",
      "unreadable",
      "route_identity_conflict",
      "competing_complete_scope_winner"
    ],
    "route_roles": [
      "mutation_receipt_route",
      "decision_identity_route",
      "resulting_version_identity_route",
      "acceptance_fact_identity_route",
      "guarded_family_relation_identity_route",
      "guarded_progression_result_identity_route",
      "deterministic_family_route",
      "admitted_scope_winner_route"
    ],
    "route_order_exact": true,
    "total_absence_rule": "all_eight_absent_and_proved_with_both_positive_fresh_postures",
    "complete_rule": "exact_original_family_every_required_route_and_member_command_binding_with_positive_fresh_posture",
    "unresolved_rule": "unchecked_partial_duplicate_foreign_malformed_unreadable_identity_conflict_mixed_missing_duplicate_or_insufficient_posture",
    "no_local_absence_outside_observations": true,
    "selector_phase": "precommit_query_plan",
    "observation_phase": "postread_classification_basis",
    "new_receipt_or_recovery_owner": false,
    "route_status_rules": {
      "unchecked": {
        "read_attempted": false,
        "readable": false,
        "evidence_ref": "null",
        "evidence_digest": "null",
        "total_absence_proved": false
      },
      "exact_complete_family": {
        "read_attempted": true,
        "readable": true,
        "evidence_ref": "nonempty_string",
        "evidence_digest": "lowercase_sha256_hex",
        "total_absence_proved": false
      },
      "absent": {
        "read_attempted": true,
        "readable": true,
        "evidence_ref": "null",
        "evidence_digest": "null",
        "total_absence_proved": true
      },
      "partial": {
        "read_attempted": true,
        "readable": true,
        "evidence_ref": "nonempty_string",
        "evidence_digest": "lowercase_sha256_hex",
        "total_absence_proved": false
      },
      "duplicate": {
        "read_attempted": true,
        "readable": true,
        "evidence_ref": "nonempty_string",
        "evidence_digest": "lowercase_sha256_hex",
        "total_absence_proved": false
      },
      "foreign": {
        "read_attempted": true,
        "readable": true,
        "evidence_ref": "nonempty_string",
        "evidence_digest": "lowercase_sha256_hex",
        "total_absence_proved": false
      },
      "malformed": {
        "read_attempted": true,
        "readable": true,
        "evidence_ref": "nonempty_string",
        "evidence_digest": "lowercase_sha256_hex",
        "total_absence_proved": false
      },
      "unreadable": {
        "read_attempted": true,
        "readable": false,
        "evidence_ref": "null",
        "evidence_digest": "null",
        "total_absence_proved": false
      },
      "route_identity_conflict": {
        "read_attempted": true,
        "readable": true,
        "evidence_ref": "nonempty_string",
        "evidence_digest": "lowercase_sha256_hex",
        "total_absence_proved": false
      },
      "competing_complete_scope_winner": {
        "read_attempted": true,
        "readable": true,
        "evidence_ref": "nonempty_string",
        "evidence_digest": "lowercase_sha256_hex",
        "total_absence_proved": false
      }
    },
    "result_fields": [
      "classification",
      "lineage_ref",
      "scope_ref",
      "current_continuity_posture_ref",
      "current_continuity_posture_digest",
      "current_sole_active_posture_ref",
      "current_sole_active_posture_digest"
    ],
    "result_posture_binding": "exact_copy_of_validated_current_recovery_posture_pairs",
    "competing_winner_rule": "scope_winner_route_only_with_all_other_routes_absent_proves_original_noncommit_without_fresh_acceptance_eligibility",
    "evidence_digest_domain": "governed-execution.nwp-rw0-c2-route-observation-evidence.v1",
    "evidence_digest_derivation": "sha256(domain_utf8+nul+evidence_ref_utf8)",
    "private_contract_vocabulary_id": "rw0-c2-private-value-contract-v1"
  },
  "validated_current_recovery_posture": {
    "name": "validated_current_recovery_posture_v1",
    "kind": "transient_private_external_current_evidence_validation_not_logical_schema",
    "fields": [
      "lineage_ref",
      "scope_ref",
      "current_continuity_posture_ref",
      "current_continuity_posture_digest",
      "continuity_state",
      "current_sole_active_posture_ref",
      "current_sole_active_posture_digest",
      "sole_active_state"
    ],
    "continuity_states": [
      "positively_established",
      "missing",
      "stale",
      "unknown",
      "conflicting",
      "negative"
    ],
    "sole_active_states": [
      "exactly_one_active_authority",
      "missing",
      "stale",
      "unknown",
      "conflicting",
      "not_exactly_one"
    ],
    "positive_continuity_state": "positively_established",
    "positive_sole_active_state": "exactly_one_active_authority",
    "binding": "exact_selector_lineage_scope_and_fresh_observation_coordinates_and_states",
    "historical_basis_allowed": false
  },
  "recovery_projection_signature": {
    "parameters": [
      "observed_set",
      "canonical_binding",
      "validated_current_posture"
    ],
    "canonical_binding_fields": [
      "command",
      "branch",
      "family",
      "selector"
    ],
    "unknown_keys": "reject",
    "classification_input": false,
    "classifier": "_classify_complete_family_recovery",
    "classification_source": "classifier_return"
  },
  "private_contract_vocabulary": {
    "private_contract_vocabulary_id": "rw0-c2-private-value-contract-v1",
    "lifecycle_ids": [
      "fresh_write_construction_v1",
      "exact_replay_readback_v1",
      "uncertain_commit_recovery_v1"
    ],
    "route_observation_statuses": [
      "unchecked",
      "exact_complete_family",
      "absent",
      "partial",
      "duplicate",
      "foreign",
      "malformed",
      "unreadable",
      "route_identity_conflict",
      "competing_complete_scope_winner"
    ],
    "recovery_result_schema_id": "governed-execution.nwp-rw0-c2-complete-family-recovery-result.v1",
    "recovery_result_payload_fields": [
      "classification",
      "lineage_ref",
      "scope_ref",
      "current_continuity_posture_ref",
      "current_continuity_posture_digest",
      "current_sole_active_posture_ref",
      "current_sole_active_posture_digest"
    ]
  }
}
```
<!-- RW0_C2_PRIVATE_VALUES_MACHINE_END -->
