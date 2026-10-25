# RW0-D2 offline evidence and cognitive review

RW0-D2 is a bounded direct-local proof continuation of RW0-D1. The D1 capsule
is the only boundary between the author effect and checking effects. The
Coordinator's existing program, author-effect, Section 41 selection, and C1
writers remain the durable owners. New native bound-effect persistence may
establish only an initial `validate_candidate` or `review_candidate` effect
family in migration 0002. Its private safe binding is an artificial assertion,
not verification of an external grant or executable permission.

## Checking child frames

The only launcher is `_rw0_d1_process_supervisor.run_fake_module`. Validator
and independent reviewer requests use distinct four-byte magics `D2V1` and
`D2R1`; each is followed by one unsigned big-endian 32-bit payload length and
one canonical UTF-8 JSON object. Canonical JSON has sorted keys, compact
separators, non-ASCII preserved, finite numbers, and no extra bytes. Duplicate,
unknown, missing, noncanonical, trailing, and multiple frames are rejected.
The complete request is at most 256 KiB; a response is at most 64 KiB.

Each request contains exactly `schema_id`, `role`, `invocation_ref`,
`command_digest`, `effect_intent_ref`, `effect_fence_ref`,
`effect_fence_digest`, `delivery_attempt_ref`, `capsule_manifest_ref`,
`portable_capsule_digest`, `requirement_ref`, `requirement_safe_digest`, and
`files`. The `files` array has exactly the three D1 paths in D1 canonical
order, with each entry containing only `path`, `length`, and `sha256` for the
candidate bytes. No blob, state root, writer, credential, or expected outcome
is sent. The child reads its own reconstructed root and refuses a hash,
length, path, mode, alias, or inventory mismatch.

Each response contains exactly `schema_id`, `role`, `invocation_ref`,
`command_digest`, `effect_fence_ref`, `effect_fence_digest`,
`delivery_attempt_ref`, `capsule_manifest_ref`, `portable_capsule_digest`,
`outcome`, `reason_code`, `source_ref`, `evidence_ref`, `observed_at`,
`file_digests`, and `record_digest`. The record digest is SHA-256 over the
literal domain `governed-execution.nwp-d2-checking-source-record.v1.identity`,
one NUL, and canonical JSON of all response fields except `record_digest`.
The source time is sampled after actual checking and before response output.

This artificial validator checks UTF-8 text, a Go `TestContract` function,
the D1 bounded candidate marker, and nonempty plan/architecture. This
artificial reviewer separately checks text for an `UNSAFE-CHANGE` marker
(failed), a `REVIEW-UNKNOWN` marker (inconclusive), and otherwise the
architecture/plan and candidate markers (passed or failed). These checks
exercise bounded source-derived outcomes; they do not compile or run supplied
code, authenticate a supplier, or confer acceptance.

## A checkpoint: checked offline evidence

`run_rw0_d2_offline(work_spec, fixture, cancelled=None)` calls the D1 offline
entry exactly once. It borrows the original D1 run while establishing two
initial bound effects through the existing fenced Coordinator writer session.
The new private `DevelopmentBoundEffectAuthorizationSafeBindingV1` is
bound-effect-only. It leaves the author-only safe-binding schema and validator
unchanged. The new command retains the exact transient capsule, requirement,
current fence and delivery, and immutable before/after bytes so the fenced
reducer and exact same-command recovery can recheck them. The operation result
uses `governed-execution.nwp-development-bound-effect-establishment-result.v1`
and is distinct from the reserved receipt result projection.

The parent closes each writer session before launching a child. It admits and
reads back 14 dependency-closed C1 members in the complete case: rank 1 x3,
rank 5 x1, rank 6 x2, rank 12 x6, rank 13 x1, and rank 14 x1. It admits the
historical D1 worker and adapter observations, worker result and process
classification; the validation/review authority and readiness; one current
qualification immediately before each corresponding child; each actual child
observation; and a fresh author authority observation at A completion. The
adapter observation retains the worker-invocation correlation checked by D1.
The reviewer-separation value is derived from exact checked C1 members and
relations. Membership readback proves persisted graph identity at that point,
not future source currentness or C2 acceptance.

`RW0D2EvidenceCheckpointV1` contains only immutable values: the D1 handback,
capture, capsule, adapter exit, two bound-effect proofs, 14 checked families,
three authority sources, readiness, two qualifications, two child outcomes and
sources, validation/review result sets and dispositions, reviewer separation,
artificial policy/risk sources and matrices, and support sets. It contains no
run owner, fixture, WorkSpec, SQLite connection, path to a live root, or second
custody mechanism. `RW0D2OfflineRun` separately owns only the original D1 run
and its disposal.

## B checkpoint: nine-role cognitive handback

After a fresh fenced read of the current phase, program/work heads, selection
head, author effect/delivery heads, and global stop, B checks the A sources'
currentness and expiry. The nine exact roles at ranks 5..13 are
`candidate_capsule`, `worker_result`, `validation_result`,
`independent_review`, `standing_policy`, `risk_lane`,
`authority_currentness_attestation`, `global_stop`, and `effect_ceiling`.
The worker result and authority role use exact checked C1 values. Other roles
carry their actual transient/source posture. The input constructor checks
V01/V02/V03/V04/V05/V06/V07/V08, then V10/V11 supply with support counts
0, 0, 6, 7, 4, 4, 0, 2, and 5. The capsule remains a single private manifest
entry; the model sees its safe projection.

The one fake review-model child uses magic `D2M1`, a four-byte unsigned payload
length, and closed canonical JSON. The request contains exactly `schema_id`,
`invocation_ref`, `input_context`, `evidence_supply`, and `input_digest`; it
contains no expected recommendation or action override. The response contains
the exact input correlations, one of five bounded recommendations, a reason,
zero to eight bounded findings, the child's completion time, and its record
digest. Its deterministic choice reads the actual supplied validation, review,
separation, policy, risk, authority, stop and ceiling values. The parent checks
the output against the exact input and normalizes it without replacing the
child's recommendation.

`PostExecutionSemanticReviewArtifactV1` has ordered fields `schema_id`,
`artifact_ref`, `proposal_ref`, `proposal_phase`, `input_context_ref`,
`capsule_manifest_ref`, `validation_disposition_ref`,
`review_disposition_ref`, `findings`, `recommendation`, `reason_code`, and
`artifact_digest`. Each finding has `finding_ref`, `source_role`,
`source_value_ref`, `source_value_digest`, and `reason_code`, bound to one of
the nine context roles. `PostExecutionSemanticReviewSafeProjectionV1` has
`schema_id`, `proposal_ref`, `proposal_phase`, `artifact_schema_id`,
`artifact_ref`, `artifact_digest`, `input_context_schema_id`,
`input_context_ref`, `input_context_digest`, `recommendation`, `reason_code`,
and `safe_projection_digest`. Each digest uses its schema plus `.identity`
domain, one NUL, and canonical content without its named self digest.

The existing common source invocation, private artifact binding, evidence
bindings/set, and historical-name proposal envelope admit the exact post phase
tuple while preserving pre-execution schema, roles, and recommendations.
`RW0D2PreadmissionHandbackV1` retains the reached proof prefix and, when
complete, the nine-role context/supply, normalized model source and artifact,
output safe projection, nine common evidence bindings/set, common proposal,
and V09 model-input binding. `preadmission_ready` means that this offline
composition has completed and cleaned its child/workspace resources. It is
not candidate acceptance, a durable Section 41 post-execution proposal family,
C1 rank-15 admission, a C2 decision input/receipt, or terminal progression.

This private source candidate is subject to external-copy validation and
independent audit; those gates are recorded separately. It invokes no live provider,
message bus, ES runtime, or direct-local production adapter.

### Later native Section 41 successor

The D2 v1 entry, handback, fake-process identities and `preadmission_ready` meaning above are preserved. An adjacent private continuation now borrows one original open D2 run and records its safe post-execution proposal family through Section 41 transaction A, then separately asks C1 for rank-15 admission and pure V22 projection. The continuation closes only its own outer run in the creator process. `.docs/section41-post-execution-proposal-family.md` owns the new bounded transaction/retention contract. Earlier statements that D2 itself adds no Section 41 writer, C1 rank-15 admission or migration 0005 remain true of the reviewed D2 v1 tranche; the additive successor supplies those three capabilities without changing D2 v1. No C2 decision or live execution follows.

### Unit 2 current checked-layout and invalid-evidence successor

The present D2 A path admits exactly the two complete Worker Wire observation
orders `worker_started, worker_completed` and `worker_started,
candidate_captured, worker_completed`. D1 parent capture and verified capsule
remain present in both. The absence of the optional worker-authored capture
observation does not negate the parent's candidate capture, and
`worker_completed` has no candidate or capsule conditional fields. The private
checked-layout resolver derives all role positions and stop prefixes from the
actual D1 result. Complete C1 checked families are 13 or 14 members with rank
sequences `(12, 12, 12, 13, 14, 1, 1, 5, 6, 12, 6, 12, 1)` and `(12, 12, 12,
12, 13, 14, 1, 1, 5, 6, 12, 6, 12, 1)`. The common tail is adapter exit,
worker result, process result, validation authority, review authority,
readiness, validation qualification, validator observation, review
qualification, reviewer observation, and author authority. V40 reviewer
separation checks the exact C1 membership/relation graph and binds candidate
identity through the parent capsule, rank-13 result, and review observation;
only the three-observation form also compares the captured observation.

After a clean reaped child, malformed closed checking evidence or a decoded
child record with an impossible canonical UTC calendar time or an unsupported
role-specific `(outcome, reason_code)` pair stops as
`validator_evidence_invalid` at `n + 7` checked members with one child, or
`reviewer_evidence_invalid` at `n + 9` with two children, where `n` is 2 or 3.
The validator pairs are `passed/validation_passed`, `failed` with one of
`validation_failed_repairable`, `validation_failed_replan_required`,
`validation_failed_terminal`, or `validation_failed_unclassified`, and
`inconclusive/validation_inconclusive`. The reviewer pairs are
`passed/review_passed`, `failed` with one of `review_failed_repair_required`,
`review_failed_replan_required`, `review_failed_terminal_reject`, or
`review_failed_unclassified`, and `inconclusive/review_inconclusive`. The
invalid observation and later child/model/native effects are not admitted.
Nonzero process exit remains a process failure; unresolved cleanup and
programming faults retain their separate paths. A stopped handback carries
only the prefix actually reached. Complete A is `n + 11`; through readiness,
validation qualification, validator observation, review qualification, and
reviewer observation are `n + 6`, `n + 7`, `n + 8`, `n + 9`, and `n + 10`.

The original three-observation command and safe-basis bytes remain compatible.
The bounded offline path still creates no C2 decision, acceptance, live worker,
provider or ES route, Git/publication effect, or autonomous loop. This
successor is implementation evidence pending independent review.

<!-- RW0_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_BEGIN -->
### Post-D2 cumulative local-commit status

The preceding pending-review sentence is historical implementation-stage
evidence, superseded only for review and local-commit status. The exact
sealed tree `3965cd3d1d3e28b43c9bc3709058c2524bad369d` was
independently reviewed for a separately governed commit gate and locally
committed as `66ee79132501e636d848ff8578fb674a208d6ac5`. The gate
reauthenticated all 299 committed blobs and Git modes and recorded 9,295
collected and 9,295 passing tests, zero failures, errors, or skips, with
three known Python 3.13 fork deprecation warnings. The two legal D2 layouts,
typed invalid-evidence stops, and original-run association above are unchanged.

The gate performed no push, PR, merge, publication, deployment, or product
effect. This is historical local-gate evidence, not a live remote-ref or
publication claim. Git objects and refs remain current commit and publication
truth. Audit, validation, provenance, reports, and status text are evidence,
not Coordinator durable authority or effect permission. The artifact-only
audit did not certify live Git, and the gate proves only its prospective
opening-to-commit interval; earlier raw-index and diagnostic-ref gaps remain
unresolved. F03 remains a nonblocking private-constructor observation; F2,
qualified F3/F6/F7, cross-host clock ordering, and live concerns remain open.

This proof adds no live custody, physical C2 decision or acceptance, terminal
outcome, executable permission, production provider or worker readiness, ES
or Bridge route, product Git authority, service, scheduler, or autonomous loop.
<!-- RW0_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_END -->
