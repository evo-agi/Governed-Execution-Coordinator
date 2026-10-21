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
