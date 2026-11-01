# RW0-C2 artificial-offline physical program

Status: independently accepted private artificial-offline P0→P1 source,
locally committed as `8704e6c7988250598809f3a0daf88c3e11493488` at tree `161ed4b544baf970cc26428b9805a106ea0f3edf`; publication and live operation
remain separate gates. The exact P0/work-head checkpoints and blocked
21-field basis predecessor below remain historical evidence. The current
basis-v2, command-digest-v2, and disclosure/eligibility-split repairs were
accepted together by the independent artifact audit. The private fenced P1
writer, readback, replay, and three-way recovery are present in source.

## Owner split

P0 owns program-independent safe admission recording and its own receipt,
replay, and three-way recovery. P1 owns the later five-branch development
progression decision and acceptance-only fact in a separate transaction. A
P0 commit grants no current authority and implies no P1 decision.

## Phase A physical family

Migration 0006 creates `rw0_c2_verified_admission_acts`,
`rw0_c2_scope_admission_facts`, `rw0_c2_scope_admission_recording_bases`, and
`rw0_c2_scope_admission_recording_receipts`. Each is immutable. The fact table
uniquely occupies act, lineage, and scope separately. The basis retains safe
historical enrollment, recording-permission, and custody evidence coordinates
without assigning them SQL uniqueness. The result is reconstructed from the
checked basis and receipt. Command and row digests follow the v1 P0 contract.

The private writer uses the existing fenced writer-session mutation controller,
receipt-first replay, collision probes, one COMMIT, and read-only original-family
recovery. Only artificial fixture-authored source observations are supported.
No live enrollment, production caller, worker, provider, ES/Bridge, Git effect,
terminal outcome, or power-loss-safe durability claim follows.

## Phase B corrected replan identity order

The current uncommitted source adds migration 0007 and its six immutable
supplemental table families, updates the cumulative migration catalog, and adds
private P1 basis, relation, proposal, row, reducer, pure write-plan, and fenced
SQLite family modules.
The historical exact-0006 checkpoint remains separately attributable;
migration 0006 and both P0 private production modules retain their checkpoint
bytes.

The earlier partial replan proposal incorrectly contained a complete
proposal-owned `WorkSpecV1`. That assigned the future Coordinator-owned
`program_version_ref` before the decision basis could derive it, creating the
preassignment cycle recorded in the retained stop package. The corrected
authority contract makes the cognitive role supply only version-neutral content
and source intent evidence. Its private
`CognitiveReplanWorkSpecTemplateV1` has exactly `schema_id`, `program_ref`,
`work_item_ref`, `repository_ref`, `base_git_object_format`, `base_git_oid`,
`authorized_paths`, `objective`, `requirements`, `exclusions`,
`validation_requirement_ref`, `review_requirement_ref`,
`privacy_classification`, and `template_digest`. Its schema is
`governed-execution.nwp-rw0-c2-cognitive-replan-work-spec-template.v1` and its
self-digest domain is that schema plus `.identity`. Private text remains only in
this transient value. The closed safe projection has exactly `schema_id`,
`program_ref`, `work_item_ref`, `repository_ref`, `base_git_object_format`,
`base_git_oid`, `authorized_paths`, `validation_requirement_ref`,
`review_requirement_ref`, `privacy_classification`, `template_digest`, and
`safe_projection_digest`; its schema is
`governed-execution.nwp-rw0-c2-cognitive-replan-work-spec-template-safe.v1`
and its digest domain is that schema plus `.identity`.

`CognitiveReplanProposalV1` has only `source_intent_ref`,
`source_intent_digest`, and `work_spec_template`. Its closed safe projection has
`schema_id`, those two source coordinates,
`work_spec_template_safe_projection`, and `proposal_digest`. That safe value is
the replan-only member of the current 23-field decision basis v2. Its 21-field
v1 predecessor is retained as historical, uncommitted, blocked evidence. V2
inserts exact typed `validation_disposition` and
`independent_review_disposition` mappings before `captured_at` and
`basis_digest`. The six branch-neutral preassignments still derive from the
accepted 24-coordinate transcript after the basis closes. The current
guarded-command-digest v2 then hashes the 30 validated relation pairs and the
exact optional `expected_branch` as pair 31. The assertion never changes a
preassignment or selects a branch.

Only after `attempt_selecting_replan` is independently selected does the
Coordinator derive new accepted-intent, work-revision, and WorkSpec refs as
three independent siblings from the ordered ten-coordinate transcript:
`command_digest`, `program_ref`, `current_program_version_ref`,
`current_accepted_intent_revision_ref`, `work_item_ref`,
`current_work_item_revision_ref`, `source_intent_ref`,
`source_intent_digest`, `work_spec_template_digest`, and
`preassigned_version_ref`. Their domains are respectively
`governed-execution.nwp-rw0-c2-replan-accepted-intent-revision-ref.v1`,
`governed-execution.nwp-rw0-c2-replan-work-item-revision-ref.v1`, and
`governed-execution.nwp-rw0-c2-replan-work-spec-ref.v1`. The Coordinator then
binds the unchanged existing `WorkSpecV1` and its existing 0002 safe
projection to those refs and the preassigned resulting version. The final
WorkSpec digests are dependent outputs and never feed the decision basis.

The current basis-v2 artificial replan identity vector is:

| Value | SHA-256 lowercase hex |
| --- | --- |
| template digest | `61dc84e3b4fdc2cc2a43291d65945c041b9b74dbf5b5a2234258b0164802dcce` |
| template safe-projection digest | `70240825c9165e43289b8e6468089f2d6e91a370f521c7b747fe64f837d3891b` |
| proposal digest | `c8bc73fd8957634173eaa889b13d926c3532d16ceaf0f6e5cd42766886277e68` |
| decision-basis digest | `3dcd3729b90e18b045d447420894261d05187f4342dc3af2634192d2bc50827d` |
| preassigned resulting version ref | `de16c32f21a01bb2c062c63cd024857c041a4c5984446047a8df0481efd4f84c` |
| historical relation-core digest v1 | `70a186fd5429da5b53e465f50755863e14e6875bd009f318e16cfee3e0facc10` |
| current command digest v2 | `7c80a9eee614e071876602b91a8fc2d1108f58b7fb8974785a47a03bd8ff43c6` |
| derived accepted-intent revision ref | `9d05a865af7f525530d3a33f74393734162340cabeece693cf1cc8017504fab8` |
| derived work-item revision ref | `8f454c0c381e8d7093125be0ea26e6b6797c040ae28fd03c81caeeee572d2144` |
| derived WorkSpec ref | `66e14a94c24b97119c77a03374bced3081a069315d6864a511398d9206dff2b7` |
| final existing WorkSpec digest | `96181b95bad1f0cd06444d7d32602619318e10631d3c963dabd8fa7e462b756e` |
| guarded relation digest | `e4d625c2f4185f5861cc70da4e9d1cde2400eadc080e084df0767af15b359203` |
| guarded result digest | `5f4c1302e303e5e26926a2a72a9f66f82db9a5c7bce8b115a6b9f48d9ea87835` |
| receipt graph digest | `a7ba446a7fe7cdab9bf86e07193498e81a46d63a4c3aa82274aed7eb03615f60` |

The earlier vector derived from basis v1 is superseded and has no current
validation credit. The template and safe proposal digests remain unchanged;
each downstream identity above is recomputed from the basis-v2 binding.

P0 remains usable independently and provides no P1 acceptance or terminal
fact. The prior failed-cycle source and report remain historical development
evidence, not P1 implementation credit.

## P1 historical replan work-head boundary

The corrected noncircular identity construction does not resolve one separate
physical replay obligation. A fresh `attempt_selecting_replan` would create an
immutable accepted-intent revision, work-item revision, two supersedes edges,
WorkSpec binding, membership closure, decision, version, and P1 supplements,
and would CAS-update the mutable `development_work_item_heads` row. The accepted
RW0-C2 private value/versioning contract freezes the guarded relation's 26
logical preimage fields and the ten common receipt-graph roles. Its retained
historical head postimage and graph role refer only to
`development_program_heads`. Neither the relation nor the graph retains the
replan work-item head postimage or its digest.

Migration 0002 does not link an immutable replan revision or membership row to
the current work-item-head revision. The work-item head can later advance, so
the original head row and its digest cease to be readable. Two histories can
then have the same immutable replan rows, receipt, and final current head while
differing in whether the first replan transaction updated that head. Rebuilding
an expected prior head from revision numbers and timestamps reconstructs a
claim, not an observed historical head update. The accepted program-head
postimage mechanism has no work-head analogue.

The requested receipt-first exact replay, full replan-family readback, and
`committed_exact` uncertain-commit classification explicitly require checking
the updated work-item head after later progression. Extending the guarded
relation or receipt graph would change a closed accepted v1 value/profile;
adding a separate immutable witness would require a new physical and authority
decision. Treating a receipt and immutable replan rows as sufficient would
silently weaken the requested completeness rule. Under the user's explicit
stop condition, P1 writer integration therefore stops here. The separate
external writer draft is retained only as superseded development evidence and
is absent from the repository source. This section records the conflict; it
does not revise the accepted contract or authorize a replacement profile.

## Authorized v2 work-head successor under implementation

The later engineering decision authorizes a bounded versioned successor to
the v1 guarded relation, guarded result, and graph profile. Their exact current
IDs are `governed-execution.nwp-rw0-c2-guarded-family-relation.v2`,
`governed-execution.nwp-rw0-c2-guarded-progression-result.v2`, and
`governed-execution.nwp-rw0-c2-receipt-graph-profile.v2`. The relation adds
four ordered work-head witness fields after the program-head postimage. Replan
alone carries a complete typed canonical work-head postimage and the extra
`historical_work_head_postimage` graph role; acceptance retains its one
acceptance role; other branches retain exactly the ten common roles. The
single generic receipt shape and pre-command/replan identity grammar stay
unchanged. The later basis-v2 successor recomputes identity bytes. The
predecessor v1 block in the private value owner remains
historical contract evidence. Migration 0007 remains six supplemental tables;
its basis-v2 schema-ID CHECK has the checksum recorded below. This section
records the v2 work-head contract decision; the physical
owner below describes the current uncommitted implementation candidate.

## Private physical P1 transaction and readback

Migration 0007's literal SQL SHA-256 is
`505d72c9c54f68e248bebab928e76564d45b853068b8b4021ebc708b640e430c`.
Its cumulative schema has 74 tables, 134 triggers, and five explicit indexes.
`_SQLiteWriterSession._record_progression_decision()` is private and uses the
existing operation guard and single mutation transaction controller. The
controller opens a resource-bound `BEGIN IMMEDIATE` transaction, revalidates
writer issuance and managed schema, and lends a nominal read capability.

Receipt-first replay precedes fresh eligibility. Fresh processing checks the
complete persisted P0 act/fact family, independently supplied artificial
continuity/sole-active/guard posture, expected program head, current 0002
program version, intent, work head/revision, membership closure, selected
attempt/fence, and inactive coding global stop. The pure five-branch reducer
consumes the exact typed validation/review dispositions embedded in the
basis-v2 canonical BLOB. Detached arguments must match them before route
probing or writes. One pure candidate-classification helper derives the
candidate reason from those persisted values for both fresh reduction and
historical reconstruction. Its model recommendation is non-authoritative.
No command record is an executable grant.

`ArtificialDecisionGuardSourceV1.checked_for(...)` validates universal current
posture only: exact source types, time window, positive and basis-bound
continuity and sole-active observations, no foreign claim with historical
binding, and recording or disclosure permission according to the operation.
It type-checks current `acceptance_exhaustively_unclaimed` as exact `bool` or
`None` without treating it as universal permission or comparing it to the
historical basis. For a fresh receipt miss, recording posture precedes route
and current-state checks; after the authoritative reducer selects
`candidate_acceptance`, `checked_acceptance_eligibility_for(...)` requires
both historical basis and current source to assert exhaustive unclaimed scope.
Current `False` or `None` returns the existing
`bootstrap_acceptance_guard_conflict` before any write. Nonaccept branches
ignore claimed status after type validation and create no acceptance fact.

The write plan is checked for cross-record coherence before insertion. Every
branch inserts one decision, resulting version, complete membership, five
common P1 supplements, and the single generic 0002 receipt. Acceptance alone
inserts the sixth acceptance fact. Replan additionally inserts one accepted
intent revision, one work revision, two revision edges, and one WorkSpec safe
binding. It CAS-updates the program head and, for replan only, CAS-updates the
work head. Both actual post-CAS heads are SELECTed and type-checked in the same
transaction; all planned immutable rows are read back before the receipt is
inserted last. A failed CAS, readback mismatch, or incomplete family rolls
back. The capability is invalidated before one COMMIT attempt. A lost commit
response or unproved close returns `commit_outcome_unknown` without automatic
retry.

Exact replay uses the receipt first and requires fresh positive protected
disclosure through the current guard source before command-digest comparison
or family reconstruction. A changed `expected_branch` has a different current
v2 command digest and conflicts on the occupied mutation route. Record mode
requires disclosure for receipt replay even when recording is denied; a
receipt-free fresh record instead requires recording posture before route
probing. Read mode checks disclosure before reporting absence. Recovery checks
disclosure before `committed_exact` or `definitely_not_committed`, and returns
`unresolved` on denied or unverifiable posture. One transaction/read timestamp
is shared by the gate and subsequent processing. Receipt-present replay/read/
recovery does not reevaluate current unclaimed-scope eligibility: after a
committed acceptance, truthful current `False` still permits exact protected
replay when universal disclosure is positive.

The bounded transaction-controller timestamp plumbing is a source successor
to the prior P0/P1 source identity. The B3c4c assurance test retains its
historical source hashes and pins the current successor while preserving the
existing controller, import, and call-boundary checks.

After the disclosure gate, replay reconstructs typed historical predecessor
rows, basis-v2 dispositions, candidate reason, and both v2 postimages from
immutable family evidence, runs the same pure reducer without renewed cognition
or historical source sampling, rebuilds the pure write plan, and compares every
resulting immutable row, membership, graph role, digest, and receipt. It never
compares a historical head witness to a later mutable head. Read-only recovery
returns `committed_exact` only for that complete family,
`definitely_not_committed` only when all original creation routes are absent
under positive continuity/sole-active and old-execution exclusion, and
`unresolved` for partial, foreign, malformed, unreadable, or contradictory
evidence. A different complete acceptance winner can occupy the scope while
the original command is definitely absent; its completeness is checked
independently and it does not permit a fresh acceptance retry. An explicit
current claimed status `False` with no complete local winner is contradictory
recovery evidence and remains `unresolved`, even when original routes are
absent. Current `None` with no contradictory claim retains the ordinary
exhaustive-route absence classification. Neither result grants fresh
acceptance eligibility.

The connected disposable proof uses actual D1/D2 offline processes and
capsule, guarded Section 41 post-execution proposal, C1 rank-15 admission, and
V22 projection in one temporary database. D1 owns creation of that database;
the connected test records the independent P0 family through a test-only
initialization hook immediately after D1 creates the state and before D1
program progression begins. The fixed
fake validator emits a passed disposition, so the four alternate P1 branches
use controlled typed validation variations on the same actual owner
coordinates. This private implementation remains uncommitted and unaudited.
It grants no live evidence source, current external grant, product Git effect,
terminal fact, service, worker transport, or production admission.

<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
## Accepted local source and residual boundaries

Independent artifact audit accepted exact Git-compatible tree `161ed4b544baf970cc26428b9805a106ea0f3edf`; local
commit `8704e6c7988250598809f3a0daf88c3e11493488` has sole parent `4519630d0db967066beb21b4ace5004e76827716`, records that tree on
`codex/rw0-c2-p0-p1-physical-program-v1`, and has no upstream. The gate
reconciled 9,473 collected/executed/JUnit/passed IDs in exact order with zero
failures, errors, or skips and three known Python 3.13 multithreaded-fork
`DeprecationWarning` records. No push, PR, merge, publication, deployment, or
product effect occurred. Git objects and refs own current commit/ref truth;
independent audit, validation, provenance, closeout, and this text are evidence
only, not Coordinator durable authority or effect permission.

The earlier candidate-stage paragraphs in this owner preserve their historical
source chronology; this block supersedes their present-tense uncommitted,
unaudited, and pending-audit status. Current source remains a bounded private
artificial-offline proof over task-owned SQLite and controlled fake processes.
P0 and P1 are separate fenced physical transactions. P0 records a verified
admission act/fact, basis, and receipt as history without current authority.
P1 records one of five progression branches; only candidate acceptance records
an acceptance fact, which is not terminal truth. Decision Basis v2 and
`guarded-command-digest.v2.identity` preserve exact branch assertion identity;
relation/result/profile v2 retain the historical work-head witness. Fresh
universal disclosure guards replay, read, and recovery, while current
unclaimed-scope eligibility is required only for fresh candidate acceptance.

F03 remains a nonblocking observation: this bounded P0 implementation does
not implement every earlier target-only selector/wrapper field, with no
observed authority bypass. F05 remains a nonblocking observation: P0 samples
time before its fresh collision probe, potentially changing no-write error
precedence only. Earlier full-ref and raw-index observation limits remain
historical limits; the gate did not backdate those proofs. No live enrollment
or custody supplier, external standing authority, terminal owner, executable
permission, production provider or worker, ES/Bridge route, product Git
effect, service, queue, scheduler, deployment, or autonomous loop is claimed.
<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure current candidate

The uncommitted `artificial_offline_normal.v1` candidate adds a separate private Coordinator terminal writer on generation-2 migration 0008. It consumes checked P0, phase, Section 41 A, C1 rank-15/V22 and P1 evidence under one fenced transaction and records only the five normal outcomes: accept, repair, replan, terminal_reject and block. The P1 decision remains prior decision history; its acceptance fact is bound only for accept and is never mutated. Cancellation, live supplier/contact, ES routing, Git effects, publication and executable permission remain outside this candidate. See `.docs/rw0-terminal-outcome-physical-closure.md`.

The integrated P0/P1 baseline is PR #17 squash `61d0330aba1160f7f5e7d9c541a325222d1c61e5`, tree `44c7dee402d46b3e16dc389ae0824b4297dfec1f`. Earlier candidate and local-commit blocks are historical. P0/P1 source and SQL meanings remain unchanged. This terminal successor awaits independent audit.
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
