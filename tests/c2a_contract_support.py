"""Non-collected test-only support for the C2A semantic contract.

This module contains parsing, canonicalization, deterministic fixture construction,
strict validators, and explicitly named canonical convenience wrappers. It is not
semantic authority, runtime truth, acceptance, authorization, or program state.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]


DOC_PATH = ROOT / ".docs/c2a-first-slice-semantic-protocol-contract.md"


DOC = DOC_PATH.read_text(encoding="utf-8")


AUTHORITY_DOC_PATH = ROOT / ".docs/authority-boundaries.md"


AUTHORITY_DOC = AUTHORITY_DOC_PATH.read_text(encoding="utf-8")


CLAUSES = (
    ("C2A-PROTO-001", "Status, Classification, Layering, And Non-Implementation", "PROCESS-ONLY GOVERNANCE", "any source"),
    ("C2A-PROTO-002", "Identity Non-Collapse And One-Writer, Source, Recorder, And Custody Roles", "ACCEPTED STRATEGIC TARGET", "any source"),
    ("C2A-PROTO-003", "Closed Semantic Schemas, Canonical Encoding, And Digest Domains", "FUTURE IMPLEMENTATION DETAIL", "any source"),
    ("C2A-PROTO-004", "Private Work Specification, Worker Command, And Delivery Envelope", "FUTURE IMPLEMENTATION DETAIL", "any source"),
    ("C2A-PROTO-005", "Standing-Authority Bindings, Attempt And Effect Fences, Global Stop, And Cancellation", "ACCEPTED STRATEGIC TARGET", "any source"),
    ("C2A-PROTO-006", "Finite Source Observations And Coordinator Ingest Dispositions", "FUTURE IMPLEMENTATION DETAIL", "any source"),
    ("C2A-PROTO-007", "Replay, Duplicate, Late, Stale, Ambiguous, And Unknown-Outcome Semantics", "FUTURE IMPLEMENTATION DETAIL", "any source"),
    ("C2A-PROTO-008", "Candidate Capsule Manifest, Portable Digest, Custody, And Retrieval", "FUTURE IMPLEMENTATION DETAIL", "any source"),
    ("C2A-PROTO-009", "Validation, Independent Review, Model Proposal, And Coordinator Decision", "ACCEPTED STRATEGIC TARGET", "any source"),
    ("C2A-PROTO-010", "Separate First-Slice Git Effect", "ACCEPTED STRATEGIC TARGET", "any source"),
    ("C2A-PROTO-011", "Direct-Local And ES Semantic Conformance", "ACCEPTED STRATEGIC TARGET", "any source"),
    ("C2A-PROTO-012", "Process, Release, Terminal Receipt, And Credential Gates", "FUTURE IMPLEMENTATION DETAIL", "external process launch"),
    ("C2A-PROTO-013", "Privacy, Redaction, And Artifact Placement", "ACCEPTED STRATEGIC TARGET", "any source"),
    ("C2A-PROTO-014", "Mechanical Direct-Local Bootstrap Stop Conditions", "ACCEPTED STRATEGIC TARGET", "any source"),
    ("C2A-PROTO-015", "Tranche Gates, No-Schema Posture, And Deferred Mechanics", "FUTURE IMPLEMENTATION DETAIL", "durable schema change"),
)


SCHEMA_ROWS = (
    ("1", "`governed-execution.nwp-work-spec.v1`", "`WorkSpecV1`", "`governed-execution.nwp-work-spec.v1.identity`"),
    ("2", "`governed-execution.nwp-attempt-fence.v1`", "`AttemptFenceV1`", "`governed-execution.nwp-attempt-fence.v1.identity`"),
    ("3", "`governed-execution.nwp-effect-fence.v1`", "`EffectFenceV1`", "`governed-execution.nwp-effect-fence.v1.identity`"),
    ("4", "`governed-execution.nwp-worker-command.v1`", "`WorkerCommandV1`", "`governed-execution.nwp-worker-command.v1.identity`"),
    ("5", "`governed-execution.nwp-delivery-envelope.v1`", "`DeliveryEnvelopeV1`", "`governed-execution.nwp-delivery-envelope.v1.identity`"),
    ("6", "`governed-execution.nwp-worker-observation.v1`", "`WorkerObservationV1`", "`governed-execution.nwp-worker-observation.v1.identity`"),
    ("7", "`governed-execution.nwp-candidate-capsule-manifest.v1`", "`CandidateCapsuleManifestV1`", "`governed-execution.nwp-candidate-capsule-manifest.v1.identity`"),
)


IDENTITIES = (
    "program_ref",
    "program_version_ref",
    "accepted_intent_revision_ref",
    "work_item_ref",
    "work_item_revision_ref",
    "semantic_attempt_ref",
    "effect_intent_ref",
    "delivery_attempt_ref",
    "source_invocation_ref",
    "observation_ref",
    "candidate_ref",
    "capsule_manifest_ref",
    "portable_capsule_digest",
    "validation_observation_ref",
    "independent_review_ref",
    "model_proposal_ref",
    "coordinator_decision_ref",
    "git_effect_intent_ref",
)


NON_EQUIVALENCES = (
    "program version != accepted-intent revision;",
    "accepted-intent revision != work-item revision;",
    "work-item revision != base Git OID;",
    "semantic attempt != effect intent;",
    "effect intent != delivery attempt;",
    "delivery attempt != source invocation;",
    "observation != candidate;",
    "candidate != capsule manifest;",
    "capsule manifest != portable digest;",
    "validation observation != independent review;",
    "independent review != model proposal;",
    "model proposal != Coordinator decision;",
    "Coordinator acceptance != Git effect intent;",
    "Git effect intent != commit OID; and",
    "commit OID != publication state.",
)


CEILING_FIELDS = (
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
    "max_wall_seconds",
)


def _rows(spec: str) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(cell.strip() for cell in line.split("|")) for line in spec.strip().splitlines())


FIELD_ROWS = {
    "WorkSpecV1 fields": _rows(
        """
1|`schema_id`|yes|`governed-execution.nwp-work-spec.v1`|identity|yes
2|`work_spec_ref`|yes|safe ref|identity|yes
3|`program_ref`|yes|safe ref|correlation|yes
4|`program_version_ref`|yes|safe ref|correlation|yes
5|`accepted_intent_revision_ref`|yes|safe ref|correlation|yes
6|`work_item_ref`|yes|safe ref|correlation|yes
7|`work_item_revision_ref`|yes|safe ref|correlation|yes
8|`repository_ref`|yes|safe ref|effect ceiling|yes
9|`base_git_object_format`|yes|`sha1`|evidence|yes
10|`base_git_oid`|yes|40 lowercase hex|evidence|yes
11|`authorized_paths`|yes|sorted unique safe-path array|effect ceiling|yes
12|`objective`|yes|bounded private string|evidence|yes
13|`requirements`|yes|ordered non-empty private-string array|evidence|yes
14|`exclusions`|yes|ordered non-empty private-string array|effect ceiling|yes
15|`validation_requirement_ref`|yes|safe ref|safe reference|yes
16|`review_requirement_ref`|yes|safe ref|safe reference|yes
17|`privacy_classification`|yes|`private_work_spec`|privacy classification|yes
18|`work_spec_digest`|yes|SHA-256|evidence|no
"""
    ),
    "AttemptFenceV1 fields": _rows(
        """
1|`schema_id`|yes|`governed-execution.nwp-attempt-fence.v1`|identity|yes
2|`attempt_fence_ref`|yes|safe ref|identity|yes
3|`parent_standing_grant_ref`|yes|safe ref|authority-sensitive binding|yes
4|`parent_standing_grant_digest`|yes|SHA-256|authority-sensitive binding|yes
5|`attempt_authorization_ref`|yes|safe ref|authority-sensitive binding|yes
6|`attempt_authorization_digest`|yes|SHA-256|authority-sensitive binding|yes
7|`program_ref`|yes|safe ref|correlation|yes
8|`program_version_ref`|yes|safe ref|correlation|yes
9|`accepted_intent_revision_ref`|yes|safe ref|correlation|yes
10|`work_item_ref`|yes|safe ref|correlation|yes
11|`work_item_revision_ref`|yes|safe ref|correlation|yes
12|`semantic_attempt_ref`|yes|safe ref|identity|yes
13|`repository_ref`|yes|safe ref|effect ceiling|yes
14|`base_git_object_format`|yes|`sha1`|evidence|yes
15|`base_git_oid`|yes|40 lowercase hex|evidence|yes
16|`path_ceiling`|yes|sorted unique safe-path array|effect ceiling|yes
17|`allowed_effect_classes`|yes|sorted subset of `author_candidate`, `validate_candidate`, `review_candidate`, `cancel_effect`, `local_git_commit`|effect ceiling|yes
18|`aggregate_ceilings`|yes|exact `CeilingsV1` object|effect ceiling|yes
19|`expires_at`|yes|whole-second UTC|authority-sensitive binding|yes
20|`global_stop_ref`|yes|safe ref|authority-sensitive binding|yes
21|`global_stop_version`|yes|non-negative integer|authority-sensitive binding|yes
22|`attempt_fence_digest`|yes|SHA-256|evidence|no
"""
    ),
    "EffectFenceV1 fields": _rows(
        """
1|`schema_id`|yes|`governed-execution.nwp-effect-fence.v1`|identity|yes
2|`effect_fence_ref`|yes|safe ref|identity|yes
3|`parent_standing_grant_ref`|yes|safe ref|authority-sensitive binding|yes
4|`parent_standing_grant_digest`|yes|SHA-256|authority-sensitive binding|yes
5|`effect_authorization_ref`|yes|safe ref|authority-sensitive binding|yes
6|`effect_authorization_digest`|yes|SHA-256|authority-sensitive binding|yes
7|`attempt_fence_ref`|yes|safe ref|authority-sensitive binding|yes
8|`attempt_fence_digest`|yes|SHA-256|authority-sensitive binding|yes
9|`program_ref`|yes|safe ref|correlation|yes
10|`program_version_ref`|yes|safe ref|correlation|yes
11|`accepted_intent_revision_ref`|yes|safe ref|correlation|yes
12|`work_item_ref`|yes|safe ref|correlation|yes
13|`work_item_revision_ref`|yes|safe ref|correlation|yes
14|`semantic_attempt_ref`|yes|safe ref|correlation|yes
15|`effect_intent_ref`|yes|safe ref|identity|yes
16|`effect_class`|yes|`author_candidate`, `validate_candidate`, `review_candidate`, `cancel_effect`, or `local_git_commit`|effect ceiling|yes
17|`command_ref`|yes|safe ref|correlation|yes
18|`command_digest`|yes|SHA-256|authority-sensitive binding|yes
19|`candidate_ref`|yes|safe ref|correlation|yes
20|`repository_ref`|yes|safe ref|effect ceiling|yes
21|`base_git_object_format`|yes|`sha1`|evidence|yes
22|`base_git_oid`|yes|40 lowercase hex|evidence|yes
23|`path_ceiling`|yes|sorted unique safe-path array|effect ceiling|yes
24|`effect_ceilings`|yes|exact `CeilingsV1` object|effect ceiling|yes
25|`expires_at`|yes|whole-second UTC|authority-sensitive binding|yes
26|`global_stop_ref`|yes|safe ref|authority-sensitive binding|yes
27|`global_stop_version`|yes|non-negative integer|authority-sensitive binding|yes
28|`portable_capsule_digest`|yes|SHA-256 or JSON `null`|authority-sensitive binding|yes
29|`cancellation_target_effect_intent_ref`|yes|safe ref or JSON `null`|authority-sensitive binding|yes
30|`cancellation_target_effect_fence_ref`|yes|safe ref or JSON `null`|authority-sensitive binding|yes
31|`cancellation_target_effect_fence_digest`|yes|SHA-256 or JSON `null`|authority-sensitive binding|yes
32|`effect_fence_digest`|yes|SHA-256|evidence|no
"""
    ),
}


FIELD_ROWS.update(
    {
        "WorkerCommandV1 fields": _rows(
            """
1|`schema_id`|yes|`governed-execution.nwp-worker-command.v1`|identity|yes
2|`command_ref`|yes|safe ref|identity|yes
3|`program_ref`|yes|safe ref|correlation|yes
4|`program_version_ref`|yes|safe ref|correlation|yes
5|`accepted_intent_revision_ref`|yes|safe ref|correlation|yes
6|`work_item_ref`|yes|safe ref|correlation|yes
7|`work_item_revision_ref`|yes|safe ref|correlation|yes
8|`semantic_attempt_ref`|yes|safe ref|correlation|yes
9|`effect_intent_ref`|yes|safe ref|correlation|yes
10|`effect_class`|yes|`author_candidate`|effect ceiling|yes
11|`candidate_ref`|yes|safe ref|identity|yes
12|`repository_ref`|yes|safe ref|effect ceiling|yes
13|`base_git_object_format`|yes|`sha1`|evidence|yes
14|`base_git_oid`|yes|40 lowercase hex|evidence|yes
15|`path_ceiling`|yes|sorted unique safe-path array|effect ceiling|yes
16|`work_spec_ref`|yes|safe ref|safe reference|yes
17|`work_spec_digest`|yes|SHA-256|evidence|yes
18|`standing_grant_ref`|yes|safe ref|authority-sensitive binding|yes
19|`standing_grant_digest`|yes|SHA-256|authority-sensitive binding|yes
20|`attempt_authorization_ref`|yes|safe ref|authority-sensitive binding|yes
21|`attempt_authorization_digest`|yes|SHA-256|authority-sensitive binding|yes
22|`effect_authorization_ref`|yes|safe ref|authority-sensitive binding|yes
23|`effect_authorization_digest`|yes|SHA-256|authority-sensitive binding|yes
24|`attempt_fence_ref`|yes|safe ref|authority-sensitive binding|yes
25|`attempt_fence_digest`|yes|SHA-256|authority-sensitive binding|yes
26|`effect_fence_ref`|yes|safe ref|authority-sensitive binding|yes
27|`effect_fence_digest`|yes|SHA-256|authority-sensitive binding|no
28|`global_stop_ref`|yes|safe ref|authority-sensitive binding|yes
29|`global_stop_version`|yes|non-negative integer|authority-sensitive binding|yes
30|`validation_requirement_ref`|yes|safe ref|safe reference|yes
31|`validation_requirement_digest`|yes|SHA-256|evidence|yes
32|`review_requirement_ref`|yes|safe ref|safe reference|yes
33|`review_requirement_digest`|yes|SHA-256|evidence|yes
34|`capsule_schema_id`|yes|`governed-execution.nwp-candidate-capsule-manifest.v1`|correlation|yes
35|`capsule_profile_ref`|yes|safe ref|safe reference|yes
36|`effect_ceilings`|yes|exact `CeilingsV1` object|effect ceiling|yes
37|`privacy_classification`|yes|`private_source_change`|privacy classification|yes
38|`redaction_profile_ref`|yes|safe ref|privacy classification|yes
39|`command_digest`|yes|SHA-256|evidence|no
"""
        ),
        "DeliveryEnvelopeV1 fields": _rows(
            """
1|`schema_id`|yes|`governed-execution.nwp-delivery-envelope.v1`|identity|yes
2|`delivery_attempt_ref`|yes|safe ref|identity|yes
3|`program_ref`|yes|safe ref|correlation|yes
4|`program_version_ref`|yes|safe ref|correlation|yes
5|`command_ref`|yes|safe ref|originating author-command lineage|yes
6|`command_digest`|yes|SHA-256|originating author-command lineage|yes
7|`semantic_attempt_ref`|yes|safe ref|originating semantic attempt|yes
8|`effect_intent_ref`|yes|safe ref|current effect intent|yes
9|`attempt_fence_ref`|yes|safe ref|originating attempt-fence binding|yes
10|`attempt_fence_digest`|yes|SHA-256|originating attempt-fence binding|yes
11|`effect_fence_ref`|yes|safe ref|current effect-fence binding|yes
12|`effect_fence_digest`|yes|SHA-256|current effect-fence binding|yes
13|`adapter_kind`|yes|`direct_local_bootstrap` or `execution_substrate`|correlation|yes
14|`adapter_safe_correlation_ref`|yes|safe ref|correlation|yes
15|`delivery_envelope_digest`|yes|SHA-256|evidence|no
"""
        ),
        "WorkerObservationV1 fields": _rows(
            """
1|`schema_id`|yes|`governed-execution.nwp-worker-observation.v1`|identity|yes
2|`observation_ref`|yes|safe ref|identity|yes
3|`source_kind`|yes|source-kind matrix value|evidence|yes
4|`source_ref`|yes|safe ref|safe reference|yes
5|`source_invocation_ref`|yes|safe ref|correlation|yes
6|`delivery_attempt_ref`|yes|safe ref|correlation|yes
7|`program_ref`|yes|safe ref|correlation|yes
8|`program_version_ref`|yes|safe ref|correlation|yes
9|`accepted_intent_revision_ref`|yes|safe ref|correlation|yes
10|`work_item_ref`|yes|safe ref|correlation|yes
11|`work_item_revision_ref`|yes|safe ref|correlation|yes
12|`semantic_attempt_ref`|yes|safe ref|correlation|yes
13|`effect_intent_ref`|yes|safe ref|correlation|yes
14|`command_ref`|yes|safe ref|correlation|yes
15|`command_digest`|yes|SHA-256|evidence|yes
16|`attempt_fence_ref`|yes|safe ref|authority-sensitive binding|yes
17|`attempt_fence_digest`|yes|SHA-256|authority-sensitive binding|yes
18|`effect_fence_ref`|yes|safe ref|authority-sensitive binding|yes
19|`effect_fence_digest`|yes|SHA-256|authority-sensitive binding|yes
20|`observation_kind`|yes|source/observation matrix value|evidence|yes
21|`outcome`|yes|source/observation matrix value|evidence|yes
22|`reason_code`|yes|bounded finite reason code|evidence|yes
23|`evidence_refs`|yes|sorted unique safe-ref array|evidence|yes
24|`observed_at`|yes|whole-second UTC source timestamp|evidence|yes
25|`candidate_ref`|conditional|safe ref|correlation|yes when present
26|`capsule_manifest_ref`|conditional|safe ref|safe reference|yes when present
27|`portable_capsule_digest`|conditional|SHA-256|evidence|yes when present
28|`process_exit_code`|conditional|integer from -255 through 255, boolean rejected|evidence|yes when present
29|`observation_digest`|yes|SHA-256|evidence|no
"""
        ),
        "CandidateCapsuleManifestV1 fields": _rows(
            """
1|`schema_id`|yes|`governed-execution.nwp-candidate-capsule-manifest.v1`|identity|yes
2|`canonicalization_profile`|yes|`canonical-json.sorted-keys.utf8.v1`|evidence|yes
3|`digest_domain`|yes|manifest digest domain|evidence|yes
4|`candidate_ref`|yes|safe ref|identity|yes
5|`capsule_manifest_ref`|yes|safe ref|identity|yes
6|`program_ref`|yes|safe ref|correlation|yes
7|`program_version_ref`|yes|safe ref|correlation|yes
8|`accepted_intent_revision_ref`|yes|safe ref|correlation|yes
9|`work_item_ref`|yes|safe ref|correlation|yes
10|`work_item_revision_ref`|yes|safe ref|correlation|yes
11|`semantic_attempt_ref`|yes|safe ref|correlation|yes
12|`effect_intent_ref`|yes|safe ref|correlation|yes
13|`command_ref`|yes|safe ref|correlation|yes
14|`command_digest`|yes|SHA-256|evidence|yes
15|`attempt_fence_ref`|yes|safe ref|authority-sensitive binding|yes
16|`attempt_fence_digest`|yes|SHA-256|authority-sensitive binding|yes
17|`effect_fence_ref`|yes|safe ref|authority-sensitive binding|yes
18|`effect_fence_digest`|yes|SHA-256|authority-sensitive binding|yes
19|`repository_ref`|yes|safe ref|effect ceiling|yes
20|`base_git_object_format`|yes|`sha1`|evidence|yes
21|`base_git_oid`|yes|40 lowercase hex|evidence|yes
22|`authorized_path_scope_digest`|yes|domain-separated SHA-256|effect ceiling|yes
23|`entries`|yes|sorted non-empty `CapsuleEntryV1` array|evidence|yes
24|`portable_capsule_digest`|yes|SHA-256|evidence|no
"""
        ),
    }
)


CAPSULE_ENTRY_ROWS = _rows(
    """
1|`path`|first-slice authorized safe relative path
2|`operation`|`replace_regular_file`
3|`mode`|`100644` or `100755`
4|`before_blob_sha256`|SHA-256
5|`before_byte_length`|non-negative integer
6|`after_blob_sha256`|SHA-256
7|`after_byte_length`|non-negative integer
"""
)


SOURCE_KINDS = (
    "direct_local_adapter",
    "es_adapter",
    "worker",
    "capsule_builder",
    "validator",
    "independent_reviewer",
    "workspace_custodian",
    "capsule_store",
)


MANIFEST_SCHEMA_ID = "governed-execution.nwp-candidate-capsule-manifest.v1"


MANIFEST_CANONICALIZATION_PROFILE = "canonical-json.sorted-keys.utf8.v1"


MANIFEST_DIGEST_DOMAIN = "governed-execution.nwp-candidate-capsule-manifest.v1.identity"


_UNSET = object()


class _RelatedRecordDictSubclass(dict):
    pass


class _RelatedRecordListSubclass(list):
    pass


class _RelatedRecordMappingLike:
    def get(self, key: object, default: object = None) -> object:
        return default


EFFECT_CLASSES = frozenset(
    ("author_candidate", "cancel_effect", "local_git_commit", "review_candidate", "validate_candidate")
)


CANCELLATION_TARGET_CLASSES = frozenset(("author_candidate", "validate_candidate", "review_candidate"))


ADAPTER_AUTHORED_OBSERVATIONS = frozenset(
    (
        "delivery_acknowledged",
        "delivery_rejected",
        "delivery_outcome_unknown",
        "cancellation_acknowledged",
        "cancellation_rejected",
        "process_exited",
        "deadline_elapsed",
    )
)


SOURCE_KIND_BY_ADAPTER = {
    "direct_local_bootstrap": "direct_local_adapter",
    "execution_substrate": "es_adapter",
}


OBSERVATION_ROWS = _rows(
    """
1|`delivery_acknowledged`|`direct_local_adapter` / `es_adapter`|`acknowledged`|none
2|`delivery_rejected`|`direct_local_adapter` / `es_adapter`|`rejected`|none
3|`worker_started`|`worker`|`started`|none
4|`worker_completed`|`worker`|`completed`|none
5|`candidate_captured`|`worker`|`captured`|candidate
6|`capsule_sealed`|`capsule_builder`|`sealed`|capsule
7|`capsule_seal_failed`|`capsule_builder`|`failed`|candidate
8|`validation_completed`|`validator`|`passed` / `failed` / `inconclusive` / `not_run`|capsule
9|`independent_review_completed`|`independent_reviewer`|`passed` / `failed` / `inconclusive`|capsule
10|`cancellation_acknowledged`|`direct_local_adapter` / `es_adapter`|`acknowledged`|none
11|`cancellation_rejected`|`direct_local_adapter` / `es_adapter`|`rejected`|none
12|`process_exited`|`direct_local_adapter` / `es_adapter`|`exited`|exit
13|`deadline_elapsed`|`direct_local_adapter` / `es_adapter`|`elapsed`|none
14|`delivery_outcome_unknown`|`direct_local_adapter` / `es_adapter`|`unknown`|none
15|`workspace_teardown_succeeded`|`workspace_custodian`|`succeeded`|capsule
16|`workspace_teardown_failed`|`workspace_custodian`|`failed`|capsule
17|`capsule_retrieval_succeeded`|`capsule_store`|`succeeded`|capsule
18|`capsule_retrieval_failed`|`capsule_store`|`failed`|capsule
"""
)


INGEST_ROWS = _rows(
    """
1|`duplicate_exact`|same `observation_ref` already exists with the same `observation_digest`|no second fact or progression action
2|`conflict_quarantined`|same `observation_ref` already exists with a different digest|quarantine both identity claims; no progression
3|`ambiguous_quarantined`|no prior ref exists, but there is no unique immutable attempt/effect/command/delivery/fence/source binding, the binding is contradictory, or source-owner evidence cannot distinguish late from stale|quarantine; no progression or blind retry
4|`stale_retained`|no prior ref exists and source-owner evidence proves the fact was authored after its bound program/work/authority/fence became stale, expired, or revoked|retain as evidence; cannot advance progression
5|`late_retained`|no prior ref exists, exact historical binding is known, the fact was authored while that binding was valid, and ingestion occurs after the effect became terminal or superseded|retain against the original effect; never apply to a newer attempt
6|`recorded`|no prior ref exists and the exact binding is current with no earlier condition|retain as evidence; evaluate separately
"""
)


OWNER_AUTHOR_ROWS = _rows(
    """
delivery acknowledged/rejected/unknown|direct-local delivery supervisor or ES submit/recovery owner|`direct_local_adapter` or `es_adapter`|the selected route only
worker started/completed and candidate captured|worker process|`worker`|direct-local or ES route
capsule sealed/seal failed|capsule builder|`capsule_builder`|direct-local or ES route
validation completed|validator/test runtime|`validator`|direct-local or ES route
independent review completed|independent reviewer|`independent_reviewer`|direct-local or ES route
cancellation acknowledged/rejected|direct-local supervisor or ES cancellation/lifecycle owner|`direct_local_adapter` or `es_adapter`|selected route
process exit/deadline|OS/supervisor for direct-local or ES lifecycle owner|`direct_local_adapter` or `es_adapter`|selected route
workspace teardown|workspace custodian|`workspace_custodian`|selected route
capsule retrieval|capsule store|`capsule_store`|selected route
"""
)


EFFECT_RELATION_ROWS = _rows(
    """
`delivery_acknowledged`|`author_candidate`, `validate_candidate`, `review_candidate`, or `cancel_effect`
`delivery_rejected`|`author_candidate`, `validate_candidate`, `review_candidate`, or `cancel_effect`
`worker_started`|`author_candidate` only
`worker_completed`|`author_candidate` only
`candidate_captured`|`author_candidate` only
`capsule_sealed`|`author_candidate` only
`capsule_seal_failed`|`author_candidate` only
`validation_completed`|`validate_candidate` only
`independent_review_completed`|`review_candidate` only
`cancellation_acknowledged`|`cancel_effect` only
`cancellation_rejected`|`cancel_effect` only
`process_exited`|`author_candidate`, `validate_candidate`, `review_candidate`, or `cancel_effect`
`deadline_elapsed`|`author_candidate`, `validate_candidate`, `review_candidate`, or `cancel_effect`
`delivery_outcome_unknown`|`author_candidate`, `validate_candidate`, `review_candidate`, or `cancel_effect`
`workspace_teardown_succeeded`|`author_candidate` or `cancel_effect`
`workspace_teardown_failed`|`author_candidate` or `cancel_effect`
`capsule_retrieval_succeeded`|`validate_candidate` or `review_candidate`
`capsule_retrieval_failed`|`validate_candidate` or `review_candidate`
"""
)


EFFECT_CLASSES_BY_OBSERVATION = {
    "delivery_acknowledged": frozenset(("author_candidate", "validate_candidate", "review_candidate", "cancel_effect")),
    "delivery_rejected": frozenset(("author_candidate", "validate_candidate", "review_candidate", "cancel_effect")),
    "worker_started": frozenset(("author_candidate",)),
    "worker_completed": frozenset(("author_candidate",)),
    "candidate_captured": frozenset(("author_candidate",)),
    "capsule_sealed": frozenset(("author_candidate",)),
    "capsule_seal_failed": frozenset(("author_candidate",)),
    "validation_completed": frozenset(("validate_candidate",)),
    "independent_review_completed": frozenset(("review_candidate",)),
    "cancellation_acknowledged": frozenset(("cancel_effect",)),
    "cancellation_rejected": frozenset(("cancel_effect",)),
    "process_exited": frozenset(("author_candidate", "validate_candidate", "review_candidate", "cancel_effect")),
    "deadline_elapsed": frozenset(("author_candidate", "validate_candidate", "review_candidate", "cancel_effect")),
    "delivery_outcome_unknown": frozenset(("author_candidate", "validate_candidate", "review_candidate", "cancel_effect")),
    "workspace_teardown_succeeded": frozenset(("author_candidate", "cancel_effect")),
    "workspace_teardown_failed": frozenset(("author_candidate", "cancel_effect")),
    "capsule_retrieval_succeeded": frozenset(("validate_candidate", "review_candidate")),
    "capsule_retrieval_failed": frozenset(("validate_candidate", "review_candidate")),
}


AUTHORIZED_PATHS = (
    ".docs/system_overview/hybrid_integration_architecture_adr.md",
    "PLANS.md",
    "docs_contract_test.go",
)


GIT_CEILINGS = {
    "max_local_commits": 1,
    "max_pushes": 0,
    "max_pull_requests": 0,
    "max_merges": 0,
    "max_deployments": 0,
}


ONE_WRITER_ROWS = _rows(
    """
Standing grant, expiry, or revocation|external standing-policy authority|external authority; Coordinator may record only a verified safe binding|external authority
Program versions, semantic attempts, effect intents, fences, cancellation intents, and semantic decisions|Coordinator under a verified parent grant|guarded Coordinator writer boundary|Coordinator durable state may retain only safe material
Delivery and reconciliation decision|Coordinator|guarded Coordinator writer boundary|Coordinator
Direct-local invocation fact|direct-local supervisor|future source-attributed Coordinator observation only|supervisor process evidence
ES admission, lifecycle, cancellation, and retained result|Execution Substrate|ES|ES; Coordinator may retain safe references
Candidate bytes|worker invocation|not Coordinator program truth|mutable worker workspace until seal
Canonical capsule manifest, blobs, and portable digest|capsule builder|private immutable capsule store|private worker-side capsule store
Validation result|validator or repository test executor|source observation; future Coordinator binding only|validator evidence system
Independent review|independent reviewer|source observation/proposal; future Coordinator binding only|reviewer evidence system
Model proposal|model invocation|non-authoritative proposal binding only|model/provider under its own contract
Git object and local ref|Git effect handler and Git|Git|Git object database and refs
Public report|no semantic authority|no authoritative fact writer|projection only
"""
)


CAPSULE_ROLE_ROWS = _rows(
    """
worker|candidate-byte source
capsule builder|canonical sealer
private immutable worker-side store|physical custodian
Coordinator|safe refs, digests, ingest dispositions, and decisions only
reviewer|read-only attempt-bound and capsule-bound retrieval
later ES|opaque carrier or custodian under an ES-owned contract
Git|object and ref truth only after a separately selected Git effect
"""
)


RETRIEVAL_NON_AUTHORITY_RULES = (
    "`capsule_manifest_ref` is not retrieval authority.",
    "`portable_capsule_digest` is not retrieval authority.",
    "Safe-reference possession is not retrieval authority.",
    "Digest possession is not authorization.",
)


RETRIEVAL_INVERSIONS = (
    "The portable capsule digest authorizes retrieval.",
    "Possession of capsule_manifest_ref is sufficient retrieval authority.",
    "The safe capsule reference is a bearer retrieval credential.",
    "Reviewers may enumerate capsules using the digest.",
    "`capsule_manifest_ref` is retrieval authority.",
    "`portable_capsule_digest` is retrieval authority.",
    "Safe-reference possession is retrieval authority.",
    "Digest possession is authorization.",
)


RELATION_VECTOR_ROWS = _rows(
    """
author|`author_candidate`|`effect-intent.author.0001`|`effect-fence.0001`|`71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3`|JSON `null` before sealing|JSON `null`|JSON `null`|JSON `null`|`delivery-attempt.author.0001`|`adapter-correlation.author.0001`|`source-invocation.capsule-builder.0001`|`observation.capsule-sealed.0001`
validation|`validate_candidate`|`effect-intent.validate.0001`|`effect-fence.validate.0001`|`d0867a8d6d6f89fcd8d7efe1a150f6eb904f0dd8a918065de0224db0cb9a9531`|`b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c`|JSON `null`|JSON `null`|JSON `null`|`delivery-attempt.validation.0001`|`adapter-correlation.validation.0001`|`source-invocation.validator.0001`|`validation-observation.0001`
review|`review_candidate`|`effect-intent.review.0001`|`effect-fence.review.0001`|`e615b172eeddca9b69fd6d956b535e7ca60eb36f51e73038586a9ce67316a2bc`|`b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c`|JSON `null`|JSON `null`|JSON `null`|`delivery-attempt.review.0001`|`adapter-correlation.review.0001`|`source-invocation.reviewer.0001`|`independent-review.0001`
cancellation|`cancel_effect`|`effect-intent.cancel.0001`|`effect-fence.cancel.0001`|`ccaf53c44a06410e602c9f39ddc1677e734c0ba6f92c783752b28d1f7e5ff463`|JSON `null`; targets the non-capsule-consuming author effect|`effect-intent.author.0001`|`effect-fence.0001`|`71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3`|`delivery-attempt.cancellation.0001`|`adapter-correlation.cancellation.0001`|`source-invocation.cancel.0001`|`observation.cancellation.0001`
"""
)


CAPSULE_CANCELLATION_VECTOR_ROWS = _rows(
    """
`effect-intent.cancel-validation.0001`|`effect-fence.cancel-validation.0001`|`ae4de68f737afa1e5f22b72384a188abad36d3f9a4ae5e28e835e7644dc0b66b`|`effect-intent.validate.0001`|`effect-fence.validate.0001`|`d0867a8d6d6f89fcd8d7efe1a150f6eb904f0dd8a918065de0224db0cb9a9531`|`b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c`
"""
)


RELATION_DIGESTS = {
    "author": (
        "71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3",
        "3f72f9a3717b54275fa5c580bba60ba30381c662ce2460bcc61dfc818a18fe9a",
        "96a4cb680ae911223392d937a5b108d0b5074196535355e69d730f7a1c542dad",
    ),
    "validation": (
        "d0867a8d6d6f89fcd8d7efe1a150f6eb904f0dd8a918065de0224db0cb9a9531",
        "888725d2de1b7095c3cb1453c5ec4e2046c7507e732556fcd3becc8635052e74",
        "44ad4d6f505e0cfff96cf4147e4864bc942a153f85022653115e910910a737c3",
    ),
    "review": (
        "e615b172eeddca9b69fd6d956b535e7ca60eb36f51e73038586a9ce67316a2bc",
        "7f351c06be0b3852d542059f7b5e9f66a23219e04fb7071c11cc4e472bc839a1",
        "be91f32ee69fc46e48526471c05b2b60f7b691b5beb7d0980e585da97b67cb13",
    ),
    "cancellation": (
        "ccaf53c44a06410e602c9f39ddc1677e734c0ba6f92c783752b28d1f7e5ff463",
        "524ad35f298997e9d9645b0ca46fa793994a0d236ad5f0485b7a82809e04e3a2",
        "9cd66023e89e15d94149bd17aae26b9b988433e6f57eb2db6feed77a29cde78d",
    ),
    "cancellation_validation": (
        "ae4de68f737afa1e5f22b72384a188abad36d3f9a4ae5e28e835e7644dc0b66b",
        "e8fb1839de45b48123014b27ec37068004543880fda95f269800435498579575",
        "9febe2f17b145ceb8d3002515cf574ac58e1633ee6ec70434ce5ca4f851fc345",
    ),
}


EFFECT_VECTOR_CONFIGS = {
    "author": ("author_candidate", "effect-intent.author.0001", "effect-fence.0001", "effect-authorization.0001", "3" * 64, None, None),
    "validation": ("validate_candidate", "effect-intent.validate.0001", "effect-fence.validate.0001", "effect-authorization.validate.0001", "6" * 64, "b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c", None),
    "review": ("review_candidate", "effect-intent.review.0001", "effect-fence.review.0001", "effect-authorization.review.0001", "7" * 64, "b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c", None),
    "cancellation": ("cancel_effect", "effect-intent.cancel.0001", "effect-fence.cancel.0001", "effect-authorization.cancel.0001", "8" * 64, None, "author"),
    "cancellation_validation": ("cancel_effect", "effect-intent.cancel-validation.0001", "effect-fence.cancel-validation.0001", "effect-authorization.cancel-validation.0001", "9" * 64, "b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c", "validation"),
}


CROSS_RECORD_ROWS = _rows(
    """
1|`program_ref`
2|`program_version_ref`
3|`accepted_intent_revision_ref`
4|`work_item_revision_ref`
5|`semantic_attempt_ref`
6|author `effect_intent_ref`
7|originating `command_ref`
8|originating `command_digest`
9|`candidate_ref`
10|`attempt_fence_ref` and `attempt_fence_digest`
11|author `effect_fence_ref` and `effect_fence_digest`
12|`repository_ref`
13|`base_git_object_format` and `base_git_oid`
14|`authorized_path_scope_digest`
15|`capsule_manifest_ref` and `portable_capsule_digest`
"""
)


GIT_PROHIBITION_ROWS = _rows(
    """
1|automatic rebase|prohibited
2|automatic merge|prohibited
3|automatic amend|prohibited
4|path or effect widening|prohibited
5|push|prohibited
6|remote-ref mutation|prohibited
7|pull-request creation|prohibited
8|deployment|prohibited
9|hooks-based extra effect|prohibited
10|hidden second commit|prohibited
11|blind second commit after unknown outcome|prohibited
"""
)


GIT_REQUIREMENT_ROWS = _rows(
    """
local feature-branch commit ceiling|exactly one
effect binding|exact accepted decision, semantic attempt, candidate, capsule manifest, portable capsule digest, repository, base, path ceiling, designated local ref, expected current ref, and intended tree
immediate pre-effect check|revalidate authority, global stop, repository, base, capsule integrity, candidate/workspace equality, path ceiling, and effect ceiling
unknown-outcome treatment|reconcile from Git object and ref truth before any further effect
commit observation|Git evidence only; not semantic completion
"""
)


DECISION_ROLE_ROWS = _rows(
    """
worker self-report|evidence only
structural validation|source-owned validation observation
repository test execution|source-owned validation observation
independent review|separate reviewer observation or proposal bound to the exact capsule
model review|non-authoritative proposal
Coordinator|sole durable semantic decision writer under valid authority
"""
)


PLACEMENT_ROWS = _rows(
    """
Coordinator SQLite|`safe_id`, `safe_ref`, `digest`, `binding`, `ceiling`, `status`, `reason_code`, `coordinator_decision`, `ingest_disposition`|every unlisted material class (closed-world)|future guarded durable progression only
private WorkSpec material|`private_objective`, `private_requirement`, `private_exclusion`, `safe_binding`|every unlisted material class (closed-world)|private desired-work attachment; not durable program truth
worker workspace|`checked_out_base_bytes`, `authorized_candidate_bytes`|every unlisted material class (closed-world)|mutable execution material only
capsule store|`authorized_changed_file_blob`, `canonical_capsule_manifest`, `immutable_capsule_blob`|every unlisted material class (closed-world)|private physical custody only
validation/review observations|`bounded_status`, `bounded_reason_code`, `safe_evidence_ref`, `candidate_ref`, `capsule_manifest_ref`, `portable_capsule_digest`|every unlisted material class (closed-world)|source evidence or proposal only
model proposals|`safe_ref`, `bounded_proposal_status`, `bounded_reason_code`, `capsule_binding`|every unlisted material class (closed-world)|non-authoritative proposal only
public reports|`safe_id`, `safe_ref`, `digest`, `status`, `reason_code`|every unlisted material class (closed-world)|projection only
logs|`bounded_reason_code`, `redacted_safe_correlation`|every unlisted material class (closed-world)|non-authoritative diagnostics only
Git|`accepted_authorized_changed_file_bytes`, `git_object`, `designated_local_ref`|every unlisted material class (closed-world)|object and ref truth only
later ES retained result|`bounded_lifecycle_envelope`, `bounded_result_envelope`, `opaque_safe_capsule_ref`|every unlisted material class (closed-world)|ES runtime truth; not Coordinator semantic truth
"""
)


PLACEMENT_ALLOWED = {
    "Coordinator SQLite": frozenset(("safe_id", "safe_ref", "digest", "binding", "ceiling", "status", "reason_code", "coordinator_decision", "ingest_disposition")),
    "private WorkSpec material": frozenset(("private_objective", "private_requirement", "private_exclusion", "safe_binding")),
    "worker workspace": frozenset(("checked_out_base_bytes", "authorized_candidate_bytes")),
    "capsule store": frozenset(("authorized_changed_file_blob", "canonical_capsule_manifest", "immutable_capsule_blob")),
    "validation/review observations": frozenset(("bounded_status", "bounded_reason_code", "safe_evidence_ref", "candidate_ref", "capsule_manifest_ref", "portable_capsule_digest")),
    "model proposals": frozenset(("safe_ref", "bounded_proposal_status", "bounded_reason_code", "capsule_binding")),
    "public reports": frozenset(("safe_id", "safe_ref", "digest", "status", "reason_code")),
    "logs": frozenset(("bounded_reason_code", "redacted_safe_correlation")),
    "Git": frozenset(("accepted_authorized_changed_file_bytes", "git_object", "designated_local_ref")),
    "later ES retained result": frozenset(("bounded_lifecycle_envelope", "bounded_result_envelope", "opaque_safe_capsule_ref")),
}


REJECTED_MATERIAL_CLASSES = frozenset(
    (
        "trust_material",
        "capsule_bytes",
        "private_work_spec",
        "unrestricted_diff",
        "database_material",
        "token",
        "raw_chat_history",
        "raw_prompt",
        "transcript",
        "codex_jsonl",
        "credential",
        "private_endpoint",
        "absolute_path",
        "raw_log",
        "workspace_bytes",
    )
)


BOOTSTRAP_STOPS = (
    "Missing or invalid standing grant, subordinate authorization, attempt fence, effect fence, or current global-stop binding.",
    "Expired, revoked, stale, ambiguous, widened, or mismatched authority.",
    "Repository identity, base OID, Git object format, or path ceiling mismatch.",
    "A second repository.",
    "A second active invocation.",
    "A Bridge, connector, CP, IM, MA, Host Lens, Symphony, or Bridge Core trigger or dependency.",
    "Direct Coordinator SQLite access by worker, adapter, supervisor, reviewer, model adapter, capsule component, or Git component.",
    "Worker/adapter creation of semantic attempts, acceptance, repair, replan, or publication decisions.",
    "Any push, remote-ref mutation, PR, merge, deployment, or production-autonomy claim.",
    "Command/delivery/observation/fence/capsule contract-version divergence between direct-local and the future ES route.",
    "Candidate authorship, capsule sealing, custody, safe-reference, or retrieval ambiguity.",
    "Unknown process or delivery outcome without authoritative reconciliation.",
    "Blind redelivery after an unknown outcome.",
    "Stale validation, review, model, decision, or Git-effect binding.",
    "Expansion beyond the first accepted slice without a Coordinator-owned durable one-shot latch and a separately accepted migration review.",
)


GOLDEN_META = {
    "WorkSpecV1": (
        "governed-execution.nwp-work-spec.v1",
        "governed-execution.nwp-work-spec.v1.identity",
        1158,
        "5ae0add98fb3b6a233b778fe165dfa7ef8d1f3c43e824dddbdb6827958360ade",
        ("work_spec_digest",),
    ),
    "AttemptFenceV1": (
        "governed-execution.nwp-attempt-fence.v1",
        "governed-execution.nwp-attempt-fence.v1.identity",
        1525,
        "7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e",
        ("attempt_fence_digest",),
    ),
    "EffectFenceV1": (
        "governed-execution.nwp-effect-fence.v1",
        "governed-execution.nwp-effect-fence.v1.identity",
        1928,
        "71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3",
        ("effect_fence_digest",),
    ),
    "WorkerCommandV1": (
        "governed-execution.nwp-worker-command.v1",
        "governed-execution.nwp-worker-command.v1.identity",
        2444,
        "6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927",
        ("effect_fence_digest", "command_digest"),
    ),
    "DeliveryEnvelopeV1": (
        "governed-execution.nwp-delivery-envelope.v1",
        "governed-execution.nwp-delivery-envelope.v1.identity",
        755,
        "83e68b50759dc21746ef7b521edb8f7b61cf5446d819c8c7aa47bee048841f0e",
        ("delivery_envelope_digest",),
    ),
    "WorkerObservationV1": (
        "governed-execution.nwp-worker-observation.v1",
        "governed-execution.nwp-worker-observation.v1.identity",
        1324,
        "b605b2779fa5b46ebff2d23d7026c643debde509c015e840608b0991f1c52a6f",
        ("observation_digest",),
    ),
    "CandidateCapsuleManifestV1": (
        "governed-execution.nwp-candidate-capsule-manifest.v1",
        "governed-execution.nwp-candidate-capsule-manifest.v1.identity",
        2178,
        "b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c",
        ("portable_capsule_digest",),
    ),
}


GOLDEN_BYTES = {
    "WorkSpecV1": b'{"accepted_intent_revision_ref":"intent-revision.0001","authorized_paths":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","exclusions":["Do not push, create a pull request, merge, or deploy.","Do not modify Execution Substrate runtime source."],"objective":"Document the bounded direct-local bootstrap proof while preserving Execution Substrate migration gates.","privacy_classification":"private_work_spec","program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","requirements":["Modify only the three authorized repository-relative paths.","Preserve Execution Substrate reliable-submit ownership and current P0.","Produce no runtime, schema, or service change."],"review_requirement_ref":"review.es-docs.0001","schema_id":"governed-execution.nwp-work-spec.v1","validation_requirement_ref":"validation.es-docs.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001","work_spec_ref":"work-spec.es-docs.0001"}',
    "AttemptFenceV1": b'{"accepted_intent_revision_ref":"intent-revision.0001","aggregate_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":10000000,"max_cpu_seconds":3600,"max_deliveries":2,"max_deployments":0,"max_local_commits":1,"max_memory_bytes":4294967296,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":3600},"allowed_effect_classes":["author_candidate","cancel_effect","local_git_commit","review_candidate","validate_candidate"],"attempt_authorization_digest":"2222222222222222222222222222222222222222222222222222222222222222","attempt_authorization_ref":"attempt-authorization.0001","attempt_fence_ref":"attempt-fence.0001","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","expires_at":"2030-01-01T00:00:00Z","global_stop_ref":"global-stop.current","global_stop_version":7,"parent_standing_grant_digest":"1111111111111111111111111111111111111111111111111111111111111111","parent_standing_grant_ref":"standing-grant.0001","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","schema_id":"governed-execution.nwp-attempt-fence.v1","semantic_attempt_ref":"semantic-attempt.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}',
    "EffectFenceV1": b'{"accepted_intent_revision_ref":"intent-revision.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","cancellation_target_effect_fence_digest":null,"cancellation_target_effect_fence_ref":null,"cancellation_target_effect_intent_ref":null,"candidate_ref":"candidate.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","effect_authorization_digest":"3333333333333333333333333333333333333333333333333333333333333333","effect_authorization_ref":"effect-authorization.0001","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":10000000,"max_cpu_seconds":3600,"max_deliveries":2,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":4294967296,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":3600},"effect_class":"author_candidate","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","expires_at":"2030-01-01T00:00:00Z","global_stop_ref":"global-stop.current","global_stop_version":7,"parent_standing_grant_digest":"1111111111111111111111111111111111111111111111111111111111111111","parent_standing_grant_ref":"standing-grant.0001","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"portable_capsule_digest":null,"program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","schema_id":"governed-execution.nwp-effect-fence.v1","semantic_attempt_ref":"semantic-attempt.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}',
}


GOLDEN_BYTES.update(
    {
        "WorkerCommandV1": b'{"accepted_intent_revision_ref":"intent-revision.0001","attempt_authorization_digest":"2222222222222222222222222222222222222222222222222222222222222222","attempt_authorization_ref":"attempt-authorization.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","candidate_ref":"candidate.0001","capsule_profile_ref":"capsule-profile.regular-replace-v1","capsule_schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","command_ref":"worker-command.0001","effect_authorization_digest":"3333333333333333333333333333333333333333333333333333333333333333","effect_authorization_ref":"effect-authorization.0001","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":10000000,"max_cpu_seconds":3600,"max_deliveries":2,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":4294967296,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":3600},"effect_class":"author_candidate","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","global_stop_ref":"global-stop.current","global_stop_version":7,"path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"privacy_classification":"private_source_change","program_ref":"program.es-docs","program_version_ref":"program-version.0001","redaction_profile_ref":"redaction.source-private-v1","repository_ref":"repository.execution-substrate","review_requirement_digest":"5555555555555555555555555555555555555555555555555555555555555555","review_requirement_ref":"review.es-docs.0001","schema_id":"governed-execution.nwp-worker-command.v1","semantic_attempt_ref":"semantic-attempt.0001","standing_grant_digest":"1111111111111111111111111111111111111111111111111111111111111111","standing_grant_ref":"standing-grant.0001","validation_requirement_digest":"4444444444444444444444444444444444444444444444444444444444444444","validation_requirement_ref":"validation.es-docs.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001","work_spec_digest":"5ae0add98fb3b6a233b778fe165dfa7ef8d1f3c43e824dddbdb6827958360ade","work_spec_ref":"work-spec.es-docs.0001"}',
        "DeliveryEnvelopeV1": b'{"adapter_kind":"direct_local_bootstrap","adapter_safe_correlation_ref":"adapter-correlation.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","delivery_attempt_ref":"delivery-attempt.0001","effect_fence_digest":"71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","program_ref":"program.es-docs","program_version_ref":"program-version.0001","schema_id":"governed-execution.nwp-delivery-envelope.v1","semantic_attempt_ref":"semantic-attempt.0001"}',
        "WorkerObservationV1": b'{"accepted_intent_revision_ref":"intent-revision.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","candidate_ref":"candidate.0001","capsule_manifest_ref":"capsule-manifest.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","delivery_attempt_ref":"delivery-attempt.0001","effect_fence_digest":"71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","evidence_refs":["evidence.capsule-seal.0001"],"observation_kind":"capsule_sealed","observation_ref":"observation.capsule-sealed.0001","observed_at":"2026-08-08T18:00:00Z","outcome":"sealed","portable_capsule_digest":"b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c","program_ref":"program.es-docs","program_version_ref":"program-version.0001","reason_code":"reason.none","schema_id":"governed-execution.nwp-worker-observation.v1","semantic_attempt_ref":"semantic-attempt.0001","source_invocation_ref":"source-invocation.capsule-builder.0001","source_kind":"capsule_builder","source_ref":"capsule-builder.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}',
        "CandidateCapsuleManifestV1": b'{"accepted_intent_revision_ref":"intent-revision.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","authorized_path_scope_digest":"881d8190e95accffbce9d463a68910703595e5106ce81ba00a8433404b6c8116","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","candidate_ref":"candidate.0001","canonicalization_profile":"canonical-json.sorted-keys.utf8.v1","capsule_manifest_ref":"capsule-manifest.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","digest_domain":"governed-execution.nwp-candidate-capsule-manifest.v1.identity","effect_fence_digest":"71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","entries":[{"after_blob_sha256":"7c1525eca0dfcccb6dcda32fe7f7f58281aa82be220018b1f69f4b529503ea8a","after_byte_length":52,"before_blob_sha256":"1ac70a99e7e54c57641ba8c0cb1e49ae7d0e6e5a7b1acaa0443e5afc1782f73a","before_byte_length":53,"mode":"100644","operation":"replace_regular_file","path":".docs/system_overview/hybrid_integration_architecture_adr.md"},{"after_blob_sha256":"3b80b40624b6a3834873b32839e8e7e73644def7437389a5eaea12abe480f180","after_byte_length":45,"before_blob_sha256":"d0cc82b8b8733e1b4ee2aba05aad19d474ed16e746bcac709b083d5ce2d848d9","before_byte_length":46,"mode":"100644","operation":"replace_regular_file","path":"PLANS.md"},{"after_blob_sha256":"267a3924b2a2ce1260c9d2532bf75db970eda7c76c40042d192e6cdece8202c2","after_byte_length":53,"before_blob_sha256":"47fc7108400e128ad4deade38d14c9c410b3f4dd23d3e022b008ac279d96ef90","before_byte_length":54,"mode":"100644","operation":"replace_regular_file","path":"docs_contract_test.go"}],"program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","semantic_attempt_ref":"semantic-attempt.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}',
    }
)


BLOB_FIXTURES = {
    ".docs/system_overview/hybrid_integration_architecture_adr.md": {
        "before": b"Synthetic fixture: architecture before C2A Repair 1.\n",
        "after": b"Synthetic fixture: architecture after C2A Repair 1.\n",
    },
    "PLANS.md": {
        "before": b"Synthetic fixture: plans before C2A Repair 1.\n",
        "after": b"Synthetic fixture: plans after C2A Repair 1.\n",
    },
    "docs_contract_test.go": {
        "before": b"Synthetic fixture: contract test before C2A Repair 1.\n",
        "after": b"Synthetic fixture: contract test after C2A Repair 1.\n",
    },
}


BLOB_EXPECTATIONS = {
    ".docs/system_overview/hybrid_integration_architecture_adr.md": (
        53,
        "1ac70a99e7e54c57641ba8c0cb1e49ae7d0e6e5a7b1acaa0443e5afc1782f73a",
        52,
        "7c1525eca0dfcccb6dcda32fe7f7f58281aa82be220018b1f69f4b529503ea8a",
    ),
    "PLANS.md": (
        46,
        "d0cc82b8b8733e1b4ee2aba05aad19d474ed16e746bcac709b083d5ce2d848d9",
        45,
        "3b80b40624b6a3834873b32839e8e7e73644def7437389a5eaea12abe480f180",
    ),
    "docs_contract_test.go": (
        54,
        "47fc7108400e128ad4deade38d14c9c410b3f4dd23d3e022b008ac279d96ef90",
        53,
        "267a3924b2a2ce1260c9d2532bf75db970eda7c76c40042d192e6cdece8202c2",
    ),
}


AUTHORIZED_PATCH_PATHS = (
    ".docs/architecture.md",
    ".docs/authority-boundaries.md",
    ".docs/autonomous-software-development-operating-model.md",
    ".docs/c2a-first-slice-semantic-protocol-contract.md",
    ".docs/durable-state-model.md",
    ".docs/software-development-progression-boundary.md",
    ".docs/worker-execution-boundary.md",
    "AGENTS.md",
    "README.md",
    "tests/test_architecture_contracts.py",
    "tests/test_autonomous_software_development_operating_model.py",
    "tests/test_c2a_first_slice_semantic_protocol_contract.py",
    "tests/test_software_development_progression_boundary.py",
)


MODEL_SECTIONS = {
    "WorkSpecV1": "WorkSpecV1 fields",
    "AttemptFenceV1": "AttemptFenceV1 fields",
    "EffectFenceV1": "EffectFenceV1 fields",
    "WorkerCommandV1": "WorkerCommandV1 fields",
    "DeliveryEnvelopeV1": "DeliveryEnvelopeV1 fields",
    "WorkerObservationV1": "WorkerObservationV1 fields",
    "CandidateCapsuleManifestV1": "CandidateCapsuleManifestV1 fields",
}


TABLE_LAYOUTS = {
    "Nominal identity inventory": (("Order", "Identity", "Meaning"), ("---:", "---", "---")),
    "One-writer, source, recorder, and custody matrix": (
        ("Fact or material", "Semantic source or authority", "Durable recorder", "Physical custodian or safe holder"),
        ("---", "---", "---", "---"),
    ),
    "Semantic schema and digest-domain inventory": (
        ("Order", "Semantic schema ID", "Model", "Unique digest domain"),
        ("---:", "---", "---", "---"),
    ),
    "CeilingsV1 object": (("Order", "Field", "Meaning"), ("---:", "---", "---")),
    "CapsuleEntryV1 object": (("Order", "Field", "Type or finite value"), ("---:", "---", "---")),
    "Current-effect/originating-author relation vectors": (
        ("Vector", "Current effect class", "Current effect intent", "Current effect fence ref", "Current effect-fence digest", "Capsule binding", "Cancellation target effect intent", "Cancellation target effect fence ref", "Cancellation target effect-fence digest", "Delivery attempt", "Adapter-safe correlation", "Source invocation", "Observation ref"),
        ("---",) * 13,
    ),
    "Capsule-consuming cancellation relation vector": (
        ("Current effect intent", "Current effect fence ref", "Current effect-fence digest", "Target effect intent", "Target effect fence ref", "Target effect-fence digest", "Capsule binding"),
        ("---",) * 7,
    ),
    "Observation fact-owner and authorship matrix": (
        ("Observation family", "Underlying fact owner", "Canonical observation author", "Permitted carrier"),
        ("---", "---", "---", "---"),
    ),
    "First-slice observation fact-owner and authorship matrix": (
        ("Observation family", "Underlying fact owner", "Canonical observation author", "Permitted carrier"),
        ("---", "---", "---", "---"),
    ),
    "Source/observation-kind matrix": (
        ("Order", "Observation kind", "Permitted source kind", "Finite outcome", "Conditional fields"),
        ("---:", "---", "---", "---", "---"),
    ),
    "Observation current-effect relation matrix": (
        ("Observation kind", "Permitted current `EffectFenceV1.effect_class`"),
        ("---", "---"),
    ),
    "Ingest-disposition precedence matrix": (
        ("Order", "Ingest disposition", "Exact condition", "Progression consequence"),
        ("---:", "---", "---", "---"),
    ),
    "Capsule cross-record binding matrix": (("Order", "Cross-record binding"), ("---:", "---")),
    "Capsule custody-role matrix": (("Role", "Capsule responsibility"), ("---", "---")),
    "Decision-role matrix": (("Stage", "Authority posture"), ("---", "---")),
    "Git-effect prohibition matrix": (("Order", "Prohibited effect", "Exact posture"), ("---:", "---", "---")),
    "Git-effect mandatory bindings and reconciliation": (("Requirement", "Exact posture"), ("---", "---")),
    "Placement matrix": (("Location", "Permitted material", "Prohibited material", "Authority posture"), ("---", "---", "---", "---")),
}


for _field_heading in MODEL_SECTIONS.values():
    TABLE_LAYOUTS[_field_heading] = (
        ("Order", "Field", "Required", "Type or finite value", "Role", "In identity"),
        ("---:", "---", "---", "---", "---", "---"),
    )


class _BoundedMarkdown:
    """One deliberately small, fence-aware representation for this contract."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.lines: list[tuple[str, int, int, bool]] = []
        self.headings: list[tuple[int, str, int, int]] = []
        self.fences: list[tuple[int, int, int, int, str, str]] = []
        opened: tuple[str, int, int, int, str] | None = None
        offset = 0
        for line in text.splitlines(keepends=True):
            content = line.rstrip("\r\n")
            stripped = content.lstrip(" ")
            indent = len(content) - len(stripped)
            marker = stripped[0] if stripped and stripped[0] in "`~" else ""
            run = len(stripped) - len(stripped.lstrip(marker)) if marker else 0
            remainder = stripped[run:] if marker else ""
            is_fence_line = False
            if indent <= 3 and run >= 3:
                if opened is None:
                    assert marker != "`" or "`" not in remainder, "invalid backtick fence info"
                    opened = (marker, run, offset, offset + len(line), remainder.strip())
                    is_fence_line = True
                elif marker == opened[0] and run >= opened[1] and not remainder.strip():
                    self.fences.append((opened[2], offset + len(line), opened[3], offset, opened[0], opened[4]))
                    opened = None
                    is_fence_line = True
            outside = opened is None and not is_fence_line
            self.lines.append((line, offset, offset + len(line), outside))
            if outside and indent <= 3:
                match = re.fullmatch(r"(#{1,6})[ \t]+(.+?)[ \t]*", stripped)
                if match:
                    title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2)).strip()
                    self.headings.append((len(match.group(1)), title, offset, offset + len(line)))
            offset += len(line)
        assert opened is None, "unclosed or mismatched fenced block"

    def span(self, title: str, level: int) -> tuple[int, int, int]:
        matches = [heading for heading in self.headings if heading[0] == level and heading[1] == title]
        assert len(matches) == 1, (title, matches)
        selected = matches[0]
        index = self.headings.index(selected)
        later = [heading for heading in self.headings[index + 1 :] if heading[0] <= level]
        return selected[3], later[0][2] if later else len(self.text), selected[2]

    def section(self, title: str, level: int) -> str:
        start, end, _ = self.span(title, level)
        return self.text[start:end]

    def outside_text(self, start: int = 0, end: int | None = None) -> str:
        bound = len(self.text) if end is None else end
        return "".join(line for line, begin, finish, outside in self.lines if outside and begin >= start and finish <= bound)

    @staticmethod
    def _cells(line: str) -> tuple[str, ...]:
        return tuple(cell.strip() for cell in line.rstrip("\r\n").strip("|").split("|"))

    def table_blocks(self, title: str, level: int) -> tuple[tuple[tuple[str, ...], tuple[str, ...], tuple[tuple[str, ...], ...], int], ...]:
        start, end, _ = self.span(title, level)
        selected = [(line, begin, outside) for line, begin, finish, outside in self.lines if begin >= start and finish <= end]
        blocks: list[tuple[tuple[str, ...], tuple[str, ...], tuple[tuple[str, ...], ...], int]] = []
        index = 0
        while index < len(selected):
            line, begin, outside = selected[index]
            if not outside or not line.startswith("|"):
                index += 1
                continue
            raw: list[str] = []
            block_start = begin
            while index < len(selected) and selected[index][2] and selected[index][0].startswith("|"):
                raw.append(selected[index][0])
                index += 1
            assert len(raw) >= 3, "normative table requires header, separator, and body"
            header, separator = self._cells(raw[0]), self._cells(raw[1])
            assert len(header) == len(separator)
            assert all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator)
            rows = tuple(self._cells(line) for line in raw[2:])
            assert all(len(row) == len(header) for row in rows)
            blocks.append((header, separator, rows, block_start))
        return tuple(blocks)

    def table(self, title: str, level: int = 3) -> tuple[tuple[str, ...], ...]:
        header, separator = TABLE_LAYOUTS[title]
        header_line = "| " + " | ".join(header) + " |"
        expected_owners = sum(
            1
            for owner, layout in TABLE_LAYOUTS.items()
            if layout[0] == header and any(heading[1] == owner for heading in self.headings)
        )
        assert expected_owners >= 1
        assert sum(line.rstrip("\r\n") == header_line for line, _, _, outside in self.lines if outside) == expected_owners
        matches = [block for block in self.table_blocks(title, level) if block[0] == header]
        assert len(matches) == 1, (title, tuple(block[0] for block in self.table_blocks(title, level)))
        assert matches[0][1] == separator
        return matches[0][2]


def _headings(text: str) -> tuple[tuple[int, str, int, int], ...]:
    return tuple(_BoundedMarkdown(text).headings)


def _section(text: str, title: str, level: int) -> str:
    return _BoundedMarkdown(text).section(title, level)


def _without_fences(text: str) -> str:
    return _BoundedMarkdown(text).outside_text()


def _table(text: str, heading: str, level: int = 3) -> tuple[tuple[str, ...], ...]:
    return _BoundedMarkdown(text).table(heading, level)


def _unordered_items(text: str) -> tuple[str, ...]:
    items: list[str] = []
    for line in _without_fences(text).splitlines():
        match = re.match(r"^- (.+)$", line)
        if match:
            items.append(match.group(1).strip())
        elif items and line.startswith("  ") and line.strip():
            items[-1] += " " + line.strip()
    return tuple(items)


def _ordered_items(text: str) -> tuple[str, ...]:
    items: list[str] = []
    expected = 1
    for line in _without_fences(text).splitlines():
        match = re.match(r"^(\d+)\. (.+)$", line)
        if match:
            assert int(match.group(1)) == expected
            expected += 1
            items.append(match.group(2).strip())
        elif items and line.startswith("   ") and line.strip():
            items[-1] += " " + line.strip()
    return tuple(items)


def _golden_from_document(model: str, text: str = DOC) -> tuple[str, str, int, str, bytes]:
    parsed = _BoundedMarkdown(text)
    title = f"Golden vector — {model}"
    start, end, _ = parsed.span(title, 4)
    outside = parsed.outside_text(start, end)
    schema, domain, length, digest, excluded = GOLDEN_META[model]
    labels = (
        f"- Schema ID: `{schema}`",
        f"- Digest domain: `{domain}`",
        f"- Canonical byte length: `{length}`",
        f"- Domain-separated SHA-256: `{digest}`",
    )
    for label in labels:
        assert outside.splitlines().count(label) == 1, (model, label)
    for prefix in (
        "- Schema ID:",
        "- Digest domain:",
        "- Canonical byte length:",
        "- Domain-separated SHA-256:",
    ):
        assert sum(line.startswith(prefix) for line in outside.splitlines()) == 1, (model, prefix)
    excluded_values = []
    for field in excluded:
        value = GOLDEN_META["EffectFenceV1"][3] if model == "WorkerCommandV1" and field == "effect_fence_digest" else digest
        excluded_values.append(f"`{field}={value}`")
    excluded_label = (
        "- Excluded full-record field: " + excluded_values[0]
        if len(excluded_values) == 1
        else "- Excluded full-record fields: " + ", ".join(excluded_values)
    )
    assert outside.splitlines().count(excluded_label) == 1, (model, excluded_label)
    assert sum(line.startswith("- Excluded full-record field") for line in outside.splitlines()) == 1
    selected = [fence for fence in parsed.fences if fence[0] >= start and fence[1] <= end and fence[5] == "json"]
    assert len(selected) == 1, (model, selected)
    assert text[selected[0][0] : selected[0][2]] == "```json\n"
    assert text[selected[0][3] : selected[0][1]] == "```\n"
    body = text[selected[0][2] : selected[0][3]]
    assert body.endswith("\n") and body.count("\n") == 1
    canonical = body[:-1].encode("utf-8")
    identical_blocks = [fence for fence in parsed.fences if fence[5] == "json" and text[fence[2] : fence[3]] == body]
    assert len(identical_blocks) == 1 and identical_blocks[0] == selected[0]
    return schema, domain, length, digest, canonical


def _duplicate_rejecting_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _strict_json(raw: bytes) -> object:
    text = raw.decode("utf-8", errors="strict")
    return json.loads(text, object_pairs_hook=_duplicate_rejecting_object)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(domain: str, canonical: bytes) -> str:
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + canonical).hexdigest()


def _identity_object(model: str) -> dict[str, object]:
    value = _strict_json(GOLDEN_BYTES[model])
    assert isinstance(value, dict)
    return value


def _field_names(model: str) -> tuple[str, ...]:
    return tuple(row[1].strip("`") for row in FIELD_ROWS[MODEL_SECTIONS[model]])


def _full_record(model: str) -> dict[str, object]:
    record = deepcopy(_identity_object(model))
    _, _, _, digest, excluded = GOLDEN_META[model]
    for field in excluded:
        record[field] = (
            GOLDEN_META["EffectFenceV1"][3]
            if model == "WorkerCommandV1" and field == "effect_fence_digest"
            else digest
        )
    rows = FIELD_ROWS[MODEL_SECTIONS[model]]
    required = {row[1].strip("`") for row in rows if row[2] == "yes"}
    allowed = {row[1].strip("`") for row in rows}
    assert required <= set(record) <= allowed
    return record


def _identity_bytes_are_valid(model: str, raw: bytes) -> bool:
    try:
        value = _strict_json(raw)
        if not isinstance(value, dict):
            return False
        expected = _identity_object(model)
        schema, domain, _, digest, _ = GOLDEN_META[model]
        if set(value) != set(expected) or value.get("schema_id") != schema:
            return False
        if "base_git_oid" in value and not _base_git_oid_valid(
            value.get("base_git_object_format"), value.get("base_git_oid")
        ):
            return False
        if _canonical(value) != raw:
            return False
        if any(isinstance(item, bool) for item in _walk(value)):
            return False
        return _digest(domain, raw) == digest
    except (UnicodeDecodeError, ValueError, TypeError, json.JSONDecodeError):
        return False


def _walk(value: object):
    if isinstance(value, dict):
        for nested in value.values():
            yield from _walk(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk(nested)
    else:
        yield value


def _normative_table_text(text: str, heading: str, level: int = 3) -> str:
    parsed = _BoundedMarkdown(text)
    expected_header = TABLE_LAYOUTS[heading][0]
    matches = [block for block in parsed.table_blocks(heading, level) if block[0] == expected_header]
    assert len(matches) == 1
    start = matches[0][3]
    end = start
    for line, begin, finish, outside in parsed.lines:
        if begin < start:
            continue
        if not outside or not line.startswith("|"):
            break
        end = finish
    return text[start:end]


def _canonical_mutation(model: str, mutate) -> bytes:
    value = deepcopy(_identity_object(model))
    mutate(value)
    return _canonical(value)


IDENTITY_PAIRS = (
    ("program_version_ref", "accepted_intent_revision_ref"),
    ("accepted_intent_revision_ref", "work_item_revision_ref"),
    ("work_item_revision_ref", "base_git_oid"),
    ("semantic_attempt_ref", "effect_intent_ref"),
    ("effect_intent_ref", "delivery_attempt_ref"),
    ("delivery_attempt_ref", "source_invocation_ref"),
    ("observation_ref", "candidate_ref"),
    ("candidate_ref", "capsule_manifest_ref"),
    ("capsule_manifest_ref", "portable_capsule_digest"),
    ("validation_observation_ref", "independent_review_ref"),
    ("independent_review_ref", "model_proposal_ref"),
    ("model_proposal_ref", "coordinator_decision_ref"),
    ("coordinator_acceptance_ref", "git_effect_intent_ref"),
    ("git_effect_intent_ref", "commit_oid"),
    ("commit_oid", "publication_state_ref"),
)


def _identity_values() -> dict[str, str]:
    names = set(IDENTITIES)
    names.update(name for pair in IDENTITY_PAIRS for name in pair)
    return {name: f"identity.{index:02d}.{name}" for index, name in enumerate(sorted(names), 1)}


def _identity_noncollapse(values: dict[str, str]) -> bool:
    return all(values[left] != values[right] for left, right in IDENTITY_PAIRS)


def _nominal_identity_binding_valid(values: dict[str, str]) -> bool:
    return values == _identity_values() and len({values[name] for name in IDENTITIES}) == len(IDENTITIES)


def _command_replay(left: dict[str, object], right: dict[str, object]) -> str:
    assert left["command_ref"] == right["command_ref"]
    if all(left[field] == right[field] for field in ("command_digest", "effect_fence_digest")):
        return "exact_replay"
    return "conflict"


def _complete_authority(**checks: bool) -> bool:
    required = {
        "structural_valid",
        "parent_grant_valid",
        "subordinate_authorization_valid",
        "fence_valid",
        "not_expired",
        "not_revoked",
        "repository_base_path_match",
        "current_global_stop_match",
    }
    return set(checks) == required and all(type(value) is bool and value for value in checks.values())


def _redelivery_valid(
    original: dict[str, object],
    candidate: dict[str, object],
    *,
    original_effect_fence: object,
    candidate_effect_fence: object,
    attempt_fence: dict[str, object] | object = _UNSET,
    author_command: dict[str, object] | object = _UNSET,
    cancellation_target: object = _UNSET,
    original_cancellation_target: object = _UNSET,
    later_cancellation_target: object = _UNSET,
    author_effect_fence: dict[str, object] | object = _UNSET,
) -> bool:
    if not (
        type(original) is dict
        and type(candidate) is dict
        and type(original_effect_fence) is dict
        and type(candidate_effect_fence) is dict
        and type(attempt_fence) is dict
        and type(author_command) is dict
        and type(author_effect_fence) is dict
    ):
        return False
    if cancellation_target is not _UNSET:
        if (
            original_cancellation_target is not _UNSET
            or later_cancellation_target is not _UNSET
        ):
            return False
        original_cancellation_target = cancellation_target
        later_cancellation_target = cancellation_target
    for record, record_effect_fence, record_cancellation_target in (
        (original, original_effect_fence, original_cancellation_target),
        (candidate, candidate_effect_fence, later_cancellation_target),
    ):
        if not _delivery_record_valid(
            record,
            effect_fence=record_effect_fence,
            attempt_fence=attempt_fence,
            author_command=author_command,
            cancellation_target=record_cancellation_target,
            author_effect_fence=author_effect_fence,
        ):
            return False
    expected = set(_field_names("DeliveryEnvelopeV1"))
    identity_fields = expected - {"delivery_envelope_digest"}
    changed = {
        field for field in identity_fields if original[field] != candidate[field]
    }
    if changed != {"delivery_attempt_ref", "adapter_safe_correlation_ref"}:
        return False
    return (
        original["delivery_envelope_digest"]
        != candidate["delivery_envelope_digest"]
    )


def _valid_redelivery_candidate(original: dict[str, object]) -> dict[str, object]:
    later = deepcopy(original)
    later["delivery_attempt_ref"] = "delivery-attempt.0002"
    later["adapter_safe_correlation_ref"] = "adapter-correlation.0002"
    return _reseal_single_digest_record("DeliveryEnvelopeV1", later)


def _matrix_values(cell: str) -> tuple[str, ...]:
    return tuple(part.strip().strip("`") for part in cell.split(" / "))


OBSERVATION_SPEC = {
    row[1].strip("`"): (_matrix_values(row[2]), _matrix_values(row[3]), row[4])
    for row in OBSERVATION_ROWS
}


CONDITIONAL_FIELDS = {
    "none": frozenset(),
    "candidate": frozenset(("candidate_ref",)),
    "capsule": frozenset(("candidate_ref", "capsule_manifest_ref", "portable_capsule_digest")),
    "exit": frozenset(("process_exit_code",)),
}


SAFE_REF_FIELDS = frozenset(
    (
        "observation_ref",
        "source_ref",
        "source_invocation_ref",
        "delivery_attempt_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "command_ref",
        "attempt_fence_ref",
        "effect_fence_ref",
        "candidate_ref",
        "capsule_manifest_ref",
    )
)


OBSERVATION_DIGEST_FIELDS = frozenset(
    (
        "command_digest",
        "attempt_fence_digest",
        "effect_fence_digest",
        "portable_capsule_digest",
        "observation_digest",
    )
)


def _safe_ref(value: object) -> bool:
    if type(value) is not str or not 1 <= len(value) <= 96:
        return False
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", value) is None:
        return False
    return not value.lower().startswith(("connector-", "tunnel-", "workspace-", "org-", "organization-", "user-"))


def _sha256(value: object) -> bool:
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _base_git_oid_valid(object_format: object, value: object) -> bool:
    return (
        object_format == "sha1"
        and type(value) is str
        and re.fullmatch(r"[0-9a-f]{40}", value) is not None
    )


def _source_timestamp(value: object) -> bool:
    if type(value) is not str or len(value) != 20 or not value.isascii():
        return False
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value) is None:
        return False
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == value


def _reason_code(value: object, kind: str) -> bool:
    if type(value) is not str or re.fullmatch(r"[a-z][a-z0-9_.-]{0,95}", value) is None:
        return False
    return value != "provably_not_accepted" or kind == "delivery_rejected"


def _sealed_record(model: str, identity: dict[str, object]) -> dict[str, object]:
    record = deepcopy(identity)
    excluded = GOLDEN_META[model][4]
    assert len(excluded) == 1
    record[excluded[0]] = _digest(GOLDEN_META[model][1], _canonical(identity))
    return record


def _reseal_single_digest_record(model: str, record: dict[str, object]) -> dict[str, object]:
    excluded = GOLDEN_META[model][4]
    assert len(excluded) == 1
    identity = {field: value for field, value in record.items() if field != excluded[0]}
    return _sealed_record(model, identity)


def _reseal_author_command(record: dict[str, object]) -> dict[str, object]:
    changed = deepcopy(record)
    identity = {
        field: value
        for field, value in changed.items()
        if field not in {"effect_fence_digest", "command_digest"}
    }
    changed["command_digest"] = _digest(
        GOLDEN_META["WorkerCommandV1"][1], _canonical(identity)
    )
    return changed


def _effect_fence_for_vector(vector: str) -> dict[str, object]:
    effect_class, intent, fence_ref, authorization_ref, authorization_digest, capsule, target_vector = EFFECT_VECTOR_CONFIGS[vector]
    identity = _identity_object("EffectFenceV1")
    identity.update(
        effect_class=effect_class,
        effect_intent_ref=intent,
        effect_fence_ref=fence_ref,
        effect_authorization_ref=authorization_ref,
        effect_authorization_digest=authorization_digest,
        portable_capsule_digest=capsule,
    )
    if target_vector is None:
        identity.update(
            cancellation_target_effect_intent_ref=None,
            cancellation_target_effect_fence_ref=None,
            cancellation_target_effect_fence_digest=None,
        )
    else:
        target = _effect_fence_for_vector(target_vector)
        identity.update(
            cancellation_target_effect_intent_ref=target["effect_intent_ref"],
            cancellation_target_effect_fence_ref=target["effect_fence_ref"],
            cancellation_target_effect_fence_digest=target["effect_fence_digest"],
        )
    return _sealed_record("EffectFenceV1", identity)


def _local_git_effect_fence() -> dict[str, object]:
    identity = _identity_object("EffectFenceV1")
    identity.update(
        effect_class="local_git_commit",
        effect_intent_ref="effect-intent.local-git-commit.0001",
        effect_fence_ref="effect-fence.local-git-commit.0001",
        effect_authorization_ref="effect-authorization.local-git-commit.0001",
        effect_authorization_digest="a" * 64,
        portable_capsule_digest=GOLDEN_META["CandidateCapsuleManifestV1"][3],
        cancellation_target_effect_intent_ref=None,
        cancellation_target_effect_fence_ref=None,
        cancellation_target_effect_fence_digest=None,
    )
    identity["effect_ceilings"]["max_local_commits"] = 1
    return _sealed_record("EffectFenceV1", identity)


def _delivery_for_vector(vector: str) -> dict[str, object]:
    fence = _effect_fence_for_vector(vector)
    token = vector.replace("_", "-")
    identity = {
        "schema_id": "governed-execution.nwp-delivery-envelope.v1",
        "program_ref": "program.es-docs",
        "program_version_ref": "program-version.0001",
        "delivery_attempt_ref": f"delivery-attempt.{token}.0001",
        "command_ref": "worker-command.0001",
        "command_digest": "6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927",
        "semantic_attempt_ref": "semantic-attempt.0001",
        "effect_intent_ref": fence["effect_intent_ref"],
        "attempt_fence_ref": "attempt-fence.0001",
        "attempt_fence_digest": "7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e",
        "effect_fence_ref": fence["effect_fence_ref"],
        "effect_fence_digest": fence["effect_fence_digest"],
        "adapter_kind": "direct_local_bootstrap",
        "adapter_safe_correlation_ref": f"adapter-correlation.{token}.0001",
    }
    return _sealed_record("DeliveryEnvelopeV1", identity)


VECTOR_OBSERVATION_CONFIG = {
    "author": ("observation.capsule-sealed.0001", "capsule_builder", "capsule-builder.0001", "source-invocation.capsule-builder.0001", "capsule_sealed", "sealed", "evidence.capsule-seal.0001", "2026-08-08T18:00:00Z", "capsule"),
    "validation": ("validation-observation.0001", "validator", "validator.0001", "source-invocation.validator.0001", "validation_completed", "passed", "evidence.validation.0001", "2026-08-08T18:01:00Z", "capsule"),
    "review": ("independent-review.0001", "independent_reviewer", "independent-reviewer.0001", "source-invocation.reviewer.0001", "independent_review_completed", "passed", "evidence.review.0001", "2026-08-08T18:02:00Z", "capsule"),
    "cancellation": ("observation.cancellation.0001", "direct_local_adapter", "direct-local-adapter.0001", "source-invocation.cancel.0001", "cancellation_acknowledged", "acknowledged", "evidence.cancellation.0001", "2026-08-08T18:03:00Z", "none"),
    "cancellation_validation": ("observation.cancellation-validation.0001", "direct_local_adapter", "direct-local-adapter.0001", "source-invocation.cancel-validation.0001", "cancellation_acknowledged", "acknowledged", "evidence.cancellation-validation.0001", "2026-08-08T18:04:00Z", "none"),
}


def _observation_for_vector(vector: str) -> dict[str, object]:
    delivery = _delivery_for_vector(vector)
    observation_ref, source_kind, source_ref, invocation, kind, outcome, evidence, observed_at, conditional = VECTOR_OBSERVATION_CONFIG[vector]
    identity: dict[str, object] = {
        "schema_id": "governed-execution.nwp-worker-observation.v1",
        "observation_ref": observation_ref,
        "source_kind": source_kind,
        "source_ref": source_ref,
        "source_invocation_ref": invocation,
        "delivery_attempt_ref": delivery["delivery_attempt_ref"],
        "program_ref": "program.es-docs",
        "program_version_ref": "program-version.0001",
        "accepted_intent_revision_ref": "intent-revision.0001",
        "work_item_ref": "work-item.es-docs.0001",
        "work_item_revision_ref": "work-revision.0001",
        "semantic_attempt_ref": "semantic-attempt.0001",
        "effect_intent_ref": delivery["effect_intent_ref"],
        "command_ref": "worker-command.0001",
        "command_digest": "6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927",
        "attempt_fence_ref": "attempt-fence.0001",
        "attempt_fence_digest": "7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e",
        "effect_fence_ref": delivery["effect_fence_ref"],
        "effect_fence_digest": delivery["effect_fence_digest"],
        "observation_kind": kind,
        "outcome": outcome,
        "reason_code": "reason.none",
        "evidence_refs": [evidence],
        "observed_at": observed_at,
    }
    if conditional == "capsule":
        identity.update(
            candidate_ref="candidate.0001",
            capsule_manifest_ref="capsule-manifest.0001",
            portable_capsule_digest="b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c",
        )
    return _sealed_record("WorkerObservationV1", identity)


def _ceilings_valid(value: object) -> bool:
    return (
        type(value) is dict
        and set(value) == set(CEILING_FIELDS)
        and all(type(value[field]) is int and value[field] >= 0 for field in CEILING_FIELDS)
    )


def _attempt_fence_record_valid(record: dict[str, object]) -> bool:
    expected = set(_field_names("AttemptFenceV1"))
    if type(record) is not dict or set(record) != expected:
        return False
    if record.get("schema_id") != "governed-execution.nwp-attempt-fence.v1":
        return False
    ref_fields = {
        "attempt_fence_ref",
        "parent_standing_grant_ref",
        "attempt_authorization_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "repository_ref",
        "global_stop_ref",
    }
    digest_fields = {
        "parent_standing_grant_digest",
        "attempt_authorization_digest",
        "attempt_fence_digest",
    }
    if not all(_safe_ref(record[field]) for field in ref_fields):
        return False
    if not all(_sha256(record[field]) for field in digest_fields):
        return False
    if not _base_git_oid_valid(record.get("base_git_object_format"), record.get("base_git_oid")):
        return False
    if not _path_set_valid(record.get("path_ceiling"), exact_first_slice=True):
        return False
    allowed = record.get("allowed_effect_classes")
    if (
        type(allowed) is not list
        or not allowed
        or allowed != sorted(allowed)
        or len(allowed) != len(set(allowed))
        or not set(allowed) <= EFFECT_CLASSES
    ):
        return False
    if not _ceilings_valid(record.get("aggregate_ceilings")):
        return False
    if not _source_timestamp(record.get("expires_at")):
        return False
    if type(record.get("global_stop_version")) is not int or record["global_stop_version"] < 0:
        return False
    identity = {field: record[field] for field in expected - {"attempt_fence_digest"}}
    return record["attempt_fence_digest"] == _digest(GOLDEN_META["AttemptFenceV1"][1], _canonical(identity))


def _author_command_record_valid(record: dict[str, object]) -> bool:
    expected = set(_field_names("WorkerCommandV1"))
    if type(record) is not dict or set(record) != expected:
        return False
    if record.get("schema_id") != "governed-execution.nwp-worker-command.v1":
        return False
    ref_fields = {field for field in expected if field.endswith("_ref")}
    digest_fields = {field for field in expected if field.endswith("_digest")}
    if not all(_safe_ref(record[field]) for field in ref_fields):
        return False
    if not all(_sha256(record[field]) for field in digest_fields):
        return False
    if record.get("effect_class") != "author_candidate":
        return False
    if not _base_git_oid_valid(record.get("base_git_object_format"), record.get("base_git_oid")):
        return False
    if not _path_set_valid(record.get("path_ceiling"), exact_first_slice=True):
        return False
    if not _ceilings_valid(record.get("effect_ceilings")):
        return False
    if record.get("capsule_schema_id") != MANIFEST_SCHEMA_ID:
        return False
    if record.get("privacy_classification") != "private_source_change":
        return False
    if type(record.get("global_stop_version")) is not int or record["global_stop_version"] < 0:
        return False
    identity = {
        field: record[field]
        for field in expected - {"effect_fence_digest", "command_digest"}
    }
    return record["command_digest"] == _digest(GOLDEN_META["WorkerCommandV1"][1], _canonical(identity))


def _author_command_matches_attempt(command: dict[str, object], attempt_fence: dict[str, object]) -> bool:
    direct = (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "attempt_authorization_ref",
        "attempt_authorization_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "global_stop_ref",
        "global_stop_version",
    )
    return (
        all(command.get(field) == attempt_fence.get(field) for field in direct)
        and command.get("standing_grant_ref") == attempt_fence.get("parent_standing_grant_ref")
        and command.get("standing_grant_digest") == attempt_fence.get("parent_standing_grant_digest")
        and command.get("path_ceiling") == attempt_fence.get("path_ceiling")
    )


def _author_effect_fence_matches_command(
    author_effect_fence: dict[str, object], author_command: dict[str, object]
) -> bool:
    direct = (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "effect_class",
        "command_ref",
        "candidate_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "path_ceiling",
        "effect_authorization_ref",
        "effect_authorization_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_ceilings",
        "global_stop_ref",
        "global_stop_version",
    )
    return (
        author_effect_fence.get("effect_class") == "author_candidate"
        and author_effect_fence.get("portable_capsule_digest") is None
        and author_effect_fence.get("cancellation_target_effect_intent_ref") is None
        and author_effect_fence.get("cancellation_target_effect_fence_ref") is None
        and author_effect_fence.get("cancellation_target_effect_fence_digest") is None
        and all(author_effect_fence.get(field) == author_command.get(field) for field in direct)
        and author_effect_fence.get("parent_standing_grant_ref")
        == author_command.get("standing_grant_ref")
        and author_effect_fence.get("parent_standing_grant_digest")
        == author_command.get("standing_grant_digest")
        and author_effect_fence.get("effect_fence_ref")
        == author_command.get("effect_fence_ref")
        and author_effect_fence.get("effect_fence_digest")
        == author_command.get("effect_fence_digest")
        and author_effect_fence.get("command_digest")
        == author_command.get("command_digest")
    )


def _effect_class_permitted(effect_fence: dict[str, object], attempt_fence: dict[str, object]) -> bool:
    allowed = attempt_fence.get("allowed_effect_classes")
    return type(allowed) is list and allowed.count(effect_fence.get("effect_class")) == 1


def _effect_fence_record_valid(
    record: dict[str, object],
    *,
    attempt_fence: dict[str, object],
    author_command: dict[str, object],
    cancellation_target: object = _UNSET,
    author_effect_fence: dict[str, object] | object = _UNSET,
) -> bool:
    expected = set(_field_names("EffectFenceV1"))
    if not (
        type(record) is dict
        and type(attempt_fence) is dict
        and type(author_command) is dict
        and type(author_effect_fence) is dict
    ):
        return False
    if set(record) != expected:
        return False
    if record.get("schema_id") != "governed-execution.nwp-effect-fence.v1":
        return False
    ordinary_refs = {
        "effect_fence_ref",
        "parent_standing_grant_ref",
        "effect_authorization_ref",
        "attempt_fence_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "command_ref",
        "candidate_ref",
        "repository_ref",
        "global_stop_ref",
    }
    ordinary_digests = {
        "parent_standing_grant_digest",
        "effect_authorization_digest",
        "attempt_fence_digest",
        "command_digest",
        "effect_fence_digest",
    }
    if not all(_safe_ref(record[field]) for field in ordinary_refs):
        return False
    if not all(_sha256(record[field]) for field in ordinary_digests):
        return False
    capsule = record.get("portable_capsule_digest")
    if capsule is not None and not _sha256(capsule):
        return False
    target_intent = record.get("cancellation_target_effect_intent_ref")
    target_ref = record.get("cancellation_target_effect_fence_ref")
    target_digest = record.get("cancellation_target_effect_fence_digest")
    if target_intent is not None and not _safe_ref(target_intent):
        return False
    if target_ref is not None and not _safe_ref(target_ref):
        return False
    if target_digest is not None and not _sha256(target_digest):
        return False
    if not _base_git_oid_valid(record.get("base_git_object_format"), record.get("base_git_oid")):
        return False
    if not _path_set_valid(record.get("path_ceiling"), exact_first_slice=True):
        return False
    if not _ceilings_valid(record.get("effect_ceilings")):
        return False
    if not _source_timestamp(record.get("expires_at")):
        return False
    if type(record.get("global_stop_version")) is not int or record["global_stop_version"] < 0:
        return False
    effect_class = record.get("effect_class")
    if effect_class not in EFFECT_CLASSES:
        return False
    identity = {field: record[field] for field in expected - {"effect_fence_digest"}}
    if record["effect_fence_digest"] != _digest(GOLDEN_META["EffectFenceV1"][1], _canonical(identity)):
        return False
    if not _attempt_fence_record_valid(attempt_fence) or not _author_command_record_valid(author_command):
        return False
    if not _author_command_matches_attempt(author_command, attempt_fence):
        return False
    if not _effect_class_permitted(record, attempt_fence):
        return False
    if effect_class == "author_candidate":
        if record != author_effect_fence:
            return False
    elif not _effect_fence_record_valid(
        author_effect_fence,
        attempt_fence=attempt_fence,
        author_command=author_command,
        author_effect_fence=author_effect_fence,
    ):
        return False
    if not _author_effect_fence_matches_command(author_effect_fence, author_command):
        return False
    attempt_fields = (
        "parent_standing_grant_ref",
        "parent_standing_grant_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "path_ceiling",
        "global_stop_ref",
        "global_stop_version",
    )
    if any(record.get(field) != attempt_fence.get(field) for field in attempt_fields):
        return False
    if record["expires_at"] > attempt_fence["expires_at"]:
        return False
    if any(record["effect_ceilings"][field] > attempt_fence["aggregate_ceilings"][field] for field in CEILING_FIELDS):
        return False
    command_fields = (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "command_ref",
        "command_digest",
        "candidate_ref",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "global_stop_ref",
        "global_stop_version",
    )
    if any(record.get(field) != author_command.get(field) for field in command_fields):
        return False
    if effect_class != "cancel_effect":
        if (target_intent, target_ref, target_digest) != (None, None, None):
            return False
        if effect_class == "author_candidate" and capsule is not None:
            return False
        if effect_class in {"validate_candidate", "review_candidate", "local_git_commit"} and capsule is None:
            return False
        return cancellation_target is _UNSET
    if type(cancellation_target) is not dict or cancellation_target is record:
        return False
    if cancellation_target.get("effect_class") not in CANCELLATION_TARGET_CLASSES:
        return False
    if not _effect_fence_record_valid(
        cancellation_target,
        attempt_fence=attempt_fence,
        author_command=author_command,
        author_effect_fence=author_effect_fence,
    ):
        return False
    if (
        target_intent != cancellation_target.get("effect_intent_ref")
        or target_ref != cancellation_target.get("effect_fence_ref")
        or target_digest != cancellation_target.get("effect_fence_digest")
    ):
        return False
    if target_ref == record.get("effect_fence_ref") or target_digest == record.get("effect_fence_digest"):
        return False
    target_relation_fields = (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "command_ref",
        "command_digest",
        "candidate_ref",
    )
    if any(record.get(field) != cancellation_target.get(field) for field in target_relation_fields):
        return False
    target_capsule = cancellation_target.get("portable_capsule_digest")
    if cancellation_target["effect_class"] == "author_candidate":
        return target_capsule is None and capsule is None
    return target_capsule is not None and capsule == target_capsule


def _default_cancellation_target(effect_fence: dict[str, object]) -> dict[str, object] | None:
    if type(effect_fence) is not dict:
        return None
    for vector in ("author", "validation", "review"):
        target = _effect_fence_for_vector(vector)
        if effect_fence.get("cancellation_target_effect_fence_ref") == target["effect_fence_ref"]:
            return target
    return None


def _canonical_cancellation_target_argument(
    effect_fence: object, supplied: object = _UNSET
) -> object:
    """Test convenience only; core validators never select golden records."""
    if supplied is not _UNSET:
        return supplied
    if type(effect_fence) is not dict or effect_fence.get("effect_class") != "cancel_effect":
        return _UNSET
    return _default_cancellation_target(effect_fence)


def _delivery_record_valid(
    record: dict[str, object],
    *,
    effect_fence: dict[str, object] | object = _UNSET,
    attempt_fence: dict[str, object] | object = _UNSET,
    author_command: dict[str, object] | object = _UNSET,
    cancellation_target: object = _UNSET,
    author_effect_fence: dict[str, object] | object = _UNSET,
) -> bool:
    expected = set(_field_names("DeliveryEnvelopeV1"))
    if not (
        type(record) is dict
        and type(effect_fence) is dict
        and type(attempt_fence) is dict
        and type(author_command) is dict
        and type(author_effect_fence) is dict
    ):
        return False
    if set(record) != expected:
        return False
    if record.get("schema_id") != "governed-execution.nwp-delivery-envelope.v1":
        return False
    ref_fields = expected - {
        "schema_id",
        "command_digest",
        "attempt_fence_digest",
        "effect_fence_digest",
        "adapter_kind",
        "delivery_envelope_digest",
    }
    if not all(_safe_ref(record[field]) for field in ref_fields):
        return False
    digest_fields = ("command_digest", "attempt_fence_digest", "effect_fence_digest", "delivery_envelope_digest")
    if not all(_sha256(record[field]) for field in digest_fields):
        return False
    if record.get("adapter_kind") not in SOURCE_KIND_BY_ADAPTER:
        return False
    identity = {field: record[field] for field in expected - {"delivery_envelope_digest"}}
    if record["delivery_envelope_digest"] != _digest(GOLDEN_META["DeliveryEnvelopeV1"][1], _canonical(identity)):
        return False
    if not _effect_fence_record_valid(
        effect_fence,
        attempt_fence=attempt_fence,
        author_command=author_command,
        cancellation_target=cancellation_target,
        author_effect_fence=author_effect_fence,
    ):
        return False
    if effect_fence.get("effect_class") == "local_git_commit":
        return False
    effect_fields = (
        "program_ref",
        "program_version_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "command_ref",
        "command_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
    )
    if any(record.get(field) != effect_fence.get(field) for field in effect_fields):
        return False
    if any(record.get(field) != author_command.get(field) for field in ("program_ref", "program_version_ref", "semantic_attempt_ref", "command_ref", "command_digest", "attempt_fence_ref", "attempt_fence_digest")):
        return False
    return True


def _observation_record_structural_valid(record: dict[str, object]) -> bool:
    if type(record) is not dict:
        return False
    required = {row[1].strip("`") for row in FIELD_ROWS["WorkerObservationV1 fields"] if row[2] == "yes"}
    kind = record.get("observation_kind")
    if type(kind) is not str or kind not in OBSERVATION_SPEC:
        return False
    sources, outcomes, conditional_key = OBSERVATION_SPEC[kind]
    expected_keys = required | set(CONDITIONAL_FIELDS[conditional_key])
    if set(record) != expected_keys:
        return False
    if record.get("schema_id") != "governed-execution.nwp-worker-observation.v1":
        return False
    if record.get("source_kind") not in sources or record.get("outcome") not in outcomes:
        return False
    if not all(_safe_ref(record[field]) for field in SAFE_REF_FIELDS & set(record)):
        return False
    if not all(_sha256(record[field]) for field in OBSERVATION_DIGEST_FIELDS & set(record)):
        return False
    if not _source_timestamp(record.get("observed_at")) or not _reason_code(record.get("reason_code"), kind):
        return False
    evidence = record.get("evidence_refs")
    if type(evidence) is not list or len(evidence) > 32 or not all(_safe_ref(item) for item in evidence):
        return False
    if evidence != sorted(evidence) or len(evidence) != len(set(evidence)):
        return False
    if "process_exit_code" in record and (type(record["process_exit_code"]) is not int or not -255 <= record["process_exit_code"] <= 255):
        return False
    identity = {field: value for field, value in record.items() if field != "observation_digest"}
    return record["observation_digest"] == _digest(GOLDEN_META["WorkerObservationV1"][1], _canonical(identity))


def _observation_valid(
    record: dict[str, object],
    *,
    effect_fence: dict[str, object],
    delivery: dict[str, object],
    author_command: dict[str, object],
    attempt_fence: dict[str, object] | object = _UNSET,
    author_effect_fence: dict[str, object] | object = _UNSET,
    capsule_manifest: dict[str, object] | object = _UNSET,
    capsule_blobs: object = _UNSET,
    author_observation: dict[str, object] | object = _UNSET,
    cancellation_target: object = _UNSET,
) -> bool:
    if not _observation_record_structural_valid(record):
        return False
    if not (
        type(effect_fence) is dict
        and type(delivery) is dict
        and type(author_command) is dict
        and type(attempt_fence) is dict
        and type(author_effect_fence) is dict
    ):
        return False
    kind = record["observation_kind"]
    if effect_fence.get("effect_class") not in EFFECT_CLASSES_BY_OBSERVATION[kind]:
        return False
    if not _delivery_record_valid(
        delivery,
        effect_fence=effect_fence,
        attempt_fence=attempt_fence,
        author_command=author_command,
        cancellation_target=cancellation_target,
        author_effect_fence=author_effect_fence,
    ):
        return False
    equality_groups = (
        (record, effect_fence, ("program_ref", "program_version_ref", "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref", "effect_intent_ref", "command_ref", "command_digest", "attempt_fence_ref", "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest")),
        (record, delivery, ("program_ref", "program_version_ref", "semantic_attempt_ref", "effect_intent_ref", "command_ref", "command_digest", "attempt_fence_ref", "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest", "delivery_attempt_ref")),
        (record, author_command, ("program_ref", "program_version_ref", "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref", "command_ref", "command_digest", "attempt_fence_ref", "attempt_fence_digest")),
    )
    for left, right, fields in equality_groups:
        if any(left.get(field) != right.get(field) for field in fields):
            return False
    if kind in ADAPTER_AUTHORED_OBSERVATIONS:
        if record.get("source_kind") != SOURCE_KIND_BY_ADAPTER.get(delivery.get("adapter_kind")):
            return False
    conditional_key = OBSERVATION_SPEC[kind][2]
    if conditional_key == "candidate":
        if (
            capsule_manifest is not _UNSET
            or capsule_blobs is not _UNSET
            or author_observation is not _UNSET
        ):
            return False
        return record.get("candidate_ref") == effect_fence.get("candidate_ref") == author_command.get("candidate_ref")
    if conditional_key == "capsule":
        if not (
            type(capsule_manifest) is dict
            and type(capsule_blobs) is dict
            and type(author_observation) is dict
        ):
            return False
        if not _manifest_valid(
            capsule_manifest,
            blobs=capsule_blobs,
            command=author_command,
            attempt_fence=attempt_fence,
            effect_fence=author_effect_fence,
            observation=author_observation,
        ):
            return False
        if any(
            record.get(field) != capsule_manifest.get(field)
            for field in ("candidate_ref", "capsule_manifest_ref", "portable_capsule_digest")
        ):
            return False
        if record.get("candidate_ref") != effect_fence.get("candidate_ref"):
            return False
        if effect_fence.get("effect_class") in {"validate_candidate", "review_candidate"}:
            if effect_fence.get("portable_capsule_digest") is None:
                return False
            if effect_fence.get("portable_capsule_digest") != capsule_manifest.get("portable_capsule_digest"):
                return False
        return True
    if kind in {"cancellation_acknowledged", "cancellation_rejected"}:
        if (
            capsule_manifest is not _UNSET
            or capsule_blobs is not _UNSET
            or author_observation is not _UNSET
        ):
            return False
        return (
            effect_fence.get("effect_class") == "cancel_effect"
            and type(cancellation_target) is dict
        )
    if (
        capsule_manifest is not _UNSET
        or capsule_blobs is not _UNSET
        or author_observation is not _UNSET
    ):
        return False
    return True


def _observation_for_kind(kind: str, effect_class: str | None = None) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    class_to_vector = {
        "author_candidate": "author",
        "validate_candidate": "validation",
        "review_candidate": "review",
        "cancel_effect": "cancellation",
    }
    selected = effect_class or next(item for item in class_to_vector if item in EFFECT_CLASSES_BY_OBSERVATION[kind])
    vector = class_to_vector[selected]
    fence = _effect_fence_for_vector(vector)
    delivery = _delivery_for_vector(vector)
    token = kind.replace("_", "-")
    delivery_identity = {field: value for field, value in delivery.items() if field != "delivery_envelope_digest"}
    delivery_identity["delivery_attempt_ref"] = f"delivery-attempt.{token}.0001"
    delivery_identity["adapter_safe_correlation_ref"] = f"adapter-correlation.{token}.0001"
    delivery = _sealed_record("DeliveryEnvelopeV1", delivery_identity)
    sources, outcomes, conditional = OBSERVATION_SPEC[kind]
    identity: dict[str, object] = {
        "schema_id": "governed-execution.nwp-worker-observation.v1",
        "observation_ref": f"observation.{token}.0001",
        "source_kind": sources[0],
        "source_ref": f"source.{sources[0].replace('_', '-')}.0001",
        "source_invocation_ref": f"source-invocation.{token}.0001",
        "delivery_attempt_ref": delivery["delivery_attempt_ref"],
        "program_ref": "program.es-docs",
        "program_version_ref": "program-version.0001",
        "accepted_intent_revision_ref": "intent-revision.0001",
        "work_item_ref": "work-item.es-docs.0001",
        "work_item_revision_ref": "work-revision.0001",
        "semantic_attempt_ref": "semantic-attempt.0001",
        "effect_intent_ref": fence["effect_intent_ref"],
        "command_ref": "worker-command.0001",
        "command_digest": "6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927",
        "attempt_fence_ref": "attempt-fence.0001",
        "attempt_fence_digest": "7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e",
        "effect_fence_ref": fence["effect_fence_ref"],
        "effect_fence_digest": fence["effect_fence_digest"],
        "observation_kind": kind,
        "outcome": outcomes[0],
        "reason_code": "reason.none",
        "evidence_refs": [f"evidence.{token}.0001"],
        "observed_at": "2026-08-08T19:00:00Z",
    }
    if conditional == "candidate":
        identity["candidate_ref"] = "candidate.0001"
    elif conditional == "capsule":
        identity.update(candidate_ref="candidate.0001", capsule_manifest_ref="capsule-manifest.0001", portable_capsule_digest="b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c")
    elif conditional == "exit":
        identity["process_exit_code"] = 0
    return _sealed_record("WorkerObservationV1", identity), fence, delivery


def _reseal_observation(record: dict[str, object]) -> dict[str, object]:
    identity = {field: value for field, value in record.items() if field != "observation_digest"}
    return _sealed_record("WorkerObservationV1", identity)


def _ingest_disposition(
    *,
    valid: bool = True,
    same_ref: bool = False,
    same_digest: bool = False,
    bound: bool = True,
    contradictory: bool = False,
    stale: bool = False,
    late: bool = False,
) -> str | None:
    if not valid:
        return None
    if same_ref:
        return "duplicate_exact" if same_digest else "conflict_quarantined"
    if not bound or contradictory or (stale and late):
        return "ambiguous_quarantined"
    if stale:
        return "stale_retained"
    if late:
        return "late_retained"
    return "recorded"


def _retargeted_cancellation(
    current: dict[str, object],
    target: dict[str, object],
) -> dict[str, object]:
    changed = deepcopy(current)
    changed["cancellation_target_effect_intent_ref"] = target["effect_intent_ref"]
    changed["cancellation_target_effect_fence_ref"] = target["effect_fence_ref"]
    changed["cancellation_target_effect_fence_digest"] = target["effect_fence_digest"]
    return _reseal_single_digest_record("EffectFenceV1", changed)


UNKNOWN_OUTCOME_DECISION_FIELDS = frozenset(
    (
        "coordinator_decision_ref",
        "decision_kind",
        "program_ref",
        "program_version_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "delivery_attempt_ref",
        "command_ref",
        "command_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "owner_evidence_ref",
        "global_stop_ref",
        "global_stop_version",
        "authority_evaluation",
    )
)


UNKNOWN_OUTCOME_AUTHORITY_FIELDS = frozenset(
    (
        "parent_standing_grant_ref",
        "parent_standing_grant_digest",
        "parent_grant_status",
        "attempt_authorization_ref",
        "attempt_authorization_digest",
        "attempt_authorization_status",
        "effect_authorization_ref",
        "effect_authorization_digest",
        "effect_authorization_status",
        "revocation_status",
        "evaluated_at",
        "current_global_stop_ref",
        "current_global_stop_version",
    )
)


UNKNOWN_OUTCOME_LIFECYCLE_FIELDS = frozenset(
    (
        "delivery_attempt_ref",
        "effect_fence_ref",
        "effect_fence_digest",
        "owner_evidence_ref",
        "source_owner_relation",
    )
)


def _unknown_observation_for_effect_vector(
    effect_vector: str,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    current_effect_fence = _effect_fence_for_vector(effect_vector)
    delivery = _delivery_for_vector(effect_vector)
    unknown_observation, _, _ = _observation_for_kind("delivery_outcome_unknown")
    token = effect_vector.replace("_", "-")
    unknown_observation.update(
        observation_ref=f"observation.delivery-outcome-unknown.{token}.0001",
        source_kind=SOURCE_KIND_BY_ADAPTER[delivery["adapter_kind"]],
        source_ref=f"source.{SOURCE_KIND_BY_ADAPTER[delivery['adapter_kind']].replace('_', '-')}.0001",
        source_invocation_ref=f"source-invocation.delivery-outcome-unknown.{token}.0001",
        program_ref=delivery["program_ref"],
        program_version_ref=delivery["program_version_ref"],
        semantic_attempt_ref=delivery["semantic_attempt_ref"],
        effect_intent_ref=delivery["effect_intent_ref"],
        delivery_attempt_ref=delivery["delivery_attempt_ref"],
        command_ref=delivery["command_ref"],
        command_digest=delivery["command_digest"],
        attempt_fence_ref=delivery["attempt_fence_ref"],
        attempt_fence_digest=delivery["attempt_fence_digest"],
        effect_fence_ref=delivery["effect_fence_ref"],
        effect_fence_digest=delivery["effect_fence_digest"],
    )
    return (
        _reseal_observation(unknown_observation),
        current_effect_fence,
        delivery,
    )


def _unknown_outcome_relation_fixture(
    effect_vector: str = "author",
) -> dict[str, object]:
    if effect_vector not in {"author", "cancellation", "cancellation_validation"}:
        raise ValueError("unknown_outcome_effect_vector")
    unknown_observation, current_effect_fence, delivery = (
        _unknown_observation_for_effect_vector(effect_vector)
    )
    owner_evidence_ref = "evidence.delivery-owner-rejection.0001"
    rejection_observation = deepcopy(unknown_observation)
    rejection_observation.update(
        observation_ref="observation.delivery-rejected-after-unknown.0001",
        source_invocation_ref="source-invocation.delivery-rejected-after-unknown.0001",
        observation_kind="delivery_rejected",
        outcome="rejected",
        reason_code="provably_not_accepted",
        evidence_refs=[owner_evidence_ref],
        observed_at="2026-08-08T19:00:01Z",
    )
    rejection_observation = _reseal_observation(rejection_observation)
    attempt_fence = _full_record("AttemptFenceV1")
    author_command = _full_record("WorkerCommandV1")
    author_effect_fence = _effect_fence_for_vector("author")
    coordinator_decision = {
        "coordinator_decision_ref": "coordinator-redelivery-decision.0001",
        "decision_kind": "redeliver",
        "program_ref": delivery["program_ref"],
        "program_version_ref": delivery["program_version_ref"],
        "semantic_attempt_ref": delivery["semantic_attempt_ref"],
        "effect_intent_ref": delivery["effect_intent_ref"],
        "delivery_attempt_ref": delivery["delivery_attempt_ref"],
        "command_ref": delivery["command_ref"],
        "command_digest": delivery["command_digest"],
        "attempt_fence_ref": delivery["attempt_fence_ref"],
        "attempt_fence_digest": delivery["attempt_fence_digest"],
        "effect_fence_ref": delivery["effect_fence_ref"],
        "effect_fence_digest": delivery["effect_fence_digest"],
        "owner_evidence_ref": owner_evidence_ref,
        "global_stop_ref": current_effect_fence["global_stop_ref"],
        "global_stop_version": current_effect_fence["global_stop_version"],
        "authority_evaluation": "valid_current",
    }
    authority_global_stop = {
        "parent_standing_grant_ref": attempt_fence["parent_standing_grant_ref"],
        "parent_standing_grant_digest": attempt_fence[
            "parent_standing_grant_digest"
        ],
        "parent_grant_status": "valid",
        "attempt_authorization_ref": attempt_fence["attempt_authorization_ref"],
        "attempt_authorization_digest": attempt_fence[
            "attempt_authorization_digest"
        ],
        "attempt_authorization_status": "valid",
        "effect_authorization_ref": current_effect_fence[
            "effect_authorization_ref"
        ],
        "effect_authorization_digest": current_effect_fence[
            "effect_authorization_digest"
        ],
        "effect_authorization_status": "valid",
        "revocation_status": "not_revoked",
        "evaluated_at": "2026-08-08T19:00:02Z",
        "current_global_stop_ref": current_effect_fence["global_stop_ref"],
        "current_global_stop_version": current_effect_fence[
            "global_stop_version"
        ],
    }
    effect_lifecycle_relation = {
        "delivery_attempt_ref": delivery["delivery_attempt_ref"],
        "effect_fence_ref": current_effect_fence["effect_fence_ref"],
        "effect_fence_digest": current_effect_fence["effect_fence_digest"],
        "owner_evidence_ref": owner_evidence_ref,
        "source_owner_relation": "current",
    }
    relation = {
        "unknown_observation": unknown_observation,
        "rejection_observation": rejection_observation,
        "delivery": delivery,
        "current_effect_fence": current_effect_fence,
        "attempt_fence": attempt_fence,
        "author_command": author_command,
        "author_effect_fence": author_effect_fence,
        "owner_evidence_ref": owner_evidence_ref,
        "selected_adapter_route": delivery["adapter_kind"],
        "canonical_observation_author": rejection_observation["source_kind"],
        "coordinator_decision": coordinator_decision,
        "authority_global_stop": authority_global_stop,
        "effect_lifecycle_relation": effect_lifecycle_relation,
    }
    if current_effect_fence["effect_class"] == "cancel_effect":
        relation["cancellation_target"] = _default_cancellation_target(
            current_effect_fence
        )
    return relation


UNKNOWN_OUTCOME_OBSERVATION_RELATION_FIELDS = (
    "program_ref",
    "program_version_ref",
    "semantic_attempt_ref",
    "effect_intent_ref",
    "delivery_attempt_ref",
    "command_ref",
    "command_digest",
    "attempt_fence_ref",
    "attempt_fence_digest",
    "effect_fence_ref",
    "effect_fence_digest",
)


def _unknown_outcome_rejection_ingest_disposition(
    unknown_observation: object,
    rejection_observation: object,
    *,
    owner_evidence_ref: object,
    effect_lifecycle_relation: object,
) -> str | None:
    if not (
        _observation_record_structural_valid(unknown_observation)
        and _observation_record_structural_valid(rejection_observation)
        and type(unknown_observation) is dict
        and type(rejection_observation) is dict
        and type(effect_lifecycle_relation) is dict
        and set(effect_lifecycle_relation) == UNKNOWN_OUTCOME_LIFECYCLE_FIELDS
        and _safe_ref(owner_evidence_ref)
    ):
        return None
    lifecycle_bound = (
        effect_lifecycle_relation.get("delivery_attempt_ref")
        == rejection_observation.get("delivery_attempt_ref")
        and effect_lifecycle_relation.get("effect_fence_ref")
        == rejection_observation.get("effect_fence_ref")
        and effect_lifecycle_relation.get("effect_fence_digest")
        == rejection_observation.get("effect_fence_digest")
        and effect_lifecycle_relation.get("owner_evidence_ref")
        == owner_evidence_ref
    )
    same_ref = (
        rejection_observation.get("observation_ref")
        == unknown_observation.get("observation_ref")
    )
    same_digest = (
        rejection_observation.get("observation_digest")
        == unknown_observation.get("observation_digest")
    )
    bound = all(
        rejection_observation.get(field) == unknown_observation.get(field)
        for field in UNKNOWN_OUTCOME_OBSERVATION_RELATION_FIELDS
    ) and lifecycle_bound
    lifecycle = effect_lifecycle_relation.get("source_owner_relation")
    contradictory = (
        lifecycle not in {"current", "stale", "late"}
        or (not same_ref and same_digest)
    )
    stale = lifecycle == "stale"
    late = lifecycle == "late"
    return _ingest_disposition(
        valid=True,
        same_ref=same_ref,
        same_digest=same_digest,
        bound=bound,
        contradictory=contradictory,
        stale=stale,
        late=late,
    )


def _unknown_outcome_cancellation_target_relation_valid(
    current_effect_fence: object, cancellation_target: object
) -> bool:
    if type(current_effect_fence) is not dict:
        return False
    if current_effect_fence.get("effect_class") != "cancel_effect":
        return cancellation_target is _UNSET
    if type(cancellation_target) is not dict:
        return False
    return (
        current_effect_fence.get("cancellation_target_effect_intent_ref")
        == cancellation_target.get("effect_intent_ref")
        and current_effect_fence.get("cancellation_target_effect_fence_ref")
        == cancellation_target.get("effect_fence_ref")
        and current_effect_fence.get("cancellation_target_effect_fence_digest")
        == cancellation_target.get("effect_fence_digest")
    )


def _unknown_outcome_redelivery_allowed(
    *,
    unknown_observation: object = _UNSET,
    rejection_observation: object = _UNSET,
    delivery: object = _UNSET,
    current_effect_fence: object = _UNSET,
    attempt_fence: object = _UNSET,
    author_command: object = _UNSET,
    author_effect_fence: object = _UNSET,
    cancellation_target: object = _UNSET,
    owner_evidence_ref: object = _UNSET,
    selected_adapter_route: object = _UNSET,
    canonical_observation_author: object = _UNSET,
    coordinator_decision: object = _UNSET,
    authority_global_stop: object = _UNSET,
    effect_lifecycle_relation: object = _UNSET,
    **detached_claims: object,
) -> bool:
    if detached_claims:
        return False
    supplied = (
        unknown_observation,
        rejection_observation,
        delivery,
        current_effect_fence,
        attempt_fence,
        author_command,
        author_effect_fence,
        owner_evidence_ref,
        selected_adapter_route,
        canonical_observation_author,
        coordinator_decision,
        authority_global_stop,
        effect_lifecycle_relation,
    )
    if any(value is _UNSET for value in supplied):
        return False
    if not (
        type(unknown_observation) is dict
        and type(rejection_observation) is dict
        and type(delivery) is dict
        and type(current_effect_fence) is dict
        and type(attempt_fence) is dict
        and type(author_command) is dict
        and type(author_effect_fence) is dict
        and type(coordinator_decision) is dict
        and type(authority_global_stop) is dict
        and type(effect_lifecycle_relation) is dict
        and _safe_ref(owner_evidence_ref)
        and type(selected_adapter_route) is str
        and type(canonical_observation_author) is str
    ):
        return False
    if not (
        _observation_record_structural_valid(unknown_observation)
        and _observation_record_structural_valid(rejection_observation)
    ):
        return False
    ingest_disposition = _unknown_outcome_rejection_ingest_disposition(
        unknown_observation,
        rejection_observation,
        owner_evidence_ref=owner_evidence_ref,
        effect_lifecycle_relation=effect_lifecycle_relation,
    )
    if ingest_disposition != "recorded":
        return False
    if not _attempt_fence_record_valid(attempt_fence):
        return False
    if not _author_command_record_valid(author_command):
        return False
    if not _author_command_matches_attempt(author_command, attempt_fence):
        return False
    if not _unknown_outcome_cancellation_target_relation_valid(
        current_effect_fence, cancellation_target
    ):
        return False
    if not _effect_fence_record_valid(
        current_effect_fence,
        attempt_fence=attempt_fence,
        author_command=author_command,
        cancellation_target=cancellation_target,
        author_effect_fence=author_effect_fence,
    ):
        return False
    if not _delivery_record_valid(
        delivery,
        effect_fence=current_effect_fence,
        attempt_fence=attempt_fence,
        author_command=author_command,
        cancellation_target=cancellation_target,
        author_effect_fence=author_effect_fence,
    ):
        return False
    for observation in (unknown_observation, rejection_observation):
        if not _observation_valid(
            observation,
            effect_fence=current_effect_fence,
            delivery=delivery,
            author_command=author_command,
            attempt_fence=attempt_fence,
            author_effect_fence=author_effect_fence,
            cancellation_target=cancellation_target,
        ):
            return False
    if (
        unknown_observation.get("observation_kind") != "delivery_outcome_unknown"
        or unknown_observation.get("outcome") != "unknown"
        or rejection_observation.get("observation_kind") != "delivery_rejected"
        or rejection_observation.get("outcome") != "rejected"
        or rejection_observation.get("reason_code") != "provably_not_accepted"
    ):
        return False
    observation_relation_fields = UNKNOWN_OUTCOME_OBSERVATION_RELATION_FIELDS
    if any(
        unknown_observation.get(field) != rejection_observation.get(field)
        for field in observation_relation_fields
    ):
        return False
    expected_author = SOURCE_KIND_BY_ADAPTER.get(selected_adapter_route)
    if (
        selected_adapter_route != delivery.get("adapter_kind")
        or expected_author is None
        or canonical_observation_author != expected_author
        or unknown_observation.get("source_kind") != expected_author
        or rejection_observation.get("source_kind") != expected_author
        or rejection_observation.get("evidence_refs", []).count(owner_evidence_ref)
        != 1
    ):
        return False
    if set(coordinator_decision) != UNKNOWN_OUTCOME_DECISION_FIELDS:
        return False
    if not _unknown_outcome_cancellation_target_relation_valid(
        current_effect_fence, cancellation_target
    ):
        return False
    decision_ref_fields = {
        "coordinator_decision_ref",
        "program_ref",
        "program_version_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "delivery_attempt_ref",
        "command_ref",
        "attempt_fence_ref",
        "effect_fence_ref",
        "owner_evidence_ref",
        "global_stop_ref",
    }
    decision_digest_fields = {
        "command_digest",
        "attempt_fence_digest",
        "effect_fence_digest",
    }
    if not all(_safe_ref(coordinator_decision[field]) for field in decision_ref_fields):
        return False
    if not all(_sha256(coordinator_decision[field]) for field in decision_digest_fields):
        return False
    decision_graph = {
        field: rejection_observation[field]
        for field in observation_relation_fields
    }
    decision_graph.update(
        owner_evidence_ref=owner_evidence_ref,
        global_stop_ref=current_effect_fence["global_stop_ref"],
        global_stop_version=current_effect_fence["global_stop_version"],
    )
    if (
        coordinator_decision.get("decision_kind") != "redeliver"
        or coordinator_decision.get("authority_evaluation") != "valid_current"
        or type(coordinator_decision.get("global_stop_version")) is not int
        or any(
            coordinator_decision.get(field) != value
            for field, value in decision_graph.items()
        )
    ):
        return False
    if set(authority_global_stop) != UNKNOWN_OUTCOME_AUTHORITY_FIELDS:
        return False
    if not _unknown_outcome_cancellation_target_relation_valid(
        current_effect_fence, cancellation_target
    ):
        return False
    authority_ref_fields = {
        "parent_standing_grant_ref",
        "attempt_authorization_ref",
        "effect_authorization_ref",
        "current_global_stop_ref",
    }
    authority_digest_fields = {
        "parent_standing_grant_digest",
        "attempt_authorization_digest",
        "effect_authorization_digest",
    }
    if not all(_safe_ref(authority_global_stop[field]) for field in authority_ref_fields):
        return False
    if not all(_sha256(authority_global_stop[field]) for field in authority_digest_fields):
        return False
    evaluated_at = authority_global_stop.get("evaluated_at")
    if not _source_timestamp(evaluated_at):
        return False
    authority_expected = {
        "parent_standing_grant_ref": attempt_fence["parent_standing_grant_ref"],
        "parent_standing_grant_digest": attempt_fence[
            "parent_standing_grant_digest"
        ],
        "attempt_authorization_ref": attempt_fence["attempt_authorization_ref"],
        "attempt_authorization_digest": attempt_fence[
            "attempt_authorization_digest"
        ],
        "effect_authorization_ref": current_effect_fence[
            "effect_authorization_ref"
        ],
        "effect_authorization_digest": current_effect_fence[
            "effect_authorization_digest"
        ],
        "current_global_stop_ref": current_effect_fence["global_stop_ref"],
        "current_global_stop_version": current_effect_fence[
            "global_stop_version"
        ],
    }
    return (
        all(
            authority_global_stop.get(field) == value
            for field, value in authority_expected.items()
        )
        and authority_global_stop.get("parent_grant_status") == "valid"
        and authority_global_stop.get("attempt_authorization_status") == "valid"
        and authority_global_stop.get("effect_authorization_status") == "valid"
        and authority_global_stop.get("revocation_status") == "not_revoked"
        and type(authority_global_stop.get("current_global_stop_version")) is int
        and evaluated_at <= attempt_fence["expires_at"]
        and evaluated_at <= current_effect_fence["expires_at"]
        and authority_global_stop["current_global_stop_ref"]
        == attempt_fence["global_stop_ref"]
        and authority_global_stop["current_global_stop_version"]
        == attempt_fence["global_stop_version"]
    )


def _portable_path_valid(path: object) -> bool:
    if not isinstance(path, str) or not path or "\x00" in path or "\\" in path:
        return False
    if path.startswith("/") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", path):
        return False
    segments = path.split("/")
    return all(segment not in ("", ".", "..") for segment in segments)


def _path_set_valid(paths: object, *, exact_first_slice: bool) -> bool:
    if type(paths) is not list or not paths or not all(_portable_path_valid(path) for path in paths):
        return False
    strings = [path for path in paths if isinstance(path, str)]
    if strings != sorted(strings):
        return False
    if len(strings) != len(set(strings)):
        return False
    if len(strings) != len({path.casefold() for path in strings}):
        return False
    if len(strings) != len({unicodedata.normalize("NFC", path) for path in strings}):
        return False
    return not exact_first_slice or tuple(strings) == AUTHORIZED_PATHS


def _authorized_path_scope_digest(paths: tuple[str, ...]) -> str:
    return _digest("governed-execution.nwp-authorized-path-scope.v1.identity", _canonical(list(paths)))


def _manifest_valid(
    manifest: dict[str, object],
    *,
    blobs: dict[str, dict[str, bytes]] | object = _UNSET,
    command: dict[str, object] | object = _UNSET,
    attempt_fence: dict[str, object] | object = _UNSET,
    effect_fence: dict[str, object] | object = _UNSET,
    observation: dict[str, object] | None | object = _UNSET,
) -> bool:
    expected_fields = set(_field_names("CandidateCapsuleManifestV1"))
    if not (
        type(manifest) is dict
        and type(blobs) is dict
        and type(command) is dict
        and type(attempt_fence) is dict
        and type(effect_fence) is dict
        and type(observation) is dict
    ):
        return False
    if set(manifest) != expected_fields:
        return False
    if (
        manifest.get("schema_id") != MANIFEST_SCHEMA_ID
        or manifest.get("canonicalization_profile") != MANIFEST_CANONICALIZATION_PROFILE
        or manifest.get("digest_domain") != MANIFEST_DIGEST_DOMAIN
    ):
        return False
    manifest_refs = {
        "candidate_ref",
        "capsule_manifest_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "command_ref",
        "attempt_fence_ref",
        "effect_fence_ref",
        "repository_ref",
    }
    manifest_digests = {
        "command_digest",
        "attempt_fence_digest",
        "effect_fence_digest",
        "authorized_path_scope_digest",
        "portable_capsule_digest",
    }
    if not all(_safe_ref(manifest[field]) for field in manifest_refs):
        return False
    if not all(_sha256(manifest[field]) for field in manifest_digests):
        return False
    if not _base_git_oid_valid(manifest.get("base_git_object_format"), manifest.get("base_git_oid")):
        return False
    entries = manifest.get("entries")
    if type(entries) is not list or not entries:
        return False
    paths: list[object] = []
    entry_fields = {row[1].strip("`") for row in CAPSULE_ENTRY_ROWS}
    if (
        any(type(path) is not str for path in blobs)
        or set(blobs) != set(AUTHORIZED_PATHS)
    ):
        return False
    for entry in entries:
        if type(entry) is not dict or set(entry) != entry_fields:
            return False
        path = entry.get("path")
        paths.append(path)
        if entry.get("operation") != "replace_regular_file":
            return False
        if entry.get("mode") not in {"100644", "100755"}:
            return False
        for field in ("before_blob_sha256", "after_blob_sha256"):
            value = entry.get(field)
            if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
                return False
        for field in ("before_byte_length", "after_byte_length"):
            value = entry.get(field)
            if type(value) is not int or value < 0:
                return False
        if type(path) is not str or path not in blobs:
            return False
        fixture = blobs[path]
        if type(fixture) is not dict or set(fixture) != {"before", "after"}:
            return False
        for phase in ("before", "after"):
            raw = fixture[phase]
            if type(raw) is not bytes:
                return False
            if entry[f"{phase}_blob_sha256"] != hashlib.sha256(raw).hexdigest():
                return False
            if entry[f"{phase}_byte_length"] != len(raw):
                return False
    string_paths = tuple(path for path in paths if type(path) is str)
    if not _path_set_valid(paths, exact_first_slice=True):
        return False
    if manifest.get("authorized_path_scope_digest") != _authorized_path_scope_digest(string_paths):
        return False
    identity = {field: value for field, value in manifest.items() if field != "portable_capsule_digest"}
    if manifest.get("portable_capsule_digest") != _digest(GOLDEN_META["CandidateCapsuleManifestV1"][1], _canonical(identity)):
        return False

    if not _attempt_fence_record_valid(attempt_fence):
        return False
    if not _author_command_record_valid(command) or not _author_command_matches_attempt(command, attempt_fence):
        return False
    if not _effect_fence_record_valid(
        effect_fence,
        attempt_fence=attempt_fence,
        author_command=command,
        author_effect_fence=effect_fence,
    ):
        return False
    if effect_fence.get("effect_class") != "author_candidate":
        return False
    if not _observation_record_structural_valid(observation):
        return False
    if observation.get("observation_kind") != "capsule_sealed":
        return False
    equality_groups = (
        (manifest, command, ("program_ref", "program_version_ref", "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref", "effect_intent_ref", "command_ref", "command_digest", "candidate_ref", "attempt_fence_ref", "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest", "repository_ref", "base_git_object_format", "base_git_oid")),
        (manifest, attempt_fence, ("program_ref", "program_version_ref", "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref", "attempt_fence_ref", "attempt_fence_digest", "repository_ref", "base_git_object_format", "base_git_oid")),
        (manifest, effect_fence, ("program_ref", "program_version_ref", "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref", "effect_intent_ref", "command_ref", "command_digest", "candidate_ref", "attempt_fence_ref", "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest", "repository_ref", "base_git_object_format", "base_git_oid")),
    )
    equality_groups += (
        (manifest, observation, ("program_ref", "program_version_ref", "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref", "effect_intent_ref", "command_ref", "command_digest", "candidate_ref", "attempt_fence_ref", "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest", "capsule_manifest_ref", "portable_capsule_digest")),
    )
    if any(left.get(field) != right.get(field) for left, right, fields in equality_groups for field in fields):
        return False
    return manifest["authorized_path_scope_digest"] == _authorized_path_scope_digest(tuple(command["path_ceiling"]))


def _manifest_with_entry_mutation(field: str, value: object) -> dict[str, object]:
    manifest = deepcopy(_full_record("CandidateCapsuleManifestV1"))
    manifest["entries"][0][field] = value
    identity = {key: item for key, item in manifest.items() if key != "portable_capsule_digest"}
    manifest["portable_capsule_digest"] = _digest(GOLDEN_META["CandidateCapsuleManifestV1"][1], _canonical(identity))
    return manifest


def _reseal_manifest(manifest: dict[str, object]) -> dict[str, object]:
    identity = {field: value for field, value in manifest.items() if field != "portable_capsule_digest"}
    result = deepcopy(manifest)
    result["portable_capsule_digest"] = _digest(GOLDEN_META["CandidateCapsuleManifestV1"][1], _canonical(identity))
    return result


def _retrieval_contract_valid(text: str) -> bool:
    try:
        clause = _section(text, f"{CLAUSES[7][0]} — {CLAUSES[7][1]}", 2)
    except AssertionError:
        return False
    for rule in RETRIEVAL_NON_AUTHORITY_RULES:
        line = f"- {rule}\n"
        if text.count(line) != 1 or line not in clause:
            return False
    normalized = " ".join(_without_fences(clause).split())
    if any(inversion in normalized for inversion in RETRIEVAL_INVERSIONS):
        return False
    required = (
        "It is read-only, attempt-bound, capsule-bound, audience-bound, non-enumerating, non-mutating, and no longer-lived than its parent authority.",
        "the portable capsule digest does not authorize retrieval",
        "possession of `capsule_manifest_ref` is not sufficient retrieval authority",
        "a safe capsule reference is not a bearer retrieval credential",
        "reviewers may not enumerate capsules using a digest",
    )
    return all(statement in normalized for statement in required)


def _placement_allows(location: object, material_class: object) -> bool:
    return type(location) is str and type(material_class) is str and location in PLACEMENT_ALLOWED and material_class in PLACEMENT_ALLOWED[location]


def _git_contract_valid(text: str) -> bool:
    try:
        clause = " ".join(_section(text, f"{CLAUSES[9][0]} — {CLAUSES[9][1]}", 2).split())
        return (
            _table(text, "Git-effect prohibition matrix") == GIT_PROHIBITION_ROWS
            and _table(text, "Git-effect mandatory bindings and reconciliation") == GIT_REQUIREMENT_ROWS
            and "hard ceilings are exactly one local commit and zero pushes, pull requests, merges, and deployments" in clause
        )
    except (AssertionError, KeyError, ValueError):
        return False


def _observation_relation(
    observation: dict[str, object],
    effect_fence: dict[str, object],
    delivery: dict[str, object],
    *,
    author_command: dict[str, object] | object = _UNSET,
    attempt_fence: dict[str, object] | object = _UNSET,
    author_effect_fence: dict[str, object] | object = _UNSET,
    capsule_manifest: dict[str, object] | object = _UNSET,
    capsule_blobs: object = _UNSET,
    author_observation: dict[str, object] | object = _UNSET,
    cancellation_target: object = _UNSET,
) -> bool:
    return _observation_valid(
        observation,
        effect_fence=effect_fence,
        delivery=delivery,
        author_command=author_command,
        attempt_fence=attempt_fence,
        author_effect_fence=author_effect_fence,
        capsule_manifest=capsule_manifest,
        capsule_blobs=capsule_blobs,
        author_observation=author_observation,
        cancellation_target=cancellation_target,
    )


def _canonical_author_effect_argument(
    effect_fence: object, supplied: object = _UNSET
) -> object:
    """Test convenience only; core validators require the actual relation."""
    if supplied is not _UNSET:
        return supplied
    if (
        type(effect_fence) is dict
        and effect_fence.get("effect_class") == "author_candidate"
    ):
        return effect_fence
    return _effect_fence_for_vector("author")


def _effect_fence_record_valid_with_canonical_relations(
    record: dict[str, object],
    *,
    attempt_fence: dict[str, object] | object = _UNSET,
    author_command: dict[str, object] | object = _UNSET,
    cancellation_target: object = _UNSET,
    author_effect_fence: dict[str, object] | object = _UNSET,
) -> bool:
    selected_attempt = (
        _full_record("AttemptFenceV1")
        if attempt_fence is _UNSET
        else attempt_fence
    )
    selected_command = (
        _full_record("WorkerCommandV1")
        if author_command is _UNSET
        else author_command
    )
    return _effect_fence_record_valid(
        record,
        attempt_fence=selected_attempt,
        author_command=selected_command,
        cancellation_target=_canonical_cancellation_target_argument(
            record, cancellation_target
        ),
        author_effect_fence=_canonical_author_effect_argument(
            record, author_effect_fence
        ),
    )


def _delivery_record_valid_with_canonical_relations(
    record: dict[str, object],
    *,
    effect_fence: dict[str, object] | object = _UNSET,
    attempt_fence: dict[str, object] | object = _UNSET,
    author_command: dict[str, object] | object = _UNSET,
    cancellation_target: object = _UNSET,
    author_effect_fence: dict[str, object] | object = _UNSET,
) -> bool:
    selected_effect = (
        _effect_fence_for_vector("author")
        if effect_fence is _UNSET
        else effect_fence
    )
    selected_attempt = (
        _full_record("AttemptFenceV1")
        if attempt_fence is _UNSET
        else attempt_fence
    )
    selected_command = (
        _full_record("WorkerCommandV1")
        if author_command is _UNSET
        else author_command
    )
    return _delivery_record_valid(
        record,
        effect_fence=selected_effect,
        attempt_fence=selected_attempt,
        author_command=selected_command,
        cancellation_target=_canonical_cancellation_target_argument(
            selected_effect, cancellation_target
        ),
        author_effect_fence=_canonical_author_effect_argument(
            selected_effect, author_effect_fence
        ),
    )


def _redelivery_valid_with_canonical_relations(
    original: dict[str, object],
    candidate: dict[str, object],
    *,
    original_effect_fence: object = _UNSET,
    candidate_effect_fence: object = _UNSET,
    attempt_fence: dict[str, object] | object = _UNSET,
    author_command: dict[str, object] | object = _UNSET,
    cancellation_target: object = _UNSET,
    original_cancellation_target: object = _UNSET,
    later_cancellation_target: object = _UNSET,
    author_effect_fence: dict[str, object] | object = _UNSET,
) -> bool:
    selected_original_effect_fence = original_effect_fence
    selected_candidate_effect_fence = candidate_effect_fence
    if (
        original_effect_fence is _UNSET
        and candidate_effect_fence is _UNSET
    ):
        canonical_effect_fence = _effect_fence_for_vector("author")
        selected_original_effect_fence = canonical_effect_fence
        selected_candidate_effect_fence = canonical_effect_fence
    selected_attempt = (
        _full_record("AttemptFenceV1")
        if attempt_fence is _UNSET
        else attempt_fence
    )
    selected_command = (
        _full_record("WorkerCommandV1")
        if author_command is _UNSET
        else author_command
    )
    selected_cancellation_target = cancellation_target
    if (
        cancellation_target is _UNSET
        and original_cancellation_target is _UNSET
        and later_cancellation_target is _UNSET
    ):
        selected_cancellation_target = _canonical_cancellation_target_argument(
            selected_original_effect_fence
        )
    return _redelivery_valid(
        original,
        candidate,
        original_effect_fence=selected_original_effect_fence,
        candidate_effect_fence=selected_candidate_effect_fence,
        attempt_fence=selected_attempt,
        author_command=selected_command,
        cancellation_target=selected_cancellation_target,
        original_cancellation_target=original_cancellation_target,
        later_cancellation_target=later_cancellation_target,
        author_effect_fence=_canonical_author_effect_argument(
            selected_original_effect_fence, author_effect_fence
        ),
    )


def _manifest_valid_with_canonical_relations(
    manifest: dict[str, object],
    *,
    blobs: dict[str, dict[str, bytes]] | object = _UNSET,
    command: dict[str, object] | object = _UNSET,
    attempt_fence: dict[str, object] | object = _UNSET,
    effect_fence: dict[str, object] | object = _UNSET,
    observation: dict[str, object] | object = _UNSET,
) -> bool:
    return _manifest_valid(
        manifest,
        blobs=BLOB_FIXTURES if blobs is _UNSET else blobs,
        command=(
            _full_record("WorkerCommandV1")
            if command is _UNSET
            else command
        ),
        attempt_fence=(
            _full_record("AttemptFenceV1")
            if attempt_fence is _UNSET
            else attempt_fence
        ),
        effect_fence=(
            _effect_fence_for_vector("author")
            if effect_fence is _UNSET
            else effect_fence
        ),
        observation=(
            _full_record("WorkerObservationV1")
            if observation is _UNSET
            else observation
        ),
    )


def _observation_valid_with_canonical_relations(
    record: dict[str, object],
    *,
    effect_fence: dict[str, object] | object = _UNSET,
    delivery: dict[str, object] | object = _UNSET,
    author_command: dict[str, object] | object = _UNSET,
    attempt_fence: dict[str, object] | object = _UNSET,
    author_effect_fence: dict[str, object] | object = _UNSET,
    capsule_manifest: dict[str, object] | object = _UNSET,
    capsule_blobs: object = _UNSET,
    author_observation: dict[str, object] | object = _UNSET,
    cancellation_target: object = _UNSET,
) -> bool:
    selected_effect = (
        _effect_fence_for_vector("author")
        if effect_fence is _UNSET
        else effect_fence
    )
    selected_delivery = (
        _full_record("DeliveryEnvelopeV1")
        if delivery is _UNSET
        else delivery
    )
    selected_command = (
        _full_record("WorkerCommandV1")
        if author_command is _UNSET
        else author_command
    )
    selected_attempt = (
        _full_record("AttemptFenceV1")
        if attempt_fence is _UNSET
        else attempt_fence
    )
    observation_kind = (
        record.get("observation_kind") if type(record) is dict else None
    )
    conditional_key = (
        OBSERVATION_SPEC.get(observation_kind, ((), (), "none"))[2]
        if type(observation_kind) is str
        else "none"
    )
    selected_manifest = capsule_manifest
    selected_capsule_blobs = capsule_blobs
    selected_author_observation = author_observation
    if conditional_key == "capsule":
        if selected_manifest is _UNSET:
            selected_manifest = _full_record("CandidateCapsuleManifestV1")
        if selected_capsule_blobs is _UNSET:
            selected_capsule_blobs = BLOB_FIXTURES
        if selected_author_observation is _UNSET:
            selected_author_observation = _full_record("WorkerObservationV1")
    return _observation_valid(
        record,
        effect_fence=selected_effect,
        delivery=selected_delivery,
        author_command=selected_command,
        attempt_fence=selected_attempt,
        author_effect_fence=_canonical_author_effect_argument(
            selected_effect, author_effect_fence
        ),
        capsule_manifest=selected_manifest,
        capsule_blobs=selected_capsule_blobs,
        author_observation=selected_author_observation,
        cancellation_target=_canonical_cancellation_target_argument(
            selected_effect, cancellation_target
        ),
    )


def _observation_relation_with_canonical_relations(
    observation: dict[str, object],
    effect_fence: dict[str, object],
    delivery: dict[str, object],
    *,
    author_command: dict[str, object] | object = _UNSET,
    attempt_fence: dict[str, object] | object = _UNSET,
    author_effect_fence: dict[str, object] | object = _UNSET,
    capsule_manifest: dict[str, object] | object = _UNSET,
    capsule_blobs: object = _UNSET,
    author_observation: dict[str, object] | object = _UNSET,
    cancellation_target: object = _UNSET,
) -> bool:
    selected_command = (
        _full_record("WorkerCommandV1")
        if author_command is _UNSET
        else author_command
    )
    selected_attempt = (
        _full_record("AttemptFenceV1")
        if attempt_fence is _UNSET
        else attempt_fence
    )
    selected_manifest = capsule_manifest
    selected_capsule_blobs = capsule_blobs
    selected_author_observation = author_observation
    observation_kind = (
        observation.get("observation_kind")
        if type(observation) is dict
        else None
    )
    conditional_key = (
        OBSERVATION_SPEC.get(observation_kind, ((), (), "none"))[2]
        if type(observation_kind) is str
        else "none"
    )
    if conditional_key == "capsule":
        if selected_manifest is _UNSET:
            selected_manifest = _full_record("CandidateCapsuleManifestV1")
        if selected_capsule_blobs is _UNSET:
            selected_capsule_blobs = BLOB_FIXTURES
        if selected_author_observation is _UNSET:
            selected_author_observation = _full_record(
                "WorkerObservationV1"
            )
    return _observation_relation(
        observation,
        effect_fence,
        delivery,
        author_command=selected_command,
        attempt_fence=selected_attempt,
        author_effect_fence=_canonical_author_effect_argument(
            effect_fence, author_effect_fence
        ),
        capsule_manifest=selected_manifest,
        capsule_blobs=selected_capsule_blobs,
        author_observation=selected_author_observation,
        cancellation_target=_canonical_cancellation_target_argument(
            effect_fence, cancellation_target
        ),
    )
