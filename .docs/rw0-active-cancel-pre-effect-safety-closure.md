# RW0 active-cancel pre-effect safety closure

Classification: `CURRENT UNCOMMITTED IMPLEMENTATION CANDIDATE` on baseline commit
`6931ae92126abaf89a75dcf0eb3781f23b4a9363`, tree
`1aea0d26cdb578267eed2c0d850c3beef40f81e1`. This document owns the
candidate physical slice; the integrated migration-0009 status is its
predecessor. Independent read-only audit remains required.

## Authority and scope

The private artificial-offline path records one generic C2B
`cancel/effect_cancellation` decision. It is a pre-effect progression fact and
does not establish a cancellation effect. A distinct
`rw0_cancel_decision_receipts` row binds exact command bytes, a result digest,
current target effect and delivery head revisions, digests, and complete safe
postimages. The closed evidence-binding family uses exactly four roles for an
author target, plus `cancel_target_capsule` for validation and review targets.
The source directive and evidence roles contain only safe refs and digests.
The receipt's program-version coordinates are the current basis, not a newly
created version.

The `rw0_terminal_anchors` registry remains the sole cross-profile phase
route. Its selected complete family owns terminal meaning. The new
`artificial_offline_cancel_pre_effect_block.v1` family owns only one
`pre_effect_cancel_basis_unusable` `block` outcome. It binds the original
cancel decision and receipt, the exact mismatch, and closure witnesses.
There is no replacement generic block decision or second phase-unique route.
Normal P1 remains the prior five-branch reducer.

No authenticated current external source is implemented. Stored source
evidence, authority-evidence bytes, model output, reports, and missing
verifier output provide no external permission. The private
`external_source_available` input is an artificial caller-supplied diagnostic
boolean, not source detection or authentication. Its default is `True`:
equal local facts produce `locally_current_source_unverified` for the default
or explicit `True`, and `external_source_unresolved` for `False`. Neither
classification is effect eligibility or executable authority. This input does
not create or erase a proven local mismatch. A future authenticated
source-owned mismatch needs a separate contract.

## Durable schema

Migration `0010_rw0_active_cancel_pre_effect_safety_closure` is sequence 10,
application generation 2, compatibility `[2,2]`, and non-destructive. It adds
six STRICT tables: decision evidence bindings, decision receipts, terminal
contexts, terminal outcomes, terminal results, and terminal receipts. There
are twelve new immutability triggers. Migration 0010 replaces only the
anchor family-admission trigger with an unchanged normal arm and a cancel arm;
the normal receipt registration trigger remains unchanged. The new cancel
receipt trigger inserts the exact 21-column anchor and aborts unless that
anchor is present. Migration 0008 and 0009 SQL resources are byte-unchanged.
The expected cumulative physical inventory is 85 tables, 159 triggers, five
explicit indexes, 1,921 columns, and 262 foreign keys. Fresh install leaves
all six new tables empty; an exact 0009 prefix requires explicit migration.
An old binary refuses the 0010 tip.

The sequence-9 administrative verifier remains normal-only for historical
0009 verification. The sequence-10 verifier requires one exact anchor for
each complete normal or cancel family and rejects extra, partial, aliased,
contradictory, or unsupported families. For a populated cancel terminal family,
it also parses the saved terminal command, reconstructs its exact four-row
plan, and checks the original saved cancel command, generic decision, receipt,
and complete evidence bindings. These are historical persisted-witness checks;
the verifier does not reinterpret current heads, stop, or external source
authority. A decision-only state is valid. It runs before migration commit
and in migration commit-uncertainty readback.

## Guarded decision path

The closed private command validates before mutation-slot acquisition. The
writer uses the existing operation lease, common lock, `BEGIN IMMEDIATE`,
writer fencing, nominal read capability, and one commit attempt. It looks up
the decision receipt before other family detail. A complete same-command
family replays its saved historical result. Reuse of a mutation ref with a
different canonical command conflicts. Fresh record validates all matching
receipt, decision, binding, phase, preassignment, and route aliases before
classifying replay, conflict, or absence; an orphan matching alias is integrity
failure. It requires the phase to have no terminal anchor. It checks the
persisted immutable basis and current Coordinator-owned program, attempt,
effect, delivery, fence, and stop facts. The immutable check joins the selected
phase to its semantic attempt, attempt fence, program/version basis, target
intent, fence, delivery, and stage-specific author/candidate/capsule lineage.
A target from another attempt or version is invalid lineage, even if its own
rows and foreign keys are valid. The current program-head version may be later
than the phase's immutable version; it is checked separately as the decision's
current basis. The writer then inserts exactly one generic decision, its
role-complete bindings, and its receipt. It reads back the complete family
before capability invalidation and one commit attempt. The shared commit-close
witness marks the real commit-attempt boundary. A fresh committed result
requires complete commit and connection-close proof; uncertainty after commit
starts returns `commit_outcome_unknown`, including outer required cleanup
failure. A fresh fenced recovery returns only
`committed_exact`, `definitely_not_committed`, or `unresolved` after exact
family and alias readback. No writer retry is inferred from uncertainty.

## Separate currentness verifier

After exact decision readback, a distinct guarded read transaction rechecks
the decision receipt and role-complete bindings, terminal route, immutable
phase and target predecessors, current program/version and attempt, target
effect and delivery heads, persisted fences, preassignments, global stop, and
available repository/base/path coordinates. Its closed classifications are
`locally_current_source_unverified`, `proven_coordinator_mismatch`,
`external_source_unresolved`, `integrity_failure`,
`occupied_terminal_phase`, and `commit_or_readback_unresolved`.

A proven mismatch is an exact difference in mutable Coordinator-owned facts.
A missing required immutable predecessor is corruption, not a mismatch. An
optional not-yet-created cancellation effect, fence, or delivery is the
expected pre-effect state. A complete competing terminal family occupies the
phase; an incomplete or malformed family is corruption or unresolved
recovery. Missing external evidence is unresolved, never a proven unusable
basis. Local equality is source-unverified even when saved evidence bindings
are present.

## Cancel-bound block

The terminal command binds the original cancel decision and receipt, the
exact typed mismatch class/ref/digest, saved closure heads and stop, safe
verification bytes, and command identity. After fencing, the terminal writer
validates any registered family and all declared context, outcome, result,
receipt, and anchor aliases before occupied-phase or replay classification.
An orphan alias cannot be hidden by a complete normal-phase winner.
Same-command replay checks
saved historical witnesses and immutable predecessors without rereading
later mutable heads or stop. Fresh record reconstructs the original complete
cancel family, then rereads current Coordinator-owned facts in its own write
transaction. It requires the **same** mismatch class/ref/digest and complete
closure head and stop bytes still to be proven. It inserts context, outcome,
result, and receipt in that order. The receipt trigger registers the phase
anchor in the same transaction. The writer verifies all four rows and exact
anchor before one commit attempt and requires the same complete commit-close
proof as the decision path. Recovery uses exact guarded three-way
readback; it authorizes no effect, request, or second family.

## Exclusions and remaining boundaries

This candidate has no cancellation effect or fence creation, delivery,
request, acknowledgement, signal, process exit, teardown, custody, terminal
`cancel`, source-native reconciliation, successor launch, Git effect,
publication, deployment, pause/resume, live source/provider/worker, ES, CP,
Bridge, Temporal, service, queue, scheduler, or autonomous loop. There is no
public StateStore or package-root route. Validation and provenance are
evidence only; Git objects and refs own commit and publication truth.
