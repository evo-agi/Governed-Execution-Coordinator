# RW0-C2 First-Live Single-Realization Proof Posture

Logical support-profile ID: `rw0-c2-single-realization-proof-v1`.
Classification: `ACCEPTED TARGET / FIRST-LIVE SUPPORT PROFILE`; unimplemented.
This is the restricted support profile for the first RW0-E live direct-local
proof, not a permanent Coordinator deployment restriction. It selects no
production supplier, launch mechanism, service, wire format, credential
encoding, SQLite layout, or migration.

## Owner boundary

This document owns the first-live operating conditions, external source
obligations, continuity-loss rule, and implementation-entry evidence. The
bootstrap guard remains the sole semantic owner of admitted lineage, one
scope, fresh universal posture, acceptance-only exhaustive unclaimed-scope
proof, immutable acceptance membership, and non-replenishment. The durable
progression-decision owner alone reduces a command to one of its five branches
and owns the atomic decision/version/head/result/receipt family, exact replay,
and one whole-family recovery classifier. External standing policy authors
admission and grants. This profile is neither an acceptance classifier nor a
second retry or recovery owner.

The eleven private schemas and receipt-graph profile in
`.docs/rw0-c2-private-value-versioning.md` keep their exact IDs, fields,
canonical bytes, and digest meanings. A future proof-source envelope needs its
own separately accepted version; it cannot be silently appended to a v1 value.
The guarded writer and the current local `WriterSession` lock do not create
external lineage or continuity authority. Reports, a stored digest, a PID,
inode, database row, signed old response, or local lock cannot establish the
current profile on their own.

## Irreversible enrollment and activation

One scope belongs to one explicitly standing-policy-admitted Coordinator
authority lineage. An authenticated external standing-policy act must admit
both that lineage and its initial live proof. An empty database, an absent
enrollment record, or a new operational identifier is never an admission act.

Before live activation, a source independent of Coordinator SQLite durably
assigns the admitted lineage to exactly one authority incarnation. That
enrollment must lie outside every Coordinator database and snapshot domain
that could recreate the incarnation. It is conditionally created once and is
non-reissuable: Coordinator, launcher, worker, and model cannot delete,
replace, renew, or reissue it. The assignment survives database rollback.
Enrollment response loss permits read-only reconciliation with the
independent source. If launch possibility remains ambiguous, no second launch
is permitted. First activation must be serialized by the privileged source
boundary; the user is not a per-command evidence courier.

A different process, copied or restored memory, copied database, different
machine, or relabeled operational identifier cannot authenticate as the
enrolled incarnation. An enrolled or historically ambiguous lineage cannot
be relabeled into a supposedly independent lineage for routine recovery.
Enrollment is an incarnation assignment, not an acceptance receipt or fact,
consumed allowance, C2 classifier, or guarantee of eventual availability.
Failure after enrollment and before acceptance can retire proof availability
without asserting that the allowance was consumed.

The separate target admission-recording semantics are owned by
`.docs/rw0-c2-scope-admission-provisioning-contract.md`. A future provisioner
may record an exact verified, program-independent immutable scope-admission
fact before a program exists;
the guarded decision writer may only read it. Migration-0002 development
mutation receipts are program-bound and cannot record this act by inventing a
dummy program or repurposing a v1 field. Admission recording and its
owner-governed readback/recovery still need later physical and runtime
contracts. Neither
enrollment nor admission recording creates a C2 acceptance fact.

## Continuous managed custody and current permission

A separately privileged managed-execution boundary must bind the enrolled
incarnation to the one live authority process and original writable SQLite
state. It enforces exclusive original storage custody, no unauthorized writer
or state copy becoming writable, and a live nontransferable source relationship
outside copied Coordinator state. It must mechanically deny or invalidate
process restart, supervisor restart or identity loss, database replacement or
in-place rollback, memory restore, clone activation, relocation, and handoff.
Simply labeling these operations unsupported does not close an unnoticed
restore path.

Each applicable C2 command obtains fresh source-authored positive lineage
continuity, sole-active, and no-foreign posture. Authenticated local contact
with the privileged enforcer can supply it; no new remote checkpoint
transaction is required. Missing, stale, unknown, ambiguous, negative, or
unfenced posture fails before protected receipt disclosure or work. The
enforcer reports incarnation and custody facts and fences resources; it does
not inspect program intent to select a C2 branch, author acceptance, advance
heads, schedule work, choose retries, classify recovery, or expand policy.

Current parent-grant, expiry, revocation, applicable global-stop,
repository/path, effect, and audience checks still apply at their existing
owners. An enrollment record is never standing execution permission. Workers
and model processes receive no Coordinator database access, enrollment
credential, management API, or proof-source signing authority.

There is one enrollment write before activation. No per-admission-write or
per-acceptance-write external arm is selected. The four nonaccept branches
require no per-nonaccept external checkpoint, and ordinary progression has no
general external checkpoint. Under uninterrupted original process and storage
custody, a committed acceptance cannot vanish while the original SQLite
state remains authoritative. Fresh source posture plus the Coordinator's
exhaustive guard-family read can therefore support acceptance-only unclaimed
proof; source posture alone never proves an unclaimed scope. The guarded
Coordinator transaction alone writes the acceptance fact atomically with the
decision/version/head/result/receipt family. The four nonaccept branches
write no acceptance fact and make no unclaimed-scope assertion.

| Operation class | External participation | Coordinator responsibility |
| --- | --- | --- |
| Initial proof admission | Authenticated standing-policy act and one independent durable incarnation enrollment before activation | Later separate provisioner records exact admission fact; no program required |
| Fresh C2 command, including nonaccept | Current source-authored custody/lineage/sole-active/no-foreign posture and existing policy checks; no external checkpoint write | Validate command and derive branch; four nonaccept branches assert no unclaimed scope |
| First candidate acceptance | Same fresh posture; no external acceptance arm or classifier | Exhaustively prove unclaimed scope, then atomically commit one acceptance family |
| Exact replay or uncertain-commit readback | Fresh positive posture for the same original incarnation and storage | Return original family or apply the one whole-family recovery classifier; unresolved gives no retry permission |
| Teardown or continuity loss | Source-owned resource fencing and completion evidence; failure freezes continuation | Preserve committed facts; do not manufacture an outcome or start a successor |
| Later ES route | Separately governed ES and standing policy | No replenishment of direct-local allowance |

## Supported lifecycle and irreversible loss

Supported operation is one initial activation, ordinary Coordinator-owned
progression during continuous original process/storage custody, four
nonaccept branches without an unclaimed assertion, at most one productive
acceptance across programs, exact replay/readback in the same incarnation
while original state and custody remain provable, and bounded source-owned
teardown under existing effect and cancellation rules. Exact replay preserves
the original command, family, and timestamp. A normal terminal closure does
not renew enrollment. Terminal output and later ES work do not replenish the
direct-local allowance.

Unsupported continuation includes authority-process restart, supervising
custody-authority restart or loss of live identity, database replacement or
in-place snapshot rollback, memory checkpoint/restore, activated clone,
relocation, machine replacement, handoff, unproved original storage, or
unproved former-writer status. Any such transition permanently denies new
protected work for this first-live proof. There is no resume, reset, new
incarnation, or replacement launch within this support profile. An independent
lineage requires a genuinely new explicit standing-policy admission, never
an operational relabel of this proof.

Custody loss is not a C2 `block`, `cancel`, terminal outcome, acceptance, or
noncommit fact. A stopped process may have finished an admitted in-flight
commit. Kill issuance, timeout, expired response, or an unreachable process
does not prove noncommit. A successor cannot activate while that uncertainty
remains; this profile forbids a successor even after a completed teardown.
While custody and the original database remain positively provable, the same
incarnation may perform Coordinator-owned exact readback. Once custody is
lost, classification remains unresolved where commitment cannot be proved;
offline diagnostics cannot reactivate the proof.

## Feasibility class, trust, and entry gate

One credible mechanism class is an independently administered, conditionally
created nonreplaceable enrollment record paired with a privileged host-managed
process/storage cell. The independent record survives Coordinator rollback.
The privileged cell serializes first activation, gives only the original
guarded writer writable storage, including SQLite journal and sidecar paths,
and keeps an external active-incarnation record. Current source responses bind
that cell's live process and storage identity, not a reusable bearer secret.
Copied Coordinator bytes, credentials, or user memory cannot acquire the
original kernel-bound process identity or the cell's live relationship; a
platform that permits duplicated kernel/VM identity fails gate B. The cell
denies snapshot/restore and restart paths or irreversibly
invalidates this profile when they occur. It must observe complete process
subtree exit and storage exclusion, including writable descriptors, before
claiming a fence complete. Supervisor
failure closes current posture and cannot reopen enrollment. An unreachable
old writer never triggers automatic takeover.

Conditional immutable object retention and privileged process/hypervisor
fencing are mechanism-family feasibility evidence only, not selected products
or existing Coordinator capabilities. Protecting one object version alone
does not prevent new versions or delete markers. A supplier must rule out
those enrollment-bypass paths; retention expiry must remain protected or
fail closed. Issuing a kill is not complete fencing: actual subtree exit and
storage exclusion are required. Network credential revocation does not fence
a process that can still commit locally to SQLite.

The first profile trusts the external standing-policy root, independent
enrollment administrator, privileged enforcer, its host/storage isolation,
and the existing Coordinator guarded writer under their separately accepted
contracts. Compromise of the policy root or privileged enforcer is excluded
from this first proof. Routine database restore, clone, process restart, and
supervisor failure are not excluded attacks; they must be covered by the
mechanism. Supplier inability to prove the essential custody or fencing
properties blocks implementation entry rather than weakening this contract.

Three distinct gates remain:

1. **Contract validity (A):** finite causal histories test these target rules.
   Synthetic evidence proves only the logical contract.
2. **Concrete implementation entry (B):** before source/runtime work, an
   actual supplier must demonstrate independent enrollment custody, unique
   launch, anti-replay and nontransferability, original-state isolation,
   denial or invalidation of restore/clone/restart, complete fencing, and
   fail-closed supervisor failure. A fixture cannot satisfy this platform gate.
3. **RW0-E execution (C):** separately authorized live work on a qualified
   host, after all contract and implementation prerequisites. This document
   authorizes no external contact.

## RW0-D, RW0-E, and successor options

RW0-D1 is implemented as a bounded artificial offline proof; RW0-D2 remains future offline engineering. The offline program may repeat and reset disposable
fixtures with explicitly artificial source observations, fake transport and
model processes, and isolated temporary state. It requires no real enrollment,
grant, continuity service, production credential, network access, or
consumption of the live allowance. Such fixtures create no production
admission, acceptance, continuity, or permission. RW0-D2 still must implement validation/review/model closure and the later
RW0-C2 physical decision; this support profile grants no live runnable route.

RW0-E remains blocked until this contract is accepted, a concrete supplier
passes gate B, program-independent admission provisioning and the necessary
C2 physical/transaction/terminal contracts and implementation are ready, and
the existing qualified-host, standing-authority, custody, effect, validation,
review, and single-delivery prerequisites hold. A full-custodian or
acceptance-focused checkpoint protocol is not an RW0-E prerequisite under
this selected profile. Those are unselected successor options, with no
automatic migration from this first-live proof to either. General deployment
continuity can be decided in a later separately authorized tranche.

## Finite causal anchors

These anchors identify hand-authored contract histories, not executable
platform evidence or a new C2 reducer.

| History | Required conclusion |
| --- | --- |
| D-repeat | Repeated artificial offline runs create no live enrollment or allowance use. |
| Enroll-before-program | Authenticated lineage and non-reissuable incarnation enrollment precede activation; separate exact admission fact may be recorded before a program. |
| Lost-activation-response | Read-only reconciliation; ambiguous launch permits no second launch. |
| Copied-state | Another process or host with identical database bytes has no live incarnation authority. |
| Late-response | Old source response cannot authorize a new incarnation. |
| Nonaccept-four | Uninterrupted nonaccept progression needs fresh posture, no external checkpoint write, and no unclaimed assertion. |
| First-then-second | First acceptance may commit once; a second candidate acceptance fails the ceiling. |
| Lost-commit-response | With original custody intact, same-incarnation readback may recover the original family; timeout alone proves no noncommit. |
| Restored-preaccept | Identical preaccept bytes after restore do not restore live custody or permission. |
| Restart | Process or supervisor restart retires this profile without re-enrollment or synthetic C2 outcome. |
| In-place-restore | Database or VM-memory rollback invalidates custody even if bytes look coherent. |
| Fence-request | Issued kill without complete exit and storage exclusion cannot authorize a successor. |
| Preaccept-failure | Proof availability can end before acceptance without claiming acceptance consumed. |
| Normal-close | Normal terminal closure does not renew the enrollment. |
| ES-later | Later ES policy does not replenish direct-local allowance. |

<!-- RW0_D1_CURRENT_STATUS_BEGIN -->
RW0-D1 is a current private artificial offline process and capsule proof. The guarded Coordinator program-initialization, C2B3D author-effect, Section 41 selection, and RW0-C1 phase writers remain the sole durable owners. A separate fake planner and fake coding worker run under the bounded D1 supervisor; the parent captures one temporary candidate, builds and independently verifies a CandidateCapsuleManifestV1, removes the mutable workspace, and returns a transient typed handback with separate parent-only disposable-state custody. The preassigned fixture base_git_oid is a WorkSpec coordinate, not Git authentication. RW0-D2 validation/review/model closure is next; RW0-C2 physical decision persistence follows D2. D1 grants no live provider/credential or source authentication, ES route, Git/publication effect, terminal acceptance, public service/CLI, or RW0-E runtime authority. The detailed implementation owner is .docs/rw0-d1-offline-process-and-capsule-spine.md.
<!-- RW0_D1_CURRENT_STATUS_END -->

<!-- RW0_D2_CURRENT_STATUS_BEGIN -->
RW0-D2 now contains a bounded private offline source candidate for the two
guarded validation/review effects, checked C1 evidence, separate fake
validator/reviewer/model processes, exact nine-role input, and transient
preadmission handback. This successor updates only the earlier D2-next status.
It adds no durable post-execution Section 41 proposal family, C1 rank-15
admission, C2 decision/acceptance/terminal writer, migration 0005, live model,
ES runtime, or production adapter. External-copy validation and independent
audit remain pending. The detailed owner is
`.docs/rw0-d2-offline-evidence-and-review.md`.
<!-- RW0_D2_CURRENT_STATUS_END -->

### Native post-D2 offline successor and live gate

An artificial one-run post-D2 continuation now records Section 41 transaction A, separately admits C1 rank 15 in transaction B and invokes pure V22 after checked readback. Migration 0005 belongs to that offline Section 41 family. Earlier statements that D2 v1 has no post-execution family, rank-15 admission or 0005 remain historical for that tranche. This successor is not the first live proof: fake children and temporary process custody do not meet live gate B, supply credentials, source authentication, provider/ES route or C2 decision/acceptance requirements.

<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure current candidate

The uncommitted `artificial_offline_normal.v1` candidate adds a separate private Coordinator terminal writer on generation-2 migration 0008. It consumes checked P0, phase, Section 41 A, C1 rank-15/V22 and P1 evidence under one fenced transaction and records only the five normal outcomes: accept, repair, replan, terminal_reject and block. The P1 decision remains prior decision history; its acceptance fact is bound only for accept and is never mutated. Cancellation, live supplier/contact, ES routing, Git effects, publication and executable permission remain outside this candidate. See `.docs/rw0-terminal-outcome-physical-closure.md`.

The candidate can later supply a checked normal terminal fact. It does not pass gate B, close cancel outcomes or establish live contact/runtime. Supplier qualification may proceed separately as read-only external evidence.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_END -->

<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
## RW0 normal terminal closure local commit status

The exact cumulative independent audit accepted Git-compatible tree `4691af58ae0ee3107b4e2e9b6b1508032944e357` for an exact-byte commit gate after its current-ledger consistency repair. The private `artificial_offline_normal.v1` implementation was locally committed as `d3fd741c872b26aa2dfe927ab6dccc638cdcf356`, with sole parent `61d0330aba1160f7f5e7d9c541a325222d1c61e5`, that exact tree, and subject `feat: add RW0 normal terminal closure`. The staged-blob gate collected and passed 9,568 selector-free tests in the same order, with zero failures, errors, skips, xfails, or xpasses and only the three known Python 3.13 multithreaded-fork deprecation warnings. This is a local topic-branch commit; no push, PR, merge, publication, deployment, service/runtime contact, or product effect followed.

Migration `0008_rw0_terminal_outcome` is the current source/catalog suffix. The private fenced terminal owner records only normal `accept`, `repair`, `replan`, `terminal_reject`, and `block`. P0 scope admission, P1 progression decision with its acceptance-only fact, and terminal closure remain separate private fenced transactions and facts. P0 grants no current permission; P1 is prior decision history, not terminal truth. Normal accept binds the immutable acceptance fact without mutation or replenishment.

Common managed-store admission may shape-check the current global-stop singleton before writer fencing. After fencing and protected disclosure, receipt-present terminal read, replay, and recovery verify saved full head postimages, saved stop, and immutable P0/Section 41/C1/P1 predecessors without today's mutable-head or semantic stop checks. A fresh receipt miss retains current-head, current-stop, recording, and disclosure checks. The old whole-operation zero-current-stop-SELECT audit failure remains historical; the accepted two-layer rule supersedes only that overbroad requirement.

Git objects and refs own commit and publication truth. Audit packages, reports, validation, this status text, WA1/QtcM evidence, and provenance are evidence only. The local commit adds no executable permission, three cancel selectors, live supplier/custody gate, worker/provider or physical remote contact, ES/Bridge route, product Git-effect handler, service, queue, scheduler, deployment, or autonomous loop. Existing F03/F05 nonblocking provenance limits retain their recorded scope; this status does not claim their repair. Candidate-stage status elsewhere in this document is preserved history; this marked block is the current local status.
<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->
